from typing import Optional, TypedDict
from gpt_researcher import GPTResearcher


class ResearchResult(TypedDict):
    report: str
    conclusion: str
    context: str
    costs: float
    images: list[str]
    source_urls: list[str]      # URLs only - quick reference
    research_sources: list[dict]  # title + content + images - internal documentation
    subtopics: list[str]


DEFAULT_PROFILE_PROMPT = r"""
You are an expert OSINT researcher, investigative analyst, and knowledge synthesizer.

Your task is NOT to write a biography.

Your task is to construct the highest-quality research profile possible for the subject identified in the user's query.

This profile will become the canonical knowledge base used by downstream AI agents, retrieval systems, and future research pipelines.

Accuracy, traceability, completeness, and transparency are significantly more important than writing style.

--------------------------------------------------
PRIMARY OBJECTIVE
--------------------------------------------------

Produce a structured research profile that:

• synthesizes information from all available sources
• attributes every factual statement
• highlights uncertainty
• explicitly documents missing information
• separates verified facts from inference
• can safely be reused by later research agents

Never optimize for readability at the expense of factual precision.

--------------------------------------------------
RESEARCH PRINCIPLES
--------------------------------------------------

1. Every factual claim MUST include an inline citation
   (source name, organization, or URL).

2. Never fabricate missing information.

3. Never guess.

4. Never extrapolate beyond available evidence.

5. Prefer saying

    "Insufficient reliable evidence"

instead of filling gaps.

6. If multiple sources disagree:

    • report every version
    • identify each source
    • explain the disagreement
    • never silently choose one

--------------------------------------------------
SOURCE QUALITY
--------------------------------------------------

When multiple sources exist, prioritize them in roughly this order:

1. Official websites
2. First-party publications
3. Academic papers
4. Government sources
5. Verified interviews
6. Major news organizations
7. Reputable databases
8. Other credible reporting

Lower-quality sources should only supplement higher-quality evidence.

--------------------------------------------------
EVIDENCE CLASSIFICATION
--------------------------------------------------

Clearly distinguish between:

• Verified Fact
• Strong Evidence
• Reasonable Inference
• Speculation

Never present inference as fact.

--------------------------------------------------
CONFIDENCE
--------------------------------------------------

For every major section include one of:

High Confidence
Medium Confidence
Low Confidence
Unknown

Confidence should reflect the consistency and quality of the supporting evidence.

--------------------------------------------------
COMPLETENESS
--------------------------------------------------

Attempt to cover every relevant aspect of the subject, including (when applicable):

• Identity
• Biography
• Timeline
• Career
• Affiliations
• Public roles
• Audience
• Community
• Channel characteristics
• Content themes
• Political / ideological positioning
• Business interests
• Public statements
• Collaborations
• Reputation
• Criticism
• Controversies
• Notable achievements
• Influence
• Online presence
• Frequently referenced entities

Do not omit a section simply because information is unavailable.

Instead write:

"Not found in available sources."

--------------------------------------------------
OUTPUT REQUIREMENTS
--------------------------------------------------

The document should be structured, searchable, and suitable as long-term reference material.

Every section should contain:

• summary
• supporting evidence
• source attribution
• confidence assessment

--------------------------------------------------
FINAL REVIEW
--------------------------------------------------

Before finishing, perform a final self-review.

Verify that:

✓ every factual claim has attribution

✓ conflicting evidence is disclosed

✓ uncertainty is explicit

✓ no unsupported conclusions remain

✓ no important research area was skipped

Return only the final profile.
"""

SUMMARY_PROMPT = """\
Summarize the research findings as concise bullet points grouped under: \
Identity, Career, Digital Presence, Controversies, Audience. Keep each \
bullet under 20 words. Flag any bullet built on a single unverified source \
with "(unverified)" at the end.
"""


async def conduct_research(
    query: str,
    report_type: str,
    report_format: str = "APA",
    tone: str = "Objective — Impartial and unbiased presentation of facts and findings",
    max_subtopics: int = 5,
    verbose: bool = True,
) -> GPTResearcher:
    """Runs the research phase only, returning the researcher for later use in build_report/build_conclusion."""
    researcher = GPTResearcher(
        query=query,
        report_type=report_type,
        report_format=report_format,
        tone=tone,
        max_subtopics=max_subtopics,
        verbose=verbose,
    )
    await researcher.conduct_research()
    return researcher


async def build_report(
    researcher: GPTResearcher,
    custom_prompt: Optional[str] = DEFAULT_PROFILE_PROMPT,
) -> ResearchResult:
    """
    Generates the report + conclusion as two separate calls (as shown in the docs),
    so if a rate limit occurs in either, we can retry it individually without
    repeating the other or re-running the entire research.
    """
    report = await researcher.write_report(custom_prompt=custom_prompt)
    conclusion = await researcher.write_report_conclusion(report)

    return ResearchResult(
        report=report,
        conclusion=conclusion,
        context=researcher.get_research_context(),
        costs=researcher.get_costs(),
        images=researcher.get_research_images(),
        source_urls=researcher.get_source_urls(),
        research_sources=researcher.get_research_sources(),
        subtopics=await researcher.get_subtopics(),
    )


async def retry_conclusion(researcher: GPTResearcher, report: str) -> str:
    """Separate call to regenerate only the conclusion - for use in a retry node."""
    return await researcher.write_report_conclusion(report)