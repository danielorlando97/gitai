#!/usr/bin/env python3
"""
Detector de recursos del sistema para proponer modelos LLM apropiados.
"""

import json
import os
import platform
import subprocess
from typing import Dict, Optional, Tuple, List
from pathlib import Path


def get_gpu_info() -> Tuple[Optional[float], Optional[str]]:
    """
    Detecta información de la GPU (VRAM y tipo).
    
    Returns:
        Tuple[Optional[float], Optional[str]]: (VRAM en GB, tipo de GPU) o (None, None)
    """
    vram_gb = None
    gpu_type = None
    
    try:
        if platform.system() == "Darwin":  # macOS
            # Verificar si es Apple Silicon
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
                        # Apple Silicon usa memoria unificada
                        import re
                        
                        # Detectar modelo del chip (M1, M2, M3, M4, etc.)
                        chip_model = None
                        chip_variant = None
                        
                        # Buscar patrón M1, M2, M3, M4, etc. en brand
                        match = re.search(r'Apple\s+(M\d+)(?:\s+(Pro|Max|Ultra))?', brand)
                        if match:
                            chip_model = match.group(1)
                            chip_variant = match.group(2) or "Base"
                        
                        # Estimar VRAM basado en el modelo del chip
                        # En Apple Silicon, la GPU comparte RAM con el sistema
                        # Usar una estimación basada en el modelo del chip
                        if chip_model:
                            # Estimar VRAM basado en modelo
                            # M4 Base: ~8-10GB VRAM efectivo
                            # M4 Pro: ~12-16GB VRAM efectivo
                            # M4 Max: ~20-24GB VRAM efectivo
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
                                # Modelo desconocido, estimación conservadora
                                vram_gb = 8.0
                        else:
                            # No se pudo detectar modelo, usar estimación conservadora
                            vram_gb = 8.0
                        
                        # Verificar que la GPU esté disponible usando ioreg
                        try:
                            ioreg_result = subprocess.run(
                                ['ioreg', '-rc', 'IOAccelerator'],
                                capture_output=True,
                                text=True,
                                timeout=5
                            )
                            if ioreg_result.returncode == 0:
                                output = ioreg_result.stdout
                                # Si no hay IOAccelerator, podría no haber GPU activa
                                if 'IOAccelerator' not in output:
                                    # Aún así, Apple Silicon siempre tiene GPU integrada
                                    pass
                        except Exception:
                            # Si ioreg falla, asumir que la GPU está disponible
                            pass
                            
            except Exception as e:
                pass
        
        elif platform.system() in ["Linux", "Windows"]:
            # Intentar detectar NVIDIA GPU
            try:
                result = subprocess.run(
                    ['nvidia-smi', '--query-gpu=memory.total', '--format=csv,noheader,nounits'],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode == 0:
                    # Obtener VRAM de todas las GPUs y sumar
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
            
            # Si no hay NVIDIA, intentar AMD (solo Linux)
            if gpu_type is None and platform.system() == "Linux":
                try:
                    result = subprocess.run(
                        ['rocm-smi', '--showid', '--showmeminfo', 'vram'],
                        capture_output=True,
                        text=True,
                        timeout=5
                    )
                    if result.returncode == 0:
                        # Parsear output de rocm-smi
                        import re
                        match = re.search(r'(\d+)\s*(GB|MB)', result.stdout)
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


def get_system_resources() -> Tuple[float, int, Optional[float], Optional[str]]:
    """
    Detecta los recursos del sistema (RAM, CPU cores, GPU VRAM y tipo).
    
    Returns:
        Tuple[float, int, Optional[float], Optional[str]]: 
        (RAM en GB, número de cores, VRAM en GB, tipo de GPU)
    """
    try:
        if platform.system() == "Darwin":  # macOS
            # Obtener RAM total usando sysctl
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
                    ram_gb = 8.0  # Default conservador
            except Exception:
                ram_gb = 8.0  # Default conservador
            
            # Obtener cores
            cores = os.cpu_count() or 1
            
        elif platform.system() == "Linux":
            # Obtener RAM total desde /proc/meminfo
            try:
                with open('/proc/meminfo', 'r') as f:
                    for line in f:
                        if line.startswith('MemTotal:'):
                            ram_kb = int(line.split()[1])
                            ram_gb = ram_kb / (1024 ** 2)
                            break
            except (FileNotFoundError, ValueError):
                ram_gb = 4.0  # Default conservador
            
            # Obtener cores
            cores = os.cpu_count() or 1
            
        elif platform.system() == "Windows":
            import ctypes
            # Obtener RAM total
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
            ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(mem_status))
            ram_gb = mem_status.ullTotalPhys / (1024 ** 3)
            
            # Obtener cores
            cores = os.cpu_count() or 1
        else:
            # Sistema desconocido, valores conservadores
            ram_gb = 4.0
            cores = 2
            
    except Exception:
        # En caso de error, valores conservadores
        ram_gb = 4.0
        cores = 2
    
    # Obtener información de GPU
    vram_gb, gpu_type = get_gpu_info()
    
    return ram_gb, cores, vram_gb, gpu_type


def detect_resource_scale(config_path: Optional[str] = None) -> str:
    """
    Detecta la escala de recursos del sistema basándose en la configuración.
    
    Args:
        config_path: Ruta al archivo de configuración JSON
        
    Returns:
        str: Nombre de la escala detectada (low, medium, high, very_high)
    """
    if config_path is None:
        config_path = os.path.join(
            os.path.dirname(__file__), "model_config.json"
        )
    
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
    except FileNotFoundError:
        return "medium"  # Default si no existe el archivo
    
    ram_gb, cores, vram_gb, gpu_type = get_system_resources()
    
    scales = config.get("resource_scales", {})
    
    # Si hay GPU, priorizar escalas que la aprovechen
    # Orden: verificar primero las escalas más específicas (con GPU)
    scale_order = ["gpu_high", "low", "medium", "high", "very_high"] if vram_gb else ["low", "medium", "high", "very_high"]
    
    for scale_name in scale_order:
        scale_config = scales.get(scale_name, {})
        if not scale_config:
            continue
            
        detection = scale_config.get("detection", {})
        max_ram = detection.get("max_ram_gb", 999999)
        max_cores = detection.get("max_cores", 999999)
        min_vram = detection.get("min_vram_gb", 0)
        max_vram = detection.get("max_vram_gb", 999999)
        
        # Verificar criterios de CPU/RAM
        ram_ok = ram_gb <= max_ram
        cores_ok = cores <= max_cores
        
        # Verificar criterios de GPU
        gpu_ok = True
        if min_vram > 0:
            # Esta escala requiere GPU
            if vram_gb is None:
                # Si se requiere GPU pero no hay, no califica
                gpu_ok = False
            else:
                gpu_ok = min_vram <= vram_gb <= max_vram
        elif vram_gb is not None and max_vram < 999999:
            # Esta escala tiene límite máximo de VRAM
            gpu_ok = vram_gb <= max_vram
        
        # Si todos los criterios se cumplen, usar esta escala
        if ram_ok and cores_ok and gpu_ok:
            return scale_name
    
    # Si no encaja en ninguna, usar very_high
    return "very_high"


def get_recommended_model(provider: str, 
                         config_path: Optional[str] = None,
                         scale: Optional[str] = None) -> Optional[str]:
    """
    Obtiene el modelo recomendado para un proveedor dado.
    
    Args:
        provider: Proveedor LLM (ollama, gemini, openai)
        config_path: Ruta al archivo de configuración JSON
        scale: Escala de recursos (si None, se detecta automáticamente)
        
    Returns:
        str: Nombre del modelo recomendado, o None si no se encuentra
    """
    if config_path is None:
        config_path = os.path.join(
            os.path.dirname(__file__), "model_config.json"
        )
    
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
    except FileNotFoundError:
        return None
    
    if scale is None:
        scale = detect_resource_scale(config_path)
    
    scales = config.get("resource_scales", {})
    scale_config = scales.get(scale, {})
    models = scale_config.get("models", {})
    
    provider_models = models.get(provider, [])
    if provider_models:
        return provider_models[0]  # Retornar el primer modelo (preferido)
    
    return None


def get_provider_priority(config_path: Optional[str] = None) -> List[str]:
    """
    Obtiene la lista de prioridad de proveedores desde la configuración.
    
    Args:
        config_path: Ruta al archivo de configuración JSON
        
    Returns:
        List[str]: Lista de proveedores en orden de prioridad
    """
    if config_path is None:
        config_path = os.path.join(
            os.path.dirname(__file__), "model_config.json"
        )
    
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
    except FileNotFoundError:
        return ["ollama", "gemini", "openai"]
    
    return config.get("provider_priority", ["ollama", "gemini", "openai"])


def get_default_provider(config_path: Optional[str] = None) -> str:
    """
    Obtiene el proveedor por defecto desde la configuración.
    
    Args:
        config_path: Ruta al archivo de configuración JSON
        
    Returns:
        str: Nombre del proveedor por defecto
    """
    if config_path is None:
        config_path = os.path.join(
            os.path.dirname(__file__), "model_config.json"
        )
    
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
    except FileNotFoundError:
        return "ollama"
    
    return config.get("default_provider", "ollama")


def print_system_info():
    """Imprime información del sistema y recomendaciones."""
    ram_gb, cores, vram_gb, gpu_type = get_system_resources()
    scale = detect_resource_scale()
    
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
        model = get_recommended_model(provider, scale=scale)
        if model:
            print(f"   {provider}: {model}")
        else:
            print(f"   {provider}: No configurado")
    print()
    
    priority = get_provider_priority()
    print(f"🎯 Prioridad de proveedores: {' > '.join(priority)}")

