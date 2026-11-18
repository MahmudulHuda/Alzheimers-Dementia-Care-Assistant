# Alzheimer's & Dementia Care Assistant

[![tests](https://github.com/MahmudulHuda/Alzheimers-Dementia-Care-Assistant/actions/workflows/tests.yml/badge.svg)](https://github.com/MahmudulHuda/Alzheimers-Dementia-Care-Assistant/actions/workflows/tests.yml)

A small question-answering assistant for families and caregivers of people
living with Alzheimer's disease or another dementia. It answers in
**English, Bangla (বাংলা) and Mandarin Chinese (中文)**.

It is built to run on an old laptop: no GPU, no language model, no API
key. Answers are looked up, not generated, so it can't make things up. If
nothing in the data matches well enough, it says so.

> This gives general health information only. It is not medical advice and
> it is not a replacement for a doctor.

## How it works

1. `scripts/fetch_data.py` downloads [MedQuAD](https://github.com/abachaa/MedQuAD)
   (question/answer pairs collected from US National Institutes of Health
   websites) and keeps the entries about Alzheimer's, dementia and related
   conditions.
2. `scripts/translate_kb.py` translates those entries into Bangla and
   Chinese once, and saves them. Nothing is translated while the app runs.
3. At start-up the app builds a TF-IDF index (character n-grams) per
   language. A question is matched against the stored questions and, with
   a lower weight, the answers. The best match is shown with a link to the
   NIH page it came from.
4. The language is detected from the script the person types in, or can be
   picked by hand.
5. Messages that look like an emergency (someone missing, not breathing,
   talk of suicide, etc.) get a "call for help now" note on top.

Character n-grams mean no tokenizer is needed for Bangla or Chinese, and
small typos in English still match.

## Quick start

Python 3.10 or newer. The finished data is already in `data/`, so there is
nothing to download or translate.

```bash
git clone https://github.com/MahmudulHuda/Alzheimers-Dementia-Care-Assistant.git
cd Alzheimers-Dementia-Care-Assistant
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

python app.py                   # open http://127.0.0.1:5000
python cli.py                   # or stay in the terminal
```

## What's in `data/`

| File | Contents |
| --- | --- |
| `kb_en.json` | 107 question/answer pairs about Alzheimer's and dementia from MedQuAD |
| `kb_bn.json` | The same, machine translated to Bangla with NLLB-200 |
| `kb_zh.json` | The same, machine translated to Simplified Chinese with NLLB-200 |

Each entry keeps the link to the NIH page it came from.

## Rebuilding the data

Only needed if you want to change the filter or the translation.

```bash
python scripts/fetch_data.py          # ~11 MB download, writes data/kb_en.json

pip install -r requirements-translate.txt
python scripts/translate_nllb.py      # offline, NLLB-200; needs a GPU to be quick
# or
python scripts/translate_kb.py        # Google Translate; often blocked on Colab
```

Both translators cache every sentence, so an interrupted run carries on
where it stopped. Add `--limit 5` for a quick trial.

No GPU at home? Open `notebooks/build_data_colab.ipynb` in Google Colab,
pick a T4 GPU runtime, and run all cells. It takes about 10 minutes and
downloads the finished files at the end.

## Tests

```bash
pytest
```

The tests use a tiny hand-written knowledge base in `tests/fixtures/`, so
they run offline. GitHub Actions runs them on every push.

## Layout

```
app.py                  Flask app
cli.py                  terminal version
careqa/
  assistant.py          loads the data, puts a reply together
  retriever.py          TF-IDF index and search
  synonyms.py           maps everyday English wording to the dataset's wording
  lang.py               language detection, text normalising
  safety.py             emergency keyword check
scripts/
  fetch_data.py         download + filter MedQuAD
  translate_kb.py       build the Bangla and Chinese copies (Google Translate)
  translate_nllb.py     same, offline with the NLLB-200 model
notebooks/
  build_data_colab.ipynb  rebuild the data on a free Colab GPU
data/                   the finished knowledge base (en, bn, zh)
templates/, static/     web page
tests/
```

## Data

MedQuAD: Ben Abacha A, Demner-Fushman D. *A Question-Entailment Approach
to Question Answering.* BMC Bioinformatics, 2019. Released under CC BY 4.0.
The copy used here is the parquet conversion at
[lavita/MedQuAD](https://huggingface.co/datasets/lavita/MedQuAD) on
Hugging Face, which leaves out the MedlinePlus answers for copyright
reasons. The files in `data/`, translations included, are derived from
MedQuAD and stay under CC BY 4.0.

## Limitations

- The Bangla and Chinese text is machine translated (Google Translate or
  NLLB-200) and has not been checked by a clinician or a native-speaking
  reviewer. Medical terms may be off. Every answer links back to the
  English source.
- The source material was written for a US audience. Services, helplines
  and drug availability will differ in Bangladesh and China.
- MedQuAD was collected around 2017-2018, so it does not cover newer
  treatments.
- Matching is lexical. It does not understand the question, it finds
  similar wording. The score cut-offs in `careqa/retriever.py` (`MIN_SCORE`)
  may need adjusting once you look at real questions.
- The emergency check is a keyword list and will miss things.

## Licence

Code: MIT, see [LICENSE](LICENSE). Data: CC BY 4.0, see [Data](#data).
