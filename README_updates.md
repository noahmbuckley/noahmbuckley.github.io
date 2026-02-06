# Website Updates (Feb 2026)

## Changes Made

### 1. Layout Improvements
- **Wider sidebar**: Increased from ~200px to 260px for better prominence
- **Better centering**: Added 80px left margin to content area for improved balance
- **Responsive**: Layout adjusts appropriately on mobile devices

### 2. SEO Optimization
- Added comprehensive meta descriptions to all pages
- Configured Open Graph and Twitter Card tags for social sharing
- Added structured keywords for search engines
- Enabled sitemap generation
- Added site-url configuration for proper indexing
- Set up Google Analytics placeholder (update with your GA4 ID)

### 3. CV System
- Created markdown-based CV in `../cv/` directory
- Supports multiple output formats:
  - HTML (for web viewing)
  - PDF (for download, matches current CV style)
  - LaTeX (can export if needed)
- Build script (`cv/build_cv.sh`) generates all formats
- Easy to maintain - edit one markdown file, get all formats

## Building the Website

From the `website/` directory:

```bash
quarto render
```

This will regenerate all HTML files in the `docs/` folder.

## Building the CV

From the `cv/` directory:

```bash
./build_cv.sh
```

This creates HTML and PDF versions of the CV.

## Publishing

The site is configured for GitHub Pages. After making changes:

```bash
cd website/
quarto render
cd docs/
git add .
git commit -m "Update website"
git push
```

## Creating Unlisted Pages

To create a page that's not in the sidebar menu:

1. Create a `.qmd` file in the website directory (e.g., `hidden-page.qmd`)
2. Don't add it to `_quarto.yml` sidebar contents
3. The page will be accessible at `/hidden-page.html` but won't appear in navigation

To make it truly hidden from search engines, add to the page YAML:
```yaml
---
title: "Hidden Page"
robots: noindex, nofollow
---
```

## Google Analytics

To enable analytics:
1. Get your Google Analytics 4 (GA4) measurement ID
2. In `_quarto.yml`, replace `"G-XXXXXXXXXX"` with your actual ID

## Sitemap

A sitemap is automatically generated at `docs/sitemap.xml` when you render the site. Submit this to:
- Google Search Console
- Bing Webmaster Tools

## Next Steps

1. Build and preview the updated site
2. If satisfied, commit and push changes
3. Set up Google Analytics (optional)
4. Submit sitemap to search engines
5. Consider adding a `robots.txt` file if needed
