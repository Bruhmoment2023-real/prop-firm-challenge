# Bibliometrix analysis for one paper's literature corpus.
# Usage (PowerShell):
#   $env:R_LIBS_USER='D:\Research-Publishing\_tools\R-lib;C:\Users\seans\AppData\Local\R\win-library\4.5'
#   & "C:\Program Files\R\R-4.5.3\bin\Rscript.exe" bibliometrix_analysis.R <bibliometrics_dir>
# Input : <dir>/data/clean/bibliometrix_input.csv (built by python/pipeline.py from OpenAlex records)
# Output: <dir>/figures/R_*.png|svg|html, <dir>/tables/R_*.csv, <dir>/vosviewer/*, <dir>/data/clean/*.rds
suppressPackageStartupMessages({
  library(bibliometrix); library(ggplot2); library(dplyr); library(tidyr); library(igraph)
  library(ggrepel); library(jsonlite); library(Matrix)
})
args <- commandArgs(TRUE)
B <- normalizePath(args[1], winslash = "/")
if (!dir.exists("D:/")) stop("D: is missing")
FIG <- file.path(B, "figures"); TAB <- file.path(B, "tables"); VOS <- file.path(B, "vosviewer")
for (d in c(FIG, TAB, VOS)) dir.create(d, showWarnings = FALSE, recursive = TRUE)
cfg <- fromJSON(file.path(B, "config.json"), simplifyVector = FALSE)
PAPER <- cfg$paper_id
set.seed(42)

M <- read.csv(file.path(B, "data/clean/bibliometrix_input.csv"), stringsAsFactors = FALSE, encoding = "UTF-8", na.strings = "NA_never")
for (cc in names(M)) if (is.character(M[[cc]])) M[[cc]][is.na(M[[cc]])] <- ""
M$TC <- as.numeric(M$TC); M$PY <- as.numeric(M$PY); M$LCS <- as.numeric(M$LCS)
M <- M[!is.na(M$PY), ]
rownames(M) <- M$SR
class(M) <- c("bibliometrixDB", "data.frame")
# ---- optional Scopus / Web of Science exports dropped by Sean or a mentor (none on this machine at build time)
drop <- file.path(B, "scopus-drop"); dir.create(drop, showWarnings = FALSE)
dropfiles <- list.files(drop, pattern = "\\.(csv|bib|txt)$", full.names = TRUE, ignore.case = TRUE)
drop_status <- data.frame(item = "scopus-drop", status = "EMPTY - no Scopus/WoS export to merge; corpus is OpenAlex-only", files = 0, records_added = 0)
if (length(dropfiles) > 0) {
  drop_status <- tryCatch({
    parts <- lapply(dropfiles, function(f) {
      ext <- tolower(tools::file_ext(f)); head3 <- paste(readLines(f, n = 5, warn = FALSE), collapse = " ")
      src <- if (ext == "csv" || grepl("scopus", head3, ignore.case = TRUE)) "scopus" else "wos"
      convert2df(f, dbsource = src, format = c(csv = "csv", bib = "bibtex", txt = "plaintext")[[ext]])
    })
    ext_all <- if (length(parts) > 1) Reduce(function(a, b) mergeDbSources(a, b, remove.duplicated = TRUE), parts) else parts[[1]]
    n0 <- nrow(M)
    keep_new <- ext_all[!(toupper(ext_all$DI) %in% M$DI[M$DI != ""]) & !(toupper(ext_all$TI) %in% M$TI), ]
    for (cc in setdiff(names(M), names(keep_new))) keep_new[[cc]] <- if (is.numeric(M[[cc]])) 0 else ""
    keep_new$SUBLIT <- "scopus_wos_import"; keep_new$DB <- "ISI"
    M <- rbind(as.data.frame(M), keep_new[, names(M)])
    M$SR <- make.unique(M$SR, sep = "-"); rownames(M) <- M$SR; class(M) <- c("bibliometrixDB", "data.frame")
    data.frame(item = "scopus-drop", status = "merged (records are NOT rule-screened; check them)", files = length(dropfiles), records_added = nrow(M) - n0)
  }, error = function(e) data.frame(item = "scopus-drop", status = paste("FAILED to merge:", conditionMessage(e)), files = length(dropfiles), records_added = 0))
}
dir.create(file.path(B, "tables"), showWarnings = FALSE)
write.csv(drop_status, file.path(B, "tables", "R_scopus_drop_status.csv"), row.names = FALSE)
cat("scopus-drop:", drop_status$status, "\n")
saveRDS(M, file.path(B, "data/clean/bibliometrix_M.rds"))
master <- read.csv(file.path(B, "data/clean/master.csv"), stringsAsFactors = FALSE, encoding = "UTF-8", fileEncoding = "UTF-8-BOM")
saveRDS(master, file.path(B, "data/clean/master.rds"))
N <- nrow(M); SMALL <- N < 50
THIS_YEAR <- as.numeric(format(Sys.Date(), "%Y"))
sub_labels <- sapply(cfg$sublits, function(s) s$label)
cat("Corpus:", N, "documents\n")

# ---------------------------------------------------------------- helpers
CAPS <- list(); LOG <- list()
cap <- function(file, title, what, how, caution) {
  CAPS[[length(CAPS) + 1]] <<- list(file = file, title = title, what = what, how = how, caution = caution, tool = "R / bibliometrix")
}
run <- function(name, expr) {
  t0 <- Sys.time()
  r <- tryCatch({ force(expr); "ok" }, error = function(e) paste("FAILED:", conditionMessage(e)))
  while (!is.null(dev.list())) dev.off()
  LOG[[length(LOG) + 1]] <<- data.frame(analysis = name, status = r, seconds = round(as.numeric(difftime(Sys.time(), t0, units = "secs")), 1))
  cat(sprintf("[%s] %s\n", name, r))
}
skip <- function(name, why) { LOG[[length(LOG) + 1]] <<- data.frame(analysis = name, status = paste("SKIPPED:", why), seconds = 0); cat(sprintf("[%s] SKIPPED: %s\n", name, why)) }
savep <- function(p, name, w = 10, h = 6.5) {
  ggsave(file.path(FIG, paste0(name, ".png")), p, width = w, height = h, dpi = 220, bg = "white")
  try(ggsave(file.path(FIG, paste0(name, ".svg")), p, width = w, height = h, bg = "white"), silent = TRUE)
}
wcsv <- function(x, name) write.csv(x, file.path(TAB, paste0(name, ".csv")), row.names = FALSE, fileEncoding = "UTF-8")
th <- theme_minimal(base_size = 12) + theme(plot.title = element_text(face = "bold"), plot.title.position = "plot", legend.position = "bottom")
`%||%` <- function(a, b) if (is.null(a)) b else a
SRC <- sprintf("Corpus: %d records (OpenAlex metadata). Paper %s.", N, PAPER)
splitc <- function(x) { v <- trimws(unlist(strsplit(x, ";"))); v[v != ""] }
shorten <- function(x, n = 55) ifelse(nchar(x) > n, paste0(substr(x, 1, n - 1), "\u2026"), x)
vos_export <- function(NetMatrix, name, n = 200, wlab = "Occurrences") {
  d <- Matrix::diag(NetMatrix); ord <- order(d, decreasing = TRUE)[seq_len(min(n, length(d)))]
  A <- as.matrix(NetMatrix[ord, ord]); labs <- rownames(A); diag(A) <- 0
  map <- data.frame(id = seq_along(labs), label = labs, w = d[ord]); names(map)[3] <- paste0("weight<", wlab, ">")
  write.table(map, file.path(VOS, paste0(name, "_map.txt")), sep = "\t", row.names = FALSE, quote = FALSE)
  idx <- which(A > 0 & upper.tri(A), arr.ind = TRUE)
  net <- data.frame(i = idx[, 1], j = idx[, 2], s = A[idx])
  write.table(net, file.path(VOS, paste0(name, "_network.txt")), sep = "\t", row.names = FALSE, col.names = FALSE, quote = FALSE)
  invisible(nrow(net))
}
netfig <- function(NetMatrix, name, title, n = 50, normalize = "association", type = "fruchterman", sub = "", labelsize = 0.75, ...) {
  png(file.path(FIG, paste0(name, ".png")), width = 2800, height = 2400, res = 220)
  par(mar = c(4, 1, 3, 1))
  net <- networkPlot(NetMatrix, normalize = normalize, n = n, Title = title, type = type, size = 5, size.cex = TRUE, labelsize = labelsize,
                     label.cex = TRUE, cluster = "louvain", remove.isolates = TRUE, remove.multiple = FALSE, edgesize = 3, alpha = 0.7,
                     halo = FALSE, curved = FALSE, verbose = TRUE, ...)
  cr <- net$cluster_res
  if (!is.null(cr) && nrow(cr) > 0) {
    g <- net$graph
    top <- cr %>% group_by(cluster) %>% slice_max(order_by = pagerank_centrality, n = 1, with_ties = FALSE) %>% ungroup()
    cols <- sapply(top$vertex, function(v) { i <- which(tolower(V(g)$name) == tolower(v))[1]; if (is.na(i)) "grey50" else adjustcolor(V(g)$color[i], alpha.f = 1) })
    legend("bottomleft", legend = paste0("Cluster ", top$cluster, ": ", shorten(top$vertex, 38)), fill = cols, cex = 0.7, bty = "n", title = "Louvain clusters (most central node)")
    wcsv(cr, paste0(name, "_clusters"))
  }
  mtext(sub, side = 1, line = 2.5, cex = 0.75)
  dev.off()
  invisible(net)
}

N <- nrow(M); SMALL <- N < 50
STOPKW <- toupper(unlist(cfg$keyword_stoplist %||% list()))
  run("historiograph", {
    Mh <- M; Mh$CR[Mh$CR == ""] <- "NO REFERENCE LIST, 0, NONE"   # histNetwork fails on documents with an empty reference field
    hr <- histNetwork(Mh, min.citations = 1, sep = ";", verbose = FALSE)
    hp <- histPlot(hr, n = 25, size = 4, labelsize = 3, verbose = FALSE)
    savep(hp$g + labs(title = "Historiograph: direct citation network of the 25 most locally cited documents", subtitle = SRC), "R_28_historiograph", 13, 8)
    wcsv(hr$histData, "R_historiograph_data")
    cap("R_28_historiograph.png", "Historiograph (direct citation network)", "Chronological map of who cites whom among the 25 most locally cited corpus documents; arrows run from the cited to the citing paper along the time axis.",
        "bibliometrix::histNetwork(min.citations = 1) and histPlot(n = 25). A Python version built from exact OpenAlex ids is in py_citation_network.html and py_main_path.png.",
        "bibliometrix matches citations by DOI/label strings, so a few links can be missed; compare with the exact-id Python network.")
  })
wj<-jsonlite::fromJSON(file.path(FIG,"_captions_R.json"),simplifyVector=FALSE)
for (cc in CAPS) wj[[length(wj)+1]] <- cc
write_json(wj, file.path(FIG, "_captions_R.json"), auto_unbox = TRUE, pretty = TRUE)
lg<-read.csv(file.path(TAB,"R_analysis_log.csv"),stringsAsFactors=FALSE); nl<-do.call(rbind,LOG); lg<-lg[lg$analysis!="historiograph",]; wcsv(rbind(lg,nl),"R_analysis_log")