# GrantLens(v1)

**From a spreadsheet of grant prospects to a defensible research plan.**

GrantLens is a Python analytics application for understanding a funding pipeline, identifying unreliable data, and prioritizing follow-up. Built as a portfolio project by V. Bryant, it extends grant prospect exploration into interactive decision support.

## Business questions

- Where is the pipeline concentrated by stage and funding type?
- Which active opportunities require attention within 30 days?
- How much recorded funding potential is supported by known amounts?
- Which data gaps prevent confident prioritization?

## Run locally

Requires Python 3.13. From this project folder:

```bash
python -m venv .venv
# Windows PowerShell:
.venv\Scripts\Activate.ps1
# macOS/Linux: source .venv/bin/activate
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

The demo loads automatically. The fixed demo analysis date is October 29, 2026; change it in the sidebar to explore deadline scenarios. Your own upload defaults to today's date.

```bash
python -m unittest discover -s tests -v
```

## A reproducible demo story

The 14-row fictional dataset deliberately contains a duplicated opportunity, an unknown amount and deadline, and an invalid fit score. With all filters selected and the default date:

| Measure | Result |
|---|---:|
| Active prospects after identity/status exclusions | 10 |
| Known active potential | $475,000 |
| Active deadlines within 30 days, inclusive | 4 |
| Active amount coverage | 90% |
| Records excluded for duplicate identities | 2 |

**Decision:** review the four near-term opportunities, resolve the past-deadline record, and verify the unknown deadline before allocating a research sprint. These are observations about fictional data, not claims about real grant availability.

## Import contract

Use `data/demo.csv` as a template. Headers are exact and case-sensitive; extra columns are ignored.

| Column | Meaning |
|---|---|
| funder, program | Nonempty opportunity identity; whitespace is trimmed |
| type | Funding category used for filters and aggregation |
| status | Research, Qualified, Preparing, Submitted, Awarded, or Declined |
| amount | Nonnegative numeric opportunity amount in USD; blank means unknown |
| fit_score | Analyst assessment from 0 to 100; blank means unknown |
| deadline | ISO date `YYYY-MM-DD`; blank means timing unknown |

Normalize currency, award ranges, and free-text deadlines before upload. The application does not guess monetary ranges or eligibility. Upload limit: 5 MB. Files are processed in app memory and are not intentionally saved by the application. A hosted app's operator processes uploads; use fictional or public information on public deployments.

## Analytical methodology

1. Validate schema and normalize whitespace; flag missing identities, unknown statuses, invalid numbers and dates.
2. Exclude every repeated funder/program pair from metrics until resolved. Identity matching is case-sensitive. Individual numeric/date gaps remain visible rather than excluding the whole opportunity.
3. Define active prospects as Research, Qualified, Preparing, or Submitted. Past-deadline records remain active until their status is resolved and are flagged for review.
4. Sum known active amounts. Missing amounts remain unknown. Potential is neither expected revenue nor an award forecast; opportunities may overlap.
5. Rank active opportunities with a current or unknown deadline using `0.8 × fit + 0.2 × urgency`. Urgency is `100 × (1 − days_left / 90)`, bounded to 0–100. Unknown timing earns zero urgency; missing fit remains unranked. Closed and past-deadline opportunities remain unranked.
6. Execute the displayed SQL in an in-memory SQLite database after filtering. Quality findings always describe the full file.

The score is a transparent heuristic for research triage. It does not estimate award probability, verify sources, or establish eligibility. Weight sensitivity and analyst rubric calibration are future work.

## Architecture and portfolio skills

`CSV → pandas validation → filtered analytical records → SQLite summaries → Streamlit / Plotly → CSV exports`

- `analytics.py`: validation, scoring, SQL aggregation, spreadsheet-safe exports.
- `app.py`: KPI cards, interactive charts, action queue, quality findings, and methodology.
- `tests/`: analytical edge cases and application smoke/filter tests.
- `.github/workflows/checks.yml`: automated checks on pushes and pull requests.

Demonstrates Python, pandas, SQL aggregation, data quality controls, interactive visualization, business interpretation, and software testing. This version uses a defined import schema rather than automatically mapping the earlier grant research spreadsheet.

## Publish on GitHub

Create an empty repository named `grantlens` under your account, then run from this folder:

```bash
git init -b main
git add .
git commit -m "Build GrantLens analytics application"
git remote add origin https://github.com/vb-datagh/grantlens.git
git push -u origin main
```

Suggested description: **Interactive grant pipeline analytics with Python, SQL, data quality checks, and transparent prioritization.**

Suggested topics: `python`, `data-analytics`, `sql`, `streamlit`, `data-quality`, `portfolio-project`.

For a hosted demo, select this repository and `app.py` in Streamlit Community Cloud. Include only the fictional demo data. Add the deployed URL and a screenshot to this README after deployment.

## Next milestones

- Map existing grant prospect spreadsheet columns with explicit review of ranges and deadlines.
- Add source URLs and verification dates.
- Compare alternative scoring weights and document a fit rubric.
- Add application outcomes and reporting over time when longitudinal data exists.

## Framework references

[Streamlit uploads](https://docs.streamlit.io/develop/api-reference/widgets/st.file_uploader) · [Streamlit application tests](https://docs.streamlit.io/develop/api-reference/app-testing)
