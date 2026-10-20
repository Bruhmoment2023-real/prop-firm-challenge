suppressPackageStartupMessages(library(bibliometrix))
M <- readRDS("data/clean/bibliometrix_M.rds")
options(error=NULL)
r <- withCallingHandlers(histNetwork(M, min.citations = 1, sep = ";", verbose = FALSE), error = function(e) { print(sys.calls()[max(1,length(sys.calls())-8):length(sys.calls())]) })
