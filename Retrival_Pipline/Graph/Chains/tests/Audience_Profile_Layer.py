# audience_intelligence_agent.py

import asyncio
import os
import sys
from dotenv import load_dotenv
from Nodes.GPT_ResearcherNode.ResearchNode import make_research
from StateGraph import GraphState

# Make the local tests folder importable whether this file is run as a script
# or imported as part of a package.
TESTS_DIR = os.path.dirname(__file__)
if TESTS_DIR not in sys.path:
    sys.path.insert(0, TESTS_DIR)

load_dotenv()

# ============================================================
# LAYERS - AUDIENCE ECOSYSTEM
# ============================================================

audience_profile_layer = {
    "name": "Audience Profile Layer",
    "objective": "Identify who composes the audience and characterize the major groups surrounding the subject.",
    "extraction_tasks": [
        "Identify the major audience segments supported by available evidence.",
        "Characterize audience groups by age, gender, education, profession, geography, socioeconomic background, or other relevant characteristics whenever evidence exists.",
        "Identify recurring religious, political, cultural, or ideological characteristics when supported by evidence.",
        "Distinguish core followers, regular consumers, casual audiences, critics, and former followers whenever possible.",
        "Identify which audience segments appear most engaged across different platforms and communication channels.",
        "Identify recurring roles assumed by audience members (e.g., students, activists, professionals, content creators, community leaders, or other relevant groups).",
        "Identify observable differences between audience segments rather than treating the audience as a single homogeneous community."
    ]
}

audience_motivation_layer = {
    "name": "Audience Motivation Layer",
    "objective": "Understand why different audience groups are attracted to the subject and what needs the ecosystem appears to satisfy.",
    "extraction_tasks": [
        "Identify the primary motivations attracting different audience segments.",
        "Analyze religious, ideological, psychological, educational, political, cultural, social, or practical motivations whenever supported by evidence.",
        "Identify recurring fears, aspirations, frustrations, identity needs, or perceived problems that increase audience engagement.",
        "Explain which aspects of the subject's ideas or communication resonate with different audience groups.",
        "Distinguish motivations that attract new audiences from those that maintain long-term engagement.",
        "Identify observable factors that strengthen trust, loyalty, or continued participation.",
        "Identify factors that reduce engagement, create disagreement, or lead individuals to disengage from the ecosystem."
    ]
}

community_ecosystem_layer = {
    "name": "Community & Ecosystem Layer",
    "objective": "Reverse engineer how the audience organizes itself into communities and how the surrounding ecosystem functions.",
    "extraction_tasks": [
        "Identify the major communities, networks, or ecosystems surrounding the subject.",
        "Identify formal and informal community structures whenever evidence exists.",
        "Identify influential followers, secondary influencers, organizations, institutions, or media channels that contribute to the ecosystem.",
        "Identify recurring community norms, identity markers, values, terminology, and shared narratives.",
        "Analyze how newcomers become integrated into the community.",
        "Identify internal divisions, competing interpretations, or subgroups whenever they exist.",
        "Explain how different parts of the ecosystem interact and reinforce one another."
    ]
}

behavioral_impact_layer = {
    "name": "Behavioral Impact Layer",
    "objective": "Identify how exposure to the subject influences individual beliefs, decisions, behaviors, and social interactions.",
    "extraction_tasks": [
        "Identify observable changes in beliefs, values, priorities, attitudes, or identity associated with exposure to the subject's ideas.",
        "Analyze behavioral effects on religion, politics, education, family life, social relationships, civic participation, or other relevant domains whenever supported by evidence.",
        "Distinguish immediate reactions from long-term behavioral changes.",
        "Identify which audience segments appear most influenced by different aspects of the subject's discourse.",
        "Identify intended and unintended behavioral outcomes whenever evidence exists.",
        "Identify positive, negative, and mixed outcomes without assuming the direction of the impact.",
        "Explain the mechanisms linking the subject's communication to observed behavioral change."
    ]
}

social_cultural_impact_layer = {
    "name": "Social & Cultural Impact Layer",
    "objective": "Assess the broader social, cultural, educational, political, and institutional impact associated with the subject's ideas and audience ecosystem.",
    "extraction_tasks": [
        "Identify observable social, cultural, educational, political, religious, or institutional impacts supported by evidence.",
        "Distinguish effects at the individual, community, and wider societal levels.",
        "Identify changes in public discourse, cultural norms, or collective behavior associated with the ecosystem.",
        "Identify positive, negative, and mixed societal outcomes without assuming the direction of the impact.",
        "Explain which audience segments or communities appear most affected by different aspects of the subject's ideas.",
        "Identify significant long-term societal trends or recurring patterns associated with the ecosystem whenever evidence exists.",
        "Separate direct observable impact from indirect or inferred effects."
    ]
}

diffusion_recruitment_layer = {
    "name": "Diffusion & Recruitment Layer",
    "objective": "Understand how ideas spread, how new audiences enter the ecosystem, and how influence expands over time.",
    "extraction_tasks": [
        "Identify the primary channels through which new audiences discover the subject.",
        "Analyze how ideas spread across platforms, communities, institutions, and personal networks.",
        "Identify recurring recruitment pathways into the ecosystem whenever evidence exists.",
        "Explain how casual consumers become regular followers and how regular followers become active advocates or secondary influencers.",
        "Identify feedback loops that reinforce audience growth and idea diffusion.",
        "Identify barriers that slow, weaken, or prevent diffusion.",
        "Explain why certain ideas spread more successfully than others."
    ]
}

trust_persuasion_layer = {
    "name": "Trust & Persuasion Mechanisms Layer",
    "objective": "Reverse engineer the mechanisms through which trust is established, maintained, and translated into persuasion and long-term influence.",
    "extraction_tasks": [
        "Identify the primary factors that lead different audience segments to trust the subject.",
        "Analyze how credibility, authority, expertise, authenticity, and legitimacy are established and reinforced.",
        "Identify recurring persuasive strategies, emotional appeals, framing techniques, and authority signals.",
        "Explain how different audience segments evaluate competing sources of information.",
        "Identify recurring psychological, social, cultural, or religious mechanisms that strengthen commitment to the subject's ideas.",
        "Identify factors that weaken trust, reduce influence, or lead followers to disengage.",
        "Separate evidence-supported mechanisms from analytical inference."
    ]
}

opposition_resistance_layer = {
    "name": "Opposition & Resistance Layer",
    "objective": "Understand how different individuals and communities reject, resist, reinterpret, or oppose the subject's ideas.",
    "extraction_tasks": [
        "Identify the principal critics, competing communities, institutions, or alternative schools of thought.",
        "Analyze the primary reasons different groups reject or criticize the subject.",
        "Identify recurring counter-narratives, competing interpretations, and ideological disagreements.",
        "Explain how supporters, critics, and neutral observers interpret the same events differently.",
        "Identify audience segments that are resistant to the subject's influence and explain why.",
        "Analyze factors that reduce susceptibility to the subject's discourse.",
        "Identify recurring conflicts, polarization patterns, and interaction dynamics between supporters and opponents."
    ]
}

audience_simulation_layer = {
    "name": "Audience Simulation Layer",
    "objective": "Extract the structured knowledge required to model, simulate, and predict audience behavior within the ecosystem.",
    "extraction_tasks": [
        "Identify stable audience archetypes that can be represented as simulation agents.",
        "Extract recurring beliefs, values, priorities, identities, and behavioral traits characterizing each audience segment.",
        "Identify the internal variables that influence audience decisions, trust, engagement, and behavioral change.",
        "Extract decision-making heuristics and recurring behavioral rules governing how different audience segments respond to new information.",
        "Identify typical state transitions such as observer → follower, follower → advocate, supporter → critic, or disengaged member whenever supported by evidence.",
        "Identify recurring interactions between different audience segments, supporters, critics, institutions, and external actors.",
        "Extract feedback loops that reinforce, weaken, or transform beliefs and community behavior over time.",
        "Identify the minimum set of entities, variables, relationships, and behavioral rules required to build an agent-based Digital Twin of the audience ecosystem."
    ]
}

# ============================================================
# SHARED GUIDELINES
# ============================================================

shared_guidelines = [
    # ============================================================
    # EVIDENCE & ATTRIBUTION
    # ============================================================
    "Identify the subject unambiguously before beginning the investigation. "
    "When multiple individuals share the same or similar names, actively disambiguate them using biography, occupation, affiliations, geography, official websites, or other identifying characteristics before collecting evidence.",

    "Search for sources primarily in the language(s) used by the subject and the communities in which the subject operates. "
    "Use additional languages mainly for verification or broader context.",

    "Collect evidence from multiple independent sources before drawing any conclusion. "
    "Major factual or analytical claims should normally be corroborated by multiple independent sources.",

    "Every factual claim must be traceable to a specific source. "
    "If a source cannot be identified, mark the claim explicitly as [UNVERIFIED] and do not present it as fact.",

    "Direct quotations require a direct URL or document reference to the exact source. "
    "If the original text or recording cannot be located, do not quote — paraphrase with source attribution instead.",

    "Separate the subject's own stated positions from descriptions, labels, or accusations "
    "made by supporters, critics, media outlets, or third parties. "
    "Never present external characterizations as established facts about the subject.",

    "Give greater weight to the subject's own recurring statements than to external interpretations whenever they conflict.",

    "Prefer reconstructing the subject's worldview from their own recurring statements, "
    "writings, speeches, lectures, and documented works — not from how opponents or supporters describe them.",

    "When attributing specific opinions, fatwas, theories, or positions to the subject, "
    "verify that they were explicitly expressed by the subject in a reliable source. "
    "Do not attribute claims based solely on quotations by third parties, social media posts, or unsourced compilations.",

    # ============================================================
    # IDEOLOGICAL LABELING
    # ============================================================
    "Do not assign ideological labels (e.g. Madkhali, Ikhwani, Jihadi, Liberal) "
    "unless the subject has explicitly self-identified with that label, "
    "or the label is supported by multiple reliable independent sources "
    "that provide specific behavioral or textual evidence — not mere association or accusation.",

    "Treat ideological classification as a conclusion to be earned by evidence, not a starting assumption. "
    "When evidence is insufficient for a label, describe observable positions and patterns instead.",

    "Never infer a broad ideological identity from one or two positions, personal associations, or isolated statements. "
    "Describe observable positions first, and assign ideological classifications only when supported by the subject's overall recurring intellectual pattern.",

    # ============================================================
    # SAMPLING & REPRESENTATIVENESS
    # ============================================================
    "Favor breadth before depth. "
    "Build a representative map of the subject's recurring ideas, positions, works, and themes before examining individual examples in detail.",

    "Build a broad and representative map of the subject's recurring ideas, positions, and works "
    "before analyzing individual examples. "
    "Do not allow one or two high-profile or viral incidents to dominate the analysis.",

    "Avoid over-representing topics that receive disproportionate media attention. "
    "Representative recurring ideas are more important than isolated controversial or viral examples.",

    "If a particular event or statement appears more than twice across different sections, "
    "this is a signal of over-reliance. Actively seek additional independent examples "
    "to represent the same pattern before continuing.",

    "Distinguish between a subject's foundational recurring positions "
    "and isolated statements made in specific contexts. "
    "Weight recurring patterns significantly higher than single incidents.",

    # ============================================================
    # INFERENCE vs FACT
    # ============================================================
    "Separate verified evidence from analytical inference. "
    "Never present inference as established fact.",

    "Audience demographics, motivations, and psychological profiles are usually inferred. "
    "Clearly distinguish such inferences from directly observed evidence and explain the observations supporting them.",

    # ============================================================
    # SOURCE QUALITY
    # ============================================================
    "Prioritize primary sources: the subject's own content, books, lectures, interviews, "
    "and documented statements. Secondary sources (news articles, Wikipedia, advocacy organizations) "
    "should mainly be used for verification or additional context, not as the sole basis for major conclusions.",

    "If primary sources on a topic cannot be found, explicitly state: "
    "'Primary source not located. The following is based on secondary reporting.' "
    "Do not silently substitute secondary sources for primary ones.",

    "When only secondary sources are available, assess and state their reliability. "
    "Advocacy organizations, political opponents, and state media each carry specific biases "
    "that should be acknowledged when their reporting is used.",

    # ============================================================
    # CONFLICTS & GAPS
    # ============================================================
    "When two or more sources conflict on any fact, present all versions explicitly, "
    "identify each source, and describe the disagreement instead of silently choosing one version.",

    "Do not omit a section because information is unavailable. "
    "Instead briefly state that insufficient reliable evidence was found. "
    "Visible knowledge gaps are preferable to unsupported conclusions.",

    # ============================================================
    # OUTPUT DISCIPLINE
    # ============================================================
    "Prioritize structured knowledge extraction over descriptive writing. "
    "The output should read as an intelligence report rather than a biography or essay.",

    "Avoid repeating the same information across multiple sections. "
    "Each section should contribute new analytical knowledge. "
    "Reference previously established findings instead of restating them.",

    "Produce reusable analytical knowledge that can support downstream intelligence analysis, "
    "academic synthesis, knowledge graphs, behavioral simulation, and Digital Twin construction.",
]

# ============================================================
# AGENT-SPECIFIC GUIDELINES
# ============================================================

audience_guidelines = shared_guidelines + [
    "Focus on the audience ecosystem surrounding the subject, not the subject themselves. "
    "Treat the subject as the source of influence rather than the primary object of analysis.",

    "Search for evidence about audience composition, behavior, and impact. "
    "Primary sources include audience comments, forum discussions, social media interactions, "
    "survey data, community content, and documented audience activities. "
    "Use the subject's own content mainly to understand what attracts audiences, "
    "not as evidence about the audiences themselves.",

    "When analyzing audience motivations and behaviors, draw examples from "
    "multiple platforms, time periods, and audience groups. "
    "Do not rely on the same example more than once across different sections.",
]

# ============================================================
# SUMMARY NODE - لتلخيص الـ Briefings
# ============================================================

async def summarize_briefings(briefing_1_path: str, briefing_2_path: str, short_query: str) -> str:
    """تاخد التقريرين وتلخصهم في تقرير واحد باستخدام make_research"""
    
    with open(briefing_1_path, "r", encoding="utf-8") as f:
        briefing_1 = f.read()
    
    with open(briefing_2_path, "r", encoding="utf-8") as f:
        briefing_2 = f.read()
    
    summary_prompt = f"""
    You are an expert summarizer.
    
    Your task is to combine and summarize the following two intelligence briefings about the same subject.
    Create a single, coherent summary that captures ALL key information from BOTH briefings.
    
    Do not lose any important information. 
    If the same information appears in both, include it once.
    If they contain different information, include both.
    If they contradict, note the contradiction.
    
    SOURCE 1:
    {briefing_1}
    
    SOURCE 2:
    {briefing_2}
    
    OUTPUT: A single comprehensive summary that combines both briefings.
    """
    
    state: GraphState = {
        "user_initial_query": short_query,
        "chain_input": {
            "query": summary_prompt,
            "guidelines": [
                "Combine both briefings into one comprehensive summary.",
                "Do not lose any important information.",
                "If information is duplicated, include it once.",
                "If information contradicts, note the contradiction.",
                "Output should be a single coherent summary."
            ],
            "follow_guidelines": True,
            "max_sections": 1,
            "verbose": True,
        },
        "identity_data": {
            "needs_reprocessing": False,
            "feedback_notes": ""
        },
        "research_iteration": 0,
    }
    
    print("📝 Summarizing the two briefings...")
    result = await make_research(state)
    
    identity_result = result.get("identity_data", {})
    summary = identity_result.get("report", "")
    
    print(f"✅ Summary created: {len(summary)} chars")
    return summary

# ============================================================
# QUERY BUILDER
# ============================================================

def build_audience_query(subject_name: str, subject_profile: str, combined_summary: str) -> str:
    layers = [
        audience_profile_layer,
        audience_motivation_layer,
        community_ecosystem_layer,
        behavioral_impact_layer,
        social_cultural_impact_layer,
        diffusion_recruitment_layer,
        trust_persuasion_layer,
        opposition_resistance_layer,
        audience_simulation_layer,
    ]

    lines = [
        "You are an expert researcher specializing in audience ecosystems,",
        "social influence, collective behavior, community analysis,",
        "diffusion dynamics, and socio-cultural systems.",
        "",
        "You analyze how audiences form, evolve, organize themselves,",
        "interpret ideas, respond to public figures,",
        "and influence one another across diverse cultural, political,",
        "religious, educational, and media environments.",
        "",
        "Your task is to produce a high-quality Audience Intelligence Report",
        "that can support downstream intelligence analysis,",
        "knowledge extraction, Knowledge Graph construction,",
        "and Digital Twin development.",
        "",
        "TASK: Audience Intelligence Profile",
        "",
        f"Subject: {subject_name}",
        "",
        "=== SUBJECT PROFILE CONTEXT ===",
        subject_profile.strip(),
        "===============================",
        "",
        "=== COMBINED SUBJECT INTELLIGENCE SUMMARY ===",
        combined_summary.strip(),
        "=============================================",
        "",
        "OBJECTIVE:",
        "Reverse engineer the audience ecosystem surrounding the subject.",
        "",
        "Treat the subject as the source of influence rather than the primary object of analysis.",
        "",
        "Identify who composes the audience,",
        "why different people become attracted to the subject,",
        "how communities organize themselves,",
        "how ideas spread,",
        "how trust develops,",
        "how beliefs evolve,",
        "how influence produces observable behavioral, social, cultural, educational, political,",
        "or institutional effects,",
        "and how different groups support, reinterpret, criticize,",
        "or resist the subject's ideas.",
        "",
        "Pay particular attention to identifying",
        "which audience segments appear most susceptible to the subject's discourse,",
        "which remain resistant,",
        "and which observable characteristics distinguish them.",
        "",
        "Treat audience behavior, community activity,",
        "and documented interactions as the primary sources of evidence,",
        "rather than relying solely on the subject's own claims or self-description.",
        "",
        "Extract reusable, evidence-based knowledge describing recurring",
        "audience structures, relationships, mechanisms,",
        "behavioral patterns, and ecosystem dynamics.",
        "",
        "Build upon the Subject Intelligence Summary rather than repeating it.",
        "",
        "Focus on mechanisms, relationships,",
        "observable behaviors, and recurring patterns",
        "instead of narrative summaries.",
        "",
        "⚠️ CRITICAL:",
        "",
        "This investigation is limited to observable evidence.",
        "",
        "Do not generate predictions.",
        "Do not simulate behavior.",
        "Do not invent motivations.",
        "Do not infer hidden psychological states without sufficient evidence.",
        "Do not generate IF-THEN rules or agent behaviors.",
        "",
        "Document the ecosystem as it exists.",
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

async def run_audience_intelligence(
    subject_name: str,
    profile_path: str,
    briefing_1_path: str,
    briefing_2_path: str,
    short_query: str,
    max_sections: int = 4,
):
    if not os.path.exists(profile_path):
        print(f"❌ Profile not found: {profile_path}")
        return None

    if not os.path.exists(briefing_1_path):
        print(f"❌ Briefing 1 not found: {briefing_1_path}")
        return None

    if not os.path.exists(briefing_2_path):
        print(f"❌ Briefing 2 not found: {briefing_2_path}")
        return None

    # STEP 1: Summarize the two briefings باستخدام make_research
    combined_summary = await summarize_briefings(briefing_1_path, briefing_2_path, short_query)
    
    # STEP 2: Read profile
    with open(profile_path, "r", encoding="utf-8") as f:
        subject_profile = f.read()

    # STEP 3: Build audience query with profile + combined summary
    full_query = build_audience_query(subject_name, subject_profile, combined_summary)

    # STEP 4: Run Audience Agent باستخدام make_research
    state: GraphState = {
        "user_initial_query": short_query,
        "chain_input": {
            "query": full_query,
            "guidelines": audience_guidelines,
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

    print("⏳ Running Audience Intelligence Agent...")
    print(f"   📄 Profile: {os.path.basename(profile_path)}")
    print(f"   📄 Combined Summary: {len(combined_summary)} chars")
    
    result = await make_research(state)
    
    identity_result = result.get("identity_data", {})
    report = identity_result.get("report", "")
    sources = identity_result.get("sources", [])
    costs = identity_result.get("costs", 0.0)

    output_path = f"{short_query}_audience_intelligence.md"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(report)

    print(f"✅ Saved: {output_path}")
    print(f"   Length : {len(report)} chars")
    print(f"   Sources: {len(sources)}")
    print(f"   Costs  : {costs}")

    return identity_result


if __name__ == "__main__":
    asyncio.run(run_audience_intelligence(
        subject_name="Sheikh Mostafa Al-Adawy",
        profile_path=r"C:\Users\DELL\graph-rag-agent\outputs\run_150f010a03c049fb8ae722c0541ad5d4\f491795c8c444e19af4c212b3b2b767e.md",
        briefing_1_path=r"C:\Users\DELL\graph-rag-agent\outputs\run_f72fdfbdb74642b59e8a8eb3eb9e8188\b113dfd89d214e61ac82e1958b61dc84.md",
        briefing_2_path=r"C:\Users\DELL\graph-rag-agent\outputs\run_f72fdfbdb74642b59e8a8eb3eb9e8188\b113dfd89d214e61ac82e1958b61dc84.md",  # غير المسار
        short_query="MostafaAlAdawy",
        max_sections=4,
    ))