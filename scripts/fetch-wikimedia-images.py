#!/usr/bin/env python3
"""
Fetch contextually relevant Wikimedia Commons images for each OrgoniteGuide article.
Downloads images and saves attribution data to src/data/wikiImages.json
"""
import json
import os
import re
import time
import urllib.request
import urllib.parse
import urllib.error
from pathlib import Path

OUT_DIR = Path(__file__).parent.parent / "public" / "images" / "wiki"
JSON_OUT = Path(__file__).parent.parent / "src" / "data" / "wikiImages.json"
ARTICLES_DIR = Path(__file__).parent.parent / "src" / "content" / "articles"

OUT_DIR.mkdir(parents=True, exist_ok=True)

# Contextual search terms per article slug
# Each entry: [primary_search, fallback_search]
ARTICLE_SEARCHES = {
    "a-complete-guide-to-build-a-joe-cell-orgone-energy-2012": ["Joe Cell water fuel cell", "electrolysis cell experiment"],
    "an-introduction-to-orgone-matrix-material": ["orgonite resin metal crystal", "epoxy resin casting crystal"],
    "annotated-bibliography-of-post-reich-orgonomic-journals": ["Wilhelm Reich books", "orgone research laboratory"],
    "baron-reichenbach-odic-magnetic-letters": ["Karl von Reichenbach scientist", "odic force magnetism 19th century"],
    "baron-reichenbach-odisch-magnetische-briefe-original-deutsch": ["Karl von Reichenbach", "odic force magnetism"],
    "bibliography-of-orgonomy-orgone": ["orgone energy books Wilhelm Reich", "bioenergy research library"],
    "cloudbuster-cloudbusting-in-arizona-1989": ["cloudbuster orgone weather device", "cumulus cloud formation desert"],
    "cloudbuster-cloudbusting-in-israel-1991": ["cloudbuster weather modification", "drought cloud seeding"],
    "cloudbusterorgonegeneratorhowtodisperse": ["cloudbuster pipe array orgone", "copper pipe rain making"],
    "contact-with-space-by-wilhelm-reich": ["Wilhelm Reich portrait scientist", "UFO flying saucer 1950s"],
    "don-croft-directions-for-cloudbuster-w-template": ["cloudbuster copper pipe orgone", "pipe array rain making device"],
    "don-croft-directions-for-earth-pipes": ["copper pipe earth orgone", "burying copper pipe ground"],
    "don-croft-directions-for-holy-handgrenade": ["orgonite pyramid crystal resin", "quartz crystal resin casting"],
    "don-croft-directions-for-how-to-maketbs": ["orgonite tower buster resin", "muffin tin resin casting orgonite"],
    "effects-of-the-orgone-accumulator-blanket-on-free-radicals": ["orgone accumulator wooden box", "free radical biology antioxidant"],
    "flying-saucer-style-wilheim-reich": ["Wilhelm Reich orgone energy", "flying saucer 1950s UFO"],
    "frequency-generator-strategies-for-cloud-busting": ["frequency generator electronics", "signal generator electronic device"],
    "how-to-use-orgonite": ["orgonite pyramid home decoration", "orgonite crystal resin piece"],
    "howtomaketbs": ["orgonite muffin tin casting", "polyester resin metal shavings"],
    "james-demeo-orgone-biophysical-research-lab": ["biophysical research laboratory", "orgone energy research scientist"],
    "jon-horrocks-trinity-wand-picture-tutorial-orgonite-wand": ["orgonite wand crystal copper", "crystal healing wand quartz"],
    "jon-logan-bioenergy-and-orgone-matrix-material-2005": ["bioenergy field kirlian photograph", "aura energy field bioenergy"],
    "jon-logan-modern-orgone": ["orgone energy field energy", "orgonite modern crystal art"],
    "jon-logan-orgonite": ["orgonite resin metal crystal pyramid", "quartz crystal orgonite art"],
    "jon-logan-zpe-orgone-0": ["zero point energy vacuum quantum", "quantum field energy physics"],
    "light-water": ["deuterium depleted water laboratory", "water molecule structure chemistry"],
    "magic-power-of-radionics-psionics-and-orgone": ["radionics device dial instrument", "psionic energy box instrument"],
    "manuel-de-l-accumulateur-d-orgone": ["orgone accumulator wooden box metal", "Wilhelm Reich orgone box therapy"],
    "materials-for-6g-technology-scientists-refine-synthesis-of-rare-iron-oxide-phas": ["iron oxide nanoparticles material science", "epsilon iron oxide crystal structure"],
    "michael-gienger-healing-cristals-the-a-z-guide-to-430-gemstones": ["healing crystals gemstones collection", "amethyst quartz crystal collection"],
    "modern-orgone-journal-issue-5": ["orgone energy research journal", "biophysics energy field research"],
    "orgone-does-wonders-pdf-version-1": ["orgone energy healing crystal", "orgonite pyramid charged crystal"],
    "operation-paradise-orgonite": ["orgonite gifting tower buster", "orgonite placed cell tower nature"],
    "organite-primer": ["orgonite beginner resin crystal", "orgonite small pyramid piece"],
    "orgone-amplifer-article-part-1": ["orgone accumulator amplifier device", "bioenergy device crystal copper"],
    "orgone-explained": ["orgone energy Wilhelm Reich life force", "bioenergy aura human energy field"],
    "orgone-field-pulser-ii-mobius-driven-bioenergy-generator": ["Mobius coil copper wire", "orgone field generator electronics"],
    "orgone-and-orgonite-dossier": ["orgonite collection types shapes", "orgone energy crystals resin"],
    "orgonite-jon-logan": ["orgonite resin metal art piece", "crystal orgonite pyramids collection"],
    "protecting-your-property-with-orgonite": ["orgonite home protection crystal", "orgonite garden placed crystal"],
    "reich-home-book": ["Wilhelm Reich biography portrait", "orgone accumulator therapy room"],
    "researchgate-orgone-and-water-oct-2022": ["water crystal structure Emoto", "structured water laboratory"],
    "robbins-peter-wilhelm-reich-orgone-and-ufos": ["Wilhelm Reich scientist portrait", "UFO unidentified aerial phenomenon"],
    "sbb-coil": ["SBB coil copper wire spiral", "double terminated crystal coil"],
    "shortened-doubleblind-controlled-experiments": ["double blind clinical trial", "scientific experiment laboratory"],
    "shungite-water": ["shungite stone black mineral Russia", "shungite water purification mineral"],
    "stone-medicine-a-chinese-medical-guide-to-healing-with-gems-and-minerals": ["Chinese traditional medicine herbs minerals", "healing crystals gemstones TCM"],
    "the-oranur-experiment": ["Wilhelm Reich laboratory nuclear", "orgone accumulator experiment"],
    "the-double-lottchen": ["Wilhelm Reich biography", "orgone therapy patient treatment"],
    "orgonite-1": ["orgonite resin metal shavings quartz", "orgonite making tutorial resin"],
    "orgonite-bible": ["orgone generator device crystal", "orgonite tower buster quartz resin"],
    "slimspurling": ["slim spurling rings copper healing", "copper ring healing device"],
    "zapperinfo": ["zapper electronic device health", "Hulda Clark zapper bioelectronics"],
    "effects-of-the-orgone-accumulator-blanket-on-free-radicals": ["orgone blanket wool steel", "free radical antioxidant biology"],
    "light-water": ["heavy water deuterium laboratory", "water purification laboratory"],
}

# Default search by category for articles not in the map
CATEGORY_DEFAULTS = {
    "what-is-orgonite": "orgone energy life force Wilhelm Reich",
    "diy-projects": "orgonite resin crystal pyramid making",
    "wilhelm-reich": "Wilhelm Reich scientist portrait orgone",
    "research": "bioenergy scientific research laboratory",
    "crystals-and-materials": "healing crystals gemstones quartz collection",
    "research-library": "orgone energy research books library",
}

def wikimedia_search(query, limit=5):
    """Search Wikimedia Commons for images matching query."""
    params = urllib.parse.urlencode({
        "action": "query",
        "list": "search",
        "srsearch": query,
        "srnamespace": 6,  # File namespace
        "srlimit": limit,
        "format": "json",
        "origin": "*",
    })
    url = f"https://commons.wikimedia.org/w/api.php?{params}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "OrgoniteGuide/1.0 (educational)"})
        with urllib.request.urlopen(req, timeout=10) as r:
            data = json.loads(r.read())
        results = data.get("query", {}).get("search", [])
        return [r["title"] for r in results if r["title"].startswith("File:")]
    except Exception as e:
        print(f"  Search error: {e}")
        return []

def get_image_info(file_title):
    """Get image URL and attribution info from Wikimedia Commons."""
    params = urllib.parse.urlencode({
        "action": "query",
        "titles": file_title,
        "prop": "imageinfo",
        "iiprop": "url|extmetadata|size",
        "iiurlwidth": 800,
        "format": "json",
        "origin": "*",
    })
    url = f"https://commons.wikimedia.org/w/api.php?{params}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "OrgoniteGuide/1.0 (educational)"})
        with urllib.request.urlopen(req, timeout=10) as r:
            data = json.loads(r.read())
        pages = data.get("query", {}).get("pages", {})
        for page in pages.values():
            info = page.get("imageinfo", [{}])[0]
            if not info:
                continue
            meta = info.get("extmetadata", {})
            w = info.get("width", 0)
            h = info.get("height", 0)
            # Skip tiny images
            if w < 200 or h < 150:
                continue
            # Skip non-image formats
            url_str = info.get("thumburl") or info.get("url", "")
            if not any(url_str.lower().endswith(ext) for ext in [".jpg", ".jpeg", ".png", ".webp"]):
                continue
            license_short = meta.get("LicenseShortName", {}).get("value", "")
            # Only use free licenses
            if license_short and not any(lic in license_short for lic in ["CC", "Public", "cc", "pd", "PD"]):
                continue
            artist = meta.get("Artist", {}).get("value", "")
            # Strip HTML from artist
            artist = re.sub(r"<[^>]+>", "", artist).strip() or "Wikimedia Commons"
            license_url = meta.get("LicenseUrl", {}).get("value", "https://creativecommons.org/licenses/by-sa/4.0/")
            desc = meta.get("ImageDescription", {}).get("value", "")
            desc = re.sub(r"<[^>]+>", "", desc).strip()[:120]
            return {
                "url": url_str,
                "width": w,
                "height": h,
                "artist": artist[:80],
                "license": license_short or "CC BY-SA",
                "licenseUrl": license_url,
                "description": desc,
                "commonsTitle": file_title,
                "commonsUrl": f"https://commons.wikimedia.org/wiki/{urllib.parse.quote(file_title)}",
            }
    except Exception as e:
        print(f"  Info error for {file_title}: {e}")
    return None

def download_image(img_info, dest_path):
    """Download image from Wikimedia to local path."""
    try:
        req = urllib.request.Request(
            img_info["url"],
            headers={"User-Agent": "OrgoniteGuide/1.0 (educational)"}
        )
        with urllib.request.urlopen(req, timeout=15) as r:
            dest_path.write_bytes(r.read())
        return True
    except Exception as e:
        print(f"  Download error: {e}")
        return False

def get_article_category(slug):
    """Read category from article frontmatter."""
    md_file = ARTICLES_DIR / f"{slug}.md"
    if not md_file.exists():
        return "what-is-orgonite"
    content = md_file.read_text()
    m = re.search(r'^category:\s*"?([^"\n]+)"?', content, re.MULTILINE)
    return m.group(1).strip() if m else "what-is-orgonite"

def process_article(slug):
    """Find and download 1-2 Wikimedia images for an article."""
    searches = ARTICLE_SEARCHES.get(slug)
    if not searches:
        cat = get_article_category(slug)
        searches = [CATEGORY_DEFAULTS.get(cat, "orgone energy crystal"), "orgonite quartz resin"]

    img_dir = OUT_DIR / slug
    img_dir.mkdir(parents=True, exist_ok=True)

    found_images = []
    seen_urls = set()

    for query in searches[:2]:  # Try up to 2 search queries
        if len(found_images) >= 2:
            break
        print(f"  🔍 Searching: '{query}'")
        titles = wikimedia_search(query, limit=8)
        time.sleep(0.5)  # Rate limit

        for title in titles:
            if len(found_images) >= 2:
                break
            info = get_image_info(title)
            time.sleep(0.3)  # Rate limit
            if not info:
                continue
            if info["url"] in seen_urls:
                continue
            seen_urls.add(info["url"])

            # Download image
            ext = ".jpg" if info["url"].lower().endswith(".jpg") or "jpeg" in info["url"].lower() else ".png"
            filename = f"{len(found_images) + 1}{ext}"
            dest = img_dir / filename
            print(f"  ⬇ Downloading {title[:60]}...")
            if download_image(info, dest):
                found_images.append({
                    "src": f"/images/wiki/{slug}/{filename}",
                    "alt": info["description"] or title.replace("File:", ""),
                    "artist": info["artist"],
                    "license": info["license"],
                    "licenseUrl": info["licenseUrl"],
                    "commonsUrl": info["commonsUrl"],
                })
                print(f"  ✓ Saved: {filename}")

    return found_images

def main():
    # Load existing data if any
    if JSON_OUT.exists():
        existing = json.loads(JSON_OUT.read_text())
    else:
        existing = {}

    # Get all article slugs
    slugs = [f.stem for f in sorted(ARTICLES_DIR.glob("*.md"))]
    print(f"Processing {len(slugs)} articles...\n")

    results = dict(existing)
    processed = 0

    for slug in slugs:
        # Skip if already has wiki images
        if slug in results and results[slug]:
            print(f"[skip] {slug} (already has {len(results[slug])} images)")
            continue

        print(f"\n[{processed+1}/{len(slugs)}] {slug}")
        images = process_article(slug)
        if images:
            results[slug] = images
            print(f"  → {len(images)} images found")
        else:
            results[slug] = []
            print(f"  → no suitable images found")

        processed += 1
        # Save progress after each article
        JSON_OUT.write_text(json.dumps(results, indent=2, ensure_ascii=False))
        time.sleep(1)  # Be respectful to Wikimedia API

    print(f"\n✅ Done! {sum(1 for v in results.values() if v)} articles have wiki images")
    print(f"📁 JSON saved to: {JSON_OUT}")

if __name__ == "__main__":
    main()
