---
description: pdf tools (including read text)
---

to read pdf content:

```
ocrmypdf <input_pdf_file> /dev/null --sidecar /tmp/ocr.txt && cat /tmp/ocr.txt
```
