# GitHub Master Monitor

This repository automates project management for multiple GitHub repos. It ensures every repo has a **7-step project board** and maintains a **Master Project dashboard** to track progress across all repos.

---

## Features

- Auto-creates a 7-step project board for each repo if missing:
  1. MVP / Idea
  2. PRD / Defined
  3. Dev / Implementation
  4. Code Review / QA Prep
  5. CI/CD / Integration
  6. Testing / Verification
  7. Release / Done
- Calculates progress per repo (`% done`)
- Updates Master Project dashboard with cards including clickable repo project links
- Fully automated via GitHub Actions (weekly or manual trigger)
- **Automatically detects all repositories** under your GitHub account; no manual list required

---

## Setup

1. **Create the Master Project**

   - In this repo (`github-master-monitor`)
   - Add at least one column: `Repo Overview`
   - Optionally: `Blocked / Attention`, `Completed / Archived`

2. **Add GitHub Secrets**

   - `GITHUB_TOKEN` → Personal Access Token with `repo` and `project` scopes
   - `MASTER_PROJECT_ID` → ID of the Master Project
   - `GITHUB_REPO` → `"gianpy99/github-master-monitor"`

3. **Push workflow**

   - `.github/workflows/manage_projects.yml` is configured to run:
     - Weekly on Mondays at 10:00 UTC
     - Or manually via "Run workflow"

---

## Usage

- **First Run**

  - Creates missing repo projects
  - Generates `repo_project_mapping.json`
  - Populates Master Project cards

- **Subsequent Runs**

  - Updates progress automatically
  - Adds new cards for new repos
  - Updates card titles with `% done` and links

---

## Adding New Repos

- Just create a new repo under your account; the script detects it automatically during the next run.  
- No manual configuration is needed.

---

## Notes

- Cards include the repo project link as a comment for quick navigation
- Keep `repo_project_mapping.json` under version control if you want to track mapping changes
- Optional columns in Master Project are for manual management, not used by automation

---

## Future Extensions

- Track number of issues per column in card comments
- Extend progress metrics beyond `% done`
- Multiple Master Projects for different project categories
