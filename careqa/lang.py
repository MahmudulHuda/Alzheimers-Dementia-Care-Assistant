import unicodedata

LANGS = ("en", "bn", "zh")


def detect(text):
    """Guess the language from the script. Good enough for en/bn/zh."""
    bn = zh = latin = 0
    for ch in text:
        cp = ord(ch)
        if 0x0980 <= cp <= 0x09FF:
            bn += 1
        elif 0x4E00 <= cp <= 0x9FFF or 0x3400 <= cp <= 0x4DBF:
            zh += 1
        elif ch.isascii() and ch.isalpha():
            latin += 1
    if bn == 0 and zh == 0:
        return "en"
    # people mix in English words ("Alzheimer", drug names) so don't
    # compare against latin, only bn vs zh
    return "bn" if bn >= zh else "zh"


def normalize(text):
    text = unicodedata.normalize("NFKC", text or "")
    text = text.replace("‌", "").replace("‍", "")  # zwnj/zwj show up in typed Bangla
    return " ".join(text.lower().split())
