"""System resource detector implementation."""

import json
import os
import platform
import subprocess
import re
from typing import Tuple, Optional, List
from pathlib import Path
from .base import AbstractDetector


class SystemResourceDetector(AbstractDetector):
    """System resource detector implementation."""

    def __init__(self, config_path: Optional[str] = None):
        """Initialize detector with config path."""
        if config_path is None:
            # Default to config/model_config.json
            base_dir = Path(__file__).parent.parent.parent.parent
            config_path = str(base_dir / "config" / "model_config.json")
        self.config_path = config_path

    def _get_gpu_info(self) -> Tuple[Optional[float], Optional[str]]:
        """Detect GPU information (VRAM and type)."""
        vram_gb = None
        gpu_type = None

        try:
            if platform.system() == "Darwin":  # macOS
                try:
                    brand_result = subprocess.run(
                        ['sysctl', '-n', 'machdep.cpu.brand_string'],
                        capture_output=True,
                        text=True,
                        timeout=2
                    )
                    if brand_result.returncode == 0:
                        brand = brand_result.stdout.strip()
                        if 'Apple' in brand:
                            gpu_type = "Apple Silicon"
                            match = re.search(
                                r'Apple\s+(M\d+)(?:\s+(Pro|Max|Ultra))?',
                                brand
                            )
                            if match:
                                chip_model = match.group(1)
                                chip_variant = match.group(2) or "Base"

                                if chip_model == "M4":
                                    if chip_variant == "Pro":
                                        vram_gb = 14.0
                                    elif chip_variant == "Max":
                                        vram_gb = 22.0
                                    else:
                                        vram_gb = 9.0
                                elif chip_model == "M3":
                                    if chip_variant == "Pro":
                                        vram_gb = 14.0
                                    elif chip_variant == "Max":
                                        vram_gb = 20.0
                                    else:
                                        vram_gb = 8.0
                                elif chip_model == "M2":
                                    if chip_variant == "Pro":
                                        vram_gb = 12.0
                                    elif chip_variant == "Max":
                                        vram_gb = 18.0
                                    else:
                                        vram_gb = 7.0
                                elif chip_model == "M1":
                                    if chip_variant == "Pro":
                                        vram_gb = 10.0
                                    elif chip_variant == "Max":
                                        vram_gb = 16.0
                                    else:
                                        vram_gb = 6.0
                                else:
                                    vram_gb = 8.0
                            else:
                                vram_gb = 8.0
                except Exception:
                    pass

            elif platform.system() in ["Linux", "Windows"]:
                try:
                    result = subprocess.run(
                        ['nvidia-smi', '--query-gpu=memory.total',
                         '--format=csv,noheader,nounits'],
                        capture_output=True,
                        text=True,
                        timeout=5
                    )
                    if result.returncode == 0:
                        vram_mb = 0
                        for line in result.stdout.strip().split('\n'):
                            if line.strip():
                                try:
                                    vram_mb += int(line.strip())
                                except ValueError:
                                    pass
                        if vram_mb > 0:
                            vram_gb = vram_mb / 1024
                            gpu_type = "NVIDIA"
                except (FileNotFoundError, subprocess.TimeoutExpired):
                    pass

                if gpu_type is None and platform.system() == "Linux":
                    try:
                        result = subprocess.run(
                            ['rocm-smi', '--showid', '--showmeminfo', 'vram'],
                            capture_output=True,
                            text=True,
                            timeout=5
                        )
                        if result.returncode == 0:
                            match = re.search(
                                r'(\d+)\s*(GB|MB)',
                                result.stdout
                            )
                            if match:
                                value = float(match.group(1))
                                unit = match.group(2)
                                if unit == 'MB':
                                    value = value / 1024
                                vram_gb = value
                                gpu_type = "AMD"
                    except (FileNotFoundError, subprocess.TimeoutExpired):
                        pass

        except Exception:
            pass

        return vram_gb, gpu_type

    def detect_resources(
        self
    ) -> Tuple[float, int, Optional[float], Optional[str]]:
        """Detect system resources."""
        try:
            if platform.system() == "Darwin":  # macOS
                try:
                    result = subprocess.run(
                        ['sysctl', '-n', 'hw.memsize'],
                        capture_output=True,
                        text=True,
                        timeout=2
                    )
                    if result.returncode == 0:
                        ram_bytes = int(result.stdout.strip())
                        ram_gb = ram_bytes / (1024 ** 3)
                    else:
                        ram_gb = 8.0
                except Exception:
                    ram_gb = 8.0

                cores = os.cpu_count() or 1

            elif platform.system() == "Linux":
                try:
                    with open('/proc/meminfo', 'r') as f:
                        for line in f:
                            if line.startswith('MemTotal:'):
                                ram_kb = int(line.split()[1])
                                ram_gb = ram_kb / (1024 ** 2)
                                break
                except (FileNotFoundError, ValueError):
                    ram_gb = 4.0

                cores = os.cpu_count() or 1

            elif platform.system() == "Windows":
                import ctypes
                class MEMORYSTATUSEX(ctypes.Structure):
                    _fields_ = [
                        ("dwLength", ctypes.c_ulong),
                        ("dwMemoryLoad", ctypes.c_ulong),
                        ("ullTotalPhys", ctypes.c_ulonglong),
                        ("ullAvailPhys", ctypes.c_ulonglong),
                        ("ullTotalPageFile", ctypes.c_ulonglong),
                        ("ullAvailPageFile", ctypes.c_ulonglong),
                        ("ullTotalVirtual", ctypes.c_ulonglong),
                        ("ullAvailVirtual", ctypes.c_ulonglong),
                        ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
                    ]

                mem_status = MEMORYSTATUSEX()
                mem_status.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
                ctypes.windll.kernel32.GlobalMemoryStatusEx(
                    ctypes.byref(mem_status)
                )
                ram_gb = mem_status.ullTotalPhys / (1024 ** 3)
                cores = os.cpu_count() or 1
            else:
                ram_gb = 4.0
                cores = 2

        except Exception:
            ram_gb = 4.0
            cores = 2

        vram_gb, gpu_type = self._get_gpu_info()

        return ram_gb, cores, vram_gb, gpu_type

    def detect_scale(self, config_path: Optional[str] = None) -> str:
        """Detect resource scale from configuration."""
        if config_path is None:
            config_path = self.config_path

        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
        except FileNotFoundError:
            return "medium"

        ram_gb, cores, vram_gb, gpu_type = self.detect_resources()

        scales = config.get("resource_scales", {})

        scale_order = (
            ["gpu_high", "low", "medium", "high", "very_high"]
            if vram_gb
            else ["low", "medium", "high", "very_high"]
        )

        for scale_name in scale_order:
            scale_config = scales.get(scale_name, {})
            if not scale_config:
                continue

            detection = scale_config.get("detection", {})
            max_ram = detection.get("max_ram_gb", 999999)
            max_cores = detection.get("max_cores", 999999)
            min_vram = detection.get("min_vram_gb", 0)
            max_vram = detection.get("max_vram_gb", 999999)

            ram_ok = ram_gb <= max_ram
            cores_ok = cores <= max_cores

            gpu_ok = True
            if min_vram > 0:
                if vram_gb is None:
                    gpu_ok = False
                else:
                    gpu_ok = min_vram <= vram_gb <= max_vram
            elif vram_gb is not None and max_vram < 999999:
                gpu_ok = vram_gb <= max_vram

            if ram_ok and cores_ok and gpu_ok:
                return scale_name

        return "very_high"

    def get_recommended_model(
        self,
        provider: str,
        config_path: Optional[str] = None,
        scale: Optional[str] = None
    ) -> Optional[str]:
        """Get recommended model for provider."""
        if config_path is None:
            config_path = self.config_path

        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
        except FileNotFoundError:
            return None

        if scale is None:
            scale = self.detect_scale(config_path)

        scales = config.get("resource_scales", {})
        scale_config = scales.get(scale, {})
        models = scale_config.get("models", {})

        provider_models = models.get(provider, [])
        if provider_models:
            return provider_models[0]

        return None

    def get_provider_priority(
        self,
        config_path: Optional[str] = None
    ) -> List[str]:
        """Get provider priority list."""
        if config_path is None:
            config_path = self.config_path

        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
        except FileNotFoundError:
            return ["ollama", "gemini", "openai"]

        return config.get(
            "provider_priority",
            ["ollama", "gemini", "openai"]
        )

    def get_default_provider(
        self,
        config_path: Optional[str] = None
    ) -> str:
        """Get default provider."""
        if config_path is None:
            config_path = self.config_path

        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
        except FileNotFoundError:
            return "ollama"

        return config.get("default_provider", "ollama")

    def print_system_info(self) -> None:
        """Print system information and recommendations."""
        ram_gb, cores, vram_gb, gpu_type = self.detect_resources()
        scale = self.detect_scale()

        print(f"💻 Recursos detectados:")
        print(f"   RAM: {ram_gb:.1f} GB")
        print(f"   CPU Cores: {cores}")
        if vram_gb is not None and gpu_type:
            print(f"   GPU: {gpu_type} ({vram_gb:.1f} GB VRAM)")
        else:
            print(f"   GPU: No detectada")
        print(f"   Escala: {scale}")
        print()

        print("📋 Modelos recomendados por proveedor:")
        for provider in ["ollama", "gemini", "openai"]:
            model = self.get_recommended_model(provider, scale=scale)
            if model:
                print(f"   {provider}: {model}")
            else:
                print(f"   {provider}: No configurado")
        print()

        priority = self.get_provider_priority()
        print(f"🎯 Prioridad de proveedores: {' > '.join(priority)}")


# Global instance for backward compatibility
_detector = SystemResourceDetector()


def detect_resource_scale(config_path: Optional[str] = None) -> str:
    """Backward compatibility function."""
    if config_path:
        detector = SystemResourceDetector(config_path)
    else:
        detector = _detector
    return detector.detect_scale(config_path)


def get_recommended_model(
    provider: str,
    config_path: Optional[str] = None,
    scale: Optional[str] = None
) -> Optional[str]:
    """Backward compatibility function."""
    if config_path:
        detector = SystemResourceDetector(config_path)
    else:
        detector = _detector
    return detector.get_recommended_model(provider, config_path, scale)


def get_provider_priority(config_path: Optional[str] = None) -> List[str]:
    """Backward compatibility function."""
    if config_path:
        detector = SystemResourceDetector(config_path)
    else:
        detector = _detector
    return detector.get_provider_priority(config_path)


def get_default_provider(config_path: Optional[str] = None) -> str:
    """Backward compatibility function."""
    if config_path:
        detector = SystemResourceDetector(config_path)
    else:
        detector = _detector
    return detector.get_default_provider(config_path)


def print_system_info() -> None:
    """Backward compatibility function."""
    _detector.print_system_info()
