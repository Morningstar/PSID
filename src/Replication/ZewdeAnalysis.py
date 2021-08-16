import pandas as pd
import os
from DataCleaningFunctions import * 
from Survey.SurveyFunctions import *
from scipy import stats
from Replication import TimeSeriesAnalyzer as TimeSeriesAnalyzer
import seaborn as sns
import matplotlib.pyplot as plt
import Inflation.CPI_InflationReader as InflationReader
import Replication.ReplicationAnalyzer as ReplicationAnalyzer


# import importlib
# importlib.reload(PSIDCrosswalkHelper)
# importlib.reload(PSIDRawLoader)
# importlib.reload(varsForInequalityAnalysis)

DEBUG_EDA = False
OUTPUT_DATA_DIR = 'C:/dev/sensitive_data/InvestorSuccess/Inequality'

''' Zewede Baby Bonds Study'''
''' "I select young adults between the ages of 18 and 25 years in the 2015 wave of the PSID. 
    Young adults from 2015 are then matched to earlier PSID waves to obtain information on 
    their household’s net worth at the time of their birth. Sample members were born between 
    1989 and 1996. Individuals are matched to the PSID wave from 1989 if they were born between 
    1989 and 1991, and matched to the wave from 1994 if they were born between 1991 and 1996. 
    All values of household wealth at birth are inflated to 2015 USD using the Consumer Price Index 
    less food and energy. I drop twelve observations reporting negative net worth in 1989 but greater 
    than $250,000 in 1994, and end with a sample size of 1,281 young adults with complete wealth 
    data in 2015 and at birth."

    Data needed
    1) Inflation -- get from CPI.InflationReader.py
    2) I: Age of Individual
    3) I: Relationship to Reference Person / HH
    4) I: Matching data to family
    5) F: Net Worth of Family 
'''

class ZewdeAnalysis(ReplicationAnalyzer.InequalityAnalyzer):
    
    INCLUDE_ONLY_HEADED_BY_YOUNGADULT = True
     
    def __init__(self, baseDir, familyInputSubDir, familyBaseName, individualInputSubDir, individualBaseName, outputSubDir):

        super().__init__(baseDir, familyInputSubDir, familyBaseName, individualInputSubDir, individualBaseName, outputSubDir,
                         yearsToInclude = [1989, 1994, 2015])
        
    def readData(self):
        individualData = pd.read_csv((self.indPath + ".csv"))
        
        # individualFieldsWeNeed = 
        familyFieldsWeNeed = ['familyInterviewId', 
                              'totalIncomeHH', 'taxableIncomeRandS', 
                              'PovertyThreshold', 
                              'NetWorthWithHome', 'valueOfHouse_Net', 'NetWorthNoHome', 'raceR', 'raceS']

        # firstWaveRelationshipVar = "relationshipToR_" + str(1989)
        # secondWaveRelationshipVar = "relationshipToR_" + str(1994)
        # firstWaveAgeVar = "ageI_" + str(1989)
        # secondWaveAgeVar = "ageI_" + str(1994)
        finalWaveAgeVar = "ageI_" + str(2015)

        finalYearSequenceVar = "sequenceNoI_" + str(2015) 
        # individualData = individualData.loc[individualData[finalYearSequenceVar] == 1].copy()
        # kidData = individualData.loc[individualData[firstWaveRelationshipVar] == 'Child'].copy()
        # kidData = individualData.loc[(individualData[firstWaveAgeVar] < 4) | (individualData[secondWaveAgeVar] < 4)].copy()
        kidData = individualData.loc[(individualData[finalWaveAgeVar] <= 25) & (individualData[finalWaveAgeVar] >= 18)].copy()
        
        if self.INCLUDE_ONLY_HEADED_BY_YOUNGADULT:
            kidData = kidData.loc[kidData[finalYearSequenceVar] == 1].copy()
        
        # Note - there may be more than one family 
        kidData['constantFamilyId'] = range(1,(len(kidData)+1), 1)
        
        kidData['waveToMatchTo'] = None
        kidData.loc[(kidData.yearOfBirthI_2015 <= 1991) & (kidData.yearOfBirthI_2015 >= 1989), 'waveToMatchTo'] = 1989
        kidData.loc[(kidData.yearOfBirthI_2015 <= 1996) & (kidData.yearOfBirthI_2015 > 1991), 'waveToMatchTo'] = 1994

        dta = kidData[[finalWaveAgeVar, 'constantFamilyId','interviewId_1989', 'interviewId_1994', 'interviewId_2015', 'waveToMatchTo', 'crossSectionalWeightI_2015']].copy() 

        # Bring in 1989
        year = 1989
        familyDataForYear = pd.read_csv((self.famPath  + str(year) + ".csv"))
        yearData = familyDataForYear[familyFieldsWeNeed].copy()
        yearData.columns = [(x + '_' + str(year)) for x in yearData.columns]
        indInterviewVar = "interviewId_" + str(year)
        dta = pd.merge(dta, yearData, right_on = 'familyInterviewId_'+ str(year), 
                            left_on = indInterviewVar, 
                            how = 'left')
        
        # Bring in 1994
        year = 1994
        familyDataForYear = pd.read_csv((self.famPath  + str(year) + ".csv"))
        yearData = familyDataForYear[familyFieldsWeNeed].copy()
        yearData.columns = [(x + '_' + str(year)) for x in yearData.columns]
        indInterviewVar = "interviewId_" + str(year)
        dta = pd.merge(dta, yearData, right_on = 'familyInterviewId_'+ str(year), 
                            left_on = indInterviewVar, 
                            how = 'left')

        # Bring in 2015 -- to see observed outcomes 
        year = 2015
        familyDataForYear = pd.read_csv((self.famPath  + str(year) + ".csv"))
        yearData = familyDataForYear[familyFieldsWeNeed].copy()
        yearData.columns = [(x + '_' + str(year)) for x in yearData.columns]
        indInterviewVar = "interviewId_" + str(year)
        dta = pd.merge(dta, yearData, right_on = 'familyInterviewId_'+ str(year), 
                            left_on = indInterviewVar, 
                            how = 'left')

        self.dta = dta
        
    def processData(self):
        
        dta = self.dta
        dta['cleaningStatus'] = 'Keep'
        dta.loc[(dta.cleaningStatus=='Keep') & (dta.crossSectionalWeightI_2015 < 0), 'cleaningStatus'] = 'Drop_NoWeight'
        dta.loc[(dta.cleaningStatus=='Keep') & (dta.NetWorthWithHome_2015.isna()), 'cleaningStatus'] = 'MissingNetworth_2015'
        dta.loc[(dta.cleaningStatus=='Keep') & (dta.waveToMatchTo.isna()), 'cleaningStatus'] = 'Mismatched Age information'

        dta['netWorthAtBirth'] = None
        dta.loc[dta.waveToMatchTo == 1989, 'netWorthAtBirth'] = dta.loc[dta.waveToMatchTo == 1989, 'NetWorth_1989']   
        dta.loc[dta.waveToMatchTo == 1994, 'netWorthAtBirth'] = dta.loc[dta.waveToMatchTo == 1994, 'NetWorth_1994']   
        dta.loc[(dta.cleaningStatus=='Keep') & (dta.netWorthAtBirth.isna()), 'cleaningStatus'] = 'Drop_NoNetWorthAtBirth'
        
        cpi = InflationReader.InflationReader() 
        inflation1989to2015 =  cpi.getInflationFactorBetweenTwoYears(1989, 2015)
        inflation1994to2015 =  cpi.getInflationFactorBetweenTwoYears(1994, 2015)

        dta['inflatedNetWorthAtBirth'] = None
        dta.loc[dta.waveToMatchTo == 1989, 'inflatedNetWorthAtBirth'] = dta.loc[dta.waveToMatchTo == 1989, 'netWorthAtBirth']  * inflation1989to2015 
        dta.loc[dta.waveToMatchTo == 1994, 'inflatedNetWorthAtBirth'] = dta.loc[dta.waveToMatchTo == 1994, 'netWorthAtBirth']  * inflation1994to2015 

        dta['changeInNetWorth_89to94'] = dta.NetWorth_1994 - dta.NetWorth_1989
        dta.loc[(dta.cleaningStatus=='Keep') & (dta.NetWorth_1989 < 0) & (dta.NetWorth_1994 > 250000), 'cleaningStatus'] = 'Drop_InvalidNetWorthPerZewde'
        
        dta.cleaningStatus.value_counts(dropna=False)

        dta= dta[dta.cleaningStatus == "Keep"].copy() 
        self.dta = dta
    # All values of household wealth at birth are inflated to 2015 USD using the Consumer Price Index 
    # less food and energy. I drop twelve observations reporting negative net worth in 1989 but greater 
    # than $250,000 in 1994, and end with a sample size of 1,281 young adults with complete wealth 
    # data in 2015 and at birth."
     

    def assignBondAtBirth(self):
        
        self.dta['wealthAtBirth_Quintile_Unweighted'] = pd.qcut(self.dta.inflatedNetWorthAtBirth, 5, labels=False)
        self.dta['wealthAtBirth_Quintile_Weighted'] = wQCut(self.dta, varForQuantile = "inflatedNetWorthAtBirth", varForWeights="crossSectionalWeightI_2015", numQuantiles = 5)
        
        bondAssignment = {1: 50000, 2: 45000, 3: 7500, 4: 5000, 5: 200} 

        self.dta['bondValueAtBirth'] =  self.dta['wealthAtBirth_Quintile_Weighted'].replace(bondAssignment, inplace=False)
        
        def bondCalculator(row):
            return (row.bondValueAtBirth * (1 + 0.2) ^ row.ageI_2015)
            
        self.dta['bondValueIn2015'] = self.dta.apply(lambda row: (row.bondValueAtBirth * ((1 + 0.2) ** row.ageI_2015)), axis=1) 

        self.dta['netWorthWithBond'] = self.dta.NetWorth_2015 + self.dta.bondValueIn2015
                
        self.dta.to_csv((self.famPath + "CombinedZewde.csv"), index=False)
  
        # Assign categorical bond values by quintiles of wealt
        # Log(birthwealth + sqrt(birthwealth^2 +1)
        
    def analyzeWealthInequality(self):
        # Get median Net Worth for all families in the sample
        wMedian(self.dta, varToGetMedian = "NetWorth_2015", varForWeights="crossSectionalWeightI_2015")

        # Get median Net Worth by race
        results = self.dta.groupby(['raceR_2015']).apply(wAverage, "NetWorth_2015", "crossSectionalWeightI_2015")
        existingGap = results['White'] / results['Black']
        print(results['White'], results['Black'], "Starting ratio:", existingGap)
        
        # Extract effect of bond program 
        results = self.dta.groupby(['raceR_2015']).apply(wAverage, "netWorthWithBond", "crossSectionalWeightI_2015")
        newGap = results['White'] / results['Black']
        print(results['White'], results['Black'], "Starting ratio:", newGap)

            
    def doIt(self):
        self.readData()
        self.processData()
        self.assignBondAtBirth()
        self.analyzeWealthInequality()


''' Allow execution from command line, etc'''    
if __name__ == "__main__":
    analyzer = ZewdeAnalysis(familyBaseFileNameWithPath = os.path.join(OUTPUT_DATA_DIR, "extractedPSID_Mapped_Recoded_"),
            individualBaseFileNameWithPath = os.path.join(OUTPUT_DATA_DIR, "extractedPSID_Individual_Mapped_Recoded"))
    analyzer.doIt()
