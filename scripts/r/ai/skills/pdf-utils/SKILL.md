---
description: Read and extract text from PDF files (supports OCR)
---

To read pdf content:

- Using `pdftotext` (fast, requires text layer):
  ```bash
  pdftotext <input_pdf_file> -
  ```
- Using `ocrmypdf` (slower, performs OCR if needed):
  ```bash
  ocrmypdf <input_pdf_file> /dev/null -q --sidecar -
  ```
