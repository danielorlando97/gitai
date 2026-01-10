"""Semantic classifier using LLM."""

import os
import re
import json
import time
from typing import List, Dict, Optional, Any
from .base import AbstractClassifier
from ..models.hunk import Hunk
from ..models.goal import Goal
from ..providers import ProviderFactory
from ..prompts import PromptFactory
from ..utils.diff import create_summary_for_llm

try:
    from langchain_core.prompts import ChatPromptTemplate
    from langchain_core.output_parsers import PydanticOutputParser
    from ..models.git_plan import GitPlan
    HAS_LANGCHAIN = True
except ImportError:
    HAS_LANGCHAIN = False

try:
    from openai import OpenAI
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False
    OpenAI = None


class SemanticClassifier(AbstractClassifier):
    """Semantic classifier using LLM to identify goals and classify hunks."""

    def __init__(self, provider: str, key_manager: Optional[Any] = None,
                 model_name: Optional[str] = None):
        """
        Initialize semantic classifier.

        Args:
            provider: Provider name (ollama, gemini, openai)
            key_manager: API key manager instance
            model_name: Model name to use
        """
        self.provider = provider
        self.key_manager = key_manager
        self.model_name = model_name
        self._provider_instance = None

    def _get_provider(self):
        """Get or create provider instance."""
        if self._provider_instance is None:
            self._provider_instance = ProviderFactory.create(
                self.provider,
                model_name=self.model_name,
                key_manager=self.key_manager
            )
        return self._provider_instance


    def _handle_llm_error(self, error: Exception, client: Any) -> bool:
        """Handle LLM error and rotate key if needed."""
        error_str = str(error).lower()

        if any(keyword in error_str for keyword in [
            'rate limit', 'quota', '429', 'too many requests'
        ]):
            if self.key_manager and hasattr(client, '_key_id'):
                self.key_manager.record_error(
                    client._key_id, 'RATE_LIMIT', str(error)
                )
            return True
        return False

    def identify_goals(
        self,
        hunks: List[Hunk],
        user_context: Optional[str] = None
    ) -> List[Goal]:
        """Identify functional goals from hunks."""
        # Convert hunks to dict format for compatibility
        hunks_dict = [h.to_dict() if hasattr(h, 'to_dict') else {
            'file': h.file,
            'content': h.content
        } for h in hunks]

        summary = create_summary_for_llm(hunks_dict)

        # Calculate max retries
        max_retries = 1
        if self.key_manager:
            all_keys = self.key_manager.list_all({"provider": self.provider})
            max_retries = max(len(all_keys) * 2, 10) if all_keys else 1

        provider = self._get_provider()
        if not provider:
            return []

        client = provider.get_client()
        used_key_ids = set()

        if hasattr(client, '_key_id') and client._key_id:
            used_key_ids.add(client._key_id)

        for attempt in range(max_retries):
            try:
                
                parser = PydanticOutputParser(pydantic_object=GitPlan)
                prompt_template = PromptFactory.get_goals_identification_prompt(
                    user_context
                )
                prompt = ChatPromptTemplate.from_template(prompt_template)
                
                chain = prompt | client | parser
                result = chain.invoke({
                    "diff_summary": summary,
                    "format_instructions": parser.get_format_instructions()
                })
                return [
                    Goal(id=g.id, description=g.description)
                    for g in result.goals
                ]

            except Exception as e:
                if self._handle_llm_error(e, client):
                    # Rotate key
                    if self.key_manager:
                        all_keys = self.key_manager.list_all(
                            {"provider": self.provider}
                        )
                        all_key_ids = {k['id'] for k in all_keys}

                        if (used_key_ids.issuperset(all_key_ids) and
                                all_key_ids and
                                len(used_key_ids) >= len(all_key_ids)):
                            # All keys tried, wait
                            wait_minutes = int(
                                os.getenv("API_KEY_WAIT_MINUTES", "5")
                            )
                            print(
                                f"\n⚠️  Todas las API keys han alcanzado "
                                f"el límite."
                            )
                            print(
                                f"⏳ Esperando {wait_minutes} minutos..."
                            )

                            total_seconds = wait_minutes * 60
                            for remaining in range(total_seconds, 0, -30):
                                mins = remaining // 60
                                secs = remaining % 60
                                print(
                                    f"   Tiempo restante: {mins:02d}:{secs:02d}",
                                    end='\r'
                                )
                                time.sleep(min(30, remaining))
                            print("\n🔄 Reintentando...")
                            used_key_ids.clear()

                    # Get new provider instance
                    self._provider_instance = None
                    provider = self._get_provider()
                    if not provider:
                        break
                    client = provider.get_client()
                    if hasattr(client, '_key_id') and client._key_id:
                        used_key_ids.add(client._key_id)
                    continue
                else:
                    if attempt < max_retries - 1:
                        continue
                    print(f"Error identificando objetivos: {e}")
                    break

        return []

    def classify_hunks(
        self,
        hunks: List[Hunk],
        goals: List[Goal],
        user_context: Optional[str] = None
    ) -> Dict[int, Dict]:
        """Classify hunks into goals."""
        # Convert to dict format
        hunks_dict = [h.to_dict() if hasattr(h, 'to_dict') else {
            'file': h.file,
            'content': h.content
        } for h in hunks]

        goals_dict = [
            {"id": g.id, "description": g.description}
            for g in goals
        ]

        classified_plan = {
            goal.id: {
                "desc": goal.description,
                "hunks": []
            } for goal in goals
        }

        print("Clasificando cambios...")
        provider = self._get_provider()
        if not provider:
            return classified_plan

        client = provider.get_client()

        for i, hunk in enumerate(hunks_dict):
            print(f"  [{i+1}/{len(hunks_dict)}] {hunk['file']}...", end='\r')

            goal_id = self._classify_single_hunk(
                hunk, goals_dict, user_context, client, provider
            )

            if goal_id and goal_id in classified_plan:
                # Convert back to Hunk object
                hunk_obj = Hunk(
                    file=hunk['file'],
                    content=hunk['content']
                )
                classified_plan[goal_id]["hunks"].append(hunk_obj)

        print()  # New line after progress
        return classified_plan

    def _classify_single_hunk(
        self,
        hunk: Dict[str, str],
        goals: List[Dict],
        user_context: Optional[str],
        client: Any,
        provider: Any
    ) -> Optional[int]:
        """Classify a single hunk."""
        goals_text = "\n".join(
            [f"{g['id']}: {g['description']}" for g in goals]
        )

        max_retries = 1
        if self.key_manager:
            all_keys = self.key_manager.list_all({"provider": self.provider})
            max_retries = max(len(all_keys) * 2, 10) if all_keys else 1

        used_key_ids = set()
        if hasattr(client, '_key_id') and client._key_id:
            used_key_ids.add(client._key_id)

        for attempt in range(max_retries):
            try:
                prompt_template = PromptFactory.get_hunk_classification_prompt(
                    user_context
                )
                
                prompt = ChatPromptTemplate.from_template(prompt_template)
                
                chain = prompt | client
                result = chain.invoke({
                    "goals": goals_text,
                    "hunk": hunk['content'][:2000]
                })
                content = result.content.strip()
                import pdb; pdb.set_trace()
                goal_id = int(re.sub(r'\D', '', content))
                if goal_id in [g['id'] for g in goals]:
                    return goal_id

            except Exception as e:
                if self._handle_llm_error(e, client):
                    # Rotate key and retry
                    self._provider_instance = None
                    provider = self._get_provider()
                    if not provider:
                        break
                    client = provider.get_client()
                    if hasattr(client, '_key_id') and client._key_id:
                        used_key_ids.add(client._key_id)
                    continue
                else:
                    if attempt < max_retries - 1:
                        continue
                    break

        return None
