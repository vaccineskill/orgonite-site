#!/usr/bin/env node
// extract-images.mjs
// Extracts images from PDFs in ~/Downloads/fb-group-files/ using PyMuPDF
// Saves to public/images/[slug]/ and writes src/data/articleImages.json

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import { execSync, spawnSync } from 'child_process';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const PDF_DIR = '/Users/yoko/Downloads/fb-group-files';
const IMG_OUT_BASE = path.join(__dirname, '../public/images');
const JSON_OUT = path.join(__dirname, '../src/data/articleImages.json');

fs.mkdirSync(IMG_OUT_BASE, { recursive: true });
fs.mkdirSync(path.dirname(JSON_OUT), { recursive: true });

function makeSlug(pdfName) {
  return pdfName
    .replace(/\.pdf$/i, '')
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '');
}

const pdfs = fs.readdirSync(PDF_DIR).filter(f => f.toLowerCase().endsWith('.pdf'));
console.log(`Found ${pdfs.length} PDFs. Extracting images...\n`);

const mapping = {};
let totalImages = 0;
let pdfsWithImages = 0;

const pythonScript = `
import sys
import json
import fitz  # PyMuPDF

pdf_path = sys.argv[1]
out_dir = sys.argv[2]
max_images = int(sys.argv[3])
min_size = 100  # px

doc = fitz.open(pdf_path)
images_saved = []
count = 0

for page_num in range(len(doc)):
    if count >= max_images:
        break
    page = doc[page_num]
    image_list = page.get_images(full=True)
    for img_index, img in enumerate(image_list):
        if count >= max_images:
            break
        xref = img[0]
        try:
            base_image = doc.extract_image(xref)
            image_bytes = base_image["image"]
            w = base_image.get("width", 0)
            h = base_image.get("height", 0)
            if w < ${100} or h < ${100}:
                continue
            out_path = f"{out_dir}/{count + 1}.jpg"
            # Write as JPEG using fitz's pixmap for consistency
            pix = fitz.Pixmap(doc, xref)
            if pix.n > 4:  # CMYK or alpha — convert to RGB
                pix = fitz.Pixmap(fitz.csRGB, pix)
            pix.save(out_path, "jpeg")
            images_saved.append(out_path)
            count += 1
        except Exception as e:
            pass

doc.close()
print(json.dumps(images_saved))
`;

// Write python script to a temp file
const tmpScript = '/tmp/extract_images_orgonite.py';
fs.writeFileSync(tmpScript, pythonScript.replace('${100}', '100').replace('${100}', '100'));

for (const pdf of pdfs) {
  const slug = makeSlug(pdf);
  const outDir = path.join(IMG_OUT_BASE, slug);
  fs.mkdirSync(outDir, { recursive: true });

  const pdfPath = path.join(PDF_DIR, pdf);

  try {
    const result = spawnSync('python3', [tmpScript, pdfPath, outDir, '8'], {
      timeout: 30000,
      encoding: 'utf-8',
    });

    if (result.status !== 0) {
      console.log(`  SKIP ${pdf} (python error: ${result.stderr?.slice(0, 100)})`);
      continue;
    }

    const stdout = result.stdout?.trim();
    if (!stdout) {
      console.log(`  SKIP ${pdf} (no output)`);
      continue;
    }

    let savedPaths;
    try {
      savedPaths = JSON.parse(stdout);
    } catch {
      console.log(`  SKIP ${pdf} (parse error)`);
      continue;
    }

    if (savedPaths.length === 0) {
      console.log(`  ${pdf}: no extractable images`);
      continue;
    }

    // Convert absolute paths to relative URLs (from public/)
    const relPaths = savedPaths.map(p => {
      const rel = path.relative(path.join(__dirname, '../public'), p);
      return rel;
    });

    mapping[slug] = relPaths;
    totalImages += relPaths.length;
    pdfsWithImages++;
    console.log(`  ${pdf}: ${relPaths.length} images -> images/${slug}/`);
  } catch (err) {
    console.log(`  ERROR ${pdf}: ${err.message}`);
  }
}

// Clean up temp script
try { fs.unlinkSync(tmpScript); } catch {}

// Write mapping JSON
fs.writeFileSync(JSON_OUT, JSON.stringify(mapping, null, 2));

console.log(`\nDone!`);
console.log(`  Total images extracted: ${totalImages}`);
console.log(`  PDFs with images: ${pdfsWithImages} / ${pdfs.length}`);
console.log(`  Mapping written to: ${JSON_OUT}`);
