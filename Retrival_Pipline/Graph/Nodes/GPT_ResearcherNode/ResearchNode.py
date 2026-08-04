from typing import Any, Dict

from Chains.GPT_Researcher import conduct_multi_agent_research
from StateGraph import GraphState, ProfileCandidate


def _normalize_raw_result(raw_result: Any) -> dict:
    """
    run_research_task() بترجع أشكال مختلفة حسب إزاي الـ pipeline خلص:
    dict عادي، أو list فيها dict، أو string خام (التقرير نفسه بس من غير
    wrapping). الدالة دي بتحول أي شكل منهم لـ dict موحّد نقدر نتعامل معاه.
    """
    if isinstance(raw_result, dict):
        return raw_result
    if isinstance(raw_result, str):
        return {"report": raw_result}
    if isinstance(raw_result, list):
        for item in raw_result:
            if isinstance(item, dict):
                return item
        return {"report": " ".join(str(x) for x in raw_result)}
    return {}


def _as_title(section: Any) -> str:
    if isinstance(section, str):
        return section
    if isinstance(section, dict):
        return section.get("title", "")
    return str(section)


def _extract_section_map(item: Any) -> Dict[str, str]:
    if isinstance(item, dict) and item:
        return item
    if isinstance(item, str):
        return {"unrecognized_section": item}
    return {}


async def make_research(state: GraphState) -> Dict[str, Any]:
    chain_input = state["chain_input"]

    raw_result = await conduct_multi_agent_research(
        query=chain_input["query"],
        max_sections=chain_input.get("max_sections", 5),
        follow_guidelines=chain_input.get("follow_guidelines", True),
        verbose=chain_input.get("verbose", True),
    )

    if raw_result is None:
        raise RuntimeError("run_research_task() رجّع None")

    raw_result = _normalize_raw_result(raw_result)

    section_content: Dict[str, str] = {}
    for item in raw_result.get("research_data", []):
        section_content.update(_extract_section_map(item))

    candidate: ProfileCandidate = {
        "title": raw_result.get("title", ""),
        "summary": "",
        "full_report": raw_result.get("report", ""),
        "introduction": raw_result.get("introduction", ""),
        "conclusion": raw_result.get("conclusion", ""),
        "initial_research": raw_result.get("initial_research", ""),
        "sub_topics": [_as_title(s) for s in raw_result.get("sections", [])],
        "section_content": section_content,
        "table_of_contents": raw_result.get("table_of_contents", ""),
        "sources": raw_result.get("sources", []),
        "costs": raw_result.get("costs", 0.0),
    }

    existing_candidates = state.get("profile_candidates", [])

    return {
        "profile_candidates": existing_candidates + [candidate],
        "research_iteration": state.get("research_iteration", 0) + 1,
    }