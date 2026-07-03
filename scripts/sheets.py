"""Read Google Sheets values — via a service account (CI) or the gws CLI (local).

Resolution order:
1. GOOGLE_SERVICE_ACCOUNT_JSON  — the service-account key as inline JSON
   (how GitHub Actions passes the secret).
2. GOOGLE_APPLICATION_CREDENTIALS — path to a service-account key file.
3. The `gws` CLI — local dev on a machine already signed in (keyring auth).

This lets the same build scripts run unchanged both on a laptop (gws) and in
CI (service account), so the automated sync and manual runs stay identical.
"""
from __future__ import annotations

import json
import os
import subprocess
import urllib.parse
import urllib.request
from functools import lru_cache

GWS = "/opt/homebrew/Cellar/googleworkspace-cli/0.22.5/bin/gws"
SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]


def _service_account_info() -> dict | None:
    inline = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON")
    if inline:
        return json.loads(inline)
    path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
    if path and os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return None


@lru_cache(maxsize=1)
def _access_token() -> str:
    from google.oauth2 import service_account  # lazy: only needed in CI
    import google.auth.transport.requests as gtr

    creds = service_account.Credentials.from_service_account_info(
        _service_account_info(), scopes=SCOPES
    )
    creds.refresh(gtr.Request())
    return creds.token


def get_values(spreadsheet_id: str, range_a1: str,
               value_render: str = "FORMATTED_VALUE") -> list[list[str]]:
    """Return the 2-D `values` array for a sheet range."""
    if _service_account_info() is not None:
        url = (f"https://sheets.googleapis.com/v4/spreadsheets/{spreadsheet_id}/values/"
               f"{urllib.parse.quote(range_a1)}?valueRenderOption={value_render}")
        req = urllib.request.Request(url, headers={"Authorization": f"Bearer {_access_token()}"})
        with urllib.request.urlopen(req) as resp:
            return json.load(resp).get("values", [])

    # Local fallback: the gws CLI (auth stored in the system keyring).
    params = {"spreadsheetId": spreadsheet_id, "range": range_a1, "valueRenderOption": value_render}
    res = subprocess.run(
        [GWS, "sheets", "spreadsheets", "values", "get", "--params", json.dumps(params)],
        capture_output=True, text=True, check=True,
    )
    out = res.stdout
    return json.loads(out[out.find("{"):]).get("values", [])
