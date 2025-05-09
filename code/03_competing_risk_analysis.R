#!/usr/bin/env Rscript
# ────────────────────────────────────────────────────────────
#  Competing‑risk analysis – full follow‑up  +  first‑72‑h
#  Outputs (../output/final/)     
# ────────────────────────────────────────────────────────────

## 1 ── packages ----------------------------------------------------------
pkgs <- c("arrow", "cmprsk", "data.table", "dplyr", "jsonlite", "ggplot2")
need <- pkgs[!vapply(pkgs, requireNamespace, logical(1), quietly = TRUE)]
if (length(need))
  install.packages(need, repos = "https://cloud.r-project.org")
invisible(lapply(pkgs, library, character.only = TRUE))

## 2 ── helpers -----------------------------------------------------------
read_parquet <- function(path) arrow::open_dataset(path) |> collect()

# ---- CIF &  CI extractor -----------------------------------------------
cif_df <- function(time, status, max_h = Inf, cause = 1, alpha = 0.05) {
  # censor after max_h
  time    <- pmin(time, max_h)
  status  <- ifelse(time >= max_h & status == cause, 0, status)
  
  fit <- cuminc(ftime = time, fstatus = status, cencode = 0)
  key <- sprintf("%d %d", cause, cause)
  
  ci  <- fit[[key]]
  out <- data.frame(time = ci$time, est = ci$est)
  
  if (!is.null(ci$lower)) {
    out$lower <- ci$lower; out$upper <- ci$upper
  } else if (!is.null(ci$var)) {
    z <- qnorm(0.975)
    out$lower <- pmax(0, ci$est - z*sqrt(ci$var))
    out$upper <- pmin(1, ci$est + z*sqrt(ci$var))
  } else {
    out$lower <- out$upper <- NA
  }
  attr(out, "cuminc") <- fit
  out
}

median_time <- function(df) {
  x <- which(df$est >= .5)
  if (length(x)) df$time[x[1]] else Inf
}

analyse_one <- function(name, path, out_csv, max_h = Inf) {
  dat <- read_parquet(path)[, c("t_event", "outcome")]
  setnames(dat, c("t_event", "outcome"), c("time", "status"))
  cif <- cif_df(dat$time, dat$status, max_h = max_h)
  fwrite(cif, out_csv)
  list(name = name,
       cif = cif,
       median = median_time(cif),
       fit = attr(cif, "cuminc"))
}

## 3 ── paths -------------------------------------------------------------
# Get current working directory
current_dir <- normalizePath(getwd())

# Check if it ends with "code"
if (basename(current_dir) == "code") {
  project_root <- current_dir
} else {
  project_root <- file.path(current_dir, "code")
}

# Optionally set the working directory
setwd(project_root)

root   <- normalizePath(getwd())
paths  <- list(
  Patel  = file.path(root, "..", "output", "intermediate",
                     "competing_risk_patel_final.parquet"),
  TEAM   = file.path(root, "..", "output", "intermediate",
                     "competing_risk_team_final.parquet"),
  Yellow = file.path(root, "..", "output", "intermediate",
                     "competing_risk_yellow_final.parquet"),
  Green  = file.path(root, "..", "output", "intermediate",
                     "competing_risk_green_final.parquet")
)
out_dir <- file.path(root, "..", "output", "final")
dir.create(out_dir, recursive = TRUE, showWarnings = FALSE)
dir.create(file.path(out_dir, "graphs"), showWarnings = FALSE)

## 4 ── CIF full follow‑up -----------------------------------------------
cat("── CIF (full follow‑up)\n")
res_full <- lapply(names(paths), \(nm)
                   analyse_one(nm, paths[[nm]],
                               file.path(out_dir, sprintf("%s_cif.csv", tolower(nm)))))

## 4·a  overlay plot ------------------------------------------------------
cols <- c(Patel="maroon", TEAM="blue", Yellow="darkgoldenrod1", Green="darkgreen")
png(file.path(out_dir, "graphs", "cif_overlay.png"),
    width = 1800, height = 1200, res = 200)
plot(0, 0, type="n", xlim=c(0, max(sapply(res_full, \(x) max(x$cif$time)))),
     ylim=c(0,1), xlab="Time (hours)", ylab="CIF", main="All follow‑up")
for (r in res_full)
  lines(r$cif$time, r$cif$est, col = cols[r$name], lwd = 2)
legend("bottomright", legend = names(cols), col = cols, lwd = 2, lty = 1)
dev.off()

fwrite(data.frame(Criterion = sapply(res_full, `[[`, "name"),
                  Median_h  = sapply(res_full, `[[`, "median")),
       file.path(out_dir, "median_times.csv"))

## 5 ── CIF truncated at 72 h --------------------------------------------
cat("── CIF (first 72 h)\n")
res_72 <- lapply(names(paths), \(nm)
                 analyse_one(nm, paths[[nm]],
                             file.path(out_dir,
                                       sprintf("cif_72hrs_%s.csv", tolower(nm))),
                             max_h = 72))

png(file.path(out_dir, "graphs", "cif_overlay_72hrs.png"),
    width = 1800, height = 1200, res = 200)
plot(0, 0, type="n", xlim = c(0,72), ylim=c(0,1),
     xlab="Time (hours)", ylab="CIF", main="First 72 h")
for (r in res_72)
  lines(r$cif$time, r$cif$est, col = cols[r$name], lwd = 2)
legend("bottomright", legend = names(cols), col = cols, lwd = 2, lty = 1)
dev.off()

fwrite(data.frame(Criterion = sapply(res_72, `[[`, "name"),
                  Median_h  = sapply(res_72, `[[`, "median")),
       file.path(out_dir, "median_times_72hrs.csv"))

## 6 ── Fine–Gray sub‑hazard  (full follow‑up & 72h) ---------------------
bind_for_fg <- \(path, grp)
as.data.table(read_parquet(path))[, .(encounter_block, t_event, outcome,
                                      group = grp)]

make_fg <- function(max_h = Inf, suffix = "") {
  
  cr <- rbindlist(list(
    bind_for_fg(paths$Patel,  "Patel"),
    bind_for_fg(paths$TEAM,   "TEAM"),
    bind_for_fg(paths$Yellow, "Yellow"),
    bind_for_fg(paths$Green,  "Green")
  ))
  
  # censor after max_h
  cr[, `:=`(
    t_event = pmin(t_event, max_h),
    outcome = ifelse(t_event >= max_h & outcome == 1, 0L, outcome)
  )]
  
  cr[, group := factor(group, levels = c("Patel","TEAM","Yellow","Green"))]
  
  # events tables
  events_total     <- table(cr$outcome)
  events_by_group  <- with(cr, table(group, outcome))
  fwrite(as.data.frame(events_by_group),
         file.path(out_dir,
                   sprintf("events_by_group%s.csv", suffix)))
  
  fg <- crr(
    ftime   = cr$t_event,
    fstatus = cr$outcome,
    cov1    = model.matrix(~ group, cr)[,-1]
  )
  
  # save summary
  capture.output(summary(fg),
                 file = file.path(out_dir,
                                  sprintf("fg_model_summary%s.txt", suffix)))
  
  fg_export <- list(
    coef   = setNames(unname(fg$coef), colnames(fg$coef)),
    var    = fg$var,
    n      = fg$n,
    events = as.numeric(events_total)
  )
  write_json(fg_export,
             path = file.path(out_dir,
                              sprintf("subhazard_summary%s.json", suffix)),
             digits = 8, auto_unbox = TRUE)
  invisible(NULL)
}

cat("── Fine–Gray (full follow‑up)\n")
make_fg(suffix = "")

cat("── Fine–Gray (first 72 h)\n")
make_fg(max_h = 72, suffix = "_72hrs")

cat("\nAll outputs written to", normalizePath(out_dir), "\n")
