import requests
from utils.env_utils import load_environment_variables, get_env_variable

# Load environment variables
load_environment_variables()

# Retrieve API key and form ID from environment variables
API_KEY = get_env_variable('API_KEY')
FORM_ID = get_env_variable('FORM_ID')

def get_latest_submission():
    """
    Fetch the latest submission from JotForm API.
    
    Returns:
        dict: The latest submission or error message.
    """
    url = f"https://api.jotform.com/form/{FORM_ID}/submissions"
    headers = {
        'APIKEY': API_KEY,
    }
    params = {
        'limit': 1,
        'orderby': 'created_at'
    }

    # Send the GET request to JotForm API
    response = requests.get(url, headers=headers, params=params)
    
    # Check if the response status code indicates an error
    if response.status_code != 200:
        return {
            'error': response.status_code,
            'message': response.text
        }
    
    # Return the JSON response
    return response.json()

