from Chains.GPT_Researcher import conduct_research, build_report, DEFAULT_PROFILE_PROMPT
from StateGraph import GraphState, ProfileCandidate
from typing import Any, Dict


async def make_research(state: GraphState) -> Dict[str, Any]:
    """
    Runs one research cycle: conduct_research -> build_report, using the
    config staged in state["chain_input"]. Appends the resulting candidate
    to profile_candidates and bumps research_iteration.
    """
    chain_input = state["chain_input"]

    researcher = await conduct_research(
        query=chain_input["query"],
        report_type=chain_input.get("report_type", "research_report"),
        report_format=chain_input.get("report_format", "APA"),
        tone=chain_input.get(
            "tone",
            "Objective — Impartial and unbiased presentation of facts and findings",
        ),
        max_subtopics=chain_input.get("max_subtopics", 5),
        verbose=chain_input.get("verbose", True),
    )

    result = await build_report(
        researcher,
        custom_prompt=chain_input.get("custom_prompt", DEFAULT_PROFILE_PROMPT),
    )

    candidate: ProfileCandidate = {
        "summary": "",  # filled by a separate summary node/pass if needed
        "full_report": result["report"],
        "conclusion": result["conclusion"],
        "sub_topics": result["subtopics"],
        "sources": result["source_urls"],
        "research_sources": result["research_sources"],
        "costs": result["costs"],
    }

    existing_candidates = state.get("profile_candidates", [])

    return {
        "profile_candidates": existing_candidates + [candidate],
        "research_iteration": state.get("research_iteration", 0) + 1,
    }