# job-tracker

A small agent that reads job-application emails and logs them to Notion.

**Pipeline (target):** apply from Proton → Proton auto-forwards job mail to a
Gmail "job-hunt" inbox → this agent reads Gmail → classifies → writes to Notion.

This repo is currently at **Phase 0**: prove Gmail and Notion connect. No
classification logic yet.

---

## One-time setup

You should already have, from the setup steps:

- `client_secret.json` — Gmail OAuth client (from Google Cloud Console)
- A Notion token (`ntn_…`)
- Your Notion database id (32-char string from the DB url)

### 1. Drop in your Gmail secret
Put `client_secret.json` in the project root (this folder). It's gitignored.

### 2. Create your `.env`
```bash
cp .env.example .env
```
Then open `.env` and paste in your real `NOTION_TOKEN` and `NOTION_DATABASE_ID`.

### 3. Install dependencies
```bash
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

---

## Run Phase 0
```bash
python main.py
```

- The **first** run opens a browser asking you to pick your job-hunt Gmail
  account and approve access. After you approve, a `token.json` is saved so
  future runs skip the browser.
- If you get an "access blocked" screen, make sure your Gmail address is added
  as a **Test user** on the Google Auth Platform consent screen.

### What success looks like
A new row appears in your Notion database titled **"TEST ROW — delete me"**,
with the subject + preview of your latest inbox email in the Notes column.
Delete the row afterward — it's just a connectivity check.

---

## Files
| file | what it does |
|------|--------------|
| `config.py` | loads your secrets + settings in one place |
| `gmail_client.py` | Gmail auth + reading the latest message |
| `notion_writer.py` | writes a row to Notion via raw REST |
| `main.py` | Phase 0 glue tying the two together |

## Common errors
- **`Could not find database`** → your integration isn't connected to the DB
  (open the DB → ••• → Connections → add it), or the database id is wrong.
- **Notion property errors** → a column name in `notion_writer.py` doesn't
  match your DB exactly (case-sensitive: `Company`, `Role`, `Status`, …).

---

## Phase 1 — automatic tracking (current)

`main.py` now scans your inbox and records job mail automatically:

- **Applied** (e.g. "thank you for applying") → creates a new row.
- **Rejected** (e.g. "unfortunately…") → updates the matching `Applied` row,
  or creates a `Rejected` row if no match is found.
- **Ignore** (newsletters, job alerts, anything unclear) → skipped.

Emails it acts on get a Gmail label called **`tracked`**, so re-running never
double-counts them. Ignored mail is left unlabeled.

### Recommended first run: dry run
Forward a few real application + rejection emails into the inbox, then:
```bash
# in .env, set:  DRY_RUN=true
python main.py
```
This prints how each email *would* be classified without writing anything.
Eyeball the results, then set `DRY_RUN=false` and run again for real.

### Tuning
- The keyword/domain rules live in `classifier.py` — add senders to
  `ATS_DOMAINS` or phrases to `APPLIED_PHRASES` / `REJECTION_PHRASES` as you
  spot misses.
- `LOOKBACK_DAYS` in `.env` controls how far back it scans.

### Forwarded mail
This is built to handle the Proton → Gmail forwarding flow. When an email is a
forward, the real sender/company is parsed out of the quoted body (the
"Forwarded message / From:" block), so the company is recorded correctly even
though the outer sender is you. No AI, no cost.

### Known limits
- **Rules miss unusual phrasing.** Oddly-worded emails are ignored rather than
  guessed at. For standard ATS mail (Greenhouse, Lever, Workday, Ashby, …) this
  is rarely an issue. If you spot a miss, add a phrase to `APPLIED_PHRASES` /
  `REJECTION_PHRASES` or a sender to `ATS_DOMAINS` in `classifier.py`.
- **Rejection→application matching is fuzzy.** It matches on company name only,
  so occasionally a rejection makes a fresh row instead of updating the original.

Everything here runs at **zero cost** — Gmail API, Notion API, and (next step)
GitHub Actions are all free.
