from models import ResearchContext, ProcessedPaper, RankedPaper


PURPOSE_KEYWORDS = {
    "course design": {
        "course", "curriculum", "learning", "teaching", "pedagogy", "assessment",
        "education", "students", "instruction", "outcomes", "classroom"
    },
    "literature review": {
        "review", "systematic", "methodology", "findings", "evidence", "gap",
        "limitations", "empirical", "study", "studies", "research"
    },
    "background research": {
        "overview", "introduction", "trend", "trends", "concept", "framework",
        "definition", "general", "field", "background"
    },
    "assignment": {
        "education", "students", "learning", "concept", "framework", "overview",
        "analysis", "example", "application", "research"
    },
    "personal study": {
        "overview", "introduction", "learning", "concept", "explainable",
        "general", "understanding", "application"
    },
}


LEVEL_KEYWORDS = {
    "undergraduate": {"introduction", "overview", "students", "learning", "education"},
    "masters": {"framework", "methodology", "analysis", "evidence", "research"},
    "doctoral": {"methodology", "empirical", "limitations", "gap", "systematic"},
    "professional": {"application", "practice", "implementation", "framework", "guidance"},
    "general audience": {"overview", "introduction", "learning", "understanding"},
}


def normalise_text(text: str) -> set[str]:
    """
    Convert text into a set of lowercase searchable terms.
    """
    cleaned_words = set()

    for word in text.lower().split():
        cleaned = "".join(character for character in word if character.isalnum())
        if cleaned:
            cleaned_words.add(cleaned)

    return cleaned_words


def get_purpose_terms(purpose: str) -> set[str]:
    """
    Return ranking terms associated with the user's research purpose.
    """
    purpose_lower = purpose.lower()

    for label, terms in PURPOSE_KEYWORDS.items():
        if label in purpose_lower:
            return terms

    return set()


def get_level_terms(audience_level: str) -> set[str]:
    """
    Return ranking terms associated with the user's intended audience or level.
    """
    level_lower = audience_level.lower()

    for label, terms in LEVEL_KEYWORDS.items():
        if label in level_lower:
            return terms

    return set()


def calculate_relevance_score(context: ResearchContext, paper: ProcessedPaper) -> tuple[int, str]:
    """
    Calculate relevance as a score out of 10.

    Scoring:
    - Query match: up to 4 points
    - Purpose match: up to 3 points
    - Audience/level match: up to 2 points
    - Source completeness: up to 1 point

    This makes the score easier to explain than an unbounded raw keyword count.
    """
    query_terms = normalise_text(context.query)
    purpose_terms = get_purpose_terms(context.purpose)
    level_terms = get_level_terms(context.audience_level)

    paper_terms = normalise_text(
        " ".join(
            [
                paper.title,
                paper.summary,
                " ".join(paper.key_terms),
            ]
        )
    )

    query_matches = query_terms.intersection(paper_terms)
    purpose_matches = purpose_terms.intersection(paper_terms)
    level_matches = level_terms.intersection(paper_terms)

    query_score = min(len(query_matches), 4)
    purpose_score = min(len(purpose_matches), 3)
    level_score = min(len(level_matches), 2)

    source_score = 1 if paper.url and paper.source.lower() != "fallback" else 0

    total_score = query_score + purpose_score + level_score + source_score

    reason_parts = [
        f"query match {query_score}/4",
        f"purpose match {purpose_score}/3",
        f"audience match {level_score}/2",
        f"source completeness {source_score}/1",
    ]

    reason = "Score based on " + ", ".join(reason_parts) + "."

    return total_score, reason


def rank_papers(context: ResearchContext, processed_papers: list[ProcessedPaper]) -> list[RankedPaper]:
    """
    Rank processed papers by relevance to the user's topic, purpose, and audience.
    """
    ranked_papers = []

    for paper in processed_papers:
        score, reason = calculate_relevance_score(context, paper)

        ranked_papers.append(
            RankedPaper(
                title=paper.title,
                summary=paper.summary,
                key_terms=paper.key_terms,
                url=paper.url,
                source=paper.source,
                relevance_score=score,
                relevance_reason=reason,
            )
        )

    return sorted(ranked_papers, key=lambda paper: paper.relevance_score, reverse=True)


def assess_evidence_consistency(context: ResearchContext, ranked_papers: list[RankedPaper]) -> str:
    """
    Provide an evidence consistency note.

    The system does not claim to automatically resolve truth. It preserves
    source-level summaries and gives the user a warning when evidence is weak,
    limited, or peripheral.
    """
    if not ranked_papers:
        return "No evidence was retrieved, so no consistency assessment could be made."

    fallback_count = sum(1 for paper in ranked_papers if paper.source.lower() == "fallback")
    strong_count = sum(1 for paper in ranked_papers if paper.relevance_score >= 7)
    moderate_count = sum(1 for paper in ranked_papers if 4 <= paper.relevance_score < 7)

    if fallback_count > 0:
        return (
            "Evidence is limited because fallback records were used after a retrieval failure. "
            "The output should be treated as a system demonstration, not a final research finding."
        )

    if strong_count >= 3:
        return (
            f"Evidence appears strong for the purpose of {context.purpose} at the "
            f"{context.audience_level} level. Several retrieved papers closely match the topic "
            "and purpose. Source-level summaries are still preserved for human review."
        )

    if strong_count >= 1 or moderate_count >= 3:
        return (
            f"Evidence appears moderately useful for {context.purpose} at the "
            f"{context.audience_level} level. Some papers are relevant, but others may be "
            "peripheral. Human review is recommended before drawing firm conclusions."
        )

    return (
        f"Evidence appears weak or mixed for {context.purpose} at the "
        f"{context.audience_level} level. The retrieved papers do not strongly match the full "
        "research context, so the system avoids producing a single confident conclusion."
    )