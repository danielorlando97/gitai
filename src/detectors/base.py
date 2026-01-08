"""Abstract base class for resource detectors."""

from abc import ABC, abstractmethod
from typing import Tuple, Optional, List


class AbstractDetector(ABC):
    """Abstract base class for system resource detectors."""

    @abstractmethod
    def detect_resources(
        self
    ) -> Tuple[float, int, Optional[float], Optional[str]]:
        """
        Detect system resources.

        Returns:
            Tuple of (RAM_GB, CPU_cores, VRAM_GB, GPU_type)
        """
        pass

    @abstractmethod
    def detect_scale(self, config_path: Optional[str] = None) -> str:
        """
        Detect resource scale from configuration.

        Args:
            config_path: Path to configuration file

        Returns:
            Scale name (low, medium, high, etc.)
        """
        pass

    @abstractmethod
    def get_recommended_model(
        self,
        provider: str,
        config_path: Optional[str] = None,
        scale: Optional[str] = None
    ) -> Optional[str]:
        """
        Get recommended model for provider.

        Args:
            provider: Provider name
            config_path: Path to configuration file
            scale: Resource scale (if None, auto-detect)

        Returns:
            Recommended model name or None
        """
        pass

    @abstractmethod
    def get_provider_priority(
        self,
        config_path: Optional[str] = None
    ) -> List[str]:
        """
        Get provider priority list.

        Args:
            config_path: Path to configuration file

        Returns:
            List of provider names in priority order
        """
        pass

    @abstractmethod
    def get_default_provider(
        self,
        config_path: Optional[str] = None
    ) -> str:
        """
        Get default provider.

        Args:
            config_path: Path to configuration file

        Returns:
            Default provider name
        """
        pass
