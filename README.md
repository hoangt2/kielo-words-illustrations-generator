# Kielo — Word list & illustration generator

This repository contains helper scripts designed to create illustrated vocabulary cards in Finnish:

- `generate_word_list.py` — uses Google Gemini to generate a JSON array of Finnish words for a topic, with translations and bilingual example sentences.
- `verify_grammar.py` — verifies and auto-fixes Finnish grammar and naturalness of words and example sentences using Gemini.
- `generate_illustrations.py` — uses Gemini's image generation to create high-resolution illustrations (720x1440px). Generates centered square illustrations on white canvases and creates a mapping file for proper word-image association.
- `add_text_to_illustrations.py` — overlays Finnish word, English translation, and bilingual example sentences on illustrations with consistent formatting and automatic text wrapping.
- `cleanup.py` — removes all generated output files and directories to start fresh.

Prerequisites

- **Create a virtual environment:**

```bash
# macOS/Linux
python3 -m venv venv

# Windows
python -m venv venv
```

- **Activate the virtual environment:**

```bash
# macOS/Linux
source venv/bin/activate

# Windows PowerShell
.\venv\Scripts\Activate.ps1
```

- **Set your Gemini/Google API key in environment variables:**

```bash
# macOS/Linux
export GEMINI_API_KEY="YOUR_API_KEY_HERE"

# Windows PowerShell
$env:GEMINI_API_KEY = "YOUR_API_KEY_HERE"
```

- **Install Python dependencies:**

```bash
pip install -r requirements.txt
```

## Quick Start

The easiest way to generate illustrated vocabulary cards is to use `main.py`, which runs all steps with sensible defaults:

```bash
# Activate virtual environment first
source venv/bin/activate  # macOS/Linux
# .\\venv\\Scripts\\Activate.ps1  # Windows PowerShell

# Generate cards for any topic
python main.py "weather"
python main.py "food"
python main.py "animals"
```

This will:
1. Generate 10 Finnish words with translations and example sentences
2. **Verify Finnish grammar** and naturalness (auto-fixes issues)
3. Create high-resolution illustrations (720x1440px) for each word
4. Add text overlays with proper formatting

**Customization:**
```bash
python main.py "weather" --count 20 --font-size 36
```

Final illustrated cards will be in `illustrations_with_text/`.

---

## Advanced Usage

If you need more control over the generation process, you can run each step individually:

### Generate a list of words

Create a list of Finnish words for a topic (e.g. `weather`):

```powershell
python generate_word_list.py --topic weather --count 30 --output scripts/words_weather.json
```

This writes a UTF-8 JSON array of words at `scripts/words_weather.json`.

Generate illustrations from the words list

Generate one high-resolution illustration per word:

```powershell
python generate_illustrations.py --words-json scripts/words_weather.json --topic weather --aspect 9:16
```

Each generated image:
- Is 720x1440px (high resolution)
- Features a centered square illustration on a white 9:16 canvas
- Is saved to `illustrations/` with filename like `word_aurinko_weather.png`
- Has its word-image association recorded in `illustrations/mapping.json`

Add text overlay to illustrations

Once illustrations are generated, add text overlays with proper word-image matching:

```powershell
python add_text_to_illustrations.py --input-dir illustrations --words-json scripts/words_food.json --output-dir illustrations_with_text
```

This creates images in `illustrations_with_text/` with:
- **Finnish word** centered above the illustration (1.5x font size, dark gray)
- **English translation** centered below the word (smaller, medium gray, dynamic spacing)
- **Finnish example sentence** centered below the image (slate blue)
- **English example sentence translation** centered below (slate blue, auto-scaled to single line)

All text is wrapped and auto-scaled to fit on single lines when needed.

Customization options:
- `--font-size 32` — set font size (default 24; example sentences scale proportionally)
- `--padding 40` — set spacing around text and image (default 40)

**Word-Image Matching:**
The script uses `illustrations/mapping.json` (created during illustration generation) to correctly match each word with its corresponding image, ensuring accurate text overlay regardless of filename sorting.

Default behavior

If you run `generate_illustrations.py` without `--words-json`, it will behave as before and process all
JSON scripts found under the `scripts/` directory.

Complete workflow example

Here's a typical end-to-end workflow to create illustrated vocabulary cards:

```bash
# 1. Activate the virtual environment
# macOS/Linux:
source venv/bin/activate
# Windows PowerShell:
# .\venv\Scripts\Activate.ps1

# 2. Generate a list of Finnish words with translations and bilingual example sentences
python generate_word_list.py --topic food --count 10 --output scripts/words_food.json

# 3. Generate high-resolution illustrations for each word
python generate_illustrations.py --words-json scripts/words_food.json --topic food --aspect 9:16

# 4. Add text overlays with proper word-image matching
python add_text_to_illustrations.py --input-dir illustrations --words-json scripts/words_food.json --output-dir illustrations_with_text --font-size 48

# 5. (Optional) Clean up and start a new topic
python cleanup.py
```

Final illustrated cards are in `illustrations_with_text/`.

Notes

- The scripts prefer the local `google.genai` client (used in `generate_illustrations.py`). If no API key or client
	is available, `generate_word_list.py` falls back to a small built-in vocabulary for a few topics so you can
	continue working offline.
- The word generator requests translations and example sentences directly from Gemini along with each word. Output is a JSON array of objects with `word`, `translation`, `example`, and `example_translation` fields.
- Illustrations are generated at high resolution (720x1440px) with centered square composition on white backgrounds (no people or dialogue).
- A `mapping.json` file is created during illustration generation to ensure accurate word-image associations, preventing mismatches from filename sorting.
- The `add_text_to_illustrations.py` script uses this mapping to correctly overlay text data from the words JSON file onto the corresponding images.
- Text spacing is proportional to font size for consistent visual presentation.
- Example sentences are auto-scaled to fit on single lines.

If you'd like, I can add a helper that converts a words JSON into individual minimal script JSON files in `scripts/`.

**Virtual Environment**

- **Create:**
  - macOS/Linux: `python3 -m venv venv`
  - Windows: `python -m venv venv`
- **Activate:**
  - macOS/Linux: `source venv/bin/activate`
  - Windows PowerShell: `.\venv\Scripts\Activate.ps1`
- **Install dependencies:** `pip install -r requirements.txt`


**Defaults & Model Note**

- **Default model:** `gemini-2.5-flash` is used by default in `generate_word_list.py`. To override, pass `--model <model-name>`.
- **If you see a model-not-found error:** try another model name with `--model`, or update the installed Google packages. The script will try a short list of candidate models when a model fails.

**.env Usage**

- Place a `.env` file at the project root with your key, e.g.: `GEMINI_API_KEY='YOUR_KEY_HERE'`.
- The scripts load `.env` automatically (via `python-dotenv` if available); if the package is not installed a small built-in `.env` parser will still set environment variables.

**Troubleshooting**

- **Missing API key:** verify `.env` contains `GEMINI_API_KEY` or set the env var in your shell.
- **Package/API mismatches:** If the `genai` client errors about missing inputs or unsupported models, activate the venv and upgrade packages:

```powershell
. .\\.venv\\Scripts\\Activate.ps1
pip install --upgrade google-generativeai google-cloud-aiplatform
```

If you'd like, I can add an automatic `ListModels` step to select a compatible text model from your account — tell me if you'd like that behavior.

**Output format from generate_word_list.py**

The generated JSON file contains an array of objects with four fields:

```json
[
  {
    "word": "aurinko",
    "translation": "sun",
    "example": "Aurinko paistaa tänään.",
    "example_translation": "The sun shines today."
  },
  {
    "word": "pilvi",
    "translation": "cloud",
    "example": "Pilviin peittää taivaan.",
    "example_translation": "Clouds cover the sky."
  }
]
```

This data is consumed by `add_text_to_illustrations.py` to overlay text on the generated images.
