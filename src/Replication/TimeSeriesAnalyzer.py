import pandas as pd
import os
# from DataCleaningFunctions import *
# from survey.SurveyFunctions import *
# from scipy import stats
        
import seaborn as sns
import matplotlib.pyplot as plt

# import importlib
# importlib.reload(PSIDCrosswalkHelper)
# importlib.reload(PSIDRawLoader)
# importlib.reload(varsForInequalityAnalysis)

DEBUG_EDA = False

class PSIDTimeSeriesAnalyzer:

    def __init__(self, baseDir, familyInputSubDir, familyBaseName, individualInputSubDir, individualBaseName, outputSubDir, yearsToInclude):
        
        self.baseDir = baseDir
        self.inputSubDir = familyInputSubDir
        self.outputSubDir = outputSubDir
        
        self.famPath = os.path.join(baseDir, familyInputSubDir, familyBaseName)
        self.indPath = os.path.join(baseDir, individualInputSubDir, individualBaseName)
        
        if yearsToInclude is not None:
            self.yearsToInclude = sorted(yearsToInclude) 
        
    def readData(self):
        combinedData = None
        
        individualData = pd.read_csv((self.indPath + ".csv"))
        
        maxYear = max(self.yearsToInclude)
        finalYearSequenceVar = "sequenceNo_" + str(maxYear)
        individualData = individualData.loc[individualData[finalYearSequenceVar] == 1].copy()
        individualData['constantFamilyId'] = range(1,(len(individualData)+1), 1)

        self.dataDict = {}
        for year in self.yearsToInclude:
            if (os.path.exists(self.famPath + str(year) + ".csv")):
                yearData = pd.read_csv((self.famPath  + str(year) + ".csv"))
                yearData['year'] = year
                
                indInterviewVar = "interviewId_" + str(year)
                individualDataNeeded = individualData[['constantFamilyId',indInterviewVar]].copy() 
                yearData = pd.merge(yearData, individualDataNeeded, left_on = 'familyInterviewId', right_on = indInterviewVar, how = 'inner')

                self.dataDict[year] = yearData 
                
                if combinedData is None:
                    combinedData = yearData
                else:
                    combinedData = pd.concat([combinedData,yearData], ignore_index=True, sort=False)
            else:
                print("Skipping year " + str(year) + ". No data file found." )
        self.combinedData = combinedData
        self.combinedData.to_csv((self.famPath + "Combined.csv"), index=False)
        
 