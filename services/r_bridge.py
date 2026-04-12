import csv
import subprocess
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
TEMP_DIR = BASE_DIR / "temp_files"
TEMP_DIR.mkdir(exist_ok=True)

# 这里改成你电脑上真实的 Rscript.exe 路径
RSCRIPT_PATH = Path(r"E:\R-4.5.1\bin\Rscript.exe")


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


def _run_r_script(script_path: Path, csv_path: Path) -> float:
    if not RSCRIPT_PATH.exists():
        raise RuntimeError(
            f"找不到 Rscript.exe：{RSCRIPT_PATH}\n"
            f"请检查 R 是否安装，或者把 RSCRIPT_PATH 改成你电脑上的真实路径。"
        )

    if not script_path.exists():
        raise RuntimeError(f"找不到 R 脚本：{script_path}")

    result = subprocess.run(
        [str(RSCRIPT_PATH), str(script_path), str(csv_path)],
        capture_output=True,
        text=True,
        cwd=BASE_DIR
    )

    if result.returncode != 0:
        raise RuntimeError(
            f"R 脚本运行失败：{script_path.name}\n\n"
            f"STDOUT:\n{result.stdout}\n\n"
            f"STDERR:\n{result.stderr}"
        )

    output = result.stdout.strip()
    if not output:
        raise RuntimeError(f"{script_path.name} 没有输出任何结果。")

    try:
        return float(output)
    except ValueError:
        raise RuntimeError(
            f"{script_path.name} 输出不是数字：\n{output}\n\nSTDERR:\n{result.stderr}"
        )


def run_health_model(health_data: dict) -> dict:
    csv_path = TEMP_DIR / "temp_health_input.csv"
    script_path = BASE_DIR / "r_models" / "health_predict.R"

    fieldnames = [
        "age", "gender", "height_cm", "weight_kg", "bmi",
        "activity_type", "duration_minutes", "intensity",
        "calories_burned", "daily_steps", "avg_heart_rate",
        "resting_heart_rate", "blood_pressure_systolic",
        "blood_pressure_diastolic", "endurance_level",
        "sleep_hours", "stress_level", "hydration_level",
        "smoking_status", "health_condition"
    ]

    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerow(health_data)

    score = _run_r_script(script_path, csv_path)

    return {
        "score": round(score, 1),
        "level": score_to_level(score),
        "module": "health"
    }


def run_psych_model(psych_data: dict) -> dict:
    csv_path = TEMP_DIR / "temp_psych_input.csv"
    script_path = BASE_DIR / "r_models" / "psych_predict.R"

    fieldnames = [
        "acad_stage_var",
        "peer_pressure",
        "home_pressure",
        "env_var",
        "cope_var",
        "habit_var",
        "compete_var",
    ]

    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerow(psych_data)

    score = _run_r_script(script_path, csv_path)

    return {
        "score": round(score, 1),
        "level": score_to_level(score),
        "module": "psychology"
    }