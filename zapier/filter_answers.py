input_data= {} 

# The following code snippet is designed for integration with Zapier workflows.
import requests, json

# Global list of customer emails who prefer line-list invoices
LINE_LIST_CUSTOMERS = input_data.get('LINE_LIST_CUSTOMERS', '{}')
# Global variable of product ids 
PRODUCT_IDS = json.loads(input_data.get('PRODUCT_IDS', '{}'))

def get_submission_by_id():
    """
    Fetch a specific submission from JotForm API using the submission ID.
    
    Returns:
        dict: The submission data or error message.
    """
    url = f"https://api.jotform.com/submission/{input_data['SUBMISSION_ID']}"
    headers = {'APIKEY': input_data['API_KEY']}
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Raises an HTTPError for bad responses
    except requests.exceptions.RequestException as e:
        return {
            'error': 'RequestException',
            'message': str(e)
        }
    
    try:
        return response.json()
    except ValueError:
        return {
            'error': 'JSONDecodeError',
            'message': 'Response is not valid JSON'
        }


def filter_answers(submission: dict) -> dict:
    """
    Extract the 'answers' field from the given submission.

    Args:
        submission (dict): A dictionary representing a form submission that should contain
                           a 'content' key with either a list or a dictionary that holds 'answers'.

    Returns:
        dict: The extracted answers, or an empty dict if not found.
    """
    if 'content' in submission:
        answers = submission['content']
        if isinstance(answers, list):
            return answers[0].get('answers', {}) if answers else {}
        return answers.get('answers', {})
    return {}


def filter_endpoints_with_answer(answers: dict[str, object]) -> dict[str, object]:
    """
    Filter the endpoints within answers that contain the "answer" field.

    Args:
        answers (dict[str, object]): A dictionary of answers to be filtered.

    Returns:
        dict[str, object]: Filtered endpoints containing the "answer" field.
    """
    return {
        key: value
        for key, value in answers.items()
        if isinstance(value, dict) and "answer" in value
    }


def filter_email_and_salesrep(answers: dict[str, dict]) -> tuple[str, str]:
    """
    Extract both the email and sales representative values from answers in a single pass.

    Args:
        answers (dict[str, dict]): The dictionary of answers, where each value is expected
                                   to be a dictionary with keys like 'type' and 'answer'.

    Returns:
        tuple[str, str]: A tuple (email, sales_rep), where each element is a string.
                        Returns empty strings if not found.
    """
    email = ""
    sales_rep = ""
    for value in answers.values():
        control_type = value.get("type")
        if control_type == "control_email" and not email:
            email = value.get("answer", "").strip().lower()
        elif control_type == "control_dropdown" and not sales_rep:
            sales_rep = value.get("answer", "")
        # Break early if both values have been found
        if email and sales_rep:
            break
    return email, sales_rep


def filter_type_control_matrix(answers: dict[str, dict]) -> dict[str, dict]:
    """
    Filter the fields within answers that have the type 'control_matrix'.

    Args:
        answers (dict[str, dict]): A dictionary of answer fields to be filtered.

    Returns:
        dict[str, dict]: Filtered fields that are of type 'control_matrix'.
    """
    return {key: value for key, value in answers.items() if value.get("type") == "control_matrix"}


def split_mrows_values(answers: dict[str, dict]) -> dict[str, dict]:
    """
    Split the 'mrows' field by '|' in each endpoint and replace it with the list of split values.

    Args:
        answers (dict[str, dict]): A dictionary of answers to process, where each value represents an endpoint 
                                   that might contain an 'mrows' field.

    Returns:
        dict[str, dict]: The updated answers, where each 'mrows' string is replaced with a list of values.
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
        list: A list of all extracted text values before the dash,
              repeated for each answer in the corresponding 'answer' list.
    """
    return [
        txt.split('-', 1)[0].strip()
        for data in filtered_answers.values()
        if '-' in (txt := data.get('text', ''))
        for _ in range(len(data.get('answer', [])))
    ]


def filter_empty_quantities(all_descriptions, all_quantities, all_product_codes):
    """
    Filter out empty or non-numeric values in all_quantities 
    and remove corresponding entries from all_descriptions and all_product_codes.

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
        try:
            # Attempt to convert to a float, if successful, keep the row
            if isinstance(quantity, (int, float)) or (isinstance(quantity, str) and quantity.isdigit()):
                filtered_descriptions.append(description)
                filtered_quantities.append(quantity)
                filtered_product_codes.append(product_code)
        except ValueError:
            # If conversion fails, simply skip this row
            continue

    return filtered_descriptions, filtered_quantities, filtered_product_codes

def map_product_codes_to_ids(product_codes):
    """
    Map product codes to product ids using a default value for missing codes.

    Args:
        product_codes (list): A list of product codes.

    Returns:
        list: A list of product ids corresponding to the product codes.
              If a code doesn't exist in the dictionary, the default id "2215" is used.
    """
    return [PRODUCT_IDS.get(code, "2215") for code in product_codes]


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
    submission = get_submission_by_id()
    
    # Check if the input or content is missing
    if not input_data or 'content' not in submission:
        return {"email": "", "sales_rep":"", "all_descriptions": [], "all_quantities": [], "all_product_ids": []}

    # Extract the answers field
    answers = filter_answers(submission)

    # Filter endpoints that contains field "answer"
    answers_with_field = filter_endpoints_with_answer(answers)

    # Extract the email and sales rep
    email, sales_rep = filter_email_and_salesrep(answers_with_field)
    
    # Filter endpoints that contains field type "control_matrix" (tables)
    control_matrix_type = filter_type_control_matrix(answers_with_field)

    # Split "mrows" values separated by '|'
    split_mrows_endpoints = split_mrows_values(control_matrix_type)

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
    # Converting product codes into product ids
    all_product_ids = map_product_codes_to_ids(all_product_codes)

    if email not in LINE_LIST_CUSTOMERS:
        # Creating bulk order
        bulk_descriptions, bulk_quantities, bulk_product_ids = create_bulk_order(
        all_descriptions, all_quantities, all_product_ids)

        # Return the final result (bulk order)
        return {
        "email": email,
        "sales_rep": sales_rep,
        "all_descriptions": bulk_descriptions,
        "all_quantities": bulk_quantities,
        "all_product_ids": bulk_product_ids
    }

    # Return the final result (line list)
    return {
        "email": email,
        "sales_rep": sales_rep,
        "all_descriptions": all_descriptions,
        "all_quantities": all_quantities,
        "all_product_ids": all_product_ids
    }

output = process_submission(input_data)
