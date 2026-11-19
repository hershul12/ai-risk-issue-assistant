from datetime import date


def calculate_score(probability: int, impact: int) -> int:
    return probability * impact


def get_priority(score: int) -> str:
    if score >= 20:
        return "Critical"
    if score >= 13:
        return "High"
    if score >= 6:
        return "Medium"
    return "Low"


def is_overdue(due_date: date, status: str) -> bool:
    return status != "Closed" and due_date < date.today()