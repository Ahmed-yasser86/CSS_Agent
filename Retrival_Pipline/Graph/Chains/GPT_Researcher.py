import os
import sys
import importlib
import inspect

# Prefer the local forked copy of the repo (not the installed package).
# Add the local gpt-researcher root to sys.path so Python resolves the local package.
LOCAL_GPT_RESEARCHER = os.path.abspath(r"C:\Users\DELL\graph-rag-agent\gpt-researcher")
if LOCAL_GPT_RESEARCHER not in sys.path:
    sys.path.insert(0, LOCAL_GPT_RESEARCHER)

try:
    from multi_agents.agents import ChiefEditorAgent
    m = importlib.import_module("multi_agents.agents")
    print("Using ChiefEditorAgent from:", inspect.getsourcefile(m))
except ImportError as exc:
    raise ImportError(
        f"Failed to import ChiefEditorAgent from local gpt_researcher fork at {LOCAL_GPT_RESEARCHER}. "
        "Make sure the local repo path is correct and that the fork contains the expected multi_agents package."
    ) from exc

detailed1_guidelines = [
    "EVIDENCE FIRST: Collect sufficient evidence from diverse sources before attempting analysis. Rely on observations of audience behavior, not just the subject's claims.",
    "EXTRACT, DO NOT DESCRIBE: Prioritize structured knowledge extraction (patterns, mechanisms, rules) over chronological narrative or descriptive text.",
    "CAUSAL FOCUS: Explain the relationship between the subject's ideas, audience composition, communication style, and observed influence.",
]

detailed2_guidelines = [
    "Do not write a conventional biography.",
    "The primary objective is to build a Digital Twin of the subject and the audience ecosystem surrounding them.",
    "Treat the subject as an influence source and the audience as the primary system being modeled.",
    "Prioritize structured knowledge extraction over narrative writing.",
    "Identify recurring behavioral, ideological, cultural, communicative, and social patterns rather than isolated events.",
    "Extract reusable knowledge suitable for behavioral simulation rather than descriptive summaries.",
    "Reverse engineer the subject's worldview, ideology, epistemology, philosophy, methodology, and system of thought.",
    "Identify the beliefs, values, assumptions, priorities, and recurring principles that consistently shape the subject's discourse.",
    "Determine which ideas define the subject's public identity and which themes dominate their communication.",
    "Analyze how the subject justifies truth, authority, evidence, morality, religion, politics, society, identity, and social order.",
    "Carefully analyze ideological characteristics supported by evidence, including conservatism, liberalism, progressivism, nationalism, populism, sectarianism, exclusivism, traditionalism, reformism, political mobilization, religious fundamentalism, extremism, discrimination, conspiracy narratives, or similar recurring patterns whenever applicable.",
    "Do not assign ideological labels unless supported by multiple independent pieces of evidence.",
    "Carefully analyze the subject's positions regarding religion, politics, democracy, secularism, women, gender roles, minorities, human rights, violence, extremism, education, social norms, and other major societal issues whenever sufficient evidence exists.",
    "Identify which ideas generate the strongest support, criticism, polarization, or controversy.",
    "Treat the audience as a complex social system rather than a list of followers.",
    "Identify audience demographics, ideological tendencies, education, geography, religiosity, socioeconomic characteristics, motivations, and cultural background whenever evidence exists.",
    "Reverse engineer why different audience groups trust, reject, defend, or criticize the subject.",
    "Analyze audience values, identities, fears, aspirations, moral intuitions, and cultural assumptions whenever observable evidence exists.",
    "Analyze how different audience segments react to specific ideas rather than only measuring engagement.",
    "Identify which ideas resonate most strongly with which communities and explain why.",
    "Analyze disagreement inside the audience whenever multiple communities interpret the subject differently.",
    "Analyze how ideas spread through books, lectures, institutions, YouTube, television, social media, personal networks, communities, organizations, and other dissemination mechanisms.",
    "Explain the interaction between ideology, communication style, audience composition, dissemination channels, and observable influence rather than describing each independently.",
    "Analyze rhetorical style, framing strategies, narratives, symbolism, emotional appeals, authority construction, persuasive techniques, storytelling, and educational methods.",
    "Identify recurring messaging patterns and communication strategies.",
    "Map important allies, critics, competing schools of thought, rival influencers, institutions, organizations, media ecosystems, and communities interacting with the subject."
]

detailed_guidelines = detailed1_guidelines + detailed2_guidelines

def _resolve_model_from_env() -> str | None:
    """
    نفس المنطق بالظبط اللي في multi_agents/main.py's open_task() -
    يقرأ STRATEGIC_LLM من .env ويستخرج اسم الموديل بعد النقطتين
    (مثال: "openai:moonshotai/Kimi-K2.6" -> "moonshotai/Kimi-K2.6").
    من غير ده، task["model"] بترجع None ويظهر خطأ "Model cannot be None".
    """
    strategic_llm = os.environ.get("STRATEGIC_LLM")
    if not strategic_llm:
        return None
    if ":" in strategic_llm:
        return strategic_llm.split(":", 1)[1]
    return strategic_llm


async def conduct_multi_agent_research(
    query: str,
    max_sections: int = 5,
    follow_guidelines: bool = True,
    guidelines: list[str]=detailed_guidelines,
    verbose: bool = True,
) -> dict:
    """
    يشغّل الـ multi-agent pipeline بالكامل:
    Browser -> Editor -> Researcher -> Reviewer -> Revisor -> Writer -> Publisher
    ويرجع النتيجة الخام زي ما بترجع من run_research_task().

    مهم: خلي query قصير (تحت ~400 حرف) لأنه بيتبعت لـ Tavily search
    داخليًا وTavily بيرفض أي query أطول من 400 حرف بـ 400 Bad Request.
    التفاصيل الطويلة والمحاور المطلوبة تتحط في guidelines بدل query.
    """
    task = {
        "query": query,
        "max_sections": max_sections,
        "publish_formats": {"markdown": True},
        "include_human_feedback": False,
        "follow_guidelines": follow_guidelines,
        "guidelines": guidelines or [],
        "verbose": verbose,
    }

    model = _resolve_model_from_env()
    if model:
        task["model"] = model

    chief_editor = ChiefEditorAgent(task)
    research_report: dict = await chief_editor.run_research_task()
    return research_report