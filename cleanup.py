#!/usr/bin/env python3
"""
cleanup.py

Remove all generated output files and directories to start fresh.
This script deletes:
  - illustrations/ (generated illustration images and mapping)
  - illustrations_with_text/ (illustrations with text overlays)
  - scripts/words_*.json (generated word lists)

Usage:
  python cleanup.py
"""
import os
import shutil
import sys


def cleanup():
    """Remove all generated output files and directories."""
    
    # Directories to remove
    dirs_to_remove = [
        "illustrations",
        "illustrations_with_text",
    ]
    
    # File patterns to remove from scripts/
    script_files_to_remove = []
    scripts_dir = "scripts"
    if os.path.exists(scripts_dir):
        for f in os.listdir(scripts_dir):
            if f.startswith("words_") and f.endswith(".json"):
                script_files_to_remove.append(os.path.join(scripts_dir, f))
    
    # Remove directories
    removed_count = 0
    for dir_path in dirs_to_remove:
        if os.path.exists(dir_path):
            try:
                shutil.rmtree(dir_path)
                print(f"✅ Removed directory: {dir_path}")
                removed_count += 1
            except Exception as e:
                print(f"❌ Error removing directory {dir_path}: {e}")
        else:
            print(f"⚠️ Directory not found: {dir_path}")
    
    # Remove script files
    for file_path in script_files_to_remove:
        try:
            os.remove(file_path)
            print(f"✅ Removed file: {file_path}")
            removed_count += 1
        except Exception as e:
            print(f"❌ Error removing file {file_path}: {e}")
    
    # Recreate empty directories
    for dir_path in dirs_to_remove:
        try:
            os.makedirs(dir_path, exist_ok=True)
            print(f"📁 Created directory: {dir_path}")
        except Exception as e:
            print(f"❌ Error creating directory {dir_path}: {e}")
    
    print(f"\n✅ Cleanup complete! Removed {removed_count} items and recreated directories.")
    print("Ready to generate new content.")


if __name__ == "__main__":
    try:
        cleanup()
    except Exception as e:
        print(f"❌ Cleanup failed: {e}")
        sys.exit(1)
