"""
load_data.py
------------
Parses data/raw_studies.json (from fetch_data.py, ClinicalTrials.gov API v2
format) and loads it into a SQLite database built from sql/schema.sql.

Usage:
    python load_data.py --input ../data/raw_studies.json --db ../data/clinical_trials.db
"""

import argparse
import json
import sqlite3
from pathlib import Path


def get_nested(d, *keys, default=None):
    """Safely walk a nested dict, e.g. get_nested(study, 'protocolSection', 'statusModule', 'overallStatus')."""
    cur = d
    for k in keys:
        if not isinstance(cur, dict):
            return default
        cur = cur.get(k)
        if cur is None:
            return default
    return cur


def build_db(db_path: str, schema_path: str):
    conn = sqlite3.connect(db_path)
    with open(schema_path) as f:
        conn.executescript(f.read())
    conn.commit()
    return conn


def normalize_phase(phases):
    """Return deliberately distinct labels for missing vs not-applicable phase."""
    if phases is None:
        return "Phase Not Reported"
    if isinstance(phases, str):
        phases = [phases]
    cleaned = [str(p).strip() for p in phases if str(p).strip()]
    if not cleaned:
        return "Phase Not Reported"
    if any(p.upper() in {"NA", "N/A", "NOT APPLICABLE"} for p in cleaned):
        return "Phase Not Applicable"
    return ", ".join(cleaned)


def categorize_why_stopped(reason):
    """Bucket free-text stop reasons into consistent, analysis-friendly categories."""
    if not reason or not str(reason).strip():
        return None
    text = str(reason).strip().lower()
    buckets = [
        ("Accrual / Recruitment", ["recruit", "enroll", "accrual", "accrue", "patient population", "slow accrual"]),
        ("Funding / Resources", ["funding", "fund", "financial", "budget", "resource"]),
        ("Safety", ["safety", "adverse", "toxicity", "side effect", "risk"]),
        ("Efficacy", ["efficacy", "futility", "ineffective", "lack of benefit", "lack of efficacy", "no benefit"]),
        ("PI / Staffing", ["principal investigator", "pi ", "staff", "staffing", "investigator", "personnel"]),
        ("Business Decision", ["business", "sponsor decision", "strategic", "company decision", "development decision", "commercial", "priority"]),
    ]
    for category, keywords in buckets:
        if any(k in text for k in keywords):
            return category
    return "Other / Unclear"


def load_studies(conn: sqlite3.Connection, studies: list):
    cur = conn.cursor()

    n_studies = n_sponsors = n_conditions = n_interventions = n_locations = 0

    for study in studies:
        protocol = study.get("protocolSection", {})

        nct_id = get_nested(protocol, "identificationModule", "nctId")
        if not nct_id:
            continue  # skip malformed records

        brief_title = get_nested(protocol, "identificationModule", "briefTitle")
        overall_status = get_nested(protocol, "statusModule", "overallStatus")
        start_date = get_nested(protocol, "statusModule", "startDateStruct", "date")
        primary_completion = get_nested(protocol, "statusModule", "primaryCompletionDateStruct", "date")
        completion_date = get_nested(protocol, "statusModule", "completionDateStruct", "date")
        why_stopped = get_nested(protocol, "statusModule", "whyStopped")
        why_stopped_category = categorize_why_stopped(why_stopped)

        phases = get_nested(protocol, "designModule", "phases", default=None)
        phase = normalize_phase(phases)

        # A trial ID can appear more than once in an input file. Remove all
        # child rows first so repeated loads cannot accumulate duplicate
        # sponsors, conditions, interventions, or locations.
        for table in ("sponsors", "conditions", "interventions", "locations"):
            cur.execute(f"DELETE FROM {table} WHERE nct_id = ?", (nct_id,))
        study_type = get_nested(protocol, "designModule", "studyType")
        enrollment_count = get_nested(protocol, "designModule", "enrollmentInfo", "count")
        enrollment_type = get_nested(protocol, "designModule", "enrollmentInfo", "type")

        cur.execute(
            """INSERT OR REPLACE INTO studies
               (nct_id, brief_title, overall_status, phase, study_type, start_date,
                primary_completion_date, completion_date, enrollment_count, enrollment_type, why_stopped, why_stopped_category)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (nct_id, brief_title, overall_status, phase, study_type, start_date,
             primary_completion, completion_date, enrollment_count, enrollment_type, why_stopped, why_stopped_category),
        )
        n_studies += 1

        # Sponsors (lead + collaborators)
        lead_name = get_nested(protocol, "sponsorCollaboratorsModule", "leadSponsor", "name")
        lead_class = get_nested(protocol, "sponsorCollaboratorsModule", "leadSponsor", "class")
        if lead_name:
            cur.execute(
                "INSERT INTO sponsors (nct_id, name, agency_class, sponsor_role) VALUES (?, ?, ?, ?)",
                (nct_id, lead_name, lead_class, "lead_sponsor"),
            )
            n_sponsors += 1

        for collab in get_nested(protocol, "sponsorCollaboratorsModule", "collaborators", default=[]):
            cur.execute(
                "INSERT INTO sponsors (nct_id, name, agency_class, sponsor_role) VALUES (?, ?, ?, ?)",
                (nct_id, collab.get("name"), collab.get("class"), "collaborator"),
            )
            n_sponsors += 1

        # Conditions
        for cond in get_nested(protocol, "conditionsModule", "conditions", default=[]):
            cur.execute("INSERT INTO conditions (nct_id, condition_name) VALUES (?, ?)", (nct_id, cond))
            n_conditions += 1

        # Interventions
        for interv in get_nested(protocol, "armsInterventionsModule", "interventions", default=[]):
            cur.execute(
                "INSERT INTO interventions (nct_id, intervention_type, intervention_name) VALUES (?, ?, ?)",
                (nct_id, interv.get("type"), interv.get("name")),
            )
            n_interventions += 1

        # Locations
        for loc in get_nested(protocol, "contactsLocationsModule", "locations", default=[]):
            cur.execute(
                "INSERT INTO locations (nct_id, facility, city, state, country) VALUES (?, ?, ?, ?, ?)",
                (nct_id, loc.get("facility"), loc.get("city"), loc.get("state"), loc.get("country")),
            )
            n_locations += 1

    conn.commit()
    print(f"Loaded: {n_studies} studies, {n_sponsors} sponsor rows, {n_conditions} condition rows, "
          f"{n_interventions} intervention rows, {n_locations} location rows.")


def main():
    parser = argparse.ArgumentParser(description="Load raw trial JSON into SQLite")
    parser.add_argument("--input", default="../data/raw_studies.json")
    parser.add_argument("--db", default="../data/clinical_trials.db")
    parser.add_argument("--schema", default="../sql/schema.sql")
    args = parser.parse_args()

    with open(args.input) as f:
        studies = json.load(f)

    Path(args.db).unlink(missing_ok=True)  # start fresh each run
    conn = build_db(args.db, args.schema)
    load_studies(conn, studies)
    conn.close()


if __name__ == "__main__":
    main()
