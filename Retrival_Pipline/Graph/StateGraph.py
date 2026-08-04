from typing import Optional, TypedDict

from pydantic import BaseModel, Field

class ProfileCandidate(TypedDict):
    """A single candidate profile generated for a research query."""
    title: str
    summary: str
    full_report: str
    introduction: str
    conclusion: str
    initial_research: str
    sub_topics: list[str]
    section_content: dict[str, str]
    table_of_contents: str
    sources: list[str]
    costs: float



class CompressedIntelligence(TypedDict):
    """Structured compression of a Subject Intelligence Report."""

    covered_topics: str
    confirmed_positions: str
    gaps_and_unknowns: str
    ecosystem_research_instructions: str



class ChainInput(TypedDict, total=False):
    """Input config for the research chain."""
    query: str
    max_sections: int
    follow_guidelines: bool
    guidelines: list[str]
    verbose: bool


class IdentityData(TypedDict, total=False):
    """Verified identity anchors data structure."""
    report: str
    """Verified identity anchors report from the identity research node."""
    sources: list[str]
    """Source URLs used for identity verification."""
    research_sources: list[dict]
    """Richer source data for identity facts."""
    costs: float
    """Cost of the identity research pass."""
    subtopics: list[str]
    """Subtopics explored during identity verification."""
    
    needs_reprocessing: bool 
    """Boolean flag to check if the user requested to re-run the research."""
    feedback_notes: str
    """The specific feedback or extra details provided by the user for the next search pass."""

class GraphState(TypedDict, total=False):
    """State shared across the graph."""
    user_initial_query: str
    chain_input: ChainInput
    profile_candidates: list[ProfileCandidate]
    selected_profile: Optional[ProfileCandidate]
    needs_more_research: bool
    feedback_notes: Optional[str]
    research_iteration: int
    compressed_intelligence: CompressedIntelligence
    identity_data: IdentityData