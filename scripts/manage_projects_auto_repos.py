import os
import json
import requests

# --------------------
# CONFIG
# --------------------
GITHUB_TOKEN = os.environ.get("MASTER_PROJECT_ID")  # This contains your auth token
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

    token = os.getenv('MASTER_PROJECT_ID')
    if not token:
        raise Exception("MASTER_PROJECT_ID environment variable not set")
    
    headers = {"Authorization": f"Bearer {token}"}
    json_data = {"query": query, "variables": variables or {}}
    response = requests.post("https://api.github.com/graphql", json=json_data, headers=headers)
    
    # Debug: print response status and content if there's an issue
    if response.status_code != 200:
        print(f"[ERROR] HTTP {response.status_code}: {response.text}")
        raise Exception(f"HTTP error {response.status_code}: {response.text}")
    
    result = response.json()
    
    # Debug: print the full response if there's no 'data' key
    if "data" not in result:
        print(f"[ERROR] Response missing 'data' key: {result}")
    
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
    
    # Debug: check if we have the expected data structure
    if "data" not in result or not result["data"] or "user" not in result["data"]:
        print(f"[ERROR] Unexpected response structure: {result}")
        raise Exception(f"Failed to get user ID for {username}")
    
    return result["data"]["user"]["id"]

def create_project_if_missing(owner_id, repo_name):
    # 1. Lista progetti già esistenti nell'owner
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

    # 2. Se già esiste con quel nome → riusa
    for p in existing_projects:
        if p["title"] == f"{repo_name} Project":
            return p["id"]

    # 3. Se non c'è → crealo
    mutation = """
    mutation($ownerId: ID!, $title: String!) {
      createProjectV2(input: {ownerId: $ownerId, title: $title}) {
        projectV2 {
          id
          title
        }
      }
    }
    """
    result = run_query(mutation, {"ownerId": owner_id, "title": f"{repo_name} Project"})
    return result["data"]["createProjectV2"]["projectV2"]["id"]

# --------------------
# USER / REPO helpers
# --------------------
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

def get_user_repos(username):
    query = """
    query($username: String!) {
      user(login: $username) {
        repositories(first: 100, ownerAffiliations: OWNER) {
          nodes {
            id
            name
          }
        }
      }
    }
    """
    result = run_query(query, {"username": username})
    return result["data"]["user"]["repositories"]["nodes"]
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

STATUS_OPTIONS = [
    {"name": "Backlog", "color": "GRAY", "description": "Task in Backlog"},
    {"name": "In Progress", "color": "BLUE", "description": "Task in Progress"},
    {"name": "Review", "color": "YELLOW", "description": "Task under Review"},
    {"name": "Done", "color": "GREEN", "description": "Completed Task"},
    {"name": "Blocked", "color": "RED", "description": "Blocked Task"},
    {"name": "On Hold", "color": "ORANGE", "description": "Task on Hold"},
    {"name": "QA", "color": "PURPLE", "description": "Quality Assurance"}
]

def create_status_field(project_id: str):
    """
    Crea un campo 'Status' SINGLE_SELECT nel progetto GitHub se non esiste già.
    """
    options = [
        {"name": "Backlog", "color": "GRAY", "description": "Task in Backlog"},
        {"name": "In Progress", "color": "BLUE", "description": "Task in Progress"},
        {"name": "Review", "color": "YELLOW", "description": "Task under Review"},
        {"name": "Done", "color": "GREEN", "description": "Completed Task"},
        {"name": "Blocked", "color": "RED", "description": "Blocked Task"},
        {"name": "On Hold", "color": "ORANGE", "description": "Task on Hold"},
        {"name": "QA", "color": "PURPLE", "description": "Quality Assurance"}
    ]

    query = """
    query($projectId: ID!) {
      node(id: $projectId) {
        ... on ProjectV2 {
          fields(first: 50) {
            nodes {
              __typename
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
    existing_fields = result.get("data", {}).get("node", {}).get("fields", {}).get("nodes", [])

    for field in existing_fields:
        if field.get("__typename") == "ProjectV2SingleSelectField" and field.get("name") == "Status":
            print(f"[INFO] Field 'Status' già presente nel progetto {project_id}")
            return field["id"]

    mutation = """
    mutation($projectId: ID!, $options: [ProjectV2SingleSelectFieldOptionInput!]!) {
      createProjectV2Field(input: {
        projectId: $projectId,
        name: "Status",
        dataType: SINGLE_SELECT,
        singleSelectOptions: $options
      }) {
        projectV2Field {
          ... on ProjectV2SingleSelectField {
            id
            name
          }
        }
      }
    }
    """
    result = run_query(mutation, {"projectId": project_id, "options": options})
    field_id = result["data"]["createProjectV2Field"]["projectV2Field"]["id"]
    print(f"[INFO] Campo 'Status' creato con ID {field_id}")
    return field_id

def get_project_items(project_id: str):
    """
    Recupera tutti gli item di un ProjectV2, gestendo correttamente i diversi tipi di contenuto
    (Issue, PullRequest, DraftIssue) e leggendo i campi SINGLE_SELECT come Status.
    """
    query = """
    query($id: ID!) {
      node(id: $id) {
        ... on ProjectV2 {
          items(first: 100) {
            nodes {
              id
              content {
                __typename
                ... on Issue {
                  id
                  title
                  repository {
                    id
                    name
                  }
                }
                ... on PullRequest {
                  id
                  title
                  repository {
                    id
                    name
                  }
                }
                ... on DraftIssue {
                  id
                  title
                }
              }
              fieldValues(first: 10) {
                nodes {
                  __typename
                  ... on ProjectV2ItemFieldSingleSelectValue {
                    field {
                      __typename
                      ... on ProjectV2SingleSelectField {
                        id
                        name
                      }
                    }
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

    nodes = result.get("data", {}).get("node", {}).get("items", {}).get("nodes", [])
    for item in nodes:
        content = item.get("content")
        content_id = None
        repo_id = None
        
        if content:
            content_type = content.get("__typename")
            content_id = content.get("id")
            
            # For Issues and PullRequests, get the repository ID
            if content_type in ["Issue", "PullRequest"] and "repository" in content:
                repo_id = content["repository"]["id"]

        status = None
        for fv in item.get("fieldValues", {}).get("nodes", []):
            if fv.get("__typename") != "ProjectV2ItemFieldSingleSelectValue":
                continue
            field = fv.get("field")
            if not field or field.get("__typename") != "ProjectV2SingleSelectField":
                continue
            if field.get("name") == "Status":
                status = fv.get("name")

        items_list.append({
            "item_id": item["id"],
            "content_id": content_id,
            "repo_id": repo_id,
            "status": status
        })

    return items_list

def sync_project_fields(project_id: str):
    """
    Sync required fields into the project.
    Currently ensures 'Status' exists.
    """
    query = """
    query($projectId: ID!) {
      node(id: $projectId) {
        ... on ProjectV2 {
          fields(first: 50) {
            nodes {
              ... on ProjectV2FieldCommon {
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
    nodes = result["data"]["node"]["fields"]["nodes"]
    existing_fields = [f["name"] for f in nodes if "name" in f]
    
    print(f"[INFO] Existing fields: {existing_fields}")

    if "Status" not in existing_fields:
        print(f"[INFO] Creating missing 'Status' field for project {project_id}")
        create_status_field(project_id)
    else:
        print(f"[INFO] 'Status' field already exists for project {project_id}")

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

def add_repo_to_master_project(master_project_id, repo_id, repo_name, status="Backlog"):
    """
    Adds a repository as a project item to the master project.
    Since repositories can't be added directly as items, we create a draft issue instead.
    """
    # Create a draft issue to represent the repository
    mutation_draft = """
    mutation($projectId: ID!, $title: String!, $body: String!) {
      addProjectV2DraftIssue(input: {
        projectId: $projectId,
        title: $title,
        body: $body
      }) {
        projectItem {
          id
        }
      }
    }
    """
    
    draft_title = f"Repository: {repo_name}"
    draft_body = f"This item represents the repository {repo_name} for project tracking purposes."
    
    result = run_query(mutation_draft, {
        "projectId": master_project_id,
        "title": draft_title,
        "body": draft_body
    })
    
    item_id = result["data"]["addProjectV2DraftIssue"]["projectItem"]["id"]

    # Set the status field
    master_fields = get_project_fields(master_project_id)
    if "Status" in master_fields:
        status_field_id = master_fields["Status"]
        
        mutation_status = """
        mutation($itemId: ID!, $fieldId: ID!, $value: String!) {
          updateProjectV2ItemField(input: {
            itemId: $itemId,
            fieldId: $fieldId,
            value: $value
          }) {
            projectV2Item { id }
          }
        }
        """
        
        run_query(mutation_status, {
            "itemId": item_id,
            "fieldId": status_field_id,
            "value": status
        })

    print(f"[SYNC] Added repo {repo_name} to Master project with status '{status}'")
    return item_id

def check_repo_in_master(master_project_id, repo_name):
    """
    Check if a repository (represented as a draft issue) already exists in the master project.
    """
    items = get_project_items(master_project_id)
    for item in items:
        # Check if there's a draft issue with the repository name
        content = item.get("content")
        if content and content.get("__typename") == "DraftIssue":
            title = content.get("title", "")
            if f"Repository: {repo_name}" in title:
                return True
    return False

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

    # Test authentication first
    token = os.environ.get("MASTER_PROJECT_ID")
    if not token:
        raise Exception("MASTER_PROJECT_ID environment variable not set")
    
    if not token.startswith(('ghp_', 'github_pat_')):
        print(f"[WARNING] Token format looks unusual. Expected to start with 'ghp_' or 'github_pat_', got: {token[:10]}...")

    print("[INFO] Testing GitHub authentication...")
    try:
        # Simple test query to verify authentication
        test_query = "query { viewer { login } }"
        test_result = run_query(test_query)
        current_user = test_result["data"]["viewer"]["login"]
        print(f"[INFO] Successfully authenticated as: {current_user}")
        
        if current_user != USERNAME:
            print(f"[WARNING] Authenticated as '{current_user}' but script is configured for '{USERNAME}'")
    except Exception as e:
        print(f"[ERROR] Authentication test failed: {e}")
        return

    print("[INFO] Fetching user and repos...")
    owner_id = get_user_id(USERNAME)  # recupera ID dello user
    repos = get_user_repos(USERNAME)
    print(f"[INFO] Found {len(repos)} repositories.")

    # --- Master Project ---
    master_project_id = mapping.get("master_project_id")
    
    # Check if we have a predefined master project ID from environment
    env_master_project_id = os.environ.get("MASTER_PROJECT_ID_2")
    
    if not master_project_id:
        if env_master_project_id:
            # Use the predefined master project ID from environment
            master_project_id = env_master_project_id
            print(f"[INFO] Using predefined master project ID from environment")
        else:
            # Look for existing or create new master project
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

    # Ensure master project has required fields
    sync_project_fields(master_project_id)

    # --- Repo Projects + Sync ---
    for repo in repos:
        repo_name = repo["name"]
        repo_id = repo["id"]
        print(f"[INFO] Checking repo: {repo_name}")
        
        # Create or get project for this repo
        project_id = create_project_if_missing(owner_id, repo_name)
        sync_project_fields(project_id)

        if repo_name in mapping["repos"]:
            repo_project_id = mapping["repos"][repo_name]
            print(f"[INFO] Repo {repo_name} already tracked with Project ID: {repo_project_id}")
        else:
            repo_project_id = project_id
            mapping["repos"][repo_name] = repo_project_id
            save_mapping(mapping)
            print(f"[INFO] Repo {repo_name} mapped with Project ID: {repo_project_id}")

        # --- Sync to Master ---
        # Check if this repo is already represented in the master project
        if not check_repo_in_master(master_project_id, repo_name):
            add_repo_to_master_project(master_project_id, repo_id, repo_name, "Backlog")
        else:
            print(f"[INFO] Repo {repo_name} already exists in master project")

if __name__ == "__main__":
    main()