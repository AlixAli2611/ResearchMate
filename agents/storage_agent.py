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
    Save the research briefing as a Markdown report.
    """
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    lines = [
        "# ResearchMate Research Briefing",
        "",
        "## Research Context",
        "",
        f"- **Research topic/query:** {context.query}",
        f"- **Purpose:** {context.purpose}",
        f"- **Audience/level:** {context.audience_level}",
        f"- **Requested papers:** {context.requested_papers}",
        "",
        "## Generated Research Plan",
        "",
    ]

    for index, step in enumerate(plan.steps, start=1):
        lines.append(f"{index}. {step}")

    lines.extend(
        [
            "",
            "## Retrieval Note",
            "",
            retrieval_note,
            "",
            "## Ranked Sources",
            "",
        ]
    )

    for index, paper in enumerate(ranked_papers, start=1):
        lines.extend(
            [
                f"### {index}. {paper.title}",
                "",
                f"- **Relevance score:** {paper.relevance_score}/10",
                f"- **Recommendation status:** {paper.recommendation_status}",
                f"- **Relevance reason:** {paper.relevance_reason}",
                f"- **Paper type:** {paper.paper_type}",
                f"- **Source:** {paper.source}",
                f"- **Citation count:** {paper.citation_count if paper.citation_count is not None else 'Not available'}",
                f"- **Publication type metadata:** {paper.publication_type or 'Not available'}",
                f"- **URL:** {paper.url}",
                f"- **Key terms:** {', '.join(paper.key_terms)}",
                "",
                "**Source-level summary:**",
                "",
                paper.summary,
                "",
            ]
        )

    lines.extend(
        [
            "## Evidence Consistency Note",
            "",
            evidence_note,
            "",
            "## Limitations",
            "",
            (
                "This prototype uses academic metadata, abstracts, and structured LLM-assisted "
                "analysis. Paper type classification, key term extraction, ranking, and evidence "
                "assessment should be checked against the original sources. The system organises "
                "and prioritises sources; it does not replace academic judgement or full-text review."
            ),
            "",
            "## Human Review Reminder",
            "",
            (
                "Users should read the original papers before relying on any findings, claims, "
                "or recommendations. Low-scoring and not-recommended papers are retained for "
                "transparency but should not be treated as strong evidence for the user's goal."
            ),
            "",
        ]
    )

    output_file.write_text("\n".join(lines), encoding="utf-8")

    return str(output_file)


def save_json_results(
    context: ResearchContext,
    plan: ResearchPlan,
    ranked_papers: list[RankedPaper],
    retrieval_note: str,
    evidence_note: str,
    output_path: str = "outputs/results.json",
) -> str:
    """
    Save the research briefing as structured JSON.
    """
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    data = {
        "query": context.query,
        "purpose": context.purpose,
        "audience_level": context.audience_level,
        "requested_papers": context.requested_papers,
        "plan": plan.model_dump(),
        "retrieval_note": retrieval_note,
        "evidence_note": evidence_note,
        "ranked_papers": [
            paper.model_dump()
            for paper in ranked_papers
        ],
        "limitations": (
            "This prototype uses academic metadata, abstracts, and structured LLM-assisted "
            "analysis. Outputs should be checked against original sources before academic use."
        ),
    }

    output_file.write_text(
        json.dumps(data, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    return str(output_file)