import json
import random
from pathlib import Path

from . import safety
from .lang import LANGS, detect
from .retriever import Index, MIN_SCORE

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

NOT_SURE = {
    "en": "I couldn't find a reliable answer to that. Try rephrasing, or ask "
          "the doctor or nurse who knows the person you care for.",
    "bn": "এই প্রশ্নের নির্ভরযোগ্য উত্তর আমার কাছে নেই। একটু অন্যভাবে লিখে দেখুন, "
          "অথবা রোগীকে যিনি দেখছেন সেই ডাক্তারের সাথে কথা বলুন।",
    "zh": "抱歉，我没有找到可靠的答案。请换一种说法再试，或咨询了解患者情况的医生。",
}

NO_DATA = {
    "en": "The English knowledge base hasn't been built yet. Run scripts/fetch_data.py first.",
    "bn": "বাংলা ডেটা এখনো তৈরি হয়নি। আগে scripts/translate_kb.py চালান।",
    "zh": "中文数据尚未生成，请先运行 scripts/translate_kb.py。",
}


class Assistant:
    def __init__(self, data_dir=DATA_DIR):
        self.indexes = {}
        for lang in LANGS:
            path = Path(data_dir) / f"kb_{lang}.json"
            if not path.exists():
                continue
            with open(path, encoding="utf-8") as f:
                items = json.load(f)
            if items:
                self.indexes[lang] = Index(lang, items)

    def languages(self):
        return list(self.indexes)

    def examples(self, lang, n=4):
        idx = self.indexes.get(lang)
        if not idx:
            return []
        qs = sorted({it["question"] for it in idx.items if len(it["question"]) < 70})
        return random.sample(qs, min(n, len(qs)))

    def ask(self, query, lang=None):
        query = (query or "").strip()
        if lang not in LANGS:
            lang = detect(query)

        reply = {"lang": lang, "found": False, "urgent": None, "related": []}
        if safety.is_urgent(query, lang):
            reply["urgent"] = safety.URGENT_NOTE[lang]

        idx = self.indexes.get(lang)
        if idx is None:
            reply["answer"] = NO_DATA[lang]
            return reply

        hits = idx.search(query)
        if not hits or hits[0][1] < MIN_SCORE[lang]:
            reply["answer"] = NOT_SURE[lang]
            # still show the nearest questions, often one of them is what they meant
            reply["related"] = [it["question"] for it, _ in hits[:3]]
            return reply

        best, score = hits[0]
        reply.update(
            found=True,
            matched=best["question"],
            answer=best["answer"],
            source=best.get("source", ""),
            url=best.get("url", ""),
            score=round(score, 3),
            related=[it["question"] for it, s in hits[1:] if s >= MIN_SCORE[lang] * 0.6],
        )
        return reply
