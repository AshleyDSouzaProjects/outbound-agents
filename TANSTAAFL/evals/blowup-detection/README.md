# Blowup Detection Eval

**The highest-leverage eval in the system, and it is available on day one.**

Almost every eval that matters for investing has a multi-year feedback lag. This one does not:
the outcomes are already known, so we can score the Tier-2 rejection filters *immediately* —
in month three rather than in 2031.

## Method

Run `governance-sentinel`, `forensic-accountant` and `capital-allocation-auditor` against each
company below using **point-in-time data only** — filings published on or before the test date,
which is set 4+ quarters before the collapse became public.

## The set

| Company | Collapse | Test as-of | Primary mechanism |
|---|---|---|---|
| Satyam | Jan 2009 | 2007-12-31 | Fabricated cash; auditor failure |
| Gitanjali Gems | Feb 2018 | 2016-12-31 | Outright fraud; RPT |
| Vakrangee | Feb 2018 | 2017-03-31 | Auditor resignation; manipulation |
| Manpasand Beverages | May 2018 | 2017-09-30 | Auditor resignation; revenue fabrication |
| IL&FS | Sep 2018 | 2017-03-31 | Group opacity; leverage |
| Zee / Essel | Jan 2019 | 2018-03-31 | Promoter pledging cascade |
| DHFL | Jun 2019 | 2018-03-31 | RPT lending; diversion |
| Coffee Day | Jul 2019 | 2018-03-31 | Promoter debt; RPT diversion |
| Yes Bank | Mar 2020 | 2018-09-30 | Concealed asset quality |

## Gate

- **Sensitivity:** reject ≥ **7 of 9** before collapse. Below that, the filters do not work and
  are not deployed.
- **Specificity:** total reject rate across the full Nifty 500 must stay in the **30–50%** band.
  A filter that rejects 90% of the universe trivially catches all nine and is useless.

Both must pass. Sensitivity alone is easy and meaningless.

## The contamination problem — read before running

**The model knows how these stories end.** That knowledge is in pretraining and cannot be
removed, which makes this eval much harder to run honestly than it looks. An agent asked to
assess Yes Bank as of 2018 will be influenced by knowing what happened in 2020, and will
produce a confident "reject" for reasons it did not actually derive from the filings.

Mitigations, in increasing order of reliability:

1. Instruct explicitly against hindsight (weak — necessary, not sufficient).
2. Require every reject to cite **specific filing evidence** with document, page and line.
   A reject whose reasons cannot be traced to a point-in-time document is void.
3. **Blind the company identity** where feasible: strip names, tickers and distinctive
   identifiers, present only the financial and governance data. This is the strongest control
   and the only one that really works.
4. Include **matched controls** — companies with similar profiles that did *not* collapse —
   also blinded. Sensitivity without specificity on matched controls proves nothing, and this
   is where a hindsight-contaminated agent gets caught.

Without control #4, a passing score on this eval is not evidence of anything. Build the
control set before trusting a single result.

## Outputs

```
results/{company}-{as_of}.yaml     verdict, reasons, cited evidence
results/_summary.md                sensitivity, specificity, per-filter attribution
results/_controls.md               matched non-collapse companies, same treatment
```
