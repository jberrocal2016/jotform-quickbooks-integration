def filter_submission_answers(submission, subendpoint):    
    """
    Filter submission answers based on the specified subendpoint.
    
    Args:
        submission (dict): The submission data.
        subendpoint (str): The subendpoint to filter answers by.
    
    Returns:
        dict: The filtered answers.
    """
    filtered_answers = {}

    # Check if the submission contains content
    if 'content' in submission:
        submissions = submission['content']

        # Ensure there is at least one submission
        if len(submissions) > 0:
            answers = submissions[0].get('answers', {})

            # Filter answers based on the subendpoint
            for key, value in answers.items():
                if subendpoint in value:
                    filtered_answers[key] = value
    
    return filtered_answers
