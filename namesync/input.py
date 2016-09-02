def get_answer(prompt, allowed=None, lowercase=False, default=None):
    answer = None
    while not answer or (allowed and answer not in allowed):
        answer = raw_input(prompt)
        answer = answer.strip()
        if lowercase:
            answer = answer.lower()
        if default:
            answer = answer or default
    return answer
