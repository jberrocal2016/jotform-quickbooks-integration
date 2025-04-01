input_data= {} # Not part of zapier integration

# The following code snippet is designed for integration with Zapier workflows.
import json

# Global list of customer emails who prefer line-list invoices
LINE_LIST_CUSTOMERS = input_data.get('LINE_LIST_CUSTOMERS', '{}')

def extract_answers(submission):
    """Extract the 'answers' field from the given submission."""
    if 'content' in submission:
        submissions = submission['content']
        return (submissions[0].get('answers', {}) 
                if isinstance(submissions, list) 
                else submissions.get('answers', {}))
    return {}

def filter_endpoints_with_field(answers, field):
    """
    Filter the endpoints within answers that contain a specific field.

    Args:
        answers (dict): A dictionary of answers to be filtered.
        field (str): The field name to filter by.

    Returns:
        dict: Filtered answers containing the specified field.
    """
    return {key: value for key, value in answers.items() if field in value}

def extract_email(answers):
    """Extract the value in the email field by identifying the 'control_email' type."""
    for key, value in answers.items():
        if value.get("type") == "control_email":
            return value.get("answer", "")
    return ""

def filter_endpoints_by_type(answers, type_value):
    """
    Filter the endpoints within answers based on a specific type.

    Args:
        answers (dict): A dictionary of answers to be filtered.
        type_value (str): The type value to filter by.

    Returns:
        dict: Filtered answers matching the specified type.
    """
    return {key: value for key, value in answers.items() if value.get('type') == type_value}

def split_mrows_values(answers):
    """
    Split the 'mrows' field by '|' in each endpoint and replace it with the split values.

    Args:
        answers (dict): A dictionary of answers to process.

    Returns:
        dict: Updated answers with split 'mrows' values.
    """
    for key, value in answers.items():
        if 'mrows' in value and value['mrows']:
            value['mrows'] = value['mrows'].split('|')
    return answers

def flatten_answers_and_duplicate_mrows(answers):
    """
    Flatten the 'answer' field and handle duplication of 'mrows' to match the flattened answers.

    Args:
        answers (dict): A dictionary of answers to process.

    Returns:
        dict: Updated answers with flattened answers and duplicated mrows.
    """
    for key, value in answers.items():
        if 'answer' in value:
            # Flatten the answers
            flattened_answer = []
            duplicated_mrows = []
            
            if isinstance(value['answer'], list):
                for i, item in enumerate(value['answer']):
                    current_mrow = value['mrows'][i] if i < len(value['mrows']) else ''
                    if isinstance(item, list):  # Handle nested lists
                        flattened_answer.extend(item)
                        duplicated_mrows.extend([current_mrow] * len(item))
                    else:
                        flattened_answer.append(item)
                        duplicated_mrows.append(current_mrow)
            else:
                flattened_answer = [value['answer']]
                duplicated_mrows = value['mrows']
            
            # Update the values
            value['answer'] = flattened_answer
            value['mrows'] = duplicated_mrows
    return answers

def sort_by_order(data):
    """Sort a dictionary's values by the 'order' field."""
    return dict(sorted(data.items(), key=lambda item: int(item[1].get('order', float('inf')))))

def combine_descriptions_and_quantities(sorted_dict):
    """
    Combine all 'mrows' and 'answer' fields from the sorted dictionary into separate lists.

    Args:
        sorted_dict (dict): A sorted dictionary of filtered answers.

    Returns:
        tuple: Two lists - one containing all 'mrows' (descriptions) and the other containing all 'answers' (quantities).
    """
    all_descriptions = []
    all_quantities = []
    for item in sorted_dict.values():
        all_descriptions.extend(item.get("mrows", []))
        all_quantities.extend(item.get("answer", []))
    return all_descriptions, all_quantities

def extract_text_before_dash(filtered_answers):
    """
    Extract the part of the 'text' field (product code) before the '-' character.

    Args:
        filtered_answers (dict): The filtered answers dictionary.

    Returns:
        list: A list of all extracted text values before the dash.
    """
    all_product_codes = []
    for key, value in filtered_answers.items():
        text = value.get('text', '')
        answers = value.get('answer', [])

        if '-' in text:
            # Split the text at '-' and take the first part (before the dash)
            trimmed_text = text.split('-')[0].strip()
            repeated_text = [trimmed_text] * len(answers)
            all_product_codes.extend(repeated_text)
    return all_product_codes

def filter_empty_quantities(all_descriptions, all_quantities, all_product_codes):
    """
    Filter out empty values in all_quantities and remove corresponding entries 
    from all_descriptions and all_product_codes.

    Args:
        all_descriptions (list): List of descriptions.
        all_quantities (list): List of quantities.
        all_product_codes (list): List of product codes.

    Returns:
        tuple: Filtered lists of descriptions, quantities, and product codes.
    """
    filtered_descriptions = []
    filtered_quantities = []
    filtered_product_codes = []

    for description, quantity, product_code in zip(all_descriptions, all_quantities, all_product_codes):
        if quantity:  # Only keep rows where the quantity is not empty
            filtered_descriptions.append(description)
            filtered_quantities.append(quantity)
            filtered_product_codes.append(product_code)

    return filtered_descriptions, filtered_quantities, filtered_product_codes

def create_bulk_order(all_descriptions, all_quantities, all_product_codes):
    """
    Create a bulk order by grouping items with the same product code and summing quantities.
    Extract the common part of all descriptions to form the bulk description.

    Args:
        all_descriptions (list): List of detailed descriptions.
        all_quantities (list): List of quantities.
        all_product_codes (list): List of product codes.

    Returns:
        tuple: Three lists - bulk product codes, bulk descriptions, and bulk total quantities.
    """
    from os.path import commonprefix

    # Group items by product code
    grouped_items = {}
    for product_code, quantity, description in zip(all_product_codes, all_quantities, all_descriptions):
        if product_code not in grouped_items:
            grouped_items[product_code] = {'descriptions': [], 'total_quantity': 0}
        grouped_items[product_code]['descriptions'].append(description)
        grouped_items[product_code]['total_quantity'] += int(quantity)

    # Prepare the output lists
    bulk_product_codes = []
    bulk_descriptions = []
    bulk_quantities = []

    for product_code, data in grouped_items.items():
        descriptions = data['descriptions']
        total_quantity = data['total_quantity']

        # Extract the common prefix from descriptions
        bulk_description = commonprefix(descriptions).strip()

        # Add to the output lists
        bulk_product_codes.append(product_code)
        bulk_descriptions.append(bulk_description)
        bulk_quantities.append(total_quantity)

    return bulk_descriptions, bulk_quantities, bulk_product_codes

def process_submission(input_data):
    """
    Process the input JSON data to filter, sort, and return combined results.

    Args:
        input_data (dict): A dictionary containing JSON data to be processed.

    Returns:
        dict: A dictionary containing email, all_descriptions, all_quantities, and all_product_codes.
    """
    # Parse the JSON data
    submission = json.loads(input_data.get('data', '{}'))
    
    # Check if the input or content is missing
    if not input_data or 'content' not in submission:
        return {"email": "", "all_descriptions": [], "all_quantities": [], "all_product_codes": []}

    # Extract the answers field
    answers = extract_answers(submission)

    # Filter endpoints with the field "answer"
    answers_with_field = filter_endpoints_with_field(answers, 'answer')

    # Extract the email value
    email = extract_email(answers_with_field).strip().lower()

    # Filter endpoints with type "control_matrix"
    control_matrix_endpoints = filter_endpoints_by_type(answers_with_field, 'control_matrix')

    # Split "mrows" values separated by '|'
    split_mrows_endpoints = split_mrows_values(control_matrix_endpoints)

    # Flatten "answer" values and handle duplication of "mrows"
    flattened_endpoints = flatten_answers_and_duplicate_mrows(split_mrows_endpoints)

    # Sort the filtered endpoints by "order"
    sorted_answers = sort_by_order(flattened_endpoints)

    # Combine descriptions and quantities
    all_descriptions, all_quantities = combine_descriptions_and_quantities(sorted_answers)

    # Extract all product codes
    all_product_codes = extract_text_before_dash(sorted_answers)

    # Filter out empty quantities and corresponding rows
    all_descriptions, all_quantities, all_product_codes = filter_empty_quantities(
    all_descriptions, all_quantities, all_product_codes
)  
    if email not in LINE_LIST_CUSTOMERS:
        # Creating bulk order
        bulk_descriptions, bulk_quantities, bulk_product_codes = create_bulk_order(
        all_descriptions, all_quantities, all_product_codes)

        # Return the final result (bulk order)
        return {
        "email": email,
        "all_descriptions": bulk_descriptions,
        "all_quantities": bulk_quantities,
        "all_product_codes": bulk_product_codes
    }


    # Return the final result (line list)
    return {
        "email": email,
        "all_descriptions": all_descriptions,
        "all_quantities": all_quantities,
        "all_product_codes": all_product_codes
    }

output = process_submission(input_data)
