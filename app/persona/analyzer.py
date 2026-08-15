

def analyzer_style(messages):
    total_length = 0
    question_count = 0

    for msg in messages:

        total_length += len(msg)

        if "?" in msg:
            question_count += 1

    avg_length = total_length / len(messages)
    question_rate = question_count / len(messages)

    return{
        "avg_length": avg_length,
        "question_rate": question_rate
    }        

    
