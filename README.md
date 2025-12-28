# Travian Bot

A Python automation bot for Travian Speed Server (gotravspeed.com).

## Features

- **Resource Management**: Increase storage and production
- **Building System**: Upgrade resource fields and buildings
- **Village Management**: Switch between villages, view details
- **Research & Upgrades**: Academy research, Armory/Smithy upgrades
- **Multiple Interfaces**: Full TUI, Minimal CLI, or Classic menu

## Installation

Requires Python 3.10+ and [uv](https://github.com/astral-sh/uv) package manager.

```bash
# Clone the repository
git clone https://github.com/sagarsiwach/pybot0724.git
cd pybot0724

# Install dependencies
uv sync
```

## Usage

### Minimal CLI (Recommended)
```bash
uv run travian-cli
```

Clean, keyboard-driven interface with all features:
- `[1]` Production
- `[2]` Storage
- `[3]` Resource Fields (view & upgrade)
- `[4]` Buildings (view & upgrade)
- `[5]` Village Selection
- `[6]` View Village Details
- `[7-9]` Academy/Armory/Smithy
- `[r]` Refresh | `[q]` Quit

### Full TUI
```bash
uv run travian-tui
```

Rich terminal UI with buttons and panels (requires larger terminal).

### Classic Menu
```bash
uv run travian-bot
```

Original interactive menu system.

## Project Structure

```
bot/
├── cli.py           # Minimal keyboard CLI
├── tui.py           # Full terminal UI (Textual)
├── bot.py           # Classic menu interface
├── session_manager.py   # Login & session handling
├── storage.py       # Storage increase
├── production.py    # Production increase
├── construction.py  # Building/resource upgrades
├── village.py       # Village management
├── database.py      # SQLite database
└── ...
```

## Configuration

Credentials are entered at runtime. No config files needed.

## Dependencies

- `httpx` - Async HTTP client
- `beautifulsoup4` - HTML parsing
- `textual` - Terminal UI framework
- `rich` - Terminal formatting
- `tabulate` - Table formatting

## Disclaimer

This bot is for educational purposes only. Use at your own risk. The developers are not responsible for any account bans or other consequences.

## License

MIT License
