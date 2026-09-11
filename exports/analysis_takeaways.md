# Analysis Takeaways

## 1. How many trials are in each phase?

**Output:** `01_how_many_trials_are_in_each_phase.csv`

**Takeaway:** Phase Not Applicable is the largest category (842 trials), while Among reported clinical phases, PHASE2 is largest (648 trials). The large non-applicable/not-reported share means phase-based comparisons should be restricted to interpretable phase categories rather than treating missingness as a clinical-development stage.

## 2. Top sponsors within each phase (window function)

**Output:** `02_top_sponsors_within_each_phase_window_function.csv`

**Takeaway:** Sponsor leadership varies by phase: Mayo Clinic leads EARLY_PHASE1 with 3 trial(s), while other phases have different leaders. For competitive or partnership analysis, phase-specific sponsor rankings are more actionable than one overall leaderboard because they compare organizations operating at similar development stages.

## 3. Average enrollment size by phase

**Output:** `03_average_enrollment_size_by_phase.csv`

**Takeaway:** Phase Not Reported has the highest average enrollment (3,517 participants), but that category is dominated by records with missing/unreported phase information.  Phase 3 averages 1,342 participants versus 94 in Phase 2. Enrollment reflects the observed registry sample and should not be treated as a universal phase requirement.

## 4. Trend: number of trials started per year

**Output:** `04_trend_number_of_trials_started_per_year.csv`

**Takeaway:** The registry shows a long-run increase in trial starts, with the highest historical year in this sample being 2023. Activity peaks at 198 starts in 2023. Recent years may be incomplete, and 2020–2021 should be interpreted cautiously because the COVID-19 disruption is a plausible confounder of trial starts and operations. The dataset also contains 5 trial(s) with a future start year; these are best treated as planned/estimated dates rather than completed historical activity.

## 5. Attrition: % of trials terminated/withdrawn/suspended, by phase

**Output:** `05_attrition_of_trials_terminated_withdrawn_suspended_by_phase.csv`

**Takeaway:** The highest observed early-stop rate is 23.4% in PHASE1, PHASE2 (39 of 167 trials). The pattern suggests that attrition risk is not uniform across development stages, but the analysis is descriptive and should be validated within condition, sponsor, and trial-design subgroups before being used for risk decisions.

## 6. Most common normalized reasons trials stopped early

**Output:** `06_most_common_normalized_reasons_trials_stopped_early.csv`

**Takeaway:** Accrual / Recruitment is the most common normalized stop-reason bucket (133 of 330 records, 40.3%). However, Other / Unclear still contains 114 records (34.5%), so recruitment should be treated as a signal for follow-up rather than a complete explanation of trial failure; broader text matching or manual/NLP review would improve coverage.

## 7. Top 10 conditions studied (by number of trials)

**Output:** `07_top_10_conditions_studied_by_number_of_trials.csv`

**Takeaway:** Breast Cancer is the most frequently represented condition (1,550 trials), with several closely related condition labels also appearing in the top 10. This illustrates why condition normalization matters: raw registry labels can split one therapeutic area across synonyms and subtypes, which can distort apparent research concentration.

## 8. Completion rate by lead-sponsor class

**Output:** `08_completion_rate_by_lead_sponsor_class.csv`

**Takeaway:** Government and Academic / Research Network sponsors have the highest observed completion rates (58.5% and 58.2%, respectively). This is 8.4 percentage points above Industry (50.1%). For partnership-risk screening, this is a useful hypothesis to investigate within the same phase and condition, but it is not evidence that sponsor class causes completion outcomes.

## 9. Average trial duration (days) by phase, for completed trials only

**Output:** `09_average_trial_duration_days_by_phase_for_completed_trials_on.csv`

**Takeaway:** Among completed trials with complete dates, PHASE1, PHASE2 has the longest average duration at 2,154 days. Phase 3 averages 2,096 days versus 1,588 days in Phase 2. Duration comparisons are sensitive to study design and reporting conventions, and the 2020–2021 COVID-19 disruption is a plausible confounder for timelines in this period.

## 10. Top 10 countries running the most trial sites

**Output:** `10_top_10_countries_running_the_most_trial_sites.csv`

**Takeaway:** The United States has the largest geographic footprint in the sample (1,270 distinct trials with at least one listed site), followed by China (400). This can inform site-footprint and recruitment discussions, but registry site counts measure reported trial presence rather than total site capacity or enrollment quality.

## 11. Intervention type distribution (Drug vs Device vs Behavioral, etc.)

**Output:** `11_intervention_type_distribution_drug_vs_device_vs_behavioral_.csv`

**Takeaway:** DRUG interventions dominate the intervention rows (2,981 of 5,840, 51.0%). Because a single trial can contribute multiple intervention rows, this is an intervention-mix view rather than a trial-level percentage; it is useful for describing the therapeutic modality mix but not market share.

## 12. Sponsors with the highest early-stop rate (CTE + minimum 5 trials)

**Output:** `12_sponsors_with_the_highest_early_stop_rate_cte_minimum_5_tria.csv`

**Takeaway:** Among sponsors with at least five lead-sponsored trials, Wake Forest University Health Sciences has the highest observed early-stop rate (71.4%, 5/7). The minimum-trial threshold removes extreme one-trial rates, but the remaining samples are still small; any partnership or sponsor-risk decision should validate the result within phase, condition, and study design.
