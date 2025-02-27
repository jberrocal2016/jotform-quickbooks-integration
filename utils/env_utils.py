import os
from dotenv import load_dotenv

def load_environment_variables():
    """Load environment variables from a .env file."""
    load_dotenv()

def get_env_variable(var_name, default_value=None):
    """
    Get the value of the environment variable or return the default value.
    Args:
        var_name (str): The name of the environment variable.
        default_value (any, optional): The default value to return if the variable is not found.
    
    Returns:
        str: The value of the environment variable or the default value.
    """
    return os.getenv(var_name, default_value)
