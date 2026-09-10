"""Strict, whole-response checks against authoritative synthetic facts."""
from __future__ import annotations

import re
import unicodedata

DIGITS = {'zero': '0', 'oh': '0', 'one': '1', 'two': '2', 'three': '3',
          'four': '4', 'five': '5', 'six': '6', 'seven': '7', 'eight': '8', 'nine': '9'}
SMALL = {'zero': 0, 'one': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5,
         'six': 6, 'seven': 7, 'eight': 8, 'nine': 9, 'ten': 10, 'eleven': 11,
         'twelve': 12, 'thirteen': 13, 'fourteen': 14, 'fifteen': 15,
         'sixteen': 16, 'seventeen': 17, 'eighteen': 18, 'nineteen': 19}
TENS = {'twenty': 20, 'thirty': 30, 'forty': 40, 'fifty': 50}


def normalized(text: str) -> str:
    return ' '.join(unicodedata.normalize('NFKC', text).lower().strip().split())


def reference_value(text: str) -> str | None:
    text = normalized(text)
    text = re.sub(r'^(?:(?:my|the|your) )?(?:reference (?:code|number)|code) is ', '', text)
    # Punctuation separates spoken letters/digits; other words cannot be dropped.
    tokens = re.sub(r'[.,-]', ' ', text).split()
    result = []
    aliases = {'dee': 'd', 'delta': 'd', 'eff': 'f', 'foxtrot': 'f', 'df': 'df'}
    for token in tokens:
        if token in DIGITS:
            result.append(DIGITS[token])
        elif token in aliases:
            result.append(aliases[token])
        elif re.fullmatch(r'[a-z0-9]+', token) and (len(token) == 1 or any(c.isdigit() for c in token)):
            result.append(token)
        else:
            return None
    return ''.join(result) if result else None


def time_value(text: str) -> tuple[int, int, str] | None:
    text = normalized(text)
    text = re.sub(r'^(?:(?:my|the|your) )?(?:appointment time|time) is ', '', text)
    text = re.sub(r'^at ', '', text)
    text = text.rstrip(' .')
    text = re.sub(r'\ba\s*\.?\s*m\.?$', 'am', text)
    text = re.sub(r'\bp\s*\.?\s*m\.?$', 'pm', text)
    numeric = re.fullmatch(r'(\d{1,2})(?:[:.](\d{2}))?\s*(am|pm)', text)
    if numeric:
        hour, minute, period = int(numeric[1]), int(numeric[2] or 0), numeric[3]
    else:
        spoken = re.fullmatch(r'([a-z ]+)\s+(am|pm)', text)
        if not spoken:
            return None
        words, period = spoken[1].split(), spoken[2]
        hour = SMALL.get(words[0], 0)
        rest = words[1:]
        if not rest or rest == ['oclock']:
            minute = 0
        elif len(rest) == 1 and rest[0] in SMALL:
            minute = SMALL[rest[0]]
        elif len(rest) == 1 and rest[0] in TENS:
            minute = TENS[rest[0]]
        elif len(rest) == 2 and rest[0] in TENS and rest[1] in DIGITS:
            minute = TENS[rest[0]] + int(DIGITS[rest[1]])
        elif len(rest) == 2 and rest[0] in {'oh', 'zero'} and rest[1] in DIGITS:
            minute = int(DIGITS[rest[1]])
        else:
            return None
    return (hour, minute, period) if 1 <= hour <= 12 and 0 <= minute < 60 else None


def matches_fact(fact: str, text: str, appointment) -> bool:
    parser = {'reference': reference_value, 'time': time_value}.get(fact)
    if parser is None:
        return False
    expected = parser(getattr(appointment, fact))
    return expected is not None and parser(text) == expected
