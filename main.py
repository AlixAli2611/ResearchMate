from models import ResearchContext
from agents.planning_agent import create_plan
from agents.retrieval_agent import retrieve_papers
from agents.processing_agent import process_papers
from agents.ranking_agent import rank_papers, assess_evidence_consistency
from agents.storage_agent import save_markdown_report, save_json_results


def get_requested_paper_count() -> int:
    """
    Ask the user how many papers to retrieve.

    The value is capped to keep the prototype manageable.
    """
    user_input = input("How many papers should ResearchMate retrieve? Default is 5, maximum is 20: ").strip()

    if not user_input:
        return 5

    try:
        requested_count = int(user_input)
    except ValueError:
        print("Invalid number entered. Using default of 5 papers.")
        return 5

    if requested_count < 1:
        print("Requested paper count must be at least 1. Using default of 5 papers.")
        return 5

    if requested_count > 20:
        print("Requested paper count capped at 20 for this prototype.")
        return 20

    return requested_count


def main():
    """
    Run the ResearchMate prototype from the command line.
    """
    print("ResearchMate: Academic Research Planning Agent")
    print("---------------------------------------------")

    query = input("Enter your academic research topic or question: ").strip()
    purpose = input(
        "Enter your research purpose, for example course design, literature review, "
        "background research, assignment, or personal study: "
    ).strip()
    audience_level = input(
        "Enter the intended audience or level, for example undergraduate, masters, "
        "doctoral, professional, or general audience: "
    ).strip()
    requested_papers = get_requested_paper_count()

    context = ResearchContext(
        query=query,
        purpose=purpose,
        audience_level=audience_level,
        requested_papers=requested_papers,
    )

    print("\nCreating research plan...")
    plan = create_plan(context)

    print("\nGenerated Plan:")
    for index, step in enumerate(plan.steps, start=1):
        print(f"{index}. {step}")

    print("\nRetrieving academic papers...")
    papers, retrieval_note = retrieve_papers(
        query=context.query,
        max_results=context.requested_papers,
    )

    print(f"\nRetrieved {len(papers)} papers.")
    print(retrieval_note)

    print("\nProcessing papers...")
    processed_papers = process_papers(papers, context)

    print("\nRanking papers...")
    ranked_papers = rank_papers(context, processed_papers)

    print("\nAssessing evidence...")
    evidence_note = assess_evidence_consistency(context, ranked_papers)

    print("\nRanked Papers:")
    for index, paper in enumerate(ranked_papers, start=1):
        print(f"\n{index}. {paper.title}")
        print(f"   Relevance score: {paper.relevance_score}/10")
        print(f"   Recommendation status: {paper.recommendation_status}")
        print(f"   Reason: {paper.relevance_reason}")
        print(f"   Paper type: {paper.paper_type}")
        print(f"   Source: {paper.source}")
        print(
            f"   Citation count: "
            f"{paper.citation_count if paper.citation_count is not None else 'Not available'}"
        )
        print(f"   Summary: {paper.summary}")
        print(f"   Key terms: {', '.join(paper.key_terms)}")
        print(f"   URL: {paper.url}")

    print("\nEvidence Note:")
    print(evidence_note)

    print("\nSaving outputs...")
    markdown_path = save_markdown_report(
        context=context,
        plan=plan,
        ranked_papers=ranked_papers,
        retrieval_note=retrieval_note,
        evidence_note=evidence_note,
    )

    json_path = save_json_results(
        context=context,
        plan=plan,
        ranked_papers=ranked_papers,
        retrieval_note=retrieval_note,
        evidence_note=evidence_note,
    )

    print(f"Markdown report saved to: {markdown_path}")
    print(f"JSON results saved to: {json_path}")

    print("\nDone.")


if __name__ == "__main__":
    main()