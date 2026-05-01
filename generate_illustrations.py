import argparse
import os
import json
import re
from io import BytesIO
from typing import List
from PIL import Image
from dotenv import load_dotenv
from google import genai
from google.genai import types

# --- Load environment variables ---
load_dotenv()

# --- Gemini Client Initialization ---
# The client automatically looks for the GEMINI_API_KEY environment variable.
try:
    # Initialize client once
    client = genai.Client()
    print("✅ Gemini client initialized.")
except Exception as e:
    print(f"❌ Error initializing Gemini client: {e}")
    print("Please ensure you have set the GEMINI_API_KEY environment variable.")
    # Exit if the client cannot be initialized due to missing key or other error
    exit()

# --- Configuration ---
INPUT_DIR = "scripts"
OUTPUT_DIR = "illustrations"
MODEL_NAME = "gemini-2.5-flash-image"

# --- Fixed illustration style description ---
ILLUSTRATION_STYLE = (
    "in a playful, modern doodle style. Bold, thick black outlines with variable line weight. Use a vibrant and conventional color palette. Solid, warm off-white background. High contrast, clean, and quirky aesthetic. Show only the single object in its most simple, recognizable form. No face, no smiley, no anthropomorphism on inanimate objects. Animals and people should have natural faces. No text, no labels, no words, no letters. No extra decorations, no stars, no sparkles, no background doodles. Minimal detail, keep it clean and uncluttered."
)

## 🏗️ Core Functions

### 1. Prompt Generation

def create_generic_prompt(data: dict) -> str:
    """Create a general illustration prompt from conversation data, including character details."""

    metadata = data.get("metadata", {})
    idea = data.get("idea", {})
    dialogues = data.get("dialogue_list", [])

    title = idea.get("title", "Untitled Scene")
    description = idea.get("description", "")
    language = metadata.get("language", "Unknown language")
    tone = metadata.get("tone", "neutral")
    length = metadata.get("length", "short")

    characters = idea.get("characters", [])
    
    # --- MODIFICATION START: Extract and format detailed character descriptions ---
    character_descriptions = []
    for char in characters:
        name = char.get("name", "Unnamed")
        gender = char.get("gender", "unspecified gender")
        age = char.get("age", "unspecified age")
        character_descriptions.append(f"{name} ({gender}, {age})")
    
    detailed_characters_list = "; ".join(character_descriptions)
    # --- MODIFICATION END ---

    # Sample dialogue preview
    all_lines = " ".join([d.get("text", "") for d in dialogues])
    sample_dialogue_words = all_lines.split()[:40]
    sample_dialogue = " ".join(sample_dialogue_words) + ("..." if len(all_lines.split()) > 40 else "")

    # Build generic illustration prompt
    prompt = (
        f"Create a visually engaging digital illustration. "
        f"{ILLUSTRATION_STYLE} "
        f"Do not include any text or captions in the image. Ensure the image is a single, clear illustration. "
        f"The language of the script is {language}, and the tone is {tone}. "
        f"Scene description: {description or 'No explicit description provided.'} "
        f"The characters involved are: {detailed_characters_list or 'unspecified characters'}. " # Updated line
        f"Depict them naturally in a setting that fits the tone and context. "
        f"The mood and expressions should reflect the feel of this sample dialogue: '{sample_dialogue}'. "
    )

    return prompt

def generate_illustration_from_json(json_path: str, aspect_ratio: str = "9:16"):
    """
    Generate an illustration for one JSON script using Gemini.

    :param json_path: Path to the input JSON file.
    :param aspect_ratio: The desired aspect ratio for the generated image.
    """
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"❌ Error: File not found at {json_path}")
        return
    except json.JSONDecodeError:
        print(f"❌ Error: Invalid JSON format in {json_path}")
        return

    prompt = create_generic_prompt(data)
    print(f"\n🎨 Generating illustration for: {os.path.basename(json_path)}")
    print(f"➡️ Prompt for image generation:\n{prompt[:250]}...\n") # Print a snippet of the new prompt

    # --- GenerateContentConfig ---
    # Configure the response to request an image modality and set the aspect ratio.
    config = types.GenerateContentConfig(
        response_modalities=[types.Modality.IMAGE],
        image_config=types.ImageConfig(
            aspect_ratio=aspect_ratio,
        )
    )

    try:
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=[prompt],
            config=config
        )
    except Exception as e:
        print(f"❌ API Error during generation for {os.path.basename(json_path)}: {e}")
        return False

    # Check 1: Ensure candidates were generated at all.
    if not response.candidates:
        print(f"⚠️ **Response failed to generate candidates** for {os.path.basename(json_path)}.")
        if response.prompt_feedback.block_reason:
            print(f"   Reason: Content was blocked due to {response.prompt_feedback.block_reason}.")
        else:
            print("   Reason: Unknown failure. Check prompt safety or API logs.")
        return False

    # Check 2 (The Fix): Ensure the content object exists to avoid AttributeError.
    first_candidate = response.candidates[0]
    if first_candidate.content is None:
        print(f"⚠️ **Candidate content is None** for {os.path.basename(json_path)}. Likely due to a safety block on the *output*.")
        finish_reason = first_candidate.finish_reason.name if first_candidate.finish_reason else 'Unknown'
        print(f"   Candidate Finish Reason: {finish_reason}.")
        print("   Try simplifying the scene description or checking API safety guidelines.")
        return False

    # Extract and save image(s)
    for part in first_candidate.content.parts:
        if part.inline_data is not None:
            image_data = part.inline_data.data

            try:
                image = Image.open(BytesIO(image_data))
            except Exception as e:
                print(f"❌ Error opening image data for {os.path.basename(json_path)}: {e}")
                continue

            os.makedirs(OUTPUT_DIR, exist_ok=True)
            # --- MODIFICATION START (Preserved existing logic) ---
            base_filename = os.path.splitext(os.path.basename(json_path))[0]
            output_filename = "conversation_" + base_filename + ".png"
            # --- MODIFICATION END ---
            output_path = os.path.join(OUTPUT_DIR, output_filename)

            image.save(output_path)
            print(f"✅ Image saved to {output_path}")
            return True # Assuming only one image is desired per script

    print(f"⚠️ No image data found in model response parts for {os.path.basename(json_path)}. Check API logs.")
    return False


def _sanitize_filename(s: str) -> str:
    s = s.strip().lower()
    s = re.sub(r"\s+", "_", s)
    s = re.sub(r"[^a-z0-9_\-]", "", s)
    return s or "word"


def generate_illustration_from_word(word: str, topic: str | None = None, aspect_ratio: str = "9:16", meaning: str | None = None):
    """Generate an illustration for a single Finnish word.
    Creates a direct, object-focused prompt tailored for concrete/abstract objects without dialogue.
    The illustration is generated as a square and then placed in the center of a 9:16 white canvas.
    Uses the English meaning in the prompt to avoid the model rendering Finnish text in the image.
    """
    # Use the English meaning for the prompt to prevent the model from rendering
    # the Finnish word as text inside the illustration
    display_concept = meaning if meaning else word
    topic_context = f" in the context of {topic}" if topic else ""
    prompt = (
        f"Create a visually engaging digital illustration depicting the concept of '{display_concept}'{topic_context}. "
        f"{ILLUSTRATION_STYLE} "
        f"CRITICAL: The image must contain ABSOLUTELY NO TEXT whatsoever. No words, no letters, no numbers, no labels, no captions, no writing of any kind. "
        f"Focus on depicting the object or concept clearly and centrally positioned in the center of the image. "
        f"The illustrated object should be prominently centered with generous whitespace or soft background around it. "
        f"The image should be a single, clean, minimalist illustration that clearly represents '{display_concept}'. "
        f"Use a vibrant, balanced color palette and modern flat design style. "
    )
    print(f"\n🎨 Generating illustration for word: {word}")
    print(f"➡️ Prompt: {prompt[:200]}...")

    # Request a square aspect ratio for the illustration
    config = types.GenerateContentConfig(
        response_modalities=[types.Modality.IMAGE],
        image_config=types.ImageConfig(aspect_ratio="1:1"),
    )

    try:
        response = client.models.generate_content(model=MODEL_NAME, contents=[prompt], config=config)
    except Exception as e:
        print(f"❌ API Error during generation for word '{word}': {e}")
        return False

    if not response.candidates:
        print(f"⚠️ No candidates generated for word '{word}'")
        return False

    first_candidate = response.candidates[0]
    if first_candidate.content is None:
        print(f"⚠️ Candidate content is None for word '{word}'. Likely safety block.")
        return False

    for part in first_candidate.content.parts:
        if part.inline_data is not None:
            image_data = part.inline_data.data
            try:
                square_image = Image.open(BytesIO(image_data))
            except Exception as e:
                print(f"❌ Error opening image data for word '{word}': {e}")
                continue

            # Parse the target aspect ratio to determine canvas dimensions
            # Default to 9:16, but respect the aspect_ratio parameter if provided
            ratio_parts = aspect_ratio.split(":")
            try:
                ratio_width = int(ratio_parts[0])
                ratio_height = int(ratio_parts[1])
            except (ValueError, IndexError):
                ratio_width, ratio_height = 9, 16

            # Create a high-resolution white canvas with the desired aspect ratio
            # Use 720px width as base for better quality
            canvas_width = 720
            canvas_height = int(canvas_width * ratio_height / ratio_width)
            canvas = Image.new("RGB", (canvas_width, canvas_height), color="white")

            # Resize the square illustration to fit within the canvas (leaving margins)
            margin = 40
            max_size = canvas_width - (2 * margin)
            square_image.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)

            # Calculate position to center the square image
            x_offset = (canvas_width - square_image.width) // 2
            y_offset = (canvas_height - square_image.height) // 2

            # Paste the square image onto the white canvas
            canvas.paste(square_image, (x_offset, y_offset))

            os.makedirs(OUTPUT_DIR, exist_ok=True)
            safe = _sanitize_filename(word)
            topic_fragment = f"_{_sanitize_filename(topic)}" if topic else ""
            output_filename = f"word_{safe}{topic_fragment}.png"
            output_path = os.path.join(OUTPUT_DIR, output_filename)

            canvas.save(output_path, quality=95)
            print(f"✅ Image saved to {output_path} ({canvas_width}x{canvas_height}px)")
            return True

    print(f"⚠️ No image data found in model response parts for word '{word}'.")
    return False

def main():
    """Main function to process all JSON scripts and generate illustrations."""
    parser = argparse.ArgumentParser(description="Generate illustrations from script JSON files or a words JSON list.")
    parser.add_argument("--words-json", help="Path to a JSON file containing an array of words. One illustration will be generated per word.")
    parser.add_argument("--topic", help="Optional topic name used in per-word prompts.")
    parser.add_argument("--aspect", default="9:16", help="Aspect ratio passed to the image generator (default 9:16).")
    args = parser.parse_args()

    # If a words JSON is provided, generate one illustration per word and exit.
    if args.words_json:
        try:
            with open(args.words_json, "r", encoding="utf-8") as f:
                words = json.load(f)
                if not isinstance(words, list):
                    print(f"⚠️ {args.words_json} does not contain a JSON array of words.")
                    return
        except FileNotFoundError:
            print(f"❌ Words file not found: {args.words_json}")
            return
        except json.JSONDecodeError:
            print(f"❌ Invalid JSON in {args.words_json}")
            return

        os.makedirs(OUTPUT_DIR, exist_ok=True)
        
        # Create mapping file to track word->image associations
        mapping = []
        
        for idx, w in enumerate(words):
            word_obj = w if isinstance(w, dict) else {'word': str(w)}
            word = word_obj.get('word', str(w))
            meaning = word_obj.get('translation', None) if isinstance(w, dict) else None
            
            safe = _sanitize_filename(word)
            topic_fragment = f"_{_sanitize_filename(args.topic)}" if args.topic else ""
            output_filename = f"word_{safe}{topic_fragment}.png"
            
            success = generate_illustration_from_word(word, topic=args.topic, aspect_ratio=args.aspect, meaning=meaning)
            if not success:
                import sys
                print(f"❌ Stopping generation due to error on word '{word}'")
                sys.exit(1)
            
            # Record the mapping
            mapping.append({
                "index": idx,
                "word": word,
                "filename": output_filename
            })
        
        # Save mapping file
        mapping_path = os.path.join(OUTPUT_DIR, "mapping.json")
        with open(mapping_path, "w", encoding="utf-8") as f:
            json.dump(mapping, f, ensure_ascii=False, indent=2)
        print(f"✅ Saved word->image mapping to {mapping_path}")
        return

    # Default behavior: process JSON files in the scripts/ directory
    os.makedirs(INPUT_DIR, exist_ok=True)
    files = [f for f in os.listdir(INPUT_DIR) if f.endswith(".json")]
    if not files:
        print(f"⚠️ No JSON files found in {INPUT_DIR}/. Create some script JSON files to begin.")
        return

    for file in files:
        json_path = os.path.join(INPUT_DIR, file)
        success = generate_illustration_from_json(json_path, aspect_ratio=args.aspect)
        if not success:
            import sys
            print(f"❌ Stopping generation due to error on {file}")
            sys.exit(1)


if __name__ == "__main__":
    main()