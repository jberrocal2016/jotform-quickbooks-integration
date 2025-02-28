def filter_submission_answers(submission, field):    
    """
    Filter submission answers based on the specified field.
    
    Args:
        submission (dict): The submission data.
        field (str): The field to filter answers by.
    
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

            # Filter answers based on the field
            for key, value in answers.items():
                if field in value:
                    filtered_answers[key] = value
    
    # Sort the filtered_answers by the "order" field
    sorted_answers = dict(sorted(filtered_answers.items(), key=lambda item: int(item[1].get("order", 0))))
    
    return sorted_answers
