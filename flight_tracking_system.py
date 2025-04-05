import requests
from requests.auth import HTTPBasicAuth
import json
import time
import google.generativeai as genai

# ========== CONFIGURATION SECTION ==========
# === Jira Credentials & Constants ===
# Credentials for authenticating with the Jira API
EMAIL = "imrishabh9@gmail.com"
API_TOKEN = "ATATT3xFfGF0KJeCW79dxuKt6rRSAWJxNOIElL2amLqLAbqssMpK-zC4vTINDXhWmm8IaSvRDpb2aESz1TPXB34AvSbYctwO_1kzQ56lzD8MeG9iMRtGqJVJmFjW-m_rs8W4Z3XEDcp4acRb9-q9ln6XPeBoiv51CUtzXaPmLUuGSWBoYod6Zrs=3239D6F2"
JIRA_BASE_URL = "https://imrishabh9.atlassian.net"
PROJECT_KEY = "CPG" # The project key in Jira where tickets will be created

# Set up authentication and headers for Jira API requests
auth = HTTPBasicAuth(EMAIL, API_TOKEN)
headers = {
    "Accept": "application/json",
    "Content-Type": "application/json"
}

# === Gemini API Configuration ===
# Multiple API keys for rotating when rate limits are hit
gemini_keys = ['AIzaSyBygmSahMqMh_lAVfskpO_cKFHyrkzYJTc','AIzaSyCWDnUTjAbu7GjfXj1J9iUZfhB8dJ1x6qk','AIzaSyDPQ4AjKwe7XCad59h0QDuvXjdK5CBQDHI','AIzaSyCot7LtzWoiy8tlaUQEEAL55hO8cifTp00']
current_gemini_index = 0

# ========== GEMINI API FUNCTIONS ==========
def get_gemini_instance():
    """
    Initialize the Gemini API using the current key.
    Returns a configured GenerativeModel instance.
    """
    global current_gemini_index
    api_key = gemini_keys[current_gemini_index]
    genai.configure(api_key=api_key)
    return genai.GenerativeModel('gemini-1.5-pro-latest')

def generate_content_with_fallback(prompt):
    """
    Generate content using Gemini API with key rotation fallback and delay logic.
    If one API key fails (due to rate limits or other issues), tries the next key.
    
    Args:
        prompt (str): The prompt to send to Gemini API
        
    Returns:
        str: The generated text response
        
    Raises:
        Exception: If all API keys fail
    """
    global current_gemini_index
    initial_index = current_gemini_index  # Remember starting key index
    attempts = 0

    while attempts < len(gemini_keys):
        try:
            model = get_gemini_instance()
            response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            print(f"Gemini key {gemini_keys[current_gemini_index]} failed: {e}")
            if '429' in str(e) or 'quota' in str(e):
                time.sleep(1)  # Wait 1 second on rate limit errors
            current_gemini_index = (current_gemini_index + 1) % len(gemini_keys)
            attempts += 1
            if current_gemini_index == initial_index:
                time.sleep(2)  # Additional delay if we've cycled through all keys
    
    raise Exception("All Gemini API keys failed after multiple attempts")

# ========== JIRA API FUNCTIONS ==========
def create_jira_ticket(summary: str, description: str):
    """
    Creates a new Jira ticket (task) with the given summary and description.
    
    Args:
        summary (str): The summary/title of the Jira ticket
        description (str): The detailed description for the ticket
        
    Returns:
        str or None: The key of the created ticket (e.g., 'CPG-123') or None if creation failed
    """
    url = f"{JIRA_BASE_URL}/rest/api/3/issue"
    payload = {
        "fields": {
            "project": {"key": PROJECT_KEY},
            "summary": summary,
            "description": {
                "type": "doc",
                "version": 1,
                "content": [
                    {
                        "type": "paragraph",
                        "content": [
                            {"type": "text", "text": description}
                        ]
                    }
                ]
            },
            "issuetype": {"name": "Task"},
            "assignee": {"id": "712020:5f0ba63e-f2a3-40da-bbea-cb1c75c04953"}
        }
    }
    response = requests.post(url, headers=headers, json=payload, auth=auth)
    if response.status_code == 201:
        issue_key = response.json()["key"]
        print(f"Created Jira ticket: {issue_key}")
        return issue_key
    else:
        print("Failed to create ticket:")
        print(response.status_code, response.text)
        return None

def create_jira_subtask(parent_key: str, summary: str, description: str):
    """
    Creates a new Jira subtask linked to a parent ticket.
    
    Args:
        parent_key (str): The key of the parent ticket (e.g., 'CPG-123')
        summary (str): The summary/title of the subtask
        description (str): The detailed description for the subtask
        
    Returns:
        str or None: The key of the created subtask or None if creation failed
    """
    url = f"{JIRA_BASE_URL}/rest/api/3/issue"
    payload = {
        "fields": {
            "project": {"key": PROJECT_KEY},
            "parent": {"key": parent_key},
            "summary": summary,
            "description": {
                "type": "doc",
                "version": 1,
                "content": [
                    {
                        "type": "paragraph",
                        "content": [
                            {"type": "text", "text": description}
                        ]
                    }
                ]
            },
            "issuetype": {"name": "Subtask"},
            "assignee": {"id": "712020:5f0ba63e-f2a3-40da-bbea-cb1c75c04953"}
        }
    }
    response = requests.post(url, headers=headers, json=payload, auth=auth)
    if response.status_code == 201:
        issue_key = response.json()["key"]
        print(f"Created Jira subtask: {issue_key} under parent {parent_key}")
        return issue_key
    else:
        print(f"Failed to create subtask under {parent_key}:")
        print(response.status_code, response.text)
        return None

def fetch_visible_tickets():
    """
    Fetches and displays all visible tickets from the Jira project,
    excluding sample tickets (CPG-1, CPG-2).
    
    Returns:
        list: List of issue objects with their details
    """
    url = f"{JIRA_BASE_URL}/rest/api/3/search"
    params = {
        "jql": f"project={PROJECT_KEY} AND key NOT IN (CPG-1, CPG-2)",
        "maxResults": 50,
        "fields": "summary,status,assignee"
    }
    response = requests.get(url, headers=headers, params=params, auth=auth)
    if response.status_code == 200:
        issues = response.json().get("issues", [])
        print(f"\nTotal visible tickets: {len(issues)}\n")
        for issue in issues:
            key = issue["key"]
            summary = issue["fields"]["summary"]
            status = issue["fields"]["status"]["name"]
            assignee = issue["fields"]["assignee"]["displayName"] if issue["fields"]["assignee"] else "Unassigned"
            print(f"{key}: {summary} [Status: {status}] (Assigned to: {assignee})")
        return issues
    else:
        print("Failed to fetch tickets:")
        print(response.status_code, response.text)
        return []

# ========== TASK GENERATION FUNCTIONS ==========
def generate_development_tasks(requirement):
    """
    Uses Gemini API to generate structured development tasks for a given requirement.
    
    Args:
        requirement (str): The main task/requirement description
        
    Returns:
        list or None: JSON array of task objects or None if parsing failed
    """
    prompt = f"""Analyze the following software development task and generate EXACTLY 3 to 5 high-level, non-overlapping subtasks:
Task: {requirement}

Instructions:
1. Generate EXACTLY 3 to 5 distinct subtasks - no more, no less.
2. Each subtask should represent a major component or phase of development.
3. Ensure subtasks are broad enough to encompass significant work but specific enough to be actionable.
4. Focus on different aspects (e.g., one backend, one frontend, one for testing) rather than breaking down the same component.
5. Ensure NO DUPLICATION or overlap between subtasks.
6. Provide a category for each task (e.g., Backend, Frontend, API Integration, DevOps, Testing).
7. Predict a module or component name if possible.
8. Each subtask summary should be comprehensive but under 100 words.

Output the result as JSON in exactly this format:
[
  {{
    "summary": "Subtask summary in under 100 words",
    "category": "Backend | Frontend | API | DevOps | Testing",
    "component": "Suggested component/module",
    "title": "Short title for the Jira ticket"
  }}
]

IMPORTANT: Verify that each subtask is unique and distinct before finalizing the output. The total number of subtasks MUST be between 3 and 5, inclusive."""
    
    response_text = generate_content_with_fallback(prompt)
    
    try:
        # Find JSON content within the response (in case there's additional text)
        json_start = response_text.find('[')
        json_end = response_text.rfind(']') + 1
        
        if json_start >= 0 and json_end > json_start:
            json_content = response_text[json_start:json_end]
            return json.loads(json_content)
        else:
            return json.loads(response_text)
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON response: {e}")
        print(f"Raw response: {response_text}")
        return None

# ========== JIRA LINKING FUNCTIONS ==========
def get_link_types():
    """
    Retrieves all available issue link types from Jira.
    
    Returns:
        list: Available link types in Jira
    """
    url = f"{JIRA_BASE_URL}/rest/api/3/issueLinkType"
    response = requests.get(url, headers=headers, auth=auth)
    
    if response.status_code == 200:
        link_types = response.json().get("issueLinkTypes", [])
        print("\nAvailable link types:")
        for lt in link_types:
            print(f"  - {lt['name']} (inward: {lt['inward']}, outward: {lt['outward']})")
        return link_types
    else:
        print("Failed to fetch link types:")
        print(response.status_code, response.text)
        return []

def link_issues(outward_issue, inward_issue, link_type="Relates"):
    """
    Links two Jira issues with the specified relationship type.
    
    Args:
        outward_issue (str): The key of the outward issue
        inward_issue (str): The key of the inward issue
        link_type (str): The type of link to create between issues
        
    Returns:
        bool: True if linking was successful, False otherwise
    """
    url = f"{JIRA_BASE_URL}/rest/api/3/issueLink"
    payload = {
        "outwardIssue": {"key": outward_issue},
        "inwardIssue": {"key": inward_issue},
        "type": {"name": link_type}
    }
    print(f"Sending link request: {json.dumps(payload)}")
    response = requests.post(url, headers=headers, json=payload, auth=auth)
    
    if response.status_code == 201:
        print(f"Successfully linked {outward_issue} and {inward_issue} with type '{link_type}'")
        return True
    else:
        print(f"Failed to link issues {outward_issue} and {inward_issue}:")
        print(f"   Status code: {response.status_code}")
        print(f"   Response: {response.text}")
        return False

def create_linked_subtasks(parent_key, subtasks):
    """
    Creates Jira tickets for each subtask and links them to the parent ticket.
    
    Args:
        parent_key (str): The key of the parent ticket
        subtasks (list): List of subtask objects generated by Gemini
        
    Returns:
        tuple: (list of created issue keys, mapping of task keys to task data)
    """
    created_issues = []
    task_data_map = {}  # Map to store task key -> task data
    
    # Get available link types from Jira
    link_types = get_link_types()
    standard_link_types = ["Relates", "Relates to", "Dependency", "Parent/Child", "Blocks"]
    available_link_names = [lt["name"] for lt in link_types]
    
    # Find a suitable link type to use
    link_type_to_use = None
    for lt in standard_link_types:
        if lt in available_link_names:
            link_type_to_use = lt
            break
    
    if not link_type_to_use and link_types:
        link_type_to_use = link_types[0]["name"]
    
    if not link_type_to_use:
        print("No link types available; tickets will be created without linking")
    else:
        print(f"Will use link type: {link_type_to_use}")
    
    # Create each subtask and link to parent
    for idx, task in enumerate(subtasks):
        description = (
            f"{task['summary']}\n\n"
            f"Category: {task['category']}\n"
            f"Component: {task['component']}\n"
            f"Parent Task: {parent_key}"
        )
        issue_key = create_jira_ticket(task["title"], description)
        
        if issue_key:
            created_issues.append(issue_key)
            task_data_map[issue_key] = task
            
            if link_type_to_use:
                print(f"Attempting to link {issue_key} to {parent_key}...")
                time.sleep(1)  # Small delay to avoid rate limiting
                link_success = link_issues(parent_key, issue_key, link_type_to_use)
                
                # Try alternative link type if first attempt fails
                if not link_success and len(link_types) > 1:
                    print("First link attempt failed; trying an alternative link type...")
                    time.sleep(1)
                    alt_link_type = link_types[1]["name"]
                    link_success = link_issues(parent_key, issue_key, alt_link_type)
    
    return created_issues, task_data_map

# ========== TEST CASE GENERATION ==========
def generate_and_create_test_cases(task_description, task_key):
    """
    Generates test cases for a given task using Gemini API and creates them as subtasks.
    
    Args:
        task_description (str): Description of the task to generate test cases for
        task_key (str): The Jira key of the task
        
    Returns:
        list: Keys of created test case subtasks
    """
    prompt = f"""Generate EXACTLY 3 to 5 comprehensive test cases for the following development task:

Task Description: {task_description}

Instructions:
1. Generate EXACTLY 3 to 5 test cases - no more, no less.
2. Each test case should cover a critical functionality or edge case.
3. Test cases should be specific, actionable, and verifiable.
4. Include expected results and acceptance criteria.
5. Focus on different aspects of the task to ensure comprehensive coverage.
6. Ensure test cases are meaningful and not trivial.

Output the result as JSON in exactly this format:
[
  {{
    "test_id": "TC-1",
    "test_name": "Short descriptive name",
    "description": "Detailed test case description",
    "steps": ["Step 1", "Step 2", "Step 3"],
    "expected_result": "Expected outcome of the test",
    "priority": "High | Medium | Low"
  }}
]

IMPORTANT: Make sure each test case is unique and thorough. The total number of test cases MUST be between 3 and 5, inclusive."""
    
    print(f"\nGenerating test cases for task {task_key}...")
    response_text = generate_content_with_fallback(prompt)
    created_subtasks = []
    
    try:
        # Extract JSON content from response
        json_start = response_text.find('[')
        json_end = response_text.rfind(']') + 1
        
        if json_start >= 0 and json_end > json_start:
            json_content = response_text[json_start:json_end]
            test_cases = json.loads(json_content)
        else:
            test_cases = json.loads(response_text)
            
        print(f"\nGenerated {len(test_cases)} test cases for task {task_key}:")
        for tc in test_cases:
            # Display the generated test case
            print(f"\n--- {tc['test_id']}: {tc['test_name']} (Priority: {tc['priority']}) ---")
            print(f"Description: {tc['description']}")
            print("Steps:")
            for i, step in enumerate(tc['steps'], 1):
                print(f"  {i}. {step}")
            print(f"Expected Result: {tc['expected_result']}")
            
            # Format test case steps for Jira description
            steps_formatted = "\n".join([f"{i+1}. {step}" for i, step in enumerate(tc['steps'])])
            subtask_description = f"""Test Case: {tc['test_name']}

Description: {tc['description']}

Steps:
{steps_formatted}

Expected Result: {tc['expected_result']}

Priority: {tc['priority']}
"""
            # Create the test case as a subtask
            subtask_summary = f"Test: {tc['test_name']} [{tc['priority']}]"
            subtask_key = create_jira_subtask(task_key, subtask_summary, subtask_description)
            
            if subtask_key:
                created_subtasks.append(subtask_key)
                print(f"Created test case subtask: {subtask_key}")
                time.sleep(1)  # Small delay to avoid rate limiting
            
        return created_subtasks
        
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON response: {e}")
        print(f"Raw response: {response_text}")
        return []

# ========== MAIN PROGRAM ==========
if __name__ == "__main__":
    # Step 1: Get the main task requirement from user input
    requirement = input("Enter the main task/requirement: ")
    
    # Step 2: Create a parent ticket for the main requirement
    print("\nCreating parent ticket for the main requirement...")
    parent_key = create_jira_ticket(
        f"Main Task: {requirement}", 
        f"This is the parent ticket for: {requirement}\n\nSubtasks will be linked to this ticket."
    )
    
    if not parent_key:
        print("Failed to create parent ticket. Exiting.")
        exit(1)
    
    # Step 3: Generate development subtasks using Gemini API
    print("\nGenerating subtasks using Gemini API...")
    subtasks = generate_development_tasks(requirement)
    
    created_task_keys = []
    task_data_map = {}
    
    if subtasks:
        # Step 4: Display generated subtasks
        print("\nGemini returned the following subtasks:")
        for idx, task in enumerate(subtasks, start=1):
            print(f"{idx}. {task['title']}: {task['summary']}")
        
        # Step 5: Create Jira tickets for each subtask and link them to parent
        print("\nCreating Jira tickets for each subtask and linking them to parent...")
        created_task_keys, task_data_map = create_linked_subtasks(parent_key, subtasks)
    else:
        print("No subtasks generated by Gemini API.")
    
    # Step 6: Generate and create test cases for each development task
    if created_task_keys:
        print(f"\nCreating Test Case Subtasks for {len(created_task_keys)} tasks")
        for task_key in created_task_keys:
            task_data = task_data_map.get(task_key)
            if task_data:
                print(f"\nProcessing task {task_key}: {task_data['title']}")
                test_case_subtasks = generate_and_create_test_cases(task_data['summary'], task_key)
                print(f"Created {len(test_case_subtasks)} test case subtasks for {task_key}")
                time.sleep(2)  # Delay between processing tasks
            else:
                print(f"Could not find task data for {task_key}, skipping test case generation")
    
    # Step 7: Display all visible tickets in the project (to confirm creation)
    fetch_visible_tickets()
