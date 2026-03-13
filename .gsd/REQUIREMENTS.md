# Requirements

## Active

### R001 — Drop-and-go OCR workflow
- Class: primary-user-loop
- Status: active
- Description: User drags files onto the app window and receives searchable PDFs with no required configuration
- Why it matters: This is the entire product thesis — OCR without friction
- Source: user
- Primary owning slice: M001/S03
- Supporting slices: M001/S02
- Validation: unmapped
- Notes: Smart defaults handle language, preprocessing, output location

### R002 — Searchable PDF output
- Class: core-capability
- Status: active
- Description: Output is a PDF/A with an invisible text layer overlaid on the original image, enabling select/search/copy
- Why it matters: The core deliverable — without this there's no product
- Source: user
- Primary owning slice: M001/S01
- Supporting slices: M001/S03
- Validation: unmapped
- Notes: OCRmyPDF handles PDF/A generation and text layer placement

### R003 — Image input support (PNG/JPEG/TIFF)
- Class: core-capability
- Status: active
- Description: App accepts PNG, JPEG, and TIFF image files as input
- Why it matters: These are the standard scanner output formats
- Source: user
- Primary owning slice: M001/S03
- Supporting slices: M001/S01
- Validation: unmapped
- Notes: None

### R004 — PDF input support
- Class: core-capability
- Status: active
- Description: App accepts existing non-searchable PDFs and makes them searchable
- Why it matters: Many users have existing scanned PDFs that need text layers added
- Source: user
- Primary owning slice: M001/S05
- Supporting slices: none
- Validation: unmapped
- Notes: OCRmyPDF handles PDF-to-PDF processing natively

### R005 — PaddleOCR as default engine
- Class: core-capability
- Status: active
- Description: PaddleOCR is the default OCR engine, providing better accuracy than Tesseract on complex layouts
- Why it matters: Engine choice directly determines OCR quality — PaddleOCR benchmarks ahead of Tesseract
- Source: user
- Primary owning slice: M001/S01
- Supporting slices: none
- Validation: unmapped
- Notes: PP-OCRv5 models are ~15MB total

### R006 — Auto-preprocessing (deskew, rotate, contrast)
- Class: quality-attribute
- Status: active
- Description: Scanned images are automatically deskewed, rotation-corrected, and contrast-enhanced before OCR
- Why it matters: Real scans are messy — preprocessing significantly improves OCR accuracy
- Source: user
- Primary owning slice: M001/S05
- Supporting slices: none
- Validation: unmapped
- Notes: OCRmyPDF has built-in deskew/rotate; may need additional contrast enhancement

### R007 — Multi-language support
- Class: core-capability
- Status: active
- Description: Users can select from 80+ languages for OCR, defaulting to English
- Why it matters: Documents exist in every language — English-only would exclude most of the world
- Source: user
- Primary owning slice: M001/S04
- Supporting slices: none
- Validation: unmapped
- Notes: PaddleOCR supports 80+ languages; language models may need on-demand download

### R008 — Output next to originals with _ocr suffix
- Class: primary-user-loop
- Status: active
- Description: Searchable PDFs are saved in the same directory as the input file with an _ocr.pdf suffix
- Why it matters: Predictable output location, no configuration needed, no data loss
- Source: user
- Primary owning slice: M001/S03
- Supporting slices: none
- Validation: unmapped
- Notes: e.g. scan.png → scan_ocr.pdf, document.pdf → document_ocr.pdf

### R009 — Per-file output
- Class: primary-user-loop
- Status: active
- Description: Each input file produces its own separate searchable PDF
- Why it matters: Predictable 1:1 mapping — no merge decisions, no confusion
- Source: user
- Primary owning slice: M001/S03
- Supporting slices: none
- Validation: unmapped
- Notes: None

### R010 — Cross-platform desktop app
- Class: launchability
- Status: active
- Description: App runs on macOS, Windows, and Linux as a native desktop application
- Why it matters: Cross-platform reach is the whole point — can't compete with ABBYY on one OS
- Source: user
- Primary owning slice: M001/S02
- Supporting slices: M002/S01
- Validation: unmapped
- Notes: Tauri v2 provides the cross-platform shell; M001 verifies macOS, M002 verifies all platforms

### R011 — Progress feedback during OCR
- Class: primary-user-loop
- Status: active
- Description: User sees per-file progress during OCR processing (not just a spinner)
- Why it matters: OCR takes seconds-to-minutes per file — silence feels broken
- Source: user
- Primary owning slice: M001/S03
- Supporting slices: none
- Validation: unmapped
- Notes: Python sidecar streams progress events to Tauri frontend

### R012 — Swappable OCR engine architecture
- Class: quality-attribute
- Status: active
- Description: OCR engine is behind a pluggable interface so alternative engines can be added without changing the pipeline
- Why it matters: User explicitly didn't want to marry to one engine — architecture should support swapping
- Source: inferred
- Primary owning slice: M001/S01
- Supporting slices: none
- Validation: unmapped
- Notes: Interface defines: recognize(image) → text regions with positions

### R013 — Downloadable installer
- Class: launchability
- Status: active
- Description: App is distributed as DMG (macOS), MSI (Windows), and AppImage (Linux)
- Why it matters: Non-technical users can't pip install — needs to be download-and-double-click
- Source: user
- Primary owning slice: M002/S01
- Supporting slices: M003 (release build workflow produces the artifacts)
- Validation: unmapped
- Notes: Tauri bundler handles this; Python sidecar bundled via PyInstaller. M003 builds the CI workflow; M002 wires up auto-updates and verifies installs.

### R014 — Settings panel for power users
- Class: differentiator
- Status: active
- Description: Collapsible settings UI for language selection, preprocessing toggles, output naming
- Why it matters: Drop-and-go is the default, but power users need control
- Source: inferred
- Primary owning slice: M001/S04
- Supporting slices: none
- Validation: unmapped
- Notes: Should not interfere with the minimal default experience

### R015 — Graceful error handling
- Class: failure-visibility
- Status: active
- Description: Errors during OCR (corrupt files, unsupported formats, engine failures) are shown as clear user-visible messages
- Why it matters: Silent failures are worse than errors — users need to know what happened
- Source: inferred
- Primary owning slice: M001/S03
- Supporting slices: none
- Validation: unmapped
- Notes: Per-file error states in the UI, not app-level crashes

### R016 — OCR quality on par with or better than raw Tesseract
- Class: quality-attribute
- Status: active
- Description: PaddleOCR output quality meets or exceeds Tesseract on standard document types
- Why it matters: If the free tool produces garbage text, nobody will use it
- Source: research
- Primary owning slice: M001/S01
- Supporting slices: none
- Validation: unmapped
- Notes: Validated via CER/WER on test fixture set

### R024 — Automated OCR quality regression testing
- Class: quality-attribute
- Status: active
- Description: A curated test fixture set (~20 images with ground truth text) is used to measure CER/WER and assert quality thresholds in CI
- Why it matters: Catches OCR quality regressions when engine versions or preprocessing changes
- Source: user
- Primary owning slice: M001/S01
- Supporting slices: M001/S06, M003 (CI workflow runs benchmarks on merge to main)
- Validation: unmapped
- Notes: Fixtures cover clean prints, skewed scans, multi-column, non-English text. M001 creates the tests; M003 wires them into CI.

## Validated

(none yet)

## Deferred

### R017 — Tesseract as alternative engine option
- Class: core-capability
- Status: deferred
- Description: Tesseract available as a selectable alternative OCR engine
- Why it matters: Lighter dependency, faster on clean text, some users may prefer it
- Source: research
- Primary owning slice: none
- Supporting slices: none
- Validation: unmapped
- Notes: Deferred — PaddleOCR is the focus; swappable architecture makes adding this cheap later

### R018 — Apple Vision backend on macOS
- Class: differentiator
- Status: deferred
- Description: Apple's built-in Vision framework as an OCR backend option on macOS
- Why it matters: Free, hardware-accelerated, excellent quality on Mac
- Source: research
- Primary owning slice: none
- Supporting slices: none
- Validation: unmapped
- Notes: Deferred — macOS-only, can't be the default for a cross-platform app

### R019 — Batch merge into single PDF
- Class: core-capability
- Status: deferred
- Description: Option to merge multiple input files into a single multi-page searchable PDF
- Why it matters: Useful for combining a stack of scanned pages into one document
- Source: user
- Primary owning slice: none
- Supporting slices: none
- Validation: unmapped
- Notes: Deferred — per-file output is the v1 behavior; merge adds UX complexity

### R020 — Text export alongside PDF
- Class: differentiator
- Status: deferred
- Description: Option to export recognized text as .txt or copy-to-clipboard alongside the searchable PDF
- Why it matters: Some users want raw text, not just a searchable PDF
- Source: user
- Primary owning slice: none
- Supporting slices: none
- Validation: unmapped
- Notes: Deferred — searchable PDF is v1; text export is a natural follow-up

## Out of Scope

### R021 — Cloud/server-based OCR
- Class: anti-feature
- Status: out-of-scope
- Description: No cloud services, no API keys, no data leaving the machine
- Why it matters: Privacy is a feature — documents stay local
- Source: inferred
- Primary owning slice: none
- Supporting slices: none
- Validation: n/a
- Notes: This is a design principle, not just a deferral

### R022 — Document management / organization
- Class: anti-feature
- Status: out-of-scope
- Description: No document library, tagging, search index, or organizational features
- Why it matters: Scope trap — Parsec is a converter, not a document manager
- Source: inferred
- Primary owning slice: none
- Supporting slices: none
- Validation: n/a
- Notes: There are good document managers already; Parsec feeds into them

### R023 — Handwriting recognition
- Class: constraint
- Status: out-of-scope
- Description: No claims or optimization for handwritten text recognition
- Why it matters: PaddleOCR handles some handwriting but quality is unreliable — claiming support sets false expectations
- Source: research
- Primary owning slice: none
- Supporting slices: none
- Validation: n/a
- Notes: May work incidentally but is not a supported use case

## Traceability

| ID | Class | Status | Primary owner | Supporting | Proof |
|---|---|---|---|---|---|
| R001 | primary-user-loop | active | M001/S03 | M001/S02 | unmapped |
| R002 | core-capability | active | M001/S01 | M001/S03 | unmapped |
| R003 | core-capability | active | M001/S03 | M001/S01 | unmapped |
| R004 | core-capability | active | M001/S05 | none | unmapped |
| R005 | core-capability | active | M001/S01 | none | unmapped |
| R006 | quality-attribute | active | M001/S05 | none | unmapped |
| R007 | core-capability | active | M001/S04 | none | unmapped |
| R008 | primary-user-loop | active | M001/S03 | none | unmapped |
| R009 | primary-user-loop | active | M001/S03 | none | unmapped |
| R010 | launchability | active | M001/S02 | M002/S01 | unmapped |
| R011 | primary-user-loop | active | M001/S03 | none | unmapped |
| R012 | quality-attribute | active | M001/S01 | none | unmapped |
| R013 | launchability | active | M002/S01 | M003 | unmapped |
| R014 | differentiator | active | M001/S04 | none | unmapped |
| R015 | failure-visibility | active | M001/S03 | none | unmapped |
| R016 | quality-attribute | active | M001/S01 | none | unmapped |
| R024 | quality-attribute | active | M001/S01 | M001/S06, M003 | unmapped |
| R017 | core-capability | deferred | none | none | unmapped |
| R018 | differentiator | deferred | none | none | unmapped |
| R019 | core-capability | deferred | none | none | unmapped |
| R020 | differentiator | deferred | none | none | unmapped |
| R021 | anti-feature | out-of-scope | none | none | n/a |
| R022 | anti-feature | out-of-scope | none | none | n/a |
| R023 | constraint | out-of-scope | none | none | n/a |

## Coverage Summary

- Active requirements: 17
- Mapped to slices: 17
- Validated: 0
- Unmapped active requirements: 0
