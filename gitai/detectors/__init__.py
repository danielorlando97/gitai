"""Resource detectors for GitClassifier."""

from .base import AbstractDetector
from .system import (
    SystemResourceDetector,
    detect_resource_scale,
    get_recommended_model,
    get_provider_priority,
    get_default_provider,
    print_system_info
)

__all__ = [
    "AbstractDetector",
    "SystemResourceDetector",
    "detect_resource_scale",
    "get_recommended_model",
    "get_provider_priority",
    "get_default_provider",
    "print_system_info"
]
