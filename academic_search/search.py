"""Public-safe academic job discovery links and conservative job fit triage.

No crawler, paid API, CV upload, or auto-application is included. Inputs are
user-supplied job listings in CSV/JSON format and remain on the local machine.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
from datetime import date
from pathlib import Path
from urllib.parse import quote, quote_plus, urlparse

PROFILE = Path(__file__).with_name("profile.json")

def load_profile(path: Path = PROFILE) -> dict:
    with path.open(encoding="utf-8") as stream:
        return json.load(stream)

def contains(text: str, term: str) -> bool:
    return re.search(r"(?<!\w)" + re.escape(term) + r"(?!\w)", text, re.I) is not None

def terms_found(text: str, terms: list[str]) -> list[str]:
    return [term for term in terms if contains(text, term)]

def load_jobs(path: Path) -> list[dict]:
    if path.suffix.lower() == ".csv":
        with path.open(encoding="utf-8-sig", newline="") as stream:
            return list(csv.DictReader(stream))
    if path.suffix.lower() == ".json":
        with path.open(encoding="utf-8") as stream:
            raw = json.load(stream)
        jobs = raw.get("jobs", []) if isinstance(raw, dict) else raw
        if not isinstance(jobs, list) or not all(isinstance(j, dict) for j in jobs):
            raise ValueError("JSON input must be a list of job objects or {jobs: [...]}.")
        return jobs
    raise ValueError("Only CSV and JSON input files are supported.")

def valid_url(value: str) -> bool:
    parts = urlparse(value)
    return parts.scheme == "https" and bool(parts.netloc)

def score_job(job: dict, profile: dict, today: date | None = None) -> dict:
    today = today or date.today()
    title = str(job.get("title") or "").strip()
    institution = str(job.get("institution") or job.get("company") or "").strip()
    location = str(job.get("location") or "").strip()
    url = str(job.get("url") or "").strip()
    description = " ".join(str(job.get(k) or "") for k in
                           ("description", "requirements", "eligibility"))
    body = title + " " + description
    flags = []
    if not title or not institution or not valid_url(url):
        flags.append("Incomplete title/institution or missing HTTPS posting URL: verify source")
    deadline = str(job.get("deadline") or "").strip()
    if deadline:
        try:
            deadline_date = date.fromisoformat(deadline)
        except ValueError:
            flags.append("Deadline is not verified YYYY-MM-DD; check official page")
            deadline_date = None
    else:
        deadline_date = None
        flags.append("Application deadline unknown; verify official posting")
    lower_title = title.lower()
    is_trainee = bool(re.search(
        r"\b(phd student|doctoral student|intern(ship)?|graduate assistant|research assistant)\b",
        lower_title))
    is_very_senior = bool(re.search(r"\b(dean|director|full professor|chair professor)\b", lower_title))
    is_assistant = bool(re.search(r"\b(assistant professor|tenure.track|lecturer|faculty)\b", lower_title))
    is_associate = "associate professor" in lower_title
    is_researcher = bool(re.search(r"\b(research scientist|research fellow|postdoc|postdoctoral|post.doctoral)\b", lower_title))
    level = 95 if is_assistant else 65 if is_associate else 70 if is_researcher else 25
    if is_trainee or is_very_senior:
        level = 5
    research = terms_found(body, profile["research_keywords"])
    teaching = terms_found(body, profile["teaching_keywords"])
    subject_score = min(100, 20 + 16 * len(research) + 7 * len(teaching))
    loc_text = location.casefold()
    if any(w in loc_text for w in profile["primary_location_keywords"]):
        location_score = 100
    elif any(w in loc_text for w in profile["secondary_location_keywords"]):
        location_score = 75
    elif contains(loc_text, "india"):
        location_score = 68
    elif loc_text:
        location_score = 58
        flags.append("International/other-location move: work authorization and relocation unverified")
    else:
        location_score = 45
        flags.append("Location unknown")
    # Professional progression heuristic, not an institutional ranking.
    trajectory = 85 if is_assistant else 70 if is_researcher else 60 if is_associate else 25
    score = round(0.35 * level + 0.35 * subject_score
                  + 0.20 * location_score + 0.10 * trajectory)
    status = "review"
    if deadline_date and deadline_date < today:
        status = "expired"
        score = 0
    elif is_trainee:
        status = "not_target"
    elif is_very_senior:
        status = "stretch"
    elif is_associate:
        flags.append("Associate Professor: verify mandatory post-PhD years and publication criteria")
        status = "eligibility_review"
    if re.search(r"\b(citizenship|security clearance|permanent resident|visa sponsorship)\b",
                 description, re.I):
        flags.append("Citizenship/work-rights condition present: read official eligibility text")
        if status == "review":
            status = "eligibility_review"
    # Never infer eligibility from a keyword alone; verify wording on official advert.
    years = re.search(
        r"(?:minimum|at least|requires?)\s+(\d+)\s+(?:years?|yrs?)\s+"
        r"(?:of\s+)?(?:post[\s-]*phd|after\s+(?:the\s+)?phd)", description, re.I)
    if years and int(years.group(1)) > 3:
        flags.append("Explicit post-PhD experience criterion may exceed current CV; verify exact cut-off")
        if status == "review":
            status = "eligibility_review"
    if not description.strip():
        flags.append("No job description provided: provisional fit only")
    return {
        "title": title, "institution": institution, "location": location,
        "country": str(job.get("country") or ""), "url": url,
        "posted_date": str(job.get("posted_date") or ""),
        "deadline": deadline, "score": score, "status": status,
        "research_matches": research, "teaching_matches": teaching,
        "flags": flags, "source": str(job.get("source") or "user supplied"),
        "score_basis": "heuristic triage from supplied text, not confirmed eligibility"
    }

def rank_jobs(jobs: list[dict], profile: dict, today: date | None = None) -> list[dict]:
    seen = set()
    ranked = []
    for job in jobs:
        row = score_job(job, profile, today)
        key = row["url"].lower() if row["url"] else (
            row["institution"].casefold(), row["title"].casefold())
        if key in seen:
            continue
        seen.add(key)
        ranked.append(row)
    return sorted(ranked, key=lambda j: (
        j["status"] == "expired", j["status"] == "not_target",
        -j["score"], j["deadline"] or "9999-12-31"))

def markdown_report(jobs: list[dict], asof: date | None = None) -> str:
    asof = asof or date.today()
    out = [
        "# Academic AI Job Search — Candidate Shortlist",
        "",
        "Generated: " + asof.isoformat(),
        "",
        "> Provisional text-matching triage only. Confirm deadlines, minimum "
        "qualifications, nationality/visa rules and vacancy status on each official page.",
        "",
        "| Score | Status | Role | Institution | Location | Deadline |",
        "|---:|---|---|---|---|---|"
    ]
    for job in jobs:
        def cell(value: object) -> str:
            return (str(value or "Unknown").replace("|", r"\|").replace("\n", " ")
                    .replace("[", r"\[").replace("]", r"\]"))
        role = ("[" + cell(job["title"]) + "](" +
                quote(job["url"], safe=":/?&=%#@+-_.~") + ")"
                if valid_url(job["url"]) else cell(job["title"]))
        out.append("| " + " | ".join([
            str(job["score"]), cell(job["status"]), role,
            cell(job["institution"]), cell(job["location"]), cell(job["deadline"])
        ]) + " |")
    out.extend(["", "## Evidence and unresolved checks", ""])
    for i, job in enumerate(jobs, 1):
        notes = job["flags"] or ["Verify all requirements on official vacancy page"]
        out.append(str(i) + ". **" + job["institution"] + " — " +
                   job["title"] + "**: " +
                   ("Topics: " + ", ".join(job["research_matches"]) + ". "
                    if job["research_matches"] else "No matched research keywords. ") +
                   "Checks: " + "; ".join(notes))
    return "\n".join(out) + "\n"

def main() -> int:
    parser = argparse.ArgumentParser(description="Public-safe faculty AI job search helper")
    parser.add_argument("--profile", type=Path, default=PROFILE)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("links", help="Print pre-built searches for academic job boards")
    rank = commands.add_parser("rank", help="Score an exported CSV/JSON vacancy list locally")
    rank.add_argument("--input", type=Path, required=True)
    rank.add_argument("--output", type=Path, default=Path("academic_search/output/shortlist.md"))
    args = parser.parse_args()
    profile = load_profile(args.profile)
    if args.command == "links":
        for term in profile["search_queries"]:
            print(term["label"] + ": https://www.google.com/search?q=" +
                  quote_plus(term["query"]))
        return 0
    ranked = rank_jobs(load_jobs(args.input), profile)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(markdown_report(ranked), encoding="utf-8")
    args.output.with_suffix(".json").write_text(
        json.dumps(ranked, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("Scored " + str(len(ranked)) + " unique listings. Report: " + str(args.output))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
