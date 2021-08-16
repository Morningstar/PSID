import os
from Survey.SurveyFunctions import *
import MStarReport.InequalityAnalysisBase as InequalityAnalysisBase
import re
from Survey.SurveyDataSummarizer import SurveyDataSummarizer

class SWAnalysisLongTerm(InequalityAnalysisBase.InequalityAnalysisBase):
    
    def __init__(self, baseDir, inputSubDir, inputBaseName,outputBaseName, outputSubDir):
        super().__init__(baseDir, inputSubDir, inputBaseName,outputBaseName, outputSubDir)

    def addWealthOverTime(self):

        ###
        # Plan out the new fields we need
        # and create lots of empty columns for holding stuff
        ####
        twoPeriodTotalFields = ['Total_NetActiveSavings', 'Total_GrossSavings',
                                'Total_OpenCloseTransfers','Total_CapitalGains',
                                'largeGift_All_AmountHH', 'SmallGift_All_AmountHH',
                                'netAssetMove']
        fpTotalFields = ["FP_" + field + "_" + self.inflatedTimespan for field in twoPeriodTotalFields]

        assetTypes = ['House', 'OtherRealEstate', 'Business', 'BrokerageStocks', 'CheckingAndSavings', 'Vehicle',
         'OtherAssets', 'AllOtherDebts', 'PrivateRetirePlan', 'EmployerRetirePlan']
        assetCharacteristics = ['CapitalGains', 'OpenCloseTransfers', 'Savings', 'TotalChangeInWealth']
        fpAssetFields = ["FP_" + assetType + "_" + assetCharacteristic + "_" + self.inflatedTimespan for assetType in assetTypes for assetCharacteristic in assetCharacteristics]

        # create the new columns, fillin in zero for all
        withNewColumns = self.dta.columns.tolist() + fpTotalFields + fpAssetFields
        self.dta.reset_index(inplace=True)
        self.dta = self.dta.reindex(columns=withNewColumns, fill_value=0)

        for i in range(0, len(self.yearsInPeriodWithWealthData)-1, 1): # not inclusive of final val, intentionally
            startSlice = self.yearsInPeriodWithWealthData[i]
            endSlice = self.yearsInPeriodWithWealthData[i+1]
            inflatedTimespan = str(startSlice) + "_" + str(endSlice) + "_as_" + self.tyStr

            for field in twoPeriodTotalFields:
                self.dta["FP_" + field + "_" + self.inflatedTimespan] = self.dta["FP_" + field + "_" + self.inflatedTimespan].add(self.dta[field + "_" + inflatedTimespan], fill_value=0)

            for assetType in assetTypes:
                for assetCharacteristic in assetCharacteristics:
                    self.dta["FP_" + assetType + "_" + assetCharacteristic + "_" + self.inflatedTimespan] = self.dta["FP_" + assetType + "_" + assetCharacteristic + "_" + self.inflatedTimespan].add(
                        self.dta[assetType + "_" + assetCharacteristic + "_" + inflatedTimespan], fill_value= 0)

        incomeStartField = "inflatedPreTaxIncome_"+ self.inflatedStart
        incomeEndField = "inflatedPreTaxIncome_"+ self.inflatedEnd
        self.dta['incomeQuintile_PreTaxReal_' + self.inflatedStart] = wQCut(self.dta, incomeStartField, 'LongitudinalWeightHH_' + self.syStr, 5)
        # self.dta['incomeQuintile_PreTaxReal_' + self.inflatedEnd] = wQCut(self.dta, incomeEndField, 'LongitudinalWeightHH_' + self.eyStr, 5)

        self.dta["race3R_"+ self.syStr] = self.dta["raceR_" + self.syStr].replace({'Asian':'Other', 'NativeAmerican':'Other', 'Pacific':'Other', 'Unknown':'Other'}, inplace=False)
        # self.dta["race3R_"+ self.eyStr] = self.dta["raceR_" + self.eyStr].replace({'Asian':'Other', 'NativeAmerican':'Other', 'Pacific':'Other', 'Unknown':'Other'}, inplace=False)


    def calcWindow(self, startYear, endYear, toYear):
        yearList = list(range(startYear, endYear +1))
        self.yearsInPeriodWithWealthData = [value for value in yearList if value in self.yearsWealthDataCollected.copy()]
        startPeriod = self.yearsInPeriodWithWealthData[0]
        endPeriod = self.yearsInPeriodWithWealthData[-1]
        super().setPeriod(startPeriod, endPeriod, toYear)

    def combineData(self):

        combinedDta = None

        for i in range(0, len(self.yearsInPeriodWithWealthData)-1, 1): # not inclusive of final val, intentionally
            startSlice = self.yearsInPeriodWithWealthData[i]
            endSlice = self.yearsInPeriodWithWealthData[i+1]

            syStr = str(startSlice)
            eyStr = str(endSlice)
            timespan = syStr + "_" + eyStr
            inflatedTimespan = syStr + "_" + eyStr + "_as_" + self.tyStr

            dta = pd.read_csv(os.path.join(self.baseDir, self.inputSubDir, self.inputBaseName + 'TwoPeriod_' + inflatedTimespan +'.csv'))

            # Do our own custom filtering
            # We need ONLY people who are the same head over time
            # are not NOT filtering out "income too low", "head too old" or "head too young" for this analysis.
            dta = dta[(~dta["cleaningStatus_" + timespan].isin(["Not same Head", "Not In Both Waves"])) &
                    (dta["cleaningStatus_" + syStr] == "Keep") &
                    (dta["cleaningStatus_" + eyStr] == "Keep")
                    ]

            if combinedDta is None:
                combinedDta = dta
            else:
                # Remove some fields that are complete duplicated
                dta.drop(columns=["countryBornI_1997", "countryBornI_1999",  "livedInUSIn68I_1997","livedInUSIn68I_1999", "stateBornI_1997", "stateBornI_1999",
                                  "constantFamilyId", "constantIndividualID"], inplace=True)


                mergeField = "familyInterviewId_" + str(startSlice)

                r = re.compile(".*_" + syStr + "$")
                startYearColsToDrop = list(filter(r.match, list(dta.columns))) # Read Note below
                startYearColsToDrop = [theCol for theCol in startYearColsToDrop if theCol != mergeField]
                dta.drop(columns=startYearColsToDrop, inplace=True)

                combinedDta = pd.merge(left=combinedDta, right=dta, left_on=mergeField, right_on=mergeField, how="inner")

        self.dta = combinedDta


    def saveWealthData(self):
        self.dta.to_csv(os.path.join(self.baseDir, self.outputSubDir, self.outputBaseName + "FP_" + self.inflatedTimespan + ".csv"), index=False)


    def addPercentFields(self):

        totalFields = ['Total_NetActiveSavings', 'Total_GrossSavings',
                                'Total_OpenCloseTransfers','Total_CapitalGains',
                                'largeGift_All_AmountHH', 'SmallGift_All_AmountHH',
                                'netAssetMove']


        fpTotalFields = ["FP_" + field + "_" + self.inflatedTimespan for field in totalFields]

        startWealthField = "inflatedNetWorthWithHomeAnd401k_AfterBalanceFillin_" + self.inflatedStart
        finalWealthField = "inflatedNetWorthWithHomeAnd401k_AfterBalanceFillin_" + self.inflatedEnd
        self.dta["ChangeInRealNetWorth_" + self.inflatedTimespan] = self.dta[finalWealthField].fillna(0) - self.dta[startWealthField].fillna(0)


        for theField in totalFields:
            totalField = "FP_" + theField + "_" + self.inflatedTimespan
            totalAsPercentOfWealthField = "FP_PctEndWth_" + theField + "_" + self.inflatedTimespan
            totalAsPercentOfChangeField = "FP_PctChangeWth_" + theField + "_" + self.inflatedTimespan

            # What part of FINAL wealth comes from each source?
            # For % of ending wealth, remove all /0s = since there is no ending wealth, the data just isn't relevant
            self.dta[totalAsPercentOfWealthField] = self.dta[totalField].div(self.dta[finalWealthField]).replace([np.inf, -np.inf], None)

            # What part of CHANGE in wealth comes from each source?
            # For % of change of wealth, remove all /0s = since there is no change in wealth, the data just isn't relevant
            self.dta[totalAsPercentOfChangeField] = self.dta[totalField].div(self.dta["ChangeInRealNetWorth_" + self.inflatedTimespan]).replace([np.inf, -np.inf], None)

        # What part of FINAL Wealth is just inflated initial wealth?
        self.dta['FP_PctEndWth_StartingWealth_' + self.inflatedTimespan] = self.dta[startWealthField].div(self.dta[finalWealthField]).replace([np.inf, -np.inf], None)

    def calcAggregateResults(self):

        totalFields = ['Total_NetActiveSavings', 'Total_GrossSavings', 'Total_OpenCloseTransfers','Total_CapitalGains',
                                'largeGift_All_AmountHH', 'SmallGift_All_AmountHH', 'netAssetMove']

        fpTotalFields = ["FP_" + field + "_" + self.inflatedTimespan for field in totalFields]
        fpPercentOfWealthFields = ["FP_PctEndWth_" + field + "_" + self.inflatedTimespan for field in totalFields]
        fpPercentOfChangeFields = ["FP_PctChangeWth_" + field + "_" + self.inflatedTimespan for field in totalFields]

        incomeStartField = 'incomeQuintile_PreTaxReal_'+ self.inflatedStart
        # incomeEndField = 'incomeQuintile_PreTaxReal_'+ self.inflatedEnd
        weightStartField = "LongitudinalWeightHH_"+ self.syStr
        weightEndField = "LongitudinalWeightHH_"+ self.eyStr
        prcntWealthField = 'FP_PctEndWth_StartingWealth_' + self.inflatedTimespan
        startWealthField = "inflatedNetWorthWithHomeAnd401k_AfterBalanceFillin_" + self.inflatedStart
        finalWealthField = "inflatedNetWorthWithHomeAnd401k_AfterBalanceFillin_" + self.inflatedEnd

        otherVarsToKeep = [weightStartField, weightEndField, "race3R_" + self.syStr,
                           incomeStartField, prcntWealthField, startWealthField, finalWealthField ] # "race3R_" + self.eyStr, , incomeEndField

        allVarsToKeep = fpTotalFields + fpPercentOfWealthFields + fpPercentOfChangeFields + otherVarsToKeep

        # This can take a while to process; so trim down to only the variables we need
        tmp = self.dta[allVarsToKeep].copy()
        tmp["ChangeInRealNetWorth_" + self.inflatedTimespan] = tmp[finalWealthField].fillna(0) - tmp[startWealthField].fillna(0)

        # Create aggreation fields
        sds = SurveyDataSummarizer(tmp, weightStartField,
                                   fieldMetaData = None,
                                   fieldsToSummarize = None,
                                   fieldsToCrossTab = ["race3R_" + self.syStr, incomeStartField])

        sds.doIt(os.path.join(self.baseDir, self.outputSubDir, 'SummaryReport_FullPeriod_' + self.inflatedTimespan +'.xlsx'))


        # SDS gives us a nice page-by-page detailed summary.
        # We also just want a simple table for use in the paper. Let's do that here.
        aggDictionary= {}
        for theField in totalFields:
            totalField = "FP_" + theField + "_" + self.inflatedTimespan
            totalAsPercentOfWealthField = "FP_PctEndWth_" + theField + "_" + self.inflatedTimespan
            totalAsPercentOfChangeField = "FP_PctChangeWth_" + theField + "_" + self.inflatedTimespan

            # Calc Median for each total field
            aggDictionary[theField + "_median"] = (totalField, 'median')
            aggDictionary["PctEndWth_" + theField + "_median"] = (totalAsPercentOfWealthField, 'median')
            aggDictionary["PctChangeWth_" + theField + "_median"] = (totalAsPercentOfChangeField, 'median')

            aggDictionary["PopTotalNoFilter_" + theField] = (totalField, 'sum')

        aggDictionary['PopTotalNoFilter_StartingWealth'] = (startWealthField, 'sum')
        aggDictionary['PopTotalNoFilter_EndingWealth'] = (finalWealthField, 'sum')
        aggDictionary['PopTotalNoFilter_ChangeInWealth'] = ("ChangeInRealNetWorth_" + self.inflatedTimespan, 'sum')
        aggDictionary["PctEndWth_StartingWealth"  "_median"] = ("FP_PctEndWth_StartingWealth_" + self.inflatedTimespan, 'median')

        results = pd.DataFrame(wAgg(tmp, aggregationDict = aggDictionary, varForWeights= (weightStartField))).transpose()
        results['Source'] = 'All_' + self.eyStr

        resultsByRace = wGroupByAgg(tmp, ['race3R_' + self.syStr], aggregationDict = aggDictionary, varForWeights = (weightStartField)).reset_index()
        resultsByRace['Source'] = 'Race3_' + self.eyStr

        resultsByIncomeQ = wGroupByAgg(tmp, ['incomeQuintile_PreTaxReal_' + self.inflatedStart], aggregationDict = aggDictionary, varForWeights = (weightStartField)).reset_index()
        resultsByIncomeQ['Source' ] ='IncomeQuintile' + self.inflatedStart

        results = pd.concat([results, resultsByRace, resultsByIncomeQ], ignore_index=True, sort=False)

        results['StartYear'] = self.startYear
        results['EndYear'] = self.endYear
        results['InflatedToYear'] = self.toYear

        results.rename(columns={'race3R_' + self.syStr: 'race3R',
                                'incomeQuintile_PreTaxReal_' + self.syStr + '_as_' + self.tyStr: 'incomeQuintile_PreTaxReal',
                                }, inplace=True)

        # Calculate Mean Values
        for theField in totalFields:
            total_SumAcrossPop_Field = "PopTotalNoFilter_" + theField
            results['PrctEndWth_' + theField + '_AvgAsSums'] = results[total_SumAcrossPop_Field] / (results.PopTotalNoFilter_EndingWealth)
            results['PctChangeWth_' + theField + '_AvgAsSums'] = results[total_SumAcrossPop_Field] / (results.PopTotalNoFilter_ChangeInWealth)
        results['PrctEndWth_StartingWealth_AvgAsSums'] = results.PopTotalNoFilter_StartingWealth / (results.PopTotalNoFilter_EndingWealth)

        results = InequalityAnalysisBase.selectiveReorder(results, ['Source', 'race3R', 'incomeQuintile_PreTaxReal'],
                                                          alphabetizeTheOthers = True)


        results.to_csv(os.path.join(self.baseDir, self.outputSubDir, 'Agg_FullPeriod_' + self.inflatedTimespan +'.csv'))

    def runAggAnalysisOnly(self, startYear, endYear, toYear):
        self.calcWindow(startYear, endYear, toYear)

        self.dta = pd.read_csv(os.path.join(self.baseDir, self.outputSubDir, self.outputBaseName + "FP_" + self.inflatedTimespan + ".csv"))
        self.calcAggregateResults()

    def doIt(self, startYear, endYear, toYear):
        self.calcWindow(startYear, endYear, toYear)
        self.combineData()
        self.addWealthOverTime()
        self.addPercentFields()
        self.saveWealthData()

        self.calcAggregateResults()

''' Allow execution from command line, etc'''
if __name__ == "__main__":

    analyzer = SWAnalysisLongTerm(
        baseDir = 'C:/dev/sensitive_data/InvestorSuccess/Inequality',
        inputSubDir = 'inequalityOutput_enrichedPop',
        inputBaseName = 'WithSavings_',
        outputSubDir = 'inequalityOutput_enrichedPop/analyses',
        outputBaseName = 'wealthChangeAcrossTime'
    )

    # analyzer.doIt(1994, 2007, 2019)
    # analyzer.doIt(2007, 2019, 2019)
    # analyzer.doIt(2009, 2019, 2019)
    # analyzer.doIt(1999, 2019, 2019)
    analyzer.doIt(1984, 2019, 2019)

