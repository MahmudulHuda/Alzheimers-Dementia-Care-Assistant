import pandas as pd

import fetch_data
import translate_kb


def _row(qid, focus, q, a, src="NIHSeniorHealth"):
    return dict(document_id=qid, document_source=src, document_url="https://example.org/" + qid,
                category=None, umls_cui="", umls_semantic_types="", umls_semantic_group="",
                synonyms=None, question_id=qid, question_focus=focus,
                question_type="information", question=q, answer=a)


def test_build_kb_filters_and_cleans():
    long = "Alzheimer's disease is a brain disorder.  It gets worse over time and affects memory."
    df = pd.DataFrame([
        _row("1", "Alzheimer's Disease", "What is (are) Alzheimer's Disease ?", long),
        _row("2", "Alzheimer's Disease", "What is (are) Alzheimer's Disease ?", long),   # exact dupe
        _row("3", "Diabetes", "What is (are) Diabetes ?", "Diabetes is a disease in which blood glucose is too high."),
        _row("4", "Lewy Body Dementia", "What causes Lewy Body Dementia ?", None, "MPlusHealthTopics"),  # stripped answer
        _row("5", "Stroke", "Can a stroke lead to dementia ?", "Yes, a stroke can damage the brain and lead to vascular dementia."),
    ])
    kb = fetch_data.build_kb(df)
    assert [it["id"] for it in kb] == ["1", "5"]
    assert kb[0]["question"] == "What is Alzheimer's Disease?"
    assert kb[0]["answer"].count("\n\n") == 1
    assert kb[1]["question"] == "Can a stroke lead to dementia?"


def test_split_text_respects_limit():
    text = " ".join(f"Sentence number {i} is here." for i in range(400))
    parts = translate_kb.split_text(text, limit=500)
    assert all(len(p) <= 500 for p in parts)
    assert " ".join(parts) == text
    assert translate_kb.split_text("x" * 1200, limit=500) == ["x" * 500, "x" * 500, "x" * 200]


def test_cached_translator(tmp_path):
    calls = []

    def fake(text):
        calls.append(text)
        return text.upper()

    cache = tmp_path / "cache.json"
    tr = translate_kb.CachedTranslator("bn", fake, cache, pause=0)
    items = [{"id": "1", "question": "what is it?", "answer": "para one.\n\npara two.", "focus": "thing"}]
    out = translate_kb.translate_items(items, tr)
    tr.save()
    assert out[0]["answer"] == "PARA ONE.\n\nPARA TWO."
    assert out[0]["id"] == "1" and items[0]["question"] == "what is it?"
    n = len(calls)

    # second run should come entirely from the cache file
    tr2 = translate_kb.CachedTranslator("bn", fake, cache, pause=0)
    translate_kb.translate_items(items, tr2)
    assert len(calls) == n


def test_translator_retries_then_gives_up(tmp_path, monkeypatch):
    monkeypatch.setattr(translate_kb.time, "sleep", lambda s: None)
    state = {"n": 0}

    def flaky(text):
        state["n"] += 1
        if state["n"] < 3:
            raise ConnectionError("boom")
        return "ok"

    tr = translate_kb.CachedTranslator("zh", flaky, tmp_path / "c.json", pause=0)
    assert tr.translate("hello") == "ok"


def test_nllb_translate_items_with_fake_model():
    import translate_nllb

    calls = []

    def fake(texts, lang):
        calls.append(list(texts))
        return [f"<{lang}:{t}>" for t in texts]

    items = [{"id": "1", "question": "What is it?", "focus": "",
              "answer": "First one. Second one!\n\nNew para."}]
    cache = {}
    out = translate_nllb.translate_items(items, "zh", fake, cache, step=2)
    # zh: no space between sentences, punctuation switched to Chinese
    assert out[0]["answer"] == "<zh：First one。><zh：Second one！>\n\n<zh：New para。>"
    assert out[0]["question"] == "<zh：What is it？>"
    assert out[0]["focus"] == ""
    assert items[0]["question"] == "What is it?"

    # Bangla joins sentences with a space, and the cache means no new calls
    n = len(calls)
    out_bn = translate_nllb.translate_items(items, "zh", fake, cache)
    assert len(calls) == n and out_bn == out
    bn = translate_nllb.translate_items(items, "bn", fake, {})
    assert bn[0]["answer"].startswith("<bn:First one.> <bn:Second one!>")


def test_fix_zh_punctuation():
    from translate_nllb import fix_zh

    assert fix_zh("阿尔茨海默病是什么?") == "阿尔茨海默病是什么？"
    assert fix_zh("约有2.4到4.5百万人,人数在增加.") == "约有2.4到4.5百万人，人数在增加。"
    assert fix_zh("超过1,000人.") == "超过1,000人。"
    # English words inside keep their spaces
    assert fix_zh("称为 Lewy body 痴呆.") == "称为 Lewy body 痴呆。"
