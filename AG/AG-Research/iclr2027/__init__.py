"""ICLR 2027 termination and architecture research utilities."""

__all__ = ["resolve_exp01_summary"]


def __getattr__(name: str):
    """Load the historical audit helper only when explicitly requested."""

    if name != "resolve_exp01_summary":
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    from .audit import resolve_exp01_summary

    globals()[name] = resolve_exp01_summary
    return resolve_exp01_summary
