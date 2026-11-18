from pathlib import Path

import pytest

from careqa.assistant import Assistant
from careqa.lang import detect

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture(scope="module")
def bot():
    return Assistant(FIXTURES)


@pytest.mark.parametrize("text,lang", [
    ("what is dementia", "en"),
    ("আলঝেইমার রোগ কী", "bn"),
    ("阿尔茨海默病会遗传吗", "zh"),
    ("আমার বাবার Alzheimer হয়েছে", "bn"),
    ("Alzheimer 的症状", "zh"),
    ("", "en"),
])
def test_detect(text, lang):
    assert detect(text) == lang


@pytest.mark.parametrize("q,expect", [
    ("is alzheimers hereditary? my mother has it", "inherited"),
    ("signs and symptoms of alzheimer", "symptoms"),
    ("I am exhausted caring for my father with dementia", "cope"),
    ("alzhiemer treatmnt", "treatments"),          # typos
    ("আলঝেইমার কি বংশগত রোগ", "বংশগত"),
    ("আলঝেইমারের লক্ষণ কী", "লক্ষণ"),
    ("老年痴呆会不会遗传", "遗传"),
    ("照顾痴呆的妈妈压力很大怎么办", "压力"),
])
def test_finds_right_entry(bot, q, expect):
    r = bot.ask(q)
    assert r["found"], r
    assert expect in r["matched"]


def test_off_topic_is_not_answered(bot):
    for q in ["best pizza in dhaka", "how do I fix my bike chain", "今天天气怎么样", "ক্রিকেট খেলার স্কোর কত"]:
        r = bot.ask(q)
        assert not r["found"], (q, r)


def test_urgent_note(bot):
    assert bot.ask("my father wandered off and I can't find him")["urgent"]
    assert bot.ask("বাবা হারিয়ে গেছেন, খুঁজে পাচ্ছি না")["urgent"]
    assert bot.ask("奶奶走失了怎么办")["urgent"]
    assert bot.ask("what is vascular dementia")["urgent"] is None


def test_related_has_no_duplicates(bot):
    r = bot.ask("what is alzheimer's disease")
    assert r["matched"] not in r["related"]
    assert len(set(r["related"])) == len(r["related"])


def test_forced_language_and_missing_kb(tmp_path):
    empty = Assistant(tmp_path)
    r = empty.ask("what is dementia")
    assert not r["found"] and "fetch_data" in r["answer"]


def test_empty_query(bot):
    assert not bot.ask("   ")["found"]
