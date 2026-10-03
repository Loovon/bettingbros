"""
Context processor — injects bet slip count into every template.
Uses the session so anonymous users can also have a bet slip.
"""


def bet_slip_count(request) -> dict:
    """Returns the number of selections in the current bet slip."""
    slip = request.session.get('bet_slip', [])
    return {'bet_slip_count': len(slip)}
