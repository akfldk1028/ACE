from .agent import MasterPlanAgent


def build_card():
    return MasterPlanAgent().build_card()


__all__ = ["build_card"]
