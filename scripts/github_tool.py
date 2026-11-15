#!/usr/bin/env python3
"""
GitHub Issues Tool for SmartPetShop
Zero-dependency GitHub integration using standard library urllib.
"""

import os
import sys
import json
import re
import subprocess
import urllib.request
import urllib.parse
import urllib.error
from pathlib import Path


def load_env():
    env_file = Path(__file__).resolve().parent.parent / ".env"
    if env_file.exists():
        with open(env_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, val = line.split("=", 1)
                    os.environ.setdefault(key.strip(), val.strip().strip('"').strip("'"))

load_env()

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
BASE_URL = "https://api.github.com"


def get_repo_info():
    repo_override = os.getenv("GITHUB_REPOSITORY")
    if repo_override:
        return repo_override.split("/", 1)

    try:
        remote_url = subprocess.check_output(
            ["git", "config", "--get", "remote.origin.url"],
            text=True
        ).strip()
        # Supports https://github.com/owner/repo.git or git@github.com:owner/repo.git
        match = re.search(r"github\.com[:/]([^/]+)/([^/\.]+)(?:\.git)?", remote_url)
        if match:
            return match.group(1), match.group(2)
    except Exception:
        pass

    return "crisb2reis", "SmartPetShop"


def github_request(endpoint, method="GET", data=None):
    if not GITHUB_TOKEN:
        print("[ERROR] GITHUB_TOKEN is required. Set it in .env or as environment variable.")
        print("To generate a token: GitHub Settings -> Developer settings -> Personal access tokens (Tokens classic) -> scope: 'repo'.")
        sys.exit(1)

    owner, repo = get_repo_info()
    full_url = f"{BASE_URL}/repos/{owner}/{repo}{endpoint}"

    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "SmartPetShop-Agent"
    }

    body = None
    if data:
        headers["Content-Type"] = "application/json"
        body = json.dumps(data).encode("utf-8")

    req = urllib.request.Request(full_url, data=body, headers=headers, method=method)

    try:
        with urllib.request.urlopen(req) as resp:
            content = resp.read().decode("utf-8")
            return json.loads(content) if content else {}
    except urllib.error.HTTPError as e:
        error_msg = e.read().decode("utf-8")
        print(f"[HTTP {e.code}] Erro ao chamar GitHub API ({endpoint}): {error_msg}")
        sys.exit(1)
    except Exception as e:
        print(f"[ERROR] Requisicao falhou: {e}")
        sys.exit(1)


def create_issue(title, body="", labels=None):
    payload = {"title": title, "body": body}
    if labels:
        payload["labels"] = labels
    return github_request("/issues", method="POST", data=payload)


def import_backlog(json_path):
    owner, repo = get_repo_info()
    print(f"Importando backlog para {owner}/{repo} via GitHub API...")

    with open(json_path, "r", encoding="utf-8") as f:
        tasks = json.load(f)

    for idx, item in enumerate(tasks, start=1):
        title = item.get("title", f"Task {idx}")
        desc = item.get("description", "")
        epic = item.get("epic", "")
        labels = item.get("labels", [])

        full_body = f"### Épico: {epic}\n\n{desc}\n\n---\n*Gerado automaticamente pelo Agente Antigravity*"
        if epic and epic not in labels:
            labels.append(epic.lower().replace(" ", "-"))

        issue = create_issue(title, body=full_body, labels=labels)
        print(f"[{idx}/{len(tasks)}] Issue #{issue['number']} criada: {title}")


def list_issues(state="open"):
    owner, repo = get_repo_info()
    issues = github_request(f"/issues?state={state}&per_page=50")
    print(f"\n--- Issues Abertas em {owner}/{repo} ---")
    if not issues:
        print("Nenhuma issue encontrada.")
        return []

    for issue in issues:
        # Ignore pull requests
        if "pull_request" in issue:
            continue
        labels_str = ", ".join([l["name"] for l in issue.get("labels", [])])
        print(f"#{issue['number']} - {issue['title']}")
        print(f"Labels: [{labels_str}]")
        print(f"URL:    {issue['html_url']}\n")
    return issues


def next_issue():
    issues = github_request("/issues?state=open&sort=created&direction=asc&per_page=1")
    if not issues:
        print("Nenhuma tarefa pendente!")
        return None
    issue = issues[0]
    print(f"\nProxima tarefa a ser realizada:")
    print(f"Issue #{issue['number']}: {issue['title']}")
    print(f"Descricao:\n{issue.get('body', '')}")
    return issue


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso:")
        print("  python scripts/github_tool.py import-backlog docs/backlog.json")
        print("  python scripts/github_tool.py list-issues")
        print("  python scripts/github_tool.py next-issue")
        sys.exit(0)

    cmd = sys.argv[1]
    if cmd == "import-backlog":
        path = sys.argv[2] if len(sys.argv) > 2 else "docs/backlog.json"
        import_backlog(path)
    elif cmd == "list-issues":
        list_issues()
    elif cmd == "next-issue":
        next_issue()
    else:
        print(f"Comando desconhecido: {cmd}")
