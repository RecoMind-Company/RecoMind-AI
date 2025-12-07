"""
Client for fetching team information from the backend API
"""
import requests
from config import settings


def fetch_company_teams(company_id: str) -> list:
    """
    Fetches the list of teams for a specific company from the backend API.
    
    Args:
        company_id: The company UUID to fetch teams for
        
    Returns:
        List of team names (strings): ["Sales", "Marketing", "HR", ...]
        
    Raises:
        ValueError: If company_id is missing
        Exception: If API call fails
    """
    if not company_id:
        raise ValueError("company_id is required to fetch teams")
    
    # Build the API URL with company_id
    api_url = settings.API_TEAMS_TEMPLATE.replace("{company_id}", company_id)
    
    print(f"Fetching teams from API for company: {company_id}...")
    
    try:
        # No authentication needed based on test results
        response = requests.get(api_url, timeout=30)
        response.raise_for_status()
        
        api_data = response.json()
        
        # API returns an array of objects: [{"id": "...", "name": "Sales"}, ...]
        # Extract only the team names
        if isinstance(api_data, list):
            team_names = [team.get("name") for team in api_data if team.get("name")]
            print(f"✔ Successfully fetched {len(team_names)} teams from API.")
            return team_names
        else:
            raise ValueError(f"Unexpected API response format. Expected list, got: {type(api_data)}")

    except requests.exceptions.HTTPError as http_err:
        print(f"✖ HTTP error occurred while fetching teams: {http_err}")
        try:
            print(f"✖ Server Response Body: {http_err.response.text}")
        except Exception:
            print("✖ Could not retrieve additional error details from the server response.")
        raise
    except Exception as e:
        print(f"✖ An unexpected error occurred while fetching teams: {e}")
        raise
