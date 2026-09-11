# Clinical Trials SQL Analysis

A SQL project analyzing public clinical trial data from ClinicalTrials.gov to
answer real pharma/biotech research operations questions: trial attrition,
sponsor behavior, phase-wise trends, and geographic distribution of trial sites.

## Pipeline

```
ClinicalTrials.gov API  →  raw_studies.json  →  SQLite DB (5 tables)  →  SQL analysis  →  CSVs + charts
     fetch_data.py                                load_data.py         analysis_queries.sql   analyze.py
```

1. **`scripts/fetch_data.py`** — pulls trial records for a chosen condition
   from the free, public ClinicalTrials.gov API (v2, no key required).
2. **`sql/schema.sql`** — relational schema: `studies` (fact table) plus
   `sponsors`, `conditions`, `interventions`, `locations` (each trial can have
   many of each, so these are separate tables joined on `nct_id`).
3. **`scripts/load_data.py`** — parses the nested API JSON and loads it into
   the SQLite tables.
4. **`sql/analysis_queries.sql`** — 12 queries answering questions like:
   phase-wise attrition rate, sponsor rankings within phase, sponsor-class
   completion rates, trial duration by phase, and geographic spread. Two
   analyses use CTE/window-function logic to demonstrate more advanced SQL.
5. **`scripts/analyze.py`** — runs every query, saves results as CSVs, generates
   two summary charts, and writes `exports/analysis_takeaways.md` with a
   short, data-driven interpretation under each output.

## How to run it

```bash
pip install requests pandas matplotlib

cd scripts
python fetch_data.py --condition "breast cancer" --max-studies 3000
python load_data.py
python analyze.py
```

Swap `--condition` for whatever therapeutic area you want to analyze
(e.g. `"type 2 diabetes"`, `"alzheimer"`, `"lung cancer"`).

> Note: this repo ships with a real dataset already pulled via `fetch_data.py`
> (`data/raw_studies.json`, 3,000 studies for the condition **"breast cancer"**)
> so you can run `load_data.py` and `analyze.py` immediately without needing
> internet access. It is one condition and one point-in-time snapshot, not a
> global sample — re-run `fetch_data.py` with a different `--condition` to
> analyze another therapeutic area or refresh the data.

## Example findings (breast cancer, n=3,000 trials, pulled via the ClinicalTrials.gov API)

- **Attrition by phase**: early-stage/mixed-phase trials stop early far more
  often than later-phase ones — 23.4% of `PHASE1, PHASE2` trials (39/167) and
  19.9% of `PHASE1` trials (59/296) were terminated, withdrawn, or suspended,
  versus 5.9% of `PHASE4` trials (4/68).
- **Sponsor concentration within phase**: leadership shifts by development
  stage — National Cancer Institute (NCI) leads PHASE1 (17 trials) and
  `PHASE1, PHASE2` (7 trials), Fudan University leads PHASE2 (27 trials), and
  Fudan/Hoffmann-La Roche tie for PHASE3 (12 trials each).
- **Completion rate by sponsor class**: Government (58.5%, 76/130) and
  Academic/Research Network (58.2%, 32/55) sponsors complete trials at a
  meaningfully higher rate than Industry (50.1%, 313/625) and Other/Unknown
  (43.3%, 949/2,190).
- **Normalized stop reasons**: Accrual/Recruitment is the largest classified
  bucket (133 of 330 stop-reason records, 40.3%), ahead of Funding/Resources
  (27), Safety (18), PI/Staffing (17), and Business Decision (17) — though
  Other/Unclear (114, 34.5%) is large enough that recruitment should be
  treated as a hypothesis, not the full explanation.
- **Geographic footprint**: the United States hosts the most trial sites
  (1,270 distinct trials with at least one US site), followed by China (400),
  France (219), Canada (187), and Spain (186).
- **Trial duration by phase**: `PHASE1, PHASE2` trials run longest on average
  among completed trials with full dates (2,154 days), followed by PHASE3
  (2,096 days) and PHASE2 (1,588 days) — durations that predate, span, or
  follow the COVID-19 disruption should be read with that in mind (see
  methodology notes below).
- **Sponsor-level early-stop rate** (min. 5 lead-sponsored trials): Wake
  Forest University Health Sciences (71.4%, 5/7) and University of Arkansas
  (66.7%, 4/6) show the highest observed early-stop rates — small samples,
  so treat as a screen for follow-up, not a verdict.
- **Intervention mix**: DRUG interventions dominate (2,981 of 5,840
  intervention rows, 51.0%), followed by Other (849) and Procedure (585).
- **Condition-label fragmentation**: "Breast Cancer" (1,550 trials) is the
  top label, but closely related synonyms — Metastatic Breast Cancer (172),
  Breast Neoplasms (168), Breast Cancer Female (70), Breast Carcinoma (60) —
  also appear in the top 10, illustrating how unnormalized condition names
  can understate one therapeutic area's true concentration.

These are real, quotable numbers for this specific pull (breast cancer,
3,000 studies, single API snapshot) — not a global or definitive estimate.
See `exports/analysis_takeaways.md` and `exports/strategy_decision_memo.md`
for the full interpretation and caveats behind each finding.

## Why this project

This was built to demonstrate SQL and relational data modeling skills using a
dataset that's directly relevant to biotech/pharma — going from raw,
nested API data to a clean relational schema to business-relevant answers,
the same workflow used in real clinical operations and R&D analytics teams.

## Suggested CV bullet

> Built an end-to-end SQL pipeline analyzing clinical trials from
> ClinicalTrials.gov — designed a 5-table relational schema, wrote 12 SQL
> analyses including CTE/window-function ranking, normalized free-text stop
> reasons, and automated CSV/chart/takeaway generation with Python.

## Strategy-oriented synthesis

The project is intentionally descriptive, but the outputs can be combined into a first-pass decision framework. For example, sponsor completion rates can be used as a hypothesis for partnership-risk screening, while phase-specific attrition and stop-reason categories identify where operational follow-up is most valuable. The generated `exports/strategy_decision_memo.md` connects these findings into a concise recommendation rather than treating each query as an isolated statistic.

**Important:** the current repository's numbers come from a real, single-condition pull (breast cancer, 3,000 studies, one point-in-time API snapshot) — they are genuine findings for that slice of the registry, not a synthetic illustration. They should still not be read as a global or definitive estimate of sponsor performance: re-run `fetch_data.py` for other conditions, and repeat sponsor comparisons within phase and condition, before using this for an actual partnership or risk decision.

## Possible extensions

- Load into PostgreSQL instead of SQLite and add a `pg_trgm`-based condition
  search
- Build a simple dashboard (Streamlit/Tableau Public) on top of the CSVs in
  `exports/`
- Add a `outcomes` table by scraping results-posted trials for actual
  efficacy data

## Data-quality and methodology notes

- `Phase Not Applicable` and `Phase Not Reported` are intentionally separate. This prevents API values such as `NA` from being confused with a missing phase.
- `why_stopped` is retained as original free text, while `why_stopped_category` applies transparent keyword-based buckets: Accrual / Recruitment, Funding / Resources, Safety, Efficacy, PI / Staffing, Business Decision, and Other / Unclear. In the bundled sample, Other / Unclear accounts for roughly 34.5% of stop-reason records, so the taxonomy is best treated as a first-pass screen; broader matching, NLP, or manual review would improve coverage.
- Sponsor analysis distinguishes Industry, Government, Academic / Research Network, and Other / Unknown instead of collapsing all non-industry sponsors into one group.
- The loader deletes child rows for an `nct_id` before re-inserting them, preventing duplicate sponsor/condition/intervention/location rows if the same trial appears more than once in an input file.
- `start_date` may represent an estimated/anticipated start for trials that have not yet begun. The sample contains five records with a 2027 start year; these are excluded from the historical trend chart and should not be read as completed historical activity.
- The 2020–2021 period coincides with the COVID-19 disruption, which is a plausible confounder for trial starts, recruitment, and timelines. Trend and duration comparisons spanning this period should acknowledge that external shock rather than attributing changes to trial characteristics alone.
- All findings remain descriptive. They should not be interpreted as causal effects or as representative of all global clinical research. Sponsor comparisons should ideally be repeated within the same phase and condition before being used for partnership or risk decisions.
- `.gitignore` excludes Python bytecode and common local environment files so compiled `__pycache__` artifacts are not shipped with the portfolio repository.

