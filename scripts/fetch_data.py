"""
Download MedQuAD (NIH question/answer pairs) and keep only the
Alzheimer's / dementia part.

    python scripts/fetch_data.py

Writes data/kb_en.json. The parquet file is about 11 MB and is kept in
data/raw/ so re-running doesn't download it again.
"""
import argparse
import json
import re
import sys
from pathlib import Path

import pandas as pd
import requests

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw" / "medquad.parquet"
OUT = ROOT / "data" / "kb_en.json"

URL = ("https://huggingface.co/datasets/lavita/MedQuAD/resolve/"
       "refs%2Fconvert%2Fparquet/default/train/0000.parquet")

TOPIC = re.compile(
    r"alzheimer|dementia|lewy bod|frontotemporal|mild cognitive impairment"
    r"|binswanger|memory loss|forgetful",
    re.I,
)


def download(dest, force=False):
    if dest.exists() and not force:
        print(f"using cached {dest}")
        return
    dest.parent.mkdir(parents=True, exist_ok=True)
    print("downloading MedQuAD ...")
    tmp = dest.with_suffix(".part")
    with requests.get(URL, stream=True, timeout=60) as r:
        r.raise_for_status()
        with open(tmp, "wb") as f:
            for chunk in r.iter_content(1 << 16):
                f.write(chunk)
    tmp.replace(dest)
    print(f"saved {dest} ({dest.stat().st_size / 1e6:.1f} MB)")


def tidy_question(q):
    q = " ".join(str(q).split())
    q = q.replace("(are) ", "")          # "What is (are) Dementia ?"
    q = re.sub(r"\s+\?", "?", q)
    return q


def tidy_answer(a):
    # keep paragraph breaks where the source had them, squash the rest
    paras = [" ".join(p.split()) for p in re.split(r"\n\s*\n|\s{2,}", str(a))]
    return "\n\n".join(p for p in paras if p)


def build_kb(df):
    df = df.fillna("")
    on_topic = df["question_focus"].str.contains(TOPIC) | df["question"].str.contains(TOPIC)
    df = df[on_topic]

    items, seen = [], set()
    for row in df.itertuples(index=False):
        answer = tidy_answer(row.answer)
        if len(answer) < 40:      # MedlinePlus answers were stripped from this copy
            continue
        question = tidy_question(row.question)
        key = (question.lower(), answer[:200])
        if key in seen:
            continue
        seen.add(key)
        items.append({
            "id": str(row.question_id),
            "question": question,
            "answer": answer,
            "focus": row.question_focus,
            "qtype": row.question_type,
            "source": row.document_source,
            "url": row.document_url,
        })
    return items


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--file", help="use a local parquet/csv copy instead of downloading")
    ap.add_argument("--force", action="store_true", help="download again")
    args = ap.parse_args()

    if args.file:
        path = Path(args.file)
    else:
        download(RAW, args.force)
        path = RAW

    df = pd.read_csv(path) if path.suffix == ".csv" else pd.read_parquet(path)
    items = build_kb(df)
    if not items:
        sys.exit("nothing matched, the dataset layout may have changed")

    OUT.parent.mkdir(exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=1)

    by_source = pd.Series([it["source"] for it in items]).value_counts()
    print(f"{len(items)} question/answer pairs -> {OUT}")
    print(by_source.to_string())


if __name__ == "__main__":
    main()
