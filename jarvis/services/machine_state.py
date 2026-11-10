"""Monitoramento profundo do estado da máquina e janela ativa via Win32 APIs."""

from __future__ import annotations

import ctypes
from ctypes import wintypes
import logging
from typing import TypedDict

logger = logging.getLogger(__name__)


class MemoryStatusEx(ctypes.Structure):
    _fields_ = [
        ("dwLength", wintypes.DWORD),
        ("dwMemoryLoad", wintypes.DWORD),
        ("ullTotalPhys", ctypes.c_uint64),
        ("ullAvailPhys", ctypes.c_uint64),
        ("ullTotalPageFile", ctypes.c_uint64),
        ("ullAvailPageFile", ctypes.c_uint64),
        ("ullTotalVirtual", ctypes.c_uint64),
        ("ullAvailVirtual", ctypes.c_uint64),
        ("ullAvailExtendedVirtual", ctypes.c_uint64),
    ]


class SystemPowerStatus(ctypes.Structure):
    _fields_ = [
        ("ACLineStatus", wintypes.BYTE),
        ("BatteryFlag", wintypes.BYTE),
        ("BatteryLifePercent", wintypes.BYTE),
        ("SystemStatusFlag", wintypes.BYTE),
        ("BatteryLifeTime", wintypes.DWORD),
        ("BatteryFullLifeTime", wintypes.DWORD),
    ]


class MachineSnapshot(TypedDict):
    active_window: str
    ram_used_gb: float
    ram_free_gb: float
    ram_percent: int
    disk_free_gb: float
    power_status: str
    is_charging: bool


class MachineStateMonitor:
    """Coleta métricas de hardware e janela em primeiro plano em tempo real (0ms)."""

    def get_active_window_title(self) -> str:
        """Retorna o título da janela atualmente em primeiro plano na tela do usuário."""
        try:
            user32 = ctypes.windll.user32
            hwnd = user32.GetForegroundWindow()
            if not hwnd:
                return "Área de Trabalho"

            length = user32.GetWindowTextLengthW(hwnd)
            if length == 0:
                return "Área de Trabalho"

            buffer = ctypes.create_unicode_buffer(length + 1)
            user32.GetWindowTextW(hwnd, buffer, length + 1)
            title = buffer.value.strip()
            return title if title else "Área de Trabalho"
        except Exception as exc:  # noqa: BLE001
            logger.debug("Falha ao obter janela ativa: %s", exc)
            return "Área de Trabalho"

    def get_memory_metrics(self) -> tuple[float, float, int]:
        """Retorna (usada_gb, livre_gb, percentual_em_uso)."""
        stat = MemoryStatusEx()
        stat.dwLength = ctypes.sizeof(MemoryStatusEx)
        ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(stat))

        total_gb = stat.ullTotalPhys / (1024**3)
        free_gb = stat.ullAvailPhys / (1024**3)
        used_gb = total_gb - free_gb
        return round(used_gb, 1), round(free_gb, 1), int(stat.dwMemoryLoad)

    def get_disk_free_gb(self) -> float:
        """Retorna os gigabytes livres na partição primária C:."""
        free_bytes = ctypes.c_ulonglong(0)
        ctypes.windll.kernel32.GetDiskFreeSpaceExW("C:\\", ctypes.byref(free_bytes), None, None)
        return round(free_bytes.value / (1024**3), 1)

    def get_power_info(self) -> tuple[str, bool]:
        """Retorna (descrição_energia, está_carregando)."""
        status = SystemPowerStatus()
        success = ctypes.windll.kernel32.GetSystemPowerStatus(ctypes.byref(status))
        if not success:
            return "alimentação direta", True

        if status.ACLineStatus == 1:
            return "conectado à tomada", True
        if status.BatteryLifePercent != 255:
            return f"bateria em {status.BatteryLifePercent}%", False
        return "alimentação direta", True

    def get_snapshot(self) -> MachineSnapshot:
        """Captura um raio-x completo do estado da máquina."""
        used_ram, free_ram, ram_pct = self.get_memory_metrics()
        power_desc, is_charging = self.get_power_info()

        return {
            "active_window": self.get_active_window_title(),
            "ram_used_gb": used_ram,
            "ram_free_gb": free_ram,
            "ram_percent": ram_pct,
            "disk_free_gb": self.get_disk_free_gb(),
            "power_status": power_desc,
            "is_charging": is_charging,
        }

    def optimize_system_memory(self) -> int:
        """Apara o conjunto de trabalho de memória do processo atual e força coleta de lixo."""
        import gc

        gc.collect()
        current_proc = ctypes.windll.kernel32.GetCurrentProcess()
        # SetProcessWorkingSetSize com -1, -1 esvazia páginas desnecessárias da memória física
        ret = ctypes.windll.kernel32.SetProcessWorkingSetSize(current_proc, ctypes.c_size_t(-1), ctypes.c_size_t(-1))
        return 1 if ret != 0 else 0
