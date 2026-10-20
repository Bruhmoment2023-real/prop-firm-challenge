# Bibliometrix analysis of the screened corpus.
# Run:  "C:\Program Files\R\R-4.5.3\bin\Rscript.exe" 01_bibliometrix_analysis.R <path to ...\bibliometrics>
# Input : data/clean/bibliometrix_input.csv  (built by python/pipeline.py master; WoS-style tags, one row per document)
# Output: figures/R*.png (+ .html for interactive ones), tables/R*.csv, data/clean/M_bibliometrix.rds, tables/R_run_log.csv
suppressMessages({
  library(bibliometrix); library(ggplot2); library(dplyr); library(tidyr); library(igraph); library(ggrepel)
})
args <- commandArgs(trailingOnly = TRUE)
base <- normalizePath(if (length(args)) args[1] else "..", winslash = "/")
if (!dir.exists("D:/")) stop("D: is missing")
fig <- file.path(base, "figures"); tab <- file.path(base, "tables")
dir.create(fig, showWarnings = FALSE); dir.create(tab, showWarnings = FALSE)
set.seed(1234)

INK <- "#0b0b0b"; INK2 <- "#52514e"; MUTED <- "#898781"; GRID <- "#e1e0d9"; SURF <- "#fcfcfb"
CAT <- c("#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#6250d6", "#e34948")
theme_set(theme_minimal(base_size = 12) + theme(
  plot.background = element_rect(fill = SURF, colour = NA), panel.grid.minor = element_blank(),
  panel.grid.major = element_line(colour = GRID, linewidth = 0.3), axis.text = element_text(colour = INK2),
  axis.title = element_text(colour = INK2), plot.title = element_text(colour = INK, face = "bold", size = 14),
  plot.subtitle = element_text(colour = INK2, size = 10), plot.caption = element_text(colour = MUTED, size = 8, hjust = 0),
  legend.position = "bottom", legend.title = element_text(size = 10), plot.title.position = "plot"))

log <- data.frame(step = character(), status = character(), note = character())
safe <- function(step, expr) {
  r <- tryCatch({ force(expr); "ok" }, error = function(e) paste("ERROR:", conditionMessage(e)))
  log[nrow(log) + 1, ] <<- c(step, ifelse(r == "ok", "ok", "failed"), ifelse(r == "ok", "", r))
  cat(sprintf("[%s] %s %s\n", format(Sys.time(), "%H:%M:%S"), step, ifelse(r == "ok", "ok", r)))
  write.csv(log, file.path(tab, "R_run_log.csv"), row.names = FALSE)
}
skip <- function(step, why) { log[nrow(log) + 1, ] <<- c(step, "skipped", why); cat("[skip]", step, "-", why, "\n") }
gsave <- function(p, name, w = 10, h = 6.5) ggsave(file.path(fig, paste0(name, ".png")), p, width = w, height = h, dpi = 300, bg = SURF)
wcsv <- function(x, name) write.csv(x, file.path(tab, paste0(name, ".csv")), row.names = FALSE, fileEncoding = "UTF-8")
netpng <- function(net, name, title, sub = "") {
  png(file.path(fig, paste0(name, ".png")), width = 3600, height = 2800, res = 300, bg = SURF)
  par(mar = c(1, 1, 3.2, 1))
  plot(net$graph, layout = net$layout)
  title(main = title, col.main = INK, cex.main = 1.2, adj = 0)
  mtext(sub, side = 1, line = -0.5, cex = 0.7, col = MUTED, adj = 0)
  dev.off()
}
netexport <- function(net, name) {
  g <- net$graph
  el <- igraph::as_data_frame(g, "edges"); vx <- igraph::as_data_frame(g, "vertices")
  cl <- net$cluster_res
  wcsv(el[, intersect(c("from", "to", "weight", "num"), names(el))], paste0(name, "_edges"))
  if (!is.null(cl)) wcsv(cl, paste0(name, "_nodes"))
}

# ---------------------------------------------------------------- load
B <- read.csv(file.path(base, "data/clean/bibliometrix_input.csv"), stringsAsFactors = FALSE, fileEncoding = "UTF-8-BOM", na.strings = character(0))
B$PY <- suppressWarnings(as.numeric(B$PY)); B$TC <- suppressWarnings(as.numeric(B$TC)); B$TC[is.na(B$TC)] <- 0
B <- B[!is.na(B$PY), ]
for (v in c("AU", "AF", "TI", "SO", "J9", "JI", "DE", "ID", "AB", "C1", "RP", "CR", "DI", "AU_UN", "AU_CO", "AU1_CO")) B[[v]][is.na(B[[v]])] <- ""
M <- B
M <- metaTagExtraction(M, Field = "SR", sep = ";")
rownames(M) <- M$SR
class(M) <- c("bibliometrixDB", "data.frame")
saveRDS(M, file.path(base, "data/clean/M_bibliometrix.rds"))
N <- nrow(M)
SUBLAB <- unique(M[, c("SUBLIT", "SUBLIT_LABEL")]); SUBLAB <- SUBLAB[order(SUBLAB$SUBLIT), ]
SUBCOL <- setNames(CAT[seq_len(nrow(SUBLAB))], SUBLAB$SUBLIT_LABEL)
src <- sprintf("Corpus: %d documents, %d-%d. Source: OpenAlex records (single-record API), screened; see search-protocol.md.", N, min(M$PY), max(M$PY))
cat("Documents:", N, "\n")
SMALL <- N < 50

# ---------------------------------------------------------------- 1 main information
res <- NULL; S <- NULL
safe("01 main information (biblioAnalysis)", {
  res <<- biblioAnalysis(M, sep = ";")
  S <<- summary(res, k = 25, pause = FALSE, verbose = FALSE)
  mi <- S$MainInformationDF
  extra <- data.frame(Description = c("Documents with an abstract", "Documents with >=1 resolved cited reference", "Documents with >=1 institution country",
                                      "Mean OpenAlex citations per document", "Median OpenAlex citations per document"),
                      Results = c(sum(nchar(M$AB) > 0), sum(nchar(M$CR) > 0), sum(nchar(M$AU_CO) > 0), round(mean(M$TC), 2), median(M$TC)))
  wcsv(rbind(mi, extra), "R01_main_information")
})

# ---------------------------------------------------------------- 2 annual production
safe("02 annual scientific production", {
  ap <- as.data.frame(table(Year = M$PY), stringsAsFactors = FALSE); ap$Year <- as.numeric(ap$Year)
  ap <- merge(data.frame(Year = min(ap$Year):max(ap$Year)), ap, all.x = TRUE); ap$Freq[is.na(ap$Freq)] <- 0
  y0 <- max(min(ap$Year), 1990); yN <- max(ap$Year) - 1          # last (partial) year left out of the growth rate
  a0 <- mean(ap$Freq[ap$Year %in% y0:(y0 + 2)]); aN <- mean(ap$Freq[ap$Year %in% (yN - 2):yN])
  cagr <- if (a0 > 0) ((aN / a0)^(1 / (yN - 1 - (y0 + 1))) - 1) * 100 else NA
  ap$bibliometrix_growth_rate_pct <- if (!is.null(S)) S$AnnualGrowthRate else NA
  ap$cagr_3yr_smoothed_pct <- round(cagr, 2)
  wcsv(ap, "R02_annual_production")
  bysub <- M %>% count(PY, SUBLIT_LABEL)
  p <- ggplot(bysub, aes(PY, n, fill = SUBLIT_LABEL)) + geom_col(width = 0.8, colour = SURF, linewidth = 0.2) +
    scale_fill_manual(values = SUBCOL, name = "Sub-literature") + guides(fill = guide_legend(nrow = length(SUBCOL))) +
    labs(title = "Annual scientific production", subtitle = sprintf("Documents per publication year, stacked by sub-literature. Smoothed growth %d-%d: %.1f%% per year.", y0, yN, cagr),
         x = "Publication year", y = "Documents in corpus", caption = paste(src, "\nThe final year is incomplete (pull date in README)."))
  gsave(p, "R02_annual_production")
})

# ---------------------------------------------------------------- 3 average citations per year
safe("03 average citations per year", {
  cur <- as.numeric(format(Sys.Date(), "%Y"))
  ac <- M %>% group_by(PY) %>% summarise(N = n(), MeanTCperArt = mean(TC), .groups = "drop") %>%
    mutate(CitableYears = pmax(cur - PY, 1), MeanTCperYear = MeanTCperArt / CitableYears)
  wcsv(ac, "R03_average_citations_per_year")
  p <- ggplot(ac[ac$N >= 3, ], aes(PY, MeanTCperYear)) + geom_line(colour = CAT[1], linewidth = 0.8) + geom_point(colour = CAT[1], size = 1.8) +
    labs(title = "Average citations per year, by publication year", subtitle = "Mean OpenAlex citations per document divided by years since publication (years with at least 3 documents)",
         x = "Publication year", y = "Mean citations per document per year", caption = src)
  gsave(p, "R03_average_citations_per_year")
})

# ---------------------------------------------------------------- 4 sources + Bradford
safe("04 most relevant sources", {
  so <- M %>% filter(!grepl("^NO SOURCE", SO)) %>% group_by(SO) %>% summarise(Documents = n(), TotalCitations = sum(TC), .groups = "drop") %>% arrange(desc(Documents))
  wcsv(so, "R04_sources")
  top <- head(so, 20); top$SO <- factor(substr(top$SO, 1, 60), levels = rev(substr(top$SO, 1, 60)))
  p <- ggplot(top, aes(Documents, SO)) + geom_col(fill = CAT[1], width = 0.7) + geom_text(aes(label = Documents), hjust = -0.25, size = 3.2, colour = INK2) +
    scale_x_continuous(expand = expansion(mult = c(0, 0.08))) +
    labs(title = "Most relevant sources", subtitle = sprintf("Top 20 of %d journals, repositories and series by number of corpus documents (%d documents have no source record)", nrow(so), sum(grepl("^NO SOURCE", M$SO))),
         x = "Documents in corpus", y = NULL, caption = src)
  gsave(p, "R04_most_relevant_sources", 10, 7)
})
safe("05 Bradford's law", {
  bf <- bradford(M[!grepl("^NO SOURCE", M$SO), ])
  wcsv(bf$table, "R05_bradford_zones")
  p <- bf$graph + labs(title = "Bradford's law: core sources", subtitle = "Sources ranked by productivity (log rank); shaded area = Zone 1 (core)", caption = src) + theme(plot.background = element_rect(fill = SURF, colour = NA))
  gsave(p, "R05_bradford_law", 10, 6.5)
})
safe("06 source dynamics", {
  sg <- sourceGrowth(M[!grepl("^NO SOURCE", M$SO), ], top = 6, cdf = TRUE)
  wcsv(sg, "R06_source_dynamics_cumulative")
  lg <- pivot_longer(sg, -Year, names_to = "Source", values_to = "Cumulative")
  lg$Source <- substr(lg$Source, 1, 45)
  p <- ggplot(lg, aes(Year, Cumulative, colour = Source)) + geom_line(linewidth = 0.9) + scale_colour_manual(values = CAT) + guides(colour = guide_legend(nrow = 3)) +
    labs(title = "Source dynamics", subtitle = "Cumulative corpus documents in the six most productive sources", x = "Publication year", y = "Cumulative documents", caption = src)
  gsave(p, "R06_source_dynamics")
})

# ---------------------------------------------------------------- 5 authors
safe("07 most productive and most cited authors", {
  al <- strsplit(M$AU, ";")
  ad <- data.frame(Author = trimws(unlist(al)), TC = rep(M$TC, lengths(al)), frac = rep(1 / pmax(lengths(al), 1), lengths(al)), LCS = rep(M$LCS_EXACT, lengths(al)))
  ad <- ad[ad$Author != "" & ad$Author != "ANONYMOUS", ]
  at <- ad %>% group_by(Author) %>% summarise(Documents = n(), Fractionalised = round(sum(frac), 2), TotalCitations = sum(TC), LocalCitations = sum(LCS), .groups = "drop") %>% arrange(desc(Documents), desc(TotalCitations))
  h <- tryCatch(Hindex(M, field = "author", elements = head(at$Author, 40), sep = ";", years = Inf)$H, error = function(e) NULL)
  if (!is.null(h)) at <- merge(at, h[, intersect(c("Element", "h_index", "g_index", "m_index", "PY_start"), names(h))], by.x = "Author", by.y = "Element", all.x = TRUE) %>% arrange(desc(Documents), desc(TotalCitations))
  wcsv(at, "R07_authors")
  t1 <- head(at, 20); t1$Author <- factor(t1$Author, levels = rev(t1$Author))
  p1 <- ggplot(t1, aes(Documents, Author)) + geom_col(fill = CAT[1], width = 0.7) + geom_text(aes(label = Documents), hjust = -0.3, size = 3.2, colour = INK2) +
    scale_x_continuous(expand = expansion(mult = c(0, 0.1))) + labs(title = "Most productive authors", subtitle = "Number of corpus documents per author (name strings as recorded by OpenAlex; not disambiguated by hand)", x = "Documents in corpus", y = NULL, caption = src)
  gsave(p1, "R07a_most_productive_authors", 9, 7)
  t2 <- head(at[order(-at$LocalCitations), ], 20); t2$Author <- factor(t2$Author, levels = rev(t2$Author))
  p2 <- ggplot(t2, aes(LocalCitations, Author)) + geom_col(fill = CAT[2], width = 0.7) + geom_text(aes(label = LocalCitations), hjust = -0.3, size = 3.2, colour = INK2) +
    scale_x_continuous(expand = expansion(mult = c(0, 0.1))) + labs(title = "Most locally cited authors", subtitle = "Sum over an author's corpus documents of citations received from other corpus documents", x = "Local citations (within corpus)", y = NULL, caption = src)
  gsave(p2, "R07b_most_cited_authors", 9, 7)
})
safe("08 Lotka's law", {
  L <- lotka(M)
  ap <- L$AuthorProd
  wcsv(ap, "R08_lotka_author_productivity")
  wcsv(data.frame(beta = L$Beta, C = L$C, R2 = L$R2, fitted = paste(names(L), collapse = "|")), "R08_lotka_fit")
  names(ap)[1:3] <- c("N.Articles", "N.Authors", "Freq")
  ap$Theoretical <- 10^(log10(L$C) - 2 * log10(ap$N.Articles))
  p <- ggplot(ap, aes(N.Articles)) + geom_line(aes(y = Freq, colour = "Observed"), linewidth = 0.9) + geom_point(aes(y = Freq, colour = "Observed"), size = 2) +
    geom_line(aes(y = Theoretical, colour = "Lotka inverse-square law"), linetype = 2, linewidth = 0.8) + scale_colour_manual(values = c("Observed" = CAT[1], "Lotka inverse-square law" = CAT[2]), name = NULL) +
    labs(title = "Author productivity and Lotka's law", subtitle = sprintf("Share of authors by number of corpus documents. Estimated beta = %.2f, R2 = %.2f", L$Beta, L$R2), x = "Documents written", y = "Proportion of authors", caption = src)
  gsave(p, "R08_lotka_law", 9, 6)
})
safe("09 author production over time", {
  apo <- authorProdOverTime(M, k = 12, graph = FALSE)
  wcsv(apo$dfAU, "R09_author_production_over_time")
  p <- apo$graph + labs(title = "Authors' production over time", subtitle = "Top 12 authors by corpus documents. Dot size = documents that year; shade = citations per year", caption = src) +
    theme(plot.background = element_rect(fill = SURF, colour = NA))
  gsave(p, "R09_author_production_over_time", 11, 7)
})

# ---------------------------------------------------------------- 6 affiliations and countries
safe("10 most relevant affiliations", {
  af <- data.frame(Affiliation = trimws(unlist(lapply(strsplit(M$AU_UN, ";"), unique)))); af <- af[af$Affiliation != "", , drop = FALSE]
  aft <- af %>% count(Affiliation, name = "Documents") %>% arrange(desc(Documents))
  wcsv(aft, "R10_affiliations")
  t <- head(aft, 20); t$Affiliation <- factor(substr(t$Affiliation, 1, 55), levels = rev(substr(t$Affiliation, 1, 55)))
  p <- ggplot(t, aes(Documents, Affiliation)) + geom_col(fill = CAT[1], width = 0.7) + geom_text(aes(label = Documents), hjust = -0.3, size = 3.2, colour = INK2) +
    scale_x_continuous(expand = expansion(mult = c(0, 0.1))) + labs(title = "Most relevant affiliations", subtitle = sprintf("Corpus documents with at least one author at the institution (%d of %d documents carry institution data)", sum(nchar(M$AU_UN) > 0), N),
                                                                    x = "Documents in corpus", y = NULL, caption = src)
  gsave(p, "R10_most_relevant_affiliations", 10, 7)
})
CO <- NULL
safe("11 countries: production, corresponding-author country, SCP/MCP", {
  cl <- lapply(strsplit(M$AU_CO, ";"), function(x) unique(trimws(x[x != ""])))
  d <- data.frame(doc = rep(seq_len(N), lengths(cl)), Country = unlist(cl))
  prod <- d %>% count(Country, name = "Documents") %>% arrange(desc(Documents))
  M$MCP <- lengths(cl) > 1
  cc <- M %>% filter(AU1_CO != "") %>% group_by(Country = AU1_CO) %>% summarise(CorrAuthorDocs = n(), SCP = sum(!MCP), MCP = sum(MCP), TotalCitations = sum(TC), .groups = "drop") %>%
    mutate(MCP_ratio = round(MCP / CorrAuthorDocs, 3), AvgCitations = round(TotalCitations / CorrAuthorDocs, 1))
  CO <<- merge(prod, cc, all = TRUE) %>% arrange(desc(Documents)); wcsv(CO, "R11_countries")
  t <- head(cc[order(-cc$CorrAuthorDocs), ], 20) %>% pivot_longer(c(SCP, MCP), names_to = "Collaboration", values_to = "n")
  t$Country <- factor(t$Country, levels = rev(unique(t$Country)))
  p <- ggplot(t, aes(n, Country, fill = Collaboration)) + geom_col(width = 0.7, colour = SURF, linewidth = 0.3) +
    scale_fill_manual(values = c(SCP = CAT[1], MCP = CAT[2]), labels = c(MCP = "Multiple-country publication", SCP = "Single-country publication"), name = NULL) +
    labs(title = "Corresponding author's country", subtitle = "Top 20 countries; single- versus multiple-country publications (corresponding author as flagged by OpenAlex, else first author)",
         x = "Documents", y = NULL, caption = paste(src, sprintf("\nCountry is known for %d of %d documents.", sum(nchar(M$AU_CO) > 0), N)))
  gsave(p, "R11_corresponding_author_countries", 10, 7)
})
safe("12 country collaboration map", {
  data(countries)
  cl <- lapply(strsplit(M$AU_CO, ";"), function(x) sort(unique(trimws(x[x != ""]))))
  pr <- do.call(rbind, lapply(cl[lengths(cl) > 1], function(x) t(combn(x, 2))))
  ed <- as.data.frame(pr, stringsAsFactors = FALSE) %>% count(V1, V2, name = "Links") %>% arrange(desc(Links))
  wcsv(setNames(ed, c("Country1", "Country2", "CoauthoredDocuments")), "R12_country_collaboration_links")
  xy <- countries[, c("countries", "Longitude", "Latitude")]
  e2 <- merge(merge(ed, xy, by.x = "V1", by.y = "countries"), xy, by.x = "V2", by.y = "countries", suffixes = c("1", "2"))
  wm <- map_data("world"); wm <- wm[wm$region != "Antarctica", ]
  nm <- c(USA = "USA", `UNITED KINGDOM` = "UK", KOREA = "South Korea", `CZECH REPUBLIC` = "Czech Republic")
  pr2 <- CO[, c("Country", "Documents")]; pr2$region <- ifelse(pr2$Country %in% names(nm), nm[pr2$Country], tools::toTitleCase(tolower(pr2$Country)))
  wm <- left_join(wm, pr2, by = "region")
  p <- ggplot() + geom_polygon(data = wm, aes(long, lat, group = group, fill = Documents), colour = SURF, linewidth = 0.1) +
    scale_fill_gradient(low = "#cde2fb", high = "#0d366b", na.value = "#ecebe6", trans = "log10", name = "Documents (log scale)") +
    geom_curve(data = e2[e2$Links >= ifelse(nrow(e2) > 150, 2, 1), ], aes(x = Longitude1, y = Latitude1, xend = Longitude2, yend = Latitude2, linewidth = Links), colour = CAT[2], alpha = 0.45, curvature = 0.2) +
    scale_linewidth(range = c(0.2, 2), name = "Co-authored documents") + coord_quickmap() +
    labs(title = "Country scientific production and collaboration", subtitle = sprintf("Shading = documents with an author in the country; arcs = international co-authorship (%s)", ifelse(nrow(e2) > 150, "pairs with 2+ documents", "all pairs")),
         x = NULL, y = NULL, caption = src) + theme(axis.text = element_blank(), panel.grid = element_blank(), legend.key.width = unit(1.2, "cm"))
  gsave(p, "R12_country_collaboration_map", 12, 7)
})

# ---------------------------------------------------------------- 7 cited documents
safe("13 most globally cited documents", {
  g <- M %>% transmute(Document = SR, Title = TI, Year = PY, DOI = DI, SubLiterature = SUBLIT_LABEL, GlobalCitations_OpenAlex = TC, CitationsPerYear = round(TC / pmax(as.numeric(format(Sys.Date(), "%Y")) - PY, 1), 1), LocalCitations = LCS_EXACT) %>% arrange(desc(GlobalCitations_OpenAlex))
  wcsv(g, "R13_most_globally_cited_documents")
  t <- head(g, 20); t$Document <- factor(t$Document, levels = rev(t$Document))
  p <- ggplot(t, aes(GlobalCitations_OpenAlex, Document, fill = SubLiterature)) + geom_col(width = 0.7) + geom_text(aes(label = GlobalCitations_OpenAlex), hjust = -0.2, size = 3, colour = INK2) +
    scale_fill_manual(values = SUBCOL, name = "Sub-literature") + guides(fill = guide_legend(nrow = length(SUBCOL))) + scale_x_continuous(expand = expansion(mult = c(0, 0.1))) +
    labs(title = "Most globally cited documents", subtitle = "Total citations in OpenAlex (all citing works, inside or outside the corpus)", x = "OpenAlex citations", y = NULL, caption = src)
  gsave(p, "R13_most_globally_cited_documents", 10, 7.5)
})
safe("14 most locally cited documents", {
  lcb <- tryCatch(localCitations(M, sep = ";")$Papers, error = function(e) NULL)
  l <- M %>% transmute(Document = SR, Title = TI, Year = PY, DOI = DI, SubLiterature = SUBLIT_LABEL, LocalCitations_exact = LCS_EXACT, GlobalCitations_OpenAlex = TC, LCS_GCS_ratio_pct = round(100 * LCS_EXACT / pmax(TC, 1), 1))
  if (!is.null(lcb)) l <- merge(l, setNames(lcb[, c("Paper", "LCS")], c("Document", "LocalCitations_bibliometrix")), all.x = TRUE)
  l <- l %>% arrange(desc(LocalCitations_exact)); wcsv(l, "R14_most_locally_cited_documents")
  t <- head(l, 20); t$Document <- factor(t$Document, levels = rev(t$Document))
  p <- ggplot(t, aes(LocalCitations_exact, Document, fill = SubLiterature)) + geom_col(width = 0.7) + geom_text(aes(label = LocalCitations_exact), hjust = -0.3, size = 3, colour = INK2) +
    scale_fill_manual(values = SUBCOL, name = "Sub-literature") + guides(fill = guide_legend(nrow = length(SUBCOL))) + scale_x_continuous(expand = expansion(mult = c(0, 0.1))) +
    labs(title = "Most locally cited documents", subtitle = "Citations received from other documents in this corpus (exact OpenAlex ID matching)", x = "Local citations", y = NULL, caption = src)
  gsave(p, "R14_most_locally_cited_documents", 10, 7.5)
})
safe("15 most cited references", {
  cr <- citations(M, field = "article", sep = ";")
  ct <- data.frame(Reference = names(cr$Cited), Citations = as.numeric(cr$Cited), Year = as.numeric(cr$Year), Source = cr$Source)
  wcsv(head(ct, 500), "R15_most_cited_references")
  t <- head(ct, 20); t$lab <- sub(", DOI .*$", "", t$Reference); t$lab <- factor(substr(t$lab, 1, 70), levels = rev(unique(substr(t$lab, 1, 70))))
  p <- ggplot(t, aes(Citations, lab)) + geom_col(fill = CAT[1], width = 0.7) + geom_text(aes(label = Citations), hjust = -0.3, size = 3, colour = INK2) + scale_x_continuous(expand = expansion(mult = c(0, 0.1))) +
    labs(title = "Most cited references", subtitle = "References cited most often by corpus documents (whether or not the reference is itself in the corpus)", x = "Citing corpus documents", y = NULL,
         caption = paste(src, "\nOnly references cited by at least two corpus documents were resolved to metadata."))
  gsave(p, "R15_most_cited_references", 11, 7.5)
})
safe("16 reference publication year spectroscopy (RPYS)", {
  rp <- rpys(M, sep = ";", timespan = c(1900, max(M$PY)), graph = FALSE)
  wcsv(rp$rpysTable, "R16_rpys_table")
  top <- rp$CR %>% group_by(Year) %>% slice_max(Freq, n = 3, with_ties = FALSE) %>% ungroup(); wcsv(top, "R16_rpys_top_references_per_year")
  p <- rp$spectroscopy + labs(title = "Reference publication year spectroscopy (RPYS)", subtitle = "Black: cited references by their publication year. Red: deviation from the 5-year median (peaks = historical roots)", caption = paste(src, "\nBuilt from references cited by at least two corpus documents.")) +
    theme(plot.background = element_rect(fill = SURF, colour = NA))
  gsave(p, "R16_rpys", 11, 6.5)
})

# ---------------------------------------------------------------- 8 keywords
KW <- NULL
STOPK <- c("ECONOMICS", "BUSINESS", "FINANCE", "MATHEMATICS", "COMPUTER SCIENCE", "PSYCHOLOGY", "FINANCIAL ECONOMICS", "ECONOMETRICS", "MATHEMATICAL ECONOMICS", "ACTUARIAL SCIENCE", "MONETARY ECONOMICS", "STATISTICS")
safe("17 most frequent keywords", {
  k <- tableTag(M, "DE", sep = ";", remove.terms = STOPK)
  KW <<- data.frame(Keyword = names(k), Occurrences = as.numeric(k)); wcsv(KW, "R17_keyword_frequencies")
  t <- head(KW, 30); t$Keyword <- factor(t$Keyword, levels = rev(t$Keyword))
  p <- ggplot(t, aes(Occurrences, Keyword)) + geom_col(fill = CAT[1], width = 0.7) + geom_text(aes(label = Occurrences), hjust = -0.3, size = 3, colour = INK2) + scale_x_continuous(expand = expansion(mult = c(0, 0.1))) +
    labs(title = "Most frequent keywords", subtitle = "OpenAlex keyword field (author keywords where the publisher supplied them, otherwise machine-assigned)", x = "Documents", y = NULL, caption = src)
  gsave(p, "R17_most_frequent_keywords", 9, 8)
})
safe("18 trend topics", {
  ft <- fieldByYear(M, field = "DE", timespan = c(max(min(M$PY), 1995), max(M$PY)), min.freq = max(3, round(N / 150)), n.items = 4, remove.terms = STOPK, graph = FALSE)
  wcsv(ft$df_graph, "R18_trend_topics")
  p <- ft$graph + labs(title = "Trend topics", subtitle = "Keywords by the median year of the documents using them; bar = first to third quartile; bubble = frequency", caption = src) + theme(plot.background = element_rect(fill = SURF, colour = NA))
  gsave(p, "R18_trend_topics", 10, 9)
})

# ---------------------------------------------------------------- 9 networks
if (SMALL) { skip("19-27 network and thematic analyses", "corpus has fewer than 50 documents; these methods are not meaningful at this size") } else {
safe("19 keyword co-occurrence network", {
  nm <- biblioNetwork(M, analysis = "co-occurrences", network = "author_keywords", sep = ";", remove.terms = STOPK)
  net <- networkPlot(nm, normalize = "association", n = 50, Title = "", type = "auto", size = 4, size.cex = TRUE, labelsize = 0.9, label.cex = TRUE, cluster = "louvain", remove.isolates = TRUE, edgesize = 4, edges.min = 2, verbose = FALSE)
  netpng(net, "R19_keyword_cooccurrence_network", "Keyword co-occurrence network", paste("50 most frequent keywords; association-strength normalisation; Louvain clusters; links with 2+ co-occurrences.", src))
  netexport(net, "R19_keyword_cooccurrence")
})
safe("20 thematic map", {
  tm <- thematicMap(M, field = "DE", n = 250, minfreq = max(4, round(N / 120)), stemming = FALSE, size = 0.5, n.labels = 3, repel = TRUE, remove.terms = STOPK)
  wcsv(tm$clusters, "R20_thematic_map_clusters"); wcsv(tm$words, "R20_thematic_map_words")
  p <- tm$map + labs(title = "Thematic map", subtitle = "Keyword clusters by centrality (relevance) and density (development). Top-right motor, top-left niche, bottom-right basic, bottom-left emerging or declining", caption = src) +
    theme(plot.background = element_rect(fill = SURF, colour = NA), plot.title = element_text(face = "bold", size = 14), plot.subtitle = element_text(size = 9))
  gsave(p, "R20_thematic_map", 11, 8)
})
safe("21 thematic evolution", {
  q <- as.numeric(quantile(M$PY, c(1 / 3, 2 / 3))); cuts <- unique(round(q))
  cuts <- cuts[cuts > min(M$PY) & cuts < max(M$PY)]
  te <- thematicEvolution(M, field = "DE", years = cuts, n = 250, minFreq = max(3, round(N / 200)), size = 0.5, n.labels = 2, repel = TRUE, remove.terms = STOPK)
  wcsv(te$Edges, "R21_thematic_evolution_edges"); wcsv(te$Nodes[, intersect(c("name", "group", "slice", "id", "sum"), names(te$Nodes))], "R21_thematic_evolution_nodes")
  wcsv(data.frame(cut_years = cuts), "R21_thematic_evolution_slices")
  w <- plotThematicEvolution(te$Nodes, te$Edges)
  hf <- file.path(fig, "R21_thematic_evolution.html")
  ok <- tryCatch({ htmlwidgets::saveWidget(w, hf, selfcontained = TRUE, title = "Thematic evolution"); TRUE }, error = function(e) FALSE)
  if (!ok) htmlwidgets::saveWidget(w, hf, selfcontained = FALSE, libdir = "R21_lib", title = "Thematic evolution")
  # static version: alluvial drawn from the same nodes/edges
  nd <- te$Nodes; ed <- te$Edges
  nd$y <- ave(seq_len(nrow(nd)), nd$slice, FUN = function(i) rev(seq_along(i)) / (length(i) + 1))
  ed$x1 <- nd$slice[ed$from + 1]; ed$x2 <- nd$slice[ed$to + 1]; ed$y1 <- nd$y[ed$from + 1]; ed$y2 <- nd$y[ed$to + 1]
  slab <- sort(unique(nd$group));
  p <- ggplot() + geom_segment(data = ed, aes(x = x1, xend = x2, y = y1, yend = y2, linewidth = Inclusion), colour = CAT[1], alpha = 0.3, lineend = "round") +
    geom_label(data = nd, aes(slice, y, label = sub("--.*$", "", name)), size = 2.8, fill = SURF, colour = INK, label.size = 0.2) +
    scale_linewidth(range = c(0.3, 5), name = "Inclusion index") + scale_x_continuous(breaks = sort(unique(nd$slice)), labels = unique(nd$group[order(nd$slice)]), expand = expansion(mult = 0.15)) +
    labs(title = "Thematic evolution", subtitle = "Keyword themes in each period (labelled by their most frequent keyword) and the flows between them", x = "Time slice", y = NULL, caption = paste(src, "\nInteractive Sankey version: R21_thematic_evolution.html")) +
    theme(axis.text.y = element_blank(), panel.grid = element_blank())
  gsave(p, "R21_thematic_evolution", 11, 7.5)
})
safe("22 co-citation network of references", {
  nm <- biblioNetwork(M, analysis = "co-citation", network = "references", sep = ";")
  net <- networkPlot(nm, n = 50, Title = "", type = "auto", size = 4, size.cex = TRUE, labelsize = 0.75, label.cex = TRUE, cluster = "louvain", remove.isolates = TRUE, edgesize = 3, edges.min = 2, verbose = FALSE)
  netpng(net, "R22_cocitation_references_network", "Co-citation network of cited references", paste("50 most cited references; a link = cited together by 2+ corpus documents; Louvain clusters.", src))
  netexport(net, "R22_cocitation_references")
})
safe("23 co-citation network of sources", {
  M2 <- metaTagExtraction(M, "CR_SO", sep = ";")
  nm <- biblioNetwork(M2, analysis = "co-citation", network = "sources", sep = ";")
  net <- networkPlot(nm, n = 40, Title = "", type = "auto", size = 4, size.cex = TRUE, labelsize = 0.8, label.cex = TRUE, cluster = "louvain", remove.isolates = TRUE, edgesize = 3, edges.min = 2, verbose = FALSE)
  netpng(net, "R23_cocitation_sources_network", "Co-citation network of sources (journals)", paste("40 most cited sources; a link = cited together in the same reference lists; Louvain clusters.", src))
  netexport(net, "R23_cocitation_sources")
})
safe("24 bibliographic coupling of documents", {
  nm <- biblioNetwork(M, analysis = "coupling", network = "references", sep = ";")
  net <- networkPlot(nm, normalize = "salton", n = 60, Title = "", type = "auto", size = 4, size.cex = TRUE, labelsize = 0.7, label.cex = TRUE, cluster = "louvain", remove.isolates = TRUE, edgesize = 3, edges.min = 0, verbose = FALSE)
  netpng(net, "R24_bibliographic_coupling_network", "Bibliographic coupling of documents", paste("60 documents with the highest coupling degree; link = shared references (Salton-normalised); Louvain clusters.", src))
  netexport(net, "R24_bibliographic_coupling")
})
safe("25 historiograph (direct citation network)", {
  hr <- histNetwork(M, min.citations = max(1, quantile(M$LCS_EXACT, 0.9)), sep = ";", verbose = FALSE)
  hp <- histPlot(hr, n = 25, size = 4, labelsize = 3, verbose = FALSE)
  wcsv(hr$histData[, intersect(c("Paper", "Title", "DOI", "Year", "LCS", "GCS"), names(hr$histData))], "R25_historiograph_data")
  p <- hp$g + labs(title = "Historiograph: direct citation network", subtitle = "The 25 most locally cited documents in time order; an arrow runs from the cited (older) to the citing (newer) document", caption = src) +
    theme(plot.background = element_rect(fill = SURF, colour = NA), plot.title = element_text(face = "bold", size = 14))
  gsave(p, "R25_historiograph", 13, 8)
})
safe("26 author collaboration network", {
  nm <- biblioNetwork(M, analysis = "collaboration", network = "authors", sep = ";")
  net <- networkPlot(nm, n = 60, Title = "", type = "auto", size = 4, size.cex = TRUE, labelsize = 0.8, label.cex = TRUE, cluster = "louvain", remove.isolates = TRUE, edgesize = 3, edges.min = 1, verbose = FALSE)
  netpng(net, "R26a_author_collaboration_network", "Author collaboration network", paste("60 most productive authors (isolates removed); link = co-authored corpus documents; Louvain clusters.", src))
  netexport(net, "R26a_author_collaboration")
})
safe("26b institution collaboration network", {
  nm <- biblioNetwork(M[nchar(M$AU_UN) > 0, ], analysis = "collaboration", network = "universities", sep = ";")
  net <- networkPlot(nm, n = 50, Title = "", type = "auto", size = 4, size.cex = TRUE, labelsize = 0.7, label.cex = TRUE, cluster = "louvain", remove.isolates = TRUE, edgesize = 3, edges.min = 1, verbose = FALSE)
  netpng(net, "R26b_institution_collaboration_network", "Institution collaboration network", paste("50 most productive institutions (isolates removed); link = co-authored corpus documents.", src))
  netexport(net, "R26b_institution_collaboration")
})
safe("26c country collaboration network", {
  nm <- biblioNetwork(M[nchar(M$AU_CO) > 0, ], analysis = "collaboration", network = "countries", sep = ";")
  net <- networkPlot(nm, n = 40, Title = "", type = "circle", size = 4, size.cex = TRUE, labelsize = 0.9, label.cex = TRUE, cluster = "louvain", remove.isolates = TRUE, edgesize = 3, edges.min = 1, verbose = FALSE)
  netpng(net, "R26c_country_collaboration_network", "Country collaboration network", paste("40 most productive countries (isolates removed); link = internationally co-authored corpus documents.", src))
  netexport(net, "R26c_country_collaboration")
})
safe("27 three-field plot (cited references - authors - keywords)", {
  w <- threeFieldsPlot(M, fields = c("CR", "AU", "DE"), n = c(15, 15, 15))
  hf <- file.path(fig, "R27_three_field_plot.html")
  ok <- tryCatch({ htmlwidgets::saveWidget(w, hf, selfcontained = TRUE, title = "Three-field plot"); TRUE }, error = function(e) FALSE)
  if (!ok) htmlwidgets::saveWidget(w, hf, selfcontained = FALSE, libdir = "R27_lib", title = "Three-field plot")
})
}
write.csv(log, file.path(tab, "R_run_log.csv"), row.names = FALSE)
cat("\nDone.", sum(log$status == "ok"), "ok,", sum(log$status == "failed"), "failed,", sum(log$status == "skipped"), "skipped\n")
