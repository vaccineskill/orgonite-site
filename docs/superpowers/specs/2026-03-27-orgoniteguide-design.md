# OrgoniteGuide.com — Design Spec
**Date:** 2026-03-27
**Status:** Approved by user

---

## 1. Project Overview

A static knowledge-base website about orgone energy, orgonite, and Wilhelm Reich. Built from 53 extracted PDF markdown files (~11.6MB of source content). Primary goals: maximum SEO traffic and AdSense revenue.

**Domain:** orgoniteguide.com
**Source content:** `/Users/yoko/.openclaw/agents/lifecoachmaster/knowledge/orgone/` (53 `.md` files)

---

## 2. Tech Stack

| Layer | Choice | Reason |
|-------|--------|--------|
| Framework | **Astro 4.x** | Static output, zero JS by default, best-in-class Core Web Vitals, native Markdown support |
| Styling | **Tailwind CSS v3** | Utility-first, purges unused CSS, tiny final bundle |
| Hosting | **Netlify (free tier)** | Auto-deploy from git, global CDN, free SSL |
| Search | **Pagefind** | Static search, no backend, runs at build time |
| Analytics | **Plausible / Google Analytics 4** | Privacy-friendly + AdSense-compatible |
| Sitemap | **@astrojs/sitemap** | Auto-generated, submitted to Google Search Console |
| Search | **Pagefind** | Runs at build time (`npx pagefind --site dist`), indexed fields: title, description, body text. Search UI: an inline search bar in the nav that opens a full-screen modal overlay on keystroke. Wired in via Pagefind's default UI bundle imported in a client-side `<script>` in `BaseLayout.astro`. |

---

## 3. Site Structure — Topic Clusters

```
orgoniteguide.com/
├── /                          ← Homepage (hero + 6 category cards + featured articles)
├── /what-is-orgonite/         ← Category hub: 8 articles
│   ├── /orgone-explained/
│   ├── /orgone-vs-orgonite/
│   └── ...
├── /diy-projects/             ← Category hub: 14 articles
│   ├── /how-to-make-tower-buster/
│   ├── /cloudbuster-guide/
│   ├── /holy-handgrenade/
│   └── ...
├── /wilhelm-reich/            ← Category hub: 9 articles
│   ├── /biography/
│   ├── /orgone-accumulator/
│   ├── /contact-with-space/
│   └── ...
├── /research/                 ← Category hub: 10 articles
│   ├── /double-blind-experiments/
│   └── ...
├── /crystals-and-materials/   ← Category hub: 7 articles
│   ├── /healing-crystals-guide/
│   ├── /shungite/
│   └── ...
├── /research-library/         ← Category hub: 5 articles (long-form journals)
├── /sitemap.xml               ← Auto-generated
└── /robots.txt                ← Allows all, points to sitemap
```

**URL rules:** all lowercase, hyphens only, no trailing slash conflicts, keyword-rich slugs derived from PDF filenames.

---

## 4. Visual Design

**Style:** Modern dark + violet accent (openclaw.ai-inspired)
**Color palette:**
- Background: `#09090b` (zinc-950)
- Surface: `#111113` / `#18181b`
- Border: `#1e1e22` / `#27272a`
- Text primary: `#fafafa`
- Text secondary: `#71717a`
- Text muted: `#52525b`
- Accent: `#a78bfa` (violet-400)
- Accent gradient: `linear-gradient(135deg, #a78bfa, #38bdf8)`

**Typography:**
- Headings: Inter, weight 700–800, letter-spacing -0.03em to -0.04em
- Body: Inter, 0.9rem, line-height 1.75, color `#a1a1aa`
- Code/mono: JetBrains Mono

**Key UI patterns:**
- Sticky nav with backdrop blur
- Hero with radial violet glow
- Category cards with icon, title, description, article count pill
- Article cards with tag, title, excerpt, read time
- Smooth hover transitions (border-color, transform)

---

## 5. Page Templates

### Required AdSense pages (must exist before applying)

| Page | Route | Content |
|------|-------|---------|
| About | `/about/` | 150-word description of OrgoniteGuide, its mission, and the source material |
| Privacy Policy | `/privacy-policy/` | Standard AdSense-compatible privacy policy including cookie and data disclosure |
| Contact | `/contact/` | Simple contact form (Netlify Forms, no backend needed) or email mailto link |

These are plain Markdown pages using the base layout (no sidebar, no ads).

### 5a. Homepage (`/`)
1. Sticky nav (logo + 5 category links + search bar)
2. Hero: badge, H1 with gradient em, description, 2 CTAs, 4 stat counters
3. Ad leaderboard 728×90 (below hero)
4. "Browse by Topic" — 3×2 grid of category cards
5. "Most Read Articles" — 2×2 article card grid
6. Footer (copyright, disclaimer, AdSense disclosure)

### 5b. Category Hub (`/[category]/`)
1. Breadcrumb + category H1 + description
2. Ad leaderboard
3. Article list (full-width cards with title, excerpt, tags, read time, CTA button)
4. Pagination (if >10 articles)
5. Related categories sidebar (on desktop)

### 5c. Article Page (`/[category]/[slug]/`)
1. Breadcrumb
2. Tag pills
3. H1 (SEO-optimised, keyword-first)
4. Article meta (source PDF, read time, category)
5. Article body (processed markdown)
6. Ad in-content #1 (after ~400 words)
7. Ad in-content #2 (after ~800 words)
8. Sticky sidebar: Table of Contents + Ad 300×250 (×2) + Related Articles
9. "Next Article" CTA at bottom — next article is the next entry alphabetically by slug within the same category; wraps to first article at category end

**Sidebar mobile behaviour:** below 1024px the sidebar is hidden; TOC moves to a collapsible `<details>` element inserted above the article body; sidebar ads are omitted on mobile (leaderboard + in-content ads only).

### 5d. 404 Page
- On-brand dark design, link back to homepage and category listing

---

## 6. SEO Implementation

### Meta tags (every page)
- `<title>`: `{Keyword-rich title} | OrgoniteGuide`
- `<meta name="description">`: 150–160 chars, includes primary keyword
- `<link rel="canonical">`: absolute URL
- Open Graph: og:title, og:description, og:image (one static 1200×630 image per category, stored in `src/assets/og/[category].png` — 6 images total, created manually or with a simple canvas script at build time)
- Twitter Card: summary_large_image

### Structured data (JSON-LD)
- `Article` schema on every article page (name, author, datePublished, description)
- `BreadcrumbList` on every page
- `WebSite` + `SearchAction` on homepage (enables Google Sitelinks search)
- `FAQPage` schema on category hub pages — 3 hardcoded Q&A pairs per category stored in `src/data/faqs.ts`, written manually (e.g. "What is orgonite?", "How do I make a Tower Buster?"). No auto-generation from article content.

### Content SEO
- H1 contains primary keyword (e.g. "how to make orgonite")
- H2s target secondary keywords / question variants
- First paragraph contains primary keyword within first 100 words
- Internal links: every article links to 3–5 related articles
- Every category hub has a 200-word intro paragraph targeting head keyword
- Image alt text on all decorative elements

### Technical SEO
- `sitemap.xml` auto-generated by `@astrojs/sitemap`; `lastmod` value = the build date (i.e. `new Date().toISOString().split('T')[0]` injected at build time via `astro.config.mjs`)
- `robots.txt` — allows all crawlers, references sitemap
- Core Web Vitals: static HTML, no layout shift, fonts preloaded
- Mobile-first responsive design
- `<html lang="en">` declared
- Preconnect to Google Fonts and AdSense domains

### Article slug strategy
- Derived from PDF filename, cleaned: lowercase, hyphens, keyword-first
- E.g. `orgonite_bible.md` → `/diy-projects/orgonite-bible-complete-guide/`

---

## 7. AdSense Placement — Layout B (Balanced)

| Position | Format | Size | Notes |
|----------|--------|------|-------|
| Below hero / below nav on inner pages | Leaderboard | 728×90 (responsive) | Above the fold but below content start |
| After 3rd paragraph in article body | Rectangle | 336×280 | Injected via rehype plugin after the 3rd `<p>` tag |
| After 7th paragraph in article body | Rectangle | 336×280 | Injected via rehype plugin after the 7th `<p>` tag; if article has <7 paragraphs, place after the last paragraph |
| Sidebar top (sticky) | Medium Rectangle | 300×250 | Sticks as user scrolls |
| Sidebar bottom (sticky) | Medium Rectangle | 300×250 | Paired with related articles |

**Total:** 5 ad slots per article page (within Google's guidelines)
**Auto ads:** disabled — manual placement only for quality control
**Category/home pages:** 1 leaderboard only (less aggressive on landing pages)

---

## 8. Content Processing Pipeline

1. Read each `.md` file from source directory
2. Parse YAML frontmatter (if present) or auto-generate:
   - `title`: cleaned filename → human-readable
   - `category`: assigned by filename keyword matching
   - `description`: first non-empty paragraph, truncated to 155 chars
   - `readTime`: estimated from word count (200 wpm)
   - `tags`: auto-extracted keywords
3. Clean PDF extraction artifacts: page number markers `<!-- page N -->`, excessive whitespace
4. Generate SEO-optimised slug from title
5. Output as Astro content collection entries

**Category assignment rules (evaluated in priority order — first match wins):**
1. `journal`, `bibliography`, `annotated`, `modern_orgone_journal` → `research-library`
2. `reich`, `oranur`, `contact_with_space`, `flying_saucer` → `wilhelm-reich`
3. `crystal`, `shungite`, `stone`, `gem`, `mineral`, `healing`, `slimspurling`, `sbb` → `crystals-and-materials`
4. `experiment`, `research`, `double_blind`, `bioenergy`, `researchgate`, `shortened` → `research`
5. `tower_buster`, `cloudbuster`, `earth_pipe`, `holy_hand`, `HHg`, `joe_cell`, `zapper`, `orgone_field_pulser`, `trinity_wand`, `how_to_make`, `directions_for`, `frequency_generator`, `cloud_bust` → `diy-projects`
6. Everything else → `what-is-orgonite`

**Slug derivation rule:** Use the cleaned source filename only — no suffixes invented. Convert to lowercase, replace spaces/underscores with hyphens, strip non-alphanumeric characters. E.g. `orgonite_bible.md` → `orgonite-bible`, full URL: `/diy-projects/orgonite-bible/`. No AI-generated suffixes.

---

## 9. Build & Deployment

```bash
# Local dev
npm run dev        # http://localhost:4321

# Production build
npm run build      # outputs to ./dist/

# Deploy
# Push to GitHub → Netlify auto-deploys from main branch
# Custom domain: add CNAME in Netlify → point orgoniteguide.com DNS
```

**Build output:** 53+ static HTML files + sitemap.xml + pagefind search index
**Estimated build time:** <30 seconds
**Estimated page size:** <100KB per page (no heavy JS)

---

## 10. Post-Launch SEO Checklist

- [ ] Submit sitemap to Google Search Console
- [ ] Submit sitemap to Bing Webmaster Tools
- [ ] Verify site in AdSense and apply for approval
- [ ] Set up Google Analytics 4 property
- [ ] Add site to Cloudflare (optional, for analytics + CDN)
- [ ] Create `/about` page (required by AdSense for approval)
- [ ] Create `/privacy-policy` page (required by AdSense)
- [ ] Create `/contact` page (required by AdSense)
