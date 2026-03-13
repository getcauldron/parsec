# FAQ

## What operating systems does Parsec support?

Parsec targets **macOS**, **Windows**, and **Linux**. It's built with Tauri, which produces native binaries for all three platforms. The Python sidecar is bundled via PyInstaller, so end users don't need Python installed.

## Does Parsec require an internet connection?

No. Parsec runs entirely offline. PaddleOCR models are bundled with the application, and all processing happens locally on your machine. Your documents never leave your computer.

## What file types can I process?

Parsec accepts **PNG**, **JPEG**, **TIFF**, and **PDF** files. The output is always a searchable PDF with an invisible text layer.

## How large can input files be?

There's no hard file size limit, but processing time scales with document size and page count. A typical single-page scan at 300 DPI takes a few seconds. Large multi-page PDFs can take longer — progress events are streamed in real time so you can track the status.

## What language codes should I use?

Use the PaddleOCR short codes listed on the [Usage](./usage.md#supported-languages) page. Some common ones:

| Language | Code |
|----------|------|
| English | `en` |
| Chinese (Simplified) | `ch` |
| Japanese | `japan` |
| Korean | `korean` |
| French | `french` |
| German | `german` |
| Spanish | `es` |
| Arabic | `ar` |
| Hindi | `hi` |

Note that some codes differ from ISO standards (e.g. `french` not `fr`, `korean` not `ko`). These are PaddleOCR's native codes — see the full table in the [Usage guide](./usage.md#supported-languages).

## My scanned document comes out with garbled text

Try these in order:

1. **Check the language setting** — wrong language is the most common cause of bad OCR results
2. **Increase DPI** — if the scan resolution is low, setting a higher DPI (400–600) can help
3. **Enable deskew** — crooked pages reduce recognition accuracy
4. **Enable clean** — removes scan artifacts that confuse the engine (requires `unpaper` installed)

## The app says "sidecar not found" or crashes on startup

The Python sidecar binary must be in the correct location. In development:

- Make sure you've run `pip install -e ./backend` to install the backend package
- Check that `pnpm tauri dev` is starting from the project root

In production builds, the sidecar binary is bundled automatically by the CI pipeline. If you're building locally, ensure PyInstaller has produced the binary in `src-tauri/binaries/`.

## OCR is slow on my machine

PaddleOCR runs on CPU by default. Processing speed depends on your hardware and the document complexity. Things that help:

- **Lower DPI** — 300 is usually sufficient; going higher adds processing time without much accuracy gain
- **Skip Text** — for PDFs that already have some searchable pages, skip them to save time
- **Disable cleaning** — the `clean` option adds an extra preprocessing pass

GPU acceleration is on the roadmap but not yet supported.

## Can I use Tesseract instead of PaddleOCR?

Not yet in the UI, but the architecture supports it. The OCR engine is behind an abstract interface (`OcrEngine`), so adding Tesseract or another engine is a matter of implementing the interface. See [Architecture](./architecture.md#abstract-engine-interface) for details.

## The output PDF looks different from the original

Parsec preserves the original image and overlays invisible text. The visual appearance should be identical to the input. If it looks different:

- Check that **Force OCR** isn't re-rendering pages unnecessarily
- For PDFs, try **Skip Text** mode to leave already-searchable pages untouched

## How do I report a bug or request a feature?

Open an issue on [GitHub](https://github.com/getcauldron/parsec/issues) using the provided templates. For bugs, include reproduction steps and your OS/version. For features, describe the use case.
