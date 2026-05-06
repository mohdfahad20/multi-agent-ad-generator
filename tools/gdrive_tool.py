"""
tools/gdrive_tool.py
CrewAI custom tool — authenticates with Google Drive and fetches
document/sheet content to use as product data for script writing.
"""

import json
import os
from pathlib import Path
from typing import Optional, Type

from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from tenacity import retry, stop_after_attempt, wait_exponential

from config import settings
from utils.logger import get_logger

logger = get_logger("gdrive_tool")


class GDriveToolInput(BaseModel):
    file_id: Optional[str] = Field(
        default=None,
        description="Google Drive file ID. Uses GDRIVE_FILE_ID from env if not provided.",
    )


class GDriveTool(BaseTool):
    """
    Fetches text content from a Google Drive document or Google Sheet.
    Requires OAuth2 credentials (see setup instructions in README).
    Falls back to a mock dataset for testing without credentials.
    """

    name: str = "GoogleDriveFetcher"
    description: str = (
        "Fetches product/brand data from a Google Drive document or sheet. "
        "Returns the document's text content to use as context for ad script writing."
    )
    args_schema: Type[BaseModel] = GDriveToolInput

    def _run(self, file_id: Optional[str] = None) -> str:
        fid = file_id or settings.GDRIVE_FILE_ID
        logger.info(f"Fetching Google Drive file: {fid}")

        if not fid:
            logger.warning("No GDRIVE_FILE_ID set — using mock product data")
            return self._mock_product_data()

        try:
            content = self._fetch_gdrive(fid)
            output_path = settings.JSON_DIR / "product_data.txt"
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(content, encoding="utf-8")
            logger.info(f"Saved product data → {output_path}")
            return json.dumps({"status": "success", "content": content})
        except Exception as e:
            logger.error(f"GDrive fetch failed: {e}", exc_info=True)
            logger.info("Falling back to mock data")
            return self._mock_product_data()

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=10))
    def _fetch_gdrive(self, file_id: str) -> str:
        """Fetch Google Drive file using service account or OAuth2."""
        try:
            from google.oauth2.credentials import Credentials
            from google.auth.transport.requests import Request
            from google_auth_oauthlib.flow import InstalledAppFlow
            from googleapiclient.discovery import build
        except ImportError:
            raise RuntimeError(
                "Google API packages not installed. Run: pip install "
                "google-api-python-client google-auth-oauthlib google-auth-httplib2"
            )

        SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]
        creds = None
        token_path = Path(settings.GDRIVE_TOKEN_PATH)
        creds_path = Path(settings.GDRIVE_CREDENTIALS_PATH)

        if token_path.exists():
            creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            elif creds_path.exists():
                flow = InstalledAppFlow.from_client_secrets_file(str(creds_path), SCOPES)
                creds = flow.run_local_server(port=0)
            else:
                raise FileNotFoundError(
                    f"Google credentials not found at {creds_path}. "
                    "See README for setup instructions."
                )
            token_path.write_text(creds.to_json())

        service = build("drive", "v3", credentials=creds)

        # Determine file type and export accordingly
        file_meta = service.files().get(fileId=file_id, fields="mimeType,name").execute()
        mime = file_meta.get("mimeType", "")
        logger.info(f"File: {file_meta.get('name')} | MIME: {mime}")

        if "document" in mime:
            docs_service = build("docs", "v1", credentials=creds)
            doc = docs_service.documents().get(documentId=file_id).execute()
            return self._extract_doc_text(doc)
        elif "spreadsheet" in mime:
            sheets_service = build("sheets", "v4", credentials=creds)
            sheet = sheets_service.spreadsheets().values().get(
                spreadsheetId=file_id, range="A1:Z1000"
            ).execute()
            rows = sheet.get("values", [])
            return "\n".join(["\t".join(row) for row in rows])
        else:
            # Plain text or other — export as plain text
            request = service.files().export_media(fileId=file_id, mimeType="text/plain")
            return request.execute().decode("utf-8")

    def _extract_doc_text(self, doc: dict) -> str:
        """Extract plain text from a Google Doc API response."""
        text_parts = []
        for element in doc.get("body", {}).get("content", []):
            paragraph = element.get("paragraph")
            if not paragraph:
                continue
            for elem in paragraph.get("elements", []):
                text_run = elem.get("textRun")
                if text_run:
                    text_parts.append(text_run.get("content", ""))
        return "".join(text_parts)

    def _mock_product_data(self) -> str:
        """
        Fallback mock data for CrowdWisdomTrading.
        Replace this with your actual Google Drive content.
        """
        mock = {
            "status": "mock",
            "content": """
CrowdWisdomTrading — Product & Brand Data

PRODUCT: CrowdWisdomTrading Premium Signals
TAGLINE: Trade smarter with the crowd

KEY BENEFITS:
- Real-time trading signals from a community of 50,000+ verified traders
- 78% win rate tracked over 24 months
- Works for stocks, crypto, and forex
- Takes less than 5 minutes per day to follow
- Beginner-friendly — no technical analysis knowledge needed

TARGET AUDIENCE:
- Age 25–45, working professionals
- Frustrated with losing money in the market alone
- Tried other tools/courses but couldn't make consistent gains
- Want a proven, community-validated system
- Fear missing out on big market moves

PAIN POINTS (from customer research):
1. "I don't have time to research stocks all day"
2. "I've lost money following random YouTube advice"
3. "I feel like the market is rigged against retail investors"
4. "I'm scared of making the wrong call and losing everything"
5. "I want financial freedom but don't know where to start"

SOCIAL PROOF:
- 50,000+ members
- $2.4M+ profits tracked by members in 2024
- Featured in: Forbes, Benzinga, TradingView
- Average member: +23% portfolio gain in first 6 months

OFFER: 7-day free trial, then $97/month. Cancel anytime.
CTA: "Start Your Free Trial"
WEBSITE: crowdwisdomtrading.com
""",
        }
        return json.dumps(mock)