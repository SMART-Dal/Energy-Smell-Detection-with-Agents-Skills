"""Energy meters. Pick one with `get_meter(name)`."""

from __future__ import annotations

from .base import DEFAULT_DOMAINS, EnergyMeter
from .codegreen_meter import CodeGreenMeter
from .null import NullMeter
from .rapl import RaplMeter

__all__ = [
    "DEFAULT_DOMAINS",
    "EnergyMeter",
    "CodeGreenMeter",
    "NullMeter",
    "RaplMeter",
    "get_meter",
]

_METERS = {
    "codegreen": CodeGreenMeter,
    "rapl": RaplMeter,
    "null": NullMeter,
}


def get_meter(name: str = "auto") -> EnergyMeter:
    """Return a meter by name, or the best available one for "auto".

    Preference order for "auto" is CodeGreen, then raw RAPL, then the null
    meter.  The null meter is never a silent fallback for real measurement --
    callers that need genuine readings should check `meter.available()`.
    """
    if name == "auto":
        for candidate in (CodeGreenMeter(), RaplMeter()):
            if candidate.available():
                return candidate
        return NullMeter()

    try:
        return _METERS[name]()
    except KeyError:
        raise ValueError(
            f"unknown meter {name!r}, expected one of {sorted(_METERS)} or 'auto'"
        ) from None
