from api_handlers.jotform_api import get_latest_submission, get_submission_by_id
#from api_handlers.quickbooks_api import send_to_quickbooks
from filters.submission_filter import filter_submission_answers
from utils.file_utils import save_to_json_file, save_custom_data_to_text_file

def main():
    """
    Main function to load environment variables, fetch the latest submission,
    filter the answers, and save them to a JSON file.
    """
        
    # Fetch the latest submission from JotForm
    #submission = get_latest_submission()

    # Fetch submission by ID from JotForm
    submission_ID = input("Please enter the submission ID: ")
    submission = get_submission_by_id(submission_ID)
    
    # Check for errors in the submission response
    if 'error' in submission:
        print(f"Error {submission['error']}: {submission['message']}")
    else:
        # Filter the answers based on the field 'answer'
        field = 'answer'
        filtered_answers = filter_submission_answers(submission, field)

        # Save the filtered answers to a JSON file
        save_to_json_file(filtered_answers, 'filtered_answers.json')
        save_custom_data_to_text_file(filtered_answers, 'filtered_anwers.txt')
        print('Filtered answers have been saved to filtered_answers.json')

        #send_to_quickbooks(filtered_answers)

if __name__ == "__main__":
    main()
