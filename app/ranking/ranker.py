def rank_response(responses):
    
    scored = []

    for r in responses:
        score = len(r)
        
        scored.append(
            (score, r)
        )

    scored.sort(reverse=True)

    return scored[0][1]