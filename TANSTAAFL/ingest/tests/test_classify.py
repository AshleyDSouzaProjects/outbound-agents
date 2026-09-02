"""Classifier tests against realistic NSE/BSE announcement phrasing.

The precedence tests matter most: a mis-tagged auditor resignation silently defeats
the highest-value governance filter in the system.
"""

from __future__ import annotations

import pytest

from tanstaafl_ingest.classify import (
    Severity,
    classify,
    coverage,
    veto_categories,
)


# ---- veto-grade governance -----------------------------------------------

@pytest.mark.parametrize(
    "subject",
    [
        "Intimation of resignation of Statutory Auditors",
        "Resignation of the Statutory Auditor of the Company",
        "M/s Deloitte Haskins & Sells, Statutory Auditors have resigned",
        "Cessation of the Statutory Auditor",
        "Resignation of M/s ABC & Co LLP, Statutory Auditors",
        "Intimation of Resignation of Joint Auditor",
    ],
)
def test_auditor_resignation_detected(subject):
    result = classify(subject)
    assert result.category == "auditor_resignation"
    assert result.is_veto
    assert result.evidence  # always cites the matched text


@pytest.mark.parametrize(
    "subject,expected",
    [
        ("Statement on Impact of Audit Qualification for FY 2019-20", "auditor_qualification"),
        ("Auditors report contains a Qualified Opinion", "auditor_qualification"),
        ("Disclosure regarding Emphasis of Matter", "auditor_qualification"),
        ("Intimation of invocation of pledge by lender", "pledge_invocation"),
        ("Update on NCLT proceedings", "insolvency"),
        ("Initiation of Corporate Insolvency Resolution Process", "insolvency"),
        ("Disclosure of default in payment of interest on NCDs", "default"),
    ],
)
def test_other_veto_events(subject, expected):
    result = classify(subject)
    assert result.category == expected
    assert result.is_veto


# ---- precedence: the cases that actually bite ----------------------------

def test_auditor_resignation_beats_director_resignation():
    """'Resignation of ... Auditor' must never be filed as a director change."""
    result = classify("Resignation of Statutory Auditor and appointment of Director")
    assert result.category == "auditor_resignation"
    assert result.severity is Severity.VETO


def test_director_resignation_excluded_when_auditor_present():
    result = classify("Resignation of Independent Director")
    assert result.category == "director_resignation"
    assert result.severity is Severity.FLAG


def test_veto_wins_over_routine_in_combined_subject():
    """Filers routinely bundle events into one announcement."""
    result = classify(
        "Outcome of Board Meeting: Unaudited Financial Results and "
        "resignation of Statutory Auditors"
    )
    assert result.category == "auditor_resignation"
    assert "results" in result.also


def test_secondary_categories_are_retained():
    result = classify("Transcript of the Earnings Conference Call and Investor Presentation")
    assert result.category == "transcript"
    assert "investor_presentation" in result.also


# ---- promise-ledger and governance inputs --------------------------------

@pytest.mark.parametrize(
    "subject",
    [
        "Transcript of Earnings Conference Call held on May 14, 2024",
        "Audio recording of the Q4 FY24 Earnings Call",
        "Intimation of Analyst / Investor Meet",
        "Conference Call transcript",
    ],
)
def test_transcripts_detected(subject):
    assert classify(subject).category == "transcript"


@pytest.mark.parametrize(
    "subject,expected",
    [
        ("Shareholding Pattern for the quarter ended March 31, 2024", "shareholding_pattern"),
        ("Disclosure under Regulation 31(1) of SEBI (SAST) Regulations - Encumbrance",
         "pledge"),
        ("Creation of pledge of shares by promoter", "pledge"),
        ("Release of pledge over equity shares", "pledge"),
        ("Disclosure of Related Party Transactions for half year ended September 2023",
         "related_party"),
        ("Revision in credit rating by CRISIL", "credit_rating"),
        ("Annual Report for the Financial Year 2023-24", "annual_report"),
        ("Preferential allotment of equity shares", "fundraise"),
        ("Scheme of Arrangement between the Company and its subsidiary", "acquisition"),
    ],
)
def test_governance_and_disclosure_categories(subject, expected):
    assert classify(subject).category == expected


# ---- mechanics ------------------------------------------------------------

def test_parts_are_concatenated():
    """The useful phrase is as often in the attachment name as the subject."""
    result = classify("Outcome of Board Meeting", None, "auditor_resignation_letter.pdf")
    assert result.category == "auditor_resignation"


def test_empty_input_is_unclassified():
    assert classify().category == "unclassified"
    assert classify("", None).category == "unclassified"


def test_unknown_subject_is_unclassified_not_guessed():
    result = classify("Some entirely unrelated corporate filing about nothing")
    assert result.category == "unclassified"
    assert result.evidence == ""


def test_classification_is_deterministic():
    """Reproducibility is the whole reason this is not an LLM."""
    subject = "Resignation of Statutory Auditors and outcome of board meeting"
    assert [classify(subject).category for _ in range(20)].count("auditor_resignation") == 20


def test_case_insensitive():
    assert classify("RESIGNATION OF STATUTORY AUDITOR").category == "auditor_resignation"
    assert classify("resignation of statutory auditor").category == "auditor_resignation"


def test_veto_categories_are_the_expected_set():
    assert set(veto_categories()) == {
        "auditor_resignation", "auditor_qualification",
        "pledge_invocation", "insolvency", "default",
    }


def test_coverage_counts_unclassified_residue():
    """A rising unclassified share means exchange phrasing drifted and rules need work."""
    hist = coverage([
        "Resignation of Statutory Auditor",
        "Shareholding Pattern for the quarter",
        "Something we have no rule for at all",
    ])
    assert hist["auditor_resignation"] == 1
    assert hist["shareholding_pattern"] == 1
    assert hist["unclassified"] == 1
