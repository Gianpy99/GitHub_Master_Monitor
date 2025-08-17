import os
import json
import requests

# --------------------
# CONFIG
# --------------------
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
USERNAME = "gianpy99"
MASTER_PROJECT_TITLE = "Master Project"
MAPPING_FILE = "repo_project_mapping.json"

HEADERS = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Content-Type": "application/json"
}

API_URL = "https://api.github.com/graphql"

# --------------------
# GRAPHQL helper
# --------------------
# --- Config ---
USERNAME = "gianpy99"
MASTER_PROJECT_ID = "ID_MASTER"

FIELDS_TO_CREATE = [
    {"name": "Status", "color": ["GRAY", "BLUE", "YELLOW", "GREEN", "RED", "ORANGE", "PURPLE"], 
     "description": ["Backlog", "In Progress", "Review", "Done", "Blocked", "On Hold", "QA"]},
    {"name": "Priority", "color": ["RED", "ORANGE", "YELLOW", "GREEN"], 
     "description": ["High", "Medium-High", "Medium", "Low"]},
    {"name": "Type", "color": ["BLUE", "GREEN", "YELLOW", "RED"], 
     "description": ["Bug", "Feature", "Chore", "Improvement"]},
    {"name": "Estimate", "color": ["GRAY"], 
     "description": ["Story Points Estimate"]},
    {"name": "Owner", "color": ["GRAY"], 
     "description": ["Assigned User"]},
    {"name": "Due Date", "color": ["GRAY"], 
     "description": ["Deadline"]},
    {"name": "Sprint", "color": ["GRAY"], 
     "description": ["Sprint Name"]}
]

# --- Funzioni base ---
def run_query(query, variables=None):
    """Esegue una query GraphQL con autenticazione."""
    import requests
    import os

    headers = {"Authorization": f"Bearer {os.getenv('GITHUB_TOKEN')}"}
    json_data = {"query": query, "variables": variables or {}}
    response = requests.post("https://api.github.com/graphql", json=json_data, headers=headers)
    result = response.json()
    if "errors" in result:
        raise Exception(f"GraphQL error: {result['errors']}")
    return result

def get_user_id(username):
    query = """
    query($username: String!) {
      user(login: $username) {
        id
      }
    }
    """
    result = run_query(query, {"username": username})
    return result["data"]["user"]["id"]

def create_project_if_missing(owner_id, repo_name):
    # Recupera tutti i progetti dell'utente
    query = """
    query($ownerId: ID!) {
      node(id: $ownerId) {
        ... on User {
          projectsV2(first: 50) {
            nodes {
              id
              title
            }
          }
        }
      }
    }
    """
    result = run_query(query, {"ownerId": owner_id})
    existing_projects = result["data"]["node"]["projectsV2"]["nodes"]
    for p in existing_projects:
        if p["title"] == f"{repo_name} Project":
            print(f"[INFO] Progetto già presente per {repo_name}")
            return p["id"]

    # Crea il progetto a livello utente
    mutation = """
    mutation($ownerId: ID!, $title: String!) {
      createProjectV2(input: {ownerId: $ownerId, title: $title}) {
        projectV2 {
          id
        }
      }
    }
    """
    result = run_query(mutation, {"ownerId": owner_id, "title": f"{repo_name} Project"})
    project_id = result["data"]["createProjectV2"]["projectV2"]["id"]
    print(f"[INFO] Progetto creato per {repo_name} con ID {project_id}")
    return project_id


def sync_project_fields(project_id):
    """Crea i campi mancanti nel progetto."""
    # Recupera i campi esistenti
    query = """
    query($projectId: ID!) {
      node(id: $projectId) {
        ... on ProjectV2 {
          fields(first: 50) {
            nodes {
              ... on ProjectV2SingleSelectField {
                id
                name
              }
            }
          }
        }
      }
    }
    """
    result = run_query(query, {"projectId": project_id})
    existing_fields = result["data"]["node"]["fields"]["nodes"]
    existing_fields = [f for f in existing_fields if "name" in f]
    existing_names = {f["name"] for f in existing_fields}

    for field in FIELDS_TO_CREATE:
        if field["name"] in existing_names:
            print(f"[INFO] Campo '{field['name']}' già presente")
            continue

        options = [{"name": desc, "color": color} for desc, color in zip(field["description"], field["color"])]
        mutation = """
        mutation($projectId: ID!, $options: [ProjectV2SingleSelectFieldOptionInput!]!) {
          createProjectV2Field(input: {
            projectId: $projectId,
            name: "%s",
            dataType: SINGLE_SELECT,
            singleSelectOptions: $options
          }) {
            projectV2Field {
              id
              name
            }
          }
        }
        """ % field["name"]

        result = run_query(mutation, {"projectId": project_id, "options": options})
        field_id = result["data"]["createProjectV2Field"]["projectV2Field"]["id"]
        print(f"[INFO] Campo '{field['name']}' creato con ID {field_id}")

# --------------------
# USER / REPO helpers
# --------------------
def get_user_id(username):
    query = """
    query($login: String!) { user(login: $login) { id } }
    """
    return run_query(query, {"login": username})["data"]["user"]["id"]

def get_user_repositories(username):
    query = """
    query($login: String!) {
      user(login: $login) {
        repositories(first: 100, ownerAffiliations: OWNER) {
          nodes { id name }
        }
      }
    }
    """
    return run_query(query, {"login": username})["data"]["user"]["repositories"]["nodes"]

# --------------------
# PROJECT helpers
# --------------------
def get_projects_for_owner(owner_login):
    query = """
    query($login: String!) {
      user(login: $login) {
        projectsV2(first: 50) { nodes { id title } }
      }
    }
    """
    return run_query(query, {"login": owner_login})["data"]["user"]["projectsV2"]["nodes"]

def get_projects_for_repo(owner, repo_name):
    query = """
    query($owner: String!, $repo: String!) {
      repository(owner: $owner, name: $repo) {
        projectsV2(first: 10) { nodes { id title } }
      }
    }
    """
    return run_query(query, {"owner": owner, "repo": repo_name})["data"]["repository"]["projectsV2"]["nodes"]

def create_project(owner_id, title):
    mutation = """
    mutation($ownerId: ID!, $title: String!) {
      createProjectV2(input: {ownerId: $ownerId, title: $title}) {
        projectV2 { id title }
      }
    }
    """
    return run_query(mutation, {"ownerId": owner_id, "title": title})["data"]["createProjectV2"]["projectV2"]["id"]

COLUMNS = [
    "MVP / Idea",
    "PRD / Defined",
    "Dev / Implementation",
    "Code Review / QA Prep",
    "CI/CD / Integration",
    "Testing / Verification",
    "Release / Done"
]

COLORS = ["BLUE", "GREEN", "YELLOW", "PURPLE", "PINK", "ORANGE", "RED"]

def create_status_field(project_id: str):
    """
    Crea un campo 'Status' SINGLE_SELECT nel progetto GitHub se non esiste già.
    """
    # Opzioni della select con colore e descrizione
    options = [
        {"name": "Backlog", "color": "GRAY", "description": "Task in Backlog"},
        {"name": "In Progress", "color": "BLUE", "description": "Task in Progress"},
        {"name": "Review", "color": "YELLOW", "description": "Task under Review"},
        {"name": "Done", "color": "GREEN", "description": "Completed Task"},
        {"name": "Blocked", "color": "RED", "description": "Blocked Task"},
        {"name": "On Hold", "color": "ORANGE", "description": "Task on Hold"},
        {"name": "QA", "color": "PURPLE", "description": "Quality Assurance"}
    ]

    # Recupera i campi esistenti del progetto
    query = """
    query($projectId: ID!) {
      node(id: $projectId) {
        ... on ProjectV2 {
          fields(first: 50) {
            nodes {
              ... on ProjectV2SingleSelectField {
                id
                name
              }
            }
          }
        }
      }
    }
    """
    result = run_query(query, {"projectId": project_id})
    existing_fields = result["data"]["node"]["fields"]["nodes"]
    
    # Controlla se il campo Status esiste già
    for field in existing_fields:
        if field["name"] == "Status":
            print(f"[INFO] Field 'Status' già presente nel progetto {project_id}")
            return field["id"]

    # Crea il campo SINGLE_SELECT
    mutation = """
    mutation($projectId: ID!, $options: [ProjectV2SingleSelectFieldOptionInput!]!) {
      createProjectV2Field(input: {
        projectId: $projectId,
        name: "Status",
        dataType: SINGLE_SELECT,
        singleSelectOptions: $options
      }) {
        projectV2Field {
          id
          name
        }
      }
    }
    """
    result = run_query(mutation, {"projectId": project_id, "options": options})
    field_id = result["data"]["createProjectV2Field"]["projectV2Field"]["id"]
    print(f"[INFO] Campo 'Status' creato con ID {field_id}")
    return field_id

# --------------------
# MASTER SYNC helpers
# --------------------
def get_project_fields(project_id):
    query = """
    query($id:ID!){
      node(id:$id) { ... on ProjectV2 { fields(first:20){ nodes { ... on ProjectV2SingleSelectField { id name } } } } }
    }
    """
    fields = run_query(query, {"id": project_id})["data"]["node"]["fields"]["nodes"]
    return {f["name"]: f["id"] for f in fields}

def get_project_items(project_id):
    query = """
    query($id:ID!){
      node(id:$id){
        ... on ProjectV2{
          items(first:100){
            nodes{
              id
              content { ... on Repository { id name url } }
              fieldValues(first:10){
                nodes{
                  ... on ProjectV2ItemFieldSingleSelectValue{
                    field { id name }
                    name
                  }
                }
              }
            }
          }
        }
      }
    }
    """
    items_list = []
    result = run_query(query, {"id": project_id})
    for item in result["data"]["node"]["items"]["nodes"]:
        status = None
        content_id = item["content"]["id"] if item["content"] else None
        for fv in item["fieldValues"]["nodes"]:
            if fv["field"]["name"] == "Status":
                status = fv["name"]
        items_list.append({"item_id": item["id"], "repo_id": content_id, "status": status})
    return items_list

def add_repo_item_to_master(master_project_id, repo_id, status):
    mutation_add = """
    mutation($projectId:ID!, $contentId:ID!){
      addProjectV2ItemById(input:{projectId:$projectId, contentId:$contentId}){
        item { id }
      }
    }
    """
    result = run_query(mutation_add, {"projectId": master_project_id, "contentId": repo_id})
    item_id = result["data"]["addProjectV2ItemById"]["item"]["id"]

    master_fields = get_project_fields(master_project_id)
    status_field_id = master_fields["Status"]

    mutation_status = """
    mutation($itemId:ID!, $fieldId:ID!, $value:String!){
      updateProjectV2ItemField(input:{
        itemId:$itemId,
        fieldId:$fieldId,
        value:$value
      }) { projectV2Item { id } }
    }
    """
    run_query(mutation_status, {"itemId": item_id, "fieldId": status_field_id, "value": status})
    print(f"[SYNC] Added repo {repo_id} to Master with status '{status}'")

# --------------------
# JSON mapping helpers
# --------------------
def load_mapping():
    if os.path.exists(MAPPING_FILE):
        with open(MAPPING_FILE, "r") as f:
            return json.load(f)
    return {"master_project_id": None, "repos": {}}

def save_mapping(mapping):
    with open(MAPPING_FILE, "w") as f:
        json.dump(mapping, f, indent=2)

# --------------------
# MAIN
# --------------------
def main():
    
    mapping = load_mapping()

    print("[INFO] Fetching user and repos...")
    owner_id = get_user_id(USERNAME)
    repos = get_user_repos(USERNAME)
    print(f"[INFO] Found {len(repos)} repositories.")

    # --- Master Project ---
    master_project_id = mapping.get("master_project_id")
    if not master_project_id:
        projects = get_projects_for_owner(USERNAME)
        master_project = next((p for p in projects if p["title"] == MASTER_PROJECT_TITLE), None)
        if master_project:
            master_project_id = master_project["id"]
        else:
            master_project_id = create_project(owner_id, MASTER_PROJECT_TITLE)
            create_status_field(master_project_id)
        mapping["master_project_id"] = master_project_id
        save_mapping(mapping)
    print(f"[RESULT] MASTER_PROJECT_ID={master_project_id}")

    # --- Repo Projects + Sync ---
    for repo in repos:
        repo_name = repo["name"]
        #repo_id = repo["id"]
        print(f"\n[INFO] Checking repo: {repo_name}")
        project_id = create_project_if_missing(repo_id, repo_name)
        sync_project_fields(project_id)

        if repo_name in mapping["repos"]:
            repo_project_id = mapping["repos"][repo_name]
            print(f"[INFO] Repo {repo_name} already tracked with Project ID: {repo_project_id}")
        else:
            # Qui si crea il progetto sotto il tuo account (owner_id) e non sotto il repo
            repo_project_id = create_project(owner_id, f"{repo_name} Project")
            create_status_field(repo_project_id)

            mapping["repos"][repo_name] = repo_project_id
            save_mapping(mapping)
            print(f"[INFO] Repo {repo_name} mapped with Project ID: {repo_project_id}")

        # --- Sync to Master ---
        items = get_project_items(repo_project_id)
        master_items = get_project_items(master_project_id)
        master_repo_ids = {item["repo_id"] for item in master_items if item["repo_id"]}

        for item in items:
            if item["repo_id"] not in master_repo_ids and item["repo_id"]:
                add_repo_item_to_master(master_project_id, item["repo_id"], item["status"] or "PRD Defined")

if __name__ == "__main__":
    main()
