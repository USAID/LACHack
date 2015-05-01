library(XLConnect)
wb <- loadWorkbook('HN-Municipal.xlsx')
ws2014 <- readWorksheet(wb,1)
ws2013 <- readWorksheet(wb,2)
ws2012 <- readWorksheet(wb,3) 
ws2011 <- readWorksheet(wb,4) 
ws2010 <- readWorksheet(wb,5) 
library(plyr)
m <- join_all(list(ws2010,ws2011,ws2012,ws2013,ws2014),by='Geoint')
result <- data.frame(Geoint=m$Geoint,Name=m$Name,Department=m$Department,
                     Rate_2010=m$Rate_2010,Rate_2011=m$Rate_2011,
                     Rate_2012=m$Rate_2012,Rate_2013=m$Rate_2013,
                     Rate_2014=m$Rate_2014)
write.csv(result,file='HN-Municipal.csv')
