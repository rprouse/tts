#!/usr/bin/env python3
"""
tts.py - Convert text or Markdown to speech using ElevenLabs.

Usage:
    tts.py "Hello world"
    tts.py -f README.md
    cat README.md | tts.py
    tts.py "Hello" --voice "Rachel"
    tts.py "Hello" --voice-id JBFqnCBsd6RMkjVDRZzb
    tts.py "Hello" --list-voices
    tts.py -f article.md --output-dir ~/Audio --model eleven_turbo_v2_5

Requirements:
    uv run tts.py  (dependencies installed automatically via pyproject.toml)

API key:
    Set ELEVENLABS_API_KEY in your environment or a .env file.
"""

import argparse
import os
import re
import sys
from datetime import datetime
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv is optional

try:
    from elevenlabs.client import ElevenLabs
except ImportError:
    print("Error: elevenlabs package not installed. Run: pip install elevenlabs", file=sys.stderr)
    sys.exit(1)


# ---------------------------------------------------------------------------
# Markdown stripping
# ---------------------------------------------------------------------------

def strip_markdown(text: str) -> str:
    """Convert Markdown to plain text suitable for TTS."""
    # Fenced code blocks -> describe them briefly
    text = re.sub(r"```[\w]*\n.*?```", "[code block]", text, flags=re.DOTALL)
    text = re.sub(r"`[^`]+`", lambda m: m.group(0).strip("`"), text)

    # Remove HTML tags
    text = re.sub(r"<[^>]+>", "", text)

    # ATX headings: strip # markers but keep text
    text = re.sub(r"^#{1,6}\s+", "", text, flags=re.MULTILINE)

    # Setext headings
    text = re.sub(r"^[=\-]{3,}\s*$", "", text, flags=re.MULTILINE)

    # Bold / italic
    text = re.sub(r"\*{1,3}([^*]+)\*{1,3}", r"\1", text)
    text = re.sub(r"_{1,3}([^_]+)_{1,3}", r"\1", text)

    # Strikethrough
    text = re.sub(r"~~([^~]+)~~", r"\1", text)

    # Links: keep link text
    text = re.sub(r"!?\[([^\]]*)\]\([^)]*\)", r"\1", text)
    text = re.sub(r"!?\[([^\]]*)\]\[[^\]]*\]", r"\1", text)

    # Images
    text = re.sub(r"!\[[^\]]*\]", "[image]", text)

    # Blockquotes
    text = re.sub(r"^>\s?", "", text, flags=re.MULTILINE)

    # Unordered list markers
    text = re.sub(r"^[\*\-\+]\s+", "", text, flags=re.MULTILINE)

    # Ordered list markers
    text = re.sub(r"^\d+\.\s+", "", text, flags=re.MULTILINE)

    # Horizontal rules
    text = re.sub(r"^[-*_]{3,}\s*$", "", text, flags=re.MULTILINE)

    # Tables: strip pipe chars
    text = re.sub(r"\|", " ", text)
    text = re.sub(r"^[\s\-:]+$", "", text, flags=re.MULTILINE)

    # Collapse excess blank lines
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()


# ---------------------------------------------------------------------------
# Voice resolution
# ---------------------------------------------------------------------------

def find_voice_by_name(client: ElevenLabs, name: str):
    """Return the first voice whose name contains `name` (case-insensitive)."""
    response = client.voices.search(search=name)
    if response.voices:
        return response.voices[0]
    return None


def resolve_voice(client: ElevenLabs, voice_arg: str | None, voice_id_arg: str | None):
    """
    Return (voice_id, voice_name).
    Priority: --voice-id > --voice (name search) > default "Rachel".
    """
    if voice_id_arg:
        return voice_id_arg, voice_id_arg

    search_term = voice_arg or "Rachel"
    voice = find_voice_by_name(client, search_term)
    if voice:
        return voice.voice_id, voice.name

    # Fallback: use search term as-is (will fail at API if invalid)
    print(f"Warning: voice '{search_term}' not found; attempting anyway.", file=sys.stderr)
    return search_term, search_term


def list_voices(client: ElevenLabs):
    """Print all available voices."""
    print("\nAvailable voices:\n")
    response = client.voices.get_all()
    voices = sorted(response.voices, key=lambda v: v.name or "")
    col_w = max(len(v.name or "") for v in voices) + 2
    for v in voices:
        category = getattr(v, "category", "") or ""
        print(f"  {(v.name or 'unnamed'):<{col_w}}  {v.voice_id}  ({category})")
    print()


# ---------------------------------------------------------------------------
# Output path
# ---------------------------------------------------------------------------

def build_output_path(output_dir: str, source_name: str) -> Path:
    """Generate a timestamped output filename."""
    out = Path(output_dir).expanduser().resolve()
    out.mkdir(parents=True, exist_ok=True)

    # Derive a base name from the source
    base = Path(source_name).stem if source_name != "<stdin>" else "tts"
    base = re.sub(r"[^\w\-]", "_", base)[:40]
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return out / f"{base}_{timestamp}.mp3"


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Convert text or Markdown to speech via ElevenLabs.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    # Input
    input_group = parser.add_mutually_exclusive_group()
    input_group.add_argument("text", nargs="?", metavar="TEXT",
                             help="Inline text to convert (quote if it contains spaces).")
    input_group.add_argument("-f", "--file", metavar="FILE",
                             help="Path to a .txt or .md file to convert.")

    # Voice selection
    voice_group = parser.add_mutually_exclusive_group()
    voice_group.add_argument("--voice", metavar="NAME",
                             help="Voice name to search for (e.g. 'Rachel', 'Adam').")
    voice_group.add_argument("--voice-id", metavar="ID",
                             help="Exact ElevenLabs voice ID.")

    # Model
    parser.add_argument(
        "--model",
        default="eleven_turbo_v2_5",
        metavar="MODEL_ID",
        help=(
            "Model ID to use. Options:\n"
            "  eleven_turbo_v2_5     - fast, low latency (default)\n"
            "  eleven_multilingual_v2 - highest quality\n"
            "  eleven_flash_v2_5     - ultra-low latency\n"
            "  eleven_v3             - most expressive"
        ),
    )

    # Output
    parser.add_argument("--output-dir", "-o", default=".",
                        metavar="DIR",
                        help="Directory to save the MP3 file (default: current dir).")

    # Utility
    parser.add_argument("--list-voices", action="store_true",
                        help="List all available voices and exit.")
    parser.add_argument("--no-strip-markdown", action="store_true",
                        help="Skip Markdown stripping (pass raw text to TTS).")
    parser.add_argument("--api-key", metavar="KEY",
                        help="ElevenLabs API key (overrides ELEVENLABS_API_KEY env var).")

    args = parser.parse_args()

    # API key
    api_key = args.api_key or os.environ.get("ELEVENLABS_API_KEY")
    if not api_key:
        print(
            "Error: ElevenLabs API key not found.\n"
            "Set ELEVENLABS_API_KEY in your environment or pass --api-key.",
            file=sys.stderr,
        )
        sys.exit(1)

    client = ElevenLabs(api_key=api_key)

    if args.list_voices:
        list_voices(client)
        sys.exit(0)

    # Read input text
    source_name = "<stdin>"
    if args.file:
        source_name = args.file
        try:
            raw = Path(args.file).expanduser().read_text(encoding="utf-8")
        except FileNotFoundError:
            print(f"Error: file not found: {args.file}", file=sys.stderr)
            sys.exit(1)
    elif args.text:
        raw = args.text
    elif not sys.stdin.isatty():
        raw = sys.stdin.read()
    else:
        parser.print_help()
        sys.exit(1)

    # Process text
    if args.no_strip_markdown:
        text = raw
    else:
        text = strip_markdown(raw)

    if not text.strip():
        print("Error: input text is empty after processing.", file=sys.stderr)
        sys.exit(1)

    # Resolve voice
    voice_id, voice_name = resolve_voice(client, args.voice, args.voice_id)
    print(f"Voice:  {voice_name}")
    print(f"Model:  {args.model}")
    print(f"Chars:  {len(text)}")

    # Generate audio
    print("Generating speech...", end=" ", flush=True)
    audio_chunks = client.text_to_speech.convert(
        text=text,
        voice_id=voice_id,
        model_id=args.model,
        output_format="mp3_44100_128",
    )
    audio_bytes = b"".join(audio_chunks)
    print("done.")

    # Write output
    out_path = build_output_path(args.output_dir, source_name)
    out_path.write_bytes(audio_bytes)
    print(f"Saved:  {out_path}")


if __name__ == "__main__":
    main()
