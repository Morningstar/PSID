import os
from Survey.SurveyFunctions import *
import MStarReport.InequalityAnalysisBase as InequalityAnalysisBase
from Survey.RSurveyInterface import *
import Inflation.CPI_InflationReader as CPI_InflationReader

class AggregatePopulationAnalyzer(InequalityAnalysisBase.InequalityAnalysisBase):

    def __init__(self, baseDir, inputSubDir, inputBaseName, outputBaseName, outputSubDir, useOriginalSampleOnly):
        super().__init__(baseDir, inputSubDir,inputBaseName, outputBaseName, outputSubDir)
        self.useOriginalSampleOnly = useOriginalSampleOnly
        self.rsi = None

    def readLongitudinalData(self):
        super().readLongitudinalData()
        # Add extra processing here as needed

    # Note, this should be calculated on the filtered groups (after irrelevant pops are excluded)
    def createSegmentBins_Longitudinal(self):
        self.dta['incomeGroup_PreTaxReal_' + self.inflatedStart] = wQCut(dta = self.dta, varForQuantile='averageRealBeforeTaxIncome_AllYears_' + self.inflatedTimespan,
                                                                         varForWeights='LongitudinalWeightHH_' + self.eyStr, numQuantiles=4)
        self.dta['incomeGroup_PostTaxReal_' + self.inflatedStart] = wQCut(self.dta, 'averageRealAfterTaxIncome_AllYears_' + self.inflatedTimespan, 'LongitudinalWeightHH_' + self.eyStr, 4)

        self.dta['incomeQuintile_PreTaxReal_' + self.inflatedStart] = wQCut(self.dta, 'averageRealBeforeTaxIncome_AllYears_' + self.inflatedTimespan, 'LongitudinalWeightHH_' + self.eyStr, 5)
        # self.dta['incomeDecile_PreTaxReal_' + self.inflatedStart] = wQCut(self.dta, 'averageRealBeforeTaxIncome_AllYears_' + self.inflatedTimespan, 'LongitudinalWeightHH_' + self.eyStr, 10)

        self.dta['incomeApproxQuintile_PreTaxReal_' + self.inflatedStart] = \
            pd.cut(self.dta['averageRealBeforeTaxIncome_AllYears_' + self.inflatedTimespan],
                        bins=[0,40000,60000,85000, 120000,999999999],
                        right= False,
                        labels=['1k:40k','40k:60k',
                                '60k:85k', '85k:120k', '>120k'])

        self.dta['wealthQuintile_Real_' + self.inflatedStart] = wQCut(self.dta, 'inflatedNetWorthWithHomeAnd401k_AfterBalanceFillin_' + self.inflatedStart, 'LongitudinalWeightHH_' + self.eyStr, 5)
        # self.dta['wealthDecile_Real_' + self.inflatedStart] = wQCut(self.dta, 'inflatedNetWorthWithHomeAnd401k_' + self.inflatedStart, 'LongitudinalWeightHH_' + self.eyStr, 10)
        # self.dta['wealthDecile_Real_' + self.inflatedEnd] = wQCut(self.dta, 'inflatedNetWorthWithHomeAnd401k_' + self.inflatedEnd, 'LongitudinalWeightHH_' + self.eyStr, 10)


    def runSegmentedAggregations(self, tmpDta, aggDictionary):
        '''
        Helper function to run a supplied list of aggregations, segmented by race, age, income and wealth over the population
        Does so for the current year

        :param aggDictionary:
        :type aggDictionary:
        :return:
        :rtype:
        '''

        # Setup a simple cleaning mask. Not used in this version (used in stats)
        tmpDta['cleaningStatus_' + self.eyStr] = 'Keep'
        dataMask = (tmpDta['cleaningStatus_' + self.eyStr] == 'Keep')

        weightVar = 'LongitudinalWeightHH_' + self.eyStr

        results = pd.DataFrame(wAgg(tmpDta.loc[dataMask], aggregationDict = aggDictionary, varForWeights= (weightVar))).transpose()
        results['Source'] = 'All_' + self.eyStr

        resultsByRace = wGroupByAgg(tmpDta.loc[dataMask], ['raceR_' + self.syStr], aggregationDict = aggDictionary, varForWeights = (weightVar)).reset_index()
        resultsByRace['Source'] = 'Race_' + self.eyStr

        tmpDta['raceAndWave_'+self.eyStr] = tmpDta['raceR_' + self.eyStr] + '_' + tmpDta['surveyInclusionGroup_'+self.eyStr] # Note -- since the newest wave is only 2017-2019 we must filter this by End Year
        resultsByRaceAndWave = wGroupByAgg(tmpDta.loc[dataMask], ['raceAndWave_' + self.eyStr], aggregationDict = aggDictionary, varForWeights = (weightVar)).reset_index()
        resultsByRaceAndWave['Source'] = 'RaceAndWave_' + self.eyStr

        resultsByAge = wGroupByAgg(tmpDta.loc[dataMask], ['ageGroup_' + self.syStr], aggregationDict = aggDictionary, varForWeights = (weightVar)).reset_index()
        resultsByAge['Source'] = 'Age_' + self.eyStr

        resultsByApproxIncomeQ = wGroupByAgg(tmpDta.loc[dataMask], ['incomeApproxQuintile_PreTaxReal_' + self.inflatedStart], aggregationDict = aggDictionary, varForWeights = (weightVar)).reset_index()
        resultsByApproxIncomeQ['Source' ] ='IncomeApproxQuintile' + self.inflatedStart

        resultsByIncomeQ = wGroupByAgg(tmpDta.loc[dataMask], ['incomeQuintile_PreTaxReal_' + self.inflatedStart], aggregationDict = aggDictionary, varForWeights = (weightVar)).reset_index()
        resultsByIncomeQ['Source' ] ='IncomeQuintile' + self.inflatedStart

        # resultsByIncomeD = wGroupByAgg(tmpDta.loc[dataMask], ['incomeDecile_PreTaxReal_' + self.inflatedStart], aggregationDict = aggDictionary, varForWeights = (weightVar)).reset_index()
        # resultsByIncomeD['Source' ] ='IncomeDecile' + self.inflatedStart

        resultsByWealthQ = wGroupByAgg(tmpDta.loc[dataMask], ['wealthQuintile_Real_' + self.inflatedStart], aggregationDict = aggDictionary, varForWeights = (weightVar)).reset_index()
        resultsByWealthQ['Source' ] ='WealthQuintile' + self.inflatedStart

        # resultsByWealthD= wGroupByAgg(tmpDta.loc[dataMask], ['wealthDecile_Real_' + self.inflatedStart], aggregationDict = aggDictionary, varForWeights = (weightVar)).reset_index()
        # resultsByWealthD['Source' ] ='WealthDecile' + self.inflatedStart

        results = pd.concat([resultsByRace, resultsByRaceAndWave, results, resultsByAge, resultsByIncomeQ, resultsByApproxIncomeQ,
              # resultsByIncomeD ,
              resultsByWealthQ
              # resultsByWealthD
              ], ignore_index=True, sort=False)

        results['StartYear'] = self.startYear
        results['EndYear'] = self.endYear
        results['InflatedToYear'] = self.toYear

        results.rename(columns={'raceR_' + self.syStr: 'raceR',
                                'raceAndWave_' + self.eyStr: 'raceAndWave', # see above on why this is EY and others are SY
                                'ageGroup_' + self.syStr: 'ageGroup',
                                'incomeQuintile_PreTaxReal_' + self.syStr + '_as_' + self.tyStr: 'incomeQuintile_PreTaxReal',
                                'incomeApproxQuintile_PreTaxReal_' + self.syStr + '_as_' + self.tyStr: 'incomeApproxQuintile_PreTaxReal',
                                # 'incomeDecile_PreTaxReal_' + self.syStr + '_as_' + self.tyStr: 'incomeDecile_PreTaxReal',

                                'wealthQuintile_Real_' + self.syStr + '_as_' + self.tyStr: 'wealthQuintile_Real',
                                # 'wealthDecile_Real_' + self.syStr + '_as_' + self.tyStr: 'wealthDecile_Real',
                                }, inplace=True)

        return results


    def calcAssetLevelComponentsForYear(self):
        '''
        For each asset class, calculate the % of people who have that account, and median value of capital gains & savings
        :return: 
        :rtype: 
        '''

        assetTypes = ['House', 'OtherRealEstate', 'Business', 'BrokerageStocks', 'CheckingAndSavings', 'Vehicle',
                         'OtherAssets', 'AllOtherDebts', 'PrivateRetirePlan', 'EmployerRetirePlan']
        otherFields = ["inflatedNetWorthWithHomeAnd401k_AfterBalanceFillin_", "cleaningStatus_Wealth", "averageRealBeforeTaxIncome_AllYears_", "LongitudinalWeightHH", "raceR", "surveyInclusionGroup_", "incomeApproxQuintile_PreTaxReal", "incomeQuintile_PreTaxReal", "ageGroup", "wealthQuintile"]
        fieldsToKeep =[]
        for theCol in self.dta.columns.copy():
            gotIt = False
            for assetType in assetTypes:
                if (~gotIt) and (assetType in theCol):
                    fieldsToKeep = fieldsToKeep + [theCol]
                    gotIt = True
            for otherField in otherFields:
                if (otherField in theCol):
                        fieldsToKeep = fieldsToKeep + [theCol]

        tmp = self.dta[fieldsToKeep].copy()

        # First, we want to create an aggregation dictionary that covers the % of people with the account
        # We can do it for the Start of the period, End, or both. There's no clear right answer. We'll go with start
        aggDictionary = {}

        tmp['valueOfPrivateRetirePlan_Net_' + self.syStr] = tmp['valueOfPrivateRetirePlan_Gross_' + self.syStr]
        tmp['valueOfPrivateRetirePlan_Net_' + self.eyStr] = tmp['valueOfPrivateRetirePlan_Gross_' + self.eyStr]
        tmp['valueOfEmployerRetirePlan_Net_' + self.syStr] = tmp['valueOfEmployerRetirePlan_Gross_' + self.syStr]
        tmp['valueOfEmployerRetirePlan_Net_' + self.eyStr] = tmp['valueOfEmployerRetirePlan_Gross_' + self.eyStr]

        tmp['trimmed_inflatedNetWorthWithHomeAnd401k_AfterBalanceFillin_' + self.inflatedEnd] = tmp['inflatedNetWorthWithHomeAnd401k_AfterBalanceFillin_' + self.inflatedEnd]
        tmp.loc[~tmp['cleaningStatus_Wealth_' + self.timespan].isna(), 'trimmed_inflatedNetWorthWithHomeAnd401k_AfterBalanceFillin_' + self.inflatedEnd] = None


        for theAsset in assetTypes:
            aggDictionary['has' + theAsset + '_prct'] = ('has' + theAsset + '_' + self.syStr, 'mean')

        # Now, we want to get the median values for each account's savings and capital gains when non-zero
        for theAsset in assetTypes:
            tmp[theAsset + '_CapitalGains_' + self.inflatedTimespan].replace({0:None, 0.0:None}, inplace=True)
            tmp[theAsset + '_Savings_' + self.inflatedTimespan].replace({0:None, 0.0:None}, inplace=True)
            # tmp.loc[tmp[theAsset + '_CapitalGains_' + self.inflatedTimespan].eq(0), theAsset + '_CapitalGains_' + self.inflatedTimespan] = None
            # tmp.loc[tmp[theAsset + '_Savings_' + self.inflatedTimespan].eq(0), theAsset + '_Savings_' + self.inflatedTimespan] = None
            tmp['valueOf' + theAsset +  '_Net_' + self.inflatedStart] =  tmp['valueOf' + theAsset +  '_Net_' + self.syStr] * self.totalInflationStartToInflatedYear
            tmp['valueOf' + theAsset +  '_Net_' + self.inflatedEnd] =  tmp['valueOf' + theAsset +  '_Net_' + self.eyStr] * self.totalInflationEndToInflatedYear

            # if theAsset == 'BrokerageStocks':
            #    print('debugHere')

            tmp['valueOfCoded' + theAsset +  '_Net_' + self.inflatedEnd] =  tmp['valueOf' + theAsset +  '_Net_' + self.eyStr] * self.totalInflationEndToInflatedYear
            # tmp.loc[(tmp['valueOfCoded' + theAsset +  '_Net_' + self.inflatedEnd]==0.0) | tmp['valueOfCoded' + theAsset +  '_Net_' + self.inflatedEnd].isna() , 'valueOfCoded' + theAsset +  '_Net_' + self.eyStr] = None
            tmp['valueOfCoded' + theAsset +  '_Net_' + self.inflatedEnd].replace({'0.0':None, 0.0:None, 0:None,np.nan:None}, inplace=True)

            tmp['valueTrimmed' + theAsset +  '_Net_' + self.inflatedEnd] =  tmp['valueOf' + theAsset +  '_Net_' + self.eyStr] * self.totalInflationEndToInflatedYear
            tmp.loc[~tmp['cleaningStatus_Wealth_' + self.timespan].isna(), 'valueTrimmed' + theAsset +  '_Net_' + self.inflatedEnd] = None

            tmp[theAsset + '_AnnualSavings_PrcntOfIncome_' + self.inflatedTimespan] =  tmp[theAsset + '_Savings_' + self.inflatedTimespan].fillna(0).div \
                (tmp['averageRealBeforeTaxIncome_AllYears_' + self.inflatedTimespan]*self.duration)
            tmp[theAsset + '_AnnualCapitalGains_PrcntOfIncome_' + self.inflatedTimespan] =  tmp[theAsset + '_CapitalGains_' + self.inflatedTimespan].fillna(0).div \
                (tmp['averageRealBeforeTaxIncome_AllYears_' + self.inflatedTimespan]*self.duration)

            # savings as percent of wealth: savings across period, divided by INITIAL Wealth, by Duration of Time
            # tmp[theAsset + '_AnnualSavings_PrcntOfWealth_' + self.inflatedTimespan] =  tmp[theAsset + '_Savings_' + self.inflatedTimespan].fillna(0).div \
            #    (tmp['inflatedNetWorthWithHomeAnd401k_AfterBalanceFillin_' + self.inflatedStart]*self.duration)
            # tmp[theAsset + '_AnnualCapitalGains_PrcntOfWealth_' + self.inflatedTimespan] =  tmp[theAsset + '_CapitalGains_' + self.inflatedTimespan].fillna(0).div \
            #    (tmp['inflatedNetWorthWithHomeAnd401k_AfterBalanceFillin_' + self.inflatedStart]*self.duration)

            # asset value as percent of wealth: value at END Of Period, divided by ENDING Wealth - NOTE this is WITHOUT dividing by time period
            tmp[theAsset + '_EndValue_PrcntOfWealth_' + self.inflatedTimespan] =  tmp['valueOf' + theAsset +  '_Net_' + self.inflatedEnd].div \
                (tmp['inflatedNetWorthWithHomeAnd401k_AfterBalanceFillin_' + self.inflatedEnd])
            tmp[theAsset + '_EndValueTrimmed_PrcntOfWealth_' + self.inflatedTimespan] =  tmp['valueTrimmed' + theAsset +  '_Net_' + self.inflatedEnd].div \
                (tmp['inflatedNetWorthWithHomeAnd401k_AfterBalanceFillin_' + self.inflatedEnd])
            tmp[theAsset + '_EndValueCoded_PrcntOfWealth_' + self.inflatedTimespan] =  tmp['valueOfCoded' + theAsset +  '_Net_' + self.inflatedEnd].fillna(0).div \
                (tmp['inflatedNetWorthWithHomeAnd401k_AfterBalanceFillin_' + self.inflatedEnd])
            tmp.loc[tmp['valueOfCoded' + theAsset +  '_Net_' + self.inflatedEnd].isna(), theAsset + '_EndValueCoded_PrcntOfWealth_' + self.inflatedTimespan]= None

            tmp[theAsset + '_AnnualCapitalGains_PrcntOfStartingValue_Recalc_' + self.inflatedTimespan] =  tmp[theAsset + '_CapitalGains_' + self.inflatedTimespan].fillna(0).div \
                (tmp['inflatedNetWorthWithHomeAnd401k_AfterBalanceFillin_' + self.inflatedStart]*self.duration)


            aggDictionary['AnnualCapitalGains_PrcntOfStartingValue_AN_' + theAsset + '_median'] = (theAsset + '_AN_CapitalGainsRate_' + self.inflatedTimespan, 'median')
            aggDictionary['AnnualCapitalGains_PrcntOfStartingValue_AN_' + theAsset + '_mean'] = (theAsset + '_AN_CapitalGainsRate_' + self.inflatedTimespan, 'mean')

            aggDictionary['AnnualSavings_PrcntOfStartingValue_AN_' + theAsset + '_median'] =      (theAsset + '_AN_SavingsRate_' + self.inflatedTimespan, 'median')
            aggDictionary['AnnualGrowthRate_PrcntOfStartingValue_AN_' + theAsset + '_median'] =      (theAsset + '_AN_TotalGrowthRate_' + self.inflatedTimespan, 'median')

            # aggDictionary['PeriodCapitalGains_' + theAsset + '_median'] = (theAsset + '_CapitalGains_' + self.inflatedTimespan, 'median')
            # aggDictionary['PeriodSavings_' + theAsset + '_median'] =      (theAsset + '_Savings_' + self.inflatedTimespan, 'median')

            aggDictionary['AnnualCapitalGains_PrcntOfIncome_' + theAsset + '_median'] = (theAsset + '_AnnualCapitalGains_PrcntOfIncome_' + self.inflatedTimespan, 'median')
            aggDictionary['AnnualSavings_PrcntOfIncome_' + theAsset + '_median'] =      (theAsset + '_AnnualSavings_PrcntOfIncome_' + self.inflatedTimespan, 'median')

            # aggDictionary['AnnualCapitalGains_PrcntOfWealth_' + theAsset + '_median'] = (theAsset + '_AnnualCapitalGains_PrcntOfWealth_' + self.inflatedTimespan, 'median')
            # aggDictionary['AnnualSavings_PrcntOfWealth_' + theAsset + '_median'] =      (theAsset + '_AnnualSavings_PrcntOfWealth_' + self.inflatedTimespan, 'median')

            aggDictionary['EndValue_PrcntOfWealth_' + theAsset + '_median'] =      (theAsset + '_EndValue_PrcntOfWealth_' + self.inflatedTimespan, 'median')
            aggDictionary['EndValueTrimmed_PrcntOfWealth_' + theAsset + '_mean'] =      (theAsset + '_EndValueTrimmed_PrcntOfWealth_' + self.inflatedTimespan, 'mean')
            aggDictionary['EndValueTrimmed_' + theAsset + '_sum'] =      ('valueTrimmed' + theAsset +  '_Net_' + self.inflatedEnd, 'sum')
            aggDictionary['EndValueCoded_PrcntOfWealth_' + theAsset + '_median'] =      (theAsset + '_EndValueCoded_PrcntOfWealth_' + self.inflatedTimespan, 'median')

            aggDictionary['trimmedFilledin_real_networth_end_sum'] = ('trimmed_inflatedNetWorthWithHomeAnd401k_AfterBalanceFillin_' + self.inflatedEnd, 'sum')

        results = self.runSegmentedAggregations(tmp, aggDictionary)

        # tmp.to_csv("C:/Dev/sensitive_data/InvestorSuccess/Inequality/inequalityOutput_enrichedPop/analyses/assetAnalysis_tmp_"+ self.eyStr + ".csv")
        wealthSumField = 'trimmedFilledin_real_networth_end_sum'
        for theAsset in assetTypes:
            assetSumField = 'EndValueTrimmed_' + theAsset + '_sum'
            assetAvgAsSumField = 'EndValueTrimmed_PrcntOfWealth_' + theAsset + '_AvgAsSums'
            results[assetAvgAsSumField] = results[assetSumField] / (results[wealthSumField])

        return results

    def calcWealthComponentsForYear(self):
        '''
        Analyze sources of wealth, for the current year.

        This analysis isbBased on Gittleman, Table 5: Summary stats on Rates of Change in Wealth and its Components
        Note -- we've recalcuated Net Worth, filling in values that are missing but readily estimatable.
        Otherwise, you get wild swings in per-person wealth

        :return:
        :rtype:
        '''

        # These are MEAN analyses, so very sensitive to outliers.
        # Trim out highest and lowest % of wealth - following Gittleman.  Note - this is an optional cleaning flag; in Media based analyses, we DON'T filter by wealth % (no need)
        tmp = self.dta.loc[self.dta['cleaningStatus_Wealth_' + self.timespan].isna()].copy()

        # In particular, we're looking at Savings Rates - so create a filtered version of that: With wide Boundaries of 2x income
        goodSavingRateFlag =  (tmp[('activeSavingsRate_PerPerson_' + self.inflatedTimespan)] < 2*100) & (tmp[('activeSavingsRate_PerPerson_' + self.inflatedTimespan)] > -2*100)
        tmp['trimmed_averageRealBeforeTaxIncome_AllYears_' + self.inflatedTimespan] = tmp['averageRealBeforeTaxIncome_AllYears_' + self.inflatedTimespan]
        tmp.loc[~goodSavingRateFlag, 'trimmed_averageRealBeforeTaxIncome_AllYears_' + self.inflatedTimespan]  = None
        tmp['trimmed_Total_NetActiveSavings_' + self.inflatedTimespan] = tmp['Total_NetActiveSavings_' + self.inflatedTimespan]
        tmp.loc[~goodSavingRateFlag, 'trimmed_Total_NetActiveSavings_' + self.inflatedTimespan]  = None

        tmp['WealthAppreciationPercent_' + self.inflatedTimespan] =  tmp['inflatedNetWorthWithHomeAnd401k_AfterBalanceFillin_' + self.inflatedEnd].sub(tmp['inflatedNetWorthWithHomeAnd401k_AfterBalanceFillin_' + self.inflatedStart],fill_value=0).div \
            (tmp['inflatedNetWorthWithHomeAnd401k_AfterBalanceFillin_' + self.inflatedStart] ,fill_value=0)
        tmp['AnnualGrossSavingsPrcntWealth_' + self.inflatedTimespan] =  tmp['Annual_Total_GrossSavings_' + self.inflatedTimespan].div(tmp['inflatedNetWorthWithHomeAnd401k_AfterBalanceFillin_' + self.inflatedStart],fill_value=0)
        tmp['AnnualOpenCloseTransfersPrcntWealth_' + self.inflatedTimespan] =  tmp['Annual_Total_OpenCloseTransfers_' + self.inflatedTimespan].div(tmp['inflatedNetWorthWithHomeAnd401k_AfterBalanceFillin_' + self.inflatedStart],fill_value=0)
        tmp['AnnualActiveSavingsPrcntWealth_' + self.inflatedTimespan] =  tmp['Annual_Total_NetActiveSavings_' + self.inflatedTimespan].div \
            (tmp['inflatedNetWorthWithHomeAnd401k_AfterBalanceFillin_' + self.inflatedStart] ,fill_value=0)
        tmp['AnnualCapitalGainsPrcntWealth_' + self.inflatedTimespan] =  tmp['Annual_Total_CapitalGains_' + self.inflatedTimespan].div(tmp['inflatedNetWorthWithHomeAnd401k_AfterBalanceFillin_' + self.inflatedStart],fill_value=0)

        tmp['HasPositiveGrossSavings_' + self.inflatedTimespan] = ~((tmp['Total_GrossSavings_' + self.inflatedTimespan]< 0) | tmp['Total_GrossSavings_' + self.inflatedTimespan].eq(0) | tmp['Total_GrossSavings_' + self.inflatedTimespan].isna())
        tmp['HasPositiveCapGains_' + self.inflatedTimespan] = ~((tmp['Total_CapitalGains_' + self.inflatedTimespan]<0) | tmp['Total_CapitalGains_' + self.inflatedTimespan].eq(0) | tmp['Total_CapitalGains_' + self.inflatedTimespan].isna())
        tmp['HasInheritances_' + self.inflatedTimespan] = ~(tmp['largeGift_All_AmountHH_' + self.inflatedTimespan].eq(0) | tmp['largeGift_All_AmountHH_' + self.inflatedTimespan].isna())
        tmp['HasSmallGifts_' + self.inflatedTimespan] =  ~(tmp['SmallGift_All_AmountHH_' + self.inflatedTimespan].eq(0) | tmp['SmallGift_All_AmountHH_' + self.inflatedTimespan].isna())
        tmp['HasNetMove_' + self.inflatedTimespan] = ~(tmp['netAssetMove_' + self.inflatedTimespan].eq(0) | tmp['netAssetMove_' + self.inflatedTimespan].isna())
        tmp['HasPositiveNetMove_' + self.inflatedTimespan] = ((tmp['netAssetMove_' + self.inflatedTimespan] > 0) & (~tmp['netAssetMove_' + self.inflatedTimespan].isna()))
        tmp['HasNegativeNetMove_' + self.inflatedTimespan] = ((tmp['netAssetMove_' + self.inflatedTimespan] < 0) & (~tmp['netAssetMove_' + self.inflatedTimespan].isna()))

        # These things aren't common - so the medians will generally be zero.
        # We need to calculate the % separately, then look at non-zeroes
        inheritanceMask = tmp['HasInheritances_' + self.inflatedTimespan]
        giftMask = tmp['HasSmallGifts_' + self.inflatedTimespan]
        moveMask = tmp['HasNetMove_' + self.inflatedTimespan]

        tmp.loc[~inheritanceMask, 'largeGift_All_AmountHH_' + self.inflatedTimespan] = None
        tmp.loc[~giftMask, 'SmallGift_All_AmountHH_' + self.inflatedTimespan] = None
        tmp.loc[~moveMask, 'netAssetMove_' + self.inflatedTimespan] = None

        tmp['AnnualInheritancesPrcntWealth_' + self.inflatedTimespan] =  tmp['Annual_largeGift_All_AmountHH_' + self.inflatedTimespan].div \
            (tmp['inflatedNetWorthWithHomeAnd401k_AfterBalanceFillin_' + self.inflatedStart])
        tmp['AnnualSmallGiftsPrcntWealth_' + self.inflatedTimespan] =  tmp['Annual_SmallGift_All_AmountHH_' + self.inflatedTimespan].div \
            (tmp['inflatedNetWorthWithHomeAnd401k_AfterBalanceFillin_' + self.inflatedStart])
        tmp['AnnualNetMovePrcntWealth_' + self.inflatedTimespan] =  tmp['Annual_netAssetMove_' + self.inflatedTimespan].div \
            (tmp['inflatedNetWorthWithHomeAnd401k_AfterBalanceFillin_' + self.inflatedStart])


        aggDictionary = {
            'familyInterview_N': ('familyInterviewId_' +self.eyStr, 'count'),

            'wealth_appreciation_rate_median': ('WealthAppreciationPercent_' + self.inflatedTimespan, 'median'),

            # Values used to compare with Descriptive Stats
            'orig_real_networth_start_sum': ('inflatedNetWorthWithHomeAnd401k_' + self.inflatedStart, 'sum'),
            'orig_real_networth_end_sum': ('inflatedNetWorthWithHomeAnd401k_' + self.inflatedEnd, 'sum'),

            'filledin_real_networth_start_sum': ('inflatedNetWorthWithHomeAnd401k_AfterBalanceFillin_' + self.inflatedStart, 'sum'),
            'filledin_real_networth_end_sum': ('inflatedNetWorthWithHomeAnd401k_AfterBalanceFillin_' + self.inflatedEnd, 'sum'),

            'annual_gross_savings_pcntwlth_median': ('AnnualGrossSavingsPrcntWealth_' + self.inflatedTimespan, 'median'),
            'gross_savings_sum': ('Total_GrossSavings_' + self.inflatedTimespan, 'sum'),

            'annual_openclose_transfers_pcntwlth_median': ('AnnualOpenCloseTransfersPrcntWealth_' + self.inflatedTimespan, 'median'),
            'openclose_transfers_sum': ('Total_OpenCloseTransfers_' + self.inflatedTimespan, 'sum'),

            'annual_active_savings_pcntwlth_median': ('AnnualActiveSavingsPrcntWealth_' + self.inflatedTimespan, 'median'),
            'active_savings_sum': ('Total_NetActiveSavings_' + self.inflatedTimespan, 'sum'),

            'annual_capital_gains_pcntwlth_median': ('AnnualCapitalGainsPrcntWealth_' + self.inflatedTimespan, 'median'),
            'capital_gains_sum': ('Total_CapitalGains_' + self.inflatedTimespan, 'sum'),

            # Since 0s are removed above, these are calculated for the HHs with with this type of transfer
            'annual_inheritance_pcntwlth_median': ('AnnualInheritancesPrcntWealth_' + self.inflatedTimespan, 'median'),
            'inheritance_sum': ('largeGift_All_AmountHH_' + self.inflatedTimespan, 'sum'),

            # Since 0s are removed above, these are calculated for the HHs with with this type of transfer
            'annual_smallgifts_pcntwlth_median': ('AnnualSmallGiftsPrcntWealth_' + self.inflatedTimespan, 'median'),
            'smallgifts_sum': ('SmallGift_All_AmountHH_' + self.inflatedTimespan, 'sum'),

            # Since 0s are removed above, these are calculated for the HHs with with this type of transfer
            'annual_movewealth_pcntwlth_median': ('AnnualNetMovePrcntWealth_' + self.inflatedTimespan, 'median'),
            'movewealth_sum': ('netAssetMove_' + self.inflatedTimespan, 'sum'),


            'hasGrossSavings_prct': ('HasPositiveGrossSavings_' + self.inflatedTimespan, 'mean'),
            'hasCapGains_prct': ('HasPositiveCapGains_' + self.inflatedTimespan, 'mean'),
            'hasInheritance_prct': ('HasInheritances_' + self.inflatedTimespan, 'mean'),
            'hasSmallGift_prct': ('HasSmallGifts_' + self.inflatedTimespan, 'mean'),
            'hasNetMove_prct': ('HasNetMove_' + self.inflatedTimespan, 'mean'),
            'hasPositiveNetMove_prct': ('HasPositiveNetMove_' + self.inflatedTimespan, 'mean'),
            'hasNegativeNetMove_prct': ('HasNegativeNetMove_' + self.inflatedTimespan, 'mean'),

            'annual_active_savings_median': ('Annual_Total_NetActiveSavings_' + self.inflatedTimespan, 'median'),
            'annual_gross_savings_median': ('Annual_Total_GrossSavings_' + self.inflatedTimespan, 'median'),
            'annual_openclose_transfers_median': ('Annual_Total_OpenCloseTransfers_' + self.inflatedTimespan, 'median'),
            'annual_capital_gains_median': ('Annual_Total_CapitalGains_' + self.inflatedTimespan, 'median'),
            'annual_smallgifts_median': ('Annual_SmallGift_All_AmountHH_' + self.inflatedTimespan, 'median'),
            'annual_movewealth_median': ('Annual_netAssetMove_' + self.inflatedTimespan, 'median'),
            'annual_inheritance_median': ('Annual_largeGift_All_AmountHH_' + self.inflatedTimespan, 'median'),

            'annual_active_savings_mean': ('Annual_Total_NetActiveSavings_' + self.inflatedTimespan, 'mean'),
            'annual_gross_savings_mean': ('Annual_Total_GrossSavings_' + self.inflatedTimespan, 'mean'),
            'annual_openclose_transfers_mean': ('Annual_Total_OpenCloseTransfers_' + self.inflatedTimespan, 'mean'),
            'annual_capital_gains_mean': ('Annual_Total_CapitalGains_' + self.inflatedTimespan, 'mean'),
            'annual_smallgifts_mean': ('Annual_SmallGift_All_AmountHH_' + self.inflatedTimespan, 'mean'),
            'annual_movewealth_mean': ('Annual_netAssetMove_' + self.inflatedTimespan, 'mean'),
            'annual_inheritance_mean': ('Annual_largeGift_All_AmountHH_' + self.inflatedTimespan, 'mean'),

            # We're also going to recalculate the Mean Savings Rate, using the trimmmed population - we need income for that
            'trimmed_real_pre_tax_income_sum': ('trimmed_averageRealBeforeTaxIncome_AllYears_' + self.inflatedTimespan, 'sum'),
            'trimmed_active_savings_sum': ('trimmed_Total_NetActiveSavings_' + self.inflatedTimespan, 'sum'),
        }

        results = self.runSegmentedAggregations(tmp, aggDictionary)

        results['wealth_appreciation_rate_AvgsAsSums'] = \
            (results.filledin_real_networth_end_sum - results.filledin_real_networth_start_sum) / (
                        results.filledin_real_networth_start_sum * self.duration)

        results['gross_savings_rate_AvgAsSums'] = results.gross_savings_sum / (results.filledin_real_networth_start_sum * self.duration)
        results['active_savings_rate_AvgAsSums'] = results.active_savings_sum / (results.filledin_real_networth_start_sum * self.duration)
        results['openclose_transfers_rate_AvgAsSums'] = results.openclose_transfers_sum / (results.filledin_real_networth_start_sum * self.duration)
        results['capital_gains_rate_AvgAsSums'] = results.capital_gains_sum / (results.filledin_real_networth_start_sum * self.duration)
        results['inheritance_rate_AvgAsSums'] = results.inheritance_sum / (results.filledin_real_networth_start_sum * self.duration)
        results['smallgift_rate_AvgAsSums'] = results.smallgifts_sum / (results.filledin_real_networth_start_sum * self.duration)
        results['movewealth_rate_AvgAsSums'] = results.movewealth_sum / (results.filledin_real_networth_start_sum * self.duration)

        # Since the wealth analysis is Trimmed of outliers, let's use this opportunity to calculate the trimmed Average Savings Rate as Well
        results['activeSavings_AvgAsSums_Trimmed'] = results.trimmed_active_savings_sum / (results.trimmed_real_pre_tax_income_sum * self.duration)

        return results


    def calcWeightedAggSavingsRatesForYear(self):
        '''

        :param self:
        :type self:
        :return:
        :rtype:
        '''
        aggDictionary = {
            'familyInterview_N': ('familyInterviewId_' + self.eyStr, 'count'),
            'familyInterview_TotalWeights': ('familyInterviewId_' + self.eyStr, 'SumOfWeights'),

            # Values needed for Savings Calc
            'real_pre_tax_income_sum': ('averageRealBeforeTaxIncome_AllYears_' + self.inflatedTimespan, 'sum'),
            'real_after_tax_income_sum': ('averageRealAfterTaxIncome_AllYears_' + self.inflatedTimespan, 'sum'),

            # 'changeInRealNetWorth_sum': ('changeInRealNetWorth_' + self.inflatedTimespan, 'sum'),
            'old_changeInRealNetWorthWithHomeAnd401k_sum': ('changeInRealNetWorthWithHomeAnd401k_' + self.inflatedTimespan, 'sum'),
            'changeInRealNetWorthWithHomeAnd401k_sum': ('changeInRealNetWorthWithHomeAnd401k_AfterBalanceFillin_' + self.inflatedTimespan, 'sum'),
            'netactive_real_sum': ('Total_NetActiveSavings_' + self.inflatedTimespan, 'sum'),

            'active_median': ('activeSavingsRate_PerPerson_' + self.inflatedTimespan, 'median'),

            # Input Values for Savings Calc
            'change_in_asset_value_sum': ('Total_ChangeInWealth_' + self.inflatedTimespan, 'sum'),
            'total_capital_gains_sum': ('Total_CapitalGains_' + self.inflatedTimespan, 'sum'),
            'total_gross_savings_sum': ('Total_GrossSavings_' + self.inflatedTimespan, 'sum'),

            # Values used to compare with Descriptive Stats
            'old_real_networth_mean': ('inflatedNetWorthNoHouseOr401k_' + self.inflatedEnd, 'mean'),
            'old_real_networth_median': ('inflatedNetWorthNoHouseOr401k_' + self.inflatedEnd, 'median'),
            'old_real_recalc_networth_mean': ('inflatedNetWorthWithHomeRecalc_' + self.inflatedEnd, 'mean'),
            'old_real_recalc_networth_median': ('inflatedNetWorthWithHomeRecalc_' + self.inflatedEnd, 'median'),

            'old_real_NetWorthWithHomeAnd401k_mean': ('inflatedNetWorthWithHomeAnd401k_' + self.inflatedEnd, 'mean'),
            'old_real_NetWorthWithHomeAnd401k_median': ('inflatedNetWorthWithHomeAnd401k_' + self.inflatedEnd, 'median'),

            'filledIn_real_NetWorthWithHomeAnd401k_mean': ('inflatedNetWorthWithHomeAnd401k_AfterBalanceFillin_' + self.inflatedEnd, 'mean'),
            'filledIn_real_NetWorthWithHomeAnd401k_median': ('inflatedNetWorthWithHomeAnd401k_AfterBalanceFillin_' + self.inflatedEnd, 'median'),

            # Pre tax
            'income_totaltaxable_avg': ('totalIncomeHH_' + self.eyStr, 'mean'),
            'income_totaltaxable_median': ('totalIncomeHH_' + self.eyStr, 'median'),

            'real_pre_tax_income_median': ('averageRealBeforeTaxIncome_AllYears_' + self.inflatedTimespan, 'median'),
            'real_after_tax_income_avg': ('averageRealAfterTaxIncome_AllYears_' + self.inflatedTimespan, 'mean'),
            'real_after_tax_income_median': ('averageRealAfterTaxIncome_AllYears_' + self.inflatedTimespan, 'median'),
        }

        results = self.runSegmentedAggregations(self.dta, aggDictionary)
        results['activeSavings_AvgAsSums'] = results.netactive_real_sum / (results.real_pre_tax_income_sum * self.duration)
        results.activeSavings_AvgAsSums = results.activeSavings_AvgAsSums * 100.0
        return results


    def runRegressionAndExtract(self, dta, IVs, DVs, reg_type, label, resultsSoFar=None):
        allVars = IVs + DVs + ['LongitudinalWeightHH_' + self.eyStr]
        tmp = dta[allVars].dropna()

        try:
            if reg_type == 'Quantile':
                if self.rsi is None:
                    self.rsi = RSurveyInterface()
                results = self.rsi.getQuantileReg(tmp, IVs, DVs, weightVar='LongitudinalWeightHH_' + self.eyStr)
                results['NumObs'] = len(tmp)
            else:
                detailedResults = wRegression(tmp, IVs, DVs, varforWeights='LongitudinalWeightHH_' + self.eyStr, addConstant=True,
                                              reg_type=reg_type)
                print(detailedResults.summary())
                results = InequalityAnalysisBase.extractRegressionResults(detailedResults)
                results = results.reset_index()
                results.rename(columns={'index': 'var'}, inplace=True)
        except Exception as e:
            data = {'var': allVars, 'coeff': str(e), 'pvalue': 0, 'NumObs': len(tmp)}
            results = pd.DataFrame.from_dict(data)
        finally:
            results['Source'] = label
            results['StartYear'] = self.startYear
            results['EndYear'] = self.endYear
            results['InflatedToYear'] = self.toYear
            if (resultsSoFar is None):
                return results
            else:
                return pd.concat([resultsSoFar, results], ignore_index=True)


    def prepDataForRegressions(self):
        # are age of head and its square, sex and education of head, marital status at start and end of period, and number of children
        tmp = self.dta.loc[self.dta['raceR_' + self.syStr].isin(['White', 'Black', 'Hispanic'])].copy()
        dummies = pd.get_dummies(tmp['raceR_' + self.syStr], drop_first=False)
        tmp = tmp.join(dummies)
        tmp.Black = tmp.Black.astype(int)
        tmp.Hispanic = tmp.Hispanic.astype(int)

        dummies = pd.get_dummies(tmp['incomeQuintile_PreTaxReal_' + self.inflatedStart], drop_first=False)
        tmp = tmp.join(dummies)

        tmp['MarriedStart'] = tmp['martialStatusR_' + self.syStr].eq("Married").astype(int)
        tmp['MarriedEnd'] = tmp['martialStatusR_' + self.eyStr].eq("Married").astype(int)

        # dummies = pd.get_dummies(tmp['familyIsMarried_' + self.syStr], drop_first= False)
        # tmp = tmp.join(dummies)

        tmp.rename(columns={'averageRealBeforeTaxIncome_AllYears_' + self.inflatedTimespan: 'Income',
                            'activeSavingsRate_PerPerson_' + self.inflatedTimespan: 'SavingsRate',
                            'ageR_' + self.syStr: 'Age',
                            'NumChildrenInFU_' + self.syStr: 'NumChildren',
                            'educationYearsR_' + self.syStr: 'Education'
                            }, inplace=True)

        tmp['Income_Sq'] = tmp['Income'] ** 2
        tmp['Age_Sq'] = tmp['Age'] ** 2

        tmp['logIncome'] = np.log2(tmp['Income']).fillna(0)

        tmp = tmp[tmp['LongitudinalWeightHH_' + self.eyStr] > 0].copy()
        tmp = tmp[~(tmp.SavingsRate.isna())].copy()
        # TODO: evaluate and document if we want to keep this. It's important for mean calcs, but could warp the median
        # tmp = tmp[(tmp.SavingsRate > -100) & (tmp.SavingsRate < 100)].copy()


        return tmp

    def calcRegressionOnSavings(self):

        tmp = self.prepDataForRegressions()

        resultsSoFar = None

#        resultsSoFar = self.runRegressionAndExtract(tmp, IVs=['Black', 'Hispanic'], DVs=['SavingsRate'], reg_type='OLS',
#                                                    label="Race OLS", resultsSoFar=None)

#        resultsSoFar = self.runRegressionAndExtract(tmp, IVs=['Black', 'Hispanic', 'Income', 'Income_Sq'], DVs=['SavingsRate'],
#                                                    reg_type='OLS', label="Race&Income OLS", resultsSoFar=resultsSoFar)

#        resultsSoFar = self.runRegressionAndExtract(tmp, IVs=['Income', 'Income_Sq', 'Age', 'Age_Sq', 'Education',
#                                                              'MarriedStart', 'NumChildren'], DVs=['SavingsRate'],
#                                                    reg_type='OLS', label="Broad OLS", resultsSoFar=resultsSoFar)
#        resultsSoFar = self.runRegressionAndExtract(tmp, IVs=['Black', 'Hispanic', 'Income', 'Income_Sq', 'Age', 'Age_Sq', 'Education',
#                                                              'MarriedStart', 'NumChildren'], DVs=['SavingsRate'],
#                                                    reg_type='OLS', label="Broad wRace OLS", resultsSoFar=resultsSoFar)
        # 'MarriedEnd',

        # resultsSoFar.to_csv(os.path.join(self.baseDir, self.outputSubDir, "SW_Analysis_Mean_Regressions_" + self.inflatedTimespan + ".csv"), index=False)

        resultsSoFar = self.runRegressionAndExtract(tmp, IVs=['Black', 'Hispanic'], DVs=['SavingsRate'], reg_type='Quantile',
                                                    label="Race Quantile", resultsSoFar=resultsSoFar)

        resultsSoFar = self.runRegressionAndExtract(tmp, IVs=['Black', 'Hispanic', 'Income', 'Income_Sq'], DVs=['SavingsRate'],
                                                    reg_type='Quantile', label="Race & SqIncome QuantileReg",
                                                    resultsSoFar=resultsSoFar)

        resultsSoFar = self.runRegressionAndExtract(tmp, IVs=['Black', 'Hispanic', 'logIncome'], DVs=['SavingsRate'],
                                                    reg_type='Quantile', label="Race & LogIncome QuantileReg",
                                                    resultsSoFar=resultsSoFar)

        resultsSoFar = self.runRegressionAndExtract(tmp, IVs=['logIncome', 'Age', 'Age_Sq', 'Education',
                                                              'MarriedStart', 'NumChildren'], DVs=['SavingsRate'],
                                                    reg_type='Quantile', label="Broad QuantileReg", resultsSoFar=resultsSoFar)

        resultsSoFar = self.runRegressionAndExtract(tmp, IVs=['Black', 'Hispanic', 'Income', 'Income_Sq', 'Age', 'Age_Sq', 'Education',
                                                              'MarriedStart', 'NumChildren'], DVs=['SavingsRate'],
                                                    reg_type='Quantile', label="Broad wRaceSqIncome QuantileReg",
                                                    resultsSoFar=resultsSoFar)

        resultsSoFar = self.runRegressionAndExtract(tmp, IVs=['Black', 'Hispanic', 'logIncome', 'Age', 'Age_Sq', 'Education',
                                                              'MarriedStart', 'NumChildren'], DVs=['SavingsRate'],
                                                    reg_type='Quantile', label="Broad wRaceLogIncome QuantileReg",
                                                    resultsSoFar=resultsSoFar)

        # 'MarriedEnd',

        return resultsSoFar


    def executeForTimespan(self, saveToFile=False,includeRegressions= True):
        self.createSegmentBins_Longitudinal()

        self.inflator = CPI_InflationReader.CPIInflationReader()
        self.totalInflationStartToEndYear = self.inflator.getInflationFactorBetweenTwoYears(self.startYear, self.endYear)
        self.totalInflationEndToInflatedYear = self.inflator.getInflationFactorBetweenTwoYears(self.endYear, self.toYear)
        self.totalInflationStartToInflatedYear = self.inflator.getInflationFactorBetweenTwoYears(self.startYear, self.toYear)

        self.dta['activeSavingsRate_PerPerson_' + self.inflatedTimespan] = 100.0 * self.dta[
            'activeSavingsRate_PerPerson_' + self.inflatedTimespan]

        assetResults = self.calcAssetLevelComponentsForYear()
        if saveToFile:
            assetResults.to_csv(os.path.join(self.baseDir, self.outputSubDir, 'AssetLevelResults_Weighted_' + self.inflatedTimespan + '.csv'))

        aggResults = self.calcWeightedAggSavingsRatesForYear()
        if saveToFile:
            aggResults.to_csv(os.path.join(self.baseDir, self.outputSubDir, 'SavingsRates_Weighted_' + self.inflatedTimespan + '.csv'))

        wealthChangeResults = self.calcWealthComponentsForYear()
        if saveToFile:
            wealthChangeResults.to_csv(os.path.join(self.baseDir, self.outputSubDir, 'WealthChange_' + self.inflatedTimespan + '.csv'))

        if (includeRegressions):
            regressionResults = self.calcRegressionOnSavings()
            if saveToFile:
                regressionResults.to_csv(os.path.join(self.baseDir, self.outputSubDir, "Analysis_Regressions_" + self.inflatedTimespan + ".csv"),index=False)
        else:
            regressionResults = None

        # savingsComponentsResults = self.calcSavingsComponentsForYear()
        # if saveToFile:
        #    savingsComponentsResults.to_csv(os.path.join(self.baseDir, self.outputSubDir, 'SavingsComponents_' + self.inflatedTimespan +'.csv'))

        return (assetResults, aggResults, wealthChangeResults, regressionResults)




''' Allow execution from command line, etc'''
if __name__ == "__main__":

    apa = AggregatePopulationAnalyzer(baseDir = 'C:/dev/sensitive_data/InvestorSuccess/Inequality',
                                        inputSubDir = 'inequalityOutput',
                                        inputBaseName = "WithSavings_",
                                        outputBaseName = "WithSavings_",
                                        outputSubDir = 'inequalityOutput/analyses'
                                    )
    apa.useCleanedDataOnly = True
    apa.clearData()
    apa.setPeriod(2017, 2019, 2019)
    apa.readLongitudinalData()

    apa.executeForTimespan(saveToFile=False,includeRegressions= False)
    apa.createSegmentBins_Longitudinal()
    apa.dta['activeSavingsRate_PerPerson_' + apa.inflatedTimespan] = 100.0 * apa.dta['activeSavingsRate_PerPerson_' + apa.inflatedTimespan]

    tmp = apa.prepDataForRegressions()


    IVs=['Black', 'Hispanic', 'Income', 'Income_Sq', 'Age', 'Age_Sq', 'Education', 'MarriedStart', 'NumChildren']
    DVs=['SavingsRate']
    resultsSoFar = apa.runRegressionAndExtract(tmp, IVs, DVs, reg_type='Quantile', label="Broad wRace Quantile", resultsSoFar=None)

    allVars = IVs + DVs + ['LongitudinalWeightHH_' + apa.syStr, 'raceR_' + apa.syStr]
    tmp = tmp[allVars].dropna()

    tmp.to_csv('C:/dev/sensitive_data/InvestorSuccess/Inequality/TempForQuantileRegressionTest_' + apa.timespan + '.csv')


    rsi = RSurveyInterface()
    results = rsi.getQuantileReg(tmp, IVs, DVs, weightVar='LongitudinalWeightHH_' + apa.syStr)

    ivDta = tmp[IVs]
    dvDta = tmp[DVs]
    # ivDta = sm.add_constant(ivDta) #Adds intercept to model
    varforWeights='LongitudinalWeightHH_' + apa.syStr
    weightDta = tmp[varforWeights]

    mod = sr.quantile_regression.QuantReg(endog=dvDta,exog=ivDta)
    result = mod.fit(q=.5)

    # detailedResults = wRegression(tmp, IVs, DVs, varforWeights, addConstant=False, reg_type='Quantile')
    # print(detailedResults.summary())





