"""
tools/apify_tool.py
CrewAI custom tool — scrapes Meta Ad Library via Apify.

ACTOR HISTORY (why we keep changing):
  "apify/meta-ads-scraper"      — never existed
  "apify/facebook-ads-scraper"  — exists but needs startUrls (URL list), not keywords
  "apify/meta-ads-library-scraper" — correct actor for keyword search on Meta Ad Library
    Input schema: { searchQuery, adType, country, limit }
    Docs: https://apify.com/apify/meta-ads-library-scraper

FALLBACK:
  If Apify fails for any reason, returns 5 realistic mock trading ads
  so Agent 2 always has content to analyse and pipeline never stops.
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Type

from apify_client import ApifyClient
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from tenacity import retry, stop_after_attempt, wait_exponential

from config import settings
from utils.logger import get_logger

logger = get_logger("apify_tool")

# Correct actor for keyword-based Meta Ad Library scraping
APIFY_ACTOR_ID = "apify/meta-ads-library-scraper"


class ApifyToolInput(BaseModel):
    keywords: str = Field(
        description="Comma-separated search keywords related to the niche"
    )
    max_ads: int = Field(default=20, description="Max number of ads to return")


class ApifyMetaAdsTool(BaseTool):
    """
    Scrapes Meta Ad Library using keyword search via Apify.
    Falls back to mock trading ad data if Apify unavailable.
    """

    name: str = "MetaAdsScraper"
    description: str = (
        "Scrapes Meta Ad Library to find successful ads in a given niche "
        "from the last 30 days. Input: comma-separated keywords. "
        "Returns top performing ads as JSON."
    )
    args_schema: Type[BaseModel] = ApifyToolInput

    def _run(self, keywords: str, max_ads: int = 20) -> str:
        logger.info(f"Starting Apify scrape | keywords={keywords} | max={max_ads}")

        try:
            result = self._scrape_meta_ads(keywords, max_ads)
            output_path = settings.JSON_DIR / "raw_ads.json"
            output_path.parent.mkdir(parents=True, exist_ok=True)

            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(result, f, indent=2, ensure_ascii=False)

            logger.info(f"Saved {len(result)} real ads → {output_path}")
            return json.dumps({
                "status": "success",
                "ads_found": len(result),
                "output_file": str(output_path),
                "ads": result[:5],
            })

        except Exception as e:
            logger.error(f"Apify scrape failed: {e}", exc_info=True)
            logger.warning("Falling back to mock ad data — pipeline will continue")
            return self._mock_ads_fallback(keywords)

    @retry(
        stop=stop_after_attempt(2),    # Fail fast — mock fallback is ready
        wait=wait_exponential(min=3, max=10),
    )
    def _scrape_meta_ads(self, keywords: str, max_ads: int) -> list[dict]:
        client = ApifyClient(settings.APIFY_API_TOKEN)

        # Use first keyword as primary search query
        primary_keyword = keywords.split(",")[0].strip()

        # meta-ads-library-scraper input schema
        # Full schema: https://apify.com/apify/meta-ads-library-scraper/input-schema
        run_input = {
            "searchQuery": primary_keyword,
            "adType": "ALL",
            "country": "US",
            "limit": max_ads * 2,       # Over-fetch then filter
            "activeStatus": "ACTIVE",
        }

        logger.info(f"Running actor '{APIFY_ACTOR_ID}' | query='{primary_keyword}'")
        run = client.actor(APIFY_ACTOR_ID).call(run_input=run_input)

        if not run or run.get("status") != "SUCCEEDED":
            raise RuntimeError(f"Apify run failed: status={run.get('status') if run else 'None'}")

        ads = []
        for item in client.dataset(run["defaultDatasetId"]).iterate_items():
            ads.append(self._normalize_ad(item))

        cutoff = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        ads = self._filter_recent(ads, cutoff)
        ads = self._rank_ads(ads)

        logger.info(f"Fetched {len(ads)} ads after filter/rank")
        return ads[:max_ads]

    def _normalize_ad(self, raw: dict) -> dict:
        return {
            "id": raw.get("id", ""),
            "page_name": raw.get("pageName", raw.get("page_name", "")),
            "ad_text": raw.get("adText", raw.get("body", raw.get("text", ""))),
            "headline": raw.get("headline", raw.get("title", "")),
            "cta": raw.get("callToAction", raw.get("cta", "")),
            "url": raw.get("url", raw.get("link", "")),
            "media_type": raw.get("mediaType", raw.get("type", "image")),
            "impressions_lower": raw.get("impressionsLowerBound", raw.get("reachLower", 0)),
            "impressions_upper": raw.get("impressionsUpperBound", raw.get("reachUpper", 0)),
            "start_date": raw.get("startDate", raw.get("createdAt", "")),
            "is_active": raw.get("isActive", raw.get("active", True)),
            "platforms": raw.get("publisherPlatforms", []),
            "thumbnail_url": raw.get("thumbnailUrl", raw.get("imageUrl", "")),
        }

    def _filter_recent(self, ads: list[dict], cutoff: str) -> list[dict]:
        return [ad for ad in ads if not ad.get("start_date") or ad["start_date"] >= cutoff]

    def _rank_ads(self, ads: list[dict]) -> list[dict]:
        def score(ad: dict) -> int:
            lo = ad.get("impressions_lower", 0) or 0
            hi = ad.get("impressions_upper", 0) or 0
            return (lo + hi) // 2
        return sorted(ads, key=score, reverse=True)

    def _mock_ads_fallback(self, keywords: str) -> str:
        """
        Realistic mock Meta ads for trading niche.
        Gives Agent 2 genuine ad copy to analyse when Apify is unavailable.
        """
        mock_ads = [
            {
                "id": "mock_001", "page_name": "TradeSignalPro",
                "ad_text": "Stop guessing which stocks to buy. Our AI signals gave members 23% gains last month. Join 50,000 traders who never miss a move. Try free for 7 days.",
                "headline": "AI Trading Signals — 78% Win Rate", "cta": "Start Free Trial",
                "impressions_lower": 500000, "impressions_upper": 1000000,
                "start_date": "2026-04-10", "media_type": "video",
            },
            {
                "id": "mock_002", "page_name": "WealthSignals",
                "ad_text": "I lost $12,000 following random YouTube advice. Then I found a community of 50k real traders sharing their actual trades. Now I'm up 31% this year.",
                "headline": "Trade With a Winning Community", "cta": "Join Now",
                "impressions_lower": 300000, "impressions_upper": 700000,
                "start_date": "2026-04-15", "media_type": "image",
            },
            {
                "id": "mock_003", "page_name": "MarketBeaters",
                "ad_text": "The market isn't rigged — you just don't have the right signals. Get real-time alerts before the move happens. Used by 50,000+ members.",
                "headline": "Beat the Market Every Week", "cta": "Get Signals",
                "impressions_lower": 200000, "impressions_upper": 500000,
                "start_date": "2026-04-20", "media_type": "video",
            },
            {
                "id": "mock_004", "page_name": "FinancialFreedomFast",
                "ad_text": "5 minutes a day. That's all it takes with our trading signals. No charts, no analysis, no stress. Just follow the alerts and watch your portfolio grow.",
                "headline": "5 Min/Day Trading System", "cta": "See How It Works",
                "impressions_lower": 150000, "impressions_upper": 400000,
                "start_date": "2026-04-22", "media_type": "image",
            },
            {
                "id": "mock_005", "page_name": "StockAlertDaily",
                "ad_text": "WARNING: Most retail investors lose money because they trade alone. The top 1% uses community intelligence. Now you can too — free trial, cancel anytime.",
                "headline": "Don't Trade Alone — Join the Crowd", "cta": "Try Free",
                "impressions_lower": 100000, "impressions_upper": 300000,
                "start_date": "2026-04-25", "media_type": "video",
            },
        ]

        output_path = settings.JSON_DIR / "raw_ads.json"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(mock_ads, f, indent=2)

        logger.info(f"Mock ads saved → {output_path}")
        return json.dumps({
            "status": "fallback",
            "note": "Apify unavailable — using mock trading ad data",
            "ads_found": len(mock_ads),
            "output_file": str(output_path),
            "ads": mock_ads,
        })