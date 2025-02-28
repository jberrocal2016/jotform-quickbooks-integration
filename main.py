from api_handlers.jotform_api import get_latest_submission
#from api_handlers.quickbooks_api import send_to_quickbooks
from filters.submission_filter import filter_submission_answers
from utils.file_utils import save_to_json_file

def main():
    """
    Main function to load environment variables, fetch the latest submission,
    filter the answers, and save them to a JSON file.
    """
        
    # Fetch the latest submission from JotForm
    latest_submission = get_latest_submission()
    
    # Check for errors in the submission response
    if 'error' in latest_submission:
        print(f"Error {latest_submission['error']}: {latest_submission['message']}")
    else:
        # Filter the answers based on the field 'answer'
        field = 'answer'
        filtered_answers = filter_submission_answers(latest_submission, field)

        # Save the filtered answers to a JSON file
        save_to_json_file(filtered_answers, 'filtered_answers.json')
        print('Filtered answers have been saved to filtered_answers.json')

        #send_to_quickbooks(filtered_answers)

if __name__ == "__main__":
    main()
