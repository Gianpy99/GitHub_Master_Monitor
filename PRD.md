## Purpose

Automate project management across multiple GitHub repos, ensuring consistent project boards and a centralized Master Project dashboard to track progress.

## Features

- Automatic creation of 7-step project boards for repos
- Master Project dashboard showing repo progress with clickable links
- Scheduled updates via GitHub Actions
- Automatically fetches all repositories; no manual list required
- Mapping of repo → project stored in JSON for tracking

## Workflow

1. MVP / Idea
2. PRD / Defined
3. Dev / Implementation
4. Code Review / QA Prep
5. CI/CD / Integration
6. Testing / Verification
7. Release / Done

## Users

- Solo developer (initially)
- Can scale to small teams in the future

## Automation

- Python script `manage_projects_auto_repos.py` for creation and sync
- GitHub Actions workflow triggers automation weekly or manually

## Data

- `repo_project_mapping.json` → auto-generated mapping of repo to project ID

## Deliverables

- `scripts/manage_projects_auto_repos.py` → all-in-one automation script
- `.github/workflows/manage_projects.yml` → GitHub Actions workflow
- Master Project dashboard in repo
- README & PRD documents

## Future Considerations

- Extend progress metrics to track issues per column
- Allow multiple Master Projects per project category
- Optional integration with notifications or reporting tools
