getDataForYear <- function(syStr, eyStr, toStr, depVar, keepLowIncome=F, keepOriginalFilters=T) {
  inflatedTimespan = paste0(syStr, "_", eyStr, "_as_",  toStr)
  duration = strtoi(eyStr) - strtoi(syStr)
  
  dta = read.csv(paste0("WithSavings_TwoPeriod_", inflatedTimespan, ".csv"), as.is=TRUE)
  
  # Filter on Longitudinal Cleaning Status
  if (keepOriginalFilters || ~keepLowIncome)
  {
    print(paste0("Dropping ", nrow(dta)-sum(dta[paste0('cleaningStatus_', syStr, '_', eyStr)] =='Keep'), " based on Long. Cleaning status"))
    dta = dta[which(dta[paste0('cleaningStatus_', syStr, '_', eyStr)] =='Keep'),]
  } else {
    print(paste0("Dropping ", nrow(dta)-sum(dta[paste0('cleaningStatus_', syStr, '_', eyStr)] =='Keep' | dta[paste0('cleaningStatus_', syStr, '_', eyStr)]=='IncomeTooLow'), " based on Long. Cleaning status"))
    dta = dta[which(dta[paste0('cleaningStatus_', syStr, '_', eyStr)] =='Keep' | dta[paste0('cleaningStatus_', syStr, '_', eyStr)] =='IncomeTooLow'),]
  }

  # And on Cross-sectional statuses
  print(paste0("Dropping ", nrow(dta)-sum(dta[paste0('cleaningStatus_', syStr)] =='Keep' & dta[paste0('cleaningStatus_', eyStr)] =='Keep'), " based on Cross Sectional Cleaning status"))
  dta = dta[which(dta[paste0('cleaningStatus_', syStr)] =='Keep' & dta[paste0('cleaningStatus_', eyStr)] =='Keep'),]
  
  if (!keepOriginalFilters) {
    # Filter on Working Status
    print(paste0("Dropping ", nrow(dta)-sum(dta[paste0('IsWorkingR_', syStr)] !='Retired' & dta[paste0('IsWorkingR_', eyStr)] !='Retired'), " based on Retired status"))
    dta = dta[which(dta[paste0('IsWorkingR_', syStr)] !='Retired' & dta[paste0('IsWorkingR_', eyStr)] !='Retired'),]
  }
    
  
  names(dta)[names(dta) == paste0('raceR_',syStr)] <- "Race"
  names(dta)[names(dta) == paste0('averageRealBeforeTaxIncome_AllYears_',inflatedTimespan)] <- "Income"
  names(dta)[names(dta) == paste0('activeSavingsRate_PerPerson_',inflatedTimespan)] <- "SavingsRate"
  names(dta)[names(dta) == paste0('ageR_',syStr)] <- "Age"
  names(dta)[names(dta) == paste0('NumChildrenInFU_',syStr)] <- "NumChildren"
  names(dta)[names(dta) == paste0('educationYearsR_',syStr)] <- "Education"
  names(dta)[names(dta) == paste0('inflatedNetWorthWithHomeAnd401k_AfterBalanceFillin_',syStr, '_as_', toStr)] <- "NetWorthStart"
  
  
  # if (keepOriginalFilters) {
  #  names(dta)[names(dta) == paste0('LongitudinalWeightHH_',syStr)] <- "Weight"
  #} else {
  names(dta)[names(dta) == paste0('LongitudinalWeightHH_',eyStr)] <- "Weight"
  #}

  dta[paste0('Annual_Total_ChangeInWealth_',inflatedTimespan)] = dta[paste0('Total_ChangeInWealth_',inflatedTimespan)]/duration
  
  names(dta)[names(dta) == paste0('Annual_Total_NetActiveSavings_',inflatedTimespan)] <- "ActiveSavings"
  names(dta)[names(dta) == paste0('Annual_Total_OpenCloseTransfers_',inflatedTimespan)] <- "OpenCloseTransfers"
  names(dta)[names(dta) == paste0('Annual_Total_ChangeInWealth_',inflatedTimespan)] <- "ChangeInWealth"
  names(dta)[names(dta) == paste0('Annual_Total_CapitalGains_',inflatedTimespan)] <- "CapitalGains"
  names(dta)[names(dta) == paste0('Annual_Total_GrossSavings_',inflatedTimespan)] <- "GrossSavings"
  
  names(dta)[names(dta) == paste0('Annual_SmallGift_All_AmountHH_',inflatedTimespan)] <- "SmallGift"
  names(dta)[names(dta) == paste0('Annual_largeGift_All_AmountHH_',inflatedTimespan)] <- "LargeGift"
  names(dta)[names(dta) == paste0('Annual_netAssetMove_',inflatedTimespan)] <- "NetMove"
  
  # names(dta)[names(dta) == paste0('netMoveIn_',inflatedTimespan)] <- "MoveIn"
  # names(dta)[names(dta) == paste0('netMoveOut_',inflatedTimespan)] <- "MoveOut"
  names(dta)[names(dta) == paste0('TotalTax_',syStr)] <- "Taxes"

  print(paste0("Dropping ", nrow(dta)-sum(dta$Race=='White' |  dta$Race=='Hispanic' |  dta$Race=='Black'), " rows with other races/ethnicities"))
  dta = dta[which(dta$Race=='White' |  dta$Race=='Hispanic' |  dta$Race=='Black'),]
  print(paste0("Dropping ", nrow(dta)-sum(dta$Weight > 0), " rows based on missing weight"))
  dta = dta[which(dta$Weight > 0),]
  print(paste0("Dropping ", nrow(dta)-sum(!is.na(dta[depVar])), " rows based on missing Dependent Var:", depVar))
  dta = dta[which(!is.na(dta[depVar])),]
  
  dta$Age_Sq = dta$Age * dta$Age
  dta$logIncome = log(dta$Income+1)
  dta$MarriedStart = dta[paste0('martialStatusR_', syStr)] == "Married"
  dta$MarriedEnd = dta[paste0('martialStatusR_', eyStr)] == "Married"
  dta$Black = dta$Race=='Black'
  dta$Hispanic = dta$Race=='Hispanic'
  

  # Identfy the vars we must have
  tmpDta = subset(dta, select=c(depVar, "NetWorthStart", 
                                "Race", "Hispanic", "Black", 
                                "logIncome", "Age", "Age_Sq", 
                                "Education", "MarriedStart", 
                                "NumChildren", "Weight", 
                                "constantFamilyId"))
  tmpDta[mapply(is.infinite, tmpDta)] <- NA
  print(paste0("Dropping ", nrow(tmpDta)-nrow(tmpDta[complete.cases(tmpDta), ]), " rows with bad data"))
  tmpDta = tmpDta[complete.cases(tmpDta), ]
  
  otherVarsForAnalysis = c("constantFamilyId", "ActiveSavings", "SavingsRate", "OpenCloseTransfers",
                           "ChangeInWealth", "CapitalGains", "GrossSavings", "SmallGift", "LargeGift", 
                           "NetMove", "Taxes") # "MoveIn", "MoveOut", 
  
  otherVarsForAnalysis = otherVarsForAnalysis[otherVarsForAnalysis != depVar]
  dta = merge(tmpDta,dta[,otherVarsForAnalysis],by="constantFamilyId", all.x = TRUE, all.y = FALSE)

  dta$Race = ordered(dta$Race, levels = c("White", "Hispanic", "Black"))
  
  dta$DummyWeight = 1
  if (depVar == "SavingsRate") { 
    dta$SavingsRate = dta$SavingsRate * 100
  }
  return(dta)
}


# Remove Outliers V1: Top and bottom 1%
removeOutliers_ByPercent <- function(dta, depVar, percent = 0.01) {
  tmp = quantile(dta[,depVar], probs = c(percent, 1-percent)) # quartile
  dta$Outlier = dta[depVar] > tmp[1] & dta[depVar] > tmp[2]
  # table(dta$Outlier)
  dta = dta[!dta$Outlier,] 
  return (dta)
}

# Remove Outliers V2: By Standard Deviation 
removeOutliers_BySDofResidual <- function(dta, depVar, numSDs = 2) {
  LM<-lm(paste0(depVar,'~Race+logIncome+Education+Age+MarriedStart+NumChildren'), data=dta)
  
  # Store the residuals as a new column in DF
  dta$Resid<-resid(LM)
  
  dta$Outlier = abs(dta$Resid-mean(dta$Resid))>numSDs*sd(dta$Resid) # dta$Resid[abs(dta$Resid-mean(dta$Resid))<2*sd(dta$Resid)])
  # table(dta$Outlier)
  dta = dta[!dta$Outlier,] 
  return (dta)
}

doMediation <- function(mediationDta, indepVar, depVar, onRQ=False)  {
  # Mediation Analysis
  # https://towardsdatascience.com/doing-and-reporting-your-first-mediation-analysis-in-r-2fe423b92171
  
  # Average Causal Mediated Effect = effect of IV on Mediator * Mediator effect on DV (when controlling for mediator)
  # Average Direct Effect = coeff on IV after controlling for mediator
  # Total Effect = ACME + ADE
  # Prop Mediated = ACME / TE
  
  tmpDta <- mediationDta
  
  library(mediation)
  
  if (onRQ) {
    # Step 1
    fit.totaleffect = rq(formula = paste0(depVar, ' ~ ', indepVar), tau=.5, data = tmpDta,  weights = Weight, method="br", na.action=na.omit); 
    summary(fit.totaleffect)
    # Step 2
    tmpDta <- mediationDta
    fit.mediator = rq(formula = paste0('logIncome~',indepVar), tau=.5, data = tmpDta,  weights = Weight, method="br", na.action=na.omit); 
    summary(fit.mediator)
    # Step 3
    tmpDta <- mediationDta
    fit.dv = rq(formula = paste0(depVar, ' ~ ', indepVar, ' + logIncome'), tau=.5, data = tmpDta,  weights = Weight, method="br", na.action=na.omit); summary(fit.dv)
    # summary(results)

    totalEffectCoeff = fit.totaleffect$coefficients[2]
    effectOfIVOnMediator = fit.mediator$coefficients[2]
    mediatorEffectOnDV =  fit.dv$coefficients[3]
    averageDirectEffect =  fit.dv$coefficients[2]
    averageCausalMediatedEffect = effectOfIVOnMediator * mediatorEffectOnDV
    totalEffectCalced = averageDirectEffect +  averageCausalMediatedEffect
    print(paste0("Total Effect: ", totalEffectCoeff, " versus ", totalEffectCalced))
    propMediated = averageCausalMediatedEffect / totalEffectCalced
    print(paste0("Proportion Mediated: ", propMediated))
    
    # results = mediate(fit.mediator, fit.dv, treat='Black', mediator='logIncome', boot=T)
    # summary(results)
    # return(results)
    return(propMediated)
  } else
  {
    fit.totaleffect=lm(formula=paste0(depVar, '~', indepVar),mediationDta); summary(fit.totaleffect)
    fit.mediator=lm(formula=paste0('logIncome~', indepVar),mediationDta); summary(fit.mediator)
    fit.dv=lm(formula=paste0(depVar, '~', indepVar, '+logIncome'),mediationDta); summary(fit.dv)
    results = mediate(fit.mediator, fit.dv, treat=indepVar, mediator='logIncome', boot=F)
    print(summary(results))
    return(results)
  }
}

rho <- function(u,tau=.5) {
  return (u*(tau - (u < 0)))
}

getPseudoRSquared_ManualCalc<- function(quantileRegressionResult, interceptOnlyRegressionResult) {
  V1 <- sum(rho(u=quantileRegressionResult$resid, tau=quantileRegressionResult$tau))
  V0 <- sum(rho(u=interceptOnlyRegressionResult$resid, tau=interceptOnlyRegressionResult$tau))
  
  return(1 - V1/V0)
}

getPseudoRSquared_UsingRho<- function(quantileRegressionResult, interceptOnlyRegressionResult) {
  return(1 - quantileRegressionResult$rho/interceptOnlyRegressionResult$rho)
}


doMedianRegression <- function(dta, depVar, interceptOnlyRegressionResult) {
  # Basic Median Regression
  theWeights = dta['Weight']
  
  theFormulaStr = paste0(depVar, ' ~ 1')
  if ("Black" %in% colnames(dta) && length(unique(dta$Black))>1) {
    theFormulaStr = paste0(theFormulaStr, " + Black")
  }
  if ("Hispanic" %in% colnames(dta) && length(unique(dta$Hispanic))>1) {
    theFormulaStr = paste0(theFormulaStr, " + Hispanic")  
  }
  
  results = rq(formula = theFormulaStr, tau=.5, data = dta,  weights = Weight, method="br", na.action=na.omit)
  print(summary(results));
  print(paste0("Pseudo R Squared Using Rho: ", getPseudoRSquared_UsingRho(results, interceptOnlyRegressionResult), "\n"))
  print(paste0("Pseudo R Squared Manual: ", getPseudoRSquared_UsingRho(results, interceptOnlyRegressionResult), "\n"))
  
  theFormulaStr = paste0(theFormulaStr, ' + logIncome + Age + Age_Sq + Education + MarriedStart + NumChildren')
  results = rq(formula = theFormulaStr, tau=.5, data = dta,  weights = Weight, method="br", na.action=na.omit)
  print(summary(results));
  print(paste0("Pseudo R Squared Using Rho: ", getPseudoRSquared_UsingRho(results, interceptOnlyRegressionResult), "\n"))
  print(paste0("Pseudo R Squared Manual: ", getPseudoRSquared_ManualCalc(results, interceptOnlyRegressionResult), "\n"))

  return(results)
}


doOLSRegression <- function(dta, depVar) {
  # Basic OLS Regression
  results = lm(formula = paste0(depVar, ' ~ 1+ Hispanic + Black'), data = dta,  weights = Weight, na.action=na.omit)
  print(summary(results));
  results = lm(formula = paste0(depVar, ' ~ 1+ Hispanic + Black + logIncome + Age + Age_Sq + Education + MarriedStart + NumChildren'), data = dta,  weights = Weight,na.action=na.omit)
  print(summary(results)); 
  return(results)
}

doIteractionAnalysis <- function(dta, indepVar, depVar, onMedian = True)  {
  if (onMedian)
  {
    interceptOnlyRegressionResult = rq(formula = paste0(depVar, ' ~ 1'), tau=.5, data = dta,  weights = Weight, method="br", na.action=na.omit)
    
    results = rq(formula = paste0(depVar, ' ~ ', indepVar, ' + logIncome + Education +NumChildren + MarriedStart+ Age + Age_Sq + ', indepVar, ':logIncome'), tau=.5, 
                 data = dta,  weights = Weight, method="br", na.action=na.omit)
    print(summary(results)); 
    print(paste0("Pseudo R Squared Using Rho: ", getPseudoRSquared_UsingRho(results, interceptOnlyRegressionResult), "\n"))
    print(paste0("Pseudo R Squared Manual: ", getPseudoRSquared_UsingRho(results, interceptOnlyRegressionResult), "\n"))
    
    
    if (FALSE) {
      # Orig Model
      results = rq(formula = paste0(depVar, ' ~ logIncome + Education +NumChildren + MarriedStart+ Age + Age_Sq'), tau=.5, 
                   data = dtaB,  weights = Weight, method="br", na.action=na.omit)
      sum(rho(results$resid, results$tau))
      
      summary(results); # getPseudoRSquared_UsingRho(results)
      
      # Orig Model
      results = rq(formula = paste0(depVar, ' ~ logIncome + Education +NumChildren + MarriedStart+ Age + Age_Sq'), tau=.5, 
                   data = dtaW,  weights = Weight, method="br", na.action=na.omit)
      summary(results); getPseudoRSquared(results)
      
      # Orig Model
      results = rq(formula = paste0(depVar, ' ~ ', indepVar, ' + logIncome + Education +NumChildren + MarriedStart+ Age + Age_Sq'), tau=.5, 
                   data = dtaWB,  weights = Weight, method="br", na.action=na.omit)
      summary(results); getPseudoRSquared(results)
      
      # Interaction with Income
      results = rq(formula = paste0(depVar, ' ~ ', indepVar, ' + logIncome + Education +NumChildren + MarriedStart+ Age + Age_Sq + logIncome*Black'), tau=.5, 
                   data = dtaWB,  weights = Weight, method="br", na.action=na.omit)
      summary(results)
      
      results = rq(formula = paste0(depVar, ' ~ ', indepVar, ' + logIncome + Education +NumChildren + MarriedStart+ Age + Age_Sq + logIncome*Black + Education*Black + MarriedStart*Black + NumChildren*', indepVar, ''), tau=.5, 
                   data = dtaWB,  weights = Weight, method="br", na.action=na.omit)
      summary(results)
      
      results = rq(formula = paste0(depVar, ' ~ ', indepVar, ' + logIncome + Age + Age_Sq + logIncome*', indepVar, ' + Education*', indepVar, ' + MarriedStart*', indepVar, ' + NumChildren*', indepVar, ''), tau=.5, 
                   data = dtaWB,  weights = Weight, method="br", na.action=na.omit)
      summary(results)
      
      results = rq(formula = paste0(depVar, ' ~ 1+ ', indepVar, ' + logIncome + Age + Age_Sq + Education*', indepVar, ' + MarriedStart*', indepVar, ' + NumChildren*', indepVar, ''), tau=.5, 
                   data = dtaWB,  weights = Weight, method="br", na.action=na.omit)
      summary(results)
    }
  }
  else {
    results = lm(formula = paste0(depVar, ' ~ 1+ ', indepVar, ' + logIncome + Age + Age_Sq + Education + MarriedStart + NumChildren+ ', indepVar, ':logIncome'), data = dta,  weights = Weight,na.action=na.omit)
    print(summary(results)); 
    return(results)
  }
  
}

getMeanAsPercentOfWealth <- function(smallDta)
{
  duration = 2
  smallDta = smallDta[,c("NetWorthStart", "ChangeInWealth", "CapitalGains", "GrossSavings", "ActiveSavings", "SmallGift", "LargeGift", "NetMove", "MoveIn", "MoveOut", "Taxes", "Weight")]
  smallDta[mapply(is.infinite, smallDta)] <- 0
  smallDta[mapply(is.na, smallDta)] <- 0
  
  ChangeInNetWorth_Sum = sum(smallDta$ChangeInWealth*smallDta$Weight)
  NetWorth_Sum = sum(smallDta$NetWorthStart*smallDta$Weight)
  
  results = data.frame(ChangeInNetWorth_Mean =100.0*ChangeInNetWorth_Sum/(NetWorth_Sum*duration),
                       GrossSavings_Mean = 100.0*sum(smallDta$GrossSavings*smallDta$Weight)/(NetWorth_Sum*duration),
                       ActiveSavings_Mean = 100.0*sum(smallDta$ActiveSavings*smallDta$Weight)/(NetWorth_Sum*duration),
                       CapitalGains_Mean = 100.0*sum(smallDta$CapitalGains*smallDta$Weight)/(NetWorth_Sum*duration),
                       Inheritance_Mean = 100.0*sum(smallDta$LargeGift*smallDta$Weight)/(NetWorth_Sum*duration),
                       SmallGift_Mean = 100.0*sum(smallDta$SmallGift*smallDta$Weight)/(NetWorth_Sum*duration),
                       NetMove_Mean = 100.0*sum(smallDta$NetMove*smallDta$Weight)/(NetWorth_Sum*duration),
                       
                       Taxes_Mean = 100.0*sum(smallDta$Taxes*smallDta$Weight)/(NetWorth_Sum*duration),
                       MoveIn_Mean = 100.0*sum(smallDta$MoveIn*smallDta$Weight)/(NetWorth_Sum*duration),
                       MoveOut_Mean = 100.0*sum(smallDta$MoveOut*smallDta$Weight)/(NetWorth_Sum*duration)
  )
  return(results)
}



doSEM <- function(dta, depVar) {
  # SEM
  library(lavaan)
}


doHierarchicalPartition <- function(dta, depVar) {
  # https://cran.r-project.org/web/packages/hier.part/hier.part.pdf
  library(hier.part)
}

# Stepwise Regression
doStepwise <- function(dta, depVar) {
  # http://www.sthda.com/english/articles/37-model-selection-essentials-in-r/154-stepwise-regression-essentials-in-r/
}

