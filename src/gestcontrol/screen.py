"""Virtual-desktop bounds resolver for multi-monitor cursor mapping.

pyautogui.size() only returns the primary monitor — wrong for spanning setups.
GetSystemMetrics with the VIRTUALSCREEN indices returns the full desktop rect.
"""

from __future__ import annotations

import ctypes
import sys


class VirtualDesktop:
    SM_XVIRTUALSCREEN  = 76
    SM_YVIRTUALSCREEN  = 77
    SM_CXVIRTUALSCREEN = 78
    SM_CYVIRTUALSCREEN = 79

    def __init__(self) -> None:
        if sys.platform != "win32":
            raise OSError("VirtualDesktop is Windows-only")
        user32 = ctypes.windll.user32
        user32.SetProcessDPIAware()
        self.left   = user32.GetSystemMetrics(self.SM_XVIRTUALSCREEN)
        self.top    = user32.GetSystemMetrics(self.SM_YVIRTUALSCREEN)
        self.width  = user32.GetSystemMetrics(self.SM_CXVIRTUALSCREEN)
        self.height = user32.GetSystemMetrics(self.SM_CYVIRTUALSCREEN)

    def to_screen(
        self,
        norm_x: float,
        norm_y: float,
        deadzone: float = 0.0,
    ) -> tuple[int, int]:
        """Map normalised [0, 1] hand coords to virtual-desktop pixels.

        deadzone clips the edges so cursor can't get stuck in corners caused
        by gesture noise — pass the value from settings['screen']['deadzone'].
        """
        norm_x = max(deadzone, min(1.0 - deadzone, norm_x))
        norm_y = max(deadzone, min(1.0 - deadzone, norm_y))

        scale_x = norm_x / (1.0 - 2 * deadzone) if deadzone else norm_x
        scale_y = norm_y / (1.0 - 2 * deadzone) if deadzone else norm_y

        x = int(self.left + scale_x * self.width)
        y = int(self.top  + scale_y * self.height)
        return x, y
