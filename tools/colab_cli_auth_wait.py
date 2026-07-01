#!/usr/bin/env python3
"""Headless helper for google-colab-cli OAuth copy/paste auth.

Writes an auth URL to .colab_auth_url.txt, waits for .colab_auth_code.txt,
then saves ~/.config/colab-cli/token.json for the normal `colab` CLI.
"""
from __future__ import annotations

import json
import os
import sys
import time
from importlib import resources
from pathlib import Path

from google_auth_oauthlib.flow import InstalledAppFlow

from colab_cli.auth import PUBLIC_SCOPES, REMOTE_REDIRECT_URI, TOKEN_CONFIG_PATH

ROOT = Path(__file__).resolve().parents[1]
URL_PATH = ROOT / ".colab_auth_url.txt"
CODE_PATH = ROOT / ".colab_auth_code.txt"
DONE_PATH = ROOT / ".colab_auth_done.json"
ERR_PATH = ROOT / ".colab_auth_error.txt"


def load_client_config() -> dict:
    explicit = Path.home() / ".colab-cli-oauth-config.json"
    if explicit.exists():
        return json.loads(explicit.read_text(encoding="utf-8"))
    config_resource = resources.files("colab_cli").joinpath("oauth_config.json")
    return json.loads(config_resource.read_text())


def main() -> int:
    for p in [URL_PATH, DONE_PATH, ERR_PATH]:
        try:
            p.unlink()
        except FileNotFoundError:
            pass
    # Leave an existing code file only if caller deliberately wrote it after URL.
    if CODE_PATH.exists():
        CODE_PATH.unlink()

    flow = InstalledAppFlow.from_client_config(load_client_config(), PUBLIC_SCOPES)
    flow.redirect_uri = REMOTE_REDIRECT_URI
    auth_url, _ = flow.authorization_url(prompt="consent", token_usage="remote")
    URL_PATH.write_text(auth_url + "\n", encoding="utf-8")
    print(f"Auth URL written to {URL_PATH}", flush=True)
    print(auth_url, flush=True)
    print(f"Waiting for code in {CODE_PATH}", flush=True)

    deadline = time.time() + 15 * 60
    while time.time() < deadline:
        if CODE_PATH.exists():
            code = CODE_PATH.read_text(encoding="utf-8").strip()
            if code:
                try:
                    flow.fetch_token(code=code)
                    creds = flow.credentials
                    token_path = Path(os.path.expanduser(TOKEN_CONFIG_PATH))
                    token_path.parent.mkdir(parents=True, exist_ok=True)
                    token_path.write_text(creds.to_json(), encoding="utf-8")
                    DONE_PATH.write_text(json.dumps({"ok": True, "token_path": str(token_path)}, indent=2), encoding="utf-8")
                    print(f"Saved token to {token_path}", flush=True)
                    return 0
                except Exception as e:
                    ERR_PATH.write_text(str(e), encoding="utf-8")
                    print(f"Auth failed: {e}", file=sys.stderr, flush=True)
                    return 1
        time.sleep(1)
    ERR_PATH.write_text("Timed out waiting for authorization code", encoding="utf-8")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
