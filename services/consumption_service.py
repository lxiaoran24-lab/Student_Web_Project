CONSUMPTION_WEIGHTS = {
    "living_fee": 0.449868,
    "rent": 0.037536,
    "food": 0.117108,
    "transport": 0.060855,
    "personal_care": 0.056115,
    "tuition": 0.076653,
    "office_supplies": 0.114978,
    "entertainment": 0.040539,
    "other_expense": 0.046344,
}


def clamp(value, low=0, high=100):
    return max(low, min(high, value))


def range_score(ratio, ideal_low, ideal_high, max_high):
    if ratio < ideal_low:
        return clamp((ratio / ideal_low) * 100) if ideal_low > 0 else 100
    if ideal_low <= ratio <= ideal_high:
        return 100
    if ratio > max_high:
        return 0
    return clamp((max_high - ratio) / (max_high - ideal_high) * 100)


def reverse_score(ratio, good_high, bad_high):
    if ratio <= good_high:
        return 100
    if ratio >= bad_high:
        return 0
    return clamp((bad_high - ratio) / (bad_high - good_high) * 100)


def calculate_consumption_score(data: dict) -> dict:
    income = max(data["living_fee"], 1)

    expense_total = (
        data["rent"] + data["food"] + data["transport"] + data["personal_care"] +
        data["tuition"] + data["office_supplies"] + data["entertainment"] + data["other_expense"]
    )

    surplus_ratio = (income - expense_total) / income
    if surplus_ratio >= 0.15:
        living_fee_score = 100
    elif surplus_ratio <= -0.30:
        living_fee_score = 0
    else:
        living_fee_score = clamp((surplus_ratio + 0.30) / 0.45 * 100)

    rent_ratio = data["rent"] / income
    food_ratio = data["food"] / income
    transport_ratio = data["transport"] / income
    personal_care_ratio = data["personal_care"] / income
    tuition_ratio = data["tuition"] / income
    office_ratio = data["office_supplies"] / income
    entertainment_ratio = data["entertainment"] / income
    other_ratio = data["other_expense"] / income

    subscores = {
        "living_fee": living_fee_score,
        "rent": range_score(rent_ratio, 0.00, 0.30, 0.50),
        "food": range_score(food_ratio, 0.10, 0.35, 0.55),
        "transport": range_score(transport_ratio, 0.02, 0.12, 0.25),
        "personal_care": range_score(personal_care_ratio, 0.01, 0.08, 0.20),
        "tuition": range_score(tuition_ratio, 0.00, 0.25, 0.50),
        "office_supplies": range_score(office_ratio, 0.01, 0.10, 0.25),
        "entertainment": reverse_score(entertainment_ratio, 0.12, 0.35),
        "other_expense": reverse_score(other_ratio, 0.08, 0.25),
    }

    score = sum(subscores[k] * CONSUMPTION_WEIGHTS[k] for k in CONSUMPTION_WEIGHTS)
    score = round(clamp(score), 1)

    return {
        "score": score,
        "level": score_to_level(score),
        "module": "consumption",
        "subscores": subscores
    }


def score_to_level(score: float) -> str:
    if score >= 90:
        return "优秀"
    elif score >= 80:
        return "良好"
    elif score >= 70:
        return "中等"
    elif score >= 60:
        return "待提升"
    return "需关注"