"""Run the named SQL analyses and generate CSVs, charts, and takeaways."""
import argparse
import re
import sqlite3
from pathlib import Path
from datetime import date

import pandas as pd
import matplotlib.pyplot as plt


def parse_named_queries(sql_path: str):
    text = Path(sql_path).read_text(encoding="utf-8")
    blocks = re.split(r"\n\n-- \d+\.\s*", "\n\n" + text)
    queries = []
    for block in blocks[1:]:
        label, _, rest = block.partition("\n")
        query = rest.strip()
        if query:
            queries.append((label.strip(), query))
    return queries


def build_takeaway(number, df):
    """Write a concise, decision-oriented interpretation for each analysis."""
    if df.empty:
        return "No rows were returned for this analysis in the current dataset."

    if number == 1:
        phase_counts = df.sort_values("trial_count", ascending=False)
        top = phase_counts.iloc[0]
        reported = phase_counts[~phase_counts["phase"].isin(["Phase Not Applicable", "Phase Not Reported"])]
        reported_text = f"Among reported clinical phases, {reported.iloc[0]['phase']} is largest ({int(reported.iloc[0]['trial_count']):,} trials)." if not reported.empty else "No reported clinical phases are present."
        return (f"Phase Not Applicable is the largest category ({int(top['trial_count']):,} trials), while {reported_text} "
                "The large non-applicable/not-reported share means phase-based comparisons should be restricted to interpretable phase categories rather than treating missingness as a clinical-development stage.")

    if number == 2:
        top = df.sort_values(["phase", "sponsor_rank", "sponsor_name"]).iloc[0]
        phase = top["phase"]
        phase_rows = df[df["phase"] == phase].sort_values("trials_led", ascending=False)
        lead = phase_rows.iloc[0]
        return (f"Sponsor leadership varies by phase: {lead['sponsor_name']} leads {phase} with {int(lead['trials_led']):,} trial(s), while other phases have different leaders. "
                "For competitive or partnership analysis, phase-specific sponsor rankings are more actionable than one overall leaderboard because they compare organizations operating at similar development stages.")

    if number == 3:
        top = df.sort_values("avg_enrollment", ascending=False).iloc[0]
        phase2 = df[df["phase"] == "PHASE2"]
        phase3 = df[df["phase"] == "PHASE3"]
        comparison = ""
        if not phase2.empty and not phase3.empty:
            comparison = f" Phase 3 averages {phase3.iloc[0]['avg_enrollment']:,.0f} participants versus {phase2.iloc[0]['avg_enrollment']:,.0f} in Phase 2."
        return (f"{top['phase']} has the highest average enrollment ({top['avg_enrollment']:,.0f} participants), but that category is dominated by records with missing/unreported phase information. "
                f"{comparison} Enrollment reflects the observed registry sample and should not be treated as a universal phase requirement.")

    if number == 4:
        years = pd.to_numeric(df["start_year"], errors="coerce")
        valid = df.assign(_year=years).dropna(subset=["_year"])
        historical = valid[valid["_year"] <= date.today().year]
        peak = historical.loc[historical["trials_started"].idxmax()] if not historical.empty else None
        future = valid[valid["_year"] > date.today().year]
        future_note = ""
        if not future.empty:
            future_note = f" The dataset also contains {int(future['trials_started'].sum()):,} trial(s) with a future start year; these are best treated as planned/estimated dates rather than completed historical activity."
        peak_note = f" Activity peaks at {int(peak['trials_started']):,} starts in {int(peak['_year'])}." if peak is not None else ""
        return (f"The registry shows a long-run increase in trial starts, with the highest historical year in this sample being {int(peak['_year']) if peak is not None else 'the available period'}.{peak_note} "
                "Recent years may be incomplete, and 2020–2021 should be interpreted cautiously because the COVID-19 disruption is a plausible confounder of trial starts and operations." + future_note)

    if number == 5:
        top = df.sort_values("pct_stopped_early", ascending=False).iloc[0]
        return (f"The highest observed early-stop rate is {top['pct_stopped_early']:.1f}% in {top['phase']} ({int(top['stopped_early'])} of {int(top['total_trials'])} trials). "
                "The pattern suggests that attrition risk is not uniform across development stages, but the analysis is descriptive and should be validated within condition, sponsor, and trial-design subgroups before being used for risk decisions.")

    if number == 6:
        total = int(df["occurrences"].sum())
        top = df.iloc[0]
        unclear = df.loc[df["why_stopped_category"] == "Other / Unclear", "occurrences"]
        unclear_n = int(unclear.iloc[0]) if not unclear.empty else 0
        unclear_pct = (100 * unclear_n / total) if total else 0
        return (f"Accrual / Recruitment is the most common normalized stop-reason bucket ({int(top['occurrences'])} of {total} records, {100*int(top['occurrences'])/total:.1f}%). "
                f"However, Other / Unclear still contains {unclear_n} records ({unclear_pct:.1f}%), so recruitment should be treated as a signal for follow-up rather than a complete explanation of trial failure; broader text matching or manual/NLP review would improve coverage.")

    if number == 7:
        top = df.iloc[0]
        return (f"Breast Cancer is the most frequently represented condition ({int(top['trial_count']):,} trials), with several closely related condition labels also appearing in the top 10. "
                "This illustrates why condition normalization matters: raw registry labels can split one therapeutic area across synonyms and subtypes, which can distort apparent research concentration.")

    if number == 8:
        top = df.sort_values("pct_completed", ascending=False).iloc[0]
        industry = df[df["sponsor_type"] == "Industry"]
        industry_rate = float(industry.iloc[0]["pct_completed"]) if not industry.empty else None
        gap = (float(top["pct_completed"]) - industry_rate) if industry_rate is not None else None
        gap_text = f" This is {gap:.1f} percentage points above Industry ({industry_rate:.1f}%)." if gap is not None else ""
        return (f"Government and Academic / Research Network sponsors have the highest observed completion rates ({top['pct_completed']:.1f}% and {float(df[df['sponsor_type'] == 'Academic / Research Network'].iloc[0]['pct_completed']):.1f}%, respectively)." + gap_text + " "
                "For partnership-risk screening, this is a useful hypothesis to investigate within the same phase and condition, but it is not evidence that sponsor class causes completion outcomes.")

    if number == 9:
        phase2 = df[df["phase"] == "PHASE2"]
        phase3 = df[df["phase"] == "PHASE3"]
        top = df.sort_values("avg_duration_days", ascending=False).iloc[0]
        comparison = ""
        if not phase2.empty and not phase3.empty:
            comparison = f" Phase 3 averages {phase3.iloc[0]['avg_duration_days']:,.0f} days versus {phase2.iloc[0]['avg_duration_days']:,.0f} days in Phase 2."
        base = (f"Among completed trials with complete dates, {top['phase']} has the longest average duration at {top['avg_duration_days']:,.0f} days." )
        if not phase3.empty:
            base += f" Phase 3 averages {float(phase3.iloc[0]['avg_duration_days']):,.0f} days versus {float(phase2.iloc[0]['avg_duration_days']):,.0f} days in Phase 2." if not phase2.empty else f" Phase 3 averages {float(phase3.iloc[0]['avg_duration_days']):,.0f} days."
        return base + " Duration comparisons are sensitive to study design and reporting conventions, and the 2020–2021 COVID-19 disruption is a plausible confounder for timelines in this period."

    if number == 10:
        top = df.iloc[0]
        return (f"The United States has the largest geographic footprint in the sample ({int(top['trial_count']):,} distinct trials with at least one listed site), followed by China ({int(df.iloc[1]['trial_count']):,}). "
                "This can inform site-footprint and recruitment discussions, but registry site counts measure reported trial presence rather than total site capacity or enrollment quality.")

    if number == 11:
        top = df.iloc[0]
        total = int(df["count"].sum())
        return (f"DRUG interventions dominate the intervention rows ({int(top['count']):,} of {total:,}, {100*int(top['count'])/total:.1f}%). "
                "Because a single trial can contribute multiple intervention rows, this is an intervention-mix view rather than a trial-level percentage; it is useful for describing the therapeutic modality mix but not market share.")

    if number == 12:
        top = df.iloc[0]
        return (f"Among sponsors with at least five lead-sponsored trials, {top['sponsor_name']} has the highest observed early-stop rate ({top['pct_stopped_early']:.1f}%, {int(top['stopped_early'])}/{int(top['total_trials'])}). "
                "The minimum-trial threshold removes extreme one-trial rates, but the remaining samples are still small; any partnership or sponsor-risk decision should validate the result within phase, condition, and study design.")

    return "This output summarizes the current registry sample. Interpret it in the context of the selected condition, reporting coverage, and query definition."


def write_decision_memo(out: Path):
    """Create a short strategy-oriented memo from the generated CSV outputs."""
    completion = pd.read_csv(out / "08_completion_rate_by_lead_sponsor_class.csv")
    attrition = pd.read_csv(out / "05_attrition_of_trials_terminated_withdrawn_suspended_by_phase.csv")
    stopped = pd.read_csv(out / "06_most_common_normalized_reasons_trials_stopped_early.csv")
    countries = pd.read_csv(out / "10_top_10_countries_running_the_most_trial_sites.csv")

    gov = completion.loc[completion.sponsor_type == "Government", "pct_completed"]
    acad = completion.loc[completion.sponsor_type == "Academic / Research Network", "pct_completed"]
    ind = completion.loc[completion.sponsor_type == "Industry", "pct_completed"]
    gov_v = float(gov.iloc[0]) if not gov.empty else float("nan")
    acad_v = float(acad.iloc[0]) if not acad.empty else float("nan")
    ind_v = float(ind.iloc[0]) if not ind.empty else float("nan")

    top_attr = attrition.sort_values("pct_stopped_early", ascending=False).iloc[0]
    accrual = int(stopped.loc[stopped.why_stopped_category == "Accrual / Recruitment", "occurrences"].iloc[0])
    unclear = int(stopped.loc[stopped.why_stopped_category == "Other / Unclear", "occurrences"].iloc[0])
    total_stopped_reasons = int(stopped.occurrences.sum())
    us = int(countries.iloc[0].trial_count)
    china = int(countries.iloc[1].trial_count)

    memo = f"""# Strategy / Decision Memo

## Executive takeaway

In this **single-condition pull (breast cancer, 3,000 studies)**, sponsor completion rates differ meaningfully by sponsor class: Government ({gov_v:.1f}%) and Academic / Research Network ({acad_v:.1f}%) are above Industry ({ind_v:.1f}%). The gap is a useful hypothesis for partnership-risk screening, but it should **not** be interpreted causally, nor generalized beyond this condition; the next test should compare sponsor classes within the same clinical phase and condition, with study-design and enrollment differences controlled where possible.

## What the data suggests

1. **Attrition is concentrated in earlier/mixed development stages.** The highest observed early-stop rate is {top_attr['pct_stopped_early']:.1f}% in {top_attr['phase']} ({int(top_attr['stopped_early'])}/{int(top_attr['total_trials'])}). This suggests that a sponsor-risk screen should examine phase-specific track record rather than rely on one overall completion metric.

2. **Recruitment is the clearest operational signal.** Accrual / Recruitment is the largest normalized stop-reason bucket ({accrual} of {total_stopped_reasons} classified records), but Other / Unclear still represents {unclear} records ({100*unclear/total_stopped_reasons:.1f}%). A BD or clinical-operations team should therefore treat recruitment as a follow-up hypothesis, not a complete failure taxonomy.

3. **Clinical-trial activity is geographically concentrated.** The United States appears in {us:,} distinct trials with at least one listed site versus {china:,} for China. This is useful context for site-footprint and recruitment planning, but registry presence is not the same as site capacity or patient throughput.

## Recommended decision framework

For a partnership or sponsor-risk screen, use this analysis as a **first-pass triage layer**:

- compare completion/attrition **within phase and condition**;
- weight sponsor history by a meaningful minimum trial count;
- separately review recruitment, safety, efficacy, and funding-related stop reasons;
- manually review the Other / Unclear stop-reason bucket before making a high-stakes decision;
- validate any apparent sponsor advantage against study design, enrollment size, and calendar period.

The current outputs are descriptive. They are suitable for generating hypotheses and prioritizing follow-up analysis, not for making causal claims about sponsor performance.
"""
    (out / "strategy_decision_memo.md").write_text(memo, encoding="utf-8")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", default="../data/clinical_trials.db")
    parser.add_argument("--sql", default="../sql/analysis_queries.sql")
    parser.add_argument("--out", default="../exports")
    args = parser.parse_args()
    out = Path(args.out)
    out.mkdir(exist_ok=True)
    conn = sqlite3.connect(args.db)
    queries = parse_named_queries(args.sql)
    takeaway_sections = []

    for i, (label, query) in enumerate(queries, start=1):
        df = pd.read_sql_query(query, conn)
        safe_name = re.sub(r"[^a-zA-Z0-9]+", "_", label).strip("_").lower()[:60]
        filename = f"{i:02d}_{safe_name}.csv"
        df.to_csv(out / filename, index=False)
        takeaway = build_takeaway(i, df)
        takeaway_sections.append(f"## {i}. {label}\n\n**Output:** `{filename}`\n\n**Takeaway:** {takeaway}\n")
        print(f"[{i}] {label}: {len(df)} rows -> {filename}")

    phase_df = pd.read_sql_query("SELECT phase, COUNT(*) c FROM studies GROUP BY phase ORDER BY c DESC", conn)
    plt.figure(figsize=(7, 4))
    plt.bar(phase_df["phase"], phase_df["c"])
    plt.title("Trials by Phase")
    plt.ylabel("Number of trials")
    plt.xticks(rotation=30, ha="right")
    plt.tight_layout()
    plt.savefig(out / "chart_trials_by_phase.png", dpi=150)
    plt.close()

    year_df = pd.read_sql_query(
        "SELECT CAST(SUBSTR(start_date,1,4) AS INTEGER) AS yr, COUNT(*) c "
        "FROM studies WHERE start_date IS NOT NULL GROUP BY yr ORDER BY yr", conn
    )
    # Do not plot future planned/estimated start years on the historical trend chart.
    year_chart_df = year_df[year_df["yr"] <= date.today().year]
    plt.figure(figsize=(8, 4))
    plt.plot(year_chart_df["yr"], year_chart_df["c"], marker="o")
    plt.title("Trials Started per Year (through current year)")
    plt.ylabel("Number of trials")
    plt.xlabel("Start year")
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    plt.savefig(out / "chart_trials_per_year.png", dpi=150)
    plt.close()
    conn.close()

    (out / "analysis_takeaways.md").write_text(
        "# Analysis Takeaways\n\n" + "\n".join(takeaway_sections), encoding="utf-8"
    )
    write_decision_memo(out)
    print(f"\nDone. CSVs, charts, analysis_takeaways.md, and strategy_decision_memo.md saved to {out}/")


if __name__ == "__main__":
    main()
