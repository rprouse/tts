# tts - Text to Speach

## Setup

```bash
pip install elevenlabs python-dotenv
export ELEVENLABS_API_KEY=your_key_here
chmod +x tts.py
```

Or put the key in a `.env` file in the same directory.

## Usage

```bash
# Inline text
python tts.py "Hello world"

# From a Markdown file
python tts.py -f README.md

# Pipe from stdin
cat article.md | python tts.py

# Select voice by name (fuzzy search)
python tts.py -f notes.md --voice "Adam"

# Select voice by exact ID (from --list-voices)
python tts.py "Hello" --voice-id JBFqnCBsd6RMkjVDRZzb

# Specify output directory
python tts.py -f notes.md --voice "Rachel" --output-dir ~/Audio

# See all available voices
python tts.py --list-voices
```

Output files are auto-named with a timestamp - e.g. `notes_20260327_142301.mp3`.

## Key features

**Markdown stripping** - headings, bold/italic, links, code blocks, tables, and list markers are all cleaned before sending to the API so the TTS output doesn't read out `##` or `**`.

**Voice selection** - `--voice` does a name search (partial match, case-insensitive), `--voice-id` uses an exact ElevenLabs voice ID if you know it. `--list-voices` dumps all voices with their IDs.

**Model selection** - defaults to `eleven_turbo_v2_5` (fast, good quality). Pass `--model eleven_multilingual_v2` for highest quality, `eleven_v3` for most expressive, or `eleven_flash_v2_5` for minimum latency.

**`--no-strip-markdown`** flag if you ever want to pass raw text through without any preprocessing.

## API Key

Log in, then click **Developers** in the left sidebar and select the **API Keys** tab. Or go directly to: **https://elevenlabs.io/app/settings/api-keys**

From there:

1. Click **+ Create API Key**
2. Give it a name (e.g. "tts-cli")
3. Set permissions - for the script, you need at minimum **Text to Speech** and **Voice list access**
4. Click **Create**
5. **Copy the key immediately** - ElevenLabs only shows it once. If you lose it, you'll need to generate a new one.

Then set it in your environment:

```bash
export ELEVENLABS_API_KEY=your_key_here
```

Or drop it in a `.env` file in the same directory as `tts.py`:

```
ELEVENLABS_API_KEY=your_key_here
```
