import pandas as pd
import os
import Replication.ReplicationAnalyzer as ReplicationAnalyzer
import DataQuality.CrossSectionalTester as CrossSectionalTester

from Survey.SurveyFunctions import *
import Inflation.NIPA_InflationReader as NIPA_InflationReader
import math

''' To replicate Dynan, Skinner & Zeldes study:
      
    Active savings is :
        Based on Ming Ching Luoh and Stafford's PSID Article "Active Saving, 1984-1989"
        Modified by Juster et al 2001
        and Summarized in Dynan, Skinner & Zeldes 
        1) Active Savings = Change in net wealth - capital gains for housing and financial assets, inheritance, gifts, 
            - assets(-debt) brought into household, + assets(-debt)  taken out of household
            THEN Correct for inflation and reporting error on moving homes,following Juster et al 2001
        2) Savings Rate = Active Savings / 5* average real income

    Which we implement as:
        Net Wealth (per above): {S217 NetWorth}
        Capital Gains for Housing:   A9_Y2 - A9_Y1 {V16324 valueOfHouse_Gross}   [Ie, not imputed Home Equity A220 
        Capital Gains for Financial Assets  {S205 valueOfCheckingAndSavings_Net} + {S211 valueOfBrokerageStocks_Net} + MAYBE S215?
        inheritance, gifts {V17384 LargeGift_1_AmountHH} + Maybe other 2nd, third etc gifts?
        assets(-debt) brought into household {V17377 PersonMovedIn_SinceLastQYr_AssetsMovedIn} {V17379 PersonMovedIn_SinceLastQYr_DebtsMovedIn}
        assets(-debt)  taken out of household {V17371 PersonMovedOut_SinceLastQYr_AssetsMovedOut} {V17373 PersonMovedOut_SinceLastQYr_DebtsMovedOut} 
'''


class DynanAnalysis(ReplicationAnalyzer.InequalityAnalyzer):
    
    def __init__(self, baseDir, familyInputSubDir, familyBaseName, individualInputSubDir, individualBaseName, outputSubDir):
        super().__init__(baseDir, familyInputSubDir, familyBaseName, individualInputSubDir, individualBaseName, outputSubDir, 
                         yearsToInclude = None) # Not used
        self.useOriginalSampleOnly = True
    
        
    def calcAfterTaxIncome(self, includeIntermediateYears=True):
        ''' 2. Disposable Income. 
        Disposable income is constructed by subtracting Federal taxes paid by the head and wife and 
        Federal taxes paid by other members of the family unit from total family money income. 
        Total family money income is the sum of taxable income of the head and wife, taxable income 
        of other members of the family unit, transfers of the head and wife, and transfers of other 
        members of the family unit. 
        
        Taxes paid are estimated by the PSID staff based on taxable income, 
        number of dependents and exemptions, filing status, estimated standard and itemized deductions, 
        estimated earned income tax credits, and estimated elderly tax credits. 
        
        All nominal components 
        of disposable income are deflated using the implicit price deflator described above. 
        
        Average disposable income is calculated for 1984-88 (1985-89 survey years). We calculate an 
        additional measures of average disposable income to use with the broader saving measure 
        described above. 
        
        This measure starts with the above measure of disposable income and adds
        # MISSING  
        1) one half of Social Security saving to average disposable income (1984-88), to correct 
        for the fact that the employer contribution to Social Security is not measured in the 
        conventional definition of income, but is measured as part of our augmented Social Security 
        saving, and 
        2) the imputed employer-contribution to defined benefit and/or defined contribution plans, 
        for the same reason.
        '''
        if includeIntermediateYears:
            yearRange = (self.yearsWithFamilyData.copy())
        else:
            yearRange = [self.startYear, self.endYear]

        for year in yearRange:
            yr = str(year)
        
            if (year >= 1970 and year <= 1991):
                self.dta['FederalIncomeTaxesHH_' + yr] = self.dta['FederalIncomeTaxesRS_' + yr].add(self.dta['FederalIncomeTaxesO_' + yr], fill_value=0)  
                self.dta['afterTaxIncomeHH_' + yr] = self.dta['totalIncomeHH_' + yr].sub(self.dta['FederalIncomeTaxesHH_' + yr], fill_value=0)  
            else:
                self.dta['afterTaxIncomeHH_' + yr] = self.dta['totalIncomeHH_' + yr].sub(self.dta['fiitax_' + yr], fill_value=0)
                     
        # Make some adjustments for strange extra data fields that Dynan used that aren't part of main sequence   
        if self.startYear == 1984 and self.endYear == 1989:
            self.dta['NetWorthWithHome_1989'] = self.dta['NetWorth_1989Only_1989']
            self.dta['NetWorthWithHome_1984'] = self.dta['NetWorth_1984_AsOf1989_1989']
        if self.startYear == 1989 and self.endYear == 1994:
            self.dta['NetWorthWithHome_1989'] = self.dta['NetWorth_1989Only_1989']

    def inflateValues(self, includeIntermediateYears=True):
        if includeIntermediateYears:
            yearRange = (self.yearsWithFamilyData.copy())
        else:
            yearRange = [self.startYear, self.endYear]
        
        ################
        # Inflate values that COULD include intermediate years
        ################
        nipa = NIPA_InflationReader.NIPAInflationReader() 
        # cpi = CPI_InflationReader.CPIInflationReader() 
        for year in yearRange:
            yr = str(year)
            timespan = yr + '_as_' + self.tyStr
            inflationGivenYear =  nipa.getInflationFactorBetweenTwoYears(year, self.toYear)
            inflationLagYear =  nipa.getInflationFactorBetweenTwoYears(year-1, self.toYear-1)

            self.dta['inflatedNetWorthWithHome_' + timespan] = self.dta['NetWorthWithHome_' + yr] * inflationGivenYear
            self.dta['inflatedAfterTaxIncome_' + timespan] = self.dta['afterTaxIncomeHH_' + yr] * inflationLagYear 
            
        ################
        # Inflate values that ONLY are relevant for start-end comparisons
        ################
        # Calc changes -- assumes all inflated to common year already 
        self.dta['changeInRealNetWorth_'      + self.inflatedTimespan] = self.dta['inflatedNetWorthWithHome_' + self.inflatedEnd].sub(self.dta['inflatedNetWorthWithHome_' + self.inflatedStart], fill_value=0)
        self.dta['averageRealAfterTaxIncome_StartEndYears_' + self.inflatedTimespan] = (self.dta['inflatedAfterTaxIncome_' + self.inflatedEnd].add(self.dta['inflatedAfterTaxIncome_' + self.inflatedStart], fill_value=0))/2.0
        
    def calcAverageMoneyIncome(self):
        self.dta['averageRealAfterTaxIncome_AllYears_' + self.inflatedTimespan] = 0                     
        self.dta['yearsOfAfterTaxIncomeData_' + self.inflatedTimespan] = 0                     
        self.dta['yearsOfNonZeonAfterTaxIncomeData_' + self.inflatedTimespan] = 0
        
        # TODO -- handle Missing income data for 1993?
        
        if (self.endYear <= 1997):
            # Dyan's Analysis, the authors look at 84-88 income (survey years 85-89) NOT survey years 84-89
            yearsToAverageOver = list(range(self.startYear+1, self.endYear +1))
        else:
            yearsToAverageOver = self.yearsWithFamilyData.copy()
        numYearsOfData = len(yearsToAverageOver)
             
        for year in yearsToAverageOver:
            inflatedYear = str(year) + '_as_' + self.tyStr
            self.dta['yearsOfAfterTaxIncomeData_' + self.inflatedTimespan] = self.dta['yearsOfAfterTaxIncomeData_' + self.inflatedTimespan].add(self.dta['inflatedAfterTaxIncome_' + inflatedYear].isna() == True)                     
            self.dta['yearsOfNonZeonAfterTaxIncomeData_' + self.inflatedTimespan] = self.dta['yearsOfNonZeonAfterTaxIncomeData_' + self.inflatedTimespan].add(~self.dta['inflatedAfterTaxIncome_' + inflatedYear].isna() & (self.dta['inflatedAfterTaxIncome_' + inflatedYear] != 0))                     
            self.dta['averageRealAfterTaxIncome_AllYears_' + self.inflatedTimespan] = self.dta['averageRealAfterTaxIncome_AllYears_' + self.inflatedTimespan].add(self.dta['inflatedAfterTaxIncome_' + inflatedYear], fill_value = 0)
        self.dta['averageRealAfterTaxIncome_AllYears_' + self.inflatedTimespan] =self.dta['averageRealAfterTaxIncome_AllYears_' + self.inflatedTimespan] / numYearsOfData                      
        
    def getReferenceAgeVar(self):
        if self.endYear <= 1997:
            halfDuration = math.ceil(self.duration/2) 
            return 'ageR_' + str(self.startYear + halfDuration)
        else:
            return 'ageR_' + str(self.endYear) # TODO -- increment in the data here 
    
    def calcSavingsRate_NetWorthChange(self):
        # First, we use the change in real net worth Divided by the average, real after federal tax, money income for the period.
        self.dta['savingsRateByNetWorth_' + self.inflatedTimespan] = (self.dta['changeInRealNetWorth_' + self.inflatedTimespan] \
                                                         / self.dta['averageRealAfterTaxIncome_AllYears_' + self.inflatedTimespan]) / self.duration

 
    def calcSavingsRate_ActiveSavings(self):
        '''1) Active Savings = Change in net wealth - capital gains for housing and financial assets, inheritance, gifts, 
                - assets(-debt) brought into household, + assets(-debt)  taken out of household
                THEN Correct for inflation and reporting error on moving homes,following Juster et al 2001
            2) Savings Rate = Active Savings / 5* average real income
    
        '''

        cpi = NIPA_InflationReader.NIPAInflationReader() 
        totalInflationStartToEndYear =  cpi.getInflationFactorBetweenTwoYears(self.startYear, self.endYear)
        totalInflationEndToInflatedYear =  cpi.getInflationFactorBetweenTwoYears(self.endYear, self.toYear)
        totalInflationStartToInflatedYear =  cpi.getInflationFactorBetweenTwoYears(self.startYear, self.toYear)

        # "For the flow saving variables, we deflate the nominal variables using the (harmonic) average of the price level over the relevant five years"
        inflationForFlow = (((totalInflationStartToEndYear - 1)/ 2) + 1) * totalInflationEndToInflatedYear 
        # "For the change-in-stock variables (house value, mortgage, and wealth variables), we deflate the nominal level in each year by the price index for that year, and then take the change in this real value." 
        inflationForStock_StartOfPeriod = totalInflationStartToInflatedYear
        inflationForStock_EndOfPeriod = totalInflationEndToInflatedYear

        # Before our major calc, fill in missing data
        varsUsed = ['PrivateRetirePlan_SinceLastQYr_AmountMovedIn_' + self.eyStr, 'PrivateRetirePlan_SinceLastQYr_AmountMovedOut_' + self.eyStr,
            'CostOfMajorHomeRenovations_' + self.eyStr,
            'OtherRealEstate_SinceLastQYr_AmountBought_' + self.eyStr, 'OtherRealEstate_SinceLastQYr_AmountSold_' + self.eyStr,
            'BrokerageStocks_SinceLastQYr_AmountBought_' + self.eyStr, 'BrokerageStocks_SinceLastQYr_AmountSold_' + self.eyStr,
            'Business_SinceLastQYr_AmountBought_' + self.eyStr, 'Business_SinceLastQYr_AmountSold_' + self.eyStr,
            'PersonMovedIn_SinceLastQYr_AssetsMovedIn_'   + self.eyStr, 'PersonMovedIn_SinceLastQYr_DebtsMovedIn_' + self.eyStr,
            'PersonMovedOut_SinceLastQYr_AssetsMovedOut_'   + self.eyStr, 'PersonMovedOut_SinceLastQYr_DebtsMovedOut_' + self.eyStr,
            
            'largeGift_All_AmountHH_' + self.eyStr,
            'House_ValueIncreaseOnMoving_' + self.timespan,
            'valueOfVehicle_Net_' + self.eyStr, 'valueOfVehicle_Net_' + self.syStr,
            'valueOfCheckingAndSavings_Net_' + self.eyStr,'valueOfCheckingAndSavings_Net_' + self.syStr,
            'valueOfOtherAssets_Net_' + self.eyStr, 'valueOfOtherAssets_Net_' + self.syStr,
            'valueOfHouse_Debt_' + self.syStr, 'valueOfHouse_Debt_' + self.eyStr,
            'valueOfAllOtherDebts_Net_' + self.syStr, 'valueOfAllOtherDebts_Net_' + self.eyStr,
            'averageRealAfterTaxIncome_AllYears_' + self.inflatedTimespan,
            'averageRealAfterTaxIncome_StartEndYears_' + self.inflatedTimespan]

        # self.checkDataQuality(self.dta[varsUsed], "Vars used in ActiveWealthChange Calc", raiseIfMissing=True)
        
        # Most of our variables have lots of NAs.  They should all be filled to 0 - either with add(fill_value) or on the DF itself, as here 
        self.dta[varsUsed] = self.dta[varsUsed].fillna(value=0)
        

        self.dta['netMoveIn_' + self.inflatedTimespan] =  self.dta['PersonMovedIn_SinceLastQYr_AssetsMovedIn_'   + self.eyStr].sub(self.dta['PersonMovedIn_SinceLastQYr_DebtsMovedIn_' + self.eyStr], fill_value=0)
        self.dta['netMoveOut_' + self.inflatedTimespan] = self.dta['PersonMovedOut_SinceLastQYr_AssetsMovedOut_' + self.eyStr].sub(self.dta['PersonMovedOut_SinceLastQYr_DebtsMovedOut_' + self.eyStr], fill_value=0)

        # Main Calculation!
        self.dta['activeWealthChange_' + self.inflatedTimespan] = \
            inflationForFlow * \
            ( \
                self.dta['PrivateRetirePlan_SinceLastQYr_AmountMovedIn_' + self.eyStr] \
                - self.dta['PrivateRetirePlan_SinceLastQYr_AmountMovedOut_' + self.eyStr] \
                + self.dta['CostOfMajorHomeRenovations_' + self.eyStr] \
                + self.dta['OtherRealEstate_SinceLastQYr_AmountBought_' + self.eyStr] \
                - self.dta['OtherRealEstate_SinceLastQYr_AmountSold_' + self.eyStr] \

                + self.dta['Business_SinceLastQYr_AmountBought_' + self.eyStr] \
                - self.dta['Business_SinceLastQYr_AmountSold_' + self.eyStr] \

                + self.dta['BrokerageStocks_SinceLastQYr_AmountBought_' + self.eyStr] \
                - self.dta['BrokerageStocks_SinceLastQYr_AmountSold_' + self.eyStr] \
                          
                + self.dta['netMoveOut_' + self.inflatedTimespan] \
                - self.dta['netMoveIn_' + self.inflatedTimespan] \
                
                - self.dta['largeGift_All_AmountHH_' + self.eyStr] \
                + self.dta['House_ValueIncreaseOnMoving_' + self.timespan]) + \
             ( \
                self.dta['valueOfVehicle_Net_' + self.eyStr]*inflationForStock_EndOfPeriod \
                - self.dta['valueOfVehicle_Net_' + self.syStr]*inflationForStock_StartOfPeriod \
                
                + self.dta['valueOfCheckingAndSavings_Net_' + self.eyStr]*inflationForStock_EndOfPeriod \
                - self.dta['valueOfCheckingAndSavings_Net_' + self.syStr]*inflationForStock_StartOfPeriod \
    
                + self.dta['valueOfOtherAssets_Net_' + self.eyStr]*inflationForStock_EndOfPeriod \
                - self.dta['valueOfOtherAssets_Net_' + self.syStr]*inflationForStock_StartOfPeriod \
    
                + self.dta['valueOfHouse_Debt_' + self.syStr]*inflationForStock_StartOfPeriod \
                - self.dta['valueOfHouse_Debt_' + self.eyStr]*inflationForStock_EndOfPeriod \
    
                + self.dta['valueOfAllOtherDebts_Net_' + self.syStr]*inflationForStock_StartOfPeriod \
                - self.dta['valueOfAllOtherDebts_Net_' + self.eyStr]*inflationForStock_EndOfPeriod \
            )

        self.dta['activeSavingsRate_PerPerson_' + self.inflatedTimespan] = (self.dta['activeWealthChange_' + self.inflatedTimespan] / self.dta['averageRealAfterTaxIncome_AllYears_' + self.inflatedTimespan]) / self.duration
        varsToExpore = varsUsed + ['LongitudinalWeightHH_' + self.eyStr, 'activeWealthChange_' + self.inflatedTimespan, 'activeSavingsRate_PerPerson_' + self.inflatedTimespan, 'netMoveIn_' + self.inflatedTimespan, 'netMoveOut_' + self.inflatedTimespan, 'savingsRateByNetWorth_' + self.inflatedTimespan]
        
        if (self.startYear == 1984 and self.endYear == 1989):
            self.dta['activeSavingsRate_Person_Alt_' + self.inflatedTimespan] = (self.dta['ActiveSavings_PSID1989_' + self.eyStr] / self.dta['averageRealAfterTaxIncome_AllYears_' + self.inflatedTimespan]) / self.duration
            varsToExpore = varsToExpore + ['ActiveSavings_PSID1989_' + self.eyStr, 'activeSavingsRate_Person_Alt_' + self.inflatedTimespan]
             
        # Output summary stats on the data, to check everything is ok:
        cleanVar = 'cleaningStatus_' + self.eyStr
        tester = CrossSectionalTester.CrossSectionalTester(dta = self.dta.loc[self.dta[cleanVar] == 'Keep', varsToExpore].copy(),
                                                        dfLabel = "Vars used in ActiveWealthChange Calc" + str(self.timespan) + ")",
                                                        year = self.endYear,
                                                        varMapping = None,
                                                        ignoreUnmappedVars = True)

        if not os.path.exists(os.path.join(self.baseDir, self.outputSubDir)):
            os.makedirs(os.path.join(self.baseDir, self.outputSubDir))

        tester.exploreData(
            reportFileNameWithPathNoExtension = os.path.join(self.baseDir, self.outputSubDir, "CombinedDynan_ActiveWealthVars_" + self.inflatedTimespan),
            weightVar = "LongitudinalWeightHH_" + self.eyStr)
        tester.checkDataQuality(raiseIfMissing = False)
            
        # Alt Formation - should be approximately equal
        '''
        Which we implement as:
            Net Wealth (per above): {S217 NetWorth}
            Capital Gains for Housing:   A9_Y2 - A9_Y1 {V16324 valueOfHouse_Gross}   [Ie, not imputed Home Equity A220 
            Capital Gains for Financial Assets  {S205 valueOfCheckingAndSavings_Net} + {S211 valueOfBrokerageStocks_Net} + MAYBE S215?
            inheritance, gifts {V17384 LargeGift_1_AmountHH} + Maybe other 2nd, third etc gifts?
            assets(-debt) brought into household {V17377 PersonMovedIn_SinceLastQYr_AssetsMovedIn} {V17379 PersonMovedIn_SinceLastQYr_DebtsMovedIn}
            assets(-debt)  taken out of household {V17371 PersonMovedOut_SinceLastQYr_AssetsMovedOut} {V17373 PersonMovedOut_SinceLastQYr_DebtsMovedOut} 

        self.dta['capitalGains_Housing_' + timespan] = self.dta['valueOfHouse_Gross_' + self.eyStr]*inflationForStock_EndOfPeriod - self.dta['valueOfHouse_Gross_' + self.syStr]*inflationForStock_StartOfPeriod
        self.dta['capitalGains_Financial_' + timespan] = (self.dta['valueOfCheckingAndSavings_Net_' + self.eyStr] - self.dta['valueOfCheckingAndSavings_Net_' + self.syStr]*inflationForStock_StartOfPeriod) + (self.dta['valueOfBrokerageStocks_Net_' + self.eyStr] - self.dta['valueOfBrokerageStocks_Net_' + self.syStr]*inflationForStock_StartOfPeriod)
        self.dta['activeWealthChange_ViaNetWealth_' + timespan] = \ 
            self.dta['changeInRealNetWorth_' + timespan] \  
            - (self.dta['capitalGains_Housing_' + timespan] + self.dta['capitalGains_Financial_' + timespan] \ 
            + self.dta['largeGift_All_AmountHH_' + timespan]*inflationForFlow - self.dta['netMoveIn_' + timespan]) 
            + (self.dta['netMoveOut_' + timespan])
        self.dta['activeSavingsRate_ViaNetWealth_' + timespan] = (self.dta['activeWealthChange_ViaNetWealth_' + timespan] / self.dta['averageRealAfterTaxIncome_' + timespan]) / numYears
        '''  
        
    def createSegmentBins(self):
        # self.dta['dummyAggGroup'] = 'All' 
        refAgeVar = self.getReferenceAgeVar()
        self.dta['dynanAgeGroupMidPeriod_' + self.eyStr] = pd.cut(self.dta[refAgeVar],bins=[0,30,40,50, 60,1000], right= False, labels=['0to29','30to39','40to49','50to59', '60to100'])
        self.dta['dynanIncomeGroup_' + self.inflatedEnd] = wQCut(self.dta, 'averageRealAfterTaxIncome_AllYears_' + self.inflatedTimespan, 'LongitudinalWeightHH_' + self.eyStr, 5,)

         
    def cleanResults(self, preliminaryClean_beforeSavingsCalcAnalysis=False):
        ''' Some fields we can filter on BEFORE we do the analysis (which makes EDA much easier), and some we can only do AFTER'''
        '''
        From the unpublished data appendix:
        
        We restrict the sample to households that had the same head in all years from
        1984 to 1989 and who had no change in family composition affecting the head over that
        period (5180 remaining observations). We drop households that didn’t tell us if they had
        moved during any year from 1983-88 (24 dropped). We then drop households whose
        head was less than 30 years old in 1987 (757 dropped). For all but Table 7, we drop
        households whose head was older than 59 in 1987 (1125 dropped) and households
        whose head-spouse combination changed over the 1984-89 period (348 dropped). We
        then drop households whose total real after-tax money income in any year from 1984-
        88 was less than $1000 in 1994 dollars (for a total of 66 dropped), and households with
        the absolute value of active saving above $750,000 in 1994 dollars (6 observations
        dropped).
        '''
        
        '''
        Cleaning: "We...
        Drop households w/ active savings > 750k (1994 dollars)
        Drop households w/ missing data on active savings (1984-89)
        Drop households w/ change in head or spouse (1984-89)
        Drop households w/ real disposable income < 1000 (1984-89)
        
        For the regressions that included lagged or future earnings, we drop households for which they was 
        a change in the head or spouse during the relevant years 
        '''
        
        cleanVar = 'cleaningStatus_' + self.eyStr
        self.dta[cleanVar] = 'Keep'

        self.dta.loc[(self.dta[cleanVar] == 'Keep') & (self.dta['interviewId_' + self.syStr] == 0), cleanVar] = 'Not In Both Waves'
        self.dta.loc[(self.dta[cleanVar] == 'Keep') & (self.dta['interviewId_' + self.eyStr] == 0), cleanVar] = 'Not In Both Waves'

        if (self.endYear == 1989 and self.startYear == 1984):
            self.dta.loc[(self.dta[cleanVar] == 'Keep') & (~(self.dta['ChangeInCompositionFU_1989FiveYear_1989'].isin([0, 1, 2]))), cleanVar] = 'Not same Head'
        else:
            self.dta.loc[(self.dta[cleanVar] == 'Keep') & (self.dta['ChangeInHeadFU_' + self.timespan]), cleanVar] = 'Not same Head'

        self.dta[cleanVar].value_counts(dropna=False) # Should have 5180 left in 1989
        
        self.dta['Cleaning_Unconditional_MovedNotSure_' + self.eyStr ]  = self.dta['MovedNotSure_' + self.timespan]
        self.dta.loc[(self.dta[cleanVar] == 'Keep') & (self.dta['MovedNotSure_' + self.timespan]), cleanVar] = 'No data on moving' # 24
        
        
        refAgeVar = self.getReferenceAgeVar()
        self.dta['Cleaning_Unconditional_AgeUnder30_' + self.eyStr ]  = (self.dta[refAgeVar] < 30)
        self.dta.loc[(self.dta[cleanVar] == 'Keep') & (self.dta[refAgeVar] < 30), cleanVar] = 'Head under 30 in 1987' # 757
        self.dta['Cleaning_Unconditional_AgeOver59_' + self.eyStr ]  = (self.dta[refAgeVar] > 59)
        self.dta.loc[(self.dta[cleanVar] == 'Keep') & (self.dta[refAgeVar] > 59), cleanVar] = 'Head 60 or older in 1987' # 1125

        # ?? households whose head-spouse combination changed over the 1984-89 period (348 dropped).
 
        if (self.endYear == 1989 and self.startYear == 1984):
            self.dta['Cleaning_Unconditional_ChangeInSpouse_' + self.eyStr ]  = (self.dta['ChangeInCompositionFU_1989FiveYear_1989'].isin([2]))
            self.dta.loc[(self.dta[cleanVar] == 'Keep') & (self.dta['ChangeInCompositionFU_1989FiveYear_1989'].isin([2])), cleanVar] = 'Not same Wife'
        else:
            self.dta['Cleaning_Unconditional_ChangeInSpouse_' + self.eyStr ]  = (self.dta['ChangeInHeadSpouseComboFU_' + self.timespan])
            self.dta.loc[(self.dta[cleanVar] == 'Keep') & (self.dta['ChangeInHeadSpouseComboFU_' + self.timespan]), cleanVar] = 'Not same Wife'

        # Which years do we want to check income over?
        if (self.endYear <= 1997):
            # Dyan's Analysis, the authors look at 84-88 income (survey years 85-89) NOT survey years 84-89
            yearsToInclude = list(range(self.startYear+1, self.endYear +1))
        else:
            yearsToInclude = self.yearsWithFamilyData.copy()

        # Look for income that was too low
        for year in yearsToInclude: # range(self.startYear+1, self.endYear + 1):  # Survey years 85 to 89, NOT 84 to 89 
            yr = str(year)
            inflatedYear = yr + '_as_' + self.tyStr
            self.dta['Cleaning_Unconditional_IncomeToLow_' + yr ]  = (self.dta['inflatedAfterTaxIncome_' + inflatedYear] < 1000)
            self.dta.loc[(self.dta[cleanVar] == 'Keep') & (self.dta['inflatedAfterTaxIncome_' + inflatedYear] < 1000), cleanVar] = 'IncomeTooLow' 

        # Check for savings being too high
        if (not preliminaryClean_beforeSavingsCalcAnalysis):        
            self.dta['Cleaning_Unconditional_SavingTooHigh_' + self.eyStr ]  = (self.dta['activeWealthChange_' + self.inflatedTimespan] > 750000)
            self.dta.loc[(self.dta[cleanVar] == 'Keep') & (self.dta['activeWealthChange_' + self.inflatedTimespan] > 750000), cleanVar] = 'SavingsToHigh' # 6
            self.dta.loc[(self.dta[cleanVar] == 'Keep') & (self.dta['activeWealthChange_' + self.inflatedTimespan].isna()), cleanVar] = 'Missing Savings'
            
        self.dta.loc[(self.dta[cleanVar] == 'Keep') & (self.dta['inflatedAfterTaxIncome_' + self.inflatedStart].isna()), cleanVar] = 'Missing_Income'
        self.dta.loc[(self.dta[cleanVar] == 'Keep') & (self.dta['inflatedAfterTaxIncome_' + self.inflatedEnd].isna()), cleanVar] = 'Missing_Income'
        
        if (not preliminaryClean_beforeSavingsCalcAnalysis):        
            self.dta = self.dta.loc[(self.dta[cleanVar] == 'Keep')].copy()
        
            

    def callAgg_NamedVars(self, locDta, groupVar):

        results = locDta.groupby(groupVar).agg(
                    familyInterview_N = ('familyInterviewId_' +self.eyStr, 'count'),
                    
#                    income_totaltaxable_avg = ('totalIncomeHH_' + self.eyStr, 'mean'),
#                    income_totaltaxable_median = ('totalIncomeHH_' + self.eyStr, 'median'),

#                    after_tax_income_avg = ('afterTaxIncomeHH_' + self.eyStr, 'mean'),
#                    after_tax_income_median = ('afterTaxIncomeHH_' + self.eyStr, 'median'),
                    
                    real_after_tax_income_avg = ('averageInflatedAfterTaxIncome_' + self.inflatedTimespan, 'mean'),
                    real_after_tax_income_median = ('averageInflatedAfterTaxIncome_' + self.inflatedTimespan, 'median'),

                    real_after_tax_income_sum = ('averageInflatedAfterTaxIncome_' + self.inflatedTimespan, 'sum'),
                    active_wealth_change_sum = ('activeWealthChange_' + self.inflatedTimespan,  'sum'),
                    # active_wealth_psid_change_sum = ('ActiveSavings_PSID1989_1989',  'sum'),
                    changeInRealNetWorth_sum = ('changeInRealNetWorth_' + self.inflatedTimespan, 'sum'),
                    
                    # netWorthCustom84_sum = ('NetWorth_1984_AsOf1989_1989', 'sum'),
                    # netWorthCustom89_sum = ('NetWorth_1989Only_1989', 'sum'),
                    # netWorth84_sum = ('NetWorth_1984', 'sum'),
                    # netWorth89_sum = ('NetWorth_1989', 'sum'),

                    savingsByNetWorth_avg = ('savingsRateByNetWorth_' + self.inflatedTimespan, 'mean'),
                    savingsByNetWorth_median = ('savingsRateByNetWorth_' + self.inflatedTimespan, 'median'),

#                    active_avg = ('activeSavingsRate_PerPerson_' + self.inflatedTimespan, 'mean'),
                    active_median = ('activeSavingsRate_PerPerson_' + self.inflatedTimespan, 'median'),

#                    active_PSID_avg = ('activeSavingsRate_Person_Alt_' + self.inflatedTimespan, 'mean'),
                    active_PSID_median = ('activeSavingsRate_Person_Alt_' + self.inflatedTimespan, 'median'),

                    )
        
        results['activeSavings_AvgAsSums_' + self.eyStr] = results.active_wealth_change_sum / (results.real_after_tax_income_sum * self.duration)
        # results['activeSavings_AvgAsSums_PSID_' + self.eyStr] = results.active_wealth_psid_change_sum / (results.real_after_tax_income_sum * self.duration)
        results['savingsRateByNetWorth_AvgAsSums_' + self.eyStr] = results.changeInRealNetWorth_sum / (results.real_after_tax_income_sum * self.duration)

        return results.reset_index()

        
    def calcUnweightedAggResultsForYear(self):
       
        dataMask = (self.dta['cleaningStatus_' + self.eyStr] == 'Keep')
        self.dta['dummyGroup'] = 'All'
        

        resultsByAge = self.callAgg_NamedVars(self.dta.loc[dataMask], 'dynanAgeGroupMidPeriod_' + self.eyStr)        
        resultsByAge['Source'] = 'Age_MidPoint_' + self.syStr + '_' + self.eyStr

        results = self.callAgg_NamedVars(self.dta.loc[dataMask], 'dummyGroup')
        results['Source'] = 'All_' + self.eyStr

        results = pd.concat([results, resultsByAge], ignore_index=True, sort=False)
        results.to_csv(os.path.join(self.baseDir, self.outputSubDir, 'SavingsRates_Unweighted_' + self.eyStr +'.csv'))


    def calcWeightedAggResultsForYear(self):
                
        aggDictionary = {
                    'familyInterview_N': ('familyInterviewId_' +self.eyStr,'count'),
                    'familyInterview_TotalWeights': ('familyInterviewId_' +self.eyStr,'SumOfWeights'),

                    'real_after_tax_income_sum' : ('averageRealAfterTaxIncome_AllYears_' + self.inflatedTimespan, 'sum'),
                    'active_wealth_change_sum' : ('activeWealthChange_' + self.inflatedTimespan,  'sum'),
                    # 'active_wealth_psid_change_sum' : ('ActiveSavings_PSID1989_1989',  'sum'),
                    'changeInRealNetWorth_sum' : ('changeInRealNetWorth_' + self.inflatedTimespan, 'sum'),
                    
                    # 'savingsByNetWorth_avg': ('savingsRateByNetWorth_' + self.inflatedTimespan, 'mean'),
                    'savingsByNetWorth_median': ('savingsRateByNetWorth_' + self.inflatedTimespan, 'median'),

                    # 'active_avg': ('activeSavingsRate_PerPerson_' + self.inflatedTimespan, 'mean'),
                    'active_median': ('activeSavingsRate_PerPerson_' + self.inflatedTimespan, 'median'),

                    'income_totaltaxable_avg': ('totalIncomeHH_' + self.eyStr, 'mean'),
                    'income_totaltaxable_median': ('totalIncomeHH_' + self.eyStr, 'median'),

                    'after_tax_income_avg': ('afterTaxIncomeHH_' + self.eyStr, 'mean'),
                    'after_tax_income_median': ('afterTaxIncomeHH_' + self.eyStr, 'median'),
                    
                    'real_after_tax_income_avg': ('averageRealAfterTaxIncome_AllYears_' + self.inflatedTimespan, 'mean'),
                    'real_after_tax_income_median': ('averageRealAfterTaxIncome_AllYears_' + self.inflatedTimespan, 'median'),
                    } 
        
                
        dataMask = (self.dta['cleaningStatus_' + self.eyStr] == 'Keep')
        
        resultsByRace = wGroupByAgg(self.dta.loc[dataMask], ['raceR_' + self.eyStr], aggregationDict = aggDictionary, varForWeights = ('LongitudinalWeightHH_' + self.eyStr)).reset_index()
        resultsByRace['Source'] = 'Race_' + self.eyStr
                
        resultsByAge = wGroupByAgg(self.dta.loc[dataMask], ['dynanAgeGroupMidPeriod_' + self.eyStr], aggregationDict = aggDictionary, varForWeights = ('LongitudinalWeightHH_' + self.eyStr)).reset_index()
        resultsByAge['Source'] = 'Age_MidPoint_' + self.syStr + '_' + self.eyStr

        resultsByIncome = wGroupByAgg(self.dta.loc[dataMask], ['dynanIncomeGroup_' + self.inflatedEnd], aggregationDict = aggDictionary, varForWeights = ('LongitudinalWeightHH_' + self.eyStr)).reset_index()
        resultsByIncome['Source']='Income' + self.inflatedEnd
        
        results = pd.DataFrame(wAgg(self.dta.loc[dataMask], aggregationDict = aggDictionary, varForWeights= ('LongitudinalWeightHH_' + self.eyStr))).transpose()
        results['Source'] = 'All_' + self.eyStr

        results = pd.concat([resultsByRace, results, resultsByAge, resultsByIncome], ignore_index=True, sort=False)
        
        results['activeSavings_AvgAsSums_' + self.eyStr] = results.active_wealth_change_sum / (results.real_after_tax_income_sum * self.duration)
        # results['activeSavings_AvgAsSums_PSID_' + self.eyStr] = results.active_wealth_psid_change_sum / (results.real_after_tax_income_sum * self.duration)
        results['savingsRateByNetWorth_AvgAsSums_' + self.eyStr] = results.changeInRealNetWorth_sum / (results.real_after_tax_income_sum * self.duration)

        results.to_csv(os.path.join(self.baseDir, self.outputSubDir, 'SavingsRates_Weighted_' + self.eyStr +'.csv'))
        
        return results

    def executeForYear(self, startYear, endYear, toYear):
        self.clearData()
        self.setPeriod(startYear, endYear, toYear)
        self.readData()
        
        self.calcIfMovedOrChangedHeadAtAnyPoint()
        self.calcAfterTaxIncome(True)
        self.inflateValues(True)
        self.calcAverageMoneyIncome()
        self.generateSavingsDebugFields() 
        self.cleanResults(preliminaryClean_beforeSavingsCalcAnalysis=True)
       
        self.calcSavingsRate_NetWorthChange()
        self.calcSavingsRate_ActiveSavings()
        self.cleanResults(preliminaryClean_beforeSavingsCalcAnalysis=False)
        self.createSegmentBins()

        self.dta = ReplicationAnalyzer.selectiveReorder(self.dta, 
                                    ['cleaningStatus_' + self.eyStr, 
                                     'raceR_' + self.eyStr,
                                     'FederalIncomeTaxesRS_' + self.eyStr,
                                    'fiitax_' + self.eyStr,
                                    'inflatedNetWorthWithHome_' + self.inflatedStart,
                                    'inflatedNetWorthWithHome_' + self.inflatedEnd,
                                    'changeInRealNetWorth_' + self.inflatedTimespan,

                                    'inflatedAfterTaxIncome_' + self.inflatedStart,    
                                    'inflatedAfterTaxIncome_' + self.inflatedEnd,    
                                    'averageRealAfterTaxIncome_StartEndYears_' + self.inflatedTimespan,
                                    'averageRealAfterTaxIncome_AllYears_' + self.inflatedTimespan,
                                     
                                    'savingsRateByNetWorth_' + self.inflatedTimespan,
                                    'activeWealthChange_' + self.inflatedTimespan,
                                    'activeSavingsRate_PerPerson_' + self.inflatedTimespan
                                    ])



        self.dta.to_csv(os.path.join(self.baseDir, self.outputSubDir, "CombinedDynan_" + self.inflatedTimespan + ".csv"), index=False)

        #if (False):
            # results = self.calcUnweightedAggResultsForYear() 
        results = self.calcWeightedAggResultsForYear()
        return results
              
    def doIt(self):
        toYear = 1994
        yearsWealthDataCollected = [1984, 1989, 1994] + list(range(1999, 2017+2, 2))
        startYear = yearsWealthDataCollected[0]
        results = None
        for endYear in yearsWealthDataCollected[1:]:
            tempResults = self.executeForYear(startYear, endYear, toYear)
            tempResults.rename(columns={'raceR_' + str(endYear): 'raceR', 
                                        'dynanAgeGroupMidPeriod_' + str(endYear): 'dynanAgeGroupMidPeriod',
                                        'dynanIncomeGroup_' + str(endYear) + '_as_' + str(toYear): 'dynanIncomeGroup_as_' + str(toYear),
                                        'activeSavings_AvgAsSums_' + str(endYear): 'activeSavings_AvgAsSums',
                                        'savingsRateByNetWorth_AvgAsSums_' + str(endYear): 'savingsRateByNetWorth_AvgAsSums'
                                        }, inplace=True)
            tempResults['StartYear'] = startYear
            tempResults['EndYear'] = endYear
            tempResults['InflatedToYear'] = toYear
            if results is None:
                results = tempResults
            else:
                results = pd.concat([results, tempResults], ignore_index=True)
                
            startYear = endYear
        
        self.combinedResults = ReplicationAnalyzer.selectiveReorder(results, ['StartYear', 'EndYear', 'InflatedToYear', 'Source', 'savingsByNetWorth_median', 'active_median', 'savingsRateByNetWorth_AvgAsSums', 'activeSavings_AvgAsSums'])
        self.combinedResults.to_csv(os.path.join(self.baseDir, self.outputSubDir, "CombinedDynan_CombinedResults_" + str(yearsWealthDataCollected[1]) + '_to_' + str(yearsWealthDataCollected[-1]) +  ".csv"), index=False)
        
        


''' Allow execution from command line, etc'''    
if __name__ == "__main__":
    analyzer = DynanAnalysis(familyBaseFileNameWithPath = 
                             os.path.join('C:/dev/sensitive_data/InvestorSuccess/Inequality',
                                          'finalInputPSID', "extractedPSID_Mapped_Recoded_"),
            individualBaseFileNameWithPath = os.path.join('C:/dev/sensitive_data/InvestorSuccess/Inequality',
                                          'finalInputPSID', "extractedPSID_Individual_Mapped_Recoded"))
    analyzer.doIt()
