# Go/NoGo Performance Analysis

rm(list = ls())
cat("\014")
if (!is.null(dev.list())) dev.off()

library(readxl)
library(dplyr)
library(tidyr)
library(ez)
library(irr)
library(writexl)

# -----------------------
# Config
# -----------------------
file_path <- "C:/1_DevuMahesan_Data/1. Ongoing_Work/3. MouseTracking/04a Analysis_manuscript/Experiment_analysis_30.01.2026/go_nogo_scored_final.xlsx"
out_xlsx  <- "C:/1_DevuMahesan_Data/1. Ongoing_Work/3. MouseTracking/04a Analysis_manuscript/Experiment_analysis_30.01.2026/performance_reliability_tables_complete.xlsx"

# -----------------------
# Helpers
# -----------------------
add_pes <- function(ez_res) {
  tab <- as.data.frame(ez_res$ANOVA)
  # partial eta^2 = SSn / (SSn + SSd)
  tab$pes <- with(tab, SSn / (SSn + SSd))
  tab
}

# -----------------------
# Load + validate data
# -----------------------
df <- read_excel(file_path) %>%
  filter(subject_id != 25) %>%
  mutate(
    participant = as.character(subject_id),
    Session = factor(session_actual),
    trial_type = factor(tolower(trial_type), levels = c("go","nogo")),
    error = 1 - accuracy
  )

stopifnot(all(c("participant","Session","trial_type","accuracy","rt_combined") %in% names(df)))

# ============================================================
# DESCRIPTIVES: ERROR
# ============================================================
desc_error <- df %>%
  group_by(Session, trial_type) %>%
  summarise(
    mean_error = mean(error, na.rm = TRUE),
    sd_error   = sd(error, na.rm = TRUE),
    n          = n(),
    .groups = "drop"
  )

# ============================================================
# PART 1: ERROR RATE ANOVA
# ============================================================
error_summary <- df %>%
  group_by(participant, Session, trial_type) %>%
  summarise(error_rate = mean(error, na.rm = TRUE), .groups = "drop")

anova_err_dat <- error_summary %>%
  mutate(Subject = factor(participant)) %>%
  rename(
    Error      = error_rate,
    TrialType  = trial_type,
    SessionVar = Session
  )

res_err <- ezANOVA(
  data = anova_err_dat,
  dv = .(Error),
  wid = .(Subject),
  within = .(SessionVar, TrialType),
  type = 3,
  detailed = TRUE
)

cat("\n=== ERROR ANOVA ===\n")
print(res_err)

anova_err_table <- add_pes(res_err)

# ============================================================
# PART 2: RT ANALYSIS (Correct trials + rt_combined > 0)
# ============================================================
df_rt <- df %>%
  filter(
    accuracy == 1,
    is.finite(rt_combined),
    rt_combined > 0
  )

# Cell-wise mean/sd (participant × Session × trial_type)
rt_stats <- df_rt %>%
  group_by(participant, Session, trial_type) %>%
  summarise(
    rt_mean_cell  = mean(rt_combined),
    rt_sd_cell    = sd(rt_combined),
    n_trials_cell = n(),
    .groups = "drop"
  )

df_rt_flagged <- df_rt %>%
  left_join(rt_stats, by = c("participant","Session","trial_type")) %>%
  mutate(
    is_outlier_rt = rt_combined < (rt_mean_cell - 2.5 * rt_sd_cell) |
      rt_combined > (rt_mean_cell + 2.5 * rt_sd_cell)
  )

outlier_summary_overall <- df_rt_flagged %>%
  summarise(
    total_trials     = n(),
    total_outliers   = sum(is_outlier_rt, na.rm = TRUE),
    percent_outliers = 100 * total_outliers / total_trials
  )

outlier_summary_participant <- df_rt_flagged %>%
  group_by(participant) %>%
  summarise(
    total_trials     = n(),
    outliers         = sum(is_outlier_rt, na.rm = TRUE),
    percent_outliers = 100 * outliers / total_trials,
    .groups = "drop"
  )

outlier_summary_cell <- df_rt_flagged %>%
  group_by(participant, Session, trial_type) %>%
  summarise(
    trials   = n(),
    outliers = sum(is_outlier_rt, na.rm = TRUE),
    .groups = "drop"
  )

df_rt_clean <- df_rt_flagged %>% filter(!is_outlier_rt)

# Descriptives RT
desc_rt <- df_rt_clean %>%
  group_by(Session, trial_type) %>%
  summarise(
    mean_rt = mean(rt_combined),
    sd_rt   = sd(rt_combined),
    n       = n(),
    .groups = "drop"
  )

# Mean RT per cell (after trimming)
rt_summary <- df_rt_clean %>%
  group_by(participant, Session, trial_type) %>%
  summarise(rt_mean = mean(rt_combined), .groups = "drop")

anova_rt_dat <- rt_summary %>%
  mutate(Subject = factor(participant)) %>%
  rename(
    RT        = rt_mean,
    TrialType = trial_type,
    SessionVar = Session
  )

res_rt <- ezANOVA(
  data = anova_rt_dat,
  dv = .(RT),
  wid = .(Subject),
  within = .(SessionVar, TrialType),
  type = 3,
  detailed = TRUE
)

cat("\n=== RT ANOVA ===\n")
print(res_rt)

anova_rt_table <- add_pes(res_rt)

# ============================================================
# PART 3: TEST–RETEST RELIABILITY (Pearson + ICC consistency)
# ============================================================
# Error rate reliability
error_go <- error_summary %>%
  filter(trial_type == "go") %>%
  pivot_wider(names_from = Session, values_from = error_rate, names_prefix = "session") %>%
  select(participant, session1, session2)

error_nogo <- error_summary %>%
  filter(trial_type == "nogo") %>%
  pivot_wider(names_from = Session, values_from = error_rate, names_prefix = "session") %>%
  select(participant, session1, session2)

# RT reliability (trimmed cell means)
rt_go <- rt_summary %>%
  filter(trial_type == "go") %>%
  pivot_wider(names_from = Session, values_from = rt_mean, names_prefix = "session") %>%
  select(participant, session1, session2)

rt_nogo <- rt_summary %>%
  filter(trial_type == "nogo") %>%
  pivot_wider(names_from = Session, values_from = rt_mean, names_prefix = "session") %>%
  select(participant, session1, session2)

# Build exportable reliability table
icc_go_err   <- irr::icc(error_go[, c("session1","session2")], model="twoway", type="consistency", unit="single")
icc_nogo_err <- irr::icc(error_nogo[, c("session1","session2")], model="twoway", type="consistency", unit="single")
icc_go_rt    <- irr::icc(rt_go[, c("session1","session2")], model="twoway", type="consistency", unit="single")
icc_nogo_rt  <- irr::icc(rt_nogo[, c("session1","session2")], model="twoway", type="consistency", unit="single")

# Build exportable reliability table (Pearson + ICC + ICC CI)
reliability_results <- tibble(
  measure = c("Go Error", "NoGo Error", "Go RT", "NoGo RT"),
  
  pearson_r = c(
    cor(error_go$session1, error_go$session2, use="pairwise.complete.obs"),
    cor(error_nogo$session1, error_nogo$session2, use="pairwise.complete.obs"),
    cor(rt_go$session1, rt_go$session2, use="pairwise.complete.obs"),
    cor(rt_nogo$session1, rt_nogo$session2, use="pairwise.complete.obs")
  ),
  
  icc = c(
    icc_go_err$value,
    icc_nogo_err$value,
    icc_go_rt$value,
    icc_nogo_rt$value
  ),
  
  icc_lwr = c(
    icc_go_err$lbound,
    icc_nogo_err$lbound,
    icc_go_rt$lbound,
    icc_nogo_rt$lbound
  ),
  
  icc_upr = c(
    icc_go_err$ubound,
    icc_nogo_err$ubound,
    icc_go_rt$ubound,
    icc_nogo_rt$ubound
  ),
  
  icc_conf_level = c(
    icc_go_err$conf.level,
    icc_nogo_err$conf.level,
    icc_go_rt$conf.level,
    icc_nogo_rt$conf.level
  )
)


# ============================================================
# EXPORT
# ============================================================
write_xlsx(
  list(
    "anova_error"               = anova_err_table,
    "anova_rt"                  = anova_rt_table,
    "reliability_summary"       = reliability_results,
    "error_go_sessions"         = error_go,
    "error_nogo_sessions"       = error_nogo,
    "rt_go_sessions"            = rt_go,
    "rt_nogo_sessions"          = rt_nogo,
    "descriptives_error"        = desc_error,
    "descriptives_rt"           = desc_rt,
    "rt_outliers_overall"       = outlier_summary_overall,
    "rt_outliers_by_participant"= outlier_summary_participant,
    "rt_outliers_by_cell"       = outlier_summary_cell
  ),
  path = out_xlsx
)

cat("\n✓ Export complete:\n", out_xlsx, "\n")
