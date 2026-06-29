from models import ResearchContext
from agents.planning_agent import create_plan
from agents.retrieval_agent import retrieve_papers
from agents.processing_agent import process_papers
from agents.ranking_agent import rank_papers, assess_evidence_consistency
from agents.storage_agent import save_markdown_report, save_json_results


def get_requested_paper_count() -> int:
    """
    Ask the user how many papers they want to retrieve.

    The value is capped to keep the prototype responsive during demonstration.
    """
    user_input = input("How many papers should be retrieved? Recommended: 5-10. ")

    try:
        requested_count = int(user_input)
    except ValueError:
        print("Invalid number entered. Using default of 5 papers.")
        return 5

    if requested_count < 1:
        print("Number too low. Using default of 5 papers.")
        return 5

    if requested_count > 20:
        print("Number too high for this prototype. Capping retrieval at 20 papers.")
        return 20

    return requested_count


def get_research_context() -> ResearchContext:
    """
    Collect the user's research context.

    Asking for purpose and level makes the system more goal-aware. The same topic
    may require different sources depending on whether the user is designing a
    course, writing a literature review, or completing an assignment.
    """
    query = input("Enter your academic research topic: ")

    print("\nWhat is the purpose of your research?")
    print("Examples: course design, literature review, background research, assignment, personal study")
    purpose = input("Purpose: ")

    print("\nWhat is the intended level or audience?")
    print("Examples: undergraduate, masters, doctoral, professional, general audience")
    audience_level = input("Level/audience: ")

    requested_papers = get_requested_paper_count()

    return ResearchContext(
        query=query.strip(),
        purpose=purpose.strip(),
        audience_level=audience_level.strip(),
        requested_papers=requested_papers,
    )


def main() -> None:
    print("ResearchMate: Academic Research Planning Agent")
    print("-" * 50)

    context = get_research_context()

    plan = create_plan(context)

    print("\nGenerated Research Plan:")
    for index, step in enumerate(plan.steps, start=1):
        print(f"{index}. {step}")

    print("\nRetrieving academic papers from arXiv...")
    papers, retrieval_note = retrieve_papers(context.query, max_results=context.requested_papers)

    print(f"\nRetrieved {len(papers)} papers:")
    for index, paper in enumerate(papers, start=1):
        print(f"\n{index}. {paper.title}")
        print(f"   Source: {paper.source}")
        print(f"   URL: {paper.url}")

    print("\n" + retrieval_note)

    print("\nProcessing retrieved papers...")
    processed_papers = process_papers(papers)

    print("\nRanking papers by relevance to your topic, purpose, and audience...")
    ranked_papers = rank_papers(context, processed_papers)
    evidence_note = assess_evidence_consistency(context, ranked_papers)

    print(f"\nRanked {len(ranked_papers)} papers:")
    for index, paper in enumerate(ranked_papers, start=1):
        print(f"\n{index}. {paper.title}")
        print(f"   Relevance score: {paper.relevance_score}/10")
        print(f"   Reason: {paper.relevance_reason}")
        print(f"   Summary: {paper.summary}")
        print(f"   Key terms: {', '.join(paper.key_terms)}")
        print(f"   URL: {paper.url}")

    print("\nEvidence consistency note:")
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


if __name__ == "__main__":
    main()