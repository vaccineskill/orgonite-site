#!/usr/bin/env python3
"""
Fetch per-article FAQ pairs from NotebookLM and save to src/data/articleFaqs.json.
Runs queries sequentially (NotebookLM can't parallelize browser sessions).
Rate limit: 50 queries/day on free Google accounts.
"""
import json, subprocess, sys, time, re
from pathlib import Path

SKILLS_DIR = Path.home() / ".claude/skills/notebooklm"
JSON_OUT = Path(__file__).parent.parent / "src" / "data" / "articleFaqs.json"
NOTEBOOK_URL = "https://notebooklm.google.com/notebook/f4e8ddf6-b9f0-45d9-b673-6d7b03c12c17"

# Priority order — most searched topics first
ARTICLES = [
    ("orgone-explained", "what is orgone energy, Wilhelm Reich's discovery, properties of orgone"),
    ("how-to-use-orgonite", "how to use orgonite for home protection, EMF shielding, placement tips"),
    ("howtomaketbs", "how to make Tower Busters, orgonite muffin tin casting, materials needed"),
    ("orgonite-1", "introduction to orgonite, what it is, how it works, resin metal crystal"),
    ("organite-primer", "beginner's guide to orgonite, what is orgonite, how to start"),
    ("don-croft-directions-for-how-to-maketbs", "Don Croft Tower Busters instructions, TB ingredients and assembly"),
    ("effects-of-the-orgone-accumulator-blanket-on-free-radicals", "orgone blanket study, DHEA levels, free radicals research results"),
    ("don-croft-directions-for-cloudbuster-w-template", "how to build a cloudbuster, copper pipes, orgonite base, deployment"),
    ("cloudbusterorgonegeneratorhowtodisperse", "cloudbuster orgone generator, disperse chemtrails, DOR energy"),
    ("orgone-amplifer-article-part-1", "orgone amplifier circuit, piezoelectric quartz, orgone generation"),
    ("shungite-water", "shungite water benefits, how to make shungite water, what is shungite"),
    ("michael-gienger-healing-cristals-the-a-z-guide-to-430-gemstones", "crystal healing, gemstone properties, healing crystals guide"),
    ("the-oranur-experiment", "ORANUR experiment, orgone and nuclear energy reaction, Wilhelm Reich"),
    ("contact-with-space-by-wilhelm-reich", "Wilhelm Reich UFO encounters, orgone and space, flying saucers"),
    ("protecting-your-property-with-orgonite", "property protection orgonite, where to place orgonite, EMF protection home"),
]


def query_faq(slug: str, topic: str) -> list | None:
    """Query NotebookLM for 3 FAQ pairs for a given article."""
    # Clear any stale singleton lock
    lock = SKILLS_DIR / "data/browser_state/browser_profile/SingletonLock"
    lock.unlink(missing_ok=True)

    question = (
        f'Generate exactly 3 FAQ question-answer pairs about the document covering: {topic}. '
        f'Write questions that people actually search on Google. '
        f'Each answer should be 2-3 sentences, accurate and grounded in this notebook only. '
        f'Output ONLY a valid JSON array: [{{"q":"question","a":"answer"}},...]  No other text.'
    )

    result = subprocess.run(
        ["python3", "scripts/run.py", "ask_question.py",
         "--question", question,
         "--notebook-url", NOTEBOOK_URL],
        cwd=str(SKILLS_DIR),
        capture_output=True,
        text=True,
        timeout=350,
    )

    output = result.stdout + result.stderr

    # Extract JSON array from output
    json_match = re.search(r'\[\s*\{.*?\}\s*\]', output, re.DOTALL)
    if json_match:
        try:
            faqs = json.loads(json_match.group())
            return faqs
        except json.JSONDecodeError:
            pass

    # Try to parse manually if JSON was spread across lines
    # Look for the answer block between === markers
    answer_match = re.search(r'={30,}.*?={30,}\n+(.*)', output, re.DOTALL)
    if answer_match:
        answer_text = answer_match.group(1)
        json_match2 = re.search(r'\[\s*\{.*?\}\s*\]', answer_text, re.DOTALL)
        if json_match2:
            try:
                faqs = json.loads(json_match2.group())
                return faqs
            except:
                pass

    print(f"  ⚠ Could not parse JSON from answer for {slug}")
    print(f"  Raw output tail: {output[-500:]}")
    return None


def main():
    # Load existing FAQs
    existing = json.loads(JSON_OUT.read_text()) if JSON_OUT.exists() else {}
    results = dict(existing)

    print(f"Fetching FAQs for {len(ARTICLES)} articles...\n")
    print(f"Rate limit: ~50 queries/day. Already in file: {len(results)} articles.\n")

    for i, (slug, topic) in enumerate(ARTICLES, 1):
        if results.get(slug) and len(results[slug]) >= 2:
            print(f"[{i}/{len(ARTICLES)}] skip {slug} (already has FAQs)")
            continue

        print(f"[{i}/{len(ARTICLES)}] {slug}")
        print(f"  topic: {topic[:60]}...")

        try:
            faqs = query_faq(slug, topic)
        except subprocess.TimeoutExpired:
            print(f"  ❌ Timeout")
            faqs = None
        except Exception as e:
            print(f"  ❌ Error: {e}")
            faqs = None

        if faqs:
            results[slug] = faqs
            print(f"  ✓ Got {len(faqs)} FAQ pairs")
            for faq in faqs:
                print(f"    Q: {faq.get('q','')[:60]}")
        else:
            print(f"  ✗ No FAQs obtained")
            results[slug] = []

        # Save progress after each article
        JSON_OUT.write_text(json.dumps(results, indent=2, ensure_ascii=False))

        # Be polite — wait between queries to avoid rate limiting
        if i < len(ARTICLES):
            print(f"  ... waiting 3s before next query")
            time.sleep(3)

    count_with = sum(1 for v in results.values() if v)
    print(f"\n✅ Done! {count_with}/{len(results)} articles have FAQs")
    JSON_OUT.write_text(json.dumps(results, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
