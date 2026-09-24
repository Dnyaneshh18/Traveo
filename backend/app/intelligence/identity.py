"""
Student identity verification rules.

Traveo is a closed, trusted network: only verified students of the *same*
institution can see and join each other's rides.  Verification is explainable
and deterministic:

1. **Name match** – the institution name printed on the student's ID card must
   match the selected college (registry name or one of its aliases).  We
   normalise both strings (case, punctuation, stop-words, common abbreviations)
   and require a token-set similarity ≥ 0.80.
2. **ID format** – the ID / roll number must match the college's registered
   pattern (each institution has its own format, e.g. `COEP-2023-CS-042`).
3. **Uniqueness** – one college ID ⇒ one account (enforced by the database).

If (1) fails the registration is rejected with a clear message.  If (1) passes
but (2) fails, the account is created in `pending` state for manual review by
the ops team (ID-card photo required) – the student can browse but cannot
create or join rides until verified.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from difflib import SequenceMatcher

_GRAMMAR_WORDS = {"the", "of", "and", "for", "at", "in", "a", "an", "&"}
_CITY_WORDS = {"pune", "mumbai", "bangalore", "bengaluru", "delhi", "hyderabad", "chennai", "nagpur", "nashik"}
_STOP_WORDS = _GRAMMAR_WORDS | _CITY_WORDS
_ABBREVIATIONS = {
    "engg": "engineering",
    "engineering": "engineering",
    "inst": "institute",
    "institute": "institute",
    "tech": "technology",
    "technology": "technology",
    "coll": "college",
    "college": "college",
    "univ": "university",
    "university": "university",
    "mgmt": "management",
    "mgt": "management",
    "sci": "science",
    "jr": "junior",
    "sr": "senior",
    "govt": "government",
    "intl": "international",
    "international": "international",
    "hs": "high school",
    "hr": "higher",
    "sec": "secondary",
}


def normalise_name(name: str, *, stop_words: set[str] | None = None) -> str:
    s = name.lower()
    s = re.sub(r"[\(\)\[\],.\-_/'’\"]+", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    stops = _STOP_WORDS if stop_words is None else stop_words
    tokens = []
    for t in s.split(" "):
        if not t or t in stops:
            continue
        tokens.append(_ABBREVIATIONS.get(t, t))
    return " ".join(tokens)


def _acronyms(name: str) -> set[str]:
    """Plausible acronyms: with/without grammar words ("of"), with/without the city."""
    variants = set()
    for stops in (set(), _GRAMMAR_WORDS, _CITY_WORDS, _STOP_WORDS):
        raw = re.sub(r"[\(\)\[\],.\-_/'’\"]+", " ", name.lower())
        tokens = [t for t in raw.split() if t and t not in stops]
        if tokens:
            variants.add("".join(t[0] for t in tokens))
    return variants


def _token_set(s: str) -> set[str]:
    return set(s.split(" ")) if s else set()


def name_similarity(a: str, b: str) -> float:
    na, nb = normalise_name(a), normalise_name(b)
    if not na or not nb:
        return 0.0
    if na == nb:
        return 1.0
    ta, tb = _token_set(na), _token_set(nb)
    jaccard = len(ta & tb) / len(ta | tb) if ta | tb else 0.0
    containment = len(ta & tb) / min(len(ta), len(tb)) if ta and tb else 0.0
    seq = SequenceMatcher(None, na, nb).ratio()
    # Acronym support – "COEP" vs "College of Engineering Pune" / "PICT" vs "Pune Institute of Computer Technology"
    compact_a = na.replace(" ", "")
    compact_b = nb.replace(" ", "")
    acronym = 0.0
    if 3 <= len(compact_a) <= 8 and (compact_a in _acronyms(b) or compact_a == compact_b):
        acronym = 1.0
    elif 3 <= len(compact_b) <= 8 and (compact_b in _acronyms(a) or compact_a == compact_b):
        acronym = 1.0
    # Partial acronym: every short token of the shorter name is either a token of the longer
    # name or the acronym of a consecutive run of its tokens ("MIT WPU" ~ "MIT World Peace University").
    if not acronym:
        short, long_ = (na, nb) if len(na) <= len(nb) else (nb, na)
        long_tokens = long_.split(" ")
        runs = {"".join(t[0] for t in long_tokens[i:j]) for i in range(len(long_tokens)) for j in range(i + 1, len(long_tokens) + 1)}
        short_tokens = short.split(" ")
        if short_tokens and all(t in long_tokens or (len(t) >= 2 and t in runs) for t in short_tokens):
            acronym = 0.9
    return max(seq, 0.5 * jaccard + 0.5 * containment, acronym)


@dataclass(slots=True)
class IdentityCheck:
    name_matches: bool
    name_score: float
    id_format_valid: bool
    matched_alias: str | None

    @property
    def auto_verified(self) -> bool:
        return self.name_matches and self.id_format_valid


DEFAULT_ID_PATTERN = r"^[A-Za-z0-9][A-Za-z0-9/\-_. ]{3,29}$"


def check_identity(
    *,
    typed_college_name: str,
    college_name: str,
    aliases: list[str],
    college_id_number: str,
    id_pattern: str | None,
    threshold: float = 0.80,
) -> IdentityCheck:
    best_alias, best = None, 0.0
    for candidate in [college_name, *aliases]:
        if not candidate:
            continue
        score = name_similarity(typed_college_name, candidate)
        if score > best:
            best, best_alias = score, candidate
    name_ok = best >= threshold

    pattern = id_pattern or DEFAULT_ID_PATTERN
    try:
        id_ok = re.fullmatch(pattern, college_id_number.strip(), flags=re.IGNORECASE) is not None
    except re.error:
        id_ok = re.fullmatch(DEFAULT_ID_PATTERN, college_id_number.strip()) is not None

    return IdentityCheck(name_matches=name_ok, name_score=round(best, 3), id_format_valid=id_ok, matched_alias=best_alias if name_ok else None)
