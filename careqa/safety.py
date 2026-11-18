import re

# Things we should never answer with a plain FAQ entry. If any of these
# match, the reply leads with an "get help now" note.
_PATTERNS = {
    "en": [
        r"suicid", r"kill (him|her|my|them)sel", r"end (his|her|my) life",
        r"not breathing", r"can'?t breathe", r"unconscious", r"unresponsive",
        r"chok(ing|ed)", r"overdos", r"took too many",
        r"(is|went|gone|has been) missing", r"wandered (off|away)",
        r"can'?t find (him|her|my)", r"bleeding", r"chest pain",
        r"fell (down|and)", r"seizure",
    ],
    "bn": [
        "আত্মহত্যা", "মরে যেতে চা", "শ্বাস নিচ্ছে না", "শ্বাস নিতে পারছে না",
        "শ্বাসকষ্ট", "অজ্ঞান", "জ্ঞান হারি", "হারিয়ে গে", "খুঁজে পাচ্ছি না",
        "নিখোঁজ", "বেশি ওষুধ খেয়ে", "রক্তপাত", "রক্ত পড়", "পড়ে গে",
        "পড়ে গি", "খিঁচুনি", "বুকে ব্যথা",
    ],
    "zh": [
        "自杀", "轻生", "不想活", "没有呼吸", "呼吸困难", "昏迷", "昏倒",
        "没有反应", "走失", "走丢", "找不到人", "不见了", "服药过量",
        "吃了太多药", "吃错药", "出血", "摔倒", "摔了", "抽搐", "胸痛",
    ],
}

URGENT_NOTE = {
    "en": ("This sounds like it may be urgent. If someone is in danger right "
           "now, call your local emergency number (999 in Bangladesh, 120 in "
           "China, 911 in the US) or go to the nearest hospital. This tool "
           "cannot help in an emergency."),
    "bn": ("বিষয়টি জরুরি মনে হচ্ছে। কেউ এই মুহূর্তে বিপদে থাকলে দেরি না করে "
           "জরুরি নম্বরে ফোন করুন (বাংলাদেশে ৯৯৯) অথবা কাছের হাসপাতালে যান। "
           "জরুরি অবস্থায় এই টুল সাহায্য করতে পারবে না।"),
    "zh": ("这听起来可能是紧急情况。如果有人现在有危险，请立即拨打当地急救电话"
           "（中国大陆 120，报警 110），或前往最近的医院。本工具无法处理紧急情况。"),
}


def is_urgent(text, lang):
    t = text.lower()
    # check the detected language first, but also the others; people mix
    for code in (lang, "en", "bn", "zh"):
        for pat in _PATTERNS.get(code, []):
            if code == "en":
                if re.search(pat, t):
                    return True
            elif pat in t:
                return True
    return False
