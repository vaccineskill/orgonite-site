import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const SOURCE_DIR = '/Users/yoko/.openclaw/agents/lifecoachmaster/knowledge/orgone';
const OUT_DIR = path.join(__dirname, '../src/content/articles');
const PDF_DIR = '/Users/yoko/orgonite-site/public/pdfs';

fs.mkdirSync(OUT_DIR, { recursive: true });

// Build PDF list for matching
const pdfFiles = fs.existsSync(PDF_DIR)
  ? fs.readdirSync(PDF_DIR).filter(f => f.toLowerCase().endsWith('.pdf'))
  : [];

function normalizeName(name) {
  return name
    .toLowerCase()
    .replace(/\.pdf$|\.md$/i, '')
    .replace(/[_\-]+/g, ' ')
    .replace(/\s+/g, ' ')
    .replace(/[^a-z0-9 ]/g, '')
    .trim();
}

function findMatchingPdf(mdFilename) {
  const mdNorm = normalizeName(mdFilename);

  // Exact normalized match
  for (const pdf of pdfFiles) {
    if (normalizeName(pdf) === mdNorm) return pdf;
  }

  // Partial match: md norm starts with pdf norm or vice versa
  let bestMatch = null;
  let bestScore = 0;
  for (const pdf of pdfFiles) {
    const pdfNorm = normalizeName(pdf);
    // Compute longest common prefix length as a simple score
    let common = 0;
    const minLen = Math.min(mdNorm.length, pdfNorm.length);
    for (let i = 0; i < minLen; i++) {
      if (mdNorm[i] === pdfNorm[i]) common++;
      else break;
    }
    // Also try word overlap score
    const mdWords = new Set(mdNorm.split(' '));
    const pdfWords = pdfNorm.split(' ');
    let wordOverlap = 0;
    for (const w of pdfWords) {
      if (w.length > 2 && mdWords.has(w)) wordOverlap++;
    }
    const score = wordOverlap * 10 + common;
    if (score > bestScore) {
      bestScore = score;
      bestMatch = pdf;
    }
  }
  return bestScore > 5 ? bestMatch : null;
}

function assignCategory(filename) {
  const f = filename.toLowerCase();
  if (/journal|bibliography|annotated|modern_orgone/.test(f)) return 'research-library';
  if (/reich|oranur|contact_with_space|flying_saucer/.test(f)) return 'wilhelm-reich';
  if (/crystal|shungite|stone|gem|mineral|healing|slimspurling|sbb/.test(f)) return 'crystals-and-materials';
  if (/experiment|researchgate|shortened|double.blind|bioenergy/.test(f)) return 'research';
  if (/tower.bust|cloudbust|earth.pipe|holy.hand|hhg|joe.cell|zapper|field.pulser|trinity|how.to.make|directions.for|frequency.gen|howto|orgone.*does.*wonder|operation.*paradise|protect.*property|orgon.*primer|an.intro.*orgone|modern.*orgone.*journal/.test(f)) return 'diy-projects';
  return 'what-is-orgonite';
}

function makeSlug(filename) {
  return filename
    .replace(/\.md$/, '')
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '');
}

function makeTitle(filename) {
  return filename
    .replace(/\.md$/, '')
    .replace(/[_\-]+/g, ' ')
    .replace(/\bpdf\b/gi, '')
    .replace(/\bversion\s*\d+\b/gi, '')
    .replace(/\s+/g, ' ')
    .trim()
    .replace(/\b\w/g, c => c.toUpperCase());
}

function deepClean(content) {
  return content
    // Remove source header line "_Source: xxx.pdf_"
    .replace(/^_Source:.*?_\s*\n/m, '')
    // Remove redundant h1 at very start (it duplicates the page title)
    .replace(/^#\s+[^\n]+\n/, '')
    // Remove page break markers
    .replace(/<!--\s*page\s*\d+\s*-->/gi, '')
    // Remove isolated page numbers (line that is just 1-4 digits, possibly with whitespace)
    .replace(/^\d{1,4}\s*$/gm, '')
    // Remove lines of only dashes/underscores/equals (3+ chars)
    .replace(/^[-_=]{3,}\s*$/gm, '')
    // Remove excessive blank lines (3+ consecutive -> max 2)
    .replace(/\n{3,}/g, '\n\n')
    // Remove "[image]" or "(see image)" PDF placeholders
    .replace(/\[image\]/gi, '')
    .replace(/\(see image\)/gi, '')
    .trim();
}

function extractDescription(content) {
  const lines = content.split('\n');
  for (const line of lines) {
    const trimmed = line.trim();
    if (trimmed && !trimmed.startsWith('#') && !trimmed.startsWith('_') && trimmed.length > 30) {
      return trimmed.slice(0, 155).replace(/"/g, "'");
    }
  }
  return 'A comprehensive guide from the OrgoniteGuide knowledge base.';
}

function estimateReadTime(content) {
  const words = content.split(/\s+/).length;
  return Math.max(1, Math.ceil(words / 200));
}

const files = fs.readdirSync(SOURCE_DIR).filter(f => f.endsWith('.md'));
console.log(`Processing ${files.length} files...`);

// Track slugs for uniqueness
const usedSlugs = new Map();

for (const file of files) {
  const raw = fs.readFileSync(path.join(SOURCE_DIR, file), 'utf-8');
  const cleaned = deepClean(raw);
  const category = assignCategory(file);
  let slug = makeSlug(file);

  // Ensure unique slugs
  if (usedSlugs.has(slug)) {
    usedSlugs.set(slug, usedSlugs.get(slug) + 1);
    slug = slug + '-' + usedSlugs.get(slug);
  } else {
    usedSlugs.set(slug, 1);
  }

  const title = makeTitle(file);
  const description = extractDescription(cleaned);
  const readTime = estimateReadTime(cleaned);

  // Find matching PDF
  const matchedPdf = findMatchingPdf(file);

  const frontmatterLines = [
    '---',
    `title: "${title.replace(/"/g, "'")}"`,
    `slug: "${slug}"`,
    `category: "${category}"`,
    `description: "${description}"`,
    `readTime: ${readTime}`,
    `tags: []`,
    `source: "${file.replace(/\.md$/, '.pdf')}"`,
  ];

  if (matchedPdf) {
    frontmatterLines.push(`pdfFile: "${matchedPdf.replace(/"/g, '\\"')}"`);
  }

  frontmatterLines.push('---', '');

  const frontmatter = frontmatterLines.join('\n');

  fs.writeFileSync(path.join(OUT_DIR, `${slug}.md`), frontmatter + cleaned);
  console.log(`  [${category}] ${slug}${matchedPdf ? ' -> ' + matchedPdf : ' (no PDF match)'}`);
}

console.log('\nDone! Files written to src/content/articles/');
