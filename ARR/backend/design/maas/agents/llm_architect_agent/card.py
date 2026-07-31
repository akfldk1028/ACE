from .agent import LLMArchitectAgent


def build_card():
    return LLMArchitectAgent().build_card()


__all__ = ["build_card"]
