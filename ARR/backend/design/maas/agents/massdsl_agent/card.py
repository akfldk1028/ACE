from .agent import MassDSLAgent


def build_card():
    return MassDSLAgent().build_card()


__all__ = ["build_card"]
