import sqlite3

from models import ResearchContext, ResearchPlan, RankedPaper
from agents.database_agent import initialise_database, save_run_to_database


def test_initialise_database_creates_database_file(tmp_path):
    """
    Test that the database file is created successfully.
    """
    db_file = tmp_path / "researchmate_test.db"

    saved_path = initialise_database(str(db_file))

    assert db_file.exists()
    assert saved_path == str(db_file)


def test_initialise_database_creates_required_tables(tmp_path):
    """
    Test that all required tables are created.
    """
    db_file = tmp_path / "researchmate_test.db"

    initialise_database(str(db_file))

    connection = sqlite3.connect(db_file)
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT name
        FROM sqlite_master
        WHERE type='table'
        """
    )

    table_names = {
        row[0]
        for row in cursor.fetchall()
    }

    connection.close()

    assert "research_runs" in table_names
    assert "research_plan_steps" in table_names
    assert "ranked_papers" in table_names


def test_save_run_to_database_creates_records(tmp_path):
    """
    Test that a complete ResearchMate run is saved to the database.
    """
    db_file = tmp_path / "researchmate_test.db"

    context = ResearchContext(
        query="AI tutors in higher education",
        purpose="course design",
        audience_level="masters",
        requested_papers=1,
    )

    plan = ResearchPlan(
        query=context.query,
        purpose=context.purpose,
        audience_level=context.audience_level,
        steps=[
            "Retrieve papers.",
            "Process papers.",
            "Rank papers.",
        ],
    )

    ranked_papers = [
        RankedPaper(
            title="AI Tutors in Higher Education",
            summary="This paper discusses AI tutors and higher education.",
            key_terms=["ai", "tutors", "higher education"],
            paper_type="Review / survey paper",
            url="https://arxiv.org/example",
            source="arXiv",
            citation_count=12,
            publication_type="Review",
            relevance_score=8,
            relevance_reason="This paper is relevant to course design.",
            recommendation_status="Strongly recommended",
        )
    ]

    saved_path = save_run_to_database(
        context=context,
        plan=plan,
        ranked_papers=ranked_papers,
        retrieval_note="Retrieved requested papers.",
        evidence_note="Evidence appears useful.",
        db_path=str(db_file),
    )

    assert saved_path == str(db_file)

    connection = sqlite3.connect(db_file)
    cursor = connection.cursor()

    cursor.execute("SELECT COUNT(*) FROM research_runs")
    run_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM research_plan_steps")
    step_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM ranked_papers")
    paper_count = cursor.fetchone()[0]

    connection.close()

    assert run_count == 1
    assert step_count == 3
    assert paper_count == 1


def test_saved_database_contains_expected_paper_data(tmp_path):
    """
    Test that saved paper data can be read back from SQLite.
    """
    db_file = tmp_path / "researchmate_test.db"

    context = ResearchContext(
        query="LLM agents for academic research",
        purpose="literature review",
        audience_level="masters",
        requested_papers=1,
    )

    plan = ResearchPlan(
        query=context.query,
        purpose=context.purpose,
        audience_level=context.audience_level,
        steps=[
            "Retrieve academic papers.",
            "Process retrieved sources.",
            "Rank papers using the rubric.",
        ],
    )

    ranked_papers = [
        RankedPaper(
            title="LLM Agents for Academic Research",
            summary="This paper discusses LLM agents for research workflows.",
            key_terms=["llm agents", "academic research", "research workflows"],
            paper_type="Methodology / framework paper",
            url="https://example.com/paper",
            source="OpenAlex",
            citation_count=20,
            publication_type="article",
            relevance_score=9,
            relevance_reason="This paper strongly matches the user's literature review purpose.",
            recommendation_status="Strongly recommended",
        )
    ]

    save_run_to_database(
        context=context,
        plan=plan,
        ranked_papers=ranked_papers,
        retrieval_note="Retrieved requested papers.",
        evidence_note="Evidence appears strong.",
        db_path=str(db_file),
    )

    connection = sqlite3.connect(db_file)
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            title,
            source,
            relevance_score,
            recommendation_status
        FROM ranked_papers
        """
    )

    saved_paper = cursor.fetchone()

    connection.close()

    assert saved_paper[0] == "LLM Agents for Academic Research"
    assert saved_paper[1] == "OpenAlex"
    assert saved_paper[2] == 9
    assert saved_paper[3] == "Strongly recommended"