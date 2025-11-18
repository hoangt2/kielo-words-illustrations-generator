#!/usr/bin/env python3
"""
generate_word_list.py

Generate a list of Finnish words for a given topic using Google Gemini (via the local
`google.genai` client or fallbacks). The script writes a JSON array of words to an output file
which can be used by `generate_illustrations.py` or other scripts.

Usage examples:
  python generate_word_list.py --topic weather --count 30 --output scripts/words_weather.json

Environment:
  - The repository's `generate_illustrations.py` expects a Gemini client and uses the
    `GEMINI_API_KEY` environment variable. This script will attempt to use that same client.
  - If no Gemini client or key is available, the script falls back to a small built-in
    vocabulary for common topics so you can continue working offline.
"""
import argparse
import json
import os
import sys
from typing import List
try:
    from dotenv import load_dotenv
    _HAS_DOTENV = True
except Exception:
    _HAS_DOTENV = False

# Load environment variables from .env if possible; otherwise attempt a simple manual loader.
if _HAS_DOTENV:
    try:
        load_dotenv()
    except Exception:
        pass
else:
    # manual parse of a .env file (KEY=VALUE lines)
    env_path = ".env"
    if os.path.exists(env_path):
        try:
            with open(env_path, "r", encoding="utf-8") as ef:
                for line in ef:
                    line = line.strip()
                    if not line or line.startswith("#") or "=" not in line:
                        continue
                    k, v = line.split("=", 1)
                    k = k.strip()
                    v = v.strip().strip('"').strip("'")
                    if k and k not in os.environ:
                        os.environ[k] = v
        except Exception:
            pass


FALLBACK_VOCAB = {
    "furniture": [
        "tuoli", "pöytä", "sohva", "sänky", "kaappi", "hylly", "matto", "lamppu"
    ],
}


def parse_args():
    parser = argparse.ArgumentParser(description="Generate Finnish word list using Gemini.")
    parser.add_argument("--topic", required=True, help="Topic name (e.g. weather, furniture)")
    parser.add_argument("--count", type=int, default=30, help="Number of words to generate")
    parser.add_argument("--model", default="gemini-2.5-flash", help="Gemini model name to use")
    parser.add_argument("--output", default="scripts/words.json", help="Output JSON file path")
    parser.add_argument("--api-key-env", default="GEMINI_API_KEY", help="Env var name for Gemini API key")
    return parser.parse_args()


def prompt_for_topic(topic: str, count: int) -> str:
    return (
        "You are a helpful assistant that generates Finnish vocabulary with translations and example sentences. "
        f"For the topic '{topic}', provide exactly {count} distinct Finnish words as a JSON array of objects. "
        "Each object must have exactly four fields (no extra fields): "
        "  - 'word': the Finnish word (single word only) "
        "  - 'translation': the English translation (one word if possible) "
        "  - 'example': a simple example sentence in Finnish "
        "  - 'example_translation': the English translation of the example sentence "
        "Return ONLY valid JSON, no prose. Example format: "
        "[{\"word\":\"aurinko\",\"translation\":\"sun\",\"example\":\"Aurinko paistaa.\",\"example_translation\":\"The sun shines.\"}, ...] "
    )


DEFAULT_MODEL_CANDIDATES = [
    "gemini-2.5-flash",
]


def try_genai_client_generate(prompt: str, model: str | list):
    # Note: this function will attempt to read API key from the environment if present.
    try:
        from google import genai
        from google.genai import types
    except Exception:
        return None

    try:
        # Prefer an explicit API key if provided in the environment
        api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        # Some genai package versions expect configuring the library before creating a Client
        if api_key:
            try:
                cfg = getattr(genai, "configure", None)
                if callable(cfg):
                    cfg(api_key=api_key)
            except Exception:
                pass

        # Create the client (most versions accept no args if configured)
        try:
            client = genai.Client()
        except TypeError:
            # Fallback: try passing api_key explicitly if constructor requires it
            if api_key:
                client = genai.Client(api_key=api_key)
            else:
                raise
    except Exception as e:
        print(f"⚠️  genai.Client() initialization failed: {e}")
        return None

    # Allow passing either a single model name or a list of candidate models
    models_to_try = []
    if isinstance(model, list):
        models_to_try = model
    elif isinstance(model, str) and model:
        models_to_try = [model]
    else:
        models_to_try = DEFAULT_MODEL_CANDIDATES

    for candidate in models_to_try:
        try:
            config = types.GenerateContentConfig(response_modalities=[types.Modality.TEXT])
            response = client.models.generate_content(model=candidate, contents=[prompt], config=config)

            if not getattr(response, "candidates", None):
                continue

            first = response.candidates[0]
            content = getattr(first, "content", None)
            if not content:
                continue

            parts = getattr(content, "parts", None)
            if parts:
                texts = []
                for p in parts:
                    t = getattr(p, "text", None)
                    if t:
                        texts.append(t)
                if texts:
                    print(f"✅ genai: succeeded with model '{candidate}'")
                    return "\n".join(texts)

            # As a last resort return string conversion if non-empty
            s = str(response)
            if s:
                print(f"✅ genai: succeeded with model '{candidate}' (string response)")
                return s
        except Exception as e:
            # Try next candidate model on errors such as model-not-found
            print(f"⚠️ genai model '{candidate}' failed: {e}")
            continue

    # All candidates failed
    return None


def try_generativeai_package(prompt: str, model: str):
    try:
        import google.generativeai as generativeai
    except Exception:
        return None

    try:
        api_key = os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")
        if api_key:
            try:
                generativeai.configure(api_key=api_key)
            except Exception:
                # ignore configure failures; some versions expose different APIs
                pass

        # Try a few possible generation function names across package versions
        gen_func = getattr(generativeai, "generate_text", None) or getattr(generativeai, "generate", None) or getattr(generativeai, "respond", None)
        if gen_func is None:
            return None

        try:
            resp = gen_func(model=model, prompt=prompt)
        except TypeError:
            # Some variants accept different arg names; try minimal call
            resp = gen_func(prompt)

        if hasattr(resp, "text"):
            return resp.text
        if isinstance(resp, dict):
            for k in ("output", "candidates", "content", "text"):
                if k in resp:
                    return json.dumps(resp[k])
        return str(resp)
    except Exception as e:
        print(f"⚠️  google.generativeai call failed: {e}")
        return None


def parse_words_from_text(text: str, expected_count: int) -> List[dict]:
    """Parse text and return list of {word, translation, example, example_translation} dicts."""
    # First, try to extract JSON from markdown code blocks (```json ... ```)
    import re as regex_module
    json_match = regex_module.search(r'```(?:json)?\s*(\[.*?\])\s*```', text, regex_module.DOTALL)
    if json_match:
        try:
            data = json.loads(json_match.group(1))
            if isinstance(data, list):
                result = []
                for item in data:
                    if isinstance(item, dict) and 'word' in item and 'translation' in item and 'example' in item:
                        result.append({
                            'word': str(item['word']).strip(),
                            'translation': str(item['translation']).strip(),
                            'example': str(item['example']).strip(),
                            'example_translation': str(item.get('example_translation', item['example'])).strip()
                        })
                if result:
                    return result[:expected_count]
        except Exception:
            pass

    # Try direct JSON parsing
    try:
        data = json.loads(text)
        if isinstance(data, list):
            result = []
            for item in data:
                if isinstance(item, dict) and 'word' in item and 'translation' in item and 'example' in item:
                    result.append({
                        'word': str(item['word']).strip(),
                        'translation': str(item['translation']).strip(),
                        'example': str(item['example']).strip(),
                        'example_translation': str(item.get('example_translation', item['example'])).strip()
                    })
                elif isinstance(item, str):
                    result.append({
                        'word': item.strip(),
                        'translation': item.strip(),
                        'example': f'Tämä on {item}.',
                        'example_translation': f'This is {item}.'
                    })
            if result:
                return result[:expected_count]
    except Exception:
        pass

    # Fallback: try to find JSON array in text
    try:
        bracket_start = text.find('[')
        bracket_end = text.rfind(']')
        if bracket_start >= 0 and bracket_end > bracket_start:
            json_str = text[bracket_start:bracket_end + 1]
            data = json.loads(json_str)
            if isinstance(data, list):
                result = []
                for item in data:
                    if isinstance(item, dict) and 'word' in item and 'translation' in item and 'example' in item:
                        result.append({
                            'word': str(item['word']).strip(),
                            'translation': str(item['translation']).strip(),
                            'example': str(item['example']).strip(),
                            'example_translation': str(item.get('example_translation', item['example'])).strip()
                        })
                if result:
                    return result[:expected_count]
    except Exception:
        pass

    # Last resort: parse text lines for word patterns
    tokens = []
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith('`') or line.startswith('[') or line.startswith('{'):
            continue
        if line[0].isdigit():
            parts = line.split(".", 1)
            if len(parts) == 2:
                line = parts[1].strip()

        for part in line.split(","):
            w = part.strip().strip('"').strip("'")
            if w and len(w) > 1 and not w.startswith('{') and not w.startswith('['):
                tokens.append(w)

    seen = set()
    out = []
    for t in tokens:
        if t not in seen:
            seen.add(t)
            out.append({
                'word': t,
                'translation': t,
                'example': f'Tämä on {t}.',
                'example_translation': f'This is {t}.'
            })
        if len(out) >= expected_count:
            break
    return out


def main():
    args = parse_args()

    topic = args.topic
    count = args.count
    model = args.model

    prompt = prompt_for_topic(topic, count)

    print("➡️ Attempting to generate words using the installed Gemini client...")
    text = try_genai_client_generate(prompt, model)

    if not text:
        print("➡️ genai client not available or failed — trying google.generativeai package...")
        text = try_generativeai_package(prompt, model)

    if not text:
        print("⚠️ No Gemini client available or API call failed. Falling back to built-in vocab for common topics.")
        fallback_words = FALLBACK_VOCAB.get(topic.lower(), [])
        if not fallback_words:
            print("⚠️ No fallback available for this topic. Try a different topic or install/configure Gemini API.")
            sys.exit(1)
        words = [{'word': w, 'translation': w, 'example': f'Tämä on {w}.', 'example_translation': f'This is {w}.'} for w in fallback_words[:count]]
    else:
        words = parse_words_from_text(text, count)
        if not words:
            print("⚠️ Could not parse words from model output. Falling back to built-in vocab if available.")
            fallback_words = FALLBACK_VOCAB.get(topic.lower(), [])[:count]
            words = [{'word': w, 'translation': w, 'example': f'Tämä on {w}.', 'example_translation': f'This is {w}.'} for w in fallback_words]

    words = words[:count]

    out_dir = os.path.dirname(args.output) or "."
    os.makedirs(out_dir, exist_ok=True)

    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(words, f, ensure_ascii=False, indent=2)

    print(f"✅ Wrote {len(words)} words (with translations and examples) for topic '{topic}' to {args.output}")


if __name__ == "__main__":
    main()
