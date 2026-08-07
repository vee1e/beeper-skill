---
name: beeper
description: Read, search, and send messages through the local Beeper Desktop API (WhatsApp, Instagram, Signal, X, Google Chat, Matrix, and more) that runs on this machine. Use when the user asks to message someone, send a link to a chat/group, read or summarize chat history, find a contact or chat, or post to a WhatsApp group via Beeper.
---

# Beeper

Beeper Desktop exposes a fully local REST API on this machine. It bridges
WhatsApp, Instagram, Signal, X, Google Chat, Matrix, and more. Everything is
local — no cloud service is involved in the send.

## Configuration

- Base URL and token live in `config.json` next to this file:
  - `BEEPER_BASE_URL` — e.g. `http://localhost:23373`. **The port is dynamic**;
    Beeper Desktop can bind to a different port. Verify it before relying on it.
  - `BEEPER_ACCESS_TOKEN` — the `bdapi_...` token shown in Beeper Desktop.
- Environment variables `BEEPER_BASE_URL` / `BEEPER_ACCESS_TOKEN` override the
  config file (useful for scripts that must not hardcode the token).

> Security: the token in `config.json` can send messages as this user from this
> machine. Treat the file as a secret — do not commit it, paste it in chat, or
> include it in logs. Rotate it from Beeper Desktop if it ever leaks.

## Start Here

1. **Verify the server is up and find the current base URL:**
   `python3 <skill-dir>/scripts/beeper.py info`
   (`<skill-dir>` = the directory containing this SKILL.md)
   If the port changed, update `BEEPER_BASE_URL` in `config.json`.

2. **List connected accounts/networks:**
   `python3 <skill-dir>/scripts/beeper.py accounts`

3. **Find the chat you want** (search by name):
   `python3 <skill-dir>/scripts/beeper.py chats search "Akhil" --type single`

## Helper CLI

All commands accept a full chat ID, e.g.
`!K-1XQXXXXXXXXXXXXXXXXXXXXXX:ba_XXX-XXXXXXXXXXXXXXXXXXXXXXX.local-whatsapp.localhost`
(chat IDs are opaque; URL-encoding is handled internally).

| Command | Purpose |
|---|---|
| `beeper.py info` | Server info, including the live base URL and port |
| `beeper.py accounts` | Connected accounts and their `accountID`s |
| `beeper.py chats search QUERY [--type single\|group]` | Find chats by name; shows participants and networks |
| `beeper.py chats list [--limit N]` | Recent chats across all accounts |
| `beeper.py messages CHAT_ID [--limit N] [--after-cursor C]` | Read a chat's message history (chronological) |
| `beeper.py send CHAT_ID "text"` | Send a plain-text message |
| `beeper.py search QUERY [--limit N]` | Search messages globally |

`messages` returns a pagination cursor (`oldestCursor`) when `hasMore` is true;
pass it back via `--after-cursor` to page further back. Note the API caps a
single page at 20 items when paginating.

## Raw REST API (when the CLI is not enough)

The API surface is small and stable. Always send `Authorization: Bearer <token>`.

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/v1/info` | Server info; authoritative base URL/port |
| GET | `/v1/accounts` | Connected accounts (networks) |
| GET | `/v1/chats/search?query=...&type=single&limit=20` | Search chats |
| GET | `/v1/chats?limit=20` | List chats |
| GET | `/v1/chats/{chatID}/messages?limit=20[&cursor=...]` | Read messages (paginate with `oldestCursor`) |
| POST | `/v1/chats/{chatID}/messages` body `{"text": "..."}` | Send a message |
| GET | `/v1/messages/search?query=...` | Search messages |
| POST | `/v1/chats/{chatID}/read` | Mark chat read |
| POST | `/v1/chats/{chatID}/unread` | Mark chat unread |
| POST | `/v1/chats/{chatID}/notify-anyway` | Notify anyway |
| POST | `/v1/chats/{chatID}/archive` | Archive a chat |
| PATCH | `/v1/chats/{chatID}` | Update chat (e.g. set a draft) |
| POST | `/v1/chats/start` | Start a new chat |
| POST | `/v1/chats/{chatID}/messages/{messageID}/reactions` | Add a reaction |
| POST | `/v1/assets/upload` | Upload an attachment |
| GET | `/v1/assets/serve?...` | Fetch an attachment |

## Workflows

### Send a message to a contact or group
1. `beeper.py chats search "<name>"` and pick the right chat (prefer the
   direct/single chat over a group unless the user says group).
2. `beeper.py send "<chat id>" "the message"` — response includes a
   `pendingMessageID`; HTTP 200 means accepted.

### Summarize a chat
1. Find the chat id (`chats search`).
2. Dump history: `beeper.py messages "<chat id>" --limit 200`.
3. For more history, page with `--after-cursor <oldestCursor>` (repeats until
   `hasMore` is false).
4. Sort by timestamp and summarize. Prefer keeping the transcript in files
   under the temp dir rather than spamming the conversation context.

### Verify delivery
If the user asks to confirm a send, re-read the chat with
`beeper.py messages "<chat id>" --limit 5` and look for the senderName/timestamp
of the just-sent message.

## Notes

- Message history depth depends on what Beeper has indexed; recent messages are
  the most reliable.
- Message `text` may contain HTML link markup (e.g. `<a href=...>@Name</a>`);
  strip tags when displaying/parsing.
- `senderID == "@vee1e:beeper.com"` (or the account's self user) marks messages
  the user sent.
- Only send messages the user asked for; do not reply on their behalf.
