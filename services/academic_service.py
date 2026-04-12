ACADEMIC_WEIGHTS = {
    "gpa": 0.190311,
    "average_score": 0.132255,
    "rank_percent": 0.091554,
    "fail_rate": 0.035895,
    "pass_rate": 0.089601,
    "focus_hours": 0.069141,
    "study_plan": 0.041916,
    "note_quality": 0.028188,
    "review_freq": 0.024174,
    "research_participation": 0.109309,
    "competition_result": 0.088389,
    "lecture_frequency": 0.048258,
    "elective_difficulty": 0.051006,
}


def clamp(value, low=0, high=100):
    return max(low, min(high, value))


def score_gpa(gpa):
    return clamp((gpa / 4.0) * 100)


def score_average_score(avg):
    return clamp(avg)


def score_rank_percent(rank_percent):
    return clamp(101 - rank_percent)


def score_fail_rate(fail_rate):
    return clamp(100 - fail_rate)


def score_pass_rate(pass_rate):
    return clamp(pass_rate)


def score_focus_hours(hours):
    return clamp((hours / 40.0) * 100)


def score_direct(value):
    return clamp(value)


def score_binary(value):
    return 100 if int(value) == 1 else 40


def calculate_academic_score(data: dict) -> dict:
    subscores = {
        "gpa": score_gpa(data["gpa"]),
        "average_score": score_average_score(data["average_score"]),
        "rank_percent": score_rank_percent(data["rank_percent"]),
        "fail_rate": score_fail_rate(data["fail_rate"]),
        "pass_rate": score_pass_rate(data["pass_rate"]),
        "focus_hours": score_focus_hours(data["focus_hours"]),
        "study_plan": score_direct(data["study_plan"]),
        "note_quality": score_direct(data["note_quality"]),
        "review_freq": score_direct(data["review_freq"]),
        "research_participation": score_binary(data["research_participation"]),
        "competition_result": score_direct(data["competition_result"]),
        "lecture_frequency": score_direct(data["lecture_frequency"]),
        "elective_difficulty": score_direct(data["elective_difficulty"]),
    }

    score = sum(subscores[k] * ACADEMIC_WEIGHTS[k] for k in ACADEMIC_WEIGHTS)
    score = round(clamp(score), 1)

    return {
        "score": score,
        "level": score_to_level(score),
        "module": "academic",
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