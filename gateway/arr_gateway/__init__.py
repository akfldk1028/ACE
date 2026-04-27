"""Hermes plugin entry point — ARR (건축법규/토지분석) tools."""
from . import schemas, tools


def register(ctx):
    """Hermes plugin registration."""
    ctx.register_tool(
        name="land_analyst",
        toolset="arr",
        schema=schemas.LAND_ANALYST,
        handler=tools.land_analyst,
    )
