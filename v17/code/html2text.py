import re, html, pathlib, sys
d = pathlib.Path(sys.argv[1])
for f in d.glob("*.html"):
    raw = f.read_text(encoding="utf-8", errors="replace")
    raw = re.sub(r"(?is)<(script|style|noscript|svg)[^>]*>.*?</\1>", " ", raw)
    raw = re.sub(r"(?i)<(br|/p|/div|/li|/tr|/h[1-6]|/td|/th|/dt|/dd|/button|/span)[^>]*>", "\n", raw)
    raw = re.sub(r"<[^>]+>", " ", raw)
    raw = html.unescape(raw)
    raw = re.sub(r"[ \t\r\f\v\xa0]+", " ", raw)
    raw = re.sub(r"\n\s*\n+", "\n", raw).strip()
    f.with_suffix(".full.txt").write_text(raw, encoding="utf-8")
    print(f.name, len(raw))
