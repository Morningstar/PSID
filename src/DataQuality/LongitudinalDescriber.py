import os
# import ReplicationAnalyzer
from Survey.SurveyFunctions import *
import DataQuality.CrossSectionalTester as CrossSectionalTester
from Survey.SurveyTimeSeriesQA import SurveyTimeSeriesQA
import MStarReport.InequalityAnalysisBase as InequalityAnalysisBase

'''
This class takes the two-period longitudinal data files, with savings rates included, and looks for common problems:
1) Large shifts in the population, usually caused by a change in the underlying meaning or coding of a PSID variable
2) Large shifts in a given household's data, usually caused by bad data or extreme events 

In then runs as series of analyses on savings rates that replicate tables from Gittleman and Wolff 2004 for comparison with their results 
These tables complement those from CrossSectionalDescriber - this one handles tables using longitudinal data; the other handles tables for cross-sectional data.

It is used for "Model Docking": it allows the user to verify, value by value, whether the code works according to published results, for a given set of parameters. 
The way to use it is to set the various input parameters for the cleaning etc code to that used in Gittleman (how outliers are handled, 
which populaton is included etc), and compare.  Then, having established a common baseline, you can chnage individual parameters to fix your desired scenario analysis, kowning that the baseline is solid. 

'''

class LongitudinalDescriber(InequalityAnalysisBase.InequalityAnalysisBase):
    
    def __init__(self, baseDir, inputSubDir, inputBaseName,outputBaseName, outputSubDir, includeChangeAnalysis, longitudinalFieldsToInclude = None):
        super().__init__(baseDir, inputSubDir, inputBaseName,outputBaseName, outputSubDir)
        self.includeChangeAnalysis = includeChangeAnalysis
        self.longitudinalFieldsToInclude = longitudinalFieldsToInclude


    def checkQualityOfInputData_Longitudinal(self):

        # Look for non-wealth vars -- available any year
        tsTester = SurveyTimeSeriesQA(dta = self.dta.copy(), dfLabel = "SW Analysis (" + str(self.timespan) + ")",
                                      baseDir = self.baseDir, outputDir = self.outputSubDir,
                                      isWeighted = True, weightVar = "familyInterviewId_" + self.syStr,
                                      raiseOnError = False)

        tsTester.setVarNameStyle(isTwoYear = False, isInflatedTo=self.toYear)

        nonWealthVarYears = ['MovedR', 'ageR', 'hasHouse', 'valueOfHouse_Gross', 'valueOfHouse_Debt', 'FederalIncomeTaxesRS','FederalIncomeTaxesO',  'totalIncomeHH',  'fiitax']
        tsTester.setup(outputFileNameBase = "QA_NonWealthYears_" + self.syStr, varsOfInterest = nonWealthVarYears, years=self.yearsWithFamilyData.copy(), isLongForm=False, twoDigitYearSuffix=False, analyzeOnlyTimeData=False)

        # tsTester.lookForExtremePerPersonChanges(percentChangeForExtreme=.50)
        if self.includeChangeAnalysis:
            tsTester.lookForExtremePerPersonChanges(idVar = "LongitudinalWeightHH_" + self.eyStr,
                                   weightVar = "familyInterviewId_" + self.syStr,
                                   fieldsToCrossTabList = ["raceR_" + self.syStr], percentChangeForExtreme=.50)
        tsTester.checkForMedianShifts(percentChangeForError=.10)

        # Look for wealth vars - only available on the start / end years
        tsTester = SurveyTimeSeriesQA(dta = self.dta.copy(), dfLabel = "SW Analysis (" + str(self.timespan) + ")",
                                      baseDir = self.baseDir, outputDir = self.outputSubDir,
                                      isWeighted = True, weightVar = "familyInterviewId_" + self.syStr,
                                      raiseOnError = False)

        tsTester.setVarNameStyle(isTwoYear = False, isInflatedTo=self.toYear)

        wealthYearVars = tsTester.getCleanVarName_Series(self.dta.columns.copy())
        wealthYearVars = np.unique(np.array(wealthYearVars))
        varsWeDontNeed = ['familyInterviewId', 'cleaningStatus']
        wealthYearVars = [x for x in wealthYearVars if ((x not in nonWealthVarYears) and (x not in varsWeDontNeed))]

        tsTester.setup(outputFileNameBase = "QA_WealthYears_" + self.syStr, varsOfInterest = wealthYearVars, years = [self.startYear, self.endYear], isLongForm=False, twoDigitYearSuffix=False, analyzeOnlyTimeData=False)
        # tsTester.lookForExtremePerPersonChanges(percentChangeForExtreme=.50)
        if self.includeChangeAnalysis:
            tsTester.lookForExtremePerPersonChanges(idVar = "LongitudinalWeightHH_" + self.eyStr,
                                   weightVar = "familyInterviewId_" + self.syStr,
                                   fieldsToCrossTabList = ["raceR_" + self.syStr], percentChangeForExtreme=.50)
        tsTester.checkForMedianShifts(percentChangeForError = .10 * self.duration)


    def checkQualityOfActiveSavingsVars_Longitudinal(self):
        # Each of the following entries should have a variable _TotalChangeInWealth, _CapitalGains and _Savings
        componentVars = ['House', 'OtherRealEstate', 'Business', 'BrokerageStocks', 'CheckingAndSavings', 'Vehicle', 'OtherAssets', 'AllOtherDebts', 'PrivateRetirePlan', 'EmployerRetirePlan']
        totalChangeVars = [s + "_TotalChangeInWealth_" + self.inflatedTimespan for s in componentVars]    
        capitalGainsVars = [s + "_CapitalGains_" + self.inflatedTimespan for s in componentVars]
        grossSavingsVars = [s + "_Savings_" + self.inflatedTimespan for s in componentVars]
        
        varsUsed = [] + totalChangeVars + capitalGainsVars + grossSavingsVars

        weightVar = 'LongitudinalWeightHH_' + self.eyStr

        varsToExpore = varsUsed + [weightVar, 'averageNominalIncome_AllYears_' + self.timespan, 'TotalTax_' + self.eyStr, 'TotalTax_' + self.syStr] + \
                                   ['Total_ChangeInWealth_'  + self.inflatedTimespan, 'Total_CapitalGains_'  + self.inflatedTimespan, 'Total_GrossSavings_'  + self.inflatedTimespan, 'Total_NetActiveSavings_'  + self.inflatedTimespan, 
                                   'netMoveIn_' + self.inflatedTimespan, 'netMoveOut_' + self.inflatedTimespan, 
                                   'activeSavingsRate_PerPerson_' + self.inflatedTimespan
                                   ]

        # Output summary stats on the data, to check everything is ok:
        cleanVar = 'cleaningStatus_' + self.eyStr
        csTester = CrossSectionalTester.CrossSectionalTester(dta = self.dta.loc[self.dta[cleanVar] == 'Keep', varsToExpore].copy(),
                                                          dfLabel = "Vars used in Active Savings Calc" + str(self.inflatedTimespan) + ")",
                                                          year = self.endYear,
                                                          varMapping = None,
                                                          ignoreUnmappedVars = True)
        
        csTester.exploreData(reportFileNameWithPathNoExtension = os.path.join(self.baseDir, self.outputSubDir, "ActiveSavingsVars_" + self.inflatedTimespan),
                             weightVar = weightVar)
        csTester.checkDataQuality(raiseIfMissing = False)


    def calcDescriptivesForTimePeriod(self):
        '''
        Replicates Tables from Gittleman and Wolff 2004 for comparison with their results
        :return: Outputs an excel file called Tables_[StartYear]_[EndYear]
        '''
        # Table 3: Summary Statistics on Wealth 1984-1994
        # Also: Appendix Table 1, part B

        if not os.path.exists(os.path.join(self.baseDir, self.outputSubDir)):
            os.makedirs(os.path.join(self.baseDir, self.outputSubDir))

        tempWriter = pd.ExcelWriter(os.path.join(self.baseDir, self.outputSubDir,'Tables_' + self.timespan + '.xlsx'), engine='xlsxwriter')

        aggDictionary = {
                    'familyInterview_N': ('familyInterviewId_' +self.eyStr,'count'),

                    # Values used to compare with Descriptive Stats
                    'real_networth_start_mean': ('inflatedNetWorthWithHome_' + self.inflatedStart, 'mean'),
                    'real_networth_start_25percentile': ('inflatedNetWorthWithHome_' + self.inflatedStart, 'percentile', [.25]),
                    'real_networth_start_50percentile': ('inflatedNetWorthWithHome_' + self.inflatedStart, 'percentile', [.5]),
                    'real_networth_start_75percentile': ('inflatedNetWorthWithHome_' + self.inflatedStart, 'percentile', [.75]),

                    'real_networth_end_mean': ('inflatedNetWorthWithHome_' + self.inflatedEnd, 'mean'),
                    'real_networth_end_25percentile': ('inflatedNetWorthWithHome_' + self.inflatedEnd, 'percentile', [.25]),
                    'real_networth_end_50percentile': ('inflatedNetWorthWithHome_' + self.inflatedEnd, 'percentile', [.5]),
                    'real_networth_end_75percentile': ('inflatedNetWorthWithHome_' + self.inflatedEnd, 'percentile', [.75]),
                    } 

        weightVar = 'LongitudinalWeightHH_' + self.eyStr
        segmentedResults = wGroupByAgg(self.dta, ['raceR_' + self.syStr], aggregationDict = aggDictionary, varForWeights = (weightVar)).reset_index()
        segmentedResults['Source'] = 'RaceR'
        # segmentedResults.to_csv(os.path.join(self.baseDir, self.outputSubDir, 'Table3_AndAppendixTable1_WealthForPeriod_' + self.timespan +'.csv'))
        segmentedResults.to_excel(tempWriter, "Tb3_AppTb1_WealthForPeriod")

        
        # Table 4: Summary stats on Change in Wealth and its Components
        aggDictionary = {
                    'familyInterview_N': ('familyInterviewId_' +self.eyStr,'count'),

                    'change_real_networth_mean': ('changeInRealNetWorth_' + self.inflatedTimespan, 'mean'),
                    'change_real_networth_percentiles_25': ('changeInRealNetWorth_' + self.inflatedTimespan, 'percentile', [.25]),
                    'change_real_networth_percentiles_50': ('changeInRealNetWorth_' + self.inflatedTimespan, 'percentile', [.5]),
                    'change_real_networth_percentiles_75': ('changeInRealNetWorth_' + self.inflatedTimespan, 'percentile', [.75]),

                    'total_change_mean': ('Total_ChangeInWealth_' + self.inflatedTimespan, 'mean'),
                    'total_change_percentile_25': ('Total_ChangeInWealth_' + self.inflatedTimespan, 'percentile', [.25]),
                    'total_change_percentiles_50': ('Total_ChangeInWealth_' + self.inflatedTimespan, 'percentile', [.5]),
                    'total_change_percentiles_75': ('Total_ChangeInWealth_' + self.inflatedTimespan, 'percentile', [.75]),

                    'total_capitalgains_mean': ('Total_CapitalGains_' + self.inflatedTimespan, 'mean'),
                    'total_capitalgains_percentiles_25': ('Total_CapitalGains_' + self.inflatedTimespan, 'percentile', [.25]),
                    'total_capitalgains_percentiles_50': ('Total_CapitalGains_' + self.inflatedTimespan, 'percentile', [.5 ]),
                    'total_capitalgains_percentiles_75': ('Total_CapitalGains_' + self.inflatedTimespan, 'percentile', [.75]),

                    'total_grosssavings_mean': ('Total_GrossSavings_' + self.inflatedTimespan, 'mean'),
                    'total_grosssavings_percentiles_25': ('Total_GrossSavings_' + self.inflatedTimespan, 'percentile', [.25]),
                    'total_grosssavings_percentiles_50': ('Total_GrossSavings_' + self.inflatedTimespan, 'percentile', [.5]),
                    'total_grosssavings_percentiles_75': ('Total_GrossSavings_' + self.inflatedTimespan, 'percentile', [.75]),

                    'total_gifts_mean': ('largeGift_All_AmountHH_' + self.inflatedTimespan, 'mean'),
                    'total_gifts_percentiles_25': ('largeGift_All_AmountHH_' + self.inflatedTimespan, 'percentile', [.25]),
                    'total_gifts_percentiles_50': ('largeGift_All_AmountHH_' + self.inflatedTimespan, 'percentile', [.5]),
                    'total_gifts_percentiles_75': ('largeGift_All_AmountHH_' + self.inflatedTimespan, 'percentile', [.75]),

                    'total_moves_mean': ('netAssetMove_' + self.inflatedTimespan, 'mean'),
                    'total_moves_percentiles_25': ('netAssetMove_' + self.inflatedTimespan, 'percentile', [.25]),
                    'total_moves_percentiles_50': ('netAssetMove_' + self.inflatedTimespan, 'percentile', [.5]),
                    'total_moves_percentiles_75': ('netAssetMove_' + self.inflatedTimespan, 'percentile', [.75]),

                    'total_activesavings_mean': ('Total_NetActiveSavings_' + self.inflatedTimespan, 'mean'),
                    'total_activesavings_percentile_25': ('Total_NetActiveSavings_' + self.inflatedTimespan, 'percentile', [.25]),
                    'total_activesavings_percentiles_50': ('Total_NetActiveSavings_' + self.inflatedTimespan, 'percentile', [.5]),
                    'total_activesavings_percentiles_75': ('Total_NetActiveSavings_' + self.inflatedTimespan, 'percentile', [.75]),
        } 

        weightVar = 'LongitudinalWeightHH_' + self.eyStr
        segmentedResults = wGroupByAgg(self.dta, ['raceR_' + self.syStr], aggregationDict = aggDictionary, varForWeights = (weightVar)).reset_index()
        segmentedResults['Source'] = 'RaceR'
        # segmentedResults.to_csv(os.path.join(self.baseDir, self.outputSubDir, 'Table4_WealthComponent_' + self.inflatedTimespan +'.csv'))
        segmentedResults.to_excel(tempWriter, "Tb4_WealthComponent")


        # Table 5: Summary stats on Rates of Change in Wealth and its Components
        self.dta['WealthAppreciationPercent_' + self.inflatedTimespan] =  self.dta['inflatedNetWorthWithHome_' + self.inflatedEnd].sub(self.dta['inflatedNetWorthWithHome_' + self.inflatedStart],fill_value=0).div(self.dta['inflatedNetWorthWithHome_' + self.inflatedStart],fill_value=0)
        self.dta['CapitalGainsPercent_' + self.inflatedTimespan] =  self.dta['Total_CapitalGains_' + self.inflatedTimespan].div(self.dta['inflatedNetWorthWithHome_' + self.inflatedStart],fill_value=0)
        self.dta['InheritancesPercent_' + self.inflatedTimespan] =  self.dta['largeGift_All_AmountHH_' + self.inflatedTimespan].div(self.dta['inflatedNetWorthWithHome_' + self.inflatedStart],fill_value=0)
        self.dta['MoveWealthPercent_' + self.inflatedTimespan] =  self.dta['netAssetMove_' + self.inflatedTimespan].div(self.dta['inflatedNetWorthWithHome_' + self.inflatedStart],fill_value=0)
        
        aggDictionary = {
                    'familyInterview_N': ('familyInterviewId_' +self.eyStr,'count'),

                    'wealth_appreciation_rate_median': ('WealthAppreciationPercent_' + self.inflatedTimespan, 'median'), 
                    # Values used to compare with Descriptive Stats
                    'real_networth_start_sum': ('inflatedNetWorthWithHome_' + self.inflatedStart, 'sum'),
                    'real_networth_end_sum': ('inflatedNetWorthWithHome_' + self.inflatedEnd, 'sum'),
                    
                    'active_savings_rate_median': ('activeSavingsRate_PerPerson_' + self.inflatedTimespan, 'median'), 
                    'real_pre_tax_income_sum' : ('averageRealBeforeTaxIncome_AllYears_' + self.inflatedTimespan, 'sum'),
                    'netactive_real_sum': ('Total_NetActiveSavings_'  + self.inflatedTimespan, 'sum'),                    
                                
                    'capital_gains_rate_median': ('CapitalGainsPercent_' + self.inflatedTimespan, 'median'), 
                    'capital_gains_sum': ('Total_CapitalGains_' + self.inflatedTimespan, 'sum'),                    

                    'inheritance_rate_median': ('InheritancesPercent_' + self.inflatedTimespan, 'median'), 
                    'inheritance_sum': ('largeGift_All_AmountHH_' + self.inflatedTimespan, 'sum'),                    
                    
                    'movewealth_rate_median': ('MoveWealthPercent_' + self.inflatedTimespan, 'median'), 
                    'movewealth_sum': ('netAssetMove_' + self.inflatedTimespan, 'sum'),                    

                    } 

        weightVar = 'LongitudinalWeightHH_' + self.eyStr
        segmentedResults = wGroupByAgg(self.dta, ['raceR_' + self.syStr], aggregationDict = aggDictionary, varForWeights = (weightVar)).reset_index()
        segmentedResults['Source'] = 'RaceR'

        segmentedResults['wealth_appreciation_rate_AvgsAsSums_' + self.inflatedTimespan] = \
                (segmentedResults.real_networth_end_sum - segmentedResults.real_networth_start_sum )/ (segmentedResults.real_networth_start_sum * self.duration) # TODO -- should this be / duration?

        segmentedResults['active_savings_rate_AvgAsSums_' + self.inflatedTimespan] = segmentedResults.netactive_real_sum / (segmentedResults.real_pre_tax_income_sum * self.duration)

        segmentedResults['capital_gains_rate_AvgAsSums_' + self.inflatedTimespan] = segmentedResults.capital_gains_sum / (segmentedResults.real_networth_start_sum * self.duration)

        segmentedResults['inheritance_rate_AvgAsSums_' + self.inflatedTimespan] = segmentedResults.inheritance_sum / (segmentedResults.real_networth_start_sum * self.duration)

        segmentedResults['movewealth_rate_AvgAsSums_' + self.inflatedTimespan] = segmentedResults.movewealth_sum / (segmentedResults.real_networth_start_sum * self.duration)

        # segmentedResults.to_csv(os.path.join(self.baseDir, self.outputSubDir, 'Table5_WealthForPeriod_' + self.inflatedTimespan +'.csv'))
        segmentedResults.to_excel(tempWriter, 'Tb5_WealthForPeriod')

        # Appendix Table 2: Demographics
        self.dta['headIsAfricanAmerican_' + self.syStr] =  self.dta['raceR_' + self.syStr].eq('Black') 
        self.dta['headIsFemale_' + self.syStr] =  self.dta['genderR_' + self.syStr].eq('Female') 

        self.dta['headIsCollegeGrad_' + self.syStr] =  False
        self.dta.loc[self.dta['educationYearsR_' + self.syStr] >= 16, 'headIsCollegeGrad_' + self.syStr] = True

        self.dta['headHasSomeCollege_' + self.syStr] =  False
        self.dta.loc[ (self.dta['educationYearsR_' + self.syStr] >= 9) & (self.dta['educationYearsR_' + self.syStr] < 12), 'headHasSomeCollege_' + self.syStr] = True

        self.dta['headIsHSGrad_' + self.syStr] =  False
        self.dta.loc[ ((self.dta['educationYearsR_' + self.syStr]) == 12), 'headIsHSGrad_' + self.syStr] = True

        self.dta['familyIsMarried_' + self.syStr] =  self.dta['martialStatusR_' + self.syStr].eq("Married")
        self.dta['familyNumChildren_' + self.syStr] =  self.dta['NumChildrenInFU_' + self.syStr]

        aggDictionary = {
                    'familyInterview_N': ('familyInterviewId_' +self.eyStr,'count'),
                    'head_is_africanamerican_percent': ('headIsAfricanAmerican_' + self.syStr, 'mean'),
                    'head_is_female_percent': ('headIsFemale_' + self.syStr, 'mean'),
                    'head_age_avg': ('ageR_' + self.syStr, 'mean'),
                    'head_is_hsgrad_percent': ('headIsHSGrad_' + self.syStr, 'mean'),
                    'head_has_some_college_percent': ('headHasSomeCollege_' + self.syStr, 'mean'),
                    'head_is_college_grad_percent': ('headIsCollegeGrad_' + self.syStr, 'mean'),
                    
                    'family_is_married_percent': ('familyIsMarried_' + self.syStr, 'mean'),
                    'family_num_children_avg': ('familyNumChildren_' + self.syStr, 'mean'),
                    } 

        dataMask = (self.dta['cleaningStatus_' + self.eyStr] == 'Keep')
        
        weightVar = 'LongitudinalWeightHH_' + self.eyStr
                        
        results = pd.DataFrame(wAgg(self.dta.loc[dataMask], aggregationDict = aggDictionary, varForWeights= (weightVar))).transpose()
        results['Source'] = 'All_' + self.eyStr

        # results.to_csv(os.path.join(self.baseDir, self.outputSubDir, 'AppendixTable2_Demographics_' + self.timespan +'.csv'))
        results.to_excel(tempWriter, 'ATb2_Demographics')

        tempWriter.book.close()


    def executeForTimespan_Longitudinal(self, startYear, endYear, toYear):
        self.clearData()
        self.setPeriod(startYear, endYear, toYear)
        self.readLongitudinalData()
        self.checkQualityOfInputData_Longitudinal()
        self.checkQualityOfActiveSavingsVars_Longitudinal()
        self.calcDescriptivesForTimePeriod()


    def doIt(self, useCleanedDataOnly = True):
        self.useCleanedDataOnly = useCleanedDataOnly
        toYear = 2019
        # self.yearsWealthDataCollected = [1989, 1994]

        # Longitudinal Descriptives
        startYear = self.yearsWealthDataCollected[0]
        for endYear in self.yearsWealthDataCollected[1:].copy():            
            self.executeForTimespan_Longitudinal(startYear, endYear, toYear)
            # Get ready for next year
            startYear = endYear


''' Allow execution from command line, etc'''
if __name__ == "__main__":
    describer = LongitudinalDescriber(baseDir='C:/dev/sensitive_data/InvestorSuccess/Inequality',
        inputSubDir='inequalityOutput',
        inputBaseName="WithSavings_",
        outputBaseName="WithSavings_",
        outputSubDir='inequalityOutput/descriptives',
        includeChangeAnalysis=True
    )

    describer.clearData()
    describer.setPeriod(2015, 2017, 2017)
    describer.readLongitudinalData()
    # describer.checkQualityOfInputData_Longitudinal()
    describer.checkQualityOfActiveSavingsVars_Longitudinal()

    #    describer.doIt()
