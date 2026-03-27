#!/usr/bin/env python3
"""
Generate SEO meta descriptions for all articles.
Reads the first meaningful prose paragraph from each article
and condenses it to 140–160 chars.
"""
import re
from pathlib import Path

ARTICLES_DIR = Path(__file__).parent.parent / "src" / "content" / "articles"

# Manual curated descriptions for articles where auto-extraction is poor
CURATED = {
    "a-complete-guide-to-build-a-joe-cell-orgone-energy-2012":
        "Step-by-step guide to building a Joe Cell orgone energy device, covering theory, materials, construction, and troubleshooting for 2012.",
    "an-introduction-to-orgone-matrix-material":
        "Introductory guide to orgone matrix material (orgonite): its resin-metal-crystal composition, how it works, and practical applications.",
    "annotated-bibliography-of-post-reich-orgonomic-journals":
        "Annotated, cross-indexed bibliography of orgonomic journals and research published after Wilhelm Reich, covering key post-Reich literature.",
    "baron-reichenbach-odic-magnetic-letters":
        "Karl von Reichenbach's translated letters on the odic force — a subtle energy he observed in magnets, crystals, and living organisms.",
    "baron-reichenbach-odisch-magnetische-briefe-original-deutsch":
        "Original German text of Baron Karl von Reichenbach's odic-magnetic letters, primary source on the Odic force and sensitive subjects.",
    "bibliography-of-orgonomy-orgone":
        "Comprehensive bibliography of orgonomy and orgone energy literature, listing books, papers, and journals spanning Wilhelm Reich's work.",
    "cloudbuster-cloudbusting-in-arizona-1989":
        "Field report of Wilhelm Reich-inspired cloudbusting operations in Arizona, 1989 — practical drought abatement using orgone weather technology.",
    "cloudbuster-cloudbusting-in-israel-1991":
        "Detailed field report of cloudbusting experiments in Israel in 1991, using orgone energy technology to address severe drought conditions.",
    "cloudbusterorgonegeneratorhowtodisperse":
        "How to build and use a cloudbuster orgone generator to disperse chemtrails, DOR energy, and restore atmospheric balance.",
    "contact-with-space-by-wilhelm-reich":
        "Wilhelm Reich's accounts of UFO encounters during 1950s ORANUR and cloudbusting operations, documenting his 'Contact With Space' research.",
    "don-croft-directions-for-cloudbuster-w-template":
        "Don Croft's complete cloudbuster building guide with plywood templates, copper pipe specs, resin ratios, and deployment instructions.",
    "don-croft-directions-for-earth-pipes":
        "Don Croft's instructions for making and burying earth pipes — orgonite devices designed to heal underground DOR energy and improve soil.",
    "don-croft-directions-for-holy-handgrenade":
        "Don Croft's directions for constructing a Holy Hand Grenade (HHG) orgonite device using resin, metal, quartz crystals, and amethyst.",
    "don-croft-directions-for-how-to-maketbs":
        "Don Croft's step-by-step instructions for making Tower Busters (TBs) — small orgonite discs used to neutralize cell tower radiation.",
    "effects-of-the-orgone-accumulator-blanket-on-free-radicals":
        "Double-blind controlled study on orgone accumulator blanket effects on DHEA levels and free radical markers in 59 subjects over 3 sessions.",
    "flying-saucer-style-wilheim-reich":
        "Wilhelm Reich's perspective on flying saucers, their possible connection to orgone energy, and his observations during cloudbusting operations.",
    "frequency-generator-strategies-for-cloud-busting":
        "Advanced strategies for using frequency generators alongside orgone cloudbusters to enhance atmospheric clearing and weather modification.",
    "how-to-use-orgonite":
        "Practical guide to using orgonite for EMF protection, home energy balancing, sleep improvement, and environmental healing.",
    "howtomaketbs":
        "Complete guide to making Tower Busters (TBs) — affordable orgonite discs cast in muffin tins with metal shavings, resin, and quartz crystals.",
    "james-demeo-orgone-biophysical-research-lab":
        "Overview of James DeMeo's Orgone Biophysical Research Lab: experiments, findings, and contributions to post-Reich orgonomy research.",
    "jon-horrocks-trinity-wand-picture-tutorial-orgonite-wand":
        "Illustrated tutorial by Jon Horrocks for building a Trinity orgonite wand using copper pipes, quartz crystals, and resin casting techniques.",
    "jon-logan-bioenergy-and-orgone-matrix-material-2005":
        "Jon Logan's 2005 paper on bioenergy and orgone matrix material, exploring Kirlian photography, aura measurement, and orgonite effectiveness.",
    "jon-logan-modern-orgone":
        "Jon Logan's guide to modern orgone theory and practice, covering orgonite construction, field effects, and bioenergy principles.",
    "jon-logan-orgonite":
        "Jon Logan's detailed introduction to orgonite: the science behind it, materials used, how to make pieces, and their reported effects.",
    "jon-logan-zpe-orgone-0":
        "Jon Logan's exploration of zero-point energy in relation to orgone: quantum vacuum, free energy concepts, and orgonite as an energy transducer.",
    "light-water":
        "Guide to light water (deuterium-depleted water): its production, biological effects, reported health benefits, and research findings.",
    "magic-power-of-radionics-psionics-and-orgone":
        "Exploration of radionics, psionics, and orgone energy as complementary systems for healing and intent amplification using subtle energy devices.",
    "manuel-de-l-accumulateur-d-orgone":
        "French manual for the orgone accumulator (accumulateur d'orgone): construction, usage, safety guidelines, and Wilhelm Reich's original research.",
    "materials-for-6g-technology-scientists-refine-synthesis-of-rare-iron-oxide-phas":
        "Research on rare epsilon iron oxide phases for 6G technology: synthesis refinement, magnetic properties, and millimeter-wave absorption applications.",
    "michael-gienger-healing-cristals-the-a-z-guide-to-430-gemstones":
        "Michael Gienger's A-Z reference guide to 430 healing gemstones and crystals, covering their properties, uses, and therapeutic applications.",
    "modern-orgone-journal-issue-5":
        "Issue 5 of the Modern Orgone Journal: articles on orgonite construction, field experiments, bioenergy research, and community projects.",
    "operation-paradise-orgonite":
        "Field reports from Operation Paradise — a global orgonite gifting campaign placing Tower Busters near cell towers to neutralize DOR energy.",
    "organite-primer":
        "Beginner's primer on orgonite: what it is, how it is made, the science behind it, and how to start using it for energy work and protection.",
    "orgone-amplifer-article-part-1":
        "Part 1: theory and circuit design of the Orgone Amplifier — a piezoelectric quartz crystal device for generating and transmitting orgone energy.",
    "orgone-and-orgonite-dossier":
        "Comprehensive dossier on orgone energy and orgonite: history, theory, types of devices, experimental evidence, and practical applications.",
    "orgone-does-wonders-pdf-version-1":
        "Testimonials and evidence for orgone energy effects: environmental healing, plant growth, weather changes, and personal energy improvements.",
    "orgone-explained":
        "Clear explanation of orgone energy: Wilhelm Reich's discovery, its properties, how it differs from DOR, and how orgonite interacts with it.",
    "orgone-field-pulser-ii-mobius-driven-bioenergy-generator":
        "Design and theory of the Orgone Field Pulser II — a Möbius coil driven bioenergy generator for amplifying and broadcasting orgone energy fields.",
    "orgonite-1":
        "Introduction to orgonite: the blend of resin, metal, and quartz crystal that converts deadly orgone (DOR) into positive life-force energy (POR).",
    "orgonite-bible":
        "The Orgonite Bible: comprehensive reference covering all aspects of orgonite from foundational theory to advanced device construction and deployment.",
    "orgonite-jon-logan":
        "Jon Logan's authoritative guide to orgonite: materials, construction techniques, device types, and the bioenergy science behind how orgonite works.",
    "protecting-your-property-with-orgonite":
        "Guide to using orgonite for property protection: placement strategies, device types, and field reports on neutralizing EMF and negative energies.",
    "reich-home-book":
        "Introduction to Wilhelm Reich's major works and ideas: character analysis, orgone energy, the orgone accumulator, and Reichian body therapy.",
    "researchgate-orgone-and-water-oct-2022":
        "ResearchGate paper (Oct 2022) examining the interaction between orgone energy and water: structured water effects and biophysical measurements.",
    "robbins-peter-wilhelm-reich-orgone-and-ufos":
        "Peter Robbins' research on Wilhelm Reich's encounters with UFOs during the 1950s and the possible connection between orgone energy and spacecraft.",
    "sbb-coil":
        "Guide to the SBB (Succor Punch Base) coil: construction using Möbius-wound copper wire, double-terminated crystals, and orgonite embedding techniques.",
    "shortened-doubleblind-controlled-experiments":
        "Summary of double-blind controlled orgone experiments testing the biological and physical effects of orgone accumulators on living organisms.",
    "shungite-water":
        "Guide to shungite water: how to make it, the mineralogy of shungite, reported purification properties, and scientific research on its effects.",
    "slimspurling":
        "Guide to Slim Spurling's healing tools: tensor rings, light-life rings, harmonizers, and their applications in environmental and personal energy work.",
    "stone-medicine-a-chinese-medical-guide-to-healing-with-gems-and-minerals":
        "Chinese medical guide to stone medicine: using gems and minerals in Traditional Chinese Medicine for healing, diagnosis, and energy balancing.",
    "the-double-lottchen":
        "Wilhelm Reich's character analysis and body therapy through the story of a patient — illustrating armoring, emotional release, and orgone therapy.",
    "the-oranur-experiment":
        "Wilhelm Reich's ORANUR experiment: the explosive reaction between concentrated orgone energy and nuclear material, and its dangerous aftermath.",
    "zapperinfo":
        "Guide to Hulda Clark-style zappers: how they work, circuit design, frequency selection, and their use in bioelectrical wellness protocols.",
}


def extract_description(content: str, max_len: int = 155) -> str:
    """Extract a description from the first meaningful prose paragraph."""
    # Strip frontmatter
    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            content = parts[2]

    lines = content.split("\n")
    prose_lines = []

    for line in lines:
        s = line.strip()
        # Skip blank lines, headings, images, links-only lines
        if not s:
            if prose_lines:
                break  # end of first paragraph
            continue
        if s.startswith(("#", "!", "[", ">", "|", "```")):
            continue
        if re.match(r"^\d+\s*$", s):  # bare page numbers
            continue
        if len(s) < 20:  # too short to be prose
            continue
        prose_lines.append(s)
        if len(" ".join(prose_lines)) > max_len * 2:
            break

    if not prose_lines:
        return ""

    text = " ".join(prose_lines)
    # Clean up PDF artifacts
    text = re.sub(r"\s+", " ", text).strip()
    text = re.sub(r"[^\x20-\x7E\u00C0-\u024F]", "", text)  # keep latin chars

    if len(text) <= max_len:
        return text

    # Trim to max_len at a word boundary
    trimmed = text[:max_len]
    last_space = trimmed.rfind(" ")
    if last_space > max_len - 20:
        trimmed = trimmed[:last_space]

    return trimmed.rstrip(".,;:") + "."


def process_article(md_path: Path) -> bool:
    """Update the description field in a single article. Returns True if changed."""
    text = md_path.read_text(encoding="utf-8")
    slug = md_path.stem

    # Use curated description if available
    new_desc = CURATED.get(slug)

    if not new_desc:
        # Auto-extract from content
        new_desc = extract_description(text)

    if not new_desc:
        return False

    # Truncate to 160 chars max
    new_desc = new_desc[:160].strip()
    if not new_desc.endswith((".","!","?")):
        # trim to last word
        if len(new_desc) > 155:
            new_desc = new_desc[:155].rsplit(" ", 1)[0]

    # Quote for YAML (use double quotes, escape internal quotes)
    new_desc_yaml = new_desc.replace('"', '\\"')

    # Replace existing description line in frontmatter
    updated = re.sub(
        r'^description:.*$',
        f'description: "{new_desc_yaml}"',
        text,
        count=1,
        flags=re.MULTILINE
    )

    if updated != text:
        md_path.write_text(updated, encoding="utf-8")
        return True

    return False


def main():
    md_files = sorted(ARTICLES_DIR.glob("*.md"))
    print(f"Generating descriptions for {len(md_files)} articles...\n")

    updated = 0
    for f in md_files:
        changed = process_article(f)
        status = "✓ updated" if changed else "· skipped"
        print(f"  {status}  {f.stem}")
        if changed:
            updated += 1

    print(f"\n✅ Done — {updated}/{len(md_files)} descriptions updated")


if __name__ == "__main__":
    main()
