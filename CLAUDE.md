# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

CLI tool that converts text or Markdown files to speech using the ElevenLabs API. Single-file Python project (`tts.py`).

## Commands

```bash
# Run the script (uv handles venv + deps automatically)
uv run tts.py "Hello world"
uv run tts.py -f somefile.md --voice "Rachel"

# Install/sync dependencies
uv sync
```

## Architecture

All logic lives in `tts.py` with four main sections:

- **Markdown stripping** (`strip_markdown`) — regex-based pipeline that removes Markdown syntax (headings, bold, links, code blocks, tables, etc.) so TTS doesn't read formatting characters
- **Voice resolution** (`resolve_voice`, `find_voice_by_name`) — searches ElevenLabs voices by name (partial, case-insensitive) or accepts an exact voice ID; defaults to "George - Warm, Captivating Storyteller" (`JBFqnCBsd6RMkjVDRZzb`)
- **Output path** (`build_output_path`) — generates timestamped filenames like `notes_20260327_142301.mp3`
- **Main CLI** — argparse-based, supports inline text, file input (`-f`), or stdin pipe

## Dependencies

Declared in `pyproject.toml`, locked in `uv.lock`:
- `elevenlabs` — API client
- `python-dotenv` — loads `.env` for API key (optional import, gracefully skipped if missing)

## API Key

Set `ELEVENLABS_API_KEY` in environment or `.env` file. The `--api-key` flag also works.
