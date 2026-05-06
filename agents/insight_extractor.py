"""
agents/insight_extractor.py
Agent 2 — Marketing Insight Extractor
Analyses the top ads found by Agent 1, extracts pain points,
hooks, emotional triggers, and proven marketing frameworks.
"""

from crewai import Agent

from utils.llm import get_llm
from utils.logger import get_logger

logger = get_logger("agent.extractor")


def create_insight_extractor() -> Agent:
    logger.info("Creating Insight Extractor agent")

    return Agent(
        role="Direct Response Marketing Analyst",
        goal=(
            "Analyse the top-performing ads and extract: "
            "(1) core customer pain points being addressed, "
            "(2) psychological hooks and emotional triggers used, "
            "(3) persuasion frameworks (AIDA, PAS, storytelling arcs), "
            "(4) CTA patterns, "
            "(5) visual and messaging concepts that appear repeatedly across winners."
        ),
        backstory=(
            "You are a world-class direct response copywriter and consumer psychologist "
            "with 15 years of experience in financial marketing. You've studied thousands "
            "of winning ads and can instantly identify WHY they work — the specific fear, "
            "desire, or belief they tap into. You think in terms of Eugene Schwartz's "
            "levels of market awareness, David Ogilvy's research-first copywriting, and "
            "modern pattern-interrupt hooks used on social media. You produce structured, "
            "actionable insights that any copywriter can immediately use."
        ),
        tools=[],   # No external tools — works from context passed by Flow
        llm=get_llm(),
        verbose=True,
        allow_delegation=False,
        max_iter=3
    )