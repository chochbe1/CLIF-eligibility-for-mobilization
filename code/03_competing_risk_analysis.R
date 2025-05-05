#!/usr/bin/env Rscript
# ────────────────────────────────────────────────────────────
#  Competing‑risk analysis – CIFs  +  Fine‑Gray sub‑hazard
#  Outputs ( ../output/final/ ) :
#     patel_cif.csv, team_cif.csv, yellow_cif.csv, green_cif.csv
#     cif_overlay.png      • median_times.csv
#     subhazard_summary.json  (coef, var‑cov, n, events)
#     fg_model_summary.txt    (plain‑text model summary)
#     events_by_group.csv     (cross‑tab for meta‑analysis)
# ────────────────────────────────────────────────────────────

## 1 ── packages ----------------------------------------------------------
pkgs <- c("arrow", "cmprsk", "data.table", "dplyr", "jsonlite")
need <- pkgs[!vapply(pkgs, requireNamespace, logical(1), quietly = TRUE)]
if (length(need))
  install.packages(need, repos = "https://cloud.r-project.org")
invisible(lapply(pkgs, library, character.only = TRUE))

## 2 ── helpers -----------------------------------------------------------
read_parquet <- function(path) arrow::open_dataset(path) |> collect()

compute_cif_df <- function(time, status, cause = 1, alpha = 0.05) {
  fit <- cmprsk::cuminc(ftime = time, fstatus = status, cencode = 0)
  key <- sprintf("%d %d", cause, cause)
  if (!key %in% names(fit)) stop("cause ", cause, " not found")
  
  ci  <- fit[[key]]
  out <- data.frame(time = ci$time, est = ci$est)
  
  if (!is.null(ci$lower) && !is.null(ci$upper)) {
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
  cros <- which(df$est >= 0.5)
  if (length(cros)) df$time[cros[1]] else Inf
}

analyse_one <- function(name, parquet_path, out_csv) {
  dat <- read_parquet(parquet_path) |>
    transmute(time = t_event, status = outcome)
  
  cif <- compute_cif_df(dat$time, dat$status)
  fwrite(cif, out_csv)
  
  list(name   = name,
       cif    = cif,
       median = median_time(cif),
       fit    = attr(cif, "cuminc"))
}

## 3 ── paths -------------------------------------------------------------
# Set project root
project_root <- normalizePath(getwd())

# Define input parquet paths relative to root
paths <- list(
  Patel  = file.path(project_root,"..", "output", "intermediate", "competing_risk_patel_final.parquet"),
  TEAM   = file.path(project_root,"..", "output", "intermediate", "competing_risk_team_final.parquet"),
  Yellow = file.path(project_root,"..", "output", "intermediate", "competing_risk_yellow_final.parquet"),
  Green  = file.path(project_root,"..", "output", "intermediate", "competing_risk_green_final.parquet")
)

# Define output directory and create it if missing
out_dir <- file.path(project_root,"..", "output", "final")
dir.create(out_dir, showWarnings = FALSE, recursive = TRUE)

## 4 ── CIF analysis ------------------------------------------------------
results <- lapply(names(paths), \(nm) analyse_one(
  name        = nm,
  parquet_path = paths[[nm]],
  out_csv      = file.path(out_dir, sprintf("%s_cif.csv", tolower(nm)))
))

## 4·a  overlay plot (base graphics) --------------------------------------
png(file.path(out_dir, "cif_overlay.png"), width = 1800, height = 1200, res = 200)
cols <- c(Patel="maroon", TEAM="blue", Yellow="darkgoldenrod1", Green="darkgreen")

plot(results[[1]]$fit$`1 1`$time, results[[1]]$fit$`1 1`$est,
     type="l", lwd = 2, col = cols[results[[1]]$name],
     xlab="Time (hours)", ylab="Cumulative Incidence Probability",
     main="Competing-risk: All criteria")
for (i in 2:length(results))
  lines(results[[i]]$fit$`1 1`$time, results[[i]]$fit$`1 1`$est,
        col = cols[results[[i]]$name], lwd = 2)
legend("bottomright", legend = names(cols), col = cols, lwd = 2, lty = 1)
dev.off()
cat("cif_overlay.png written\n")

## 4·b median times -------------------------------------------------------
median_tbl <- data.frame(
  Criterion = sapply(results, `[[`, "name"),
  Median_h  = sapply(results, `[[`, "median")
)
fwrite(median_tbl, file.path(out_dir, "median_times.csv"))
print(median_tbl, row.names = FALSE)

## 5 ── Fine–Gray sub‑hazard model ---------------------------------------
bind_for_fg <- function(path, grp) {
  as.data.table(read_parquet(path))[, .(
    encounter_block, t_event, outcome, group = grp)]
}
cr_data <- rbindlist(list(
  bind_for_fg(paths$Patel,  "Patel"),
  bind_for_fg(paths$TEAM,   "TEAM"),
  bind_for_fg(paths$Yellow, "Yellow"),
  bind_for_fg(paths$Green,  "Green")
))
cr_data[, group := factor(group, levels = c("Patel","TEAM","Yellow","Green"))]

# events by cause (overall) and by (group × cause)
events_total      <- as.numeric(table(cr_data$outcome))
names(events_total) <- names(table(cr_data$outcome))

events_by_group <- with(cr_data, table(group, outcome))
fwrite(as.data.frame(events_by_group),
       file.path(out_dir, "events_by_group.csv"))

fg <- crr(
  ftime   = cr_data$t_event,
  fstatus = cr_data$outcome,
  cov1    = model.matrix(~ group, cr_data)[, -1]   # drop intercept (Patel ref.)
)

# save text summary
capture.output(summary(fg),
               file = file.path(out_dir, "fg_model_summary.csv"))
print(summary(fg))

# export JSON for meta‑analysis
fg_export <- list(
  coef   = setNames(unname(fg$coef), colnames(fg$coef)),
  var    = fg$var,
  n      = fg$n,
  events = events_total            # overall events by cause
)
write_json(fg_export,
           path = file.path(out_dir, "subhazard_summary.json"),
           digits = 8, auto_unbox = TRUE)

cat("\n Fine–Gray objects written to",
    normalizePath(out_dir), "\n")
