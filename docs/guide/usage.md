# Usage

Parsec processes scanned documents and images into searchable PDFs. This page covers supported formats, OCR options, and the full language list.

## Supported Input Formats

| Format | Extensions | Notes |
|--------|-----------|-------|
| PNG | `.png` | Raster images |
| JPEG | `.jpg`, `.jpeg` | Raster images |
| TIFF | `.tiff`, `.tif` | Single or multi-page |
| PDF | `.pdf` | Existing PDFs — adds a text layer |

The output is always a PDF with an invisible text layer overlay, making the content searchable and selectable.

## OCR Options

These options control how Parsec processes your documents:

### Language

**Default:** `en` (English)

Set the recognition language to match your document's content. Using the correct language dramatically improves accuracy. See the [full language list](#supported-languages) below.

### DPI

**Default:** `300`

Image resolution in dots per inch. Used when the source image doesn't include DPI metadata. Higher values improve accuracy for small text but increase processing time. 300 is a good default for most scanned documents.

### Deskew

**Default:** off

Corrects page skew (slight rotation from crooked scanning) before OCR. Enable this when your scans aren't perfectly straight. Adds a small amount of processing time.

### Rotate Pages

**Default:** off

Detects and corrects 90°, 180°, or 270° page rotation. Useful for documents scanned in mixed orientations. Works independently of deskew.

### Clean

**Default:** off

Removes scan artifacts (noise, dust marks, border shadows) using the `unpaper` tool before OCR. Requires `unpaper` to be installed on your system. Most useful for photocopied or faxed documents.

### Skip Text

**Default:** off

For PDF inputs only. Skips OCR on pages that already have a text layer, processing only pages without existing text. Useful for mixed PDFs where some pages are already searchable. Mutually exclusive with Force OCR.

### Force OCR

**Default:** off

Re-OCR all pages regardless of whether they already contain text. Use this when the existing text layer is incorrect or low-quality. Mutually exclusive with Skip Text.

## Supported Languages

Parsec supports 49 languages across 12 writing systems via PaddleOCR.

### Latin Script

| Language | Code |
|----------|------|
| English | `en` |
| French | `french` |
| German | `german` |
| Spanish | `es` |
| Portuguese | `pt` |
| Italian | `it` |
| Dutch | `nl` |
| Norwegian | `no` |
| Swedish | `sv` |
| Danish | `da` |
| Finnish | `fi` |
| Polish | `pl` |
| Czech | `cs` |
| Slovak | `sk` |
| Slovenian | `sl` |
| Croatian | `hr` |
| Romanian | `ro` |
| Hungarian | `hu` |
| Turkish | `tr` |
| Estonian | `et` |
| Latvian | `lv` |
| Lithuanian | `lt` |
| Indonesian | `id` |
| Malay | `ms` |
| Vietnamese | `vi` |
| Latin | `la` |

### CJK

| Language | Code |
|----------|------|
| Chinese (Simplified) | `ch` |
| Chinese (Traditional) | `chinese_cht` |
| Japanese | `japan` |
| Korean | `korean` |

### Cyrillic

| Language | Code |
|----------|------|
| Russian | `ru` |
| Ukrainian | `uk` |
| Bulgarian | `bg` |

### Arabic Script

| Language | Code |
|----------|------|
| Arabic | `ar` |
| Persian | `fa` |
| Urdu | `ur` |

### Devanagari / Indic

| Language | Code |
|----------|------|
| Hindi | `hi` |
| Marathi | `mr` |
| Nepali | `ne` |
| Bengali | `bn` |
| Tamil | `ta` |
| Telugu | `te` |
| Kannada | `ka` |

### Other Scripts

| Language | Code |
|----------|------|
| Greek | `el` |
| Hebrew | `he` |
| Thai | `th` |
| Myanmar (Burmese) | `my` |
| Khmer | `km` |
| Lao | `lo` |
