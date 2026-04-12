suppressPackageStartupMessages(library(lightgbm))

args <- commandArgs(trailingOnly = TRUE)

if (length(args) < 1) {
  stop("Missing input csv path")
}

input_csv <- args[1]

model <- lgb.load("model_assets/health_lgb_model.txt")
input_data <- read.csv(input_csv)

feature_order <- c(
  "age", "gender", "height_cm", "weight_kg", "bmi",
  "activity_type", "duration_minutes", "intensity",
  "calories_burned", "daily_steps", "avg_heart_rate",
  "resting_heart_rate", "blood_pressure_systolic",
  "blood_pressure_diastolic", "endurance_level",
  "sleep_hours", "stress_level", "hydration_level",
  "smoking_status", "health_condition"
)

test_matrix <- data.matrix(input_data[, feature_order])

raw_score <- predict(model, test_matrix)

# 你的新模型大概率已经直接输出 0-100 评分
final_score <- max(0, min(100, raw_score))

cat(round(final_score, 1))