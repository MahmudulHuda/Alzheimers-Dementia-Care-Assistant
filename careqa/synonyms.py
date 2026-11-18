import re

# MedQuAD questions follow a handful of templates ("Is X inherited?",
# "What are the treatments for X?"). People don't phrase it like that, so
# nudge common wording toward the template words before searching.
# English only; the translated questions don't follow fixed templates.
_RULES = [
    (r"heredit|genetic|runs? in (the |my )?famil|pass(ed)? (it )?(on|down)", "inherited genetic"),
    (r"\bcure|medicine|medication|drug|therap|pills?\b", "treatments"),
    (r"\bsigns?\b|warning", "symptoms"),
    (r"\bwhy\b|reason|risk factor", "causes"),
    (r"avoid|reduce (the |my )?risk|lower (the |my )?risk|protect", "prevent"),
    (r"\btests?\b|\bscan|check(ed)? for|find out if", "diagnose diagnosis"),
    (r"life expectancy|how long|prognos|get worse|stages?\b", "outlook"),
    (r"exhaust|burn ?out|stress|overwhelm|tired", "caregiver cope caring"),
]
_RULES = [(re.compile(p, re.I), extra) for p, extra in _RULES]


def expand(query):
    extra = [words for pat, words in _RULES if pat.search(query)]
    return query + " " + " ".join(extra) if extra else query
