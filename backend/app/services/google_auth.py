from __future__ import annotations

from pathlib import Path
from typing import Sequence

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build


def build_google_service(
    api_name: str,
    api_version: str,
    credentials_file: str,
    token_file: str,
    scopes: Sequence[str],
):
    """Build a Google API service using local OAuth credentials.

    For the first run, this opens a browser so the clinic/doctor account can approve
    access. After that, the token file is reused and refreshed automatically.
    """
    credentials_path = Path(credentials_file)
    token_path = Path(token_file)
    token_path.parent.mkdir(parents=True, exist_ok=True)

    if not credentials_path.exists():
        raise FileNotFoundError(
            f"Google credentials file not found: {credentials_path}. "
            "Download the OAuth client JSON from Google Cloud Console and place it there."
        )

    creds = None
    if token_path.exists():
        creds = Credentials.from_authorized_user_file(str(token_path), list(scopes))

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(str(credentials_path), list(scopes))
            creds = flow.run_local_server(port=0)
        token_path.write_text(creds.to_json(), encoding="utf-8")

    return build(api_name, api_version, credentials=creds)
