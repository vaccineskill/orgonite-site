#!/usr/bin/env python3
"""
Fetch CURATED Wikimedia Commons images — specific known files that are
contextually relevant to each OrgoniteGuide article.
"""
import json, os, time, urllib.request, urllib.parse, re
from pathlib import Path

OUT_DIR  = Path(__file__).parent.parent / "public" / "images" / "wiki"
JSON_OUT = Path(__file__).parent.parent / "src" / "data" / "wikiImages.json"

OUT_DIR.mkdir(parents=True, exist_ok=True)

# Curated list: slug → list of specific Wikimedia Commons File: titles
# All chosen for topical relevance and known existence on Commons
CURATED = {
    "orgone-explained": [
        "File:Wilhelm_Reich.jpg",
        "File:Orgone_accumulator.jpg",
    ],
    "how-to-use-orgonite": [
        "File:Quartz_oisan.jpg",
        "File:NatCopper.jpg",
    ],
    "howtomaketbs": [
        "File:Silicone_molds.jpg",
        "File:Quartz_Br%C3%A9sil.jpg",
    ],
    "don-croft-directions-for-how-to-maketbs": [
        "File:Quartz_crystal.jpg",
        "File:Aluminium_shavings.jpg",
    ],
    "don-croft-directions-for-holy-handgrenade": [
        "File:Amethyst._Magaliesburg,_South_Africa.jpg",
        "File:Quartz_crystal.jpg",
    ],
    "don-croft-directions-for-cloudbuster-w-template": [
        "File:Cumulonimbus_cloud_over_Africa.jpg",
        "File:Copper_pipes_at_a_hardware_store.jpg",
    ],
    "don-croft-directions-for-earth-pipes": [
        "File:NatCopper.jpg",
        "File:Copper_pipes_at_a_hardware_store.jpg",
    ],
    "cloudbuster-cloudbusting-in-arizona-1989": [
        "File:Cumulonimbus_cloud_over_Africa.jpg",
        "File:Arizona_desert_with_saguaro.jpg",
    ],
    "cloudbuster-cloudbusting-in-israel-1991": [
        "File:Cumulonimbus_cloud_over_Africa.jpg",
        "File:Negev_desert_02.jpg",
    ],
    "cloudbusterorgonegeneratorhowtodisperse": [
        "File:Cumulus_clouds_in_fair_weather.jpeg",
        "File:Copper_pipe.jpg",
    ],
    "frequency-generator-strategies-for-cloud-busting": [
        "File:Tektronix_465_Oscilloscope.jpg",
        "File:Signal_generator_Hameg_HM8030-6.jpg",
    ],
    "orgone-field-pulser-ii-mobius-driven-bioenergy-generator": [
        "File:Moebius_strip.jpg",
        "File:Copper_wire_spiral.jpg",
    ],
    "sbb-coil": [
        "File:Copper_coil.jpg",
        "File:Double_terminated_quartz_crystal.jpg",
    ],
    "jon-horrocks-trinity-wand-picture-tutorial-orgonite-wand": [
        "File:Quartz_crystal.jpg",
        "File:NatCopper.jpg",
    ],
    "a-complete-guide-to-build-a-joe-cell-orgone-energy-2012": [
        "File:Electrolysis_of_water_labeled.jpg",
        "File:Stainless_Steel_pipes.jpg",
    ],
    "jon-logan-bioenergy-and-orgone-matrix-material-2005": [
        "File:Kirlian_hand.jpg",
        "File:Human_aura_photo.jpg",
    ],
    "jon-logan-modern-orgone": [
        "File:Quartz_Br%C3%A9sil.jpg",
        "File:Amethyst._Magaliesburg,_South_Africa.jpg",
    ],
    "jon-logan-orgonite": [
        "File:Quartz_oisan.jpg",
        "File:Resin_casting_molds.jpg",
    ],
    "orgonite-1": [
        "File:Quartz_crystal.jpg",
        "File:Polyester_resin.jpg",
    ],
    "organite-primer": [
        "File:Quartz_Br%C3%A9sil.jpg",
        "File:NatCopper.jpg",
    ],
    "orgone-and-orgonite-dossier": [
        "File:Orgone_accumulator.jpg",
        "File:Quartz_crystal.jpg",
    ],
    "orgonite-jon-logan": [
        "File:Quartz_crystal.jpg",
        "File:Amethyst._Magaliesburg,_South_Africa.jpg",
    ],
    "protecting-your-property-with-orgonite": [
        "File:Quartz_crystal.jpg",
        "File:Home_garden.jpg",
    ],
    "operation-paradise-orgonite": [
        "File:Cell_tower_in_a_field.jpg",
        "File:Quartz_oisan.jpg",
    ],
    "orgone-does-wonders-pdf-version-1": [
        "File:Orgone_accumulator.jpg",
        "File:Quartz_crystal.jpg",
    ],
    "an-introduction-to-orgone-matrix-material": [
        "File:Epoxy_resin_casting.jpg",
        "File:Metal_shavings.jpg",
    ],
    "magic-power-of-radionics-psionics-and-orgone": [
        "File:Psionics_device.jpg",
        "File:Orgone_accumulator.jpg",
    ],
    "orgone-amplifer-article-part-1": [
        "File:Orgone_accumulator.jpg",
        "File:Quartz_crystal.jpg",
    ],
    "jon-logan-zpe-orgone-0": [
        "File:Vacuum_fluctuations_and_virtual_particles.jpg",
        "File:Quantum_field_theory_Feynman_diagram.png",
    ],
    "light-water": [
        "File:Water_drops_on_a_leaf.jpg",
        "File:Deuterium_lamp_test.jpg",
    ],
    "shungite-water": [
        "File:Shungite.jpg",
        "File:Water_molecule_3D.svg",
    ],
    "researchgate-orgone-and-water-oct-2022": [
        "File:Water_drops_on_a_leaf.jpg",
        "File:Laboratory_glassware_and_equipment.jpg",
    ],
    "effects-of-the-orgone-accumulator-blanket-on-free-radicals": [
        "File:Orgone_accumulator.jpg",
        "File:Free_radical.png",
    ],
    "shortened-doubleblind-controlled-experiments": [
        "File:Clinical_trial_laboratory.jpg",
        "File:Scientific_experiment_controlled_study.jpg",
    ],
    "james-demeo-orgone-biophysical-research-lab": [
        "File:Orgone_accumulator.jpg",
        "File:Research_laboratory_biophysics.jpg",
    ],
    "michael-gienger-healing-cristals-the-a-z-guide-to-430-gemstones": [
        "File:Amethyst._Magaliesburg,_South_Africa.jpg",
        "File:Various_crystal_specimens.jpg",
    ],
    "stone-medicine-a-chinese-medical-guide-to-healing-with-gems-and-minerals": [
        "File:Traditional_Chinese_Medicine_herbs.jpg",
        "File:Jade_stone_mineral.jpg",
    ],
    "slimspurling": [
        "File:Copper_ring_coil.jpg",
        "File:NatCopper.jpg",
    ],
    "zapperinfo": [
        "File:Electronic_circuit_board.jpg",
        "File:9V_battery.jpg",
    ],
    "materials-for-6g-technology-scientists-refine-synthesis-of-rare-iron-oxide-phas": [
        "File:Iron_oxide_nanoparticles.jpg",
        "File:Materials_science_laboratory.jpg",
    ],
    "baron-reichenbach-odic-magnetic-letters": [
        "File:Karl_von_Reichenbach_lithography.jpg",
        "File:Magnetism_field_iron_filing.jpg",
    ],
    "baron-reichenbach-odisch-magnetische-briefe-original-deutsch": [
        "File:Karl_von_Reichenbach_lithography.jpg",
        "File:Magnetism_field_iron_filing.jpg",
    ],
    "the-oranur-experiment": [
        "File:Wilhelm_Reich.jpg",
        "File:Nuclear_radiation_symbol.svg",
    ],
    "flying-saucer-style-wilheim-reich": [
        "File:Wilhelm_Reich.jpg",
        "File:UFO_Farmington_New_Mexico_1950.jpg",
    ],
    "robbins-peter-wilhelm-reich-orgone-and-ufos": [
        "File:Wilhelm_Reich.jpg",
        "File:UFO_Farmington_New_Mexico_1950.jpg",
    ],
    "contact-with-space-by-wilhelm-reich": [
        "File:Wilhelm_Reich.jpg",
        "File:Night_sky_stars_milky_way.jpg",
    ],
    "reich-home-book": [
        "File:Wilhelm_Reich.jpg",
        "File:Orgone_accumulator.jpg",
    ],
    "the-double-lottchen": [
        "File:Wilhelm_Reich.jpg",
        "File:Psychoanalysis_couch.jpg",
    ],
    "annotated-bibliography-of-post-reich-orgonomic-journals": [
        "File:Wilhelm_Reich.jpg",
        "File:Academic_journals_library.jpg",
    ],
    "bibliography-of-orgonomy-orgone": [
        "File:Wilhelm_Reich.jpg",
        "File:Books_library_shelf.jpg",
    ],
    "modern-orgone-journal-issue-5": [
        "File:Orgone_accumulator.jpg",
        "File:Scientific_journal_open.jpg",
    ],
    "manuel-de-l-accumulateur-d-orgone": [
        "File:Orgone_accumulator.jpg",
        "File:Wooden_cabinet_box.jpg",
    ],
}

# Known safe fallback images (definitely exist on Commons, highly relevant)
FALLBACKS = [
    "File:Quartz_crystal.jpg",
    "File:Orgone_accumulator.jpg",
    "File:Wilhelm_Reich.jpg",
]

def get_image_info(file_title):
    """Get image URL and attribution from Wikimedia Commons API."""
    params = urllib.parse.urlencode({
        "action": "query",
        "titles": urllib.parse.unquote(file_title),
        "prop": "imageinfo",
        "iiprop": "url|extmetadata|size",
        "iiurlwidth": 900,
        "format": "json",
        "origin": "*",
    })
    url = f"https://commons.wikimedia.org/w/api.php?{params}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "OrgoniteGuide/1.0"})
        with urllib.request.urlopen(req, timeout=12) as r:
            data = json.loads(r.read())
        pages = data.get("query", {}).get("pages", {})
        for page in pages.values():
            if page.get("missing") is not None:
                return None
            info = page.get("imageinfo", [{}])[0]
            if not info:
                return None
            img_url = info.get("thumburl") or info.get("url", "")
            if not img_url:
                return None
            if not any(img_url.lower().split("?")[0].endswith(ext)
                       for ext in [".jpg", ".jpeg", ".png", ".webp", ".gif"]):
                return None
            w, h = info.get("width", 0), info.get("height", 0)
            if w < 150 or h < 100:
                return None
            meta = info.get("extmetadata", {})
            artist = re.sub(r"<[^>]+>", "", meta.get("Artist", {}).get("value", "")).strip() or "Wikimedia Commons"
            license_short = meta.get("LicenseShortName", {}).get("value", "CC BY-SA 4.0")
            license_url   = meta.get("LicenseUrl", {}).get("value", "https://creativecommons.org/licenses/by-sa/4.0/")
            desc = re.sub(r"<[^>]+>", "", meta.get("ImageDescription", {}).get("value", "")).strip()[:120]
            commons_page  = f"https://commons.wikimedia.org/wiki/{urllib.parse.quote(urllib.parse.unquote(file_title))}"
            return {
                "url": img_url, "width": w, "height": h,
                "artist": artist[:80], "license": license_short,
                "licenseUrl": license_url, "description": desc,
                "commonsUrl": commons_page,
            }
    except Exception as e:
        print(f"    API error for {file_title}: {e}")
    return None

def download_image(img_url, dest_path):
    try:
        req = urllib.request.Request(img_url, headers={"User-Agent": "OrgoniteGuide/1.0"})
        with urllib.request.urlopen(req, timeout=20) as r:
            dest_path.write_bytes(r.read())
        return True
    except Exception as e:
        print(f"    Download error: {e}")
        return False

def process_slug(slug, file_titles):
    img_dir = OUT_DIR / slug
    img_dir.mkdir(parents=True, exist_ok=True)
    saved = []
    idx = 1
    for title in file_titles:
        if len(saved) >= 2:
            break
        print(f"  → {title[:70]}")
        info = get_image_info(title)
        time.sleep(0.4)
        if not info:
            print(f"    ✗ not found / no image")
            continue
        ext = ".png" if info["url"].lower().split("?")[0].endswith(".png") else ".jpg"
        dest = img_dir / f"{idx}{ext}"
        if download_image(info["url"], dest):
            saved.append({
                "src": f"/images/wiki/{slug}/{idx}{ext}",
                "alt": info["description"] or title.replace("File:", ""),
                "artist": info["artist"],
                "license": info["license"],
                "licenseUrl": info["licenseUrl"],
                "commonsUrl": info["commonsUrl"],
            })
            print(f"    ✓ saved as {idx}{ext} ({info['width']}×{info['height']})")
            idx += 1
        time.sleep(0.6)
    return saved

def main():
    existing = json.loads(JSON_OUT.read_text()) if JSON_OUT.exists() else {}
    results = dict(existing)

    print(f"Fetching curated Wikimedia images for {len(CURATED)} articles...\n")

    for i, (slug, titles) in enumerate(CURATED.items(), 1):
        # Skip if already has good images
        if results.get(slug) and len(results[slug]) >= 1:
            print(f"[{i}/{len(CURATED)}] skip {slug} (has {len(results[slug])} images)")
            continue
        print(f"\n[{i}/{len(CURATED)}] {slug}")
        imgs = process_slug(slug, titles)
        if not imgs:
            print(f"  ✗ No images — skipping")
        results[slug] = imgs
        # Save progress incrementally
        JSON_OUT.write_text(json.dumps(results, indent=2, ensure_ascii=False))
        time.sleep(1.0)

    total_with = sum(1 for v in results.values() if v)
    print(f"\n✅ Done! {total_with}/{len(results)} articles have Wikimedia images")
    JSON_OUT.write_text(json.dumps(results, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()
