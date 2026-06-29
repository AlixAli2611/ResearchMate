import arxiv
from models import Paper


def get_fallback_papers(query: str) -> list[Paper]:
    """
    Provide fallback paper-like records when the external arXiv service fails.

    This is not used as real research evidence. It exists so the rest of the
    ResearchMate pipeline can still be demonstrated and tested when an external
    academic API is temporarily unavailable.
    """
    return [
        Paper(
            title=f"Fallback result: AI-supported learning related to {query}",
            authors=["ResearchMate fallback dataset"],
            abstract=(
                "This fallback record represents a placeholder academic source. "
                "It allows the processing, ranking, and storage agents to continue "
                "running when the live arXiv API is unavailable."
            ),
            url="https://arxiv.org/",
            published=None,
            source="Fallback",
        ),
        Paper(
            title=f"Fallback result: Intelligent tutoring systems and {query}",
            authors=["ResearchMate fallback dataset"],
            abstract=(
                "This fallback record is used only for system demonstration. "
                "It should be replaced by live arXiv results when the external "
                "retrieval service is available."
            ),
            url="https://arxiv.org/",
            published=None,
            source="Fallback",
        ),
    ]


def suggest_related_topics(query: str) -> list[str]:
    """
    Suggest broader or related search directions when retrieval is limited.

    These suggestions are rule-based so the system can give useful next steps
    without pretending it has solved the shortage of evidence automatically.
    """
    query_lower = query.lower()

    suggestions = [
        f"Broaden the search from '{query}' to a wider topic.",
        "Try using fewer keywords or more general academic terms.",
        "Search for recent review papers on the broader field.",
    ]

    if "tutor" in query_lower or "education" in query_lower or "learning" in query_lower:
        suggestions.extend(
            [
                "Try related terms such as 'intelligent tutoring systems'.",
                "Try related terms such as 'AI in education'.",
                "Try related terms such as 'adaptive learning systems'.",
            ]
        )

    if "health" in query_lower or "medical" in query_lower:
        suggestions.extend(
            [
                "Try related terms such as 'clinical decision support'.",
                "Try related terms such as 'AI in healthcare education'.",
            ]
        )

    if "agent" in query_lower or "llm" in query_lower:
        suggestions.extend(
            [
                "Try related terms such as 'LLM agents'.",
                "Try related terms such as 'multi-agent systems'.",
                "Try related terms such as 'autonomous planning agents'.",
            ]
        )

    return suggestions[:5]


def create_retrieval_note(
    requested_count: int,
    retrieved_count: int,
    query: str,
    used_fallback: bool = False,
) -> str:
    """
    Create a clear note about retrieval coverage.

    This helps the user understand whether the available evidence is complete,
    limited, or affected by an external service issue.
    """
    if used_fallback:
        suggestions = suggest_related_topics(query)
        suggestion_text = "\n".join(f"- {suggestion}" for suggestion in suggestions)

        return (
            f"Retrieval note: The system could not retrieve live arXiv records because "
            f"the external service failed or was unavailable. Fallback records were used "
            f"only to demonstrate the pipeline.\n\nSuggested next searches:\n{suggestion_text}"
        )

    if retrieved_count >= requested_count:
        return (
            f"Retrieval note: The system retrieved the requested number of papers "
            f"({retrieved_count}/{requested_count})."
        )

    suggestions = suggest_related_topics(query)
    suggestion_text = "\n".join(f"- {suggestion}" for suggestion in suggestions)

    return (
        f"Retrieval note: The system retrieved fewer papers than requested "
        f"({retrieved_count}/{requested_count}). This may happen when the query is too narrow, "
        f"when arXiv has limited coverage for the topic, or when only a small number of highly "
        f"relevant records are available.\n\nSuggested next searches:\n{suggestion_text}"
    )


def retrieve_papers(query: str, max_results: int = 5) -> tuple[list[Paper], str]:
    """
    Retrieve academic papers from arXiv.

    arXiv was selected for the prototype because it provides free access to
    academic metadata without requiring an API key. This keeps the system
    reproducible for marking and demonstration.

    The retrieval step includes exception handling because external APIs can
    fail, rate limit, or return temporary server errors. When that happens, the
    system returns clearly labelled fallback records instead of crashing.
    """
    if not query or not query.strip():
        raise ValueError("A research query is required for retrieval.")

    try:
        client = arxiv.Client(
            page_size=max_results,
            delay_seconds=3,
            num_retries=2,
        )

        search = arxiv.Search(
            query=query.strip(),
            max_results=max_results,
            sort_by=arxiv.SortCriterion.Relevance,
        )

        papers = []

        for result in client.results(search):
            papers.append(
                Paper(
                    title=result.title,
                    authors=[author.name for author in result.authors],
                    abstract=result.summary,
                    url=result.entry_id,
                    published=str(result.published.date()) if result.published else None,
                    source="arXiv",
                )
            )

        retrieval_note = create_retrieval_note(
            requested_count=max_results,
            retrieved_count=len(papers),
            query=query,
        )

        if not papers:
            fallback_papers = get_fallback_papers(query)
            fallback_note = create_retrieval_note(
                requested_count=max_results,
                retrieved_count=len(fallback_papers),
                query=query,
                used_fallback=True,
            )
            return fallback_papers, fallback_note

        return papers, retrieval_note

    except Exception as error:
        print(f"arXiv retrieval failed: {error}")
        print("Using fallback records so the pipeline can continue.")

        fallback_papers = get_fallback_papers(query)
        fallback_note = create_retrieval_note(
            requested_count=max_results,
            retrieved_count=len(fallback_papers),
            query=query,
            used_fallback=True,
        )

        return fallback_papers, fallback_note