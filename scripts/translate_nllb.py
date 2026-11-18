"""
Offline alternative to translate_kb.py, using Meta's NLLB-200 model.
Use this when Google Translate blocks you (happens a lot on Colab).

    pip install transformers sentencepiece torch
    python scripts/translate_nllb.py --limit 5     # quick try
    python scripts/translate_nllb.py

Works on CPU but is much faster on a GPU (Colab: Runtime > Change
runtime type > T4 GPU). The first run downloads the model, about 2.5 GB.
Finished sentences are cached, so an interrupted run picks up where it
stopped.
"""
import argparse
import hashlib
import json
import re
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
MODEL = "facebook/nllb-200-distilled-600M"
CODES = {"bn": "ben_Beng", "zh": "zho_Hans"}
FIELDS = ("question", "answer", "focus")


def split_paragraphs(text):
    """Text -> list of paragraphs, each a list of sentences."""
    out = []
    for para in (text or "").split("\n\n"):
        sents = [s for s in re.split(r"(?<=[.!?])\s+", para.strip()) if s]
        if sents:
            out.append(sents)
    return out


def key(text):
    return hashlib.md5(text.encode("utf-8")).hexdigest()


_ZH_PUNCT = [
    (re.compile(r"(?<!\d),|,(?!\d)"), "，"),   # keep 1,000 as it is
    (re.compile(r"(?<!\d)\.|\.(?!\d)"), "。"), # keep 2.5 as it is
    (re.compile(r"\?"), "？"),
    (re.compile(r"!"), "！"),
    (re.compile(r":"), "："),
    (re.compile(r";"), "；"),
]


def fix_zh(text):
    """NLLB writes Chinese with English punctuation, swap it back."""
    for pat, rep in _ZH_PUNCT:
        text = pat.sub(rep, text)
    return text.replace(" ", "") if re.fullmatch(r"[^A-Za-z]*", text) else text


def join(sents, lang):
    if lang == "zh":
        # Chinese doesn't put spaces between sentences
        return "".join(fix_zh(s) for s in sents)
    return " ".join(sents)


class NLLB:
    def __init__(self, model_name=MODEL, device="auto", beams=2):
        import torch
        from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

        if device == "auto":
            device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"loading {model_name} on {device} ...")
        self.torch = torch
        self.tok = AutoTokenizer.from_pretrained(model_name, src_lang="eng_Latn")
        self.model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
        if device == "cuda":
            self.model = self.model.half()
        self.model.to(device).eval()
        self.device = device
        self.beams = beams

    def __call__(self, texts, lang, batch_size=16):
        target = self.tok.convert_tokens_to_ids(CODES[lang])
        out = []
        for i in range(0, len(texts), batch_size):
            chunk = texts[i:i + batch_size]
            enc = self.tok(chunk, return_tensors="pt", padding=True,
                           truncation=True, max_length=400).to(self.device)
            with self.torch.inference_mode():
                gen = self.model.generate(
                    **enc,
                    forced_bos_token_id=target,
                    num_beams=self.beams,
                    max_new_tokens=int(enc["input_ids"].shape[1] * 2) + 20,
                )
            out.extend(self.tok.batch_decode(gen, skip_special_tokens=True))
        return out


def translate_items(items, lang, translate, cache, save=lambda: None, step=64):
    """translate(list_of_sentences, lang) -> list of translations."""
    pieces = set()
    for it in items:
        for field in FIELDS:
            for sents in split_paragraphs(it.get(field, "")):
                pieces.update(sents)

    # similar lengths together means less padding, faster batches
    todo = sorted((p for p in pieces if key(p) not in cache), key=len)
    print(f"  {len(pieces)} sentences, {len(todo)} still to translate")
    start = time.time()
    for i in range(0, len(todo), step):
        chunk = todo[i:i + step]
        result = translate(chunk, lang)
        if len(result) != len(chunk):
            raise RuntimeError("translator returned the wrong number of sentences")
        for src, dst in zip(chunk, result):
            cache[key(src)] = dst.strip()
        save()
        done = i + len(chunk)
        rate = done / max(time.time() - start, 1e-6)
        print(f"  [{lang}] {done}/{len(todo)}  (~{(len(todo) - done) / rate / 60:.1f} min left)")

    out = []
    for it in items:
        new = dict(it)
        for field in FIELDS:
            paras = split_paragraphs(it.get(field, ""))
            new[field] = "\n\n".join(join([cache[key(s)] for s in sents], lang) for sents in paras)
        out.append(new)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--langs", nargs="+", default=list(CODES), choices=list(CODES))
    ap.add_argument("--limit", type=int, help="only the first N entries (for a quick try)")
    ap.add_argument("--device", default="auto", choices=["auto", "cpu", "cuda"])
    ap.add_argument("--beams", type=int, default=2, help="1 is faster, 4 is a bit better")
    ap.add_argument("--batch-size", type=int, default=16)
    args = ap.parse_args()

    src = DATA / "kb_en.json"
    if not src.exists():
        raise SystemExit("data/kb_en.json not found, run scripts/fetch_data.py first")
    items = json.loads(src.read_text(encoding="utf-8"))
    if args.limit:
        items = items[:args.limit]

    model = NLLB(device=args.device, beams=args.beams)

    def translate(texts, lang):
        return model(texts, lang, args.batch_size)

    for lang in args.langs:
        cache_path = DATA / f".nllb_cache_{lang}.json"
        cache = json.loads(cache_path.read_text(encoding="utf-8")) if cache_path.exists() else {}

        def save():
            cache_path.write_text(json.dumps(cache, ensure_ascii=False), encoding="utf-8")

        print(f"translating {len(items)} entries to {lang}")
        out = translate_items(items, lang, translate, cache, save)
        dest = DATA / f"kb_{lang}.json"
        dest.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"wrote {dest}")


if __name__ == "__main__":
    main()
