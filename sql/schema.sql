-- ============================================================
-- Clinical Trials Analysis DB — Schema
-- Source: ClinicalTrials.gov API v2 (https://clinicaltrials.gov/api/v2/studies)
-- ============================================================

DROP TABLE IF EXISTS locations;
DROP TABLE IF EXISTS interventions;
DROP TABLE IF EXISTS conditions;
DROP TABLE IF EXISTS sponsors;
DROP TABLE IF EXISTS studies;

-- One row per clinical trial (the "fact" table)
CREATE TABLE studies (
    nct_id                  TEXT PRIMARY KEY,       -- unique trial identifier, e.g. NCT01234567
    brief_title             TEXT,
    overall_status          TEXT,                   -- Recruiting, Completed, Terminated, Withdrawn, ...
    phase                   TEXT,                   -- Phase 1, Phase 2, Phase 3, Phase 4, N/A
    study_type              TEXT,                   -- Interventional, Observational
    start_date              TEXT,                   -- ISO date, may be partial (YYYY-MM)
    primary_completion_date TEXT,
    completion_date         TEXT,
    enrollment_count        INTEGER,
    enrollment_type         TEXT,                   -- Actual / Estimated
    why_stopped              TEXT,                   -- original free text
    why_stopped_category     TEXT                    -- normalized analysis bucket
);

-- One row per sponsor per trial (lead sponsor + collaborators)
CREATE TABLE sponsors (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    nct_id       TEXT REFERENCES studies(nct_id),
    name         TEXT,
    agency_class TEXT,          -- Industry, NIH, Academic, U.S. Fed, Other, ...
    sponsor_role TEXT           -- lead_sponsor / collaborator
);

-- One row per condition studied per trial (a trial can target multiple conditions)
CREATE TABLE conditions (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    nct_id         TEXT REFERENCES studies(nct_id),
    condition_name TEXT
);

-- One row per intervention arm per trial
CREATE TABLE interventions (
    id                 INTEGER PRIMARY KEY AUTOINCREMENT,
    nct_id             TEXT REFERENCES studies(nct_id),
    intervention_type  TEXT,     -- Drug, Device, Behavioral, Biological, Procedure, ...
    intervention_name  TEXT
);

-- One row per trial site
CREATE TABLE locations (
    id       INTEGER PRIMARY KEY AUTOINCREMENT,
    nct_id   TEXT REFERENCES studies(nct_id),
    facility TEXT,
    city     TEXT,
    state    TEXT,
    country  TEXT
);

-- Helpful indexes for the analysis queries
CREATE INDEX idx_sponsors_nct        ON sponsors(nct_id);
CREATE INDEX idx_conditions_nct      ON conditions(nct_id);
CREATE INDEX idx_interventions_nct   ON interventions(nct_id);
CREATE INDEX idx_locations_nct       ON locations(nct_id);
CREATE INDEX idx_studies_phase       ON studies(phase);
CREATE INDEX idx_studies_status      ON studies(overall_status);
