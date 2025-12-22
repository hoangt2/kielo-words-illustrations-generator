#!/usr/bin/env python3
"""
verify_grammar.py

Verify and fix Finnish grammar in generated word lists.
Checks that Finnish words and example sentences are grammatically correct and natural.

Usage:
    python verify_grammar.py --words-json scripts/words_weather.json
"""

import argparse
import json
import os
try:
    from dotenv import load_dotenv
    _HAS_DOTENV = True
except ImportError:
    _HAS_DOTENV = False

# Load environment variables
if _HAS_DOTENV:
    load_dotenv()

from google import genai
from google.genai import types


def verify_and_fix_grammar(words_data: list, api_key: str = None) -> tuple[list, list]:
    """
    Verify Finnish grammar and naturalness of words and example sentences.
    Returns: (corrected_words_data, issues_found)
    """
    if api_key is None:
        api_key = os.getenv("GEMINI_API_KEY")
    
    if not api_key:
        print("⚠️ No API key found. Skipping grammar verification.")
        return words_data, []
    
    # Initialize Gemini client
    client = genai.Client(api_key=api_key)
    
    issues = []
    corrected_data = []
    
    print(f"\n🔍 Verifying grammar for {len(words_data)} words...\n")
    
    for idx, item in enumerate(words_data, 1):
        word = item.get('word', '')
        translation = item.get('translation', '')
        example = item.get('example', '')
        example_translation = item.get('example_translation', '')
        
        # Create verification prompt
        prompt = f"""You are a Finnish language expert. Verify this vocabulary entry for a {'' if idx == 1 else 'lesson about the topic'}.

Word: {word}
English Translation: {translation}
Finnish Example: {example}
English Translation: {example_translation}

Check for these issues:
1. Is this a real Finnish word (not a placeholder like 'esimerkki', 'sana', 'lukeminen', 'kirja')?
2. Is the Finnish word spelled correctly?
3. Does the English translation accurately match the Finnish word?
4. Is the Finnish example sentence grammatically correct and natural?
5. Does the example use the word meaningfully (not just 'Tämä on...' format)?
6. Does the English translation match the Finnish example?

If EVERYTHING is correct, respond with exactly: CORRECT

If there are ANY issues, provide corrections in this JSON format:
{{
  "word": "corrected_word",
  "translation": "corrected_translation",  
  "example": "natural_example_sentence_in_Finnish",
  "example_translation": "corrected_English_translation",
  "issues": "Explanation of what was wrong"
}}"""

        try:
            response = client.models.generate_content(
                model='gemini-2.0-flash-exp',
                contents=[prompt],
                config=types.GenerateContentConfig(
                    temperature=0.1,
                    response_mime_type="text/plain"
                )
            )
            
            result = response.text.strip()
            
            if "CORRECT" in result:
                print(f"✅ [{idx}/{len(words_data)}] {word} - Grammar OK")
                corrected_data.append(item)
            else:
                # Try to parse JSON correction
                try:
                    # Extract JSON from response
                    json_start = result.find('{')
                    json_end = result.rfind('}') + 1
                    if json_start >= 0 and json_end > json_start:
                        json_str = result[json_start:json_end]
                        correction = json.loads(json_str)
                        
                        issue_msg = correction.get('issues', 'Grammar issues found')
                        issues.append({
                            'index': idx,
                            'word': word,
                            'issue': issue_msg,
                            'correction': correction
                        })
                        
                        print(f"⚠️  [{idx}/{len(words_data)}] {word} - CORRECTED")
                        print(f"   Issue: {issue_msg}")
                        
                        # Use corrected data
                        corrected_item = {
                            'word': correction.get('word', word),
                            'translation': correction.get('translation', translation),
                            'example': correction.get('example', example),
                            'example_translation': correction.get('example_translation', example_translation)
                        }
                        corrected_data.append(corrected_item)
                    else:
                        # Couldn't parse correction, keep original
                        print(f"⚠️  [{idx}/{len(words_data)}] {word} - Could not parse correction, keeping original")
                        corrected_data.append(item)
                except json.JSONDecodeError:
                    print(f"⚠️  [{idx}/{len(words_data)}] {word} - Could not parse correction, keeping original")
                    corrected_data.append(item)
                    
        except Exception as e:
            print(f"❌ [{idx}/{len(words_data)}] {word} - Error during verification: {e}")
            corrected_data.append(item)
    
    # Final duplicate check - remove any duplicates that slipped through
    seen_words = set()
    final_data = []
    duplicates_removed = 0
    
    for item in corrected_data:
        word_lower = item['word'].lower()
        if word_lower not in seen_words:
            seen_words.add(word_lower)
            final_data.append(item)
        else:
            duplicates_removed += 1
            print(f"⚠️  Removed duplicate: {item['word']}")
    
    if duplicates_removed > 0:
        print(f"\n⚠️  Removed {duplicates_removed} duplicate word(s) during verification")
    
    return final_data, issues


def main():
    parser = argparse.ArgumentParser(description="Verify and fix Finnish grammar in word lists.")
    parser.add_argument("--words-json", required=True, help="Path to words JSON file to verify.")
    parser.add_argument("--output", help="Optional output path for corrected JSON (defaults to overwriting input).")
    parser.add_argument("--report", help="Optional path to save grammar issues report.")
    args = parser.parse_args()
    
    words_json = args.words_json
    output_path = args.output or words_json
    
    # Load words data
    try:
        with open(words_json, 'r', encoding='utf-8') as f:
            words_data = json.load(f)
    except Exception as e:
        print(f"❌ Error loading {words_json}: {e}")
        return
    
    if not isinstance(words_data, list):
        print(f"❌ {words_json} must contain a JSON array of words.")
        return
    
    # Verify and fix grammar
    corrected_data, issues = verify_and_fix_grammar(words_data)
    
    # Save corrected data
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(corrected_data, f, ensure_ascii=False, indent=2)
        print(f"\n✅ Saved verified/corrected data to {output_path}")
    except Exception as e:
        print(f"\n❌ Error saving corrected data: {e}")
        return
    
    # Print summary
    print(f"\n{'='*60}")
    print(f"📊 Grammar Verification Summary")
    print(f"{'='*60}")
    print(f"Total words checked: {len(words_data)}")
    print(f"Issues found: {len(issues)}")
    print(f"Corrections made: {len(issues)}")
    
    if issues:
        print(f"\n⚠️  Issues that were corrected:")
        for issue in issues:
            print(f"  • Word #{issue['index']}: {issue['word']}")
            print(f"    {issue['issue']}")
    
    # Save report if requested
    if args.report and issues:
        try:
            with open(args.report, 'w', encoding='utf-8') as f:
                json.dump(issues, f, ensure_ascii=False, indent=2)
            print(f"\n📄 Saved detailed report to {args.report}")
        except Exception as e:
            print(f"\n⚠️ Could not save report: {e}")
    
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
