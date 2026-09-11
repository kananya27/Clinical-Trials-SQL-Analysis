-- ============================================================
-- Clinical Trials SQL Analysis — Research Questions
-- ============================================================

-- 1. How many trials are in each phase?
SELECT phase, COUNT(*) AS trial_count
FROM studies
GROUP BY phase
ORDER BY trial_count DESC;


-- 2. Top sponsors within each phase (window function)
WITH sponsor_phase AS (
    SELECT st.phase, s.name AS sponsor_name, s.agency_class, COUNT(*) AS trials_led
    FROM studies st
    JOIN sponsors s ON s.nct_id = st.nct_id AND s.sponsor_role = 'lead_sponsor'
    GROUP BY st.phase, s.name, s.agency_class
), ranked AS (
    SELECT *, RANK() OVER (PARTITION BY phase ORDER BY trials_led DESC) AS sponsor_rank
    FROM sponsor_phase
)
SELECT phase, sponsor_rank, sponsor_name, agency_class, trials_led
FROM ranked
WHERE sponsor_rank <= 3
ORDER BY phase, sponsor_rank, sponsor_name;


-- 3. Average enrollment size by phase
SELECT phase,
       ROUND(AVG(enrollment_count), 0) AS avg_enrollment,
       COUNT(*) AS trial_count
FROM studies
WHERE enrollment_count IS NOT NULL
GROUP BY phase
ORDER BY avg_enrollment DESC;


-- 4. Trend: number of trials started per year
SELECT SUBSTR(start_date, 1, 4) AS start_year, COUNT(*) AS trials_started
FROM studies
WHERE start_date IS NOT NULL
GROUP BY start_year
ORDER BY start_year;


-- 5. Attrition: % of trials terminated/withdrawn/suspended, by phase
SELECT phase,
       COUNT(*) AS total_trials,
       SUM(CASE WHEN overall_status IN ('TERMINATED', 'WITHDRAWN', 'SUSPENDED') THEN 1 ELSE 0 END) AS stopped_early,
       ROUND(100.0 * SUM(CASE WHEN overall_status IN ('TERMINATED', 'WITHDRAWN', 'SUSPENDED') THEN 1 ELSE 0 END)
             / COUNT(*), 1) AS pct_stopped_early
FROM studies
GROUP BY phase
ORDER BY pct_stopped_early DESC;


-- 6. Most common normalized reasons trials stopped early
SELECT why_stopped_category, COUNT(*) AS occurrences
FROM studies
WHERE why_stopped_category IS NOT NULL
GROUP BY why_stopped_category
ORDER BY occurrences DESC;


-- 7. Top 10 conditions studied (by number of trials)
SELECT condition_name, COUNT(DISTINCT nct_id) AS trial_count
FROM conditions
GROUP BY condition_name
ORDER BY trial_count DESC
LIMIT 10;


-- 8. Completion rate by lead-sponsor class
SELECT
    CASE
        WHEN UPPER(COALESCE(s.agency_class, '')) = 'INDUSTRY' THEN 'Industry'
        WHEN UPPER(COALESCE(s.agency_class, '')) IN ('NIH', 'FED', 'OTHER_GOV') THEN 'Government'
        WHEN UPPER(COALESCE(s.agency_class, '')) IN ('ACADEMIC', 'NETWORK') THEN 'Academic / Research Network'
        ELSE 'Other / Unknown'
    END AS sponsor_type,
    COUNT(*) AS total_trials,
    SUM(CASE WHEN st.overall_status = 'COMPLETED' THEN 1 ELSE 0 END) AS completed_trials,
    ROUND(100.0 * SUM(CASE WHEN st.overall_status = 'COMPLETED' THEN 1 ELSE 0 END) / COUNT(*), 1) AS pct_completed
FROM studies st
JOIN sponsors s ON s.nct_id = st.nct_id AND s.sponsor_role = 'lead_sponsor'
GROUP BY sponsor_type
ORDER BY pct_completed DESC;


-- 9. Average trial duration (days) by phase, for completed trials only
SELECT phase,
       ROUND(AVG(JULIANDAY(completion_date) - JULIANDAY(start_date)), 0) AS avg_duration_days,
       COUNT(*) AS trial_count
FROM studies
WHERE overall_status = 'COMPLETED'
  AND start_date IS NOT NULL AND completion_date IS NOT NULL
  AND LENGTH(start_date) = 10 AND LENGTH(completion_date) = 10
GROUP BY phase
ORDER BY avg_duration_days DESC;


-- 10. Top 10 countries running the most trial sites
SELECT country, COUNT(DISTINCT nct_id) AS trial_count
FROM locations
WHERE country IS NOT NULL
GROUP BY country
ORDER BY trial_count DESC
LIMIT 10;


-- 11. Intervention type distribution (Drug vs Device vs Behavioral, etc.)
SELECT intervention_type, COUNT(*) AS count
FROM interventions
GROUP BY intervention_type
ORDER BY count DESC;


-- 12. Sponsors with the highest early-stop rate (CTE + minimum 5 trials)
WITH sponsor_stats AS (
    SELECT s.name AS sponsor_name,
           COUNT(*) AS total_trials,
           SUM(CASE WHEN st.overall_status IN ('TERMINATED', 'WITHDRAWN', 'SUSPENDED') THEN 1 ELSE 0 END) AS stopped_early
    FROM studies st
    JOIN sponsors s ON s.nct_id = st.nct_id AND s.sponsor_role = 'lead_sponsor'
    GROUP BY s.name
    HAVING COUNT(*) >= 5
)
SELECT sponsor_name,
       total_trials,
       stopped_early,
       ROUND(100.0 * stopped_early / total_trials, 1) AS pct_stopped_early
FROM sponsor_stats
ORDER BY pct_stopped_early DESC, total_trials DESC
LIMIT 10;
