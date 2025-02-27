from utils.env_utils import load_environment_variables, get_env_variable

# Load environment variables
load_environment_variables()

QUICKBOOKS_API_KEY = get_env_variable('QUICKBOOKS_API_KEY')

def send_to_quickbooks(data):
    # Use QUICKBOOKS_API_KEY in your API request
    # Your existing implementation
    pass
