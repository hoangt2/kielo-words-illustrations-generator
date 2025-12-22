#!/usr/bin/env python3
"""
generate_caption.py

Generate a short, engaging TikTok caption in both Finnish and English for a given topic.
"""
import argparse
import os
import sys

try:
    from dotenv import load_dotenv
    _HAS_DOTENV = True
except Exception:
    _HAS_DOTENV = False

if _HAS_DOTENV:
    try:
        load_dotenv()
    except Exception:
        pass


def get_genai_client():
    """Initialize and return the Gemini client."""
    try:
        from google import genai
    except Exception:
        return None

    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if api_key:
        try:
            cfg = getattr(genai, "configure", None)
            if callable(cfg):
                cfg(api_key=api_key)
        except Exception:
            pass
    
    try:
        if api_key:
            return genai.Client(api_key=api_key)
        return genai.Client()
    except Exception as e:
        print(f"⚠️  genai.Client() initialization failed: {e}")
        return None



FALLBACK_CAPTIONS = {
    "furniture": (
        "Sisusta kotisi tyylillä! 🛋️✨\n"
        "Decorate your home with style! 🛋️✨"
    ),
    "weather": (
        "Opi sääsanoja! ☀️🌧️\n"
        "Learn weather words! ☀️🌧️"
    ),
    "default": (
        "Opi uutta sanastoa! 📚🇫🇮\n"
        "Learn new vocabulary! 📚🇫🇮"
    )
}

def generate_caption(topic, model="gemini-2.5-flash"):
    client = get_genai_client()
    if not client:
        print("⚠️  Gemini client not available. Using fallback caption.")
        return FALLBACK_CAPTIONS.get(topic, FALLBACK_CAPTIONS["default"])

    prompt = (
        f"Create a short, engaging TikTok caption for a video about learning Finnish vocabulary related to '{topic}'. "
        "The caption should be in both Finnish and English. "
        "It should be fun, encouraging, and include appropriate emojis. "
        "Format the output strictly as:\n"
        "Finnish Caption\n"
        "English Caption\n"
        "\n"
        "Example:\n"
        "Opi uusia sanoja säästä! ☀️🌧️\n"
        "Learn new words about weather! ☀️🌧️"
    )

    try:
        from google.genai import types
        config = types.GenerateContentConfig(response_modalities=[types.Modality.TEXT])
        response = client.models.generate_content(model=model, contents=[prompt], config=config)
        
        if response.text:
            return response.text.strip()
            
    except Exception as e:
        print(f"❌ Error generating caption: {e}")
        
    print("⚠️  Generation failed. Using fallback caption.")
    return FALLBACK_CAPTIONS.get(topic, FALLBACK_CAPTIONS["default"])


def main():
    parser = argparse.ArgumentParser(description="Generate TikTok captions.")
    parser.add_argument("--topic", required=True, help="Topic of the content")
    parser.add_argument("--output", help="Output file to save the caption")
    parser.add_argument("--model", default="gemini-2.5-flash", help="Gemini model to use")
    
    args = parser.parse_args()
    
    print(f"✍️  Generating caption for topic: '{args.topic}'...")
    caption = generate_caption(args.topic, args.model)
    
    if caption:
        print("\n✨ Generated Caption:\n")
        print(caption)
        print("\n" + "="*40 + "\n")
        
        if args.output:
            try:
                os.makedirs(os.path.dirname(args.output), exist_ok=True)
                with open(args.output, "w", encoding="utf-8") as f:
                    f.write(caption)
                print(f"✅ Caption saved to: {args.output}")
            except Exception as e:
                print(f"❌ Error saving caption: {e}")
    else:
        print("❌ Failed to generate caption.")
        sys.exit(1)


if __name__ == "__main__":
    main()
