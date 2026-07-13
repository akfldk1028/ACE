from .agent import GrammarCriticAgent


def build_card():
    return GrammarCriticAgent().build_card()


__all__ = ["build_card"]
