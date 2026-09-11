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

> Note: this repo ships with a synthetic sample dataset (`data/raw_studies.json`,
> matching the real API's JSON structure) so you can test `load_data.py` and
> `analyze.py` immediately without needing internet access. Replace it with
> real data using `fetch_data.py` before drawing any actual conclusions.

## Example findings (on the sample data)

- Trial attrition (terminated/withdrawn/suspended) rate by phase
- Sponsor concentration within each phase
- Completion rates across industry, government, academic/research-network,
  and other/unknown sponsor classes
- Rule-based buckets for free-text stop reasons
- Which countries host the most trial sites for a given condition
- Average trial duration by phase

(Swap in real data and these numbers become genuine findings you can quote.)

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

## Possible extensions

- Load into PostgreSQL instead of SQLite and add a `pg_trgm`-based condition
  search
- Build a simple dashboard (Streamlit/Tableau Public) on top of the CSVs in
  `exports/`
- Add a `outcomes` table by scraping results-posted trials for actual
  efficacy data

## Data-quality and methodology notes

- `Phase Not Applicable` and `Phase Not Reported` are intentionally separate. This prevents API values such as `NA` from being confused with a missing phase.
- `why_stopped` is retained as original free text, while `why_stopped_category` applies transparent keyword-based buckets: Accrual / Recruitment, Funding / Resources, Safety, Efficacy, PI / Staffing, Business Decision, and Other / Unclear. These are heuristic categories, not a substitute for NLP/manual coding.
- Sponsor analysis distinguishes Industry, Government, Academic / Research Network, and Other / Unknown instead of collapsing all non-industry sponsors into one group.
- The loader deletes child rows for an `nct_id` before re-inserting them, preventing duplicate sponsor/condition/intervention/location rows if the same trial appears more than once in an input file.
- All findings remain descriptive. They should not be interpreted as causal effects or as representative of all global clinical research.
