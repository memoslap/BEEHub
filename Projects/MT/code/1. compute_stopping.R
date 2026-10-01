# ==============================================================================
# 1. SETUP & CONFIGURATION
# ==============================================================================

# Load required packages (no runtime install; env is expected to be provisioned)
suppressPackageStartupMessages({
  library(dplyr)      # Data manipulation
  library(tidyr)      # Data tidying
  library(jsonlite)   # Parse JSON arrays (params)
  library(stringr)    # String manipulation
  library(ggplot2)    # QC plots (supplementary)
  library(purrr)      # Functional programming
})
# readxl / writexl are not needed: input is now BIDS TSV, not Excel.

# --------------------------------------------------
# File paths (BEEHub derivation contract)
# Called as: Rscript <this file> --input <dir> --output <dir> [--params <json>]
# --input  : BIDS dataset with sub-*/ses-*/beh/*_task-gonogo_beh.tsv
# --output : directory for the scored derivative (sub-*/ses-*/beh/...)
# --------------------------------------------------
args   <- commandArgs(trailingOnly = TRUE)
input  <- args[which(args == "--input")  + 1]
output <- args[which(args == "--output") + 1]
i      <- which(args == "--params")
params <- if (length(i)) jsonlite::fromJSON(args[i + 1]) else list()

# --------------------------------------------------
# Experimental parameters
# Delivered defaults; overridden by matching keys in --params
# --------------------------------------------------

# Target box coordinates (PsychoPy: pos=(200,300), size=(100,100))
# Note: Boundaries are EXCLUDED (using > and < not >= and <=)
BOX_CONFIG <- list(
  x_min = 150,
  x_max = 250,
  y_min = 250,
  y_max = 350,
  include_boundary = FALSE  # Exclude exact boundary coordinates
)

# NoGo stopping detection parameters
NOGO_CONFIG <- list(
  v_thresh = 10,               # Velocity threshold (pixels/sec) for "stillness"
  min_still_sec = 0.15,        # Minimum duration (sec) of stillness to count as "stopped"
  post_still_sec = 0.25,       # Duration (sec) after stopping to verify sustained stillness
  deadline_sec = 1.5,          # Trial deadline (sec)
  dist_thresh_no_move = 5,     # Max displacement (pixels) to classify as "no movement"
  post_still_criterion = 0.9   # Proportion of post-stop samples that must be below v_thresh
)

# Apply --params overrides (delivered values above are the defaults)
# Only override keys that already exist in the config list (no new keys added).
for (blk in c("BOX_CONFIG", "NOGO_CONFIG")) {
  if (blk %in% names(params)) {
    for (k in intersect(names(params[[blk]]), names(get(blk)))) {
      cur <- get(blk)
      cur[[k]] <- params[[blk]][[k]]
      assign(blk, cur)
    }
  }
}

# ==============================================================================
# 2. UTILITY FUNCTIONS
# ==============================================================================

#' Safely parse JSON vector from string
#' 
#' Handles malformed JSON and returns explicit parse failure flag.
#' This prevents corrupted data from silently inflating accuracy.
#' 
#' @param x Character string containing JSON array
#' @return List with 'vec' (numeric vector) and 'parse_failed' (logical)
safe_parse_vec <- function(x) {
  # Handle NA or empty
  if (length(x) == 0 || is.na(x)) {
    return(list(vec = numeric(0), parse_failed = TRUE))
  }
  
  # Coerce to character if not already (handles factors)
  if (!is.character(x)) {
    x <- as.character(x)
  }
  
  # Handle empty string
  if (x == "") {
    return(list(vec = numeric(0), parse_failed = TRUE))
  }
  
  # Try to parse
  out <- tryCatch(fromJSON(x), error = function(e) NULL)
  if (is.null(out)) {
    return(list(vec = numeric(0), parse_failed = TRUE))
  }
  
  list(vec = suppressWarnings(as.numeric(out)), parse_failed = FALSE)
}

#' Align vector to target length with padding or repetition
#' 
#' CRITICAL FIX: If length=1, REPEAT the value (don't discard it).
#' Original bug: single-value vectors were replaced with padding.
#' 
#' @param v Input vector
#' @param n Target length
#' @param pad Padding value for empty vectors (default: NA)
#' @return Vector of length n
align_to_n <- function(v, n, pad = NA_real_) {
  if (length(v) == 0) return(rep(pad, n))
  
  len_v <- length(v)
  
  # If exact match, return as-is
  if (len_v == n) return(v)
  
  # If single value and n > 1, repeat (assume constant state)
  if (len_v == 1 && n > 1) return(rep(v, n))
  
  # If longer than needed, truncate
  if (len_v > n) return(v[seq_len(n)])
  
  # If shorter, pad
  c(v, rep(pad, n - len_v))
}

#' Check if coordinates are inside target box
#' 
#' @param x X coordinate(s)
#' @param y Y coordinate(s)
#' @param box Box configuration list
#' @return Logical vector
inside_box <- function(x, y, box) {
  if (box$include_boundary) {
    x >= box$x_min & x <= box$x_max & y >= box$y_min & y <= box$y_max
  } else {
    x > box$x_min & x < box$x_max & y > box$y_min & y < box$y_max
  }
}

#' Interpolate X,Y position at query time
#' 
#' Uses linear interpolation to estimate mouse position at click onset time.
#' 
#' @param t Time vector
#' @param x X coordinate vector
#' @param y Y coordinate vector
#' @param tq Query time
#' @return Numeric vector c(x_interp, y_interp) or c(NA, NA) if insufficient data
interp_xy <- function(t, x, y, tq) {
  ok <- is.finite(t) & is.finite(x) & is.finite(y)
  if (sum(ok) < 2) return(c(NA_real_, NA_real_))
  
  c(
    approx(t[ok], x[ok], xout = tq, rule = 1)$y,
    approx(t[ok], y[ok], xout = tq, rule = 1)$y
  )
}

# ==============================================================================
# 3. CORE PROCESSING FUNCTIONS
# ==============================================================================

#' Extract LEFT-button clicks with interpolated positions
#' 
#' Identifies all left-button click onsets (0→1 transitions) and interpolates
#' mouse position at each click time. Determines whether clicks are inside/outside
#' target box. Also detects right/middle button presses for contamination checks.
#' 
#' CRITICAL: Detects click ONSETS (button press events), not held states.
#' Because trials end when clicking inside box, multiple inside-clicks are impossible.
#' But multiple outside-clicks ARE possible (trial continues until inside-click).
#' 
#' @param x_str JSON string of X coordinates
#' @param y_str JSON string of Y coordinates
#' @param t_str JSON string of timestamps
#' @param lb_str JSON string of left button states (0 or 1)
#' @param rb_str JSON string of right button states
#' @param mb_str JSON string of middle button states
#' @param box Box configuration list
#' @return List with:
#'   - clicks: tibble(rt, x, y, inside) - all left-click onsets
#'   - qc: tibble of QC flags (parse failures, button contamination)
extract_left_clicks <- function(x_str, y_str, t_str, lb_str, rb_str, mb_str, box) {
  
  # Parse all input arrays
  px  <- safe_parse_vec(x_str)
  py  <- safe_parse_vec(y_str)
  pt  <- safe_parse_vec(t_str)
  plb <- safe_parse_vec(lb_str)
  prb <- safe_parse_vec(rb_str)
  pmb <- safe_parse_vec(mb_str)
  
  # Initialize QC flags
  qc <- tibble(
    parse_failed_time    = pt$parse_failed,
    parse_failed_xy      = px$parse_failed | py$parse_failed,
    parse_failed_buttons = plb$parse_failed | prb$parse_failed | pmb$parse_failed
  )
  
  # CRITICAL FIX #3: Validate vector length consistency
  # Check that all successfully parsed vectors have compatible lengths
  vec_lengths <- c(
    if (!px$parse_failed) length(px$vec) else NA_integer_,
    if (!py$parse_failed) length(py$vec) else NA_integer_,
    if (!pt$parse_failed) length(pt$vec) else NA_integer_,
    if (!plb$parse_failed) length(plb$vec) else NA_integer_,
    if (!prb$parse_failed) length(prb$vec) else NA_integer_,
    if (!pmb$parse_failed) length(pmb$vec) else NA_integer_
  )
  vec_lengths <- vec_lengths[!is.na(vec_lengths)]
  
  # Flag if lengths are inconsistent (differ by more than 1 sample)
  # Allow ±1 difference for edge cases in PsychoPy logging
  qc <- qc %>% mutate(
    mismatched_lengths = length(unique(vec_lengths)) > 1 && 
                         (max(vec_lengths) - min(vec_lengths)) > 1
  )
  
  # Check for critical parse failures
  if (qc$parse_failed_time || length(pt$vec) < 2) {
    return(list(
      clicks = tibble(),
      qc = qc %>% mutate(
        any_rb_nonzero = NA,
        any_mb_nonzero = NA
      )
    ))
  }
  
  # Align all vectors to time length
  nT <- length(pt$vec)
  t  <- pt$vec
  x  <- align_to_n(px$vec,  nT, NA_real_)
  y  <- align_to_n(py$vec,  nT, NA_real_)
  lb <- align_to_n(plb$vec, nT, 0)
  rb <- align_to_n(prb$vec, nT, 0)
  mb <- align_to_n(pmb$vec, nT, 0)
  
  # Convert to relative time (from trial onset)
  t_rel <- t - t[1]
  
  # Detect left-button click onsets (0→1 transitions)
  # lag() shifts vector: [0,0,1,1,0] → [NA,0,0,1,1]
  # We find positions where current=1 AND previous=0
  lb_down   <- lb > 0
  lb_onsets <- which(lb_down & !dplyr::lag(lb_down, default = FALSE))
  
  # Check for button contamination (ANY press of right/middle anywhere in trial)
  qc <- qc %>%
    mutate(
      any_rb_nonzero = any(rb > 0, na.rm = TRUE),
      any_mb_nonzero = any(mb > 0, na.rm = TRUE)
    )
  
  # If no left-clicks detected, return empty
  if (length(lb_onsets) == 0) {
    return(list(clicks = tibble(), qc = qc))
  }
  
  # Get click times and interpolate positions at those exact times
  t_click <- t_rel[lb_onsets]
  xy <- t(sapply(t_click, interp_xy, t = t_rel, x = x, y = y))
  inside <- inside_box(xy[, 1], xy[, 2], box)
  
  # Create clicks tibble
  clicks <- tibble(
    rt = t_click,
    x = xy[, 1],
    y = xy[, 2],
    inside = inside
  ) %>% 
    filter(is.finite(rt), is.finite(x), is.finite(y))
  
  list(clicks = clicks, qc = qc)
}

#' Detect any button clicks (for NoGo trials)
#' 
#' Checks for ANY button press (left, right, or middle) anywhere in the trial.
#' CRITICAL FIX: Returns NA if parsing fails (prevents corrupted data from
#' appearing as "no clicks" and inflating NoGo accuracy).
#' 
#' @param lb_str JSON string of left button states
#' @param rb_str JSON string of right button states
#' @param mb_str JSON string of middle button states
#' @return Tibble with click flags (NA if parse failed)
compute_any_click <- function(lb_str, rb_str, mb_str) {
  plb <- safe_parse_vec(lb_str)
  prb <- safe_parse_vec(rb_str)
  pmb <- safe_parse_vec(mb_str)
  
  parse_failed <- plb$parse_failed | prb$parse_failed | pmb$parse_failed
  
  # CRITICAL FIX: If parse failed, return NA (not FALSE)
  # This prevents corrupted trials from being scored as "correct"
  tibble(
    parse_failed_buttons = parse_failed,
    any_click = if (parse_failed) NA else
      (any(plb$vec > 0, na.rm = TRUE) | 
         any(prb$vec > 0, na.rm = TRUE) | 
         any(pmb$vec > 0, na.rm = TRUE)),
    any_left  = if (parse_failed) NA else any(plb$vec > 0, na.rm = TRUE),
    any_right = if (parse_failed) NA else any(prb$vec > 0, na.rm = TRUE)
  )
}

#' Detect stopping behavior in NoGo trials
#' 
#' Uses velocity-based stopping detection with robust edge-case handling:
#' 1. No movement: max velocity < threshold AND displacement < threshold → RT=0
#' 2. Movement then stop: finds peak velocity, then searches for sustained 
#'    low-velocity period (>150ms below threshold) after peak
#' 3. Validates stopping by checking post-stop period (250ms after stop onset)
#' 
#' CRITICAL FIXES:
#' - Handles NA sample_dt (prevents crashes)
#' - Checks loop bounds (prevents out-of-bounds indexing)
#' - Validates post-stop period AFTER detected stop (not at trial end)
#' 
#' @param x_str JSON string of X coordinates
#' @param y_str JSON string of Y coordinates  
#' @param t_str JSON string of timestamps
#' @param nogo_cfg NoGo configuration list
#' @return List with:
#'   - stop_time: stopping latency (sec), 0 if no movement, NA if no stop
#'   - stopped: logical, TRUE if successfully stopped
#'   - outcome: character description of stopping behavior
#'   - parse_failed: logical, TRUE if data parsing failed
compute_nogo_stop <- function(x_str, y_str, t_str, nogo_cfg) {
  
  # Parse input
  pt <- safe_parse_vec(t_str)
  px <- safe_parse_vec(x_str)
  py <- safe_parse_vec(y_str)
  
  # Need at least 3 samples for velocity computation
  if (pt$parse_failed || length(pt$vec) < 3) {
    return(list(
      stop_time = NA_real_,
      stopped = FALSE,
      outcome = "too_short_or_bad_time",
      parse_failed = TRUE
    ))
  }
  
  # CRITICAL FIX #3: Validate vector length consistency
  vec_lengths <- c(
    if (!px$parse_failed) length(px$vec) else NA_integer_,
    if (!py$parse_failed) length(py$vec) else NA_integer_,
    if (!pt$parse_failed) length(pt$vec) else NA_integer_
  )
  vec_lengths <- vec_lengths[!is.na(vec_lengths)]
  
  # Warn if lengths are very different (>1 sample difference)
  if (length(unique(vec_lengths)) > 1 && (max(vec_lengths) - min(vec_lengths)) > 1) {
    # Continue processing but flag in outcome
    length_warning <- TRUE
  } else {
    length_warning <- FALSE
  }
  
  # Align vectors
  nT <- length(pt$vec)
  t  <- pt$vec
  x  <- align_to_n(px$vec, nT, NA_real_)
  y  <- align_to_n(py$vec, nT, NA_real_)
  
  # Check for missing coordinates
  valid <- is.finite(x) & is.finite(y)
  if (sum(valid) < 3) {
    return(list(
      stop_time = NA_real_,
      stopped = FALSE,
      outcome = "missing_xy",
      parse_failed = (px$parse_failed | py$parse_failed)
    ))
  }
  
  # Keep only valid samples
  last <- max(which(valid))
  x <- x[1:last]
  y <- y[1:last]
  t <- t[1:last]
  
  # Convert to relative time
  t_rel <- t - t[1]
  
  # Compute velocity
  dt <- diff(t_rel)
  dt[dt <= 0] <- NA_real_  # Handle non-monotonic time
  
  # CRITICAL FIX: Check if sample_dt is valid
  sample_dt <- suppressWarnings(median(dt, na.rm = TRUE))
  if (!is.finite(sample_dt) || sample_dt <= 0) {
    return(list(
      stop_time = NA_real_,
      stopped = FALSE,
      outcome = "bad_sampling_rate",
      parse_failed = TRUE
    ))
  }
  
  # Compute velocity (pixels per second)
  # NOTE: v[i] represents velocity BETWEEN time points t[i] and t[i+1]
  # Therefore v has length (n-1) where n = length(t_rel)
  v_raw <- sqrt(diff(x)^2 + diff(y)^2) / dt
  v_raw[!is.finite(v_raw)] <- NA_real_
  
  # CRITICAL FIX #4: Pad velocity vector to align with time indices
  # v[i] should represent velocity AT time point i (approximated from i-1 to i)
  # We pad at the START with NA since velocity is undefined before first movement
  v <- c(NA_real_, v_raw)
  # Now: v[i] ≈ velocity arriving at time point t_rel[i]
  # Length: v has same length as t_rel, x, y
  
  # Check if trial reached deadline
  full_like_deadline <- is.finite(max(t_rel)) &&
    max(t_rel) >= (nogo_cfg$deadline_sec - 2 * sample_dt)
  
  # --------------------------------------------------
  # Case 1: No movement at all
  # --------------------------------------------------
  # Use v_raw (exclude the NA we just added) for max velocity check
  max_v <- suppressWarnings(max(v_raw, na.rm = TRUE))
  if (!is.finite(max_v)) max_v <- Inf
  
  dist <- sqrt((x - x[1])^2 + (y - y[1])^2)
  max_dist <- suppressWarnings(max(dist, na.rm = TRUE))
  if (!is.finite(max_dist)) max_dist <- Inf
  
  if (max_v < nogo_cfg$v_thresh && max_dist < nogo_cfg$dist_thresh_no_move) {
    return(list(
      stop_time = 0,  # Convention: 0 = no movement initiated
      stopped = TRUE,
      outcome = if (full_like_deadline) {
        "no_movement_full_duration"
      } else {
        "no_movement_early"
      },
      parse_failed = FALSE
    ))
  }
  
  # --------------------------------------------------
  # Case 2: Movement detected - search for stopping
  # --------------------------------------------------
  
  # Check if all velocities are NA (excluding our padding)
  if (all(!is.finite(v_raw))) {
    return(list(
      stop_time = NA_real_,
      stopped = FALSE,
      outcome = "velocity_all_na",
      parse_failed = TRUE
    ))
  }
  
  # Find peak velocity (replace NA with -Inf for which.max)
  # Note: v[1] is NA (our padding), so peak will be >= 2
  peak <- which.max(replace(v, !is.finite(v), -Inf))
  
  # Calculate number of samples needed for min_still_sec
  n_still <- ceiling(nogo_cfg$min_still_sec / sample_dt)
  
  # CRITICAL FIX: Check if we have enough samples after peak
  # Prevents loop index errors when start > end
  if (length(v) - n_still + 1 <= peak + 1) {
    return(list(
      stop_time = NA_real_,
      stopped = FALSE,
      outcome = "too_short_after_peak",
      parse_failed = FALSE
    ))
  }
  
  # Search for sustained low-velocity period after peak
  # CRITICAL FIX #5: Handle NA values in velocity comparisons
  stop_idx <- NA_integer_
  for (i in (peak + 1):(length(v) - n_still + 1)) {
    # Check if window has enough valid samples
    v_window <- v[i:(i + n_still - 1)]
    
    # Require: (1) at least 50% valid samples, AND (2) all valid samples < threshold
    n_valid <- sum(is.finite(v_window))
    if (n_valid >= n_still * 0.5) {
      if (all(v_window[is.finite(v_window)] < nogo_cfg$v_thresh)) {
        stop_idx <- i
        break
      }
    }
  }
  
  # If no stopping detected
  if (is.na(stop_idx)) {
    return(list(
      stop_time = NA_real_,
      stopped = FALSE,
      outcome = if (full_like_deadline) {
        "no_stop_timeout"
      } else {
        "no_stop_early"
      },
      parse_failed = FALSE
    ))
  }
  
  # Get stopping time - now correctly aligned with time vector
  stop_time <- t_rel[stop_idx]
  n_post <- ceiling(nogo_cfg$post_still_sec / sample_dt)
  
  # Use last n_post samples (or all if shorter)
  v_post <- tail(v, min(length(v), n_post))
  
  # IMPROVEMENT: Handle NA values properly
  v_post_valid <- v_post[is.finite(v_post)]
  
  if (length(v_post_valid) == 0) {
    # No valid post samples - reject
    post_ok <- FALSE
  } else {
    # Check if enough samples are below threshold
    post_ok <- mean(v_post_valid < nogo_cfg$v_thresh) >= nogo_cfg$post_still_criterion
  }
  
  list(
    stop_time = if (post_ok) stop_time else NA_real_,
    stopped = post_ok,
    outcome = if (post_ok) {
      if (full_like_deadline) "stopped_near_deadline" else "stopped_early"
    } else {
      if (full_like_deadline) "no_stop_timeout" else "no_stop_early"
    },
    parse_failed = FALSE
  )
}
  

# ==============================================================================
# 4. DATA PROCESSING PIPELINE
# ==============================================================================

cat("==============================================================================\n")
cat("ULTIMATE Go/NoGo ACCURACY & RT RECALCULATION\n")
cat("==============================================================================\n\n")

# --------------------------------------------------
# Discover BIDS input files and process each independently
# --------------------------------------------------

input_files <- list.files(
  input, pattern = "_task-gonogo_beh\\.tsv$", full.names = TRUE, recursive = TRUE
)
cat("Found", length(input_files), "BIDS data files\n")

# Helper: process a single BIDS TSV and return scored tibble
process_one_file <- function(fpath) {
  dat <- read.delim(fpath, sep = "\t", stringsAsFactors = FALSE, na.strings = c("n/a", ""))
  n_in <- nrow(dat)

  # Extract session from participant suffix (e.g. "10a" -> subject 10, session 1)
  dat <- dat %>%
    mutate(
      subject_id = as.integer(str_replace(participant, "[ab]$", "")),
      session_actual = case_when(
        str_detect(participant, "a$") ~ 1L,
        str_detect(participant, "b$") ~ 2L,
        TRUE ~ NA_integer_
      )
    )

  # Trial-level metrics (unchanged algorithm)
  dat <- dat %>%
    rowwise() %>%
    mutate(
      metrics = list({
        left <- extract_left_clicks(
          mouse_resp.x, mouse_resp.y, mouse_resp.time,
          mouse_resp.leftButton, mouse_resp.rightButton, mouse_resp.midButton,
          box = BOX_CONFIG
        )
        click_info <- compute_any_click(
          mouse_resp.leftButton,
          mouse_resp.rightButton,
          mouse_resp.midButton
        )
        stop <- compute_nogo_stop(
          mouse_resp.x,
          mouse_resp.y,
          mouse_resp.time,
          nogo_cfg = NOGO_CONFIG
        )
        n_left_clicks <- nrow(left$clicks)
        first_left_inside <- n_left_clicks > 0 && left$clicks$inside[1]
        first_left_rt <- if (n_left_clicks > 0) left$clicks$rt[1] else NA_real_
        tibble(
          n_left_clicks = n_left_clicks,
          go_first_left_inside = first_left_inside,
          go_first_left_rt = first_left_rt,
          parse_failed_time = left$qc$parse_failed_time,
          parse_failed_xy = left$qc$parse_failed_xy,
          parse_failed_buttons = left$qc$parse_failed_buttons,
          any_rb_nonzero = left$qc$any_rb_nonzero,
          any_mb_nonzero = left$qc$any_mb_nonzero,
          any_click = click_info$any_click,
          any_left = click_info$any_left,
          any_right = click_info$any_right,
          nogo_stop_time = stop$stop_time,
          nogo_stopped = stop$stopped,
          nogo_outcome = stop$outcome,
          nogo_parse_failed = stop$parse_failed | click_info$parse_failed_buttons
        )
      })
    ) %>%
    ungroup() %>%
    unnest(metrics)

  # RT and accuracy (unchanged algorithm)
  dat <- dat %>%
    mutate(
      rt_combined = case_when(
        trial_type == "go" & go_first_left_inside ~ go_first_left_rt,
        trial_type == "nogo" & nogo_stopped & !is.na(any_click) & !any_click &
          nogo_outcome %in% c("no_movement_full_duration", "no_movement_early") ~ 0,
        trial_type == "nogo" & nogo_stopped & !is.na(any_click) & !any_click ~ nogo_stop_time,
        TRUE ~ NA_real_
      ),
      accuracy = case_when(
        trial_type == "go" ~ case_when(
          parse_failed_time | parse_failed_xy | parse_failed_buttons ~ NA_integer_,
          TRUE ~ as.integer(
            go_first_left_inside &
              n_left_clicks == 1 &
              !any_rb_nonzero &
              !any_mb_nonzero
          )
        ),
        trial_type == "nogo" ~ case_when(
          nogo_parse_failed ~ NA_integer_,
          is.na(any_click)  ~ NA_integer_,
          TRUE ~ as.integer(nogo_stopped & !any_click)
        ),
        TRUE ~ NA_integer_
      )
    )

  # Write BIDS output: sub-XXX/ses-XX/beh/sub-XXX_ses-XX_task-gonogo_desc-scored_beh.tsv
  # Derive sub/ses from the input file path
  m <- regmatches(fpath, regexpr("sub-[0-9]+/ses-[0-9]+", fpath))
  sub_id <- sub("/ses-.*", "", m)
  ses_id <- sub(".*ses-", "ses-", m)
  out_rel <- file.path(sub_id, ses_id, "beh",
                       paste0(sub_id, "_", ses_id, "_task-gonogo_desc-scored_beh.tsv"))
  out_path <- file.path(output, out_rel)
  dir.create(dirname(out_path), recursive = TRUE, showWarnings = FALSE)

  # Write TSV (BIDS: NA as empty, no row names)
  write.table(dat, out_path, sep = "\t", row.names = FALSE, col.names = TRUE,
              quote = FALSE, na = "")

  cat(sprintf("  %s -> %s (%d trials)\n", basename(fpath), out_rel, nrow(dat)))
  invisible(dat)
}

# Process all files
start_time <- Sys.time()
all_scored <- lapply(input_files, process_one_file)
end_time <- Sys.time()
cat(sprintf("Processed %d files in %.1f minutes\n", length(input_files),
            round(difftime(end_time, start_time, units = "mins"), 1)))

# Bind all for QC summary
dat_scored <- bind_rows(all_scored)

# ==============================================================================
# 5. QUALITY CONTROL & VALIDATION
# ==============================================================================

cat("\n")
cat("================================================================================\n")
cat("QUALITY CONTROL REPORT\n")
cat("================================================================================\n\n")

# --------------------------------------------------
# 5.1 Data completeness
# --------------------------------------------------

cat("--- DATA COMPLETENESS ---\n")
cat("Total trials:", nrow(dat_scored), "\n")
cat("Unique subjects:", length(unique(dat_scored$subject_id)), "\n")
cat("Unique participants (subject × session):", 
    length(unique(dat_scored$participant)), "\n\n")

cat("Trials per session:\n")
print(table(Session = dat_scored$session_actual, useNA = "ifany"))
cat("\n")

cat("Trials per trial type:\n")
print(table(TrialType = dat_scored$trial_type, useNA = "ifany"))
cat("\n")

# --------------------------------------------------
# 5.2 Parse failures
# --------------------------------------------------

cat("--- PARSE FAILURES (DATA QUALITY ISSUES) ---\n")
cat("Trials with time parse failures:", 
    sum(dat_scored$parse_failed_time, na.rm = TRUE), 
    sprintf("(%.2f%%)\n", 100 * mean(dat_scored$parse_failed_time, na.rm = TRUE)))

cat("Trials with XY parse failures:", 
    sum(dat_scored$parse_failed_xy, na.rm = TRUE),
    sprintf("(%.2f%%)\n", 100 * mean(dat_scored$parse_failed_xy, na.rm = TRUE)))

cat("Trials with button parse failures:", 
    sum(dat_scored$parse_failed_buttons, na.rm = TRUE),
    sprintf("(%.2f%%)\n", 100 * mean(dat_scored$parse_failed_buttons, na.rm = TRUE)))

cat("NoGo trials with parse failures:", 
    sum(dat_scored$nogo_parse_failed & dat_scored$trial_type == "nogo", na.rm = TRUE),
    sprintf("(%.2f%% of NoGo trials)\n\n", 
            100 * mean(dat_scored$nogo_parse_failed[dat_scored$trial_type == "nogo"], na.rm = TRUE)))

# --------------------------------------------------
# 5.3 Button contamination
# --------------------------------------------------

cat("--- BUTTON CONTAMINATION ---\n")
cat("Trials with right-button press:", 
    sum(dat_scored$any_rb_nonzero, na.rm = TRUE),
    sprintf("(%.2f%%)\n", 100 * mean(dat_scored$any_rb_nonzero, na.rm = TRUE)))

cat("Trials with middle-button press:", 
    sum(dat_scored$any_mb_nonzero, na.rm = TRUE),
    sprintf("(%.2f%%)\n\n", 100 * mean(dat_scored$any_mb_nonzero, na.rm = TRUE)))

# --------------------------------------------------
# 5.4 Go trial click patterns
# --------------------------------------------------

cat("--- GO TRIAL CLICK PATTERNS ---\n")
go_click_patterns <- dat_scored %>%
  filter(trial_type == "go") %>%
  count(n_left_clicks, go_first_left_inside) %>%
  arrange(desc(n))

cat("Distribution of left-click counts on Go trials:\n")
print(go_click_patterns)
cat("\n")

cat("Go trials with multiple clicks (exploratory behavior):\n")
multi_click <- dat_scored %>%
  filter(trial_type == "go", n_left_clicks > 1) %>%
  nrow()
cat(sprintf("%d trials (%.2f%% of Go trials)\n\n", 
            multi_click,
            100 * multi_click / sum(dat_scored$trial_type == "go")))

# --------------------------------------------------
# 5.5 NoGo outcomes
# --------------------------------------------------

cat("--- NOGO OUTCOMES ---\n")
nogo_outcome_table <- dat_scored %>%
  filter(trial_type == "nogo") %>%
  count(nogo_outcome, nogo_stopped) %>%
  arrange(desc(n))
print(nogo_outcome_table)
cat("\n")

# --------------------------------------------------
# 5.6 Accuracy rates
# --------------------------------------------------

cat("--- OVERALL ACCURACY ---\n")
accuracy_summary <- dat_scored %>%
  group_by(trial_type) %>%
  summarise(
    n_total = n(),
    n_correct = sum(accuracy == 1, na.rm = TRUE),
    n_incorrect = sum(accuracy == 0, na.rm = TRUE),
    n_missing = sum(is.na(accuracy)),
    accuracy_rate = mean(accuracy, na.rm = TRUE),
    .groups = "drop"
  )
print(accuracy_summary)
cat("\n")

cat("--- ACCURACY BY SESSION & TRIAL TYPE ---\n")
accuracy_by_session <- dat_scored %>%
  group_by(session_actual, trial_type) %>%
  summarise(
    n = n(),
    n_correct = sum(accuracy == 1, na.rm = TRUE),
    accuracy_rate = mean(accuracy, na.rm = TRUE),
    .groups = "drop"
  )
print(accuracy_by_session)
cat("\n")

cat("--- ACCURACY BY SUBJECT ---\n")
accuracy_by_subject <- dat_scored %>%
  group_by(subject_id, session_actual, trial_type) %>%
  summarise(
    n_trials = n(),
    n_correct = sum(accuracy == 1, na.rm = TRUE),
    accuracy_rate = mean(accuracy, na.rm = TRUE),
    .groups = "drop"
  ) %>%
  pivot_wider(
    names_from = c(session_actual, trial_type),
    values_from = accuracy_rate,
    names_prefix = "acc_s"
  )

print(head(accuracy_by_subject, 10))
cat("... (showing first 10 subjects)\n\n")

# Identify low-performing subjects
low_performers <- accuracy_by_subject %>%
  rowwise() %>%
  mutate(
    min_go_acc = min(c_across(starts_with("acc_s") & ends_with("_go")), na.rm = TRUE)
  ) %>%
  filter(min_go_acc < 0.6)

if (nrow(low_performers) > 0) {
  cat("WARNING: Subjects with <60% Go accuracy in any session:\n")
  print(low_performers %>% select(subject_id, starts_with("acc_s")))
  cat("\n")
}

# --------------------------------------------------
# 5.7 RT distributions
# --------------------------------------------------

cat("--- REACTION TIME DISTRIBUTIONS ---\n")
rt_summary <- dat_scored %>%
  filter(!is.na(rt_combined)) %>%
  group_by(trial_type, session_actual) %>%
  summarise(
    n = n(),
    mean_rt = mean(rt_combined),
    sd_rt = sd(rt_combined),
    median_rt = median(rt_combined),
    min_rt = min(rt_combined),
    max_rt = max(rt_combined),
    n_below_100ms = sum(rt_combined < 0.1),
    n_above_1500ms = sum(rt_combined > 1.5),
    .groups = "drop"
  )
print(rt_summary)
cat("\n")

# RT outliers
if (any(dat_scored$rt_combined < 0.1, na.rm = TRUE)) {
  cat("WARNING: Detected RTs < 100ms (possible anticipatory responses)\n")
  anticipatory <- dat_scored %>%
    filter(rt_combined < 0.1) %>%
    count(subject_id, trial_type) %>%
    arrange(desc(n))
  print(anticipatory)
  cat("\n")
}

# --------------------------------------------------
# 5.8 Session pairing check
# --------------------------------------------------

cat("--- SESSION PAIRING CHECK (FOR TEST-RETEST RELIABILITY) ---\n")
session_pairs <- dat_scored %>%
  select(subject_id, session_actual) %>%
  distinct() %>%
  group_by(subject_id) %>%
  summarise(
    sessions_present = paste(sort(session_actual), collapse = ","),
    n_sessions = n(),
    .groups = "drop"
  )

cat("Subjects with both sessions:", sum(session_pairs$n_sessions == 2), "\n")
cat("Subjects with only one session:", sum(session_pairs$n_sessions == 1), "\n")

if (any(session_pairs$n_sessions == 1)) {
  cat("\nWARNING: Subjects with incomplete sessions (cannot compute test-retest reliability):\n")
  incomplete <- session_pairs %>% filter(n_sessions == 1)
  print(incomplete)
}
cat("\n")

cat("================================================================================\n")
cat("END OF QC REPORT\n")
cat("================================================================================\n\n")

# ==============================================================================
# 6. OUTPUT SUMMARY
# ==============================================================================

# BIDS TSV files were written per-input-file by process_one_file().
# Confirm the full set.

out_files <- list.files(
  output,
  pattern = "_desc-scored_beh\\.tsv$",
  recursive = TRUE,
  full.names = TRUE
)

# --------------------------------------------------
# 6.1 QC plots (supplementary, non-BIDS)
# --------------------------------------------------
# Plots are written to <output>/QC_plots/ alongside the BIDS sub/ses TSVs.
# They are supplementary artifacts (not part of the desc-scored derivative
# glob) and are skipped if ggplot2 is unavailable.

qc_plot_dir <- file.path(output, "QC_plots")

if (requireNamespace("ggplot2", quietly = TRUE)) {
  dir.create(qc_plot_dir, recursive = TRUE, showWarnings = FALSE)

  # RT distribution plot
  p_rt <- ggplot2::ggplot(
    dat_scored %>% filter(!is.na(rt_combined), rt_combined > 0),
    ggplot2::aes(x = rt_combined, fill = as.factor(session_actual))
  ) +
    ggplot2::geom_histogram(bins = 50, alpha = 0.6, position = "identity") +
    ggplot2::facet_grid(session_actual ~ trial_type, scales = "free_y") +
    ggplot2::labs(
      title = "RT Distributions by Trial Type and Session",
      x = "Reaction Time (sec)",
      y = "Count",
      fill = "Session"
    ) +
    ggplot2::theme_minimal() +
    ggplot2::theme(legend.position = "none")
  ggplot2::ggsave(
    file.path(qc_plot_dir, "RT_distributions.png"),
    p_rt,
    width = 10, height = 6, dpi = 300
  )

  # Accuracy by subject plot
  p_acc <- ggplot2::ggplot(
    accuracy_by_subject %>%
      tidyr::pivot_longer(
        cols = dplyr::starts_with("acc_s"),
        names_to = "condition",
        values_to = "accuracy"
      ),
    ggplot2::aes(x = condition, y = accuracy)
  ) +
    ggplot2::geom_boxplot() +
    ggplot2::geom_jitter(alpha = 0.3, width = 0.2) +
    ggplot2::labs(
      title = "Accuracy Distribution by Session and Trial Type",
      x = "Condition",
      y = "Accuracy Rate"
    ) +
    ggplot2::theme_minimal() +
    ggplot2::theme(axis.text.x = ggplot2::element_text(angle = 45, hjust = 1))
  ggplot2::ggsave(
    file.path(qc_plot_dir, "Accuracy_by_subject.png"),
    p_acc,
    width = 8, height = 6, dpi = 300
  )

  cat("Saved QC plots to:", qc_plot_dir, "\n")
} else {
  cat("ggplot2 not available; skipping QC plots\n")
}

cat("\n")
cat("================================================================================\n")
cat("PROCESSING COMPLETE\n")
cat("================================================================================\n")
cat("Total trials processed:", nrow(dat_scored), "\n")
cat("Output BIDS TSV files written:", length(out_files), "\n")
cat("Output root:", output, "\n")
cat("\n")


