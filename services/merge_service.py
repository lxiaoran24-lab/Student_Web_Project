from services.report_service import build_text_report


def merge_all_results(record_id, academic_result, consumption_result, health_result, psychology_result, future_result):
    overall_score = round(
        (
            academic_result["score"] +
            consumption_result["score"] +
            health_result["score"] +
            psychology_result["score"]
        ) / 4,
        1
    )

    report_text = build_text_report(
        overall_score=overall_score,
        academic_score=academic_result["score"],
        consumption_score=consumption_result["score"],
        health_score=health_result["score"],
        psychology_score=psychology_result["score"],
    )

    return {
        "record_id": record_id,
        "overall_score": overall_score,

        "academic_score": academic_result["score"],
        "consumption_score": consumption_result["score"],
        "health_score": health_result["score"],
        "psychology_score": psychology_result["score"],

        "future_score": float(future_result.get("score", 0)),
        "future_readiness_score": float(future_result.get("readiness_score", 0)),
        "future_details": future_result.get("details", []),
        "future_report_text": future_result.get("future_report_text", "暂无未来发展文字报告。"),
        "career_recommendations": future_result.get("career_recommendations", []),
        "target_category_name": future_result.get("target_category_name", "未知门类"),

        "summary": build_summary(
            overall_score,
            academic_result,
            consumption_result,
            health_result,
            psychology_result
        ),

        "overall_summary_text": report_text["overall_summary"],
        "academic_report_text": report_text["academic_report"],
        "consumption_report_text": report_text["consumption_report"],
        "health_report_text": report_text["health_report"],
        "psychology_report_text": report_text["psychology_report"],
        "combo_report_text": report_text["combo_report"],
        "academic_grade": report_text["academic_grade"],
        "psych_grade": report_text["psych_grade"],
    }


def build_summary(overall_score, academic_result, consumption_result, health_result, psychology_result):
    parts = [
        f"综合得分为 {overall_score} 分。",
        f"学业：{academic_result['level']}（{academic_result['score']}）",
        f"消费：{consumption_result['level']}（{consumption_result['score']}）",
        f"身体：{health_result['level']}（{health_result['score']}）",
        f"心理：{psychology_result['level']}（{psychology_result['score']}）",
    ]
    return " ".join(parts)