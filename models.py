from typing import List, Optional
from pydantic import BaseModel, Field


class ResearchContext(BaseModel):
    """
    Stores the user's research goal and context.

    This gives the planning and ranking agents more information than a topic alone.
    Relevance is therefore judged against the user's purpose and audience, not only
    against keyword overlap.
    """
    query: str
    purpose: str
    audience_level: str
    requested_papers: int


class ResearchPlan(BaseModel):
    """
    Structured plan created by the Planning Agent.

    Pydantic validates the shape of the agent output. It does not verify whether
    research claims are factually true.
    """
    query: str
    purpose: str
    audience_level: str
    steps: List[str]


class Paper(BaseModel):
    """
    Standard structure for an academic paper retrieved by the system.
    """
    title: str
    authors: List[str] = Field(default_factory=list)
    abstract: str
    url: str
    published: Optional[str] = None
    source: str = "arXiv"
    citation_count: Optional[int] = None
    publication_type: Optional[str] = None


class ProcessedPaper(BaseModel):
    """
    Source-level summary of a paper.
    """
    title: str
    summary: str
    key_terms: List[str]
    paper_type: str
    url: str
    source: str
    citation_count: Optional[int] = None
    publication_type: Optional[str] = None


class RankedPaper(ProcessedPaper):
    relevance_score: int
    relevance_reason: str
    recommendation_status: str


class ResearchReport(BaseModel):
    """
    Final structured output created by ResearchMate.
    """
    query: str
    purpose: str
    audience_level: str
    plan: List[str]
    ranked_papers: List[RankedPaper]
    retrieval_note: str
    evidence_note: str