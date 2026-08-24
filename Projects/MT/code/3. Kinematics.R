# ============================================================
# Go/NoGo KINEMATICS ANALYSIS - CORRECTED VERSION
# Option B: Movement epoch + stabilization window
# Mean velocity & acceleration are time-weighted
#
# FIXES APPLIED:
# 1. Duplicate time points handled correctly (Issue 3.1)
# 2. Inf values filtered in max calculations (Issue 3.2)
# 3. Parse failures properly detected (Issue 4 - colleague's concern)
# 4. Package installation check added (Issue 1.1)
# 5. Session structure validation added (Issue 4.1)
# 6. Documentation improved throughout
#
# ANOVA: reports partial eta^2; uses GG p-values when sphericity is violated
# ICC: exports ICC value + CI (lbound/ubound)
# ============================================================

# -----------------------
# Package Management
# -----------------------
required_packages <- c("readxl", "dplyr", "tidyr", "purrr", "jsonlite", "ez", "irr", "writexl")
missing_packages <- required_packages[!(required_packages %in% installed.packages()[,"Package"])]

if(length(missing_packages) > 0) {
  stop("Please install missing packages first:\n",
       "install.packages(c('", paste(missing_packages, collapse = "', '"), "'))")
}

# Clear workspace
rm(list = ls())
cat("\014")
if (!is.null(dev.list())) dev.off()

library(readxl)
library(dplyr)
library(tidyr)
library(purrr)
library(jsonlite)
library(ez)
library(irr)
library(writexl)

# -----------------------
# Config
# -----------------------
file_path   <- "C:/1_DevuMahesan_Data/1. Ongoing_Work/3. MouseTracking/04a Analysis_manuscript/Experiment_analysis_30.01.2026/go_nogo_scored_final.xlsx"
output_xlsx <- "C:/1_DevuMahesan_Data/1. Ongoing_Work/3. MouseTracking/04a Analysis_manuscript/Experiment_analysis_30.01.2026/3. Kinematics_results01_CORRECTED.xlsx"

# NoGo stabilization window (150ms after stopping to verify sustained stillness)
POST_STILL_SEC <- 0.150

required_cols <- c(
  "subject_id", "session_actual", "trial_type",
  "accuracy", "rt_combined",
  "mouse_resp.x", "mouse_resp.y", "mouse_resp.time"
)

# -----------------------
# Helper Functions
# -----------------------

#' Parse JSON string to numeric vector
#' Returns list with vector and parse_failed flag
safe_parse_vec <- function(x) {
  if (is.na(x) || x == "") return(list(vec = numeric(0), parse_failed = TRUE))
  out <- tryCatch(jsonlite::fromJSON(x), error = function(e) NULL)
  if (is.null(out)) return(list(vec = numeric(0), parse_failed = TRUE))
  list(vec = as.numeric(out), parse_failed = FALSE)
}

#' Align vector to expected length, padding with NA if needed
#' Issues warning when padding occurs (indicates data quality issue)
align_to_n_strict <- function(v, n, label = "") {
  if (length(v) == 0) return(rep(NA_real_, n))
  if (length(v) < n) {
    if (label != "") {
      warning("Vector '", label, "' length ", length(v), " < expected ", n, ". Padding with NA.")
    }
  }
  if (length(v) >= n) return(v[seq_len(n)])
  c(v, rep(NA_real_, n - length(v)))
}

#' Extract ANOVA table with partial eta-squared and GG correction when needed
extract_anova_with_pes <- function(ez_res) {
  
  a <- as.data.frame(ez_res$ANOVA)
  
  # Compute partial eta-squared: ηp² = SSn / (SSn + SSd)
  if (all(c("SSn","SSd") %in% names(a))) {
    a$pes <- with(a, SSn / (SSn + SSd))
  } else {
    a$pes <- NA_real_
  }
  
  # Default: use uncorrected p-value
  a$p_report <- a$p
  a$correction_used <- "none"
  
  # If Mauchly's test detected sphericity violation, use GG corrected p-value
  if (!is.null(ez_res$Mauchly) && nrow(ez_res$Mauchly) > 0) {
    m <- as.data.frame(ez_res$Mauchly) %>%
      select(Effect, p) %>%
      rename(mauchly_p = p)
    
    a <- a %>% left_join(m, by = "Effect")
    
    # Apply GG correction when sphericity violated (Mauchly p < .05)
    if ("p[GG]" %in% names(a)) {
      violated <- !is.na(a$mauchly_p) & a$mauchly_p < 0.05 & !is.na(a$`p[GG]`)
      a$p_report[violated] <- a$`p[GG]`[violated]
      a$correction_used[violated] <- "GG"
    }
  } else {
    a$mauchly_p <- NA_real_
  }
  
  a
}

# -----------------------
# Core Kinematics Computation (time-weighted means)
# -----------------------

#' Compute kinematic features from mouse trajectory
#' 
#' @param x_str JSON string of x coordinates
#' @param y_str JSON string of y coordinates  
#' @param t_str JSON string of timestamps
#' @param end_time Maximum time to analyze (seconds from trial start)
#' 
#' @details
#' For Go trials: end_time = RT (time of click in box)
#' For NoGo trials: end_time = stop_time + 150ms (includes stabilization window)
#' 
#' Velocity: Time-weighted mean = total_path_length / total_duration
#' Acceleration: Time-weighted mean = sum(|a| * dt) / sum(dt)
#' 
#' @return tibble with kinematic metrics
compute_kinematics <- function(x_str, y_str, t_str, end_time) {
  
  # Parse JSON arrays
  px <- safe_parse_vec(x_str)
  py <- safe_parse_vec(y_str)
  pt <- safe_parse_vec(t_str)
  
  # FIX ISSUE 4: Check for parse failures in x or y coordinates
  # If either x or y failed to parse, this trial cannot be analyzed
  if (px$parse_failed || py$parse_failed || pt$parse_failed) {
    return(tibble(
      kin_parse_failed = TRUE,
      kin_n_samples = 0L,
      duration = NA_real_,
      path_length = NA_real_,
      max_velocity = NA_real_,
      mean_velocity = NA_real_,
      max_acceleration = NA_real_,
      mean_acceleration = NA_real_
    ))
  }
  
  # Require minimum 3 samples for meaningful kinematics
  if (length(pt$vec) < 3) {
    return(tibble(
      kin_parse_failed = TRUE,
      kin_n_samples = 0L,
      duration = NA_real_,
      path_length = NA_real_,
      max_velocity = NA_real_,
      mean_velocity = NA_real_,
      max_acceleration = NA_real_,
      mean_acceleration = NA_real_
    ))
  }
  
  # Align x and y to time vector length
  nT <- length(pt$vec)
  x <- align_to_n_strict(px$vec, nT, "x")
  y <- align_to_n_strict(py$vec, nT, "y")
  t <- pt$vec
  
  # Convert to relative time (seconds from trial start)
  t_rel <- t - t[1]
  
  # Filter to analysis window (0 to end_time)
  keep <- which(t_rel <= end_time)
  if (length(keep) < 3) {
    return(tibble(
      kin_parse_failed = FALSE,
      kin_n_samples = length(keep),
      duration = NA_real_,
      path_length = NA_real_,
      max_velocity = NA_real_,
      mean_velocity = NA_real_,
      max_acceleration = NA_real_,
      mean_acceleration = NA_real_
    ))
  }
  
  x <- x[keep]
  y <- y[keep]
  t_rel <- t_rel[keep]
  
  # Remove non-finite values (NA, Inf, NaN)
  ok <- is.finite(x) & is.finite(y) & is.finite(t_rel)
  x <- x[ok]
  y <- y[ok]
  t_rel <- t_rel[ok]
  
  if (length(t_rel) < 3) {
    return(tibble(
      kin_parse_failed = FALSE,
      kin_n_samples = length(t_rel),
      duration = NA_real_,
      path_length = NA_real_,
      max_velocity = NA_real_,
      mean_velocity = NA_real_,
      max_acceleration = NA_real_,
      mean_acceleration = NA_real_
    ))
  }
  
  # FIX ISSUE 3.1: Remove duplicate time points properly
  # Use duplicated() to identify ALL duplicates, keeping only first occurrence
  dup_mask <- !duplicated(t_rel)
  x2 <- x[dup_mask]
  y2 <- y[dup_mask]
  t2 <- t_rel[dup_mask]
  
  # Verify we still have enough samples
  if (length(t2) < 3) {
    return(tibble(
      kin_parse_failed = FALSE,
      kin_n_samples = length(t2),
      duration = NA_real_,
      path_length = NA_real_,
      max_velocity = NA_real_,
      mean_velocity = NA_real_,
      max_acceleration = NA_real_,
      mean_acceleration = NA_real_
    ))
  }
  
  # Verify time is strictly increasing (should be true after removing duplicates)
  dt_check <- diff(t2)
  if (any(dt_check <= 0)) {
    # This should not happen, but catch it just in case
    return(tibble(
      kin_parse_failed = FALSE,
      kin_n_samples = length(t2),
      duration = NA_real_,
      path_length = NA_real_,
      max_velocity = NA_real_,
      mean_velocity = NA_real_,
      max_acceleration = NA_real_,
      mean_acceleration = NA_real_
    ))
  }
  
  # -----------------------
  # Compute Velocity
  # -----------------------
  
  # Spatial differences
  dx <- diff(x2)
  dy <- diff(y2)
  dt <- diff(t2)
  
  # Euclidean distance and instantaneous velocity
  ds <- sqrt(dx^2 + dy^2)
  v <- ds / dt  # pixels per second
  
  # Path metrics
  duration <- t2[length(t2)] - t2[1]
  path_len <- sum(ds)
  
  # Time-weighted mean velocity = total distance / total time
  # This is the CORRECT approach (not arithmetic mean of instantaneous velocities)
  mean_v <- if (is.finite(duration) && duration > 0) {
    path_len / duration
  } else {
    NA_real_
  }
  
  # FIX ISSUE 3.2: Filter out Inf/NaN before taking max
  # (Inf can occur if there were zero-duration intervals that we missed)
  max_v <- if (length(v) > 0 && any(is.finite(v))) {
    max(v[is.finite(v)])
  } else {
    NA_real_
  }
  
  # -----------------------
  # Compute Acceleration
  # -----------------------
  
  if (length(v) >= 2) {
    # Velocity changes
    dv <- diff(v)
    
    # Time intervals for acceleration calculation
    # Use "latter" intervals: a[i] = (v[i+1] - v[i]) / dt[i+1]
    # This is a valid convention assuming v[i] represents velocity at end of interval i
    dt_a <- dt[-1]  # removes first interval, keeps dt[2], dt[3], ..., dt[n]
    
    # Acceleration (pixels per second squared)
    a <- dv / dt_a
    
    # Filter valid accelerations for time-weighted mean
    ok_a <- is.finite(a) & is.finite(dt_a) & dt_a > 0
    
    # Time-weighted mean of ABSOLUTE acceleration
    # Uses absolute value because we care about magnitude of acceleration changes
    mean_a <- if (sum(ok_a) > 0) {
      sum(abs(a[ok_a]) * dt_a[ok_a]) / sum(dt_a[ok_a])
    } else {
      NA_real_
    }
    
    # FIX ISSUE 3.5: Filter Inf/NaN before taking max
    max_a <- if (any(is.finite(a))) {
      max(abs(a[is.finite(a)]))
    } else {
      NA_real_
    }
    
  } else {
    mean_a <- NA_real_
    max_a <- NA_real_
  }
  
  # Return results
  tibble(
    kin_parse_failed = FALSE,
    kin_n_samples = length(t2),
    duration = duration,
    path_length = path_len,
    max_velocity = max_v,
    mean_velocity = mean_v,
    max_acceleration = max_a,
    mean_acceleration = mean_a
  )
}

# -----------------------
# Load & Validate Data
# -----------------------
cat("\n=== LOADING DATA ===\n")
df <- read_excel(file_path)

# Check for required columns
missing_cols <- setdiff(required_cols, names(df))
if (length(missing_cols) > 0) {
  stop("Missing required columns: ", paste(missing_cols, collapse = ", "))
}

# Filter and prepare data
df <- df %>%
  filter(!subject_id %in% c("25")) %>%
  mutate(
    participant = as.character(subject_id),
    Session = factor(session_actual),
    trial_type = factor(tolower(trial_type), levels = c("go", "nogo"))
  )

cat(sprintf("Loaded %d trials from %d participants\n",
            nrow(df), length(unique(df$participant))))

# FIX ISSUE 4.1: Validate session structure for test-retest reliability
cat("\n=== VALIDATING SESSION STRUCTURE ===\n")
session_check <- df %>%
  group_by(participant) %>%
  summarise(
    n_sessions = n_distinct(Session),
    sessions = paste(sort(unique(Session)), collapse = ","),
    .groups = "drop"
  )

# Check for participants without exactly 2 sessions
invalid_sessions <- session_check %>% filter(n_sessions != 2)
if (nrow(invalid_sessions) > 0) {
  warning("⚠ Participants without exactly 2 sessions:\n")
  print(invalid_sessions)
} else {
  cat("✓ All participants have exactly 2 sessions\n")
}

# Check session labels
unique_sessions <- sort(unique(df$Session))
if (!all(unique_sessions == c("1", "2"))) {
  warning("⚠ Session labels are: ", paste(unique_sessions, collapse = ", "),
          " (expected: 1, 2)")
} else {
  cat("✓ Session labels are correct (1, 2)\n")
}

# -----------------------
# Pre-filtering Summary
# -----------------------
pre_summary <- df %>%
  group_by(trial_type) %>%
  summarise(
    total = n(),
    correct = sum(accuracy == 1, na.rm = TRUE),
    with_rt = sum(accuracy == 1 & is.finite(rt_combined) & rt_combined > 0, na.rm = TRUE),
    pct_usable = 100 * with_rt / total,
    .groups = "drop"
  )

cat("\n=== PRE-FILTERING SUMMARY ===\n")
print(pre_summary)

# -----------------------
# Filter Correct Trials with Movement
# -----------------------
# VERIFIED FROM rt_combined DOCUMENTATION:
# - Go: rt_combined = time of first click inside box (seconds from trial start)
# - NoGo Case 1: rt_combined = 0 if no movement initiated (< 5 pixels, < 10 pix/s)
# - NoGo Case 2: rt_combined = time when velocity drops below 10 pix/s and stays there ≥150ms
#
# For kinematics:
# - Go: analyze movement from 0 to rt_combined (click time)
# - NoGo: analyze movement from 0 to rt_combined + 150ms (includes stabilization check)

df_filtered <- df %>%
  filter(
    accuracy == 1,           # Only correct trials
    is.finite(rt_combined),  # Valid RT
    rt_combined > 0          # Exclude NoGo trials with no movement (rt_combined = 0)
  ) %>%
  mutate(
    # For NoGo: add 150ms stabilization window after stopping
    # For Go: use RT directly (time of click in box)
    end_time_kin = if_else(
      trial_type == "nogo",
      rt_combined + POST_STILL_SEC,
      rt_combined
    )
  )

cat(sprintf("\nComputing kinematics for %d trials (%.1f%% of all trials)\n",
            nrow(df_filtered), 100*nrow(df_filtered)/nrow(df)))

# -----------------------
# Compute Kinematics
# -----------------------
cat("\n=== COMPUTING KINEMATICS ===\n")

df_kin <- df_filtered %>%
  rowwise() %>%
  mutate(kin = list(
    compute_kinematics(mouse_resp.x, mouse_resp.y, mouse_resp.time, end_time_kin)
  )) %>%
  ungroup() %>%
  unnest(kin) %>%
  filter(
    !kin_parse_failed,           # Exclude parse failures
    kin_n_samples >= 3,          # Minimum samples
    is.finite(duration) & duration > 0,
    is.finite(max_velocity),
    is.finite(mean_velocity),
    is.finite(path_length)
  )

cat(sprintf("✓ Valid kinematics: %d trials (%.1f%% of filtered trials)\n",
            nrow(df_kin), 100*nrow(df_kin)/nrow(df_filtered)))

# -----------------------
# Duration Verification
# -----------------------
cat("\n=== DURATION VERIFICATION ===\n")

duration_check <- df_kin %>%
  group_by(trial_type) %>%
  summarise(
    n = n(),
    mean_rt = mean(rt_combined, na.rm = TRUE),
    mean_duration = mean(duration, na.rm = TRUE),
    mean_diff = mean(duration - rt_combined, na.rm = TRUE),
    sd_diff = sd(duration - rt_combined, na.rm = TRUE),
    max_diff = max(duration - rt_combined, na.rm = TRUE),
    .groups = "drop"
  )
print(duration_check)

# -----------------------
# Outlier Trimming (±2.5 SD per cell)
# -----------------------
cat("\n=== OUTLIER REMOVAL ===\n")

metrics <- c("max_velocity", "mean_velocity", "max_acceleration", "mean_acceleration", "path_length")

# Function to trim outliers for a single metric
trim_outliers <- function(dat, metric) {
  dat %>%
    group_by(participant, Session, trial_type) %>%
    mutate(
      cell_mean = mean(.data[[metric]], na.rm = TRUE),
      cell_sd = sd(.data[[metric]], na.rm = TRUE),
      is_outlier = ifelse(
        is.finite(cell_sd) & cell_sd > 0,
        abs(.data[[metric]] - cell_mean) > 2.5 * cell_sd,
        FALSE
      )
    ) %>%
    ungroup() %>%
    select(-cell_mean, -cell_sd) %>%
    filter(!is_outlier) %>%
    select(-is_outlier)
}

# Report outlier counts per metric
outlier_summary <- map_dfr(metrics, function(m) {
  before <- df_kin %>% filter(is.finite(.data[[m]])) %>% nrow()
  after  <- df_kin %>% trim_outliers(m) %>% nrow()
  tibble(
    metric = m,
    n_before = before,
    n_removed = before - after,
    pct_removed = round(100 * (before - after) / before, 2)
  )
})

cat("\nOutlier removal summary (2.5 SD per cell):\n")
print(outlier_summary)

# Compute cell means after outlier removal
# NOTE: Each metric is trimmed independently, so different trials may be excluded per metric
# This is acceptable as we're computing means per metric separately
cell_means <- map_dfr(metrics, function(m) {
  df_kin %>%
    trim_outliers(m) %>%
    group_by(participant, Session, trial_type) %>%
    summarise(
      value = mean(.data[[m]], na.rm = TRUE),
      n_trials = n(),
      .groups = "drop"
    ) %>%
    mutate(metric = m)
})

# Create wide format for scatterplots (session 1 vs session 2)
scatterplot_wide <- cell_means %>%
  mutate(col = paste(metric, trial_type, Session, sep = "_")) %>%
  select(participant, col, value) %>%
  pivot_wider(
    id_cols = participant,
    names_from = col,
    values_from = value,
    values_fn = mean  # in case of duplicates
  )

# -----------------------
# Statistical Analysis
# -----------------------
cat("\n=== RUNNING STATISTICAL ANALYSES ===\n")

#' Run complete statistical analysis for one metric
#' Returns: ANOVA, Mauchly, Sphericity, t-tests, reliability (ICC + Pearson r)
run_stats <- function(metric_name) {
  
  cat("Processing:", metric_name, "...\n")
  
  d <- cell_means %>%
    filter(metric == metric_name) %>%
    mutate(Subject = factor(participant))
  
  # -----------------------
  # 2×2 Repeated Measures ANOVA (Session × Trial Type)
  # -----------------------
  ez_res <- ezANOVA(
    data = d,
    dv = .(value),
    wid = .(Subject),
    within = .(Session, trial_type),
    type = 3,           # Type III SS
    detailed = TRUE     # Get SS for effect sizes
  )
  
  anova_tbl <- extract_anova_with_pes(ez_res) %>%
    mutate(metric = metric_name)
  
  # Extract Mauchly's test (sphericity assumption)
  mauchly_tbl <- if (!is.null(ez_res$Mauchly) && nrow(ez_res$Mauchly) > 0) {
    as.data.frame(ez_res$Mauchly) %>% mutate(metric = metric_name)
  } else {
    tibble(metric = metric_name)
  }
  
  # Extract sphericity corrections (GG, HF)
  sph_tbl <- if (!is.null(ez_res$`Sphericity Corrections`) && nrow(ez_res$`Sphericity Corrections`) > 0) {
    as.data.frame(ez_res$`Sphericity Corrections`) %>% mutate(metric = metric_name)
  } else {
    tibble(metric = metric_name)
  }
  
  # -----------------------
  # Paired t-tests (Simple Effects)
  # -----------------------
  
  # Create wide format for each comparison
  go_wide <- d %>%
    filter(trial_type == "go") %>%
    select(participant, Session, value) %>%
    pivot_wider(names_from = Session, values_from = value, names_prefix = "S")
  
  nogo_wide <- d %>%
    filter(trial_type == "nogo") %>%
    select(participant, Session, value) %>%
    pivot_wider(names_from = Session, values_from = value, names_prefix = "S")
  
  s1_wide <- d %>%
    filter(Session == "1") %>%
    select(participant, trial_type, value) %>%
    pivot_wider(names_from = trial_type, values_from = value)
  
  s2_wide <- d %>%
    filter(Session == "2") %>%
    select(participant, trial_type, value) %>%
    pivot_wider(names_from = trial_type, values_from = value)
  
  # Safe t-test function
  safe_t <- function(w, a, b, label) {
    if (!(a %in% names(w)) || !(b %in% names(w))) return(NULL)
    tmp <- w %>% filter(is.finite(.data[[a]]) & is.finite(.data[[b]]))
    if (nrow(tmp) < 3) return(NULL)
    
    tt <- t.test(tmp[[a]], tmp[[b]], paired = TRUE)
    tibble(
      metric = metric_name,
      test = label,
      n = nrow(tmp),
      mean_a = mean(tmp[[a]]),
      mean_b = mean(tmp[[b]]),
      mean_diff = mean(tmp[[a]] - tmp[[b]]),
      t = unname(tt$statistic),
      df = unname(tt$parameter),
      p = tt$p.value,
      ci_lower = tt$conf.int[1],
      ci_upper = tt$conf.int[2]
    )
  }
  
  # Four comparisons:
  # 1. Go: Session 1 vs 2
  # 2. NoGo: Session 1 vs 2
  # 3. Session 1: Go vs NoGo
  # 4. Session 2: Go vs NoGo
  ttests <- bind_rows(
    safe_t(go_wide,   "S1", "S2", "Session: Go"),
    safe_t(nogo_wide, "S1", "S2", "Session: NoGo"),
    safe_t(s1_wide,   "go", "nogo", "TrialType: Session 1"),
    safe_t(s2_wide,   "go", "nogo", "TrialType: Session 2")
  )
  
  # -----------------------
  # Test-Retest Reliability (Pearson r + ICC)
  # -----------------------
  
  reliability <- map_dfr(c("go","nogo"), function(ttype) {
    
    w <- d %>%
      filter(trial_type == ttype) %>%
      select(participant, Session, value) %>%
      pivot_wider(names_from = Session, values_from = value, names_prefix = "S")
    
    if (!("S1" %in% names(w)) || !("S2" %in% names(w))) return(NULL)
    
    w2 <- w %>% filter(is.finite(S1) & is.finite(S2))
    if (nrow(w2) < 3) return(NULL)
    
    # Pearson correlation
    ct <- cor.test(w2$S1, w2$S2)
    
    # ICC(3,1): Two-way mixed effects, consistency, single measurement
    # Appropriate for test-retest reliability
    # "Consistency" ignores systematic session differences (e.g., practice effects)
    # "Two-way mixed" treats sessions as fixed effects (these specific two sessions)
    ic <- irr::icc(
      w2[, c("S1","S2")],
      model = "twoway",      # Two-way mixed effects
      type = "consistency",  # Relative consistency (ignores mean differences)
      unit = "single"        # Single measurement (not average)
    )
    
    tibble(
      metric = metric_name,
      trial_type = ttype,
      n = nrow(w2),
      pearson_r = unname(ct$estimate),
      pearson_p = ct$p.value,
      pearson_ci_lower = ct$conf.int[1],
      pearson_ci_upper = ct$conf.int[2],
      icc = ic$value,
      icc_lwr = ic$lbound,
      icc_upr = ic$ubound
    )
  })
  
  # Return all results
  list(
    anova = anova_tbl,
    mauchly = mauchly_tbl,
    sphericity = sph_tbl,
    ttests = ttests,
    reliability = reliability
  )
}

# Run statistics for all metrics
stats <- map(metrics, run_stats)

# Combine results across metrics
anova_all      <- bind_rows(map(stats, "anova"))
mauchly_all    <- bind_rows(map(stats, "mauchly"))
sphericity_all <- bind_rows(map(stats, "sphericity"))
ttests_all     <- bind_rows(map(stats, "ttests"))
reliab_all     <- bind_rows(map(stats, "reliability"))

# -----------------------
# Export Results
# -----------------------
cat("\n=== EXPORTING RESULTS ===\n")

write_xlsx(
  list(
    "01_trial_kinematics"   = df_kin,
    "02_pre_filter_summary" = pre_summary,
    "03_duration_check"     = duration_check,
    "04_outlier_summary"    = outlier_summary,
    "05_cell_means"         = cell_means,
    "06_scatterplot_wide"   = scatterplot_wide,
    "07_anova"              = anova_all,
    "08_mauchly"            = mauchly_all,
    "09_sphericity"         = sphericity_all,
    "10_ttests"             = ttests_all,
    "11_reliability"        = reliab_all
  ),
  path = output_xlsx
)

cat("\n✓ Kinematics analysis complete\n")
cat(sprintf("✓ Results saved to: %s\n", output_xlsx))
cat("\n=== SUMMARY ===\n")
cat(sprintf("Total trials analyzed: %d\n", nrow(df_kin)))
cat(sprintf("Participants: %d\n", length(unique(df_kin$participant))))
cat(sprintf("Metrics computed: %s\n", paste(metrics, collapse = ", ")))
cat("\nAll fixes applied successfully:\n")
cat("  ✓ Duplicate time points removed correctly\n")
cat("  ✓ Inf values filtered in max calculations\n")
cat("  ✓ Parse failures detected properly (x/y/time)\n")
cat("  ✓ Package installation checked\n")
cat("  ✓ Session structure validated\n")
cat("  ✓ Documentation improved throughout\n")
