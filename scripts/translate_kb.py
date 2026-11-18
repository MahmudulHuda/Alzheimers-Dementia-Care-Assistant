"""
Translate data/kb_en.json into Bangla and Chinese.

    python scripts/translate_kb.py              # both languages
    python scripts/translate_kb.py --langs bn --limit 20

Uses Google Translate through deep-translator, so it needs internet but
no API key and no GPU. Every translated piece is cached on disk; if it
stops halfway just run it again.
"""
import argparse
import hashlib
import json
import re
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
TARGETS = {"bn": "bn", "zh": "zh-CN"}
MAX_CHARS = 4500     # google rejects anything over 5000


def split_text(text, limit=MAX_CHARS):
    """Break long text into pieces under the limit, on sentence ends."""
    if len(text) <= limit:
        return [text]
    parts, cur = [], ""
    for sent in re.split(r"(?<=[.!?])\s+|\n+", text):
        if not sent:
            continue
        while len(sent) > limit:          # one giant "sentence", just cut it
            parts.append(sent[:limit])
            sent = sent[limit:]
        if cur and len(cur) + len(sent) + 1 > limit:
            parts.append(cur)
            cur = sent
        else:
            cur = f"{cur} {sent}".strip()
    if cur:
        parts.append(cur)
    return parts


class CachedTranslator:
    def __init__(self, lang, translate_fn, cache_path, pause=0.4):
        self.fn = translate_fn
        self.path = Path(cache_path)
        self.pause = pause
        self.cache = {}
        if self.path.exists():
            self.cache = json.loads(self.path.read_text(encoding="utf-8"))
        self.lang = lang
        self.new = 0

    def save(self):
        self.path.write_text(json.dumps(self.cache, ensure_ascii=False), encoding="utf-8")

    def _one(self, text):
        key = hashlib.md5(text.encode("utf-8")).hexdigest()
        if key in self.cache:
            return self.cache[key]
        for attempt in range(4):
            try:
                out = self.fn(text)
                break
            except Exception as e:
                wait = 3 * (attempt + 1)
                print(f"  translate failed ({e}), retrying in {wait}s")
                time.sleep(wait)
        else:
            raise RuntimeError("translation keeps failing, try again later")
        if not out:
            raise RuntimeError("got an empty translation back")
        self.cache[key] = out
        self.new += 1
        if self.new % 20 == 0:
            self.save()
        time.sleep(self.pause)
        return out

    def translate(self, text):
        # paragraph by paragraph so the layout survives
        out = []
        for para in text.split("\n\n"):
            pieces = [self._one(p) for p in split_text(para)]
            out.append(" ".join(pieces))
        return "\n\n".join(out)


def translate_items(items, tr):
    done = []
    for n, it in enumerate(items, 1):
        new = dict(it)
        new["question"] = tr.translate(it["question"])
        new["answer"] = tr.translate(it["answer"])
        new["focus"] = tr.translate(it["focus"]) if it.get("focus") else ""
        done.append(new)
        if n % 10 == 0:
            print(f"  [{tr.lang}] {n}/{len(items)}")
    return done


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--langs", nargs="+", default=list(TARGETS), choices=list(TARGETS))
    ap.add_argument("--limit", type=int, help="only the first N entries (for a quick try)")
    args = ap.parse_args()

    from deep_translator import GoogleTranslator

    src = DATA / "kb_en.json"
    if not src.exists():
        raise SystemExit("data/kb_en.json not found, run scripts/fetch_data.py first")
    items = json.loads(src.read_text(encoding="utf-8"))
    if args.limit:
        items = items[:args.limit]

    for lang in args.langs:
        print(f"translating {len(items)} entries to {lang}")
        g = GoogleTranslator(source="en", target=TARGETS[lang])
        tr = CachedTranslator(lang, g.translate, DATA / f".tr_cache_{lang}.json")
        try:
            out = translate_items(items, tr)
        finally:
            tr.save()
        dest = DATA / f"kb_{lang}.json"
        dest.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"wrote {dest}")


if __name__ == "__main__":
    main()
