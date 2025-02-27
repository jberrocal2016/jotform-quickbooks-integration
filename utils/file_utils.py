import json, os

# Define the directory where JSON files will be saved
JSON_DIR = 'json_files'

def ensure_directory_exists(directory):
    """
    Ensure that the specified directory exists.
    
    Args:
        directory (str): The path of the directory to check and create if it doesn't exist.
    """
    if not os.path.exists(directory):
        os.makedirs(directory)

def get_json_file_path(filename):
    """
    Get the full file path for a JSON file.
    
    Args:
        filename (str): The name of the JSON file.
    
    Returns:
        str: The full file path.
    """
    return os.path.join(JSON_DIR, filename)

def save_to_json_file(data, filename): 
    """
    Save the provided data to a JSON file.

    Args:
        data (dict): The data to save.
        filename (str): The name of the file to save the data to.
    """
    # Ensure the directory for the file exists
    ensure_directory_exists(JSON_DIR)
    
    # Get the full file path
    file_path = get_json_file_path(filename)
    
    with open(file_path, 'w') as json_file:
        json.dump(data, json_file, indent=4)
