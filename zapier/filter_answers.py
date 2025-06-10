input_data= {} 

# The following code snippet is designed for integration with Zapier workflows.
import requests, json

# Jotform Credentials
SUBMISSION_ID = input_data['SUBMISSION_ID']
API_KEY = input_data['API_KEY']

# product_ids-table
PRODUCT_CODES = input_data.get('PRODUCT_CODES', '{}').split(',')
PRODUCT_IDS = input_data.get('PRODUCT_IDS', '{}').split(',')
PRODUCT_DICT = dict(zip(PRODUCT_CODES, PRODUCT_IDS))

# line_list_customers-table
LINE_LIST_CUSTOMERS = [customer.lower() for customer in input_data.get('LINE_LIST_CUSTOMERS', '').split(',') if customer]

# client_ids-table
CLIENT_ID = input_data.get('CLIENT_ID', "1754")  # Default ID 1754


def get_submission_by_id():
    """
    Fetch a specific submission from JotForm API using the submission ID.

    Returns:
        dict: The submission data or an error message.
    """
    url = f"https://api.jotform.com/submission/{SUBMISSION_ID}"
    headers = {'APIKEY': API_KEY}

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


def filter_submission(submission: dict) -> dict:
    """
    Extract the 'answers' field from the submission and filter endpoints that contain the "answer" field.
    """
    # Extract answers field
    if 'content' in submission:
        answers_data = submission['content']
        if isinstance(answers_data, list):
            answers = answers_data[0].get('answers', {}) if answers_data else {}
        else:
            answers = answers_data.get('answers', {})
    else:
        answers = {}

    # Filter endpoints with "answer" field
    filtered_endpoints = {
        key: value
        for key, value in answers.items()
        if isinstance(value, dict) and "answer" in value
    }
    return filtered_endpoints


def sort_by_order(data: dict) -> dict:
    """
    Sort a dictionary's values based on the 'order' field.
    """
    return dict(sorted(data.items(), key=lambda item: int(item[1].get('order', float('inf')))))


def filter_answers_by_type(answers: dict, target_type: str, single: bool = True, extract: bool = True, require_list_answer: bool = False) -> dict:
    """
    Filter `answers` for entries matching `target_type`.  

    - If `require_list_answer` is True, we additionally demand that
      the `"answer"` field is a Python list (not a string or HTML blob).  
    - If `extract` is True, we return just the answer value;  
      otherwise we return the full entry so you can still see its keys.  
    - If `single` is True, we stop on the first match;  
      set it False to gather _all_ matches.
    """
    filtered = {}
    for key, value in answers.items():
        if value.get("type") != target_type:
            continue

        ans = value.get("answer", "")
        if require_list_answer and not isinstance(ans, list):
            continue

        # good block
        filtered[key] = ans if extract else value
        if single:
            break

    return filtered


def split_mrows_values(answers: dict) -> dict:
    """
    Split the 'mrows' field by '|' in each endpoint.
    """
    for key, value in answers.items():
        if 'mrows' in value and value['mrows']:
            value['mrows'] = value['mrows'].split('|')
    return answers


def flatten_answers_and_duplicate_mrows(answers: dict) -> dict:
    """
    Flatten the 'answer' field and duplicate 'mrows', ensuring they align.
    """
    for key, value in answers.items():
        if 'answer' in value:
            flattened_answer = []
            duplicated_mrows = []

            if isinstance(value['answer'], list):
                for i, item in enumerate(value['answer']):
                    current_mrow = value['mrows'][i] if i < len(value.get('mrows', [])) else ''
                    if isinstance(item, list):  # In case of nested lists
                        flattened_answer.extend(item)
                        duplicated_mrows.extend([current_mrow] * len(item))
                    else:
                        flattened_answer.append(item)
                        duplicated_mrows.append(current_mrow)
            else:
                flattened_answer = [value['answer']]
                duplicated_mrows = value['mrows']

            value['answer'] = flattened_answer
            value['mrows'] = duplicated_mrows
    return answers


def combine_descriptions_and_quantities(flattened_endpoints: dict) -> tuple:
    """
    Combine all 'mrows' (descriptions) and 'answer' (quantities) fields from the sorted endpoints.
    """
    all_descriptions = []
    all_quantities = []
    for item in flattened_endpoints.values():
        all_descriptions.extend(item.get("mrows", []))
        all_quantities.extend(item.get("answer", []))
    return all_descriptions, all_quantities


def extract_text_before_dash(flattened_endpoints: dict) -> list:
    """
    Extract the part of the 'text' value (usually a product code) before the '-' character,
    repeated for each corresponding answer.
    """
    result = []
    for data in flattened_endpoints.values():
        txt = data.get('text', '')
        if '-' not in txt:
            continue
        product_code = txt.split('-', 1)[0].strip()
        count = len(data.get('answer', []))
        # Duplicate the product code 'count' times
        result.extend([product_code] * count)
    return result


def filter_out_empty_quantities(all_descriptions: list, all_quantities: list, all_product_codes: list) -> tuple:
    """
    Remove rows that have non-numeric or empty quantity values.
    """
    filtered_descriptions = []
    filtered_quantities = []
    filtered_product_codes = []

    for description, quantity, product_code in zip(all_descriptions, all_quantities, all_product_codes):
        try:
            num = float(quantity)
            filtered_descriptions.append(description)
            filtered_quantities.append(num)
            filtered_product_codes.append(product_code)
        except (ValueError, TypeError):
            continue

    return filtered_descriptions, filtered_quantities, filtered_product_codes


def map_product_codes_to_ids(product_codes: list, default_id: str = "2215") -> list:
    """
    Map product codes to product ids, using a default if not found.
    """
    return [PRODUCT_DICT.get(code, default_id) for code in product_codes]


def create_bulk_order(all_descriptions: list, all_quantities: list, all_product_ids: list) -> tuple:
    """
    Create a bulk order by grouping items with the same product id and summing their quantities.
    Also, extract the common base description.
    """
    grouped_items = {}
    for description, quantity, product_id in zip(all_descriptions, all_quantities, all_product_ids):
        if product_id not in grouped_items:
            grouped_items[product_id] = {"descriptions": [], "total_quantity": 0}
        grouped_items[product_id]["descriptions"].append(description)
        grouped_items[product_id]["total_quantity"] += float(quantity)

    bulk_descriptions = []
    bulk_quantities = []
    bulk_product_ids = []
    for product_id, data in grouped_items.items():
        descriptions = data["descriptions"]
        total_quantity = data["total_quantity"]

        if descriptions and '-' in descriptions[0]:
            bulk_description = descriptions[0].split('-', 1)[0].strip()
        else:
            bulk_description = descriptions[0] if descriptions else ''

        bulk_descriptions.append(bulk_description)
        bulk_quantities.append(total_quantity)
        bulk_product_ids.append(product_id)

    return bulk_descriptions, bulk_quantities, bulk_product_ids


def process_submission(input_data: dict) -> dict:
    """
    Process the submission by filtering, sorting, and organizing data.
    Depending on the email, return either a bulk order or a line list.
    """
    submission = get_submission_by_id()

    # Early exit if input or content is missing
    if not input_data or 'content' not in submission:
        return {
            "client_id": "",
            "email": "",
            "sales_rep": "",
            "all_descriptions": [],
            "all_quantities": [],
            "all_product_ids": []
        }

    # Process submission data
    answers = filter_submission(submission)
    answers = sort_by_order(answers)

    # Extract email from answers
    email_dict = filter_answers_by_type(answers, "control_email")
    email = next(iter(email_dict.values()), "").lower()

    # Extract sales_rep from answers
    sales_rep_dict = filter_answers_by_type(answers, "control_dropdown")
    sales_rep = next(iter(sales_rep_dict.values()), "")
    if sales_rep.upper() == "JOHN":
        sales_rep = "JE"

    # Filter endpoints containing tables from answers 
    tables = filter_answers_by_type(answers, "control_matrix", single=False, extract=False, require_list_answer=True)
    
    # Format tables
    split_mrows_endpoints = split_mrows_values(tables)
    flattened_endpoints = flatten_answers_and_duplicate_mrows(split_mrows_endpoints)
    
    all_descriptions, all_quantities = combine_descriptions_and_quantities(flattened_endpoints)
    
    all_product_codes = extract_text_before_dash(flattened_endpoints)
    all_descriptions, all_quantities, all_product_codes = filter_out_empty_quantities(
        all_descriptions, all_quantities, all_product_codes
    )
    all_product_ids = map_product_codes_to_ids(all_product_codes)

    # Decide whether to create a bulk order or use the line list based on the email.
    descriptions, quantities, product_ids = (
        create_bulk_order(all_descriptions, all_quantities, all_product_ids)
        if email not in LINE_LIST_CUSTOMERS
        else (all_descriptions, all_quantities, all_product_ids)
    )
    
    return {
        "client_id": CLIENT_ID,
        "email": email,
        "sales_rep": sales_rep,
        "all_descriptions": descriptions,
        "all_quantities": quantities,
        "all_product_ids": product_ids
    }


# Execute the processing of the submission
output = process_submission(input_data)
