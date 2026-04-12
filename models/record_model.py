from datetime import datetime
from models.db import db


class AssessmentRecord(db.Model):
    __tablename__ = "assessment_records"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # 原始输入（JSON 文本）
    academic_json = db.Column(db.Text, nullable=False)
    consumption_json = db.Column(db.Text, nullable=False)
    health_json = db.Column(db.Text, nullable=False)
    psychology_json = db.Column(db.Text, nullable=False)
    future_json = db.Column(db.Text, nullable=False)

    # 分数
    academic_score = db.Column(db.Float, nullable=False)
    consumption_score = db.Column(db.Float, nullable=False)
    health_score = db.Column(db.Float, nullable=False)
    psychology_score = db.Column(db.Float, nullable=False)
    overall_score = db.Column(db.Float, nullable=False)

    # 未来发展
    future_similarity_score = db.Column(db.Float, nullable=False, default=0)
    future_readiness_score = db.Column(db.Float, nullable=False, default=0)

    user = db.relationship("User", back_populates="assessment_records")
    report = db.relationship(
        "ReportRecord",
        back_populates="assessment",
        uselist=False,
        cascade="all, delete-orphan"
    )


class ReportRecord(db.Model):
    __tablename__ = "report_records"

    id = db.Column(db.Integer, primary_key=True)
    assessment_id = db.Column(db.Integer, db.ForeignKey("assessment_records.id"), nullable=False, unique=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    overall_summary_text = db.Column(db.Text, nullable=False)
    academic_report_text = db.Column(db.Text, nullable=False)
    consumption_report_text = db.Column(db.Text, nullable=False)
    health_report_text = db.Column(db.Text, nullable=False)
    psychology_report_text = db.Column(db.Text, nullable=False)
    combo_report_text = db.Column(db.Text, nullable=False)
    future_report_text = db.Column(db.Text, nullable=False)

    assessment = db.relationship("AssessmentRecord", back_populates="report")