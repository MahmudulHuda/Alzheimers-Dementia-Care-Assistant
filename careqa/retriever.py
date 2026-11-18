import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import linear_kernel

from .lang import normalize
from .synonyms import expand

# char n-grams so we don't need a tokenizer for Bangla or Chinese,
# and typos in English still land somewhere sensible
_NGRAMS = {
    "en": dict(analyzer="char_wb", ngram_range=(3, 5)),
    "bn": dict(analyzer="char_wb", ngram_range=(2, 4)),
    "zh": dict(analyzer="char", ngram_range=(1, 3)),
}

# below this we say "not sure" instead of guessing
MIN_SCORE = {"en": 0.22, "bn": 0.22, "zh": 0.20}

Q_WEIGHT = 0.75


class Index:
    def __init__(self, lang, items):
        self.lang = lang
        self.items = items
        opts = _NGRAMS[lang]
        self.q_vec = TfidfVectorizer(sublinear_tf=True, **opts)
        self.a_vec = TfidfVectorizer(sublinear_tf=True, max_features=60000, **opts)
        self.q_mat = self.q_vec.fit_transform(self._q_text(it) for it in items)
        self.a_mat = self.a_vec.fit_transform(normalize(it["answer"]) for it in items)

    @staticmethod
    def _q_text(it):
        # focus is the condition name from MedQuAD, helps short questions
        return normalize(it["question"] + " " + it.get("focus", ""))

    def search(self, query, k=4):
        q = normalize(query)
        if not q:
            return []
        if self.lang == "en":
            q = expand(q)
        qs = linear_kernel(self.q_vec.transform([q]), self.q_mat).ravel()
        ans = linear_kernel(self.a_vec.transform([q]), self.a_mat).ravel()
        scores = Q_WEIGHT * qs + (1 - Q_WEIGHT) * ans

        out, seen = [], set()
        for i in np.argsort(-scores):
            if scores[i] <= 0:
                break
            key = normalize(self.items[i]["question"])
            if key in seen:      # MedQuAD repeats the same question across sources
                continue
            seen.add(key)
            out.append((self.items[i], float(scores[i])))
            if len(out) == k:
                break
        return out
