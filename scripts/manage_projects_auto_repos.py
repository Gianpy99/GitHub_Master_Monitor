import os
import json
import requests

# --------------------
# CONFIG
# --------------------
GITHUB_TOKEN = os.environ.get("MASTER_PROJECT_ID")  # This contains your auth token
USERNAME = "Gianpy99"
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
    
    # Clean any whitespace from token
    token = token.strip()
    
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
    # 1. Lista progetti giÃ  esistenti nell'owner
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

    # 2. Se giÃ  esiste con quel nome â†' riusa
    for p in existing_projects:
        if p["title"] == f"{repo_name} Project":
            return p["id"]

    # 3. Se non c'Ã¨ â†' crealo
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
    Crea un campo 'Status' SINGLE_SELECT nel progetto GitHub se non esiste giÃ .
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
            print(f"[INFO] Field 'Status' giÃ  presente nel progetto {project_id}")
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
    """
    Get project fields mapping with comprehensive field type support and error handling.
    """
    query = """
    query($id: ID!) {
      node(id: $id) {
        ... on ProjectV2 {
          fields(first: 50) {
            nodes {
              __typename
              ... on ProjectV2Field {
                id
                name
              }
              ... on ProjectV2IterationField {
                id
                name
              }
              ... on ProjectV2SingleSelectField {
                id
                name
                options {
                  id
                  name
                }
              }
            }
          }
        }
      }
    }
    """
    
    try:
        result = run_query(query, {"id": project_id})
        
        if "errors" in result:
            print(f"[ERROR] GraphQL errors getting fields for {project_id}: {result['errors']}")
            return {}
            
        if not result.get("data") or not result["data"].get("node"):
            print(f"[ERROR] Invalid response structure for project {project_id}: {result}")
            return {}
            
        fields = result["data"]["node"]["fields"]["nodes"]
        
        # Debug: print the fields structure to understand what we're getting
        print(f"[DEBUG] Raw fields from project {project_id}: {fields}")
        
        # Filter out fields that don't have both name and id - be extra safe
        field_mapping = {}
        for field in fields:
            try:
                if (isinstance(field, dict) and 
                    field.get("name") is not None and 
                    field.get("id") is not None and
                    len(str(field.get("name")).strip()) > 0):
                    field_mapping[field["name"]] = field["id"]
                else:
                    print(f"[DEBUG] Skipping field without valid name/id: {field}")
            except Exception as field_error:
                print(f"[DEBUG] Error processing field {field}: {field_error}")
                continue
        
        print(f"[DEBUG] Final field mapping for {project_id}: {field_mapping}")
        return field_mapping
        
    except Exception as e:
        print(f"[ERROR] Failed to get project fields for {project_id}: {e}")
        import traceback
        print(f"[ERROR] Full traceback: {traceback.format_exc()}")
        return {}

def add_repo_to_master_project(master_project_id, repo_id, repo_name, status="Backlog"):
    """
    Adds a repository as a project item to the master project.
    Since repositories can't be added directly as items, we create a draft issue instead.
    """
    print(f"[DEBUG] Adding repo {repo_name} to master project {master_project_id}")
    
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
    
    try:
        result = run_query(mutation_draft, {
            "projectId": master_project_id,
            "title": draft_title,
            "body": draft_body
        })
        
        item_id = result["data"]["addProjectV2DraftIssue"]["projectItem"]["id"]
        print(f"[DEBUG] Created draft issue with item_id: {item_id}")

        # Set the status field - with error handling
        print(f"[DEBUG] Getting master project fields...")
        master_fields = get_project_fields(master_project_id)
        print(f"[DEBUG] Master fields received: {master_fields}")
        
        if "Status" in master_fields:
            status_field_id = master_fields["Status"]
            print(f"[DEBUG] Found Status field with ID: {status_field_id}")
            
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
            
            try:
                run_query(mutation_status, {
                    "itemId": item_id,
                    "fieldId": status_field_id,
                    "value": status
                })
                print(f"[DEBUG] Successfully set status to '{status}'")
            except Exception as status_error:
                print(f"[WARNING] Failed to set status field: {status_error}")
        else:
            print(f"[WARNING] No 'Status' field found in master project fields: {list(master_fields.keys())}")

        print(f"[SYNC] Added repo {repo_name} to Master project with status '{status}'")
        return item_id
        
    except Exception as e:
        print(f"[ERROR] Failed to add repo {repo_name} to master project: {e}")
        import traceback
        print(f"[ERROR] Full traceback: {traceback.format_exc()}")
        raise

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

    # Debug: List all environment variables that might be related
    print("[DEBUG] Checking environment variables...")
    for key in os.environ.keys():
        if 'PROJECT' in key.upper() or 'GITHUB' in key.upper() or 'TOKEN' in key.upper():
            value = os.environ[key]
            # Mask tokens for security, show length and first few chars
            if len(value) > 10:
                print(f"[DEBUG] {key}: length={len(value)}, starts with '{value[:6]}...'")
            else:
                print(f"[DEBUG] {key}: '{value}'")

    # Test authentication first
    token = os.environ.get("MASTER_PROJECT_ID")
    if not token:
        # Try alternative environment variable names
        token = os.environ.get("GITHUB_TOKEN")
        if token:
            print("[INFO] Using GITHUB_TOKEN instead of MASTER_PROJECT_ID")
        else:
            print("[ERROR] No authentication token found in environment variables")
            print("[ERROR] Available env vars:", [k for k in os.environ.keys() if 'TOKEN' in k.upper() or 'PROJECT' in k.upper()])
            raise Exception("No GitHub token found in environment variables")
    
    # Debug token info
    print(f"[DEBUG] Token length: {len(token)}")
    print(f"[DEBUG] Token first 10 chars: '{token[:10]}'")
    print(f"[DEBUG] Token last 10 chars: '{token[-10:]}'")
    print(f"[DEBUG] Token has whitespace: {token != token.strip()}")
    
    # Clean the token of any whitespace
    clean_token = token.strip()
    
    if not clean_token.startswith(('ghp_', 'github_pat_')):
        print(f"[WARNING] Token format looks unusual. Expected to start with 'ghp_' or 'github_pat_'")
        print(f"[DEBUG] Clean token first 15 chars: '{clean_token[:15]}'")

    print("[INFO] Testing GitHub authentication...")
    try:
        # Use the cleaned token for the test
        headers = {"Authorization": f"Bearer {clean_token}"}
        json_data = {"query": "query { viewer { login } }"}
        response = requests.post("https://api.github.com/graphql", json=json_data, headers=headers)
        
        print(f"[DEBUG] Response status: {response.status_code}")
        if response.status_code != 200:
            print(f"[DEBUG] Response headers: {dict(response.headers)}")
            print(f"[DEBUG] Response text: {response.text}")
        
        result = response.json()
        
        if "data" in result and result["data"] and "viewer" in result["data"]:
            current_user = result["data"]["viewer"]["login"]
            print(f"[INFO] Successfully authenticated as: {current_user}")
            
            if current_user != USERNAME:
                print(f"[WARNING] Authenticated as '{current_user}' but script is configured for '{USERNAME}'")
        else:
            print(f"[ERROR] Unexpected response: {result}")
            return
            
    except Exception as e:
        print(f"[ERROR] Authentication test failed: {e}")
        return

    print("[INFO] Fetching user and repos...")
    owner_id = get_user_id(USERNAME)  # recupera ID dello user
    repos = get_user_repos(USERNAME)
    print(f"[INFO] Found {len(repos)} repositories.")

    # --- Master Project ---
    master_project_id = mapping.get("master_project_id")
    
    print(f"[DEBUG] master_project_id from mapping: {master_project_id}")
    
    # FORCE CLEAR any placeholder or invalid IDs
    if master_project_id == "ID_MASTER":
        print(f"[INFO] DETECTED PLACEHOLDER 'ID_MASTER' - FORCE CLEARING")
        master_project_id = None
    elif not master_project_id:
        print(f"[INFO] No master project ID found")
        master_project_id = None
    elif len(str(master_project_id)) < 10:
        print(f"[INFO] Invalid master project ID (too short): '{master_project_id}' - CLEARING")
        master_project_id = None
    else:
        print(f"[INFO] Using existing master project ID: {master_project_id}")
    
    # Always regenerate if we don't have a valid ID
    if master_project_id is None:
        print(f"[INFO] Looking for existing projects for user {USERNAME}...")
        projects = get_projects_for_owner(USERNAME)
        print(f"[DEBUG] Found {len(projects)} existing projects")
        
        for p in projects:
            print(f"[DEBUG] Project: '{p['title']}' - ID: {p['id']}")
        
        master_project = next((p for p in projects if p["title"] == MASTER_PROJECT_TITLE), None)
        if master_project:
            master_project_id = master_project["id"]
            print(f"[INFO] Found existing master project: {master_project_id}")
        else:
            print(f"[INFO] Creating new master project titled '{MASTER_PROJECT_TITLE}'...")
            master_project_id = create_project(owner_id, MASTER_PROJECT_TITLE)
            create_status_field(master_project_id)
            print(f"[INFO] Created new master project: {master_project_id}")
        
        # Save the real project ID
        mapping["master_project_id"] = master_project_id
        save_mapping(mapping)
        print(f"[INFO] Saved real master project ID to mapping file")
    
    print(f"[INFO] Final Master Project ID: {master_project_id}")

    # Ensure master project has required fields
    print(f"[DEBUG] About to sync fields for project ID: {master_project_id}")
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