# https://gist.githubusercontent.com/schaunwheeler/5825002/raw/xlsxToR.r
#
# The MIT License (MIT)
#
# Copyright (c) 2012 Schaun Jacob Wheeler
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.


library(XML)
library(plyr)
library(pbapply)

xlsxToR <- function(file, keep_sheets = NULL, header = FALSE) {
  
  temp_dir <- file.path(tempdir(), "xlsxToRtemp")
  suppressWarnings(dir.create(temp_dir))
  
  file.copy(file, temp_dir)
  new_file <- list.files(temp_dir, full.name = TRUE, pattern = basename(file))
  unzip(new_file, exdir = temp_dir)
  
  # Get OS
  # These lines are included because R documentation states that Excel handles 
  # date origins differently on Mac than on Windows. However, manual inspection
  # of Excel files created on Windows and Mac indicated that in fact the origin
  # is handled the same across both platforms. I've kept the original code here
  # commented out in case it can be of use in the future.
  # mac <- xmlToList(xmlParse(list.files(
  #   paste0(temp_dir, "/docProps"), full.name = TRUE, pattern = "app.xml")))
  # mac <- grepl("Macintosh", mac$Application)
  # if(mac) {
  #   os_origin <- "1899-12-30" # documentation says should be "1904-01-01"
  # } else {
  #   os_origin <- "1899-12-30"
  # }
  
  # Get names of sheets
  sheet_names <- xmlToList(xmlParse(list.files(
    paste0(temp_dir, "/xl"), full.name = TRUE, pattern = "workbook.xml")))
  sheet_names <- rbind.fill(lapply(sheet_names$sheets, function(x) {
    as.data.frame(as.list(x), stringsAsFactors = FALSE)
  }))
  rownames(sheet_names) <- NULL
  sheet_names <- as.data.frame(sheet_names,stringsAsFactors = FALSE)
  sheet_names$id <- gsub("\\D", "", sheet_names$id)
  
  # Get column classes
  styles <- xmlParse(list.files(
    paste0(temp_dir, "/xl"), full.name = TRUE, pattern = "styles.xml"))
  styles <- xpathApply(styles, "//x:xf[@applyNumberFormat and @numFmtId]", 
                       namespaces = "x", xmlAttrs)
  styles <- lapply(styles, function(x) {
    x[grepl("applyNumberFormat|numFmtId", names(x))]})
  styles <- do.call("rbind", (lapply(styles, 
                                     function(x) as.data.frame(as.list(x[c("applyNumberFormat", "numFmtId")]),
                                                               stringsAsFactors = FALSE))))
  
  if(!is.null(keep_sheets)) {
    sheet_names <- sheet_names[sheet_names$name %in% keep_sheets,]
    
  }
  
  worksheet_paths <- list.files(
    paste0(temp_dir, "/xl/worksheets"), 
    full.name = TRUE, 
    pattern = paste0(
      "sheet(", 
      paste(sheet_names$id, collapse = "|"), 
      ")\\.xml$"))
  
  worksheets <- lapply(worksheet_paths, function(x) xmlRoot(xmlParse(x))[["sheetData"]])
  
  worksheets <- pblapply(seq_along(worksheets), function(i) {
    
    x <- xpathApply(worksheets[[i]], "//x:c", namespaces = "x", function(node) {
      c("v" = xmlValue(node[["v"]]), xmlAttrs(node))
    })
    
    if(length(x) > 0) {
      
      x_rows <- unlist(lapply(seq_along(x), function(i) rep(i, length(x[[i]]))))
      x <- unlist(x)
      
      x <- reshape(
        data.frame(
          "row" = x_rows,
          "ind" = names(x),
          "value" = x,
          stringsAsFactors = FALSE), 
        idvar = "row", timevar = "ind", direction = "wide")
      
      x$sheet <- sheet_names[sheet_names$id == i, "name"] 
      colnames(x) <- gsub("^value\\.", "", colnames(x))
    }
    x
  })
  worksheets <- do.call("rbind.fill", 
                        worksheets[sapply(worksheets, class) == "data.frame"])
  
  entries <- xmlParse(list.files(paste0(temp_dir, "/xl"), full.name = TRUE, 
                                 pattern = "sharedStrings.xml$"))
  entries <- xpathSApply(entries, "//x:si", namespaces = "x", xmlValue)
  names(entries) <- seq_along(entries) - 1
  
  entries_match <- entries[
    match(worksheets$v[worksheets$t == "s" & !is.na(worksheets$t)], 
          names(entries))]
  worksheets$v[worksheets$t == "s" & !is.na(worksheets$t)] <- entries_match
  worksheets$cols <- match(gsub("\\d", "", worksheets$r), LETTERS)
  worksheets$rows <- as.numeric(gsub("\\D", "", worksheets$r))
  
  if(!any(grepl("^s$", colnames(worksheets)))) {
    worksheets$s <- NA
  }
  
  workbook <- lapply(unique(worksheets$sheet), function(x) {
    y <- worksheets[worksheets$sheet == x,]
    y_style <- as.data.frame(tapply(y$s, list(y$rows, y$cols), identity), 
                             stringsAsFactors = FALSE)
    y <- as.data.frame(tapply(y$v, list(y$rows, y$cols), identity), 
                       stringsAsFactors = FALSE)
    
    if(header) {
      colnames(y) <- y[1,]
      y <- y[-1,]
      y_style <- y_style[-1,]
    }
    
    y_style <- sapply(y_style, function(x) {
      out <- names(which.max(table(x)))
      out[is.null(out)] <- NA
      out
    })
    
    if(length(styles) > 0) {
      y_style <- styles$numFmtId[match(y_style, styles$applyNumberFormat)]
    }
    
    y_style[y_style %in% 14:17] <- "date"
    y_style[y_style %in% c(18:21, 45:47)] <- "time"
    y_style[y_style %in% 22] <- "datetime"
    y_style[is.na(y_style) & !sapply(y, function(x)any(grepl("\\D", x)))] <- "numeric"
    y_style[is.na(y_style)] <- "character"
    y_style[!(y_style %in% c("date", "time", "datetime", "numeric"))] <- "character"
    
    y[] <- lapply(seq_along(y), function(i) {
      switch(y_style[i],
             character = y[,i],
             numeric = as.numeric(y[,i]),
             date = as.Date(as.numeric(y[,i]), origin = os_origin),
             time = strftime(as.POSIXct(as.numeric(y[,i]), origin = os_origin), format = "%H:%M:%S"),
             datetime = as.POSIXct(as.numeric(y[,i]), origin = os_origin))
    }) 
    y 
  })
  
  if(length(workbook) == 1) {
    workbook <- workbook[[1]]
  } else { 
    names(workbook) <- sheet_names$name
  }
  
  workbook
}
