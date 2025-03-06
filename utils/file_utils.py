import json, os

# Define the directory where JSON files will be saved
JSON_DIR = 'submission_files'

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

def save_custom_data_to_text_file(submission, filename):
    """
    Save specific fields in custom formats to a text file.

    Args:
        submission (dict): The submission data.
        filename (str): The name of the text file to save.
    """
    # Ensure the directory for the file exists
    ensure_directory_exists(JSON_DIR)
    
    # Get the full file path
    file_path = get_json_file_path(filename)

    with open(file_path, 'w', encoding='utf-8') as file:
        items = list(submission.items())  # Convert to list

        # Process the first 3 fields
        for key, value in items[:3]:  # Slice for the first 3 items
            text = value.get("text", "N/A")
            answer = value.get("answer", "N/A")
            file.write(f"{text}: {answer}\n")

        # Process the 4th field separately
        if len(items) > 3:  # Ensure there is a 4th field to process
            key, value = items[3]  # Get the 4th item
            text = value.get("text", "N/A")
            pretty_format = value.get("prettyFormat", "N/A")  # Custom formatting
            file.write(f"{text}: {pretty_format}\n")

        # Add an empty line after the top 4 fields
        file.write("\n")

        # Process the remaining fields
        for key, value in items[4:]:  # Iterate over items after the 4th

            # Split mrows into individual rows
            mrows = value.get("mrows", "N/A").split("|")  # Split by '|' delimiter

            # Flatten the nested answer list
            answers = [ans[0] if ans else "" for ans in value.get("answer", [])]  # Flatten answers

            # Extract the product code from the text field
            text = value.get("text", "N/A")
            product_code = text.split('-')[0] if '-' in text else ""

            # Pair mrows and answers together
            for description, quantity in zip(mrows, answers):
                # Only write rows with a non-empty answer
                if quantity.strip():  # Check if answer is not empty
                    file.write(f"{product_code} | {description.strip()} | {quantity.strip()}\n")
