"""
fetch_data.py
-------------
Pulls clinical trial records from the public ClinicalTrials.gov API (v2)
and saves the raw JSON to data/raw_studies.json.

No API key needed - it's a free, open API.
Docs: https://clinicaltrials.gov/data-api/api

Usage:
    python fetch_data.py --condition "breast cancer" --max-studies 2000
    python fetch_data.py --condition "diabetes" --max-studies 5000

Run this on your own machine (not in a sandboxed/offline environment) -
it needs internet access to clinicaltrials.gov.
"""

import argparse
import json
import time
import requests

API_URL = "https://clinicaltrials.gov/api/v2/studies"

# Fields we actually need - keeping the payload small and the pipeline fast.
FIELDS = [
    "NCTId",
    "BriefTitle",
    "OverallStatus",
    "Phase",
    "StudyType",
    "StartDate",
    "PrimaryCompletionDate",
    "CompletionDate",
    "EnrollmentCount",
    "EnrollmentType",
    "WhyStopped",
    "LeadSponsorName",
    "LeadSponsorClass",
    "CollaboratorName",
    "CollaboratorClass",
    "Condition",
    "InterventionType",
    "InterventionName",
    "LocationFacility",
    "LocationCity",
    "LocationState",
    "LocationCountry",
]


def fetch_studies(condition: str, max_studies: int, page_size: int = 100):
    """Page through the API until max_studies is hit or results run out."""
    all_studies = []
    params = {
        "query.cond": condition,
        "fields": ",".join(FIELDS),
        "pageSize": page_size,
        "format": "json",
    }
    next_token = None

    while len(all_studies) < max_studies:
        if next_token:
            params["pageToken"] = next_token

        resp = requests.get(API_URL, params=params, timeout=30)
        resp.raise_for_status()
        payload = resp.json()

        studies = payload.get("studies", [])
        all_studies.extend(studies)
        print(f"Fetched {len(all_studies)} studies so far...")

        next_token = payload.get("nextPageToken")
        if not next_token or not studies:
            break

        time.sleep(0.3)  # be polite to the API

    return all_studies[:max_studies]


def main():
    parser = argparse.ArgumentParser(description="Fetch trials from ClinicalTrials.gov")
    parser.add_argument("--condition", required=True, help='e.g. "breast cancer", "type 2 diabetes"')
    parser.add_argument("--max-studies", type=int, default=2000)
    parser.add_argument("--out", default="../data/raw_studies.json")
    args = parser.parse_args()

    studies = fetch_studies(args.condition, args.max_studies)

    with open(args.out, "w") as f:
        json.dump(studies, f)

    print(f"Saved {len(studies)} studies to {args.out}")


if __name__ == "__main__":
    main()
