import os
from Survey.SurveyFunctions import *
from Survey.SurveyDataSummarizer import SurveyDataSummarizer
import MStarReport.InequalityAnalysisBase as InequalityAnalysisBase


''' 
This class takes single-year processed, recoded, and cleaned PSID files and 
generates tables to mimic Gittleman and Wolff (2004). 

It is used for "Model Docking": it allows the user to verify, value by value, whether the code works according to published results, for a given set of parameters. 
The way to use it is to set the various input parameters for the cleaning etc code to that used in Gittleman (how outliers are handled, 
which populaton is included etc), and compare.  Then, having established a common baseline, you can chnage individual parameters to fix your desired scenario analysis, kowning that the baseline is solid. 
 
'''
class CrossSectionalDescriber(InequalityAnalysisBase.InequalityAnalysisBase):
    
    def __init__(self, baseDir, inputSubDir, inputBaseName,outputBaseName, outputSubDir):
        super().__init__(baseDir, inputSubDir, inputBaseName,outputBaseName, outputSubDir)


    def calcDescriptivesForYear_Generic(self, analysisYear, toYear):

        varsToSegmentTo = [
                            'ageGroup_' + self.syStr,
                            'ageGroup_' + self.syStr,
                           'educationGroup_' + self.syStr,
                           'maritalStatusGroup_' + self.syStr,
                           'raceR_' + self.syStr,
                           ]

        weightVar = 'LongitudinalWeightHH_' + self.eyStr
        sds = SurveyDataSummarizer(self.dta, weightVar, fieldMetaData=None,
                                   fieldsToSummarize=None, fieldsToCrossTab=varsToSegmentTo)
        sds.doIt(os.path.join(self.baseDir, self.outputSubDir, 'SummaryReport_CrossSectional_' + str(analysisYear) +'.xlsx'))



    def calcDescriptivesForYear_ReportTables(self, analysisYear, toYear):
        ''' Generates tables to mimic, and manually compare against, Gittleman and Wolff (2004) '''
        weightVar = 'LongitudinalWeightHH_' + self.eyStr

        if not os.path.exists(os.path.join(self.baseDir, self.outputSubDir)):
            os.makedirs(os.path.join(self.baseDir, self.outputSubDir))

        writer = pd.ExcelWriter(os.path.join(self.baseDir, self.outputSubDir, 'ReportTables_DescriptiveXS_' + str(analysisYear) +'.xlsx') , engine='xlsxwriter')
        workbook = writer.book

        # Make some names consistent, to make it easier to analyze
        self.dta["valueOfEmployerRetirePlan_Net_" + self.eyStr] = self.dta["valueOfEmployerRetirePlan_Gross_" + self.eyStr]
        self.dta["valueOfPrivateRetirePlan_Net_" + self.eyStr] = self.dta["valueOfPrivateRetirePlan_Gross_" + self.eyStr]

        # Table 1: Wealth Characteristics by Head of Family Income, 1994
        # PLUS Appendix Table 1, Cross-Sectional Component
        varsToSegmentTo = ['ageGroup_' + self.syStr,
                           'educationGroup_' + self.syStr,
                           'maritalStatusGroup_' + self.syStr,
                           # 'incomeGroup_PreTaxReal_' + self.inflatedEnd
                           ]
                                
        aggDictionary = {
                    'familyInterview_N': ('familyInterviewId_' +self.eyStr,'count'),
                    'familyInterview_TotalWeights': ('familyInterviewId_' +self.eyStr,'SumOfWeights'),

                    # Values used to compare with Descriptive Stats
                    'real_networth_mean': ('inflatedNetWorthWithHome_' + self.inflatedEnd, 'mean'),
                    'real_networth_median': ('inflatedNetWorthWithHome_' + self.inflatedEnd, 'median')
                    } 
        
                

        results = pd.DataFrame(wAgg(self.dta, aggregationDict = aggDictionary, varForWeights= (weightVar))).transpose()
        results['Source'] = 'All_' + self.eyStr

        segmentedResults = wGroupByAgg(self.dta, ['raceR_' + self.syStr], aggregationDict = aggDictionary, varForWeights = (weightVar))
        if segmentedResults is not None:
            segmentedResults.reset_index(inplace=True)
            segmentedResults['Source'] = 'RaceR'
            segmentedResults.to_excel(writer, "A_Tb1_CrossSectionalWealth")

            results = pd.concat([segmentedResults, results], ignore_index=True, sort=False)
        else:
            print("Debug me")

        for var in varsToSegmentTo:
            segmentVar = 'raceR_' + var
            segmentVars = ['raceR_' + self.syStr, var]
            # tmpDta[segmentVar] =  tmpDta['raceR_' + self.syStr] + tmpDta[var].astype(str) 
            segmentedResults = wGroupByAgg(self.dta, segmentVars, aggregationDict = aggDictionary, varForWeights = (weightVar)).reset_index()
            segmentedResults['Source'] = segmentVar

            results = pd.concat([segmentedResults, results], ignore_index=True, sort=False)
        
        results.to_excel(writer, "Tb1_WealthByGroup")


        # Table 2: Portfolio Composition of Wealth by Race 
        weightVar = 'LongitudinalWeightHH_' + self.eyStr
        tmpDta = self.dta.copy()

        componentVars = ['House','OtherRealEstate', 'Vehicle', 'Business', 'BrokerageStocks',  'CheckingAndSavings', 'OtherAssets', 'AllOtherDebts', 'PrivateRetirePlan', 'EmployerRetirePlan']
        theVars = ['valueOf' + s + '_Net_' + self.syStr for s in componentVars] + ['NetWorthWithHomeAnd401k_' + self.syStr]
        tmpDta[theVars] = tmpDta[theVars].fillna(value=0)
        
        tmpDta['House_HasAsset_' + self.syStr] = tmpDta['valueOfHouse_Net_' + self.syStr].ne(0)
        tmpDta['OtherRealEstate_HasAsset_' + self.syStr] = tmpDta['valueOfOtherRealEstate_Net_' + self.syStr].ne(0)
        tmpDta['Vehicle_HasAsset_' + self.syStr] = tmpDta['valueOfVehicle_Net_' + self.syStr].ne(0)
        tmpDta['Business_HasAsset_' + self.syStr] = tmpDta['valueOfBusiness_Net_' + self.syStr].ne(0)
        tmpDta['BrokerageStocks_HasAsset_' + self.syStr] = tmpDta['valueOfBrokerageStocks_Net_' + self.syStr].ne(0)
        tmpDta['CheckingAndSavings_HasAsset_' + self.syStr] = tmpDta['valueOfCheckingAndSavings_Net_' + self.syStr].ne(0)
        tmpDta['OtherAssets_HasAsset_' + self.syStr] = tmpDta['valueOfOtherAssets_Net_' + self.syStr].ne(0)
        tmpDta['AllOtherDebts_HasAsset_' + self.syStr] = tmpDta['valueOfAllOtherDebts_Net_' + self.syStr].ne(0)
        tmpDta['PrivateRetirePlan_HasAsset_' + self.syStr] = tmpDta['valueOfPrivateRetirePlan_Gross_' + self.syStr].ne(0)
        tmpDta['EmployerRetirePlan_HasAsset_' + self.syStr] = tmpDta['valueOfEmployerRetirePlan_Gross_' + self.syStr].ne(0)

        tmpDta['House_PercentOfWealth_' + self.syStr] = tmpDta['valueOfHouse_Net_' + self.syStr].div(tmpDta['NetWorthWithHomeAnd401k_' + self.syStr], fill_value=0)
        tmpDta['OtherRealEstate_PercentOfWealth_' + self.syStr] = tmpDta['valueOfOtherRealEstate_Net_' + self.syStr].div(tmpDta['NetWorthWithHomeAnd401k_' + self.syStr], fill_value=0)
        tmpDta['Vehicle_PercentOfWealth_' + self.syStr] = tmpDta['valueOfVehicle_Net_' + self.syStr].div(tmpDta['NetWorthWithHomeAnd401k_' + self.syStr], fill_value=0)
        tmpDta['Business_PercentOfWealth_' + self.syStr] = tmpDta['valueOfBusiness_Net_' + self.syStr].div(tmpDta['NetWorthWithHomeAnd401k_' + self.syStr], fill_value=0)
        tmpDta['BrokerageStocks_PercentOfWealth_' + self.syStr] = tmpDta['valueOfBrokerageStocks_Net_' + self.syStr].div(tmpDta['NetWorthWithHomeAnd401k_' + self.syStr], fill_value=0)
        tmpDta['CheckingAndSavings_PercentOfWealth_' + self.syStr] = tmpDta['valueOfCheckingAndSavings_Net_' + self.syStr].div(tmpDta['NetWorthWithHomeAnd401k_' + self.syStr], fill_value=0)
        
        tmpDta['OtherAssets_PercentOfWealth_' + self.syStr] = tmpDta['valueOfOtherAssets_Net_' + self.syStr].div(tmpDta['NetWorthWithHomeAnd401k_' + self.syStr], fill_value=0)
        tmpDta['AllOtherDebts_PercentOfWealth_' + self.syStr] = tmpDta['valueOfAllOtherDebts_Net_' + self.syStr].div(tmpDta['NetWorthWithHomeAnd401k_' + self.syStr], fill_value=0)
        tmpDta['PrivateRetirePlan_PercentOfWealth_' + self.syStr] = tmpDta['valueOfPrivateRetirePlan_Gross_' + self.syStr].div(tmpDta['NetWorthWithHomeAnd401k_' + self.syStr], fill_value=0)
        tmpDta['EmployerRetirePlan_PercentOfWealth_' + self.syStr] = tmpDta['valueOfEmployerRetirePlan_Gross_' + self.syStr].div(tmpDta['NetWorthWithHomeAnd401k_' + self.syStr], fill_value=0)
          
        aggDictionary = {
                    'familyInterview_N': ('familyInterviewId_' +self.eyStr,'count'),
                    'familyInterview_TotalWeights': ('familyInterviewId_' +self.eyStr,'SumOfWeights'),

                    # Values used to compare with Descriptive Stats
                    'House_HasAsset_Percent': ('House_HasAsset_' + self.syStr, 'mean'),
                    'OtherRealEstate_HasAsset_Percent': ('OtherRealEstate_HasAsset_' + self.syStr, 'mean'),
                    'Vehicle_HasAsset_Percent': ('Vehicle_HasAsset_' + self.syStr, 'mean'),
                    'Business_HasAsset_Percent': ('Business_HasAsset_' + self.syStr, 'mean'),
                    'BrokerageStocks_HasAsset_Percent': ('BrokerageStocks_HasAsset_' + self.syStr, 'mean'),
                    'CheckingAndSavings_HasAsset_Percent': ('CheckingAndSavings_HasAsset_' + self.syStr, 'mean'),
                    'OtherAssets_HasAsset_Percent': ('OtherAssets_HasAsset_' + self.syStr, 'mean'),
                    'AllOtherDebts_HasAsset_Percent': ('AllOtherDebts_HasAsset_' + self.syStr, 'mean'),
                    'PrivateRetirePlan_HasAsset_Percent': ('PrivateRetirePlan_HasAsset_' + self.syStr, 'mean'),
                    'EmployerRetirePlan_HasAsset_Percent': ('EmployerRetirePlan_HasAsset_' + self.syStr, 'mean'),
                    
                    # Values used to compare with Descriptive Stats
                    'House_PercentOfWealth_Avg': ('House_PercentOfWealth_' + self.syStr, 'mean'),
                    'OtherRealEstate_PercentOfWealth_Avg': ('OtherRealEstate_PercentOfWealth_' + self.syStr, 'mean'),
                    'Vehicle_PercentOfWealth_Avg': ('Vehicle_PercentOfWealth_' + self.syStr, 'mean'),
                    'Business_PercentOfWealth_Avg': ('Business_PercentOfWealth_' + self.syStr, 'mean'),
                    'BrokerageStocks_PercentOfWealth_Avg': ('BrokerageStocks_PercentOfWealth_' + self.syStr, 'mean'),
                    'CheckingAndSavings_PercentOfWealth_Avg': ('CheckingAndSavings_PercentOfWealth_' + self.syStr, 'mean'),
                    'OtherAssets_PercentOfWealth_Avg': ('OtherAssets_PercentOfWealth_' + self.syStr, 'mean'),
                    'AllOtherDebts_PercentOfWealth_Avg': ('AllOtherDebts_PercentOfWealth_' + self.syStr, 'mean'),
                    'PrivateRetirePlan_PercentOfWealth_Avg': ('PrivateRetirePlan_PercentOfWealth_' + self.syStr, 'mean'),
                    'EmployerRetirePlan_PercentOfWealth_Avg': ('EmployerRetirePlan_PercentOfWealth_' + self.syStr, 'mean'),

                    # Values used to compare with Descriptive Stats
                    'NetWorthWithHomeRecalc_Sum': ('NetWorthWithHomeRecalc_' + self.syStr, 'sum'),
                    'NetWorthWithHome_Sum': ('NetWorthWithHome_' + self.syStr, 'sum'),
                    'NetWorthWithHomeAnd401k_Sum': ('NetWorthWithHomeAnd401k_' + self.syStr, 'sum'),
                    'House_Value_Sum': ('valueOfHouse_Net_' + self.syStr, 'sum'),
                    'OtherRealEstate_Value_Sum': ('valueOfOtherRealEstate_Net_' + self.syStr, 'sum'),
                    'Vehicle_Value_Sum': ('valueOfVehicle_Net_' + self.syStr, 'sum'),
                    'Business_Value_Sum': ('valueOfBusiness_Net_' + self.syStr, 'sum'),
                    'BrokerageStocks_Value_Sum': ('valueOfBrokerageStocks_Net_' + self.syStr, 'sum'),
                    'CheckingAndSavings_Value_Sum': ('valueOfCheckingAndSavings_Net_' + self.syStr, 'sum'),
                    'OtherAssets_Value_Sum': ('valueOfOtherAssets_Net_' + self.syStr, 'sum'),
                    'AllOtherDebts_Value_Sum': ('valueOfAllOtherDebts_Net_' + self.syStr, 'sum'),
                    'PrivateRetirePlan_Value_Sum': ('valueOfPrivateRetirePlan_Gross_' + self.syStr, 'sum'),
                    'EmployerRetirePlan_Value_Sum': ('valueOfEmployerRetirePlan_Gross_' + self.syStr, 'sum'),
                    } 

        segmentedResults = wGroupByAgg(tmpDta, 'raceR_' + self.syStr, 
                                       aggregationDict = aggDictionary, 
                                       varForWeights = (weightVar)).reset_index()
        segmentedResults['Source'] = segmentVar
    
        segmentedResults['House_PercentOfWealth_AvgAsSums_' + self.syStr] =  segmentedResults.House_Value_Sum / (segmentedResults.NetWorthWithHomeAnd401k_Sum)
        segmentedResults['OtherRealEstate_PercentOfWealth_AvgAsSums_' + self.syStr] =  segmentedResults.OtherRealEstate_Value_Sum / (segmentedResults.NetWorthWithHomeAnd401k_Sum)
        segmentedResults['Vehicle_PercentOfWealth_AvgAsSums_' + self.syStr] =  segmentedResults.Vehicle_Value_Sum / (segmentedResults.NetWorthWithHomeAnd401k_Sum)
        segmentedResults['Business_PercentOfWealth_AvgAsSums_' + self.syStr] =  segmentedResults.Business_Value_Sum / (segmentedResults.NetWorthWithHomeAnd401k_Sum)
        segmentedResults['BrokerageStocks_PercentOfWealth_AvgAsSums_' + self.syStr] =  segmentedResults.BrokerageStocks_Value_Sum / (segmentedResults.NetWorthWithHomeAnd401k_Sum)
        segmentedResults['CheckingAndSavings_PercentOfWealth_AvgAsSums_' + self.syStr] =  segmentedResults.CheckingAndSavings_Value_Sum / (segmentedResults.NetWorthWithHomeAnd401k_Sum)
        segmentedResults['OtherAssets_PercentOfWealth_AvgAsSums_' + self.syStr] =  segmentedResults.OtherAssets_Value_Sum / (segmentedResults.NetWorthWithHomeAnd401k_Sum)
        segmentedResults['AllOtherDebts_PercentOfWealth_AvgAsSums_' + self.syStr] =  segmentedResults.AllOtherDebts_Value_Sum / (segmentedResults.NetWorthWithHomeAnd401k_Sum)
        segmentedResults['PrivateRetirePlan_PercentOfWealth_AvgAsSums_' + self.syStr] =  segmentedResults.PrivateRetirePlan_Value_Sum / (segmentedResults.NetWorthWithHomeAnd401k_Sum)
        segmentedResults['EmployerRetirePlan_PercentOfWealth_AvgAsSums_' + self.syStr] =  segmentedResults.EmployerRetirePlan_Value_Sum / (segmentedResults.NetWorthWithHomeAnd401k_Sum)
        
        segmentedResults.to_excel(writer, "Tb2_AssetsByType")
        workbook.close()


    def doIt(self, useCleanedDataOnly = True):
        self.useCleanedDataOnly = useCleanedDataOnly
        toYear = 2019
        # yearsWealthDataCollected = [1989, 1994]

        # Cross Sectional Descriptives
        for year in self.yearsWealthDataCollected.copy():
            self.clearData()
            self.setPeriod(year, year, toYear)
            self.readCrossSectionalData(year)
            self.calcDescriptivesForYear_ReportTables(year, toYear)

        theMin = (min(self.yearsWealthDataCollected))
        self.calcDescriptivesForYear_Generic(theMin, toYear)
        theMax = (max(self.yearsWealthDataCollected))
        self.calcDescriptivesForYear_Generic(theMax, toYear)
