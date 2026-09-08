"""Energy meters. Pick one with `get_meter(name)`."""

from __future__ import annotations

from .base import DEFAULT_DOMAINS, EnergyMeter
from .codegreen_meter import CodeGreenMeter
from .null import NullMeter
from .rapl import RaplMeter

__all__ = [
    "DEFAULT_DOMAINS",
    "describe",
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


def describe(name: str = "auto") -> dict:
    """What a meter will actually cover on this host, measured not assumed.

    A RAPL domain the current user cannot read is skipped silently by both
    real meters, which quietly narrows a reading from "package + DRAM" to
    whatever happened to be readable.

    For a one-off check from a shell, not for use inside a measurement run:
    taking a CodeGreen reading starts a sampler thread that keeps warning on
    stderr about every counter it cannot read, for the remaining life of the
    process.  `verify.py` therefore reads its coverage off the measurements it
    already takes, in the child process, rather than probing here.
    """
    meter = get_meter(name)
    visible = getattr(meter, "visible_domains", lambda: ())()
    missing = getattr(meter, "missing_domains", lambda: ())()
    return {
        "meter": meter.name,
        "requested_domains": list(DEFAULT_DOMAINS),
        "visible_domains": list(visible),
        "missing_domains": list(missing),
    }
