import pandas as pd
import numpy as np
import os
from Survey.SurveyFunctions import *
import Inflation.CPI_InflationReader as CPI_InflationReader
import MStarReport.InequalityAnalysisBase as InequalityAnalysisBase


''' Key Descriptions

'''


class InequalityDataPrep(InequalityAnalysisBase.InequalityAnalysisBase):

    familyFieldsWeNeedStartEnd = ['familyInterviewId', 'familyId1968',
                            'ChangeInCompositionFU', 'ChangeInCompositionFU_1989FiveYear',
                            'totalIncomeHH',
                            'NetWorthWithHome', 'NetWorthWithHomeRecalc',
                                  'NetWorthNoHome', 'NetWorthWithHomeAnd401k',

                            'PovertyThreshold',
                            'valueOfHouse_Debt', 'valueOfHouse_Gross', 'valueOfHouse_Net',
                            'valueOfVehicle_Net', 'valueOfCheckingAndSavings_Net', 'valueOfBrokerageStocks_Net',
                            'valueOfOtherAssets_Net', 'valueOfAllOtherDebts_Net', 'valueOfOtherRealEstate_Net', 'valueOfBusiness_Net',
                            'valueOfPrivateRetirePlan_Gross', 'valueOfEmployerRetirePlan_Gross',
                            'retirementContribRateR','retirementContribRateS', 'retirementContribHH',
                            
                            'largeGift_All_AmountHH', 'SmallGift_All_AmountHH',
                            'PersonMovedIn_SinceLastQYr_AssetsMovedIn', 'PersonMovedIn_SinceLastQYr_DebtsMovedIn',
                            'PersonMovedOut_SinceLastQYr_AssetsMovedOut', 'PersonMovedOut_SinceLastQYr_DebtsMovedOut',
                            'PrivateRetirePlan_SinceLastQYr_AmountMovedIn', 'PrivateRetirePlan_SinceLastQYr_AmountMovedOut',
                              
                            'CostOfMajorHomeRenovations',
                            'OtherRealEstate_SinceLastQYr_AmountBought', 'OtherRealEstate_SinceLastQYr_AmountSold',
                            'BrokerageStocks_SinceLastQYr_AmountBought', 'BrokerageStocks_SinceLastQYr_AmountSold',
                            'Business_SinceLastQYr_AmountBought', 'Business_SinceLastQYr_AmountSold',

                            'educationYearsR',
                            'martialStatusGenR', 'martialStatusR',
                            'NumChildrenInFU',
                            'raceR', 'raceS', 'ageR', 'genderR',
                            'hispanicR','hispanicS',

                            'institutionLocationHH',
                            'inMixedRaceCouple',
                            'surveyInclusionGroup',
                            'genderOfPartners',
                            'householdStructure',

                            'stateH', 'stateH_SOI', 'stateH_FIPS',
                            'regionH','isMetroH', 'metroSizeH','sizeLargestCityH',
                            'regionGrewUpR','geoMobilityR','regionGrewUpS','geoMobilityS',
                            'stateGrewUpR', 'stateGrewUpS',

                            'hasHouse', 'hasOtherRealEstate', 'hasVehicle', 'hasBrokerageStocks',
                            'hasCheckingAndSavings', 'hasBusiness', 'hasOtherAssets', 'hasEmployerRetirePlan',
                            'hasPrivateRetirePlan', 'hasAllOtherDebts',

                            'LongitudinalWeightHH',
                            'MovedR',
                            'ActiveSavings_PSID1989',

                            'IsWorkingR', 'IsWorkingS',
                            'reasonLeftLastJobR', 'reasonLeftLastJobS',
                            'RetPlan_IsEligibleR', 'RetPlan_IsParticipatingR',
                            'RetPlan_IsEligibleS', 'RetPlan_IsParticipatingS',
                            'RetPlan_TypeR', 'RetPlan_TypeS',
                                  
                            'FederalIncomeTaxesRS', 'FederalIncomeTaxesO',
                              # From TaxSim:
                             'fiitax', 'siitax', 'fica',

                            # Immigration
                            'firstYearInUS_R', 'firstYearInUS_S','immigrantStatusIn2016_HH',
                            'englishSpokenMostOftenR', 'understandEnglishR', 'speakEnglishR', 'readEnglishR', 'writeEnglishR',

                            # Helping Others
                            'helpsOthersFinancially', 'numberOtherHelpedFinancially', 'amountOtherHelpedFinancially',
                            'providesChildSupport', 'amountChildSupport', 'providesAlimony', 'amountAlimony'
                              ] 

    familyFieldsWeNeedMiddleYears = [
                            'familyInterviewId', 'familyId1968', 
                            'MovedR', 'ChangeInCompositionFU',
                            'ageR','educationYearsR', 'martialStatusR',
                            'retirementContribRateR','retirementContribRateS', 'retirementContribHH',
                            'totalIncomeHH',  'institutionLocationHH',
                            'hasHouse',
                            'valueOfHouse_Gross', 'valueOfHouse_Debt',
                            'FederalIncomeTaxesRS', 'FederalIncomeTaxesO', 'fiitax', 'siitax', 'fica'
                            ]


    def __init__(self, baseDir, familyInputSubDir, familyBaseName, individualInputSubDir, individualBaseName, outputSubDir,
                 inputBaseName, outputBaseName,  useOriginalSampleOnly):
        
        super().__init__(baseDir, inputSubDir = familyInputSubDir,
                         inputBaseName = inputBaseName,outputBaseName = outputBaseName, outputSubDir = outputSubDir)
        
        self.famPath = os.path.join(baseDir, familyInputSubDir, familyBaseName)
        self.indPath = os.path.join(baseDir, individualInputSubDir, individualBaseName)
        
        self.useOriginalSampleOnly = useOriginalSampleOnly

        self.inflator = CPI_InflationReader.CPIInflationReader()


    def readRawData(self):
        '''
        The main function to read each year of single-year PSID data, clean it, and save the resulting single-year files
        :return:
        :rtype:
        '''

        individualData = pd.read_csv((self.indPath + ".csv"),low_memory=False)
        
        finalWaveAgeVar = "ageI_" + self.eyStr
        
        # Get head of household 
        finalYearSequenceVar = "sequenceNoI_" + self.eyStr
        finalFamilyInterviewVar = "interviewId_" + self.eyStr
        individualData = individualData.loc[individualData[finalYearSequenceVar] == 1].copy()

        # if (self.useOriginalSampleOnly): 
        #     individualData = individualData.loc[(individualData.interviewId_1968 < 3000) | (individualData.interviewId_1968 > 5000 and (individualData.interviewId_1968 < 7000))].copy()
        
        # Note - there may be more than one family 
        individualData['constantFamilyId'] = range(1,(len(individualData)+1), 1) #
        # individualData['constantFamilyId'] = individualData[finalFamilyInterviewVar]
        # if (len(individualData)+1) !=  individualData['constantFamilyId'].unique()):
        #         raise Except("Final Year Interview Id for Head of Household isn't a unique id for all rows")


        inidvidualVars = [finalWaveAgeVar, 'constantFamilyId', 'constantIndividualID',
                          'longitudinalWeightI_' + self.eyStr] + \
                         ['stateBornI_1997','stateBornI_1999'] + \
                         ['countryBornI_1997','countryBornI_1999'] + \
                         ['livedInUSIn68I_1997','livedInUSIn68I_1999']

        for year in (self.yearsWithFamilyData.copy()):
            inidvidualVars = inidvidualVars + ['interviewId_' + str(year)]
            
        dta = individualData[inidvidualVars].copy() 

        familyInterviewVars = []
        
        for year in (self.yearsWithFamilyData.copy()):
            
            theVars = self.familyFieldsWeNeedMiddleYears
            if ((year == self.startYear) | (year == self.endYear) ):
                theVars= self.familyFieldsWeNeedStartEnd
        
            # Bring in a year of family data -- to see observed outcomes 
            familyDataForYear = pd.read_csv((self.famPath  + str(year) + ".csv"),low_memory=False)
            self.yearData = familyDataForYear[theVars].copy()
            self.yearDataYear= year

            self.yearData.columns = [(x + '_' + str(year)) for x in self.yearData.columns]
            
            # Clean it, Inflate it, save it.
            self.processCrossSectionalData()

            self.yearData = InequalityAnalysisBase.selectiveReorder(self.yearData,
                                                                    ['familyInterviewId_' + str(self.yearDataYear),
                                                                'familyId1968_' + str(self.yearDataYear),
                                                                'ChangeInCompositionFU_' + str(self.yearDataYear),
                                                                'cleaningStatus_' + str(self.yearDataYear),
                                                                 'modificationStatus_' + str(self.yearDataYear),
                                                                 ],
                                                                    alphabetizeTheOthers = True)
            self.saveCrossSectionalData(self.yearData, self.yearDataYear)
            
            indInterviewVar = "interviewId_" + str(year)
            dta = pd.merge(dta, self.yearData, right_on = 'familyInterviewId_'+ str(year), 
                                left_on = indInterviewVar, 
                                how = 'left')

            familyInterviewVars = familyInterviewVars + ['familyInterviewId_'+ str(year)]

        # TODO -- Drop any all blank-ones
        self.dta = dta.loc[~(dta[familyInterviewVars].isnull().all(axis=1))].copy()


    def processCrossSectionalData(self):
        '''
        Handles all of the cleaning and procesing we need for a year of PSID family+individual data
        :return:
        :rtype:
        '''
        self.processCrossSectional_CalcAfterTaxIncome()
        self.processCrossSectional_InflateValues()
        self.processCrossSectional_Clean()
        self.processCrossSectional_CreateCSSegmentBins()


    def processCrossSectional_CalcAfterTaxIncome(self):
        yr = str(self.yearDataYear)
        if (self.yearDataYear >= 1970 and self.yearDataYear <= 1991):
            self.yearData['TotalTax_' + yr] = self.yearData['FederalIncomeTaxesRS_' + yr].add(self.yearData['FederalIncomeTaxesO_' + yr], fill_value=0)  
        else:
            self.yearData['TotalTax_' + yr] = self.yearData['fiitax_' + yr]

        #CHANGE FROM GITTLEMAN: Included State Tax
        self.yearData['TotalTax_' + yr] = self.yearData['TotalTax_' + yr].add(self.yearData['siitax_' + yr], fill_value=0) 

        # Add FICA -- was not included in Gittleman?
        self.yearData['TotalTax_' + yr] = self.yearData['TotalTax_' + yr].add(self.yearData['fica_' + yr]/2.0, fill_value=0)

        self.yearData['afterTaxIncomeHH_' + yr] = self.yearData['totalIncomeHH_' + yr].sub(self.yearData['TotalTax_' + yr], fill_value=0)


    def processCrossSectional_InflateValues(self):
        '''
        Inflate our key dollar values to the 'toYear' of this analysis
        :return:
        :rtype:
        '''
        yr = str(self.yearDataYear)
        
        ################
        # Inflate values that COULD include intermediate years
        ################
        inflatedYear = yr + '_as_' + self.tyStr
        inflationGivenYear =  self.inflator.getInflationFactorBetweenTwoYears(self.yearDataYear, self.toYear)
        # inflationLagYear =  nipa.getInflationFactorBetweenTwoYears(year-1, self.toYear-1)
        # TODO -- Gittleman doesn't use lag year?

        if (self.yearDataYear in self.yearsWealthDataCollected):
            self.yearData['inflatedNetWorthNoHouseOr401k_' + inflatedYear] = self.yearData['NetWorthNoHome_' + yr] * inflationGivenYear
            self.yearData['inflatedNetWorthWithHome_' + inflatedYear] = self.yearData['NetWorthWithHome_' + yr] * inflationGivenYear
            self.yearData['inflatedNetWorthWithHomeRecalc_' + inflatedYear] = self.yearData['NetWorthWithHomeRecalc_' + yr] * inflationGivenYear
            self.yearData['inflatedNetWorthWithHomeAnd401k_' + inflatedYear] = self.yearData['NetWorthWithHomeAnd401k_' + yr] * inflationGivenYear

        self.yearData['inflatedPreTaxIncome_' + inflatedYear] = self.yearData['totalIncomeHH_' + yr] * inflationGivenYear # inflationLagYear 
        self.yearData['inflatedAfterTaxIncome_' + inflatedYear] = self.yearData['afterTaxIncomeHH_' + yr] * inflationGivenYear # inflationLagYear 


    def processCrossSectional_Clean(self):
        '''
        Flag bad data, based on prior researchers's analyses and our own identification of problematic data
        :return:
        :rtype:
        '''

        modificationVar = 'modificationStatus_' + str(self.yearDataYear)
        self.yearData[modificationVar] = ''
        cleanVar = 'cleaningStatus_' + str(self.yearDataYear)
        self.yearData[cleanVar] = 'Keep'

        if ((self.yearDataYear >= 1984 and self.yearDataYear <= 1993) or (self.yearDataYear >= 1999)):
            self.yearData.loc[(self.yearData[cleanVar] == 'Keep') &
                              (self.yearData['institutionLocationHH_' + str(self.yearDataYear)].ne("")) &
                              (~self.yearData['institutionLocationHH_' + str(self.yearDataYear)].isna())
            , cleanVar] = "HH in Institution"

        # This doesn't do anything...
        # self.yearData.loc[(self.yearData[cleanVar] == 'Keep') &
        #                  (self.yearData['familyId1968_' + str(self.yearDataYear)] == 9999), cleanVar] = "HH is NA or Shared HH"

        if (self.useOriginalSampleOnly):
            # For the original sample, the only valid family ids are < 3000 and 5000-7000
            self.yearData.loc[(self.yearData[cleanVar] == 'Keep') &
                              (~((self.yearData['familyId1968_' + str(self.yearDataYear)] < 3000) | (
                        (self.yearData['familyId1968_' + str(self.yearDataYear)] > 5000) & (self.yearData['familyId1968_' + str(self.yearDataYear)] < 7000))
                                )), cleanVar] = "Not Original PSID Sample"
        else: # If we're using the 'enriched' sample, we still want to remove the short-lived, non-representative 'Latino Sample'
            # Latino Sample 1968 Ids are > 7000
            self.yearData.loc[((self.yearData[cleanVar] == 'Keep') &
                               (self.yearData['familyId1968_' + str(self.yearDataYear)] > 7000)
                                ), cleanVar] = "Non-representative Latino Sample"


        # Juster, Smith and Stafford (1998) say: “The PSID other savings number in 1984 is unusually high. This is due to a few large outlier values that appear to be miscodes.” (p. 17, footnote 12). 
        # There are 7 cases where the other savings value is giving as $9 million, which is an extreme outlier. These observations are excluded from the 1984 cross-sectional sample. 
        if self.yearDataYear == 1984:
            self.yearData.loc[(self.yearData[cleanVar] == 'Keep') & ((self.yearData.valueOfOtherAssets_Net_1984 > 5000000)), cleanVar] = "Invalid High Other Assets - Juster et al 1998"
         # else:
        #    self.dta.loc[(self.dta['valueOfOtherAssets_Net_' + str(analysisYear)] > 5000000), 'valueOfOtherAssets_Net_' + str(analysisYear)]

        # There are some cases of clearly mislabeled data. Clear them
        self.yearData.loc[self.yearData['retirementContribRateR_' +  str(self.yearDataYear)] > 0.5,  modificationVar] = "Contribution over .5"
        self.yearData.loc[self.yearData['retirementContribRateR_' +  str(self.yearDataYear)] > 0.5, 'retirementContribHH_' +  str(self.yearDataYear) ] = np.NaN
        self.yearData.loc[self.yearData['retirementContribRateR_' +  str(self.yearDataYear)] > 0.5, 'retirementContribRateR_' +  str(self.yearDataYear) ] = np.NaN

        self.yearData.loc[self.yearData['retirementContribRateS_' +  str(self.yearDataYear)] > 0.5,  modificationVar] = "Contribution over .5"
        self.yearData.loc[self.yearData['retirementContribRateS_' +  str(self.yearDataYear)] > 0.5, 'retirementContribHH_' +  str(self.yearDataYear) ] = np.NaN
        self.yearData.loc[self.yearData['retirementContribRateS_' +  str(self.yearDataYear)] > 0.5, 'retirementContribRateS_' +  str(self.yearDataYear) ] = np.NaN

        # And a few negative Dividends (like 1986 DividendS)
        # Dividends arent used currently, so not important here
        # self.yearData.loc[self.yearData['DividendsR_' +  str(self.yearDataYear)] < 0, 'DividendsR' ] = 0
        # self.yearData.loc[self.yearData['DividendsS_' +  str(self.yearDataYear)] < 0, 'DividendsS' ] = 0


    # Note, this should be calculated on the filtered groups (after irrelevant pops are excluded)
    def processCrossSectional_CreateCSSegmentBins(self):
        '''
        Create Segments for age, educational and martial status  in the single-year data
        :return:
        :rtype:
        '''
        yrStr = str(self.yearDataYear)
        self.yearData['ageGroup_' + yrStr] = pd.cut(self.yearData['ageR_' + yrStr],bins=[0,25,35,45, 55, 65, 1000], right= False, labels=['0to24','25to34','35to44','45to54','55to64', '65to100'])
        
        # These are LONGITUDINAL bins -- and, since they are quantiles, need the full cleaning and processing of the longitudinal data
        # self.yearData['incomeGroup_PreTaxReal_' + self.inflatedEnd] = wQCut(self.yearData, 'averageRealBeforeTaxIncome_AllYears_' + self.inflatedTimespan, 'LongitudinalWeightHH_' + self.eyStr, 4)
        # self.yearData['incomeGroup_PostTaxReal_' + self.inflatedEnd] = wQCut(self.yearData, 'averageRealAfterTaxIncome_AllYears_' + self.inflatedTimespan, 'LongitudinalWeightHH_' + self.eyStr, 4)
          
        # From PSID (1994)
        # Values in the range 1-16 represent the actual grade of school completed; e.g., a value of
        # 8 indicates that the Head completed the eighth grade. A code value of 17 indicates that
        # the Head completed at least some postgraduate work.
        self.yearData['educationGroup_' + yrStr] = pd.cut(self.yearData['educationYearsR_' + yrStr],
                        bins=[0,12,13,16, 17, 100],
                        right= False,
                        labels=['Less than High School (0-11)','High School Graduate (12)',
                                'Some College (13-15)', 'College Grad (16)', 'Post College (17+)'])

        # TODO: revisit. should this be the formal marriage or marriage + cohabiting?
        self.yearData['maritalStatusGroup_' + yrStr] = self.yearData['martialStatusR_' + yrStr].copy()
        self.yearData.loc[ ~(self.yearData['maritalStatusGroup_' + yrStr] == 'Married'), 'maritalStatusGroup_' + yrStr] = 'Not married'
        # self.dta.martialStatusGenR.replace({1:'MarriedOrCohabit', 2: 'Never Married', 3: 'Widowed', 4: 'Divorced/Annulled', 5: 'Separated',8: None, 9: None}, inplace=True)

    def cleanData_Longitudinal_PrepForSavingsCalcAnalysis(self):
        '''
        On the two-period longitudinal data, filter out bad or irrelevant data.
        In particular, remove:
        1) Remove changes in  head of HH
        2) HH is < 20 or > 70
        3) Top 1% and bottom 1% by change in wealth

        :return:
        :rtype:
        '''

        cleanVar = 'cleaningStatus_' + self.timespan
        self.dta[cleanVar] = 'Keep'

        self.dta.loc[(self.dta[cleanVar] == 'Keep') & (self.dta['interviewId_' + self.syStr] == 0), cleanVar] = 'Not In Both Waves'
        self.dta.loc[(self.dta[cleanVar] == 'Keep') & (self.dta['interviewId_' + self.eyStr] == 0), cleanVar] = 'Not In Both Waves'

        # if (self.endYear == 1989 and self.startYear == 1984):
        #     self.dta.loc[(self.dta[cleanVar] == 'Keep') & (~(self.dta['ChangeInCompositionFU_1989FiveYear_1989'].isin([0, 1, 2]))), cleanVar] = 'Not same Head'
        # else:
        self.dta.loc[(self.dta[cleanVar] == 'Keep') & (self.dta['ChangeInHeadFU_' + self.timespan]), cleanVar] = 'Not same Head'

        self.dta[cleanVar].value_counts(dropna=False) # Should have 5180 left in 1989

        # For trimmed samples, the top and bottom 1 percent of the distribution of changes in wealth in each five year period is excluded.
        nwVar = 'changeInRealNetWorthWithHomeAnd401k_' + self.inflatedTimespan
        weightVar = 'LongitudinalWeightHH_' + self.eyStr

        # Handle Outliers by Wealth. We have two different routes. One to replicate Gittelman et al, one we use here
        if True:
            topThreshold_ChangeInNW = np.percentile(self.dta.loc[(self.dta[cleanVar] == 'Keep'),nwVar], 99)
            bottomThreshold_ChangeInNW = np.percentile(self.dta.loc[(self.dta[cleanVar] == 'Keep'), nwVar], 1)
            
            # An optional flag for the analysis: Only in doing averages do we want to drop these. Medians are fine as is.
            wealthCleanVar = 'cleaningStatus_Wealth_' + self.timespan
            self.dta.loc[(self.dta[cleanVar] == 'Keep') & (self.dta[nwVar] > topThreshold_ChangeInNW), wealthCleanVar] = 'Trim_WealthChangeHigh'
            self.dta.loc[(self.dta[cleanVar] == 'Keep') & (self.dta[nwVar] < bottomThreshold_ChangeInNW), wealthCleanVar] = 'Trim_WealthChangeLow'
        elif False:
            # It appears that Gittleman used the unweighted percentiles, above, not weighted percentiles
            thresholds_ChangeInNW = wPercentile_ForSeries(values = self.dta.loc[(self.dta[cleanVar] == 'Keep'), nwVar], 
                                                quantiles = [.01,.99], sample_weight = self.dta.loc[(self.dta[cleanVar] == 'Keep'), weightVar])
            bottomThreshold_ChangeInNW = thresholds_ChangeInNW[0]
            topThreshold_ChangeInNW = thresholds_ChangeInNW[1]
                
            self.dta.loc[(self.dta[cleanVar] == 'Keep') & (self.dta[nwVar] > topThreshold_ChangeInNW), cleanVar] = 'Trim_WealthChangeHigh'
            self.dta.loc[(self.dta[cleanVar] == 'Keep') & (self.dta[nwVar] < bottomThreshold_ChangeInNW), cleanVar] = 'Trim_WealthChangeLow'

        if self.startYear == 1984:
            self.dta.loc[(self.dta[cleanVar] == 'Keep') & (self.dta.valueOfOtherAssets_Net_1984 > 5000000), cleanVar] = 'Other Savings Too High'

        # Filter based on RECEIVED income.  If the person doesn't have income, savings rates don't mean the same thing.
        # It's a rough measure, but we'll define 'any income' as 50% of time at minimum wage for 52 weeks in the year
        # It's rough becuase  inflation and the federal minimum wage don't move in lockstep.
        self.dta.loc[(self.dta[cleanVar] == 'Keep') & (self.dta['averageRealBeforeTaxIncome_AllYears_' + self.inflatedTimespan] < 7540), cleanVar] = 'IncomeTooLow'
        # Filter based on AGE.
        self.dta.loc[(self.dta[cleanVar] == 'Keep') & (self.dta['ageR_' + self.eyStr] < 20), cleanVar] = 'Head too Young'
        self.dta.loc[(self.dta[cleanVar] == 'Keep') & (self.dta['ageR_' + self.eyStr] > 70), cleanVar] = 'Head too Old'


    def calcAverageMoneyIncome(self):
        
        # Kick out if we aren't looking at a time frame
        if (self.startYear == self.endYear):
            self.dta['averageRealBeforeTaxIncome_AllYears_' + self.inflatedTimespan] = self.dta['inflatedPreTaxIncome_' + self.inflatedStart]
            self.dta['averageNominalIncome_AllYears_' + self.timespan] = self.dta['totalIncomeHH_' + self.syStr]                     
            self.dta['averageRealAfterTaxIncome_AllYears_' + self.inflatedTimespan] = self.dta['inflatedAfterTaxIncome_' + self.inflatedStart]                     
            self.dta['averageNominalAfterTaxIncome_AllYears_' + self.timespan] = self.dta['afterTaxIncomeHH_' + self.syStr]
            return 
        
        self.dta['averageRealBeforeTaxIncome_AllYears_' + self.inflatedTimespan] = 0
        self.dta['averageNominalIncome_AllYears_' + self.timespan] = 0                     
        self.dta['averageRealAfterTaxIncome_AllYears_' + self.inflatedTimespan] = 0                     
        self.dta['averageNominalAfterTaxIncome_AllYears_' + self.timespan] = 0                     
        
        if (self.endYear <= 1997):
            # Dynan's Analysis, the authors look at 84-88 income (survey years 85-89) NOT survey years 84-89
            yearsToAverageOver = list(range(self.startYear+1, self.endYear +1))
        else:
            yearsToAverageOver = self.yearsWithFamilyData.copy()
            
        numYearsOfData = len(yearsToAverageOver)
             
        for year in yearsToAverageOver:
            if (year == 1994):
                numYearsOfData = numYearsOfData - 1 # Skip it and use the average over the other years; When Gittleman did the analysis, there was no year-1993 (survey 1994) income data 
            else:
                yrStr = str(year)
                inflatedYearStr = str(year) + '_as_' + self.tyStr
                
                self.dta['averageRealBeforeTaxIncome_AllYears_' + self.inflatedTimespan] = self.dta['averageRealBeforeTaxIncome_AllYears_' + self.inflatedTimespan].add(self.dta['inflatedPreTaxIncome_' + inflatedYearStr], fill_value = 0)
                self.dta['averageNominalIncome_AllYears_' + self.timespan] = self.dta['averageNominalIncome_AllYears_' + self.timespan].add(self.dta['totalIncomeHH_' + yrStr], fill_value = 0)

                self.dta['averageRealAfterTaxIncome_AllYears_' + self.inflatedTimespan] = self.dta['averageRealAfterTaxIncome_AllYears_' + self.inflatedTimespan].add(self.dta['inflatedAfterTaxIncome_' + inflatedYearStr], fill_value = 0)
                self.dta['averageNominalAfterTaxIncome_AllYears_' + self.timespan] = self.dta['averageNominalAfterTaxIncome_AllYears_' + self.timespan].add(self.dta['afterTaxIncomeHH_' + yrStr], fill_value = 0)

        self.dta['averageRealBeforeTaxIncome_AllYears_' + self.inflatedTimespan] =self.dta['averageRealBeforeTaxIncome_AllYears_' + self.inflatedTimespan] / numYearsOfData
        self.dta['averageNominalIncome_AllYears_' + self.timespan] =self.dta['averageNominalIncome_AllYears_' + self.timespan] / numYearsOfData
        self.dta['averageRealAfterTaxIncome_AllYears_' + self.inflatedTimespan] =self.dta['averageRealAfterTaxIncome_AllYears_' + self.inflatedTimespan] / numYearsOfData
        self.dta['averageNominalAfterTaxIncome_AllYears_' + self.timespan] =self.dta['averageNominalAfterTaxIncome_AllYears_' + self.timespan] / numYearsOfData


        ################
        # Inflate values that ONLY are relevant for start-end comparisons
        ################
        # Calc changes -- assumes all are inflated to common year already 
        self.dta['changeInRealNetWorth_' + self.inflatedTimespan] = self.dta['inflatedNetWorthWithHome_' + self.inflatedEnd].sub(self.dta['inflatedNetWorthWithHome_' + self.inflatedStart], fill_value=0)
        self.dta['changeInRealNetWorthWithHomeAnd401k_' + self.inflatedTimespan] = self.dta['inflatedNetWorthWithHomeAnd401k_' + self.inflatedEnd].sub(self.dta['inflatedNetWorthWithHomeAnd401k_' + self.inflatedStart], fill_value=0)



    def calcIfValueOnMoveAndChangedHeadAtAnyPoint(self):    

        modificationVar = 'modificationStatus_' + self.timespan
        self.dta[modificationVar] = ''

        self.dta['ChangeInHeadFU_' + self.timespan] = False
        
        # Changes on Move
        self.dta['House_ValueIncrease_WhenMoving_' + self.inflatedTimespan] = None
        self.dta['House_TotalChangeInMortgageDebt_WhenMoving_' + self.inflatedTimespan] = None

        # Changes without Move
        self.dta['House_TotalChangeInMortgageDebt_WhenNotMoving_' + self.inflatedTimespan] = None
        self.dta['House_ValueIncrease_WhenNotMoving_' + self.inflatedTimespan] = None
        priorOwnRentStatus = None

        for year in (self.yearsWithFamilyData.copy()):
            inflationPriorYear =  self.inflator.getInflationFactorBetweenTwoYears(year-self.timeStep, self.toYear)
            inflationGivenYear =  self.inflator.getInflationFactorBetweenTwoYears(year, self.toYear)
            movedVar = 'MovedR_' + str(year)
            housingStatusVar = 'hasHouse_' + str(year)
            
            if (year >= (self.startYear + self.timeStep)):
                
                # Following Dynan, flag people who moved but didn't report it
                mask = (self.dta[movedVar] == False) & (~(self.dta[housingStatusVar].isna())) & \
                       (~(priorOwnRentStatus.isna())) & \
                       (self.dta[housingStatusVar].ne(priorOwnRentStatus))

                numToUpdate = len(self.dta.loc[mask])
                print ("fixing " + str(numToUpdate) + " move statuses")
                if (numToUpdate > 400):
                    warnings.warn("something ain't right here")

                '''
                tmp1 = self.dta.loc[mask, ['MovedR_1992', movedVar, 'MovedR_1994', 'hasHouse_1992', housingStatusVar, 'hasHouse_1994', 'valueOfHouse_Gross_1992', 'valueOfHouse_Gross_1993', 'valueOfHouse_Gross_1994', 'familyInterviewId_1992', 'familyInterviewId_1993', 'familyInterviewId_1994',
                                           'constantFamilyId', 'constantIndividualID']]
                tmp1.to_csv(os.path.join(self.baseDir, "tmpTest.csv"))

                tmp2 = self.dta[['MovedR_1992', movedVar, 'MovedR_1994', 'hasHouse_1992', housingStatusVar, 'hasHouse_1994', 'valueOfHouse_Gross_1992', 'valueOfHouse_Gross_1993', 'valueOfHouse_Gross_1994', 'familyInterviewId_1992', 'familyInterviewId_1993', 'familyInterviewId_1994',
                                           'constantFamilyId', 'constantIndividualID']]
                tmp2.to_csv(os.path.join(self.baseDir, "tmpTestFull.csv"))

                '''
                # tmp2 = priorOwnRentStatus[mask]
                # tmp1 = tmp1.join(tmp2)

                self.dta.loc[mask, modificationVar] = self.dta.loc[mask, modificationVar] + "Move Status Changed to True;"
                self.dta.loc[mask, movedVar]= True

                # if the person moved, add any changes in house value from the move
                if (self.dta[movedVar].sum() >= 1): # ie not all nones
                    self.dta.loc[self.dta[movedVar] == True, 'House_ValueIncrease_WhenMoving_' + self.inflatedTimespan] = self.dta.loc[self.dta[movedVar] == True, 'House_ValueIncrease_WhenMoving_' + self.inflatedTimespan].fillna(0) \
                        .add(self.dta.loc[self.dta[movedVar] == True, 'valueOfHouse_Gross_' + str(year)] * inflationGivenYear, fill_value=0) \
                        .sub(self.dta.loc[self.dta[movedVar] == True, 'valueOfHouse_Gross_' + str(year-self.timeStep)] * inflationPriorYear, fill_value=0)
                        
                    self.dta.loc[ (self.dta[movedVar] == True), 'House_TotalChangeInMortgageDebt_WhenMoving_' + self.inflatedTimespan] = self.dta.loc[ (self.dta[movedVar] == True), 'House_TotalChangeInMortgageDebt_WhenMoving_' + self.inflatedTimespan].fillna(0) \
                        .add(self.dta.loc[ (self.dta[movedVar] == True), 'valueOfHouse_Debt_' + str(year)] * inflationGivenYear, fill_value=0) \
                        .sub(self.dta.loc[ (self.dta[movedVar] == True), 'valueOfHouse_Debt_' + str(year-self.timeStep)] * inflationPriorYear, fill_value=0)

                else:
                    raise Warning("Hmm... Missing moving data")
                
                # if the person DIDN'T MOVE, add up the cumulative changes in principal and house value
                self.dta.loc[ ~(self.dta[movedVar] == True), 'House_ValueIncrease_WhenNotMoving_' + self.inflatedTimespan] = self.dta.loc[ ~(self.dta[movedVar] == True), 'House_ValueIncrease_WhenNotMoving_' + self.inflatedTimespan].fillna(0) \
                    .add(self.dta.loc[ ~(self.dta[movedVar] == True), 'valueOfHouse_Gross_' + str(year)] * inflationGivenYear, fill_value=0) \
                    .sub(self.dta.loc[ ~(self.dta[movedVar] == True), 'valueOfHouse_Gross_' + str(year-self.timeStep)] * inflationPriorYear, fill_value=0)
                self.dta.loc[ ~(self.dta[movedVar] == True), 'House_TotalChangeInMortgageDebt_WhenNotMoving_' + self.inflatedTimespan] = self.dta.loc[ ~(self.dta[movedVar] == True), 'House_TotalChangeInMortgageDebt_WhenNotMoving_' + self.inflatedTimespan].fillna(0) \
                    .add(self.dta.loc[ ~(self.dta[movedVar] == True), 'valueOfHouse_Debt_' + str(year)] * inflationGivenYear, fill_value=0) \
                    .sub(self.dta.loc[ ~(self.dta[movedVar] == True), 'valueOfHouse_Debt_' + str(year-self.timeStep)] * inflationPriorYear, fill_value=0)

            priorOwnRentStatus = self.dta[housingStatusVar].copy()

            if (year > self.startYear): # Look at changes in composition SINCE start, not from start to year prior
                changeVar = 'ChangeInCompositionFU_' + str(year)
                if (self.dta[changeVar].sum() > 1): # ie not all nones
                    self.dta.loc[~(self.dta['ChangeInHeadFU_' + self.timespan]) & ~(self.dta[changeVar].isin([0, 1, 2])), 'ChangeInHeadFU_' + self.timespan] = True




    def executeForTimespan(self, startYear, endYear, toYear):
        self.clearData()
        self.setPeriod(startYear, endYear, toYear)
        self.readRawData()
                                
        self.calcIfValueOnMoveAndChangedHeadAtAnyPoint()
        self.calcAverageMoneyIncome()
        self.cleanData_Longitudinal_PrepForSavingsCalcAnalysis()

        self.dta = InequalityAnalysisBase.selectiveReorder(self.dta,
                                                           ['cleaningStatus_' + self.timespan,
                                     'modificationStatus_' + self.timespan,
                                     'familyInterviewId_' + str(self.syStr),
                                     'familyInterviewId_' + str(self.eyStr),
                                     'raceR_' + self.syStr,
                                     'inflatedNetWorthWithHome_' + self.inflatedStart,
                                     'changeInRealNetWorth_' + self.inflatedTimespan,
                                     'changeInRealNetWorthWithHomeAnd401k_' + self.inflatedTimespan,
                                     'inflatedAfterTaxIncome_' + self.inflatedStart,
                                    ], alphabetizeTheOthers = True)
        self.saveLongitudinalData()

    def doIt(self, useCleanedDataOnly = True):
        self.useCleanedDataOnly = useCleanedDataOnly
        toYear = 2019
        # yearsWealthDataCollected = [1989, 1994]
        startYear = self.yearsWealthDataCollected[0]
        
        for endYear in self.yearsWealthDataCollected[1:]:            
            # Do the core analysis: change in wealth and savings rates over time
            self.executeForTimespan(startYear, endYear, toYear)
            # Get ready for next year
            startYear = endYear

                 

''' Allow execution from command line, etc'''    
if __name__ == "__main__":
    analyzer = InequalityDataPrep(familyBaseFileNameWithPath = 
                             os.path.join('C:/dev/sensitive_data/InvestorSuccess/Inequality',
                                          'finalInputPSID', "extractedPSID_Mapped_Recoded_"),
            individualBaseFileNameWithPath = os.path.join('C:/dev/sensitive_data/InvestorSuccess/Inequality',
                                          'finalInputPSID', "extractedPSID_Individual_Mapped_Recoded"))
    analyzer.doIt()
