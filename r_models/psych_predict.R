suppressPackageStartupMessages(library(bnlearn))

args <- commandArgs(trailingOnly = TRUE)

if (length(args) < 1) {
  stop("Missing input csv path")
}

input_csv <- args[1]

bn_fitted <- readRDS("model_assets/academic_stress_bn_model.rds")
input_data <- read.csv(input_csv, stringsAsFactors = FALSE)

# ---- 读取网页输入 ----
p_stage <- trimws(input_data$acad_stage_var[1])
p_peer <- as.numeric(input_data$peer_pressure[1])
p_home <- as.numeric(input_data$home_pressure[1])
p_env <- trimws(input_data$env_var[1])
p_cope <- trimws(input_data$cope_var[1])
p_habit <- trimws(input_data$habit_var[1])
p_compete <- as.numeric(input_data$compete_var[1])

# ---- 缺失保护 ----
if (is.na(p_peer)) p_peer <- 3
if (is.na(p_home)) p_home <- 3
if (is.na(p_compete)) p_compete <- 3

peer_low <- max(1, p_peer - 1)
peer_high <- min(5, p_peer + 1)

home_low <- max(1, p_home - 1)
home_high <- min(5, p_home + 1)

comp_low <- max(1, p_compete - 1)
comp_high <- min(5, p_compete + 1)

set.seed(123)

# ---- 贝叶斯推理：三分类概率 ----
p_low <- cpquery(
  fitted = bn_fitted,
  event = (stress_cat == "low"),
  evidence = (
    acad_stage_var == p_stage &
    peer_var >= peer_low & peer_var <= peer_high &
    home_var >= home_low & home_var <= home_high &
    env_var == p_env &
    cope_var == p_cope &
    habit_var == p_habit &
    compete_var >= comp_low & compete_var <= comp_high
  ),
  n = 50000
)

p_medium <- cpquery(
  fitted = bn_fitted,
  event = (stress_cat == "medium"),
  evidence = (
    acad_stage_var == p_stage &
    peer_var >= peer_low & peer_var <= peer_high &
    home_var >= home_low & home_var <= home_high &
    env_var == p_env &
    cope_var == p_cope &
    habit_var == p_habit &
    compete_var >= comp_low & compete_var <= comp_high
  ),
  n = 50000
)

p_high <- cpquery(
  fitted = bn_fitted,
  event = (stress_cat == "high"),
  evidence = (
    acad_stage_var == p_stage &
    peer_var >= peer_low & peer_var <= peer_high &
    home_var >= home_low & home_var <= home_high &
    env_var == p_env &
    cope_var == p_cope &
    habit_var == p_habit &
    compete_var >= comp_low & compete_var <= comp_high
  ),
  n = 50000
)

# ---- NA 保护 ----
if (is.na(p_low)) p_low <- 0
if (is.na(p_medium)) p_medium <- 0
if (is.na(p_high)) p_high <- 0

p_sum <- p_low + p_medium + p_high

# ---- 主评分：三分类概率加权 ----
if (p_sum > 0) {
  p_low <- p_low / p_sum
  p_medium <- p_medium / p_sum
  p_high <- p_high / p_sum

  # 部署层稳定化打分
  health_score <- p_low * 86 + p_medium * 68 + p_high * 48
} else {
  # ---- fallback：若采样匹配不到，则按原始输入做平滑估计 ----
  risk <- 0

  risk <- risk + (p_peer - 1) * 6
  risk <- risk + (p_home - 1) * 6
  risk <- risk + (p_compete - 1) * 5

  if (p_env == "Noisy") {
    risk <- risk + 6
  } else if (p_env == "Moderate") {
    risk <- risk + 3
  }

  if (p_cope == "Avoid thinking about it") {
    risk <- risk + 8
  } else if (p_cope == "Release emotions through entertainment") {
    risk <- risk + 4
  } else if (p_cope == "Talk to someone and seek support") {
    risk <- risk - 2
  } else if (p_cope == "Analyze the situation and handle it with intellect") {
    risk <- risk - 4
  }

  if (p_habit == "Yes") {
    risk <- risk + 5
  }

  if (p_stage == "phd") {
    risk <- risk + 3
  } else if (p_stage == "postgraduate") {
    risk <- risk + 2
  }

  health_score <- 82 - risk
}

# ---- 最终校准：避免极端值 ----
health_score <- max(35, min(92, health_score))

cat(round(health_score, 1))