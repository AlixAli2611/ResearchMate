import json
from pathlib import Path
from models import ResearchContext, ResearchPlan, RankedPaper


def save_markdown_report(
    context: ResearchContext,
    plan: ResearchPlan,
    ranked_papers: list[RankedPaper],
    retrieval_note: str,
    evidence_note: str,
    output_path: str = "outputs/research_report.md",
) -> str:
    """
    Save a human-readable Markdown research report.

    Markdown was chosen because it is lightweight, easy to inspect, and suitable
    for demonstrating the system output without requiring extra PDF generation
    dependencies.
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    lines = [
        "# ResearchMate Research Briefing",
        "",
        "## Research Context",
        f"- **Topic:** {context.query}",
        f"- **Purpose:** {context.purpose}",
        f"- **Audience/Level:** {context.audience_level}",
        f"- **Requested papers:** {context.requested_papers}",
        "",
        "## Generated Research Plan",
    ]

    for index, step in enumerate(plan.steps, start=1):
        lines.append(f"{index}. {step}")

    lines.extend(
        [
            "",
            "## Retrieval Note",
            retrieval_note,
            "",
            "## Ranked Sources",
        ]
    )

    for index, paper in enumerate(ranked_papers, start=1):
        lines.extend(
            [
                "",
                f"### {index}. {paper.title}",
                f"- **Relevance score:** {paper.relevance_score}/10",
                f"- **Relevance reason:** {paper.relevance_reason}",
                f"- **Paper type:** {paper.paper_type}",
                f"- **Source:** {paper.source}",
                f"- **Citation count:** {paper.citation_count if paper.citation_count is not None else 'Not available'}",
                f"- **Publication type metadata:** {paper.publication_type or 'Not available'}",
                f"- **URL:** {paper.url}",
                f"- **Key terms:** {', '.join(paper.key_terms)}",
                "",
                f"**Source-level summary:** {paper.summary}",
            ]
        )

    lines.extend(
        [
            "",
            "## Evidence Consistency Note",
            evidence_note,
            "",
            "## Human Review Reminder",
            (
                "ResearchMate organises and ranks retrieved academic sources, but it does "
                "not replace human academic judgement. Source-level summaries should be "
                "checked against the original papers before being used in formal work."
            ),
        ]
    )

    path.write_text("\n".join(lines), encoding="utf-8")
    return str(path)


def save_json_results(
    context: ResearchContext,
    plan: ResearchPlan,
    ranked_papers: list[RankedPaper],
    retrieval_note: str,
    evidence_note: str,
    output_path: str = "outputs/results.json",
) -> str:
    """
    Save a machine-readable JSON record of the system output.

    JSON is useful for testing, debugging, and demonstrating that the system
    produces structured outputs in addition to a readable report.
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    data = {
        "query": context.query,
        "purpose": context.purpose,
        "audience_level": context.audience_level,
        "requested_papers": context.requested_papers,
        "plan": plan.steps,
        "retrieval_note": retrieval_note,
        "evidence_note": evidence_note,
        "ranked_papers": [paper.model_dump() for paper in ranked_papers],
    }

    path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return str(path)