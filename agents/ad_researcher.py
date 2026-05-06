"""
agents/ad_researcher.py
Agent 1 — Ad Researcher
Searches Meta Ad Library via Apify for top-performing ads
in the CWT niche over the last 30 days. Saves results to JSON.
"""

from crewai import Agent

from config import settings
from tools.apify_tool import ApifyMetaAdsTool
from utils.llm import get_llm
from utils.logger import get_logger

logger = get_logger("agent.researcher")


def create_ad_researcher() -> Agent:
    logger.info("Creating Ad Researcher agent")

    return Agent(
        role="Meta Ads Research Specialist",
        goal=(
            f"Find the top 20 highest-performing Meta ads in the "
            f"'{settings.CWT_NICHE}' niche from the last 30 days. "
            "Identify ads with the highest estimated impressions and engagement."
        ),
        backstory=(
            "You are a seasoned digital advertising analyst with deep expertise "
            "in the financial trading and investment niche. You have years of "
            "experience dissecting Meta ad campaigns to understand what makes "
            "them go viral. You know that the best-performing ads are those with "
            "the highest impression counts and longest run times — because "
            "advertisers only keep running what's profitable. You use data, "
            "not guesswork."
        ),
        tools=[ApifyMetaAdsTool()],
        llm=get_llm(),
        verbose=True,
        allow_delegation=False,
        max_iter=3,
    )