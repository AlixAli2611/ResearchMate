from agents.llm_utils import call_groq_json
from models import ResearchContext, ResearchPlan


def create_fallback_plan(context: ResearchContext) -> list[str]:
    """
    Create a deterministic fallback plan.

    The fallback keeps the system reproducible and testable when no Groq API key
    is available or when the LLM service fails.
    """
    return [
        f"Clarify the research goal: {context.query}.",
        f"Interpret the research purpose as: {context.purpose}.",
        f"Consider the intended level or audience: {context.audience_level}.",
        "Retrieve academic papers related to the topic from arXiv, Semantic Scholar, and OpenAlex where available.",
        "Process each retrieved paper by creating a source-level summary, context-aware key terms, and paper type label.",
        "Rank papers using query match, purpose match, audience match, paper type fit, and source completeness.",
        "Assess whether the retrieved evidence appears strong, moderate, weak, limited, or mixed.",
        "Save the final research briefing as Markdown, JSON, and persistent storage outputs where available.",
    ]


def create_llm_plan(context: ResearchContext) -> list[str]:
    """
    Use Groq/Llama to generate a research plan.

    The LLM is given a role, rules, and a required JSON structure so its output
    can be parsed and validated by the Python application.
    """
    system_message = (
        "You are the Planning Agent in ResearchMate, an academic research "
        "assistant. You create concise, structured research plans. Return only "
        "valid JSON. Do not include markdown or extra commentary."
    )

    user_message = f"""
Create a concise research plan for an academic research assistant.

User context:
- Topic: {context.query}
- Purpose: {context.purpose}
- Audience/level: {context.audience_level}
- Requested papers: {context.requested_papers}

Rules:
- The plan must be suitable for academic research or structured information gathering.
- The plan must include retrieval, processing, ranking, evidence assessment, and output saving.
- Do not claim that sources have been read yet.
- Do not invent paper titles, authors, or findings.
- Keep the plan to 6 to 8 steps.
- Make the plan specific to the user's topic, purpose, and audience level.
- The plan should describe what the system will do, not what the final answer already proves.

Return only valid JSON in this exact structure:
{{
  "steps": [
    "step 1",
    "step 2",
    "step 3"
  ]
}}
"""

    parsed = call_groq_json(
        system_message=system_message,
        user_message=user_message,
        temperature=0.2,
    )

    steps = parsed.get("steps", [])

    if not isinstance(steps, list) or not steps:
        raise ValueError("The LLM did not return a valid list of planning steps.")

    cleaned_steps = [str(step).strip() for step in steps if str(step).strip()]

    if not cleaned_steps:
        raise ValueError("The LLM returned empty planning steps.")

    return cleaned_steps


def create_plan(context: ResearchContext) -> ResearchPlan:
    """
    Create an ordered research plan from the user's query, purpose, and audience.

    The planner first attempts to use Groq/Llama for LLM-supported planning. If
    no API key is available or the LLM call fails, it falls back to a deterministic
    plan so the system remains reproducible for testing and marking.
    """
    if not context.query or not context.query.strip():
        raise ValueError("A research query is required.")

    try:
        steps = create_llm_plan(context)
        planning_mode = "LLM-powered planning through Groq/Llama"
    except Exception as error:
        print(f"LLM planning unavailable: {error}")
        print("Using deterministic fallback planning.")
        steps = create_fallback_plan(context)
        planning_mode = "Deterministic fallback planning"

    steps.insert(0, f"Planning mode: {planning_mode}.")

    return ResearchPlan(
        query=context.query,
        purpose=context.purpose,
        audience_level=context.audience_level,
        steps=steps,
    )