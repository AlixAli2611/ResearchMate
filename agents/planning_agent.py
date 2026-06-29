from models import ResearchContext, ResearchPlan


def create_plan(context: ResearchContext) -> ResearchPlan:
    """
    Create an ordered research plan from the user's query, purpose, and audience.

    The plan is adapted to the user's research purpose so the agent does not treat
    all research tasks as identical. This supports a more goal-oriented planning
    process.
    """
    if not context.query or not context.query.strip():
        raise ValueError("A research query is required.")

    steps = [
        f"Clarify the research goal: {context.query}.",
        f"Interpret the research purpose as: {context.purpose}.",
        f"Consider the intended level or audience: {context.audience_level}.",
        "Retrieve academic papers related to the topic from arXiv.",
        "Process each retrieved paper by creating a source-level summary.",
        "Rank papers using query match, purpose match, academic usefulness, and source completeness.",
        "Check whether the retrieved evidence appears consistent, limited, or mixed.",
        "Save the final research briefing as Markdown and JSON outputs.",
    ]

    return ResearchPlan(
        query=context.query,
        purpose=context.purpose,
        audience_level=context.audience_level,
        steps=steps,
    )