"""PR summary generation service."""

from typing import Dict, Optional, Any
from ..prompts import PromptFactory
from ..providers import ProviderFactory


class PRService:
    """Service for generating PR summaries."""

    @staticmethod
    def generate_summary(
        plan: Dict[int, Dict],
        user_description: Optional[str] = None,
        provider: str = "gemini",
        key_manager: Optional[Any] = None,
        model_name: Optional[str] = None
    ) -> Optional[str]:
        """
        Generate PR summary from git plan.

        Args:
            plan: Git plan dictionary
            user_description: Optional user description
            provider: LLM provider name
            key_manager: API key manager
            model_name: Model name to use

        Returns:
            Generated PR summary or None if generation fails
        """
        try:
            provider_instance = ProviderFactory.create(
                provider,
                model_name=model_name,
                key_manager=key_manager
            )

            if not provider_instance:
                return None

            commits = []
            for g_id in sorted(plan.keys()):
                data = plan[g_id]
                if data.get("hunks"):
                    commits.append({
                        "id": g_id,
                        "message": data['desc'],
                        "files": len(set(
                            h.file if hasattr(h, 'file') else h['file']
                            for h in data["hunks"]
                        ))
                    })

            # Format commits for prompt
            commits_text = "\n".join([
                f"- {c['message']} ({c['files']} archivos)"
                for c in commits
            ])

            description_context = ""
            if user_description:
                description_context = (
                    f"\n\nDescripción proporcionada por el usuario:\n"
                    f"{user_description}"
                )

            prompt_template = PromptFactory.get_pr_summary_prompt(
                user_description
            )
            prompt = prompt_template.format(
                description_context=description_context,
                commits=commits_text
            )

            summary = provider_instance.invoke(prompt)
            return summary

        except Exception as e:
            print(f"⚠️  Error generando resumen de PR: {e}")
            return None
