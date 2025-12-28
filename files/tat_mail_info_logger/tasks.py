# tasks.py
# Invoke tasks for msg2json
#
# Usage examples:
#   invoke msg2json
#   invoke msg2json --input="msg" --output="json"
#   invoke msg2json --input="some/file.msg" --output="json" --dry-run
#   invoke msg2json --model="gemini-flash-latest"
#   invoke msg2json --api-key="YOUR_KEY"
#
# Notes:
# - This assumes your converter script is named "msg2json.py" in the same directory.
#   If your filename is different, pass --script="yourname.py" or change DEFAULT_SCRIPT below.

from __future__ import annotations

import os
import shlex
from invoke import task

DEFAULT_SCRIPT = "pyt/msg2json.py"
DEFAULT_APP    = "app.py"


def _q(s: str) -> str:
    """Shell-quote helper."""
    return shlex.quote(s)


@task(
    help={
        "input": "Input .msg file or directory (default: msg)",
        "output": "Output directory or path (default: json)",
        "model": "Gemini model name (default: gemini-flash-latest)",
        "api_key": "API key (optional; otherwise rely on env GEMINI_API_KEY/GOOGLE_API_KEY)",
        "dry_run": "If set, do not call Gemini; just print extracted mail head/body preview",
        "script": "Python script filename to run (default: msg2json.py)",
        "python": "Python executable to use (default: python3 or $PYTHON)",
        "extra": "Extra raw CLI args appended to the command (optional)",
    }
)
def msg2json(
    c,
    input: str = "msg",
    output: str = "json",
    model: str = "gemini-flash-latest",
    api_key: str | None = None,
    dry_run: bool = False,
    script: str = DEFAULT_SCRIPT,
    python: str | None = None,
    extra: str | None = None,
):
    """
    Run msg2json converter via Invoke.

    This calls:
      python msg2json.py -i <input> -o <output> --model <model> [--api-key ...] [--dry-run]
    """
    py = python or os.environ.get("PYTHON") or "python3"

    cmd_parts = [
        _q(py),
        _q(script),
        "-i",
        _q(input),
        "-o",
        _q(output),
        "--model",
        _q(model),
    ]

    if api_key:
        cmd_parts += ["--api-key", _q(api_key)]

    if dry_run:
        cmd_parts.append("--dry-run")

    if extra:
        # Append as-is (user responsibility). If you want safe splitting, pass it like:
        #   invoke msg2json --extra='--dry-run'
        cmd_parts.append(extra)

    cmd = " ".join(cmd_parts)
    c.run(cmd, pty=True)

@task(
    help={
        "app": "Streamlit app file (default: app.py)",
        "port": "Server port (default: 8501)",
        "server_headless": "Run Streamlit in headless mode (useful on servers/CI)",
        "browser": "Open browser automatically (default: False; use --browser to enable)",
        "extra": "Extra raw args appended to streamlit command (optional)",
        "python": "Python executable to use (default: python3 or $PYTHON)",
    }
)

def run(
    c,
    app: str = DEFAULT_APP,
    port: int = 8501,
    server_headless: bool = False,
    browser: bool = False,
    extra: str | None = None,
    python: str | None = None,
):
    """
    Launch Streamlit app:
      streamlit run app.py
    """
    py = python or os.environ.get("PYTHON") or "python3"

    # Use `python -m streamlit` to avoid PATH issues where `streamlit` command isn't found.
    cmd_parts = [
        _q(py),
        "-m",
        "streamlit",
        "run",
        _q(app),
        "--server.port",
        _q(str(port)),
    ]

    if server_headless:
        cmd_parts += ["--server.headless", "true"]

    # Streamlit default is to open browser; many people want the opposite in dev shells.
    # We treat --browser as an opt-in to open.
    if not browser:
        cmd_parts += ["--server.headless", "true"] if server_headless else []
        # If you want to *force* no browser open locally, Streamlit doesn't have a perfect flag,
        # but headless=true is the common approach.

    if extra:
        cmd_parts.append(extra)

    cmd = " ".join(cmd_parts)
    c.run(cmd, pty=True)

    
@task
def version(c, script: str = DEFAULT_SCRIPT, python: str | None = None):
    """Show msg2json.py --help (quick sanity check)."""
    py = python or os.environ.get("PYTHON") or "python3"
    c.run(f"{_q(py)} {_q(script)} --help", pty=True)
