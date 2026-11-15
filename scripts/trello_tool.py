#!/usr/bin/env python3
"""
Trello CLI Tool for SmartPetShop
Zero-dependency Trello integration using standard library urllib.
"""

import os
import sys
import json
import urllib.request
import urllib.parse
import urllib.error
from pathlib import Path

# Load .env file manually if exists
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

API_KEY = os.getenv("TRELLO_API_KEY", "")
TOKEN = os.getenv("TRELLO_TOKEN", "")
BOARD_ID = os.getenv("TRELLO_BOARD_ID", "")
BASE_URL = "https://api.trello.com/1"


def trello_request(endpoint, method="GET", params=None, data=None):
    if not API_KEY or not TOKEN:
        print("[ERROR] TRELLO_API_KEY and TRELLO_TOKEN must be set in your .env or environment.")
        sys.exit(1)

    url_params = {"key": API_KEY, "token": TOKEN}
    if params:
        url_params.update(params)

    query_str = urllib.parse.urlencode(url_params)
    full_url = f"{BASE_URL}{endpoint}?{query_str}"

    headers = {"Accept": "application/json"}
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
        print(f"[HTTP {e.code}] Error calling {endpoint}: {error_msg}")
        sys.exit(1)
    except Exception as e:
        print(f"[ERROR] Request failed: {e}")
        sys.exit(1)


def list_boards():
    """Lists all boards for the authenticated member."""
    boards = trello_request("/members/me/boards", params={"fields": "name,id,url"})
    print("\n--- Seus Quadros no Trello ---")
    for b in boards:
        print(f"Nome: {b['name']}")
        print(f"ID:   {b['id']}")
        print(f"URL:  {b['url']}\n")


def get_board_lists(board_id=None):
    b_id = board_id or BOARD_ID
    if not b_id:
        print("[ERROR] Please provide a BOARD_ID or configure TRELLO_BOARD_ID in .env")
        sys.exit(1)
    return trello_request(f"/boards/{b_id}/lists", params={"fields": "name,id"})


def create_list(board_id, name):
    return trello_request("/lists", method="POST", params={"name": name, "idBoard": board_id})


def setup_board(board_id=None):
    """Ensures standard lists exist in the board."""
    b_id = board_id or BOARD_ID
    if not b_id:
        print("[ERROR] Please provide a board ID.")
        sys.exit(1)

    existing = {lst["name"].lower(): lst["id"] for lst in get_board_lists(b_id)}
    standard_lists = ["Backlog", "To Do", "In Progress", "Review", "Done"]

    print(f"Configurando quadro {b_id}...")
    for s_list in standard_lists:
        if s_list.lower() not in existing:
            created = create_list(b_id, s_list)
            print(f"[OK] Criada lista: {s_list} (ID: {created['id']})")
        else:
            print(f"[INFO] Lista ja existe: {s_list}")


def create_card(list_id, title, description=""):
    return trello_request(
        "/cards",
        method="POST",
        params={"idList": list_id, "name": title, "desc": description}
    )


def import_backlog(json_path, board_id=None):
    """Imports cards from a JSON file into the 'Backlog' list."""
    b_id = board_id or BOARD_ID
    if not b_id:
        print("[ERROR] BOARD_ID is required.")
        sys.exit(1)

    lists = get_board_lists(b_id)
    backlog_list = next((l for l in lists if l["name"].strip().lower() in ["backlog", "a fazer", "to do"]), None)

    if not backlog_list:
        print("[ERROR] Could not find 'Backlog' or 'To Do' list on the board.")
        sys.exit(1)

    with open(json_path, "r", encoding="utf-8") as f:
        tasks = json.load(f)

    print(f"Importando {len(tasks)} tarefas para a lista '{backlog_list['name']}'...")
    for idx, item in enumerate(tasks, start=1):
        title = item.get("title", f"Task {idx}")
        desc = item.get("description", "")
        if "labels" in item and item["labels"]:
            desc += f"\n\n**Labels / Tags:** {', '.join(item['labels'])}"
        if "epic" in item:
            desc = f"**Epic:** {item['epic']}\n\n" + desc

        card = create_card(backlog_list["id"], title, desc)
        print(f"[{idx}/{len(tasks)}] Criado card: {title} (ID: {card['id']})")


def list_tasks(list_name="To Do", board_id=None):
    """Lists cards in a specific column."""
    b_id = board_id or BOARD_ID
    if not b_id:
        print("[ERROR] BOARD_ID is required.")
        sys.exit(1)

    lists = get_board_lists(b_id)
    target_list = next((l for l in lists if l["name"].strip().lower() == list_name.strip().lower()), None)

    if not target_list:
        print(f"[ERROR] Lista '{list_name}' nao encontrada.")
        return []

    cards = trello_request(f"/lists/{target_list['id']}/cards", params={"fields": "name,desc,id"})
    print(f"\n--- Tarefas em '{target_list['name']}' ---")
    for c in cards:
        print(f"ID: {c['id']}")
        print(f"Titulo: {c['name']}")
        print(f"Descricao: {c.get('desc', '')[:120]}...\n")
    return cards


def move_card(card_id, destination_list_name, board_id=None):
    b_id = board_id or BOARD_ID
    lists = get_board_lists(b_id)
    target_list = next((l for l in lists if l["name"].strip().lower() == destination_list_name.strip().lower()), None)
    if not target_list:
        print(f"[ERROR] Destino '{destination_list_name}' nao encontrado.")
        sys.exit(1)

    trello_request(f"/cards/{card_id}", method="PUT", params={"idList": target_list["id"]})
    print(f"[OK] Card {card_id} movido para '{target_list['name']}'")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso:")
        print("  python trello_tool.py list-boards")
        print("  python trello_tool.py setup-board [BOARD_ID]")
        print("  python trello_tool.py import-backlog <caminho_json> [BOARD_ID]")
        print("  python trello_tool.py list-tasks [NOME_DA_LISTA]")
        print("  python trello_tool.py move-card <CARD_ID> <NOME_DA_LISTA>")
        sys.exit(0)

    cmd = sys.argv[1]
    if cmd == "list-boards":
        list_boards()
    elif cmd == "setup-board":
        b_id = sys.argv[2] if len(sys.argv) > 2 else None
        setup_board(b_id)
    elif cmd == "import-backlog":
        if len(sys.argv) < 3:
            print("Informe o arquivo JSON. Ex: python trello_tool.py import-backlog docs/backlog.json")
            sys.exit(1)
        b_id = sys.argv[3] if len(sys.argv) > 3 else None
        import_backlog(sys.argv[2], b_id)
    elif cmd == "list-tasks":
        l_name = sys.argv[2] if len(sys.argv) > 2 else "To Do"
        list_tasks(l_name)
    elif cmd == "move-card":
        if len(sys.argv) < 3:
            print("Uso: python trello_tool.py move-card <CARD_ID> <DESTINATION_LIST>")
            sys.exit(1)
        move_card(sys.argv[2], sys.argv[3])
    else:
        print(f"Comando desconhecido: {cmd}")
