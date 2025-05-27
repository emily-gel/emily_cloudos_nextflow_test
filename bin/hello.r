library(optparse)

option_list <- list(
  make_option(c("--greeting"), type = "character", help = "A greeting.", metavar = "greeting")
)

opt_parser <- OptionParser(option_list = option_list)
opts <- parse_args(opt_parser)

hello <- function(greeting) {
  out <- file("output.txt", "w")
  writeLines(paste(greeting, ", World!", sep = ""), out)
  close(out)
}

if (!is.null(opts$greeting)) {
  hello(opts$greeting)
}
