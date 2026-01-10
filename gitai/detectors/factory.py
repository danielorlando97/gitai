"""Factory for creating detector instances."""

from typing import Optional
from .base import AbstractDetector
from .system import SystemResourceDetector


class DetectorFactory:
    """Factory for creating detector instances."""

    _detectors = {
        "system": SystemResourceDetector
    }

    @classmethod
    def create(
        cls,
        detector_type: str = "system",
        config_path: Optional[str] = None
    ) -> AbstractDetector:
        """
        Create a detector instance.

        Args:
            detector_type: Type of detector to create
            config_path: Optional path to config file

        Returns:
            Detector instance

        Raises:
            ValueError: If detector type is not registered
        """
        if detector_type not in cls._detectors:
            raise ValueError(
                f"Unknown detector type: {detector_type}. "
                f"Available: {list(cls._detectors.keys())}"
            )

        detector_class = cls._detectors[detector_type]
        if config_path:
            return detector_class(config_path=config_path)
        return detector_class()

    @classmethod
    def register(cls, detector_type: str, detector_class: type) -> None:
        """
        Register a new detector type.

        Args:
            detector_type: Name of the detector type
            detector_class: Detector class to register
        """
        if not issubclass(detector_class, AbstractDetector):
            raise TypeError(
                "Detector class must inherit from AbstractDetector"
            )
        cls._detectors[detector_type] = detector_class
