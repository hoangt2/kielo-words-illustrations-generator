#!/usr/bin/env python3
"""
main.py

Main script to generate illustrated Finnish vocabulary cards with default options.
Users only need to provide a topic argument.

Usage:
    python main.py "weather"
    python main.py "food"
"""

import argparse
import subprocess
import sys
import os
from pathlib import Path


def run_command(cmd, description):
    """Run a command and handle errors."""
    print(f"\n{'='*60}")
    print(f"🚀 {description}")
    print(f"{'='*60}")
    print(f"Running: {' '.join(cmd)}\n")
    
    result = subprocess.run(cmd, capture_output=False, text=True)
    
    if result.returncode != 0:
        print(f"\n❌ Error: {description} failed with exit code {result.returncode}")
        sys.exit(1)
    
    print(f"\n✅ {description} completed successfully!")
    return result


def main():
    parser = argparse.ArgumentParser(
        description="Generate illustrated Finnish vocabulary cards with default options.",
        epilog="Example: python main.py weather"
    )
    parser.add_argument(
        "topic",
        help="Topic for generating vocabulary cards (e.g., weather, food, furniture)"
    )
    parser.add_argument(
        "--count",
        type=int,
        default=10,
        help="Number of words to generate (default: 10)"
    )
    parser.add_argument(
        "--font-size",
        type=int,
        default=48,
        help="Font size for text overlay (default: 48)"
    )
    parser.add_argument(
        "--text-only",
        action="store_true",
        help="Only regenerate text overlays on existing illustrations (skips word generation and image generation)"
    )
    args = parser.parse_args()
    
    topic = args.topic
    count = args.count
    font_size = args.font_size
    text_only = args.text_only
    
    # Define paths
    scripts_dir = Path("scripts")
    illustrations_dir = Path("illustrations")
    output_dir = Path("illustrations_with_text")
    words_json = scripts_dir / f"words_{topic}.json"
    
    # Ensure scripts directory exists
    scripts_dir.mkdir(exist_ok=True)
    
    print(f"\n{'='*60}")
    print(f"🎨 Kielo Word List & Illustration Generator")
    print(f"{'='*60}")
    print(f"Topic: {topic}")
    if not text_only:
        print(f"Word count: {count}")
    print(f"Font size: {font_size}")
    print(f"Mode: {'Text overlay only' if text_only else 'Full generation'}")
    print(f"Output: {output_dir}")
    print(f"{'='*60}\n")
    
    if text_only:
        # Check if required files exist
        if not words_json.exists():
            print(f"❌ Error: Words file not found: {words_json}")
            print(f"   Run without --text-only first to generate words and illustrations.")
            sys.exit(1)
        if not illustrations_dir.exists() or not any(illustrations_dir.glob("*.png")):
            print(f"❌ Error: No illustrations found in: {illustrations_dir}")
            print(f"   Run without --text-only first to generate illustrations.")
            sys.exit(1)
    else:
        # Step 1: Generate word list
        cmd_words = [
            sys.executable,
            "generate_word_list.py",
            "--topic", topic,
            "--count", str(count),
            "--output", str(words_json)
        ]
        run_command(cmd_words, f"Step 1/4: Generating {count} Finnish words for topic '{topic}'")
        
        # Step 2: Verify and fix grammar
        cmd_grammar = [
            sys.executable,
            "verify_grammar.py",
            "--words-json", str(words_json)
        ]
        run_command(cmd_grammar, f"Step 2/4: Verifying Finnish grammar and naturalness")
        
        # Step 3: Generate illustrations
        cmd_illustrations = [
            sys.executable,
            "generate_illustrations.py",
            "--words-json", str(words_json),
            "--topic", topic,
            "--aspect", "9:16"
        ]
        run_command(cmd_illustrations, f"Step 3/4: Generating illustrations for '{topic}'")
    
    # Step 4: Add text overlay (always runs)
    step_label = "Step 1/1" if text_only else "Step 4/4"
    cmd_text = [
        sys.executable,
        "add_text_to_illustrations.py",
        "--input-dir", str(illustrations_dir),
        "--words-json", str(words_json),
        "--output-dir", str(output_dir),
        "--font-size", str(font_size)
    ]
    run_command(cmd_text, f"{step_label}: Adding text overlays to illustrations")

    if not text_only:
        # Step 5: Generate TikTok caption
        caption_file = scripts_dir / f"caption_{topic}.txt"
        cmd_caption = [
            sys.executable,
            "generate_caption.py",
            "--topic", topic,
            "--output", str(caption_file)
        ]
        run_command(cmd_caption, f"Step 5/5: Generating TikTok caption")
    
    # Success message
    print(f"\n{'='*60}")
    print(f"🎉 SUCCESS!")
    print(f"{'='*60}")
    if text_only:
        print(f"✨ Regenerated text overlays for topic: {topic}")
    else:
        print(f"✨ Generated illustrated vocabulary cards for topic: {topic}")
    print(f"📁 Output directory: {output_dir}/")
    print(f"📝 Word list: {words_json}")
    print(f"🖼️  Illustrations: {illustrations_dir}/")
    print(f"🎨 Final cards: {output_dir}/")
    if not text_only:
        caption_file = scripts_dir / f"caption_{topic}.txt"
        print(f"📄 Caption: {caption_file}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
