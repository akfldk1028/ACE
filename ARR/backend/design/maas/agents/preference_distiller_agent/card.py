from .agent import PreferenceDistillerAgent


def build_card():
    return PreferenceDistillerAgent().build_card()


__all__ = ["build_card"]

