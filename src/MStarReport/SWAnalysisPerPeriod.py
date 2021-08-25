import matplotlib.pyplot as plt
import seaborn as sns
import os
from Survey.ExcelOutputWrapper import ExcelOutputWrapper
from Survey.SurveyFunctions import *
import MStarReport.InequalityAnalysisBase as InequalityAnalysisBase
import MStarReport.AggregatePopulationAnalyzer as apa
from io import BytesIO

class SWAnalysisPerPeriod(InequalityAnalysisBase.InequalityAnalysisBase):
    
    def __init__(self, baseDir, inputSubDir, inputBaseName,outputBaseName, outputSubDir, useOriginalSampleOnly):
        super().__init__(baseDir, inputSubDir, inputBaseName,outputBaseName, outputSubDir)
        self.useOriginalSampleOnly = useOriginalSampleOnly


    def calcResultsAcrossTime(self, years, toYear, calcRegressions=True):

        startYear = years[0]

        combinedAssetResults = None
        combinedAggResults = None
        combinedWealthChangeResults = None
        combinedRegressionResults = None
        
        for endYear in years[1:].copy():
            # Get our core results: change in wealth over time
            populationAnalyzer = apa.AggregatePopulationAnalyzer(self.baseDir, self.inputSubDir, self.inputBaseName, self.outputBaseName, self.outputSubDir,
                self.useOriginalSampleOnly)
            populationAnalyzer.useCleanedDataOnly = self.useCleanedDataOnly

            populationAnalyzer.clearData()
            populationAnalyzer.setPeriod(startYear, endYear, toYear)
            populationAnalyzer.readLongitudinalData()

            resultsTuple = populationAnalyzer.executeForTimespan(saveToFile=False,includeRegressions=calcRegressions)

            assetResults = resultsTuple[0]
            if combinedAssetResults is None:
                combinedAssetResults = assetResults
            else:
                combinedAssetResults = pd.concat([combinedAssetResults, assetResults], ignore_index=True)

            if combinedAggResults is None:
                combinedAggResults = resultsTuple[1]
            else:
                combinedAggResults = pd.concat([combinedAggResults, resultsTuple[1]], ignore_index=True)

            if combinedWealthChangeResults is None:
                combinedWealthChangeResults = resultsTuple[2]
            else:
                combinedWealthChangeResults = pd.concat([combinedWealthChangeResults, resultsTuple[2]], ignore_index=True)
                        
            if (combinedRegressionResults is None) and (len(resultsTuple) >= 3) :
                combinedRegressionResults = resultsTuple[3]
            else:
                combinedRegressionResults = pd.concat([combinedRegressionResults, resultsTuple[3]], ignore_index=True)

            # Get ready for next year
            startYear = endYear

        if not os.path.exists(os.path.join(self.baseDir, self.outputSubDir)):
            os.makedirs(os.path.join(self.baseDir, self.outputSubDir))

        combinedAssetResults = InequalityAnalysisBase.selectiveReorder(combinedAssetResults, ['StartYear', 'EndYear', 'InflatedToYear', 'Source'])
        combinedAssetResults.to_csv(os.path.join(self.baseDir, self.outputSubDir, "SW_Asset_Results_" + str(years[0]) + '_to_' + str(years[-1]) +  ".csv"), index=False)

        combinedAggResults = InequalityAnalysisBase.selectiveReorder(combinedAggResults, ['StartYear', 'EndYear', 'InflatedToYear', 'Source', 'active_median', 'activeSavings_AvgAsSums'])
        combinedAggResults.to_csv(os.path.join(self.baseDir, self.outputSubDir, "SW_Aggregation_Results_" + str(years[0]) + '_to_' + str(years[-1]) +  ".csv"), index=False)

        combinedWealthChangeResults = InequalityAnalysisBase.selectiveReorder(combinedWealthChangeResults, ['StartYear', 'EndYear', 'InflatedToYear', 'Source', 'wealth_appreciation_rate_median', 'wealth_appreciation_rate_AvgsAsSums'])
        combinedWealthChangeResults.to_csv(os.path.join(self.baseDir, self.outputSubDir, "SW_WealthChange_Results_" + str(years[0]) + '_to_' + str(years[-1]) +  ".csv"), index=False)

        if combinedRegressionResults is not None:
            combinedRegressionResults = InequalityAnalysisBase.selectiveReorder(combinedRegressionResults, ['StartYear', 'EndYear', 'InflatedToYear', 'Source', 'var', 'coeff'])
            combinedRegressionResults.to_csv(os.path.join(self.baseDir, self.outputSubDir, "SW_Regression_Results_" + str(years[0]) + '_to_' + str(years[-1]) +  ".csv"), index=False)
        

    def generateStatsForSWReport(self, years, toYear):

        #####
        ## Gather the input data we need
        #####

        # Assets - median and rates over time
        combinedAssetResults = pd.read_csv(os.path.join(self.baseDir, self.outputSubDir, "SW_Asset_Results_" + str(years[0]) + '_to_' + str(years[-1]) +  ".csv"))
        # Aggregates - median, mean over time
        combinedAggResults = pd.read_csv(os.path.join(self.baseDir, self.outputSubDir, "SW_Aggregation_Results_" + str(years[0]) + '_to_' + str(years[-1]) +  ".csv"))
        # Aggregates - median, mean over time
        combinedWealthChangeResults = pd.read_csv(os.path.join(self.baseDir, self.outputSubDir, "SW_WealthChange_Results_" + str(years[0]) + '_to_' + str(years[-1]) +  ".csv"))
        # Regressions to explain savings rates
        combinedRegressionResults = pd.read_csv(os.path.join(self.baseDir, self.outputSubDir, "SW_Regression_Results_" + str(years[0]) + '_to_' + str(years[-1]) +  ".csv"))

        #####
        ## Setup excel file for output
        #####

        excelWrapper = ExcelOutputWrapper()
        excelWrapper.startFile(os.path.join(self.baseDir, self.outputSubDir, 'FiguresForPaper_' + str(years[0]) + '_to_' + str(years[-1]) + '.xlsx'))

        #####
        ## Start making the data tables & graphics!
        #####
        # Appendix Table 1: Basic Summary Stats
        dta = combinedAggResults.loc[(combinedAggResults.Source.str.startswith("All_")),
                                 ("StartYear", "EndYear", "familyInterview_N", "familyInterview_TotalWeights",
                                  "filledIn_real_NetWorthWithHomeAnd401k_median", "real_pre_tax_income_median", "real_after_tax_income_median")].copy()
        dta.rename(columns={"familyInterview_N":"Num Households",
                            "familyInterview_TotalWeights": "Num Households Represented",
                            "filledIn_real_NetWorthWithHomeAnd401k_median": "Median Net Worth, Real",
                            "real_pre_tax_income_median": "Median Pre Tax Income, Real",
                            "real_after_tax_income_median": "Median After Tax Income, Real"
                            }, inplace=True)

        # dta.to_csv(os.path.join(self.baseDir, self.outputSubDir, 'Table1_SummaryStats_' + str(years[0]) + '_to_' + str(years[-1]) + '.csv'))
        excelWrapper.addWorksheet("A1_SummaryStats")
        excelWrapper.addTable(dta=dta,  tableName="Appendix Table 1: Summary Statistics",
                              description=None,
                              columnFormats={'Num Households':excelWrapper.wholeNumberFormat,
                                             'Num Households Represented':excelWrapper.numberFormat,
                                             'Median Net Worth, Real':excelWrapper.numberFormat,
                                             'Median Pre Tax Income, Real':excelWrapper.numberFormat,
                                             'Median After Tax Income, Real':excelWrapper.numberFormat,
                                             },
                              direction="down")

        # Figure 1: Active Savings Rates over time
        dta = combinedAggResults[(combinedAggResults.Source.str.startswith("All_"))][["EndYear", "active_median"]]
        sns_plot = sns.pointplot(x="EndYear", y="active_median", data=dta, ci=None)
        sns_plot.set(xlabel='Year', ylabel='Active Savings Rate (Median)')
        # sns_plot = sns.lineplot(x="EndYear", y="activeSavings_AvgAsSums", data=dta)
        # sns_plot.set(xlabel='Year', ylabel='Active Savings Rate (Mean)')
        figByteFile = BytesIO()
        sns_plot.get_figure().savefig(figByteFile) # os.path.join(self.baseDir, self.outputSubDir, 'Fig1_SavingsRates_Median_All_' + str(years[0]) + '_to_' + str(years[-1]) + '.png'))
        plt.clf()
        excelWrapper.addWorksheet("F1_SR_Med_All")
        excelWrapper.addTable(dta=dta,  tableName="Figure 1: Median Savings Rates Across All Participants", description=None,
                              columnFormats={'EndYear':excelWrapper.wholeNumberFormat,
                                             'active_median':excelWrapper.numberFormat}, direction="down")
        excelWrapper.addImage(imageData=figByteFile, imageName = "Median Savings Rates (All Participants)", direction="down")


        # Figure 2: Active Savings Rates over time by Income (Quintile)
        dta = combinedAggResults[~(combinedAggResults.incomeApproxQuintile_PreTaxReal.isna())][['EndYear', 'active_median', "incomeApproxQuintile_PreTaxReal"]]
        sns_plot = sns.lineplot(x="EndYear", y="active_median", hue="incomeApproxQuintile_PreTaxReal", data=dta, ci=None, legend='full') #, label="incomeQuintile_PreTaxReal")
        sns_plot.set(xlabel='Year', ylabel='Active Savings Rate (Median)')
        figByteFile = BytesIO()
        sns_plot.get_figure().savefig(figByteFile) # os.path.join(self.baseDir, self.outputSubDir, 'Fig2_SavingsRates_Median_ByIncomeQuintile_' + str(years[0]) + '_to_' + str(years[-1]) + '.png'))
        plt.clf()
        excelWrapper.addWorksheet("F2_SR_Med_ByIncomeApproxQuintile")
        # Convert to wide format -- long data doesn't work well in Chartbuilder
        dta = dta.pivot_table(index=["EndYear"], columns="incomeApproxQuintile_PreTaxReal", values="active_median")
        excelWrapper.addTable(dta=dta,  tableName="Figure 2: Median Savings Rates, by Approx. Income Quintile", description=None,
                              columnFormats={'incomeApproxQuintile_PreTaxReal':excelWrapper.wholeNumberFormat,
                                             'EndYear':excelWrapper.wholeNumberFormat,
                                             'active_median':excelWrapper.numberFormat}, direction="down")
        excelWrapper.addImage(imageData=figByteFile, imageName = "Median Savings Rates, by Approx. Income Quintile", direction="down")

        # In Text Stat: Regression 2019 Causes of Savings Rates
        tmpTable2 = combinedRegressionResults[(combinedRegressionResults.EndYear == 2019) & (combinedRegressionResults.Source == 'Race Quantile')]
        # tmpTable2.to_csv(os.path.join(self.baseDir, self.outputSubDir, 'Stat_SavingsRates_Regression_Median_2019.csv'))
        excelWrapper.addWorksheet("S1_SR_MedReg")
        excelWrapper.addTable(dta=tmpTable2,  tableName="Inline Stat: Median Regression on Savings Rates, 2019", description=None,
                             columnFormats={'ALL': excelWrapper.numberFormat}, direction="down")

        # Table 2: Regression 2019 Causes of Savings Rates with Race
        tmpTable2 = combinedRegressionResults[(combinedRegressionResults.EndYear == 2019) & (combinedRegressionResults.Source == 'Broad wRaceLogIncome QuantileReg')]
        # tmpTable2.to_csv(os.path.join(self.baseDir, self.outputSubDir, 'Table2_SavingsRates_Regression_WithRace_Median_2019.csv'))
        excelWrapper.addWorksheet("T2_SR_MedReg_WithRace")
        excelWrapper.addTable(dta=tmpTable2,  tableName="Table 2: Median Regression on Savings Rates, with Race 2019", description=None,
                             columnFormats={'ALL': excelWrapper.numberFormat}, direction="down")

        # Table 3: Regression Coeff Acrss Time, Causes of Savings Rates with Race
        tmpTable3 = combinedRegressionResults[(combinedRegressionResults['var'].isin(['Black','Hispanic'])) & (combinedRegressionResults.Source == 'Broad wRaceLogIncome QuantileReg')]
        # tmpTable3.to_csv(os.path.join(self.baseDir, self.outputSubDir, 'Table3_SavingsRates_Regression_WithRace_Median_OverTime.csv'))
        excelWrapper.addWorksheet("T3_SR_MedReg_AcrossTime")
        excelWrapper.addTable(dta=tmpTable3,  tableName="Table 3: Median Regression on Savings Rates, with Race, Across Time", description=None,
                             columnFormats={'ALL': excelWrapper.numberFormat}, direction="down")

        # Figure 3: Active Savings Rates over time by Race
        dta = combinedAggResults[(combinedAggResults.raceR.isin(["Black", "White", "Hispanic"]))][["EndYear", "StartYear", "active_median", "raceR", "familyInterview_N"]]
        if (~self.useOriginalSampleOnly):
            dta.loc[(dta.raceR == "Hispanic") & (dta.StartYear < 1999), "active_median"] = None
        sns_plot = sns.pointplot(x="EndYear", y="active_median", hue="raceR", data=dta, ci=None)
        sns_plot.set(xlabel='Year', ylabel='Active Savings Rate (Median)')
        figByteFile = BytesIO()
        sns_plot.get_figure().savefig(figByteFile) # os.path.join(self.baseDir, self.outputSubDir, 'Fig3_SavingsRates_Median_ByRace_' + str(years[0]) + '_to_' + str(years[-1]) + '.png'))
        plt.clf()
        excelWrapper.addWorksheet("F3_SavingsRates_Median_ByRace")

        # Convert to wide format -- long data doesn't work well in Chartbuilder
        dta = dta.pivot_table(index=["EndYear"], columns="raceR", values="active_median")
        excelWrapper.addTable(dta=dta,  tableName="Figure 3: Median Savings Rates, by Race", description=None,
                              columnFormats={'raceR':excelWrapper.noFormat,
                                             'EndYear':excelWrapper.wholeNumberFormat,
                                             'active_median':excelWrapper.numberFormat}, direction="down")
        excelWrapper.addImage(imageData=figByteFile, imageName = "Median Savings Rates, by Race", direction="down")

        # Figure 3A: Active Savings Rates over time by Race, Separating Hispanic Americans into 3 Waves
        dta = combinedAggResults[(combinedAggResults.raceAndWave.isin(
            [ "White_OriginalSample",
             "Black_OriginalSample",
             "Hispanic_OriginalSample",
             "Hispanic_1997-99 Immigrant",
              "Black_1997-99 Immigrant",
             "White_1997-99 Immigrant",
             "Hispanic_2017-19 Immigrant",
              "Black_2017-19 Immigrant",
              "White_2017-19 Immigrant",
             ]))][["EndYear", "StartYear", "active_median", "raceAndWave", "familyInterview_N"]]
        sns_plot = sns.pointplot(x="EndYear", y="active_median", hue="raceAndWave", data=dta, ci=None)
        sns_plot.set(xlabel='Year', ylabel='Active Savings Rate (Median)')
        figByteFile = BytesIO()
        sns_plot.get_figure().savefig(figByteFile) # os.path.join(self.baseDir, self.outputSubDir, 'Fig3_SavingsRates_Median_ByRace_' + str(years[0]) + '_to_' + str(years[-1]) + '.png'))
        plt.clf()
        excelWrapper.addWorksheet("F3A_SavingsRates_Median_ByRaceWave")

        # Convert to wide format -- long data doesn't work well in Chartbuilder
        dta = dta.pivot_table(index=["EndYear"], columns="raceAndWave", values="active_median")
        excelWrapper.addTable(dta=dta,  tableName="Figure 3A: Median Savings Rates, by Race and Immigration Wave", description=None,
                              columnFormats={'raceAndWave':excelWrapper.noFormat,
                                             'EndYear':excelWrapper.numberFormat,
                                             'active_median':excelWrapper.numberFormat}, direction="down")
        excelWrapper.addImage(imageData=figByteFile, imageName = "Median Savings Rates, by Race and Wage", direction="down")


        # Figure 4: Median Savings Rates over time by Income
        dta = combinedAggResults[~(combinedAggResults.incomeApproxQuintile_PreTaxReal.isna())][["EndYear", "active_median", "incomeApproxQuintile_PreTaxReal"]]
        sns_plot = sns.lineplot(x="EndYear", y="active_median", hue="incomeApproxQuintile_PreTaxReal", data=dta, ci=None, legend='full')
        sns_plot.set(xlabel='Year', ylabel='Active Savings Rate (Median)')
        figByteFile = BytesIO()
        sns_plot.get_figure().savefig(figByteFile) # os.path.join(self.baseDir, self.outputSubDir, 'F4_Wealth_Median_ByIncome_' + str(years[0]) + '_to_' + str(years[-1]) + '.png'))
        plt.clf()
        excelWrapper.addWorksheet("F4_SRM_ByIncome")
        # Convert to wide format -- long data doesn't work well in Chartbuilder
        dta = dta.pivot_table(index=["EndYear"], columns="incomeApproxQuintile_PreTaxReal", values="active_median")
        excelWrapper.addTable(dta=dta,  tableName="Figure 4: Median Savings Rates, by Income", description=None,
                              columnFormats={'active_median':excelWrapper.wholeNumberFormat,
                                             'EndYear':excelWrapper.wholeNumberFormat,
                                             'incomeApproxQuintile_PreTaxReal':excelWrapper.numberFormat}, direction="down")
        excelWrapper.addImage(imageData=figByteFile, imageName = "Median Savings Rates, by Income", direction="down")


        # Appendix Table & Note in Report Text: Active Savings Rates over Wealth Quintles
        dta = combinedAggResults[~(combinedAggResults.wealthQuintile_Real.isna())]
        sns_plot = sns.lineplot(x="EndYear", y="active_median", hue="wealthQuintile_Real", data=dta)
        sns_plot.set(xlabel='Year', ylabel='Active Savings Rate (Median)')
        figByteFile = BytesIO()
        sns_plot.get_figure().savefig(figByteFile) # os.path.join(self.baseDir, self.outputSubDir, 'Fig5_Wealth_Median_ByRace_' + str(years[0]) + '_to_' + str(years[-1]) + '.png'))
        plt.clf()
        excelWrapper.addWorksheet("TextNote_SRbyWealth_Median")
        # Convert to wide format -- long data doesn't work well in Chartbuilder
        dta = dta.pivot_table(index=["EndYear"], columns="wealthQuintile_Real", values="active_median")
        excelWrapper.addTable(dta=dta,  tableName="Appendix Table: Median Savings Rates, by Wealth", description=None,
                              columnFormats={'active_median':excelWrapper.numberFormat,
                                             'EndYear':excelWrapper.wholeNumberFormat,
                                             'wealthQuintile_Real':excelWrapper.wholeNumberFormat}, direction="down")
        excelWrapper.addImage(imageData=figByteFile, imageName = "Savings Rates, by Wealth", direction="down")



        # Table 5 Ownership of & % Wealth in Diferent Assets
        filter_col_Having = ['EndYear', 'raceR', 'Source'] + [col for col in combinedAssetResults.columns if (col.startswith('has'))]
        filter_col_Wealth_Median = ['EndYear', 'raceR', 'Source'] + [col for col in combinedAssetResults.columns if (col.startswith("EndValueCoded_PrcntOfWealth"))]
        filter_col_Wealth_AvgAsSums = ['EndYear', 'raceR', 'Source'] + [col for col in combinedAssetResults.columns if (col.endswith("_AvgAsSums"))]

        prcntHaving = combinedAssetResults.loc[(combinedAssetResults.EndYear==2019) &
                                 (combinedAssetResults.Source.isin(["Race_2019", "All_2019"])) &
                                 (combinedAssetResults.raceR.isna() | combinedAssetResults.raceR.isin(['Black','Hispanic','White'])), filter_col_Having].copy()
        prcntWealthMedian = combinedAssetResults.loc[(combinedAssetResults.EndYear==2019) &
                                 (combinedAssetResults.Source.isin(["Race_2019", "All_2019"])) &
                                 (combinedAssetResults.raceR.isna() | combinedAssetResults.raceR.isin(['Black','Hispanic','White'])), filter_col_Wealth_Median].copy()
        prcntWealthAvgAsSums = combinedAssetResults.loc[(combinedAssetResults.EndYear==2019) &
                                 (combinedAssetResults.Source.isin(["Race_2019", "All_2019"])) &
                                 (combinedAssetResults.raceR.isna() | combinedAssetResults.raceR.isin(['Black','Hispanic','White'])), filter_col_Wealth_AvgAsSums].copy()
        excelWrapper.addWorksheet("T5_AssetType_ByRace")
        # Convert to wide format -- long data doesn't work well in Chartbuilder
        prcntHaving = prcntHaving.T
        excelWrapper.addTable(dta=prcntHaving,  tableName="Table 5A: % Asset Ownership,  By Race", description=None, direction="down")

        prcntWealthMedian = prcntWealthMedian.T
        excelWrapper.addTable(dta=prcntWealthMedian,  tableName="Table 5B: Asset As Percent of Wealth, Median By Race", description=None, direction="down")

        prcntWealthAvgAsSums = prcntWealthAvgAsSums.T
        excelWrapper.addTable(dta=prcntWealthAvgAsSums,  tableName="Table 5C: Asset As Percent of Wealth, Mean (Avg as Sums) By Race", description=None, direction="down")

        # Table 6 Components of Wealth Accumulation Over Time
        filter_col_AccumRate = ['EndYear', 'Source'] + [col for col in combinedWealthChangeResults.columns if ((col == 'wealth_appreciation_rate_AvgsAsSums') | col.endswith('_rate_AvgAsSums'))]
        dta = combinedWealthChangeResults.loc[(combinedWealthChangeResults.Source.str.startswith("All_")),
                    filter_col_AccumRate].copy()
        excelWrapper.addWorksheet("T6_ComponentsOfWealthAccum")
        excelWrapper.addTable(dta=dta,  tableName="Table 6: Components  of Wealth Accumulation over time", description=None, direction="down")

        # Table A-5 Components of Wealth Accumulation, By Race
        filter_col_AccumRate = ['EndYear', 'raceR', 'Source'] + [col for col in combinedWealthChangeResults.columns if ((col == 'wealth_appreciation_rate_AvgsAsSums') | col.endswith('_rate_AvgAsSums'))]
        dta = combinedWealthChangeResults.loc[(combinedWealthChangeResults.Source.str.startswith("Race_")),
                    filter_col_AccumRate].copy()
        excelWrapper.addWorksheet("A5_ComponentsOfWealthAccum_ByRace")
        excelWrapper.addTable(dta=dta,  tableName="Appendix Table 5: Components  of Wealth Accumulation, By Race", description=None, direction="down")

        # Table A-6 Components of Wealth Accumulation, By Income
        filter_col_AccumRate = ['EndYear', 'incomeApproxQuintile_PreTaxReal', 'Source'] +  [col for col in combinedWealthChangeResults.columns if ((col == 'wealth_appreciation_rate_AvgsAsSums') | col.endswith('_rate_AvgAsSums'))]
        dta = combinedWealthChangeResults.loc[(combinedWealthChangeResults.Source.str.startswith("IncomeApproxQuintile_")), filter_col_AccumRate].copy()
        excelWrapper.addWorksheet("A6_ComponentsOfWealthAccum_ByIncome")
        excelWrapper.addTable(dta=dta,  tableName="Appendix Table 6: Components  of Wealth Accumulation, By Income", description=None, direction="down")

        # In Text Stat: MEAN (trimmed) Savings Rates and Income -> Mean Amount Saved
        combinedWealthChangeResults['duration'] =combinedWealthChangeResults.EndYear - combinedWealthChangeResults.StartYear
        filter_col_MeanSavings = ['EndYear', 'raceR', 'Source'] + ['activeSavings_AvgAsSums_Trimmed','annual_active_savings_mean', 'duration', 'filledin_real_networth_end_sum', 'filledin_real_networth_start_sum']
        dta = combinedWealthChangeResults.loc[(combinedWealthChangeResults.Source.str.startswith("Race_") | combinedWealthChangeResults.Source.str.startswith("All_")),
                                              filter_col_MeanSavings].copy()
        excelWrapper.addWorksheet("TextNote_MeanAmountSaved")
        excelWrapper.addTable(dta=dta,  tableName="TextNote Mean Income, Saving Rate and Amount Saved, for Thought Experiment", description=None, direction="down")

        '''
        # Figure 5: Median Wealth over time by Income
        dta = combinedAggResults[~(combinedAggResults.incomeApproxQuintile_PreTaxReal.isna())][["EndYear", "filledIn_real_NetWorthWithHomeAnd401k_median", "incomeApproxQuintile_PreTaxReal"]]
        sns_plot = sns.lineplot(x="EndYear", y="filledIn_real_NetWorthWithHomeAnd401k_median", hue="incomeApproxQuintile_PreTaxReal", data=dta, ci=None, legend='full')
        sns_plot.set(xlabel='Year', ylabel='Net Worth (Median)')
        figByteFile = BytesIO()
        sns_plot.get_figure().savefig(figByteFile) # os.path.join(self.baseDir, self.outputSubDir, 'F4_Wealth_Median_ByIncome_' + str(years[0]) + '_to_' + str(years[-1]) + '.png'))
        plt.clf()
        excelWrapper.addWorksheet("F5_Wealth_Median_ByIncome")
        # Convert to wide format -- long data doesn't work well in Chartbuilder
        dta = dta.pivot_table(index=["EndYear"], columns="incomeApproxQuintile_PreTaxReal", values="filledIn_real_NetWorthWithHomeAnd401k_median")
        excelWrapper.addTable(dta=dta,  tableName="Figure 5: Median Wealth, by Income", description=None,
                              columnFormats={'filledIn_real_NetWorthWithHomeAnd401k_median':excelWrapper.wholeNumberFormat,
                                             'EndYear':excelWrapper.wholeNumberFormat,
                                             'incomeApproxQuintile_PreTaxReal':excelWrapper.numberFormat}, direction="down")
        excelWrapper.addImage(imageData=figByteFile, imageName = "Median Wealth, by Income", direction="down")

        # Figure 6: Median Wealth over time by Race
        dta = combinedAggResults[(combinedAggResults.raceR.isin(["Black", "White", "Hispanic"]))][["EndYear", "filledIn_real_NetWorthWithHomeAnd401k_median", "raceR"]]
        sns_plot = sns.pointplot(x="EndYear", y="filledIn_real_NetWorthWithHomeAnd401k_median", hue="raceR", data=dta, ci=None)
        sns_plot.set(xlabel='Year', ylabel='Net Worth (Median)')
        figByteFile = BytesIO()
        sns_plot.get_figure().savefig(figByteFile) # os.path.join(self.baseDir, self.outputSubDir, 'Fig5_Wealth_Median_ByRace_' + str(years[0]) + '_to_' + str(years[-1]) + '.png'))
        plt.clf()
        excelWrapper.addWorksheet("Fig6_Wealth_Median_ByRace")
        # Convert to wide format -- long data doesn't work well in Chartbuilder
        dta = dta.pivot_table(index=["EndYear"], columns="raceR", values="filledIn_real_NetWorthWithHomeAnd401k_median")
        excelWrapper.addTable(dta=dta,  tableName="Figure 6: Median Wealth, by Race", description=None,
                              columnFormats={'raceR':excelWrapper.noFormat,
                                             'EndYear':excelWrapper.wholeNumberFormat,
                                             'filledIn_real_NetWorthWithHomeAnd401k_median':excelWrapper.wholeNumberFormat}, direction="down")
        excelWrapper.addImage(imageData=figByteFile, imageName = "Median Wealth, by Race", direction="down")


        # Figure NOT USED: Active Savings Rates (Mean) over time by Income  (Quintile)
        dta = combinedAggResults[~(combinedAggResults.incomeQuintile_PreTaxReal.isna())]
        sns_plot = sns.lineplot(x="EndYear", y="activeSavings_AvgAsSums", hue="incomeQuintile_PreTaxReal", data=dta, ci=None)
        sns_plot.set(xlabel='Year', ylabel='Active Savings Rate (Mean)')
        sns_plot.get_figure().savefig(os.path.join(self.baseDir, self.outputSubDir, 'SavingsRates_Means_ByIncomeQuintile_' + str(years[0]) + '_to_' + str(years[-1]) + '.png'))
        plt.clf()

        # Figure NOT USED: Active Savings Rates (Mean) over time by Income  (Decile)
        dta = combinedAggResults[~(combinedAggResults.incomeDecile_PreTaxReal.isna())]
        sns_plot = sns.lineplot(x="EndYear", y="activeSavings_AvgAsSums", hue="incomeDecile_PreTaxReal", data=dta)
        sns_plot.set(xlabel='Year', ylabel='Active Savings Rate (Mean)')
        sns_plot.get_figure().savefig(os.path.join(self.baseDir, self.outputSubDir, 'SavingsRates_Means_ByIncomeDecile_' + str(years[0]) + '_to_' + str(years[-1]) + '.png'))
        plt.clf()

        # NOT USED Graph: Active Savings Rates over Wealth Deciles
        dta = combinedAggResults[~(combinedAggResults.wealthDecile_Real.isna())]
        sns_plot = sns.lineplot(x="EndYear", y="activeSavings_AvgAsSums", hue="wealthDecile_Real", data=dta)
        sns_plot.set(xlabel='Year', ylabel='Active Savings Rate (Mean)')
        sns_plot.get_figure().savefig(os.path.join(self.baseDir, self.outputSubDir, 'SavingsRates_Means_ByWealthDecile_' + str(years[0]) + '_to_' + str(years[-1]) + '.png'))
        plt.clf()

        # Figure 6: Causes of Net Wealth Change over Time:
        # Active Savings, Capital Gains, Inheritance, Small Gifts & Support, Household Changes,
#        dta = combinedWealthChangeResults[~(combinedWealthChangeResults.incomeDecile_PreTaxReal.isna())]
        dta = combinedWealthChangeResults[(combinedWealthChangeResults.Source.str.startswith("All_"))]
        plt.stackplot(dta.EndYear,
                                dta.annual_active_savings_pcntwlth_median,
                                dta.annual_capital_gains_pcntwlth_median,
                                dta.annual_inheritance_pcntwlth_median,
                                dta.annual_smallgifts_pcntwlth_median,
                                dta.annual_movewealth_pcntwlth_median,
                                labels=['Savings','Capital Gains','Inheritance', 'Small Gifts', 'NetMove'])

        # plt.stackplot(x,y, labels=['A','B','C'])
        # plt.legend(loc='upper left')

        # plt.set(xlabel='Year', ylabel='Rate (Median)')
        plt.legend(loc='upper left')
        # plt.show()
        plt.savefig(os.path.join(self.baseDir, self.outputSubDir, 'F6_WealthChange_Median_' + str(years[0]) + '_to_' + str(years[-1]) + '.png'))
        plt.clf()
        '''




        excelWrapper.endFile()


    def doIt(self, useCleanedDataOnly = True):
        self.useCleanedDataOnly = useCleanedDataOnly
        toYear = 2019
        # self.yearsWealthDataCollected = [1984, 1989, 1994, 1999]
        # self.yearsWealthDataCollected = [2001, 2003]
        # self.yearsWealthDataCollected = [2017, 2019]
        
        self.calcResultsAcrossTime(self.yearsWealthDataCollected.copy(), toYear, calcRegressions=True)
        self.generateStatsForSWReport(self.yearsWealthDataCollected.copy(), toYear)

