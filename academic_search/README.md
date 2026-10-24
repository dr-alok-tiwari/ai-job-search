# Academic AI Job Search — personalised for Dr Alok Tiwari

This optional, **public-safe** layer supplements this repository's existing
Claude Code /scrape, /rank, /apply, and /interview workflows. It is built from
the **24 October 2026 CV** without publishing the full CV or personal contact data.

## Intended targets

- **India, highest priority:** IIM Information Systems / Analytics / Operations &
  Decision Sciences; IIT management, AI and analytics departments; IIIT AI/DS;
  strong research-led business schools; healthcare analytics / health informatics.
- **International:** assistant professor / lecturer / tenure-track AI, business
  analytics, information systems; applied medical AI and health informatics;
  research scientist or research fellow only when career progression is credible.
- **Review before pursuing:** Associate Professor (post-PhD years and publication
  norms vary), overseas roles with work-rights uncertainty and fixed-term postdocs.
- **Usually exclude:** PhD student, internships, research assistant and senior
  administrative leadership unless explicitly requested.

Current evidence: PhD from IIT (BHU), July 2023; faculty appointments
since March 2022 (not all post-PhD); four peer-reviewed journal papers
in supplied CV. Six pipeline manuscripts are *not* published papers.

## Fast start

~~~
python3 academic_search/search.py links
python3 academic_search/search.py rank --input academic_search/example_postings.json
python3 -m unittest discover -s tests -p 'test_academic_search.py'
~~~

The example contains only fictitious postings. **Never interpret it as
live opportunities.** The command writes a Markdown shortlist and machine-
readable JSON to academic_search/output/ (ignored by Git).

For real listings, export a CSV/JSON list with columns:
title, institution, location, country, url, posted_date, deadline,
description, requirements, eligibility, source.
Dates must be YYYY-MM-DD. Supply each original job-specific HTTPS vacancy URL,
not just a generic employer home page. Search links are discovery aids; a
search hit is **not** a verified open vacancy.

~~~
python3 academic_search/search.py rank --input /path/to/real_vacancies.csv
~~~

The score is transparent **heuristic triage**, not a trained ML model,
official university ranking, offer probability or eligibility determination.
Weights: role/level 35%, topical match 35%, location 20%, research career
trajectory 10%. Adjust geography and keywords in profile.json for new goals.
Human verification is mandatory for each vacancy's requirements, deadlines,
pay scale, citizenship and visa conditions.

## Integrating the existing AI agent

Clone this repository onto a **private working machine or private repository**.
If using Claude Code, open the repo and run:

- /scrape broad — finds job notices via installed portal skills and web search.
  This fork's scraper queries prioritise Indian academia and international
  research careers; Danish demo boards should be disabled or ignored.
- /rank — deeper AI assisted triage of scraped postings.
- /apply <original posting URL> — assessment and tailored application draft
  **only after manual fit verification**. Nothing is automatically sent.
- /interview — interview preparation once an application is tracked.

The independent Python tool consumes your exported listings; it does not
claim to scrape LinkedIn, IIM websites, EURAXESS or any board itself. Do not
mass-scrape sites against their terms. For real discovery also set official
alerts at EURAXESS (euraxess.ec.europa.eu/jobs/search), jobs.ac.uk,
academicpositions.com, higheredjobs.com and direct IIM/IIT faculty pages.

## Privacy

**This repository is public.** Never commit the original PDF CV,
phone/email, references, salary expectations, tracked applications, interview
notes, or outputs. Put private evidence under the already-ignored documents/cv/
directory on your own clone. The profile deliberately includes public
professional search attributes only. GitHub pull request branches in a public
repository are also public.

A date absent from a vacancy remains unknown. A search result or heuristic
match is not proof the role is open or that its formal eligibility criteria
are satisfied.
