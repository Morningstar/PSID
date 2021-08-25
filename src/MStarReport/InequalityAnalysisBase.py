import os
import pandas as pd
import numpy as np

''' Key Descriptions

'''


class InequalityAnalysisBase():

    # Numeric Version    
    startYear = None
    endYear = None
    toYear = None
    
    # String Version    
    syStr = None
    eyStr = None
    tyStr = None
    
    # When do we have detailed wealth data in the PSID?
    yearsWealthDataCollected = [1984, 1989, 1994] + list(range(1999, 2019+2, 2))

    def __init__(self, baseDir, inputSubDir, inputBaseName, outputBaseName, outputSubDir):
        self.baseDir = baseDir
        self.inputSubDir = inputSubDir
        self.outputSubDir = outputSubDir
        self.inputBaseName = inputBaseName
        self.outputBaseName = outputBaseName

        self.useCleanedDataOnly = False

        self.dta = None
        self.duration = None
        self.timespan = None
        self.inflatedTimespan =  None
        self.inflatedEnd = None
        self.inflatedStart = None


    def clearData(self):
        self.dta = None
        self.syStr = None
        self.eyStr = None
        self.tyStr = None
        self.startYear = None
        self.endYear = None
        self.toYear = None

    def getInflatedYearSuffix(self, year):
        return formatInflatedYearSuffix(year, self.toYear)
        
    def setPeriod(self, startYear, endYear, toYear):
        self.startYear = startYear
        self.endYear = endYear
        self.toYear = toYear
        
        self.syStr = str(startYear)
        self.eyStr = str(endYear)
        self.tyStr = str(toYear)
    
        self.duration = endYear - startYear
        self.timespan = formatTimeSpanSuffix(self.startYear, self.endYear)
        self.inflatedTimespan =  formatInflatedTimeSpanSuffix(self.startYear, self.endYear, self.toYear)
        self.inflatedEnd = self.getInflatedYearSuffix(self.endYear)
        self.inflatedStart = self.getInflatedYearSuffix(self.startYear) 
        
        yearList = list(range(self.startYear, self.endYear +1))
        yearsFamilyDataCollected = list(range(1980, 1997+1, 1)) +  list(range(1999, 2019+2, 2))
        intersection = [value for value in yearList if value in yearsFamilyDataCollected] 
        self.yearsWithFamilyData = intersection
 
        if (endYear <= 1997):
            self.timeStep = 1
        else:
            self.timeStep = 2

    # When we're saving, it's output!
    def saveCrossSectionalData(self, yearData, year):
        if not os.path.exists(os.path.join(self.baseDir, self.outputSubDir)):
            os.makedirs(os.path.join(self.baseDir, self.outputSubDir))
        yearData.to_csv(os.path.join(self.baseDir, self.outputSubDir, 'YearData_' + self.outputBaseName + self.getInflatedYearSuffix(year) +'.csv'), index=False)

    def saveLongitudinalData(self):
        if not os.path.exists(os.path.join(self.baseDir, self.outputSubDir)):
            os.makedirs(os.path.join(self.baseDir, self.outputSubDir))
        self.dta.to_csv(os.path.join(self.baseDir, self.outputSubDir, 'TwoPeriod_' + self.outputBaseName +  self.inflatedTimespan + ".csv"), index=False)

    # When we're reading, it's input!
    def readCrossSectionalData(self, year):
        self.dta = pd.read_csv(os.path.join(self.baseDir, self.inputSubDir, 'YearData_' + self.inputBaseName + self.getInflatedYearSuffix(year) +'.csv'))
        if self.useCleanedDataOnly:
            self.dta = self.dta[self.dta["cleaningStatus_" + str(year)] == "Keep"].copy()

    def readLongitudinalData(self):
        self.dta = pd.read_csv(os.path.join(self.baseDir, self.inputSubDir, 'TwoPeriod_' + self.inputBaseName + self.inflatedTimespan +'.csv'))
        if self.useCleanedDataOnly:
            self.dta = self.dta[(self.dta["cleaningStatus_" + self.timespan] == "Keep") &
                                (self.dta["cleaningStatus_" + self.syStr] == "Keep") &
                                (self.dta["cleaningStatus_" + self.eyStr] == "Keep")
            ].copy()


def extractRegressionResults(results):
    return pd.concat([results.params.rename("coeff",inplace=True),
                      results.pvalues.rename("pvalue",inplace=True),
                      pd.Series(data = [results.model.nobs]*len(results.params), 
                                name="NumObs", index=results.params.index)], 
                      axis=1 , names=['coeff', 'pvalue', 'NumObs'])

# Little helper function to place certain fields at begingging of DF, for easier review                
def selectiveReorder(dta, colsToPutFirst, alphabetizeTheOthers = False):
    remainingColumns = dta.columns.drop(colsToPutFirst).tolist()
    if alphabetizeTheOthers:
        remainingColumns.sort()
    new_columns = colsToPutFirst + remainingColumns
    return dta[new_columns]
 
def formatInflatedYearSuffix(fromYr, toYear):
    return str(fromYr) + '_as_' + str(toYear)

def formatInflatedTimeSpanSuffix(startYear, endYear, toYear):
    return str(startYear) + '_' + str(endYear) + '_as_' + str(toYear)

def formatTimeSpanSuffix(startYear, endYear):
    return str(startYear) + '_' + str(endYear)
