import Replication.GittlemanAnalysis as GittlemanAnalysis
import Inflation.NIPA_InflationReader as NIPA_InflationReader
import Inflation.CPI_InflationReader as CPI_InflationReader

from Survey.SurveyFunctions import *
import unittest
import os
import pandas as pd
import numpy.testing as npt
from pandas.testing import assert_frame_equal, assert_series_equal
from pandas.api.types import is_numeric_dtype

"""Tests for Gittman Savings Analysis Functions"""

# Major Bugs:
# 1) Replace 1994 data
# 2) TaxSim Returns 0 
# 3) Marital Status = 0
# 4) Savings Rates negative


# import importlib
# importlib.reload(rlc)
def closeEnough(a, b):
    try:
         npt.assert_approx_equal(a, b, 5, err_msg='', verbose= False)
         return True
    except:
        return False

def withinPercentDiff(a, b, percentDiff = 0.05):
    if a != 0:
        if (abs(b - a)/a) > percentDiff:
            return False
    elif b != 0:
        if (abs(a - b)/b) > percentDiff:
            return False
    return True


# Perform a % difference analysis on each cell of a dataframe.
# If instead, you just want toa analyze floats with accuracy within elispon, use https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.testing.assert_frame_equal.html with the Precision set
def dataFramesEqualish(a, b, percentDiff = 0.05):
    if (len(set(a.columns) - (set(b.columns))) != 0):
        print('A has extra columns')
        return False
    if (len(set(b.columns) - (set(a.columns))) != 0):
        print('B has extra columns')
        return False
    
    for col in a.columns:
        if (is_numeric_dtype(a[col]) and is_numeric_dtype(b[col])):  
            for i in range(0,len(a),1):
                if not withinPercentDiff(a[col].iloc[i], b[col].iloc[i], percentDiff):
                    print('Values dont match for col ', col, ' row ', str(i), '(', str(a[col].iloc[i]),  ';', str(b[col].iloc[i]), ')')
                    return False
        else:
            assert_series_equal(a[col].copy().reset_index(drop=True), b[col].copy().reset_index(drop=True), check_index_type=False, check_names=False)
            
    return True
    
    
    
class GittlemanResultsTest(unittest.TestCase):

    def getInflation(self):
        self.ga.startYear
        nipa = NIPA_InflationReader.NIPAInflationReader() 
        self.nipa_inflationStartToEndYear =  nipa.getInflationFactorBetweenTwoYears(self.ga.startYear, self.ga.endYear)
        self.nipa_inflationEndToTargetYear =  nipa.getInflationFactorBetweenTwoYears(self.ga.endYear, self.ga.toYear)

        cpi = CPI_InflationReader.CPIInflationReader() 
        self.cpi_totalInflationStartToEndYear =  cpi.getInflationFactorBetweenTwoYears(self.ga.startYear, self.ga.endYear)
        self.cpi_totalInflationStartToTargetYear =  cpi.getInflationFactorBetweenTwoYears(self.ga.startYear, self.ga.toYear)
        self.cpi_inflationEndToTargetYear =  cpi.getInflationFactorBetweenTwoYears(self.ga.endYear, self.ga.toYear)

        # startEndDiff = self.nipa_inflationStartToEndYear - self.cpi_totalInflationStartToEndYear 
        # endTargetDiff = self.nipa_inflationEndToTargetYear - self.cpi_inflationEndToTargetYear 


    def getResults(self, start, end, to):
        self.ga = GittlemanAnalysis.GittlemanAnalysis(baseDir= "C:/Dev/sensitive_data/InvestorSuccess/Inequality/", 
                                       familyInputSubDir = "B", 
                                       familyBaseName = "C", 
                                       individualInputSubDir = "D", 
                                       individualBaseName = "E", 
                                       outputSubDir = "gittlemanOutput")
        self.ga.setPeriod(start, end, to)
        self.getInflation()

        self.dta = pd.read_csv(os.path.join(self.ga.baseDir, self.ga.outputSubDir, "CombinedGittleman_" + self.ga.inflatedTimespan + ".csv"))
        secondRun = 1989
        finalRun = 2017
        self.results = pd.read_csv(os.path.join(self.ga.baseDir, self.ga.outputSubDir, "CombinedGittleman_CombinedResults_" + str(secondRun) + '_to_' + str(finalRun) +  ".csv"))
        
    def test_TotalChange_NoHouse(self):
        
        self.getResults(1984, 1989, 1998)
        
        componentVarsNoHouse = ['OtherRealEstate', 'Business', 'BrokerageStocks', 'CheckingAndSavings', 'Vehicle', 'OtherAssets', 'OtherDebts']

        '''
        self.dta['NetWorthNoHomeReCalc'] = self.dta.valueOfOtherRealEstate. \
            add(self.dta.valueOfVehicle, fill_value=0). \
            add(self.dta.valueOfBusiness, fill_value=0). \
            add(self.dta.valueOfBrokerageStocks, fill_value=0). \
            add(self.dta.valueOfCheckingAndSavings, fill_value=0). \
            add(self.dta.valueOfOtherAssets, fill_value=0). \
            sub(self.dta.valueOfOtherDebts, fill_value=0)
        '''

        # This is the solid data from PSID -- our calculation of change should come out to the SAME 
        self.dta['inflatedNetWorthNoHouse_' + self.ga.inflatedStart] = self.dta['NetWorthNoHome_' + self.ga.syStr] * self.cpi_totalInflationStartToTargetYear
        self.dta['inflatedNetWorthNoHouse_' + self.ga.inflatedEnd] = self.dta['NetWorthNoHome_' + self.ga.eyStr] * self.cpi_inflationEndToTargetYear
        self.dta['changeInRealNetWorthNoHouse_' + self.ga.inflatedTimespan] = self.dta['inflatedNetWorthNoHouse_' + self.ga.inflatedEnd].sub(self.dta['inflatedNetWorthNoHouse_' + self.ga.inflatedStart], fill_value=0)
        
        # Basic version: Calculate the inflated Value of each one, and its change, and sum those.
        # That should be mathematically equivalent to changeInRealNetWorthAbove
        for theVar in componentVarsNoHouse:
            self.dta[theVar + '_ChangeInWealthRecalc_' + self.ga.inflatedTimespan] = (self.dta['valueOf' + theVar+  '_' + self.ga.eyStr]*self.cpi_inflationEndToTargetYear).sub( self.dta['valueOf' + theVar+  '_' + self.ga.syStr] * self.cpi_totalInflationStartToTargetYear, fill_value=0)  
            if theVar == 'OtherDebts':
                self.dta[theVar + '_ChangeInWealthRecalc_' + self.ga.inflatedTimespan] = -self.dta[theVar + '_ChangeInWealthRecalc_' + self.ga.inflatedTimespan]

        changeRecalcVars = [s + '_ChangeInWealthRecalc_' + self.ga.inflatedTimespan for s in componentVarsNoHouse]
        self.dta['TotalNoHome_ChangeInRealWealthRecalc_'  + self.ga.inflatedTimespan]= self.dta[changeRecalcVars].sum(axis=1)
        
        # Existing Version: Add the Total Change calculated in the Gittleman Analysis code - should be very close to valueOf diffs
        totalChangeVars = [s + "_TotalChangeInWealth_" + self.ga.inflatedTimespan for s in componentVarsNoHouse]    
        self.dta['TotalNoHome_ChangeInRealWealth_'  + self.ga.inflatedTimespan]= self.dta[totalChangeVars].sum(axis=1) 
        # self.dta['TotalNoHome_ChangeInRealWealth_'  + self.ga.inflatedTimespan] = self.dta['TotalNoHome_ChangeInNominalWealth_'  + self.ga.timespan] * self.cpi_inflationEndToTargetYear

        aggDictionary = {
                    'familyInterview_N': ('familyInterviewId_' +self.ga.eyStr,'count'),
                    'familyInterview_TotalWeights': ('familyInterviewId_' +self.ga.eyStr,'SumOfWeights'),
                                        
                    # New, no house
                    'New_changeInRealNetWorthNoHouse_mean' : ('changeInRealNetWorthNoHouse_' + self.ga.inflatedTimespan, 'mean'),
                    'New_changeInRealNetWorthNoHouse_median' : ('changeInRealNetWorthNoHouse_' + self.ga.inflatedTimespan, 'median'),

                    'New_TotalNoHome_ChangeInRealWealthRecalc_mean' : ('TotalNoHome_ChangeInRealWealthRecalc_' + self.ga.inflatedTimespan, 'mean'),
                    'New_TotalNoHome_ChangeInRealWealthRecalc_median' : ('TotalNoHome_ChangeInRealWealthRecalc_' + self.ga.inflatedTimespan, 'median'),

                    'New_TotalNoHome_ChangeInRealWealth_mean' : ('TotalNoHome_ChangeInRealWealth_' + self.ga.inflatedTimespan, 'mean'),
                    'New_TotalNoHome_ChangeInRealWealth_median' : ('TotalNoHome_ChangeInRealWealth_' + self.ga.inflatedTimespan, 'median'),
                    
                    } 
        
                
        dataMask = (self.dta['cleaningStatus_' + self.ga.eyStr] == 'Keep')
        
        weightVar = 'LongitudinalWeightHH_' + self.ga.syStr
                                
        resultsByRace = wGroupByAgg(self.dta.loc[dataMask], ['raceR_' + self.ga.syStr], aggregationDict = aggDictionary, varForWeights = (weightVar)).reset_index()
        resultsByRace['Source'] = 'Race_' + self.ga.eyStr

        tmp  = resultsByRace.loc[resultsByRace.raceR_1984.isin(['Black', 'White'])].copy()
        
        # Start with a simple empty DF -- two families
        yrStr = str(1984)
        correctData = pd.DataFrame({
                'raceR_' + yrStr :['Black', 'White'], 
                'familyInterview_N' :[1839,3240], 
                'familyInterview_TotalWeights' :[11534,79925], 
                'New_changeInRealNetWorthNoHouse_mean': [3908.831548, 25945.14286],
                'New_changeInRealNetWorthNoHouse_median': [0, 4087.904778],
                'Source': ['Race_' + self.ga.eyStr, 'Race_' + self.ga.eyStr]
                },
            columns=['raceR_' + yrStr, 'familyInterview_N','familyInterview_TotalWeights', 'New_changeInRealNetWorthNoHouse_mean', 'New_changeInRealNetWorthNoHouse_median', 'Source'])

        correctData['New_TotalNoHome_ChangeInRealWealthRecalc_mean'] = correctData['New_changeInRealNetWorthNoHouse_mean']
        correctData['New_TotalNoHome_ChangeInRealWealthRecalc_median'] = correctData['New_changeInRealNetWorthNoHouse_median']

        correctData['New_TotalNoHome_ChangeInRealWealth_mean'] = correctData['New_changeInRealNetWorthNoHouse_mean']
        correctData['New_TotalNoHome_ChangeInRealWealth_median'] = correctData['New_changeInRealNetWorthNoHouse_median']

        self.assertTrue(dataFramesEqualish(correctData, tmp))


        # resultsByRace.to_csv(os.path.join(self.ga.baseDir, self.ga.outputSubDir, 'Test_TotalChangeNoHouse_' + self.ga.timespan +'.csv'))

    def test_TotalChange_WithHouse(self):
        
        self.getResults(1984, 1989, 1998)
        
        componentVars = ['House', 'OtherRealEstate', 'Business', 'BrokerageStocks', 'CheckingAndSavings', 'Vehicle', 'OtherAssets', 'MortgagePrincipal', 'OtherDebts']

        '''
        self.dta['NetWorthNoHomeReCalc'] = self.dta.valueOfOtherRealEstate. \
            add(self.dta.valueOfVehicle, fill_value=0). \
            add(self.dta.valueOfBusiness, fill_value=0). \
            add(self.dta.valueOfBrokerageStocks, fill_value=0). \
            add(self.dta.valueOfCheckingAndSavings, fill_value=0). \
            add(self.dta.valueOfOtherAssets, fill_value=0). \
            sub(self.dta.valueOfOtherDebts, fill_value=0).
            sub(self.dta.valueOfHouse_Debt, fill_value=0).
        '''
        
        # Basic version: Calculate the inflated Value of each one, and its change, and sum those.
        # That should be mathematically equivalent to changeInRealNetWorthAbove
        for theVar in componentVars:
            self.dta[theVar + '_ChangeInWealthRecalc_' + self.ga.inflatedTimespan] = (self.dta['valueOf' + theVar+  '_' + self.ga.eyStr]*self.cpi_inflationEndToTargetYear).sub( self.dta['valueOf' + theVar+  '_' + self.ga.syStr] * self.cpi_totalInflationStartToTargetYear, fill_value=0)  
            if ((theVar == 'OtherDebts') or (theVar == 'MortgagePrincipal')):
                self.dta[theVar + '_ChangeInWealthRecalc_' + self.ga.inflatedTimespan] = -self.dta[theVar + '_ChangeInWealthRecalc_' + self.ga.inflatedTimespan]

        changeRecalcVars = [s + '_ChangeInWealthRecalc_' + self.ga.inflatedTimespan for s in componentVars]
        self.dta['Total_ChangeInRealWealthRecalc_'  + self.ga.inflatedTimespan]= self.dta[changeRecalcVars].sum(axis=1)
        
        # Existing Version: Add the Total Change calculated in the Gittleman Analysis code - should be very close to valueOf diffs
        # WITHOUT Mortgage -- alcready inccluded in the TotalChangeInWealth values
        componentVars = ['House', 'OtherRealEstate', 'Business', 'BrokerageStocks', 'CheckingAndSavings', 'Vehicle', 'OtherAssets', 'OtherDebts']
        totalChangeVars = [s + "_TotalChangeInWealth_" + self.ga.inflatedTimespan for s in componentVars]    
        self.dta['Total_ChangeInRealWealth_'  + self.ga.inflatedTimespan]= self.dta[totalChangeVars].sum(axis=1) 
        # self.dta['Total_ChangeInRealWealth_'  + self.ga.inflatedTimespan] = self.dta['Total_ChangeInNominalWealth_'  + self.ga.timespan] * self.cpi_inflationEndToTargetYear
        


        aggDictionary = {
                    'familyInterview_N': ('familyInterviewId_' +self.ga.eyStr,'count'),
                    'familyInterview_TotalWeights': ('familyInterviewId_' +self.ga.eyStr,'SumOfWeights'),
                                       
                    # Real Values                    
                    # Orig, with house
                    'Old_changeInRealNetWorth_mean' : ('changeInRealNetWorth_' + self.ga.inflatedTimespan, 'mean'),
                    'Old_changeInRealNetWorth_median' : ('changeInRealNetWorth_' + self.ga.inflatedTimespan, 'median'),

                    'Old_Total_ChangeInRealWealth_mean' : ('Total_ChangeInWealth_' + self.ga.inflatedTimespan, 'mean'),
                    'Old_Total_ChangeInRealWealth_median' : ('Total_ChangeInWealth_' + self.ga.inflatedTimespan, 'median'),

                    
                    # New, 
                    'New_Total_ChangeInRealWealthRecalc_mean' : ('Total_ChangeInRealWealthRecalc_' + self.ga.inflatedTimespan, 'mean'),
                    'New_Total_ChangeInRealWealthRecalc_median' : ('Total_ChangeInRealWealthRecalc_' + self.ga.inflatedTimespan, 'median'),

                    'New_Total_ChangeInRealWealth_mean' : ('Total_ChangeInRealWealth_' + self.ga.inflatedTimespan, 'mean'),
                    'New_Total_ChangeInRealWealth_median' : ('Total_ChangeInRealWealth_' + self.ga.inflatedTimespan, 'median'),
                    
                    } 
        
                
        dataMask = (self.dta['cleaningStatus_' + self.ga.eyStr] == 'Keep')
        
        weightVar = 'LongitudinalWeightHH_' + self.ga.syStr
                                
        resultsByRace = wGroupByAgg(self.dta.loc[dataMask], ['raceR_' + self.ga.syStr], aggregationDict = aggDictionary, varForWeights = (weightVar)).reset_index()
        resultsByRace['Source'] = 'Race_' + self.ga.eyStr

        tmp  = resultsByRace.loc[resultsByRace.raceR_1984.isin(['Black', 'White'])].copy()
        
        # Start with a simple empty DF -- two families
        yrStr = str(1984)
        correctData = pd.DataFrame({
                'raceR_' + yrStr :['Black', 'White'], 
                'familyInterview_N' :[1839,3240], 
                'familyInterview_TotalWeights' :[11534,79925], 
                'Old_changeInRealNetWorth_mean': [9565.85899, 41333.14102],
                'Old_changeInRealNetWorth_median': [339.4462728, 9249.689528],
                'Source': ['Race_' + self.ga.eyStr, 'Race_' + self.ga.eyStr]
                },
            columns=['raceR_' + yrStr, 'familyInterview_N','familyInterview_TotalWeights', 'Old_changeInRealNetWorth_mean', 'Old_changeInRealNetWorth_median', 'Source'])
        correctData['Old_Total_ChangeInRealWealth_mean'] = correctData['Old_changeInRealNetWorth_mean']
        correctData['Old_Total_ChangeInRealWealth_median'] = correctData['Old_changeInRealNetWorth_median']

        correctData['New_Total_ChangeInRealWealthRecalc_mean'] = correctData['Old_changeInRealNetWorth_mean']
        correctData['New_Total_ChangeInRealWealthRecalc_median'] = correctData['Old_changeInRealNetWorth_median']

        correctData['New_Total_ChangeInRealWealth_mean'] = correctData['Old_changeInRealNetWorth_mean']
        correctData['New_Total_ChangeInRealWealth_median'] = correctData['Old_changeInRealNetWorth_median']

        self.assertTrue(dataFramesEqualish(correctData, tmp))

        # resultsByRace.to_csv(os.path.join(self.ga.baseDir, self.ga.outputSubDir, 'Test_TotalChangeWithHome_' + self.ga.inflatedTimespan +'.csv'))


    def test_inflation(self):
        self.getResults(1984, 1989, 1998)
        self.assertTrue(closeEnough(self.cpi_totalInflationStartToEndYear,  1.193455))
        self.assertTrue(closeEnough(self.cpi_inflationEndToTargetYear, 1.314516))


    def test_Appendix1_CrossSectional(self):
        self.getResults(1984, 1989, 1998)
        tmp84 = pd.read_csv(os.path.join(self.ga.baseDir, self.ga.outputSubDir, "AppendixTable1_CrossSectionalWealth_1984.csv"))
        yrStr = str(1984)
        
        # Start with a simple empty DF -- two families
        correctData = pd.DataFrame({
                'raceR_' + yrStr :['Black', 'White'], 
                'familyInterview_N' :[2575,4336], 
                'real_networth_mean': [29100, 149200],
                'real_networth_median': [3800, 60400],
                },
            columns=['raceR_' + yrStr, 'familyInterview_N','real_networth_mean','real_networth_median'])

        self.assertTrue(dataFramesEqualish(correctData, tmp84.loc[tmp84.raceR_1984.isin(['Black', 'White']),correctData.columns]))
           
        tmp89 = pd.read_csv(os.path.join(self.ga.baseDir, self.ga.outputSubDir, "AppendixTable1_CrossSectionalWealth_1989.csv"))
        self.assertTrue(withinPercentDiff(tmp89.loc[tmp89.raceR_1989=='Black', 'familyInterview_N'].iloc[0], 2609, 0.02))
        self.assertTrue(withinPercentDiff(tmp89.loc[tmp89.raceR_1989=='White', 'familyInterview_N'].iloc[0], 4505, 0.02))        

        tmp94 = pd.read_csv(os.path.join(self.ga.baseDir, self.ga.outputSubDir, "AppendixTable1_CrossSectionalWealth_1994.csv"))
        self.assertTrue(withinPercentDiff(tmp94.loc[tmp94.raceR_1994=='Black', 'familyInterview_N'].iloc[0], 2611, 0.02))
        self.assertTrue(withinPercentDiff(tmp94.loc[tmp94.raceR_1994=='White', 'familyInterview_N'].iloc[0], 4804, 0.02))        
        
    def test_Appendix1_Longitudinal(self):
        self.getResults(1984, 1989, 1998)
        tmp84to89 = pd.read_csv(os.path.join(self.ga.baseDir, self.ga.outputSubDir, "Table3_AndAppendixTable1_WealthForPeriod_1984_1989.csv"))
        
        # ['Unnamed: 0', 'raceR_1984', 'familyInterview_N', 'real_networth_start_mean', 'real_networth_start_25percentile', 'real_networth_start_50percentile', 'real_networth_start_75percentile', 'real_networth_end_mean', 'real_networth_end_25percentile', 'real_networth_end_50percentile', 'real_networth_end_75percentile', 'Source']

        # self.assertTrue(withinPercentDiff(tmp84to89, 10))
                
        tmp89to94 = pd.read_csv(os.path.join(self.ga.baseDir, self.ga.outputSubDir, "Table3_AndAppendixTable1_WealthForPeriod_1989_1994.csv"))
        
