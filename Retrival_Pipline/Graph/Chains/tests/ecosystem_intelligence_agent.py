import asyncio
import os
import sys
from dotenv import load_dotenv
from Nodes.GPT_ResearcherNode.ResearchNode import make_research
from StateGraph import GraphState

TESTS_DIR = os.path.dirname(__file__)
if TESTS_DIR not in sys.path:
    sys.path.insert(0, TESTS_DIR)

# from guidelines import shared_guidelines
from Nodes.research_compressor_node import compress_subject_intelligence, format_compressed_for_injection

load_dotenv()

# ============================================================
# LAYERS - ECOSYSTEM ONLY
# ============================================================
# -*- coding: utf-8 -*-

shared_guidelines = [
    # ============================================================
    # ORIGINAL GUIDELINES (UNCHANGED)
    # ============================================================
    
    "Collect evidence from multiple independent sources before drawing any conclusion. ",
    "A minimum of three independent sources is required before treating any claim as established.",

    "Every factual claim must be traceable to a specific source. ",
    "If a source cannot be identified, mark the claim explicitly as [UNVERIFIED] and do not present it as fact.",

    "Direct quotations require a direct URL or document reference to the exact source. ",
    "If the original text or recording cannot be located, do not quote — paraphrase with source attribution instead.",

    "Separate the subject's own stated positions from descriptions, labels, or accusations ",
    "made by supporters, critics, media outlets, or third parties. ",
    "Never present external characterizations as established facts about the subject.",

    "Prefer reconstructing the subject's worldview from their own recurring statements, ",
    "writings, speeches, lectures, and documented works — not from how opponents or supporters describe them.",

    "Do not assign ideological labels  ",
    "unless the subject has explicitly self-identified with that label, ",
    "or the label is supported by at least three independent and reliable sources ",
    "that provide specific behavioral or textual evidence — not mere association or accusation.",

    "Treat ideological classification as a conclusion to be earned by evidence, not a starting assumption. ",
    "When evidence is insufficient for a label, describe observable positions and patterns instead.",

    "Build a broad and representative map of the subject's recurring ideas, positions, and works ",
    "before analyzing individual examples. ",
    "Do not allow one or two high-profile or viral incidents to dominate the analysis.",

    "If a particular event or statement appears more than twice across different sections, ",
    "this is a signal of over-reliance. Actively seek additional independent examples ",
    "to represent the same pattern before continuing.",

    "Distinguish between a subject's foundational recurring positions ",
    "and isolated statements made in specific contexts. ",
    "Weight recurring patterns significantly higher than single incidents.",

    "Explicitly mark the epistemic status of every major claim using one of: ",
    "[VERIFIED], [STRONG EVIDENCE], [REASONABLE INFERENCE], or [INSUFFICIENT EVIDENCE]. ",
    "Never present inference as verified fact.",

    "Audience demographics, motivations, and psychological profiles are almost always inferred. ",
    "Label them clearly as [INFERRED FROM PATTERNS] and identify what observable evidence the inference is based on.",

    "Prioritize primary sources: the subject's own content, books, lectures, interviews, ",
    "and documented statements. Secondary sources (news articles, Wikipedia, advocacy organizations) ",
    "are supporting evidence only — never the sole basis for a major claim.",

    "If primary sources on a topic cannot be found, explicitly state: ",
    "'Primary source not located. The following is based on secondary reporting.' ",
    "Do not silently substitute secondary sources for primary ones.",

    "When only secondary sources are available, assess and state their reliability. ",
    "Advocacy organizations, political opponents, and state media each carry specific biases ",
    "that must be acknowledged when their reporting is used.",

    "When two or more sources conflict on any fact, present all versions explicitly, ",
    "identify each source, and flag the conflict. Never silently resolve a conflict by choosing one version.",

    "Do not omit a section because information is unavailable. ",
    "Instead write: 'Insufficient reliable evidence found on this topic.' ",
    "Visible gaps are more valuable than silent omissions.",

    "Prioritize structured knowledge extraction over narrative writing. ",
    "The output should read as an intelligence document, not a biography or an essay.",

    "Avoid repeating the same information across multiple sections. ",
    "Each section must contribute new knowledge. ",
    "If a point was already established, reference it — do not restate it.",

    "Produce findings that can support downstream intelligence analysis, ",
    "knowledge graphs, behavioral simulation, and Digital Twin construction.",
    
    "IMPORTANT: This report will be ingested directly into a Retrieval-Augmented Generation (RAG) knowledge base. Every unnecessary sentence reduces retrieval quality.",

    "Start immediately with the first requested section heading. Never write an introduction, overview, executive summary, preface, opening paragraph, or any contextual lead-in.",

    "Do not generate any conclusion, closing remarks, summary, final thoughts, recommendations, or wrap-up section under any circumstance.",

    "The report must end immediately after the final requested section. Do not append any closing sentence or transition.",

    "Never add filler or connective phrases such as 'In conclusion', 'Overall', 'To summarize', 'This report examines', 'The above shows', 'Finally', or similar narrative transitions.",

    "Output only the explicitly requested sections in the specified order. Do not create additional headings or explanatory sections.",

    "Do not write for human readability or essay style. Write for machine retrieval, indexing, and knowledge extraction.",

    "Every paragraph must contain factual, retrievable information. Remove any sentence that does not introduce new knowledge.",

    "Do not include stylistic, rhetorical, or narrative text. Any sentence that does not improve retrieval precision is considered an error.",

    "The report is a structured knowledge artifact, not an article, report, or essay. Treat every token as part of a future RAG corpus.",


    # ============================================================
    # ADDITIONAL GUIDELINES (Concise Anti-Hallucination)
    # ============================================================
    
    "CRITICAL RULE: Do not generate, estimate, or invent any percentage, statistic, or numerical figure unless explicitly stated in a directly cited source. A number without a direct citation is a hallucination.",

    "When quantitative data is unavailable, use descriptive language: 'commonly observed', 'frequently appears', 'recurring pattern' instead of percentages. Label as [INFERRED FROM PATTERNS] and specify the evidence base.",

    "Every statistic must be traceable to: (a) specific source document, (b) page/table/question number, (c) direct URL. If any missing → [UNVERIFIED].",

    "For every claim about what an organization published, verify the organization's scope matches the claim. Survey organizations do not classify respondents by affiliation with specific individuals. Human rights organizations do not publish comparative fiqh studies. Scope mismatch → [UNVERIFIED].",

    "Do not present comparative statistics (X% vs Y%) unless both numbers come from the same study with same methodology, same group definitions, and direct citation. Otherwise state: 'No quantitative comparison available.'",

    "Before citing any source, verify: (1) source exists, (2) source contains the claim, (3) source scope is appropriate. If any check fails → do not use.",

    "When evidence contradicts a claim, present all versions explicitly with sources. Never silently resolve conflicts by choosing one version.",
]

controversy_opposition_layer = {
    "name": "Controversy & Opposition Intelligence",
    "objective": (
        "Understand the major sources of disagreement, criticism, opposition, "
        "and competing narratives surrounding the subject."
    ),
    "extraction_tasks": [
        "Identify the subject's principal critics, competitors, and opposing communities.",
        "Identify the major sources of disagreement, criticism, or public controversy.",
        "Explain which ideas, positions, or actions generate the strongest support and opposition.",
        "Analyze competing narratives and alternative interpretations presented by different groups.",
        "Identify recurring criticisms directed at the subject and evaluate the evidence supporting them.",
        "Analyze how the subject responds to criticism, disagreement, or public controversy.",
        "Explain how supporters, critics, and neutral observers interpret the same events differently.",
        "Identify recurring patterns of polarization, alliance formation, and conflict within the surrounding ecosystem.",
    ],
}

audience_community_layer = {
    "name": "Audience & Community Layer",
    "objective": "Understand who composes the audience, why they participate, how communities form, and how engagement evolves over time.",
    "extraction_tasks": [
        "Identify the major audience segments and characterize them by demographics, education, and socioeconomic background. Clearly mark demographic claims as [INFERRED] when not based on direct data.",
        "Explain why each segment is attracted to the subject, what psychological needs are fulfilled, and how engagement differs across groups.",
        "Extract the shared cultural norms, moral priorities, identity markers, and assumptions characterizing the audience ecosystem.",
        "Identify formal and informal community structures, influential followers, and secondary influencers.",
        "Determine how trust develops, how newcomers integrate, and how long-term members differ from casual consumers.",
        "Analyze how disagreement, controversy, or conflicting interpretations are handled within the community.",
        "Extract shared language, terminology, symbols, and recurring narratives used by followers.",
    ],
}

influence_layer = {
    "name": "Influence Intelligence",
    "objective": (
        "Understand how the subject generates influence, shapes public discourse, "
        "and affects individuals, communities, and institutions."
    ),
    "extraction_tasks": [
        "Identify the subject's primary sources of influence and authority.",
        "Analyze how influence is established, maintained, and expanded over time.",
        "Identify the communities, institutions, organizations, or networks most affected by the subject.",
        "Explain how the subject influences beliefs, attitudes, behaviors, or decision-making.",
        "Identify ideas or narratives that have produced measurable public impact. Provide at least three distinct examples from different domains or time periods.",
        "Analyze the factors that strengthen, weaken, or limit the subject's influence.",
        "Identify recurring patterns of trust, credibility, reputation, and authority that reinforce long-term influence.",
        "Distinguish direct influence from indirect influence through followers, organizations, or secondary influencers.",
    ],
}

network_structure_layer = {
    "name": "Network Structure Layer",
    "objective": (
        "Map the ecosystem's key institutions, influencers, communities, and dissemination channels, "
        "and explain how they are connected to the subject and to each other."
    ),
    "extraction_tasks": [
        "Identify the major nodes in the ecosystem: institutions, media channels, groups, and influential individuals.",
        "Explain how information, support, and criticism flow between these nodes.",
        "Identify which channels amplify the subject's ideas and which channels oppose or moderate them.",
        "Describe formal and informal networks that shape audience behavior and ecosystem response.",
        "Point out structural strengths and weak links in the ecosystem network.",
    ],
}

resilience_layer = {
    "name": "Resilience & Vulnerability Layer",
    "objective": (
        "Identify what strengthens or weakens the ecosystem, how feedback loops operate, "
        "and where the system is most likely to change or break under pressure."
    ),
    "extraction_tasks": [
        "Identify factors that reinforce the ecosystem against external criticism, regulation, or loss of legitimacy.",
        "Identify vulnerabilities that could destabilize audience support, institutions, or influence channels.",
        "Map the feedback loops that sustain, amplify, or dampen community energy and engagement.",
        "Explain which behaviors or events are most likely to trigger rapid ecosystem shifts.",
        "Identify early warning signals, tipping points, or common failure modes in this ecosystem.",
    ],
}

simulation_layer = {
    "name": "Simulation Knowledge Collection",
    "objective": (
        "Collect only the factual evidence and structured observations required "
        "by a downstream simulation model. Do not design, infer, or propose "
        "simulation rules."
    ),
    "extraction_tasks": [
        "Collect documented audience behaviors observed across multiple independent sources.",
        "Collect documented reactions to major events, controversies, criticism, and external pressure.",
        "Collect evidence describing how information spreads through the community.",
        "Collect documented examples of interactions between supporters, critics, neutral observers, and institutions.",
        "Collect evidence describing trust formation, authority recognition, credibility assessment, and influence relationships.",
        "Collect recurring community norms, terminology, rituals, symbols, and identity markers.",
        "Collect evidence about audience segmentation, membership evolution, and community lifecycle.",
        "Collect observable feedback patterns reported by reliable sources.",
        "Collect measurable behavioral indicators, timelines, frequencies, and historical examples whenever available.",
        "Flag missing information explicitly rather than inferring it.",
    ],
}

# ============================================================
# AGENT-SPECIFIC GUIDELINES
# ============================================================

ecosystem_guidelines = shared_guidelines + [
    "This run focuses exclusively on the ecosystem surrounding the subject: ",
    "audience, community, influence mechanisms, opposition, and simulation. ",
    "Do not re-analyze the subject's personal ideology or biography — ",
    "that was covered in the Subject Intelligence run.",

    "If the model begins to drift into abstract political philosophy, stop and focus on concrete ecosystem dynamics only.",
    "Avoid generic descriptions of ideology, political theory, or philosophy unless they are directly required to explain a specific ecosystem behavior tied to this subject.",
    "Map at least three distinct controversy events or opposition sources. ",
    "Do not allow a single controversy to dominate the Opposition section.",
]

# ============================================================
# QUERY BUILDER
# ============================================================

def build_ecosystem_query(subject_name: str, subject_profile: str, compressed_briefing: str) -> str:
    layers = [
        controversy_opposition_layer,
        audience_community_layer,
        influence_layer,
        network_structure_layer,
        resilience_layer,
        simulation_layer,
    ]

    lines = [
        "You are an expert researcher specializing in reverse-engineering influence ecosystems,", 
        "network analysis, and socio-political dynamics across diverse contexts and backgrounds.",
        "You analyze religious figures, political actors, thought leaders, media personalities,", 
        "and cultural influencers with methodological rigor and contextual awareness.",
        "",
        "Your task is to produce a high-quality Ecosystem Intelligence Report",
        "that can be used for downstream analysis and knowledge extraction.",
        "",
        "TASK: Ecosystem Intelligence Profile",
        "",
        f"Subject: {subject_name}",
        "",
        "=== SUBJECT PROFILE CONTEXT ===",
        subject_profile.strip(),
        "===============================",
        "",
        "=== COMPRESSED BRIEFING (PREVIOUS SEARCH RESULTS) ===",
        compressed_briefing.strip(),
        "=====================================================",
        "",
        "OBJECTIVE:",
        "Map the ecosystem surrounding the subject - the networks, audiences,",
        "institutions, controversies, and influence mechanisms that form the",
        "subject's real-world sphere of activity.",
        "Extract structured, evidence-based knowledge about how the ecosystem operates.",
        "",
        "This is NOT a biography of the subject. Build on the existing Subject Intelligence Report.",
        "",
        "⚠️ CRITICAL: This task is for OBSERVED ecosystem dynamics only.",
        "Do NOT generate any simulation rules, IF-THEN statements, compliance rates,",
        "percentages, or predictive behavioral models.",
        "Focus exclusively on documented behaviors, events, and relationships.",
        "",
        "RESEARCH FRAMEWORKS:",
        "",
    ]

    for layer in layers:
        lines.append(f"### {layer['name']} ###")
        lines.append(f"Objective: {layer['objective']}")
        for task in layer["extraction_tasks"]:
            lines.append(f"- {task}")
        lines.append("")

    return "\n".join(lines)

# ============================================================
# MAIN
# ============================================================

async def run_ecosystem_intelligence(
    subject_name: str,
    profile_path: str,
    subject_intelligence_path: str,
    short_query: str,
    max_sections: int = 4,
):
    if not os.path.exists(profile_path):
        print(f"❌ Profile not found: {profile_path}")
        return None

    # Use the real subject intelligence output report when available, so the ecosystem run continues directly.
    subject_intelligence_report_path = subject_intelligence_path
    fallback_report_path = None
    if subject_intelligence_report_path and not os.path.isabs(subject_intelligence_report_path):
        fallback_report_path = os.path.join(TESTS_DIR, subject_intelligence_report_path)

    if subject_intelligence_report_path and os.path.exists(subject_intelligence_report_path):
        report_source_path = subject_intelligence_report_path
    elif fallback_report_path and os.path.exists(fallback_report_path):
        report_source_path = fallback_report_path
    else:
        report_source_path = None

    if report_source_path is None:
        intermediate_report_path = r"C:\Users\DELL\graph-rag-agent\outputs\run_150f010a03c049fb8ae722c0541ad5d4\f491795c8c444e19af4c212b3b2b767e.md"
        if os.path.exists(intermediate_report_path):
            report_source_path = intermediate_report_path
            print(f"⚠️ Warning: subject_intelligence_path not found. Falling back to fixed intermediate report: {report_source_path}")
        else:
            print("❌ Neither the subject intelligence report nor the fixed intermediate report were found.")
            return None

    # قراءة الملفات
    with open(profile_path, "r", encoding="utf-8") as f:
        subject_profile = f.read()

    with open(report_source_path, "r", encoding="utf-8") as f:
        intermediate_report_content = f.read()

    print(f"🔗 Using subject intelligence report: {report_source_path}")

    print("⏳ Compressing Intermediate Report...")
    compressed_state = compress_subject_intelligence({
        "subject_intelligence_report": intermediate_report_content
    })
    
    compressed_briefing = format_compressed_for_injection(
        compressed_state["compressed_intelligence"]
    )

    print("\n" + "="*60)
    print("🔍 COMPRESSED BRIEFING (Before sending to Agent):")
    print("="*60)
    print(compressed_briefing)
    print("="*60 + "\n")

    full_query = build_ecosystem_query(
        subject_name, 
        subject_profile, 
        compressed_briefing
    )

    state: GraphState = {
        "user_initial_query": short_query,
        "chain_input": {
            "query": full_query,
            "guidelines": ecosystem_guidelines,
            "follow_guidelines": True,
            "max_sections": max_sections,
            "verbose": True,
        },
        "identity_data": {
            "needs_reprocessing": False,
            "feedback_notes": ""
        },
        "research_iteration": 0,
    }

    print("⏳ Running Ecosystem Intelligence Agent...")
    result = await make_research(state)

    identity_result = result.get("identity_data", {})
    report = identity_result.get("report", "")
    sources = identity_result.get("sources", [])
    costs = identity_result.get("costs", 0.0)

    output_path = f"{short_query}_ecosystem_intelligence.md"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(report)

    print(f"✅ Saved: {output_path}")
    print(f"   Length : {len(report)} chars")
    print(f"   Sources: {len(sources)}")
    print(f"   Costs  : {costs}")

    return identity_result


if __name__ == "__main__":
    asyncio.run(run_ecosystem_intelligence(
        subject_name="Sheikh Mostafa Al-Adawy",
        profile_path=r"C:\Users\DELL\graph-rag-agent\mostafa_el_adawy_the_egyptian_salafai_report.md",
        subject_intelligence_path="MostafaAlAdawy_subject_intelligence.md",
        short_query="MostafaAlAdawy",
        max_sections=4,
    ))