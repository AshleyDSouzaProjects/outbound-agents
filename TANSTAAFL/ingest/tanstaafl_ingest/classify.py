"""Deterministic classifier for exchange corporate announcements.

WHY RULES AND NOT AN LLM
------------------------
1. Reproducibility. A backtest must give identical answers on every rerun. An LLM
   classifier does not, so it would quietly invalidate every point-in-time result.
2. Cost. ~500 companies x 15 years x ~50 announcements is ~375,000 items. This is a
   one-cent problem with regexes and a four-figure one with a model.
3. Auditability. Every classification cites the exact substring that triggered it, so
   `governance-sentinel` can carry evidence rather than an opinion (CLAUDE.md §2).
4. Testability. Deterministic rules can be unit-tested against known subject lines.

An LLM belongs on the `UNCLASSIFIED` residue only — as an escalation for building new
rules, never as the classifier of record.

Announcement subjects are messy, inconsistent between exchanges, and frequently
misfiled by the filer. Precision beats recall here: an announcement we fail to tag
gets caught by the annual full-text pass, whereas a mis-tagged auditor resignation
silently defeats the highest-value governance filter we have.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Iterable


class Severity(str, Enum):
    """Maps onto governance-sentinel's authority (doctrine/20-india-context.md)."""

    VETO = "veto"      # hard-reject trigger
    FLAG = "flag"      # investigate
    INFO = "info"      # routine; useful as evidence, not as a signal


@dataclass(frozen=True, slots=True)
class Rule:
    category: str
    severity: Severity
    precedence: int  # lower wins when several rules match
    patterns: tuple[str, ...]
    # Guards let a specific rule pre-empt a general one, e.g. auditor resignation
    # must not be swallowed by the generic director-resignation rule.
    excludes: tuple[str, ...] = ()

    def match(self, variants: tuple[str, ...]) -> str | None:
        for text in variants:
            for pattern in self.patterns:
                m = re.search(pattern, text, re.IGNORECASE)
                if m:
                    if any(
                        re.search(x, v, re.IGNORECASE)
                        for x in self.excludes
                        for v in variants
                    ):
                        return None
                    return m.group(0)
        return None


# Precedence: 10s = governance vetoes, 20s = governance flags, 30s = disclosures,
# 40s = routine. Lower number wins the primary label.
RULES: tuple[Rule, ...] = (
    # ---- 10s: veto-grade governance events -----------------------------
    Rule(
        "auditor_resignation", Severity.VETO, 10,
        (
            r"resignation\s+of\s+(the\s+)?(statutory\s+|joint\s+|secretarial\s+)?auditor",
            r"(statutory\s+|joint\s+)?auditors?\s+(has|have)\s+resigned",
            r"cessation\s+of\s+(the\s+)?statutory\s+auditor",
            r"resignation\s+of\s+m/s\.?\s+[^,]{2,60},?\s*(the\s+)?(statutory\s+)?auditor",
            # Reversed order, common in attachment filenames and some subject lines:
            # "Auditor Resignation Letter", "Statutory Auditors Resignation"
            r"auditors?\s+resignation",
        ),
    ),
    Rule(
        "auditor_qualification", Severity.VETO, 11,
        (
            r"qualified\s+opinion",
            r"adverse\s+opinion",
            r"disclaimer\s+of\s+opinion",
            r"modified\s+opinion",
            r"emphasis\s+of\s+matter",
            r"statement\s+on\s+impact\s+of\s+audit\s+qualification",
        ),
    ),
    Rule(
        "pledge_invocation", Severity.VETO, 12,
        (r"invocation\s+of\s+(the\s+)?pledge", r"pledged?\s+shares?\s+invoked"),
    ),
    Rule(
        "insolvency", Severity.VETO, 13,
        (
            r"\bNCLT\b", r"insolvency\s+and\s+bankruptcy\s+code", r"\bIBC\b",
            r"corporate\s+insolvency\s+resolution\s+process", r"\bCIRP\b",
            r"winding\s+up", r"liquidation",
        ),
    ),
    Rule(
        "default", Severity.VETO, 14,
        (
            r"default\s+in\s+payment", r"delay\s+in\s+payment\s+of\s+interest",
            r"disclosure\s+of\s+default", r"failure\s+to\s+repay",
        ),
    ),

    # ---- 20s: flag-grade governance ------------------------------------
    Rule(
        "auditor_change", Severity.FLAG, 20,
        (
            r"appointment\s+of\s+(the\s+)?(statutory\s+|joint\s+)?auditor",
            r"change\s+in\s+(the\s+)?(statutory\s+)?auditor",
            r"re-?appointment\s+of\s+(the\s+)?statutory\s+auditor",
        ),
    ),
    Rule(
        "pledge", Severity.FLAG, 21,
        (
            r"encumbrance", r"pledge\s+of\s+shares", r"creation\s+of\s+pledge",
            r"regulation\s+31\s*\(\s*[12]\s*\)", r"release\s+of\s+pledge",
            r"revocation\s+of\s+pledge",
        ),
    ),
    Rule(
        "director_resignation", Severity.FLAG, 22,
        (
            r"resignation\s+of\s+(the\s+)?(independent\s+)?director",
            r"resignation\s+of\s+(the\s+)?(managing\s+director|chief\s+\w+\s+officer|CFO|CEO|company\s+secretary)",
            r"cessation\s+of\s+(the\s+)?director",
        ),
        excludes=(r"auditor",),
    ),
    Rule(
        "related_party", Severity.FLAG, 23,
        (r"related\s+party\s+transaction", r"\bRPT\b", r"materially\s+significant\s+related\s+part"),
    ),
    Rule(
        "credit_rating", Severity.FLAG, 24,
        (
            r"credit\s+rating", r"revision\s+in\s+rating", r"rating\s+action",
            r"\b(CRISIL|ICRA|CARE\s+Ratings|India\s+Ratings|Brickwork|Acuite)\b",
        ),
    ),

    # ---- 30s: substantive disclosures ----------------------------------
    Rule(
        "transcript", Severity.INFO, 30,
        (
            r"transcript",                       # feeds the promise ledger
            r"earnings\s+call",
            r"(analyst|investor)s?\s+(call|conference|meet)",
            r"con(ference)?\s*call",
        ),
    ),
    Rule(
        "shareholding_pattern", Severity.INFO, 31,
        (r"shareholding\s+pattern", r"regulation\s+31\s+of\s+.{0,40}LODR"),
    ),
    Rule(
        "annual_report", Severity.INFO, 32,
        (r"annual\s+report", r"notice\s+of\s+(the\s+)?annual\s+general\s+meeting", r"\bAGM\b"),
    ),
    Rule(
        "results", Severity.INFO, 33,
        (
            r"(un)?audited\s+financial\s+results", r"financial\s+results\s+for\s+the\s+quarter",
            r"outcome\s+of\s+(the\s+)?board\s+meeting", r"quarterly\s+results",
        ),
    ),
    Rule(
        "fundraise", Severity.FLAG, 34,
        (
            r"preferential\s+(issue|allotment)", r"qualified\s+institutions\s+placement",
            r"\bQIP\b", r"rights\s+issue", r"issue\s+of\s+(equity\s+)?shares",
            r"conversion\s+of\s+warrants", r"fund\s*rais",
        ),
    ),
    Rule(
        "buyback", Severity.INFO, 35,
        (r"buy-?back", r"buyback\s+of\s+(equity\s+)?shares"),
    ),
    Rule(
        "acquisition", Severity.FLAG, 36,
        (
            r"acquisition\s+of", r"scheme\s+of\s+(arrangement|amalgamation|merger)",
            r"\bmerger\b", r"\bdemerger\b", r"slump\s+sale", r"divestment",
        ),
    ),

    # ---- 40s: routine ---------------------------------------------------
    Rule(
        "board_meeting_notice", Severity.INFO, 40,
        (r"(intimation|notice)\s+of\s+board\s+meeting", r"board\s+meeting\s+intimation"),
    ),
    Rule(
        "corporate_action", Severity.INFO, 41,
        (r"\bdividend\b", r"\bbonus\s+issue\b", r"stock\s+split", r"sub-?division\s+of\s+shares",
         r"record\s+date"),
    ),
    Rule(
        "investor_presentation", Severity.INFO, 42,
        (r"investor\s+presentation", r"corporate\s+presentation", r"press\s+release"),
    ),
    Rule(
        "trading_window", Severity.INFO, 43,
        (r"trading\s+window", r"closure\s+of\s+trading\s+window", r"code\s+of\s+conduct"),
    ),
)


@dataclass(slots=True)
class Classification:
    category: str
    severity: Severity
    evidence: str           # the exact substring that matched — auditable
    also: list[str] = field(default_factory=list)  # other categories that matched

    @property
    def is_veto(self) -> bool:
        return self.severity is Severity.VETO


UNCLASSIFIED = Classification("unclassified", Severity.INFO, "")


def classify(*parts: str | None) -> Classification:
    """Classify an announcement from its subject, description and attachment name.

    All parts are concatenated: exchanges scatter the meaningful text across fields
    inconsistently, and the useful phrase is as often in the attachment filename as
    in the subject.
    """
    text = " ".join(p for p in parts if p).strip()
    if not text:
        return UNCLASSIFIED

    # Attachment filenames carry the meaningful phrase as often as the subject does,
    # but separated by underscores or hyphens rather than spaces. Match against
    # normalised variants too and take the union, so neither form is a false
    # negative: hyphen-normalising alone would break patterns like `re-?appointment`.
    variants = (
        text,
        re.sub(r"[_.]+", " ", text),
        re.sub(r"[_\-.]+", " ", text),
    )

    hits: list[tuple[Rule, str]] = []
    for rule in RULES:
        evidence = rule.match(variants)
        if evidence:
            hits.append((rule, evidence))

    if not hits:
        return UNCLASSIFIED

    hits.sort(key=lambda h: h[0].precedence)
    primary, evidence = hits[0]
    return Classification(
        category=primary.category,
        severity=primary.severity,
        evidence=evidence,
        also=[r.category for r, _ in hits[1:]],
    )


def categories() -> list[str]:
    return sorted({r.category for r in RULES})


def veto_categories() -> list[str]:
    return sorted({r.category for r in RULES if r.severity is Severity.VETO})


def coverage(texts: Iterable[str]) -> dict[str, int]:
    """Category histogram, including the unclassified residue.

    Track this over time: a rising `unclassified` share means the exchanges have
    changed their phrasing and the rules need extending. Silent drift here degrades
    every governance filter downstream.
    """
    out: dict[str, int] = {}
    for text in texts:
        c = classify(text)
        out[c.category] = out.get(c.category, 0) + 1
    return out
