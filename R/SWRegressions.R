# Title     : R code to analyze PSID savings rates data
# Created by: Swendel
# Created on: 5/23/2021


# ########################
# Setup: libraries & directories
# ########################

rm(list=ls())
library(survey)
library(quantreg)
library(stargazer)
source("C:/dev/src/InvestorSuccess/Inequality/R/SWAnalysisFunctions.R")
s <- summary
f <- factor
setwd("C:/dev/sensitive_data/InvestorSuccess/Inequality/inequalityOutput_enrichedPop")


depVar = "SavingsRate"
# depVar = "ActiveSavings"
# depVar = "NetWorthStart"

save_stargazer <- function(output_file, ...) {
  # Thanks to https://stackoverflow.com/questions/30195718/stargazer-save-to-file-dont-show-in-console
  output <- capture.output(stargazer(...))
  cat(paste(output, collapse = "\n"), "\n", file=output_file, append=FALSE)
}


runCoreAnalysis <- function(resultsOutputFileBase, startYear, endYear, depVar, keepOriginalFilters, keepLowIncome, captureOutput=FALSE) {

  if (captureOutput) {
    con <- file(paste0(resultsOutputFileBase, ".log"))
    sink(con, append=TRUE)
    sink(con, append=TRUE, type="message")
  }

    
  # ########################
  # Get the data
  # ########################
  dtaAll= getDataForYear("2017", "2019", "2019", depVar = depVar, keepLowIncome=keepLowIncome, keepOriginalFilters=keepOriginalFilters)
  dtaAll$Black = as.integer(dtaAll$Black)
  dtaAll$Hispanic = as.integer(dtaAll$Hispanic)
  
  dtaWB = dtaAll[which(dtaAll$Race=='White' |  dtaAll$Race=='Black'),]
  dtaWH = dtaAll[which(dtaAll$Race=='White' |  dtaAll$Race=='Hispanic'),]
  dtaB = dtaAll[which(dtaAll$Race=='Black'),]
  dtaH = dtaAll[which(dtaAll$Race=='Hispanic'),]
  dtaW = dtaAll[which(dtaAll$Race=='White'),]
  
  dtaLocal <- dtaAll
  dtaLocal <<- dtaAll # Something strange happens in RQ, in that it draws from global rather than local env
  
  # ########################
  # Do the Analyses: Determinants of Savings Rates
  # ########################

  
  # Medians:
  nrow(dtaAll);nrow(dtaLocal); 
  print("#######################################################\n
        #### Full Population Median  Regressions \n
        #######################################################")
  # dtaLocal <- dtaAll
  # dtaLocal <<- dtaAll # Something strange happens in RQ, in that it draws from global rather than local env, and changes the DF itself
  # mediationDta <- dtaLocal
  # mediationDta <<- dtaLocal
  
  interceptOnlyRegressionResult = rq(formula = paste0(depVar, ' ~ 1'), tau=.5, data = dtaLocal,  weights = Weight, method="br", na.action=na.omit)
  resultsFullPop = doMedianRegression(dtaLocal, depVar, interceptOnlyRegressionResult)
  # doIteractionAnalysis(dtaLocal, depVar, onMedian = TRUE)
  
  print("#######################################################\n
        #### White-Black Median  Regressions \n
        #######################################################")
  # dtaWB <- dtaAll[which(dtaAll$Race=='White' |  dtaAll$Race=='Black'),]
  # dtaWB <<- dtaAll[which(dtaAll$Race=='White' |  dtaAll$Race=='Black'),]
  # mediationDta <- dtaWB
  # mediationDta <<- dtaWB
  
  interceptOnlyRegressionResult = rq(formula = paste0(depVar, ' ~ 1'), tau=.5, data = dtaWB,  weights = Weight, method="br", na.action=na.omit)
  resultsWB = doMedianRegression(dtaWB, depVar, interceptOnlyRegressionResult)

  doMediation(dtaWB, 'Black', depVar, onRQ=TRUE)
  doIteractionAnalysis(dtaWB, 'Black', depVar, onMedian = TRUE)
  
  print("#######################################################\n
        #### White-Hispanic  Median Regressions \n
        #######################################################")

  # dtaWH <- dtaAll[which(dtaAll$Race=='White' |  dtaAll$Race=='Hispanic'),]
  # dtaWH <<- dtaAll[which(dtaAll$Race=='White' |  dtaAll$Race=='Hispanic'),]
  # mediationDta <- dtaWH
  # mediationDta <<- dtaWH
  
  interceptOnlyRegressionResult = rq(formula = paste0(depVar, ' ~ 1'), tau=.5, data = dtaWH,  weights = Weight, method="br", na.action=na.omit)
  resultsWH = doMedianRegression(dtaWH, depVar, interceptOnlyRegressionResult)
  doMediation(dtaWH, 'Hispanic', depVar, onRQ=TRUE)
    
    
  print("#######################################################\n
        #### MEAN Regressions \n
        #######################################################")
  # Compare results to :
  # dta = removeOutliers_ByPercent(dta=dtaAll, depVar=depVar)
  # dtaLocal = removeOutliers_BySDofResidual(dta=dtaAll, depVar=depVar)
  dtaLocal = dtaAll[which(dtaAll$SavingsRate > -2 & dtaAll$SavingsRate < 2),] # as in - saved or dissaved more than 2x income for that year
  nrow(dtaAll);nrow(dtaLocal); 
  results_OLS_FullPop = doOLSRegression(dtaLocal, depVar)
  print("## Mean Mediation, Black ##")
  doMediation(dtaLocal, 'Black', depVar, onRQ=FALSE)
  print("## Mean Mediation, Hispanic ##")
  doMediation(dtaLocal, 'Hispanic', depVar, onRQ=FALSE)
  
  doIteractionAnalysis(dtaLocal, 'Black', depVar, onMedian = FALSE)
  
  if (captureOutput) {
    sink() 
    sink(type="message")
  }
  
  save_stargazer(paste0(resultsOutputFileBase, ".txt"), resultsFullPop, resultsWB, resultsWH, results_OLS_FullPop, type="text", title="Regression Results", align=TRUE)

  return(dtaAll)  
}

printDescriptiveStats <- function(dtaLocal)
{
  #### Get descriptive Stats on Savings rates & race
  dtaLocal = dtaAll
  survey_design = svydesign(ids = ~1, weights = ~dtaLocal$Weight, data = dtaLocal)
  svyby(~SavingsRate,~Race, survey_design, svymean, na.rm=T)
  svyby(~SavingsRate,~Race, survey_design, svyquantile, quantile=c(0.5), ci=TRUE)
}

analyzeDeterminantsOfWealth <- function(dtaLocal)
{
  # ########################
  # Do the Analyses: Determinants of Wealth Growth
  # ########################

  interceptOnlyRegressionResult = rq(formula = paste0(depVar, ' ~ 1'), tau=.5, data = dtaLocal,  weights = dtaLocal$Weight, method="br", na.action=na.omit)
  
  # Basic Median Regression
  theWeights = dtaLocal['Weight']
  dtaLocal$changeInWealthAsPercentOfWealth = dtaLocal$ChangeInWealth / dtaLocal$NetWorthStart
  results = rq(formula = 'changeInWealthAsPercentOfWealth ~ ActiveSavings + CapitalGains', tau=.5, data = dtaLocal,  weights = Weight, method="br", na.action=na.omit)
  print(summary(results)); 
  results = rq(formula = 'ChangeInWealth ~ ActiveSavings + OpenCloseTransfers + CapitalGains + SmallGift + LargeGift + NetMove + Taxes', tau=.5, data = dtaLocal,  weights = Weight, method="br", na.action=na.omit)
  print(summary(results)); 
  results = rq(formula = 'ChangeInWealth ~ 1+ Race + logIncome + Age + Age_Sq + Education + MarriedStart + NumChildren + ActiveSavings + OpenCloseTransfers + CapitalGains + SmallGift + LargeGift + NetMove + Taxes', tau=.5, data = dtaLocal,  weights = Weight, method="br", na.action=na.omit)
  print(summary(results)); 
  
  print(paste0("Pseudo R Squared Using Rho: ", getPseudoRSquared_UsingRho(results, interceptOnlyRegressionResultForMedian), "\n"))
  print(paste0("Pseudo R Squared Manual: ", getPseudoRSquared_UsingRho(results, interceptOnlyRegressionResultForMedian), "\n"))

  # dtaLocal$OpenCloseTransfers

  
  # Wealth Analysis
  print(getMeanAsPercentOfWealth(dtaLocal))
  print(by(dtaLocal, dtaLocal$Race, getMeanAsPercentOfWealth))
}


# Core Regressions
dtaAll= runCoreAnalysis("analyses\\sw_medianRegressions_originalfilter",  startYear, endYear, depVar, keepOriginalFilters=TRUE, keepLowIncome=FALSE, captureOutput=FALSE)
analyzeDeterminantsOfWealth(dtaAll)

dtaLocal= runCoreAnalysis("analyses\\sw_medianRegressions_allowLowIncome", startYear, endYear, depVar, keepOriginalFilters=FALSE, keepLowIncome=TRUE, captureOutput=TRUE)
analyzeDeterminantsOfWealth(dtaLocal)
  


####################
# Analysis of Asset Types as Percent of Wealth, over time: three versions of data cleaning 
#######################
# Get results over time
keepOriginalFilters = T
first = T
for (year in seq(2009, 2017, 2)) {
  dtaAll= getDataForYear(toString(year), toString(year+2), "2019", depVar = depVar, keepLowIncome=F, keepOriginalFilters=keepOriginalFilters)
  results = getMeanAsPercentOfWealth(dtaAll)
  results$syStr = toString(year)
  results$eyStr = toString(year+2)
  results$N = nrow(dtaAll)
  if (first) {
    resultDf = results
    first = F
  } else {
    resultDf = rbind(resultDf, results)
  }
}
originalFilter = resultDf
originalFilter$source = "Original"

keepOriginalFilters = F
first = T
for (year in seq(2009, 2017, 2)) {
  dtaAll= getDataForYear(toString(year), toString(year+2), "2019", depVar = depVar, keepLowIncome=F, keepOriginalFilters=keepOriginalFilters)
  results = getMeanAsPercentOfWealth(dtaAll)
  results$syStr = toString(year)
  results$eyStr = toString(year+2)
  results$N = nrow(dtaAll)
  if (first) {
    resultDf = results
    first = F
  } else {
    resultDf = rbind(resultDf, results)
  }
}
newFilter = resultDf
newFilter$source = "New"


keepOriginalFilters = F
first = T
for (year in seq(2009, 2017, 2)) {
  dtaAll= getDataForYear(toString(year), toString(year+2), "2019", depVar = depVar, keepLowIncome=F, keepOriginalFilters=keepOriginalFilters)
  dtaAll = removeOutliers_ByPercent(dta=dtaAll, depVar="ChangeInWealth")
  results = getMeanAsPercentOfWealth(dtaAll)
  results$syStr = toString(year)
  results$eyStr = toString(year+2)
  results$N = nrow(dtaAll)
  if (first) {
    resultDf = results
    first = F
  } else {
    resultDf = rbind(resultDf, results)
  }
}
meanChoppedFilter = resultDf
meanChoppedFilter$source = "PercentilesChopped"

results = rbind(originalFilter, newFilter, meanChoppedFilter)
write.csv(results, "AssetTypes_FilterTests.csv")



###########################
## Check on effect of Not Weighting the Data, on Core Median Regression
############################

Note -- need to set the specific dataset here.

# Unweighted
if (unweighted) {
  theFormula= formula(paste0(depVar, ' ~ 1 + Black + Hispanic + Income + Income_Sq + Age + Age_Sq + Education + MarriedStart + NumChildren'))
  results = rq(formula=theFormula, tau=.5, data = dta, method="br")
  summary(results)
  rho <- function(u,tau=.5)u*(tau - (u < 0))
  sum(rho(results$resid, results$tau))
}


############
## Test code, not used
############# 
summary(svyglm(formula=theFormula, design=survey_design))

srs_design_srvyr <- dta %>% as_survey_design(ids = 1, weights = LongitudinalWeightHH_2017)
survey_median(~raceR_2017, srs_design_srvyr)
srs_design_srvyr %>%
  group_by(raceR_2017) %>%
  summarize(medians = survey_median(SavingsRate))


