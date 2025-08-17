import os
import json
from github import Github, GithubException

# ------------------------
# CONFIGURATION
# ------------------------
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
MAPPING_FILE = "repo_project_mapping.json"
MASTER_PROJECT_ID = int(os.environ.get("MASTER_PROJECT_ID"))
GITHUB_REPO = os.environ.get("GITHUB_REPO")  # e.g., gianpy99/github-master-monitor

# Professional 7-step columns
COLUMNS = [
    "MVP / Idea",
    "PRD / Defined",
    "Dev / Implementation",
    "Code Review / QA Prep",
    "CI/CD / Integration",
    "Testing / Verification",
    "Release / Done"
]

# ------------------------
# HELPER FUNCTIONS
# ------------------------
def load_mapping():
    if os.path.exists(MAPPING_FILE):
        with open(MAPPING_FILE, "r") as f:
            return json.load(f)
    return {}

def save_mapping(mapping):
    with open(MAPPING_FILE, "w") as f:
        json.dump(mapping, f, indent=2)

def fetch_all_repos(g):
    """
    Automatically fetch all repositories for the authenticated user
    """
    user = g.get_user()
    return [repo.full_name for repo in user.get_repos()]

def create_project_if_missing(repo):
    projects = list(repo.get_projects())
    if projects:
        print(f"[INFO] Project exists for {repo.full_name}")
        return projects[0].id
    print(f"[INFO] Creating project for {repo.full_name}")
    project = repo.create_project(name="Development Board",
                                  body="Automated 7-step workflow")
    for col_name in COLUMNS:
        project.create_column(col_name)
    return project.id

def fetch_column_counts(project):
    counts = {}
    for col in project.get_columns():
        counts[col.name] = col.get_cards().totalCount
    return counts

def calculate_progress(column_counts):
    done_columns = ["Release / Done"]
    total_issues = sum(column_counts.values())
    if total_issues == 0:
        return 0
    done_issues = sum(column_counts[col] for col in done_columns if col in column_counts)
    return round((done_issues / total_issues) * 100, 2)

def update_master_project_card(master_project, repo_name, progress, repo_project_url):
    column = master_project.get_columns()[0]  # First column: "Repo Overview"
    existing_cards = list(column.get_cards())
    card_title = f"{repo_name} – {progress}% done"
    card_note = f"Project board: {repo_project_url}"

    # Update existing card if present
    for card in existing_cards:
        if repo_name in card.note or repo_name in card_title:
            card.edit(note=card_title)
            try:
                comments = list(card.get_comments())
                if not comments:
                    card.create_comment(card_note)
            except Exception:
                pass
            return

    # Create new card if not found
    new_card = column.create_card(note=card_title)
    try:
        new_card.create_comment(card_note)
    except Exception:
        pass

# ------------------------
# MAIN LOGIC
# ------------------------
def main():
    g = Github(GITHUB_TOKEN)
    mapping = load_mapping()

    # Automatically fetch all repositories
    repos_list = fetch_all_repos(g)
    print(f"[INFO] Found {len(repos_list)} repositories.")

    master_project_repo = g.get_repo(GITHUB_REPO)
    master_project = master_project_repo.get_project(MASTER_PROJECT_ID)

    for repo_name in repos_list:
        try:
            repo = g.get_repo(repo_name)
            # Ensure repo project exists
            project_id = mapping.get(repo_name)
            if not project_id:
                project_id = create_project_if_missing(repo)
                mapping[repo_name] = project_id

            # Fetch repo project stats
            repo_project = repo.get_project(project_id)
            column_counts = fetch_column_counts(repo_project)
            progress = calculate_progress(column_counts)

            # Update Master Project
            update_master_project_card(master_project, repo_name, progress, repo_project.html_url)
            print(f"[INFO] {repo_name}: {progress}% done")

        except GithubException as e:
            print(f"[ERROR] Failed for {repo_name}: {e}")

    save_mapping(mapping)
    print("[INFO] All projects created/updated successfully!")

if __name__ == "__main__":
    main()
