from typing import Any, Dict, TypedDict
from langchain.chat_models import init_chat_model
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
from Retrival_Pipline.Graph.state import GraphState
from Ingestion_Pipline.config.settings import ChatModelSettings
from Retrival_Pipline.Graph.Chains.ChainUtil import build_chat_model




class CompressedIntelligence(BaseModel):
    """Structured compression of a Subject Intelligence Report."""

    covered_topics: str = Field(
        description="Bullet-point summary of topics already researched and confirmed with evidence."
    )
    confirmed_positions: str = Field(
        description="Key verified positions, beliefs, or patterns extracted from the report."
    )
    gaps_and_unknowns: str = Field(
        description="Topics explicitly missing, marked insufficient, or needing deeper research."
    )
    ecosystem_research_instructions: str = Field(
        description="Specific instructions for the Ecosystem Agent: what to prioritize, what to avoid repeating, and where to go deeper."
    )


llm = build_chat_model()
llm_with_structured_output = llm.with_structured_output(CompressedIntelligence)

system = """
You are an intelligence compression specialist.

You receive a Subject Intelligence Report produced by a research agent.

Your job is to compress it into four structured outputs:

1. COVERED TOPICS
   - List every topic that was researched and has at least .
   - Use short bullet points only. No prose.
   - Format: "- [topic]: [one-line summary]" 

2. CONFIRMED POSITIONS
   - Extract the subject's key verified positions, beliefs, methodologies, and patterns.
   - Use short bullet points only.
   - Format: "- [position or pattern]"

3. GAPS AND UNKNOWNS
   - Also identify topics that were mentioned briefly but not researched in depth.
   - Format: "- [gap topic]: [why it matters]"

4. ECOSYSTEM RESEARCH INSTRUCTIONS
   - Write specific instructions for the next agent (Ecosystem Intelligence Agent).
   - Tell it exactly what NOT to repeat (already covered in Subject Intelligence).
   - Format: numbered instructions.

Rules:
- Be extremely concise. This output will be injected directly into the next agent's context window.
- Do not rewrite the report. Do not add analysis. Compress and instruct only.
- Focus on what the Ecosystem Intelligence Agent should do next, what it should avoid, and which ecosystem questions remain open.
- Do not suggest that the next agent should write a general political philosophy or ideological essay.
- If the report is thin on evidence, say so explicitly in the gaps section.
"""

compress_prompt = ChatPromptTemplate.from_messages([
    ("system", system),
    ("human", "Subject Intelligence Report:\n\n{report}"),
])

intelligence_compressor = compress_prompt | llm_with_structured_output




def compress_subject_intelligence(state: GraphState) -> Dict[str, Any]:
    """
    Compresses the Subject Intelligence Report into structured briefing
    for the Ecosystem Intelligence Agent.

    Args:
        state (dict): Must contain state['subject_intelligence_report']

    Returns:
        state (dict): Adds state['compressed_intelligence']
    """

    report = state.get("subject_intelligence_report", "")

    if not report:
        print("⚠️  No subject_intelligence_report found in state. Skipping compression.")
        return {
            **state,
            "compressed_intelligence": {
                "covered_topics": "",
                "confirmed_positions": "",
                "gaps_and_unknowns": "No report provided.",
                "ecosystem_research_instructions": "Research all layers from scratch.",
            }
        }

    print("⏳ Compressing Subject Intelligence Report...")

    result: CompressedIntelligence = intelligence_compressor.invoke({"report": report})

    compressed = {
        "covered_topics": result.covered_topics,
        "confirmed_positions": result.confirmed_positions,
        "gaps_and_unknowns": result.gaps_and_unknowns,
        "ecosystem_research_instructions": result.ecosystem_research_instructions,
    }

    print("✅ Compression complete.")
    print(f"   Gaps identified: {result.gaps_and_unknowns[:100]}...")

    return {
        **state,
        "compressed_intelligence": compressed,
    }




def format_compressed_for_injection(compressed: dict) -> str:
    """
    Formats the compressed intelligence dict into a clean string
    ready to be injected into the Ecosystem Agent's query.
    """
    return "\n".join([
        "=== SUBJECT INTELLIGENCE BRIEFING ===",
        "",
        "ALREADY COVERED (do not repeat):",
        compressed.get("covered_topics", ""),
        "",
        "CONFIRMED POSITIONS (use as established context):",
        compressed.get("confirmed_positions", ""),
        "",
        "GAPS TO RESEARCH DEEPER:",
        compressed.get("gaps_and_unknowns", ""),
        "",
        "SPECIFIC INSTRUCTIONS FOR THIS RUN:",
        compressed.get("ecosystem_research_instructions", ""),
        "",
        "AVOID THIS FOR THE NEXT AGENT:",
        "- Do not write generic political theory, broad ideology analysis, or abstract philosophy unrelated to this subject's audience ecosystem.",
        "- Do not repeat the subject intelligence analysis as a standalone ideology report.",
        "- Stay focused on observable ecosystem dynamics, audience behavior, opposition, influence channels, and simulation rules.",
        "",
        "=====================================",
    ])