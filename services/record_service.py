import json
from models.db import db
from models.record_model import AssessmentRecord, ReportRecord


def save_assessment_and_report(user_id, raw_data, result_data):
    assessment = AssessmentRecord(
        user_id=user_id,
        academic_json=json.dumps(raw_data.get("academic", {}), ensure_ascii=False),
        consumption_json=json.dumps(raw_data.get("consumption", {}), ensure_ascii=False),
        health_json=json.dumps(raw_data.get("health", {}), ensure_ascii=False),
        psychology_json=json.dumps(raw_data.get("psychology", {}), ensure_ascii=False),
        future_json=json.dumps(raw_data.get("future", {}), ensure_ascii=False),

        academic_score=result_data["academic_score"],
        consumption_score=result_data["consumption_score"],
        health_score=result_data["health_score"],
        psychology_score=result_data["psychology_score"],
        overall_score=result_data["overall_score"],

        future_similarity_score=result_data.get("future_score", 0),
        future_readiness_score=result_data.get("future_readiness_score", 0),
    )

    db.session.add(assessment)
    db.session.flush()

    report = ReportRecord(
        assessment_id=assessment.id,
        overall_summary_text=result_data["overall_summary_text"],
        academic_report_text=result_data["academic_report_text"],
        consumption_report_text=result_data["consumption_report_text"],
        health_report_text=result_data["health_report_text"],
        psychology_report_text=result_data["psychology_report_text"],
        combo_report_text=result_data["combo_report_text"],
        future_report_text=result_data.get("future_report_text", "暂无未来发展文字报告。"),
    )

    db.session.add(report)
    db.session.commit()

    return assessment