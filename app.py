from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_login import login_user, logout_user, login_required, current_user

import os
import uuid
import traceback

from models.db import init_extensions, db
from services.auth_service import create_user, authenticate_user
from services.r_bridge import run_health_model, run_psych_model
from services.academic_service import calculate_academic_score
from services.consumption_service import calculate_consumption_score
from services.similarity_service import calculate_major_similarity
from services.merge_service import merge_all_results

from services.future_service import build_future_result

app = Flask(__name__)
RESULT_CACHE = {}
app.secret_key = "your-secret-key"

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, "student_system.db")

app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{DB_PATH}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

init_extensions(app)

from models.user_model import User
from models.record_model import AssessmentRecord, ReportRecord

with app.app_context():
    db.create_all()

# =========================
# 基础工具函数
# =========================
def init_assessment_session():
    if "assessment_data" not in session:
        session["assessment_data"] = {
            "academic": {},
            "consumption": {},
            "health": {},
            "psychology": {},
            "future": {}
        }
        session.modified = True


def get_section_data(section_name: str) -> dict:
    init_assessment_session()
    return session["assessment_data"].get(section_name, {})


def save_section_data(section_name: str, field_names: list):
    init_assessment_session()
    section_data = {}
    for field in field_names:
        section_data[field] = request.form.get(field, "").strip()

    session["assessment_data"][section_name] = section_data
    session.modified = True


def to_float(value, default=0.0):
    try:
        if value is None or value == "":
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def to_int(value, default=0):
    try:
        if value is None or value == "":
            return default
        return int(float(value))
    except (TypeError, ValueError):
        return default


# =========================
# 健康模块：用户输入 -> 模型输入
# =========================
ACTIVITY_TYPE_MAP = {
    "几乎不运动": 0,
    "步行/散步": 1,
    "跑步/有氧": 2,
    "力量训练": 3,
    "球类运动": 4,
    "综合训练": 5,
}

INTENSITY_MAP = {
    "低": 1,
    "中": 2,
    "高": 3,
}

HEALTH_CONDITION_MAP = {
    "无明显问题": 0,
    "轻微问题": 1,
    "长期慢性问题": 2,
}

ENDURANCE_MAP = {
    "不达标": 5,
    "一般": 10,
    "良好": 15,
    "优秀": 17,
}


def calc_bmi(height_cm, weight_kg):
    if height_cm <= 0:
        return 0
    height_m = height_cm / 100
    return round(weight_kg / (height_m ** 2), 2)


def map_gender(gender_text):
    return 1 if gender_text == "男" else 0


def map_activity_type(activity_name):
    return ACTIVITY_TYPE_MAP.get(activity_name, 0)


def map_intensity(intensity_label):
    return INTENSITY_MAP.get(intensity_label, 1)


def estimate_calories_burned(duration_minutes, intensity_value, activity_type_value):
    intensity_base = {
        1: 4.0,
        2: 7.0,
        3: 10.0,
    }

    activity_factor = {
        0: 0.2,
        1: 0.8,
        2: 1.2,
        3: 1.1,
        4: 1.0,
        5: 1.15,
    }

    base = intensity_base.get(intensity_value, 4.0)
    factor = activity_factor.get(activity_type_value, 1.0)
    return round(duration_minutes * base * factor, 2)


def map_hydration_level(cups_per_day):
    if cups_per_day <= 3:
        return 1.5
    elif cups_per_day <= 6:
        return 2.5
    else:
        return 3.5


def map_smoking_status(smoking_text):
    return 1 if smoking_text == "是" else 0


def map_health_condition(condition_label):
    return HEALTH_CONDITION_MAP.get(condition_label, 0)


def map_endurance_level(endurance_status):
    return ENDURANCE_MAP.get(endurance_status, 10)


# =========================
# 通用页面
# =========================
@app.route("/")
def home():
    return render_template("home.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("history"))

    if request.method == "POST":
        username_or_email = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()

        user = authenticate_user(username_or_email, password)

        if not user:
            flash("用户名/邮箱或密码错误")
            return render_template("login.html")

        login_user(user)
        flash("登录成功")
        return redirect(url_for("history"))

    return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("history"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "").strip()

        user, error = create_user(username, email, password)

        if error:
            flash(error)
            return render_template("register.html")

        login_user(user)
        flash("注册成功，已自动登录")
        return redirect(url_for("history"))

    return render_template("register.html")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("你已退出登录")
    return redirect(url_for("home"))


from flask_login import login_required, current_user
from models.record_model import AssessmentRecord

@app.route("/history")
def history():
    return redirect(url_for("home"))


# =========================
# 评估流程入口
# =========================
@app.route("/assessment")
def assessment_start():
    init_assessment_session()
    return redirect(url_for("assessment_academic"))


@app.route("/assessment/reset")
def assessment_reset():
    session.pop("assessment_data", None)
    session.pop("latest_result_id", None)
    return redirect(url_for("assessment_academic"))


# =========================
# 第 1 步：学业模块
# =========================
@app.route("/assessment/academic", methods=["GET", "POST"])
def assessment_academic():
    field_names = [
        "gpa",
        "average_score",
        "rank_percent",
        "fail_rate",
        "focus_hours",
        "study_plan",
        "note_quality",
        "review_freq",
        "research_participation",
        "competition_result",
        "lecture_frequency",
        "elective_difficulty",
    ]

    if request.method == "POST":
        save_section_data("academic", field_names)
        return redirect(url_for("assessment_consumption"))

    data = get_section_data("academic")
    return render_template("assessment_academic.html", data=data)


# =========================
# 第 2 步：消费模块
# =========================
@app.route("/assessment/consumption", methods=["GET", "POST"])
def assessment_consumption():
    field_names = [
        "living_fee",
        "rent",
        "food",
        "transport",
        "personal_care",
        "office_supplies",
        "entertainment",
        "other_expense",
    ]

    if request.method == "POST":
        save_section_data("consumption", field_names)
        return redirect(url_for("assessment_health"))

    data = get_section_data("consumption")
    return render_template("assessment_consumption.html", data=data)


# =========================
# 第 3 步：身体模块
# =========================
@app.route("/assessment/health", methods=["GET", "POST"])
def assessment_health():
    field_names = [
        "age",
        "gender",
        "height_cm",
        "weight_kg",
        "activity_type_name",
        "exercise_days_per_week",
        "duration_minutes",
        "intensity_label",
        "daily_steps",
        "sleep_hours",
        "stress_level",
        "cups_per_day",
        "smoking_status_text",
        "health_condition_label",
        "endurance_status",
        "avg_heart_rate",
        "resting_heart_rate",
        "blood_pressure_systolic",
        "blood_pressure_diastolic",
    ]

    if request.method == "POST":
        save_section_data("health", field_names)
        return redirect(url_for("assessment_psychology"))

    data = get_section_data("health")
    return render_template("assessment_health.html", data=data)


# =========================
# 第 4 步：心理模块
# =========================
@app.route("/assessment/psychology", methods=["GET", "POST"])
def assessment_psychology():
    field_names = [
        "acad_stage_var",
        "peer_pressure",
        "home_pressure",
        "env_var",
        "cope_var",
        "habit_var",
        "compete_var",
    ]

    if request.method == "POST":
        save_section_data("psychology", field_names)
        return redirect(url_for("assessment_future"))

    data = get_section_data("psychology")
    return render_template("assessment_psychology.html", data=data)


# =========================
# 第 5 步：未来发展模块 + 最终提交
# =========================
@app.route("/assessment/future", methods=["GET", "POST"])
def assessment_future():
    field_names = [
        "current_major_code",
        "target_major_code",
    ]

    if request.method == "POST":
        try:
            save_section_data("future", field_names)

            all_data = session.get("assessment_data", {})
            academic_raw = all_data.get("academic", {})
            consumption_raw = all_data.get("consumption", {})
            health_raw = all_data.get("health", {})
            psychology_raw = all_data.get("psychology", {})
            future_raw = all_data.get("future", {})

            fail_rate = to_float(academic_raw.get("fail_rate", 0))
            academic_data = {
                "gpa": to_float(academic_raw.get("gpa", 0)),
                "average_score": to_float(academic_raw.get("average_score", 0)),
                "rank_percent": to_float(academic_raw.get("rank_percent", 100)),
                "fail_rate": fail_rate,
                "pass_rate": max(0.0, 100.0 - fail_rate),
                "focus_hours": to_float(academic_raw.get("focus_hours", 0)),
                "study_plan": to_float(academic_raw.get("study_plan", 0)),
                "note_quality": to_float(academic_raw.get("note_quality", 0)),
                "review_freq": to_float(academic_raw.get("review_freq", 0)),
                "research_participation": to_int(academic_raw.get("research_participation", 0)),
                "competition_result": to_float(academic_raw.get("competition_result", 0)),
                "lecture_frequency": to_float(academic_raw.get("lecture_frequency", 0)),
                "elective_difficulty": to_float(academic_raw.get("elective_difficulty", 0)),
            }

            consumption_data = {
                "living_fee": to_float(consumption_raw.get("living_fee", 0)),
                "rent": to_float(consumption_raw.get("rent", 0)),
                "food": to_float(consumption_raw.get("food", 0)),
                "transport": to_float(consumption_raw.get("transport", 0)),
                "personal_care": to_float(consumption_raw.get("personal_care", 0)),
                "tuition": 0.0,
                "office_supplies": to_float(consumption_raw.get("office_supplies", 0)),
                "entertainment": to_float(consumption_raw.get("entertainment", 0)),
                "other_expense": to_float(consumption_raw.get("other_expense", 0)),
            }

            age = to_float(health_raw.get("age", 0))
            gender_text = health_raw.get("gender", "")
            height_cm = to_float(health_raw.get("height_cm", 0))
            weight_kg = to_float(health_raw.get("weight_kg", 0))
            activity_type_name = health_raw.get("activity_type_name", "")
            exercise_days_per_week = to_float(health_raw.get("exercise_days_per_week", 0))
            duration_minutes = to_float(health_raw.get("duration_minutes", 0))
            intensity_label = health_raw.get("intensity_label", "")
            daily_steps = to_float(health_raw.get("daily_steps", 0))
            sleep_hours = to_float(health_raw.get("sleep_hours", 0))
            stress_level = to_float(health_raw.get("stress_level", 0))
            cups_per_day = to_float(health_raw.get("cups_per_day", 0))
            smoking_status_text = health_raw.get("smoking_status_text", "")
            health_condition_label = health_raw.get("health_condition_label", "")
            endurance_status = health_raw.get("endurance_status", "")

            gender_value = map_gender(gender_text)
            bmi_value = calc_bmi(height_cm, weight_kg)
            activity_type_value = map_activity_type(activity_type_name)
            intensity_value = map_intensity(intensity_label)

            adjusted_duration = duration_minutes * max(1, min(exercise_days_per_week, 7) / 3)

            calories_burned_value = estimate_calories_burned(
                adjusted_duration,
                intensity_value,
                activity_type_value
            )

            hydration_level_value = map_hydration_level(cups_per_day)
            smoking_status_value = map_smoking_status(smoking_status_text)
            health_condition_value = map_health_condition(health_condition_label)
            endurance_level_value = map_endurance_level(endurance_status)

            health_data = {
                "age": age,
                "gender": float(gender_value),
                "height_cm": height_cm,
                "weight_kg": weight_kg,
                "bmi": bmi_value,
                "activity_type": float(activity_type_value),
                "duration_minutes": adjusted_duration,
                "intensity": float(intensity_value),
                "calories_burned": calories_burned_value,
                "daily_steps": daily_steps,
                "avg_heart_rate": to_float(health_raw.get("avg_heart_rate", ""), 75.0),
                "resting_heart_rate": to_float(health_raw.get("resting_heart_rate", ""), 70.0),
                "blood_pressure_systolic": to_float(health_raw.get("blood_pressure_systolic", ""), 120.0),
                "blood_pressure_diastolic": to_float(health_raw.get("blood_pressure_diastolic", ""), 80.0),
                "endurance_level": float(endurance_level_value),
                "sleep_hours": sleep_hours,
                "stress_level": stress_level,
                "hydration_level": hydration_level_value,
                "smoking_status": float(smoking_status_value),
                "health_condition": float(health_condition_value),
            }

            psych_data = {
                "acad_stage_var": psychology_raw.get("acad_stage_var", "").strip(),
                "peer_pressure": to_float(psychology_raw.get("peer_pressure", 0)),
                "home_pressure": to_float(psychology_raw.get("home_pressure", 0)),
                "env_var": psychology_raw.get("env_var", "").strip(),
                "cope_var": psychology_raw.get("cope_var", "").strip(),
                "habit_var": psychology_raw.get("habit_var", "").strip(),
                "compete_var": to_float(psychology_raw.get("compete_var", 0)),
            }

            future_data = {
                "current_major_code": future_raw.get("current_major_code", "").strip(),
                "target_major_code": future_raw.get("target_major_code", "").strip(),
            }

            academic_result = calculate_academic_score(academic_data)
            consumption_result = calculate_consumption_score(consumption_data)
            health_result = run_health_model(health_data)
            psychology_result = run_psych_model(psych_data)
            similarity_result = calculate_major_similarity(
                future_data["current_major_code"],
                future_data["target_major_code"]
            )

            future_result = build_future_result(
                current_major_code=future_data["current_major_code"],
                target_major_code=future_data["target_major_code"],
                similarity_result=similarity_result,
                academic_score=academic_result["score"],
                consumption_score=consumption_result["score"],
                health_score=health_result["score"],
                psychology_score=psychology_result["score"],
            )

            final_result = merge_all_results(
                record_id=str(uuid.uuid4())[:8],
                academic_result=academic_result,
                consumption_result=consumption_result,
                health_result=health_result,
                psychology_result=psychology_result,
                future_result=future_result
            )

            result_id = final_result["record_id"]
            RESULT_CACHE[result_id] = final_result

            session["latest_result_id"] = result_id
            session.modified = True

            return redirect(url_for("result"))

            

        except Exception as e:
            error_text = f"{str(e)}\n\n{traceback.format_exc()}"
            return render_template("result_error.html", error_message=error_text)

    data = get_section_data("future")
    return render_template("assessment_future.html", data=data)


# =========================
# 结果页
# =========================
@app.route("/result")
def result():
    result_id = session.get("latest_result_id")
    if not result_id:
        return redirect(url_for("assessment_academic"))

    result_data = RESULT_CACHE.get(result_id)
    if not result_data:
        return redirect(url_for("assessment_academic"))

    return render_template("result.html", result=result_data)


# =========================
# 报告页
# =========================
@app.route("/report")
def report():
    result_id = session.get("latest_result_id")
    if not result_id:
        return redirect(url_for("assessment_academic"))

    result_data = RESULT_CACHE.get(result_id)
    if not result_data:
        return redirect(url_for("assessment_academic"))

    return render_template("report.html", result=result_data)


if __name__ == "__main__":
    app.run(debug=True)
    with app.app_context():
        db.create_all()