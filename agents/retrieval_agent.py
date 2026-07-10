import arxiv
import requests

from models import Paper


def get_fallback_papers(query: str) -> list[Paper]:
    """
    Provide fallback paper-like records when external services fail.

    These records are not real research evidence. They allow the rest of the
    pipeline to be demonstrated and tested when live academic APIs are unavailable.
    """
    return [
        Paper(
            title=f"Fallback result: AI-supported learning related to {query}",
            authors=["ResearchMate fallback dataset"],
            abstract=(
                "This fallback record represents a placeholder academic source. "
                "It allows the processing, ranking, and storage agents to continue "
                "running when live retrieval services are unavailable."
            ),
            url="https://arxiv.org/",
            published=None,
            source="Fallback",
            citation_count=None,
            publication_type="Fallback",
        ),
        Paper(
            title=f"Fallback result: Intelligent tutoring systems and {query}",
            authors=["ResearchMate fallback dataset"],
            abstract=(
                "This fallback record is used only for system demonstration. "
                "It should be replaced by live academic results when retrieval "
                "services are available."
            ),
            url="https://arxiv.org/",
            published=None,
            source="Fallback",
            citation_count=None,
            publication_type="Fallback",
        ),
    ]


def reconstruct_openalex_abstract(abstract_inverted_index: dict | None) -> str:
    """
    Reconstruct an OpenAlex abstract from its inverted-index format.

    OpenAlex often returns abstracts as an inverted index rather than a plain
    text string. This function rebuilds a readable abstract when possible.
    """
    if not abstract_inverted_index:
        return "No abstract available from OpenAlex."

    word_positions = []

    for word, positions in abstract_inverted_index.items():
        for position in positions:
            word_positions.append((position, word))

    if not word_positions:
        return "No abstract available from OpenAlex."

    sorted_words = [
        word
        for _, word in sorted(word_positions, key=lambda item: item[0])
    ]

    return " ".join(sorted_words)


def suggest_related_topics(query: str) -> list[str]:
    """
    Suggest broader or related search directions when retrieval is limited.
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
    sources_used: list[str],
    used_fallback: bool = False,
) -> str:
    """
    Create a clear note about retrieval coverage.
    """
    source_text = ", ".join(sorted(set(sources_used))) if sources_used else "none"

    if used_fallback:
        suggestions = suggest_related_topics(query)
        suggestion_text = "\n".join(f"- {suggestion}" for suggestion in suggestions)

        return (
            "Retrieval note: The system could not retrieve enough live academic records "
            "because the external retrieval services failed or returned limited results. "
            "Fallback records were used only to demonstrate the pipeline.\n\n"
            f"Sources attempted: {source_text}\n\n"
            f"Suggested next searches:\n{suggestion_text}"
        )

    if retrieved_count >= requested_count:
        return (
            f"Retrieval note: The system retrieved the requested number of papers "
            f"({retrieved_count}/{requested_count}) using: {source_text}."
        )

    suggestions = suggest_related_topics(query)
    suggestion_text = "\n".join(f"- {suggestion}" for suggestion in suggestions)

    return (
        f"Retrieval note: The system retrieved fewer papers than requested "
        f"({retrieved_count}/{requested_count}). This may happen when the query is too narrow, "
        "when academic sources have limited coverage for the topic, or when external APIs "
        "return incomplete results.\n\n"
        f"Sources used: {source_text}\n\n"
        f"Suggested next searches:\n{suggestion_text}"
    )


def retrieve_arxiv_papers(query: str, max_results: int) -> list[Paper]:
    """
    Retrieve papers from arXiv.
    """
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
                citation_count=None,
                publication_type=None,
            )
        )

    return papers


def retrieve_semantic_scholar_papers(query: str, max_results: int) -> list[Paper]:
    """
    Retrieve papers from Semantic Scholar.

    Semantic Scholar is used as a second academic source because it can provide
    citation counts and publication type metadata where available.
    """
    url = "https://api.semanticscholar.org/graph/v1/paper/search"

    params = {
        "query": query.strip(),
        "limit": max_results,
        "fields": "title,abstract,url,year,authors,citationCount,publicationTypes",
    }

    response = requests.get(url, params=params, timeout=20)
    response.raise_for_status()

    data = response.json().get("data", [])

    papers = []

    for item in data:
        title = item.get("title") or "Untitled Semantic Scholar result"
        abstract = item.get("abstract") or "No abstract available from Semantic Scholar."
        authors = [author.get("name", "Unknown Author") for author in item.get("authors", [])]
        publication_types = item.get("publicationTypes") or []

        papers.append(
            Paper(
                title=title,
                authors=authors,
                abstract=abstract,
                url=item.get("url") or "https://www.semanticscholar.org/",
                published=str(item.get("year")) if item.get("year") else None,
                source="Semantic Scholar",
                citation_count=item.get("citationCount"),
                publication_type=", ".join(publication_types) if publication_types else None,
            )
        )

    return papers


def retrieve_openalex_papers(query: str, max_results: int) -> list[Paper]:
    """
    Retrieve papers from OpenAlex.

    OpenAlex adds a third academic metadata source and can provide citation
    counts, publication years, work types, DOI links, and reconstructed abstracts.
    """
    url = "https://api.openalex.org/works"

    params = {
        "search": query.strip(),
        "per-page": max_results,
        "select": (
            "display_name,authorships,abstract_inverted_index,id,doi,"
            "publication_year,cited_by_count,type"
        ),
    }

    response = requests.get(url, params=params, timeout=20)
    response.raise_for_status()

    results = response.json().get("results", [])

    papers = []

    for item in results:
        title = item.get("display_name") or "Untitled OpenAlex result"

        authors = []
        for authorship in item.get("authorships", []):
            author = authorship.get("author", {})
            author_name = author.get("display_name")

            if author_name:
                authors.append(author_name)

        abstract = reconstruct_openalex_abstract(
            item.get("abstract_inverted_index")
        )

        doi = item.get("doi")
        openalex_id = item.get("id")
        url_value = doi or openalex_id or "https://openalex.org/"

        papers.append(
            Paper(
                title=title,
                authors=authors,
                abstract=abstract,
                url=url_value,
                published=str(item.get("publication_year")) if item.get("publication_year") else None,
                source="OpenAlex",
                citation_count=item.get("cited_by_count"),
                publication_type=item.get("type"),
            )
        )

    return papers


def deduplicate_papers(papers: list[Paper]) -> list[Paper]:
    """
    Deduplicate papers by normalised title.

    Multi-source retrieval can return the same paper from different services.
    Deduplication keeps the final output concise and avoids double-counting.
    """
    seen_titles = set()
    unique_papers = []

    for paper in papers:
        title_key = paper.title.lower().strip()

        if title_key not in seen_titles:
            seen_titles.add(title_key)
            unique_papers.append(paper)

    return unique_papers


def select_balanced_papers(papers: list[Paper], max_results: int) -> list[Paper]:
    """
    Select papers in a balanced way across retrieval sources.

    Without this, one source such as arXiv can dominate the final result list.
    Balanced selection gives Semantic Scholar and OpenAlex a fair chance to
    contribute useful sources.
    """
    papers_by_source = {}

    for paper in papers:
        papers_by_source.setdefault(paper.source, []).append(paper)

    selected_papers = []
    source_names = list(papers_by_source.keys())

    while len(selected_papers) < max_results:
        added_this_round = False

        for source_name in source_names:
            source_papers = papers_by_source[source_name]

            if source_papers:
                selected_papers.append(source_papers.pop(0))
                added_this_round = True

                if len(selected_papers) >= max_results:
                    break

        if not added_this_round:
            break

    return selected_papers


def clean_retrieval_errors(errors: list[str]) -> list[str]:
    """
    Convert technical retrieval errors into presentation-friendly warnings.
    """
    cleaned_errors = []

    for error in errors:
        if "429" in error:
            cleaned_errors.append(
                "One retrieval source was rate-limited during this run, so the system continued using available results from other sources."
            )
        else:
            cleaned_errors.append(error)

    return cleaned_errors


def retrieve_papers(query: str, max_results: int = 5) -> tuple[list[Paper], str]:
    """
    Retrieve academic papers from arXiv, Semantic Scholar, and OpenAlex.

    The function attempts multiple sources so that the prototype is closer to the
    original ResearchMate design while still remaining simple enough to run and test.
    """
    if not query or not query.strip():
        raise ValueError("A research query is required for retrieval.")

    all_papers = []
    sources_attempted = []
    errors = []

    try:
        arxiv_papers = retrieve_arxiv_papers(query, max_results)
        all_papers.extend(arxiv_papers)
        sources_attempted.append("arXiv")
    except Exception as error:
        errors.append(f"arXiv failed: {error}")

    try:
        semantic_papers = retrieve_semantic_scholar_papers(query, max_results)
        all_papers.extend(semantic_papers)
        sources_attempted.append("Semantic Scholar")
    except Exception as error:
        errors.append(f"Semantic Scholar failed: {error}")

    try:
        openalex_papers = retrieve_openalex_papers(query, max_results)
        all_papers.extend(openalex_papers)
        sources_attempted.append("OpenAlex")
    except Exception as error:
        errors.append(f"OpenAlex failed: {error}")

    unique_papers = deduplicate_papers(all_papers)
    selected_papers = select_balanced_papers(unique_papers, max_results)

    if not selected_papers:
        for error in errors:
            print(error)

        fallback_papers = get_fallback_papers(query)
        fallback_note = create_retrieval_note(
            requested_count=max_results,
            retrieved_count=len(fallback_papers),
            query=query,
            sources_used=sources_attempted or ["arXiv", "Semantic Scholar", "OpenAlex"],
            used_fallback=True,
        )
        return fallback_papers, fallback_note

    retrieval_note = create_retrieval_note(
        requested_count=max_results,
        retrieved_count=len(selected_papers),
        query=query,
        sources_used=sources_attempted,
    )

    if errors:
        cleaned_errors = clean_retrieval_errors(errors)
        retrieval_note += "\n\nRetrieval warnings:\n" + "\n".join(
            f"- {error}" for error in cleaned_errors
        )

    return selected_papers, retrieval_note