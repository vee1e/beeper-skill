#!/usr/bin/env python3
"""Beeper Desktop API helper.

Reads BEEPER_BASE_URL and BEEPER_ACCESS_TOKEN from config.json next to this
file (or from the environment, which takes precedence). Uses only the stdlib.

Usage:
  beeper.py info                     # server info incl. current base URL
  beeper.py accounts                 # list connected accounts/networks
  beeper.py chats search QUERY [--type single|group] [--limit N]
  beeper.py chats list [--limit N]   # recent chats across all accounts
  beeper.py messages CHAT_ID [--limit N] [--after-cursor C]
  beeper.py send CHAT_ID "text"      # send a plain-text message
  beeper.py search QUERY [--limit N] # global message search
"""

import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

CONFIG_PATH = Path(__file__).resolve().parent.parent / "config.json"


def load_config():
    cfg = {}
    if CONFIG_PATH.exists():
        cfg = json.loads(CONFIG_PATH.read_text())
    base = os.environ.get("BEEPER_BASE_URL") or cfg.get("BEEPER_BASE_URL")
    token = os.environ.get("BEEPER_ACCESS_TOKEN") or cfg.get("BEEPER_ACCESS_TOKEN")
    if not base or not token:
        sys.exit("error: BEEPER_BASE_URL and BEEPER_ACCESS_TOKEN required (config.json or env)")
    return base.rstrip("/"), token


def api(base, token, method, path, params=None, body=None, timeout=30):
    url = f"{base}{path}"
    if params:
        qs = urllib.parse.urlencode(params)
        url = f"{url}?{qs}"
    data = None
    headers = {"Authorization": f"Bearer {token}"}
    if body is not None:
        data = json.dumps(body).encode()
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read()
            return resp.status, json.loads(raw) if raw else None
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode(errors="replace")


def pretty(obj):
    return json.dumps(obj, indent=2, ensure_ascii=False)


def quote_chat_id(chat_id):
    return urllib.parse.quote(chat_id, safe="")


def cmd_info(base, token, args):
    code, data = api(base, token, "GET", "/v1/info")
    print(f"HTTP {code}")
    print(pretty(data))


def cmd_accounts(base, token, args):
    code, data = api(base, token, "GET", "/v1/accounts")
    print(f"HTTP {code}")
    if not data:
        return
    for acc in data:
        print(f"- {acc.get('network')!r} accountID={acc.get('accountID')} "
              f"user={acc.get('user', {}).get('fullName')} "
              f"status={acc.get('status')}")


def cmd_chats_search(base, token, args):
    params = {"query": args.query, "limit": args.limit or 20}
    if args.type:
        params["type"] = args.type
    code, data = api(base, token, "GET", "/v1/chats/search", params)
    print(f"HTTP {code}")
    for it in (data or {}).get("items", []):
        print(f"id: {it.get('id')}")
        print(f"  {it.get('network')} | type={it.get('type')} | title={it.get('title')}")
        for p in it.get("participants", {}).get("items", []):
            print(f"   - {p.get('fullName')} {p.get('phoneNumber') or ''}"
                  + (" [self]" if p.get("isSelf") else ""))
        print()


def cmd_chats_list(base, token, args):
    code, data = api(base, token, "GET", "/v1/chats", {"limit": args.limit or 20})
    print(f"HTTP {code}")
    for it in (data or {}).get("items", []):
        print(f"id: {it.get('id')}")
        print(f"  {it.get('network')} | type={it.get('type')} | title={it.get('title')}")
        print()


def cmd_messages(base, token, args):
    params = {"limit": args.limit or 50}
    if args.after_cursor:
        params["cursor"] = args.after_cursor
    code, data = api(base, token, "GET",
                     f"/v1/chats/{quote_chat_id(args.chat_id)}/messages", params)
    print(f"HTTP {code}")
    if not data:
        return
    items = data.get("items", [])
    for m in sorted(items, key=lambda x: x.get("timestamp") or ""):
        print(f"[{m.get('timestamp')}] {m.get('senderName')}: {m.get('text')}")
    print(f"\n{len(items)} messages | hasMore={data.get('hasMore')} "
          f"| oldestCursor={data.get('oldestCursor')}")


def cmd_send(base, token, args):
    code, data = api(base, token, "POST",
                     f"/v1/chats/{quote_chat_id(args.chat_id)}/messages",
                     body={"text": args.text})
    print(f"HTTP {code}")
    if data:
        print(pretty(data))


def cmd_search(base, token, args):
    params = {"query": args.query, "limit": args.limit or 20}
    code, data = api(base, token, "GET", "/v1/messages/search", params)
    print(f"HTTP {code}")
    for it in (data or {}).get("items", []):
        print(f"[{it.get('timestamp')}] {it.get('chatID')}")
        print(f"  {it.get('senderName')}: {it.get('text')}")
        print()


def main():
    base, token = load_config()
    p = argparse.ArgumentParser(description="Beeper Desktop API helper")
    sub = p.add_subparsers(dest="cmd", required=True)

    pi = sub.add_parser("info")
    pi.set_defaults(fn=cmd_info)
    pa = sub.add_parser("accounts")
    pa.set_defaults(fn=cmd_accounts)

    s = sub.add_parser("chats")
    ssub = s.add_subparsers(dest="sub", required=True)
    ps = ssub.add_parser("search")
    ps.add_argument("query")
    ps.add_argument("--type", choices=["single", "group"])
    ps.add_argument("--limit", type=int)
    ps.set_defaults(fn=cmd_chats_search)
    pl = ssub.add_parser("list")
    pl.add_argument("--limit", type=int)
    pl.set_defaults(fn=cmd_chats_list)

    pm = sub.add_parser("messages")
    pm.add_argument("chat_id")
    pm.add_argument("--limit", type=int)
    pm.add_argument("--after-cursor", dest="after_cursor")
    pm.set_defaults(fn=cmd_messages)

    ps2 = sub.add_parser("send")
    ps2.add_argument("chat_id")
    ps2.add_argument("text")
    ps2.set_defaults(fn=cmd_send)

    pg = sub.add_parser("search")
    pg.add_argument("query")
    pg.add_argument("--limit", type=int)
    pg.set_defaults(fn=cmd_search)

    args = p.parse_args()
    args.fn(base, token, args)


if __name__ == "__main__":
    main()
