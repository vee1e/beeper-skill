# beeper-skill

An agent skill for reading, searching, and sending messages through Beeper Desktop.

Beeper Desktop connects WhatsApp, Instagram, Signal, X, Google Chat, Matrix, and more. Everything runs locally on your machine.

## Setup

1. Copy this directory to `~/.agents/skills/beeper/`.
2. Create `config.json` in that directory with your base URL and access token from Beeper Desktop:

```json
{
  "BEEPER_BASE_URL": "http://localhost:23373",
  "BEEPER_ACCESS_TOKEN": "bdapi_your_token_here"
}
```

The port is dynamic. Run `beeper.py info` to find the current one.

## Usage

Run commands through the bundled helper script:

```sh
python3 <skill-dir>/scripts/beeper.py info
python3 <skill-dir>/scripts/beeper.py accounts
python3 <skill-dir>/scripts/beeper.py chats search "Name"
python3 <skill-dir>/scripts/beeper.py messages "CHAT_ID" --limit 100
python3 <skill-dir>/scripts/beeper.py send "CHAT_ID" "Hello"
python3 <skill-dir>/scripts/beeper.py search "keyword"
```

## Security

The token in `config.json` can send messages as you. Do not commit or share it. It is already excluded via `.gitignore`.
