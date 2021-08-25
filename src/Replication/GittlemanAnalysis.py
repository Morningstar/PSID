import os
import Replication.ReplicationAnalyzer as ReplicationAnalyzer
from Survey.SurveyFunctions import *
import Inflation.CPI_InflationReader as CPI_InflationReader
import DataQuality.CrossSectionalTester as CrossSectionalTester
from Survey.SurveyTimeSeriesQA import SurveyTimeSeriesQA

''' 
This class seeks to replicate the results from Gittleman and Wolff's 2004 Paper: Racial Differences in Patterns of Wealth Accumulation
'''


''' Key Descriptions

Information on asset levels and flows enables a division of changes in net worth into saving, 
capital gains, and transfers. For each asset, the change in value over a period can be divided 
into two parts-the capital gain and the amount of additional funds invested in that asset, 
which we term gross saving. Details of the algorithm used are contained in the appendix on the 
JHR website, but the basic approach is as follows: 

For those assets for which the amount of the net inflow-that is, the gross saving in that 
asset-is known, it is straightforward to calculate the capital gain, as it is simply the 
difference between the asset's change in value over the period and the net inflow. 

For assets for which nothing is known about the net inflow, an appropriate market-based rate of return 
is assigned in order to calculate the amount of the capital gain, and, for these assets, 
the amount of gross saving is calculated as the difference between the change in the value 
of the asset over the period and capital gains on the asset. Summing over the group of 
assets, one arrives at a total for capital gains and one for gross saving.

-- Main Difference from PSID (and closely related Dynan et al)
First, divide the change in net equity of the home (less the value of any home improvements) 
into a portion that is saving (the reduction in mortgage principal) and that is capital gains 
(the change in the value of the house), rather than attributing the entire amount to capital 
gains. 

Second, for the assets for which there are specific questions about inflows-those other 
than the main home, other real estate, farm/business, and stocks-the PSID approach 
implicitly assumes that changes net value are entirely attributable to saving, 
rather than allocating some portion into capital gains by applying a market-based 
rate of return, as we do. 

In any case, with either method, it is apparent that saving can potentially flow into any 
assets, and not just those for which there are specific questions in the PSID's active 
saving module.
'''


''' By Asset Type - calculate or set RoR (how to handle Assets moved in or out??

'''

''' To replicate Gittleman and Wolff study:
    
    1) Definition of: NetWorth  [Uses PSID -- Same as Dynan et al]
1.    Main home – house value minus remaining mortgage principal. [value of home equity (S220)]
2.    Other real estate – net value of second home, land, rental real estate, money owed in land contract. [S209 (Other real estate, beyond home)]
3.    Net equity in farm or business.  [S203 (farm/business)]
4.    Stock – stock in publicly-held corporations, mutual funds, investment trusts, including stocks in IRAs. [S211 (stock including Stock in IRA)]
5.    Checking and saving - checking or saving accounts, money market funds, certificates of deposit, government saving bonds, or Treasury bills, including IRA's. [S205 (checking , savings, bonds, bonds in IRA)]
6.    Net value of vehicles. [S213 (vehicles)]
7.    Other savings -- bonds, rights in a trust or estate, cash value in a life insurance policy, or a valuable collection for investment purposes. [S215 (trusts, life insurance,valuable collection etc))]
8.    Other debts – credit card, student loans, loans from relatives, medical or legal bills. [net of debt value (S207)]


    2) Definition of Active Savings:
    
    Covers all flow variables from Dynan, without Home Value Adjusment
    and not including any Changes in Stock -- Handled Separately to Calculate Capital Gains versus Active Savings
    
    1.    Amount of money put aside in private annuities.  [PrivateRetirePlan_SinceLastQYr_AmountMovedIn_]
    2.    Value of pensions or annuities cashed in.     [PrivateRetirePlan_SinceLastQYr_AmountMovedOut]_
    3.    Amount of money invested in real estate other than main home.  [OtherRealEstate_SinceLastQYr_AmountBought_ / Sold]
            * Does this include SOLD?
    4.    Value of additions or improvements worth $10,000 or more to main home or other real estate.  [CostOfMajorHomeRenovations_]
    5.    Amount of money invested in farm or business.  [Business_SinceLastQYr_AmountBought_ ]
    6.    Amount of money realized from sale of farm or business assets. [Business_SinceLastQYr_AmountSold_]
    7.    Net value of any stocks in publicly-held corporations, mutual funds or investment trusts bought or sold.
                [BrokerageStocks_SinceLastQYr_AmountBought_/Sold_]
    8.    Net value of debt and assets removed from family holdings by someone with more than $5,000 of either leaving the family. [netMoveOut_]
    9.    Net value of debt and assets added to family holdings by someone with more than $5,000 of either joining the family.  [netMoveIn_]
    10.    Value of any gifts or inheritances of money or property worth $10,000 or more. [largeGift_All_AmountHH_]

'''


class GittlemanAnalysis(ReplicationAnalyzer.InequalityAnalyzer):
    
    def __init__(self, baseDir, familyInputSubDir, familyBaseName, individualInputSubDir, individualBaseName, outputSubDir):
        super().__init__(baseDir, familyInputSubDir, familyBaseName, individualInputSubDir, individualBaseName, outputSubDir, 
                         yearsToInclude = None) # Not used
        self.useOriginalSampleOnly = True
        self.dta = None

        self.inflation = CPI_InflationReader.CPIInflationReader()


        
    def readData(self):
        super().readData()
        for year in [self.startYear, self.endYear]:
            self.dta['raceR_' +  str(year)].replace({'Hispanic':'White'}, inplace=True)

        # Not clear why, but this looks like the only why the data lines up with their report
        if self.endYear == 1994:
            self.dta.loc[self.dta.PrivateRetirePlan_SinceLastQYr_AmountMovedOut_1994 == 9999997] = 0

        # Remove all Recontact Families
        self.dta = self.dta.loc[self.dta['ChangeInCompositionFU_' + self.eyStr].ne(8)].copy()

    def checkQualityOfInputData(self):
        tsTester = SurveyTimeSeriesQA(dta = self.dta, dfLabel = "Gittleman Analysis (" + str(self.timespan) + ")",
            baseDir = self.baseDir, outputDir = self.outputSubDir, isWeighted = False, weightVar = None, raiseOnError = False)

        nonWealthVarYears = ['MovedR', 'ageR', 'hasHouse', 'NetWorthWithHome', 'NetWorthWithHomeRecalc', 'valueOfHouse_Gross', 'valueOfHouse_Debt', 'FederalIncomeTaxesRS','FederalIncomeTaxesO',  'totalIncomeHH',  'fiitax']

        # Look for non-wealth vars -- available any year
        tsTester.setup(outputFileNameBase="QAReviewNonWealth_", varsOfInterest = nonWealthVarYears, years = self.yearsWithFamilyData.copy(), isLongForm = False, twoDigitYearSuffix=False, analyzeOnlyTimeData = False)
        tsTester.checkForMedianShifts(percentChangeForError = .10)

        # Look for wealth vars - only available on the start / end years
        wealthVarYears = self.familyFieldsWeNeedStartEnd.copy()
        varsWeDontNeed = ['familyInterviewId']
        wealthVarYears = [x for x in wealthVarYears if ((x not in nonWealthVarYears) and (x not in varsWeDontNeed))]        

        tsTester.setup(outputFileNameBase="QAReviewWealth_", varsOfInterest = self.familyFieldsWeNeedStartEnd, years = [self.startYear, self.endYear], isLongForm = False, twoDigitYearSuffix=False, analyzeOnlyTimeData = False)
        tsTester.checkForMedianShifts(percentChangeForError = .10 * self.duration)

    def cleanData_CrossSectional(self, analysisYear):
        self.dta['ChangeInHeadFU_' + self.timespan] = False

        cleanVar = 'cleaningStatus_' + self.eyStr
        self.dta[cleanVar] = 'Keep'
        self.dta.loc[(self.dta[cleanVar] == 'Keep') & (self.dta['interviewId_' + self.syStr] == 0), cleanVar] = 'Not In Wave'

        # There are no sample selection criteria for inclusion in these samples. 
        # However, Juster, Smith and Stafford (1998) say: “The PSID other savings number in 1984 is unusually high. This is due to a few large outlier values that appear to be miscodes.” (p. 17, footnote 12). There are 7 cases where the other savings value is giving as $9 million, which is an extreme outlier. These observations are excluded from the 1984 cross-sectional sample. All calculations with these samples use the cross-sectional PSID family weights.
        if analysisYear == 1984:
            self.dta.loc[(self.dta[cleanVar] == 'Keep') & (self.dta.valueOfOtherAssets_Net_1984 > 5000000), cleanVar] = 'Other Savings Too High'        
        else:
            self.dta.loc[(self.dta['valueOfOtherAssets_Net_' + str(analysisYear)] > 5000000), 'valueOfOtherAssets_Net_' + str(analysisYear)]
            
        # self.dta[cleanVar].value_counts()
        dataMask = (self.dta[cleanVar] == 'Keep')
        self.dta = self.dta.loc[dataMask].copy()


    def cleanData_Longitudinal_PrepForSavingsCalcAnalysis(self):
        ''' Sample Selection
        1) No change in head of HH
        2) Only in analyses using regressions or averages: "in analyses where the results are sensitive to outliers, 
        families at the top and bottom 1 percent in terms of wealth appreciation are trimmed from the sample"
        That's it.
        '''
        
        cleanVar = 'cleaningStatus_' + self.eyStr
        self.dta[cleanVar] = 'Keep'

        self.dta.loc[(self.dta[cleanVar] == 'Keep') & (self.dta['interviewId_' + self.syStr] == 0), cleanVar] = 'Not In Both Waves'
        self.dta.loc[(self.dta[cleanVar] == 'Keep') & (self.dta['interviewId_' + self.eyStr] == 0), cleanVar] = 'Not In Both Waves'

        # if (self.endYear == 1989 and self.startYear == 1984):
        #     self.dta.loc[(self.dta[cleanVar] == 'Keep') & (~(self.dta['ChangeInCompositionFU_1989FiveYear_1989'].isin([0, 1, 2]))), cleanVar] = 'Not same Head'
        # else:
        self.dta.loc[(self.dta[cleanVar] == 'Keep') & (self.dta['ChangeInHeadFU_' + self.timespan]), cleanVar] = 'Not same Head'

        self.dta[cleanVar].value_counts(dropna=False) # Should have 5180 left in 1989
        
        # For trimmed samples, the top and bottom 1 percent of the distribution of changes in wealth in each five year period is excluded.
        nwVar = 'changeInRealNetWorth_' + self.inflatedTimespan
        weightVar = 'LongitudinalWeightHH_' + self.syStr

        if True:
            topThreshold_ChangeInNW = np.percentile(self.dta.loc[(self.dta[cleanVar] == 'Keep'),nwVar], 99)
            bottomThreshold_ChangeInNW = np.percentile(self.dta.loc[(self.dta[cleanVar] == 'Keep'), nwVar], 1)
            self.dta.loc[(self.dta[cleanVar] == 'Keep') & 
                         (self.dta[nwVar] > topThreshold_ChangeInNW), cleanVar] = 'Trim_WealthChangeHigh'
            self.dta.loc[(self.dta[cleanVar] == 'Keep') & 
                         (self.dta[nwVar] < bottomThreshold_ChangeInNW), cleanVar] = 'Trim_WealthChangeLow'
    
        elif False:
            # It appears that Gittleman used the unweighted percentiles, above, not weighted percentiles
            thresholds_ChangeInNW = wPercentile_ForSeries(values = self.dta.loc[(self.dta[cleanVar] == 'Keep'), nwVar], 
                                                quantiles = [.01,.99], sample_weight = self.dta.loc[(self.dta[cleanVar] == 'Keep'), weightVar])
            bottomThreshold_ChangeInNW = thresholds_ChangeInNW[0]
            topThreshold_ChangeInNW = thresholds_ChangeInNW[1]
                
            self.dta.loc[(self.dta[cleanVar] == 'Keep') & 
                         (self.dta[nwVar] > topThreshold_ChangeInNW), cleanVar] = 'Trim_WealthChangeHigh'
            self.dta.loc[(self.dta[cleanVar] == 'Keep') & 
                         (self.dta[nwVar] < bottomThreshold_ChangeInNW), cleanVar] = 'Trim_WealthChangeLow'
        else:
            raceVar = 'raceR_' + self.syStr
            # White
            topThreshold_ChangeInNW_White = np.percentile(self.dta.loc[(self.dta[cleanVar] == 'Keep') & (self.dta[raceVar] == 'White'),nwVar], 99)
            bottomThreshold_ChangeInNW_White = np.percentile(self.dta.loc[(self.dta[cleanVar] == 'Keep') & (self.dta[raceVar] == 'White'), nwVar], 1)
                    
            self.dta.loc[(self.dta[cleanVar] == 'Keep') & (self.dta[raceVar] == 'White') & (self.dta[nwVar] > topThreshold_ChangeInNW_White), cleanVar] = 'Trim_WealthChangeHigh'
            self.dta.loc[(self.dta[cleanVar] == 'Keep') & (self.dta[raceVar] == 'White') & (self.dta[nwVar] < bottomThreshold_ChangeInNW_White), cleanVar] = 'Trim_WealthChangeLow'

            # Black
            topThreshold_ChangeInNW_Black = np.percentile(self.dta.loc[(self.dta[cleanVar] == 'Keep') & (self.dta[raceVar] == 'Black'),nwVar], 99)
            bottomThreshold_ChangeInNW_Black= np.percentile(self.dta.loc[(self.dta[cleanVar] == 'Keep') & (self.dta[raceVar] == 'Black'), nwVar], 1)
                    
            self.dta.loc[(self.dta[cleanVar] == 'Keep') & (self.dta[raceVar] == 'Black') & (self.dta[nwVar] > topThreshold_ChangeInNW_Black), cleanVar] = 'Trim_WealthChangeHigh'
            self.dta.loc[(self.dta[cleanVar] == 'Keep') & (self.dta[raceVar] == 'Black') & (self.dta[nwVar] < bottomThreshold_ChangeInNW_Black), cleanVar] = 'Trim_WealthChangeLow'


        if self.startYear == 1984:
            self.dta.loc[(self.dta[cleanVar] == 'Keep') & (self.dta.valueOfOtherAssets_Net_1984 > 5000000), cleanVar] = 'Other Savings Too High'

        # self.dta[cleanVar].value_counts(dropna=False)
        self.dta = self.dta.loc[(self.dta[cleanVar] == 'Keep')].copy()

    # def cleanData_Longitudinal_PostSavingsCalc(self):
    #    cleanVar = 'cleaningStatus_' + self.eyStr
        

    def calcAfterTaxIncome(self, includeIntermediateYears=True):
        if includeIntermediateYears:
            yearRange = (self.yearsWithFamilyData.copy())
        else:
            yearRange = [self.startYear, self.endYear]

        for year in yearRange:
            yr = str(year)
            
            if (year >= 1970 and year <= 1991):
                self.dta['TotalTax_' + yr] = self.dta['FederalIncomeTaxesRS_' + yr].add(self.dta['FederalIncomeTaxesO_' + yr], fill_value=0)  
            else:
                self.dta['TotalTax_' + yr] = self.dta['fiitax_' + yr]

            #CHANGE FROM GITTLEMAN: Included State Tax
            self.dta['TotalTax_' + yr] = self.dta['TotalTax_' + yr].add(self.dta['siitax_' + yr], fill_value=0) 

            self.dta['afterTaxIncomeHH_' + yr] = self.dta['totalIncomeHH_' + yr].sub(self.dta['TotalTax_' + yr], fill_value=0)
                     
    def inflateValues(self, includeIntermediateYears=True):
        if includeIntermediateYears:
            yearRange = (self.yearsWithFamilyData.copy())
        else:
            yearRange = [self.startYear, self.endYear]
        
        ################
        # Inflate values that COULD include intermediate years
        ################
        for year in yearRange:
            yr = str(year)
            inflatedYear = yr + '_as_' + self.tyStr
            inflationGivenYear =  self.inflation.getInflationFactorBetweenTwoYears(year, self.toYear)
            # inflationLagYear =  nipa.getInflationFactorBetweenTwoYears(year-1, self.toYear-1)
            # TODO -- Gittleman doesn't use lag year?
            self.dta['inflatedNetWorthWithHome_' + inflatedYear] = self.dta['NetWorthWithHome_' + yr] * inflationGivenYear
            self.dta['inflatedNetWorthWithHomeRecalc_' + inflatedYear] = self.dta['NetWorthWithHomeRecalc_' + yr] * inflationGivenYear
            self.dta['inflatedPreTaxIncome_' + inflatedYear] = self.dta['totalIncomeHH_' + yr] * inflationGivenYear # inflationLagYear 
            self.dta['inflatedAfterTaxIncome_' + inflatedYear] = self.dta['afterTaxIncomeHH_' + yr] * inflationGivenYear # inflationLagYear 
            
        ################
        # Inflate values that ONLY are relevant for start-end comparisons
        ################
        # Calc changes -- assumes all inflated to common year already 
        self.dta['changeInRealNetWorth_'      + self.inflatedTimespan] = self.dta['inflatedNetWorthWithHome_' + self.inflatedEnd].sub(self.dta['inflatedNetWorthWithHome_' + self.inflatedStart], fill_value=0)
                
                
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

    def calcIfValueOnMoveAndChangedHeadAtAnyPoint(self):    

        self.dta['ChangeInHeadFU_' + self.timespan] = False
        
        # Changes on Move
        self.dta['House_ValueIncrease_WhenMoving_' + self.inflatedTimespan] = 0
        self.dta['House_TotalChangeInMortgageDebt_WhenMoving_' + self.inflatedTimespan] = 0

        # Changes without Move
        self.dta['House_TotalChangeInMortgageDebt_WhenNotMoving_' + self.inflatedTimespan] = 0
        self.dta['House_ValueIncrease_WhenNotMoving_' + self.inflatedTimespan] = 0


        for year in (self.yearsWithFamilyData.copy()):
            inflationPriorYear =  self.inflation.getInflationFactorBetweenTwoYears(year-self.timeStep, self.toYear)
            inflationGivenYear =  self.inflation.getInflationFactorBetweenTwoYears(year, self.toYear)

            # Not used from Dynan and parent class:  Fixing 'Move Statuses' 
            
            if (year >= (self.startYear + self.timeStep)):
                
                # if the person moved, add any changes in house value from the move
                movedVar = 'MovedR_' + str(year)
                if (self.dta[movedVar].sum() >= 1): # ie not all nones
                    self.dta.loc[self.dta[movedVar] == True, 'House_ValueIncrease_WhenMoving_' + self.inflatedTimespan] = self.dta.loc[self.dta[movedVar] == True, 'House_ValueIncrease_WhenMoving_' + self.inflatedTimespan] \
                        .add(self.dta.loc[self.dta[movedVar] == True, 'valueOfHouse_Gross_' + str(year)] * inflationGivenYear, fill_value=0) \
                        .sub(self.dta.loc[self.dta[movedVar] == True, 'valueOfHouse_Gross_' + str(year-self.timeStep)] * inflationPriorYear, fill_value=0)
                        
                    self.dta.loc[ (self.dta[movedVar] == True), 'House_TotalChangeInMortgageDebt_WhenMoving_' + self.inflatedTimespan] = self.dta.loc[ (self.dta[movedVar] == True), 'House_TotalChangeInMortgageDebt_WhenMoving_' + self.inflatedTimespan] \
                        .add(self.dta.loc[ (self.dta[movedVar] == True), 'valueOfHouse_Debt_' + str(year)] * inflationGivenYear, fill_value=0) \
                        .sub(self.dta.loc[ (self.dta[movedVar] == True), 'valueOfHouse_Debt_' + str(year-self.timeStep)] * inflationPriorYear, fill_value=0)

                else:
                    print("Hmm... Missing moving data")
                
                # if the person DIDN'T MOVE, add up the cumulative changes in principal and house value
                self.dta.loc[ ~(self.dta[movedVar] == True), 'House_ValueIncrease_WhenNotMoving_' + self.inflatedTimespan] = self.dta.loc[ ~(self.dta[movedVar] == True), 'House_ValueIncrease_WhenNotMoving_' + self.inflatedTimespan] \
                    .add(self.dta.loc[ ~(self.dta[movedVar] == True), 'valueOfHouse_Gross_' + str(year)] * inflationGivenYear, fill_value=0) \
                    .sub(self.dta.loc[ ~(self.dta[movedVar] == True), 'valueOfHouse_Gross_' + str(year-self.timeStep)] * inflationPriorYear, fill_value=0)
                self.dta.loc[ ~(self.dta[movedVar] == True), 'House_TotalChangeInMortgageDebt_WhenNotMoving_' + self.inflatedTimespan] = self.dta.loc[ ~(self.dta[movedVar] == True), 'House_TotalChangeInMortgageDebt_WhenNotMoving_' + self.inflatedTimespan] \
                    .add(self.dta.loc[ ~(self.dta[movedVar] == True), 'valueOfHouse_Debt_' + str(year)] * inflationGivenYear, fill_value=0) \
                    .sub(self.dta.loc[ ~(self.dta[movedVar] == True), 'valueOfHouse_Debt_' + str(year-self.timeStep)] * inflationPriorYear, fill_value=0)

            if (year > self.startYear): # Look at changes in composition SINCE start, not from start to year prior
                changeVar = 'ChangeInCompositionFU_' + str(year)
                if (self.dta[changeVar].sum() > 1): # ie not all nones
                    self.dta.loc[~(self.dta['ChangeInHeadFU_' + self.timespan]) & ~(self.dta[changeVar].isin([0, 1, 2])), 'ChangeInHeadFU_' + self.timespan] = True



    def calcDetermineAssetLevelCapitalGains(self):
        
        totalInflationStartToEndYear =  self.inflation.getInflationFactorBetweenTwoYears(self.startYear, self.endYear)
        totalInflationEndToInflatedYear =  self.inflation.getInflationFactorBetweenTwoYears(self.endYear, self.toYear)
        totalInflationStartToInflatedYear =  self.inflation.getInflationFactorBetweenTwoYears(self.startYear, self.toYear)

        # Unlike Dynan, Does not appear to use a average here. 
        inflationForFlow = totalInflationEndToInflatedYear 
        # "For the change-in-stock variables (house value, mortgage, and wealth variables), we deflate the nominal level in each year by the price index for that year, and then take the change in this real value." 
        inflationForStock_StartOfPeriod = totalInflationStartToInflatedYear
        inflationForStock_EndOfPeriod = totalInflationEndToInflatedYear

        # Home:
        # 1.    Main home – Division is done by calculating capital gains and saving in each year and then summing them. 
        # If family did not move, the capital gains in each year equals the rise in the value of the home and saving equals the reduction in mortgage principal.
        # In years in which the family moves, the change in the net value of the house is considered saving. 
        # In addition, the value of additions or improvements, which is assumed to apply to main home, is added to saving as well.''

        # NOTE -- different from Gittleman. It appears that they DID NOT remove CostOfMajorHomeRenovations from Capital Gains
        # NOTE --- House_TotalChangeInMortgageDebt_WhenNotMoving is generally (though not always) NEGATIVE.

        self.dta['House_NetOfDebtValueIncrease_WhenMoving_' + self.inflatedTimespan] = self.dta['House_ValueIncrease_WhenMoving_' + self.inflatedTimespan].sub(self.dta['House_TotalChangeInMortgageDebt_WhenMoving_' + self.inflatedTimespan], fill_value=0)

        self.dta['House_CapitalGains_' + self.inflatedTimespan] = self.dta['House_ValueIncrease_WhenNotMoving_' + self.inflatedTimespan].sub(self.dta['CostOfMajorHomeRenovations_' + self.eyStr]*inflationForFlow, fill_value=0)
        self.dta['House_Savings_' + self.inflatedTimespan] = (self.dta['CostOfMajorHomeRenovations_' + self.eyStr]*inflationForFlow).add(self.dta['House_NetOfDebtValueIncrease_WhenMoving_' + self.inflatedTimespan], fill_value=0).sub(self.dta['House_TotalChangeInMortgageDebt_WhenNotMoving_' + self.inflatedTimespan], fill_value=0)
        self.dta['House_TotalChangeInWealth_' + self.inflatedTimespan] = self.dta['House_Savings_' + self.inflatedTimespan].add(self.dta['House_CapitalGains_' + self.inflatedTimespan], fill_value=0)

                    
        # 2.    Other real estate – Saving is the amount of money invested in real estate other than main home. Capital gains is the change in the net value of the asset minus saving in this asset.
        # Total: 
        self.dta['OtherRealEstate_TotalChangeInWealth_'+ self.inflatedTimespan] =  (self.dta['valueOfOtherRealEstate_Net_'+ self.eyStr]*inflationForStock_EndOfPeriod).sub(self.dta['valueOfOtherRealEstate_Net_'+ self.syStr]*inflationForStock_StartOfPeriod, fill_value=0) 
        self.dta['OtherRealEstate_Savings_' + self.inflatedTimespan] = (self.dta['OtherRealEstate_SinceLastQYr_AmountBought_' + self.eyStr]*inflationForFlow).sub(self.dta['OtherRealEstate_SinceLastQYr_AmountSold_' + self.eyStr]*inflationForFlow, fill_value=0)
        self.dta['OtherRealEstate_CapitalGains_' + self.inflatedTimespan] = self.dta['OtherRealEstate_TotalChangeInWealth_' + self.inflatedTimespan].sub(self.dta['OtherRealEstate_Savings_' + self.inflatedTimespan], fill_value=0)

        # 3.    Net equity in farm or business – Saving is the difference between the amount of money invested in farm or business and the amount realized from the sale of such assets. Capital gains is the change in the net value of the asset minus active saving in this asset.
        self.dta['Business_TotalChangeInWealth_'+ self.inflatedTimespan] =  (self.dta['valueOfBusiness_Net_'+ self.eyStr]*inflationForStock_EndOfPeriod).sub(self.dta['valueOfBusiness_Net_'+ self.syStr]*inflationForStock_StartOfPeriod, fill_value=0) 
        self.dta['Business_Savings_' + self.inflatedTimespan] = (self.dta['Business_SinceLastQYr_AmountBought_' + self.eyStr]*inflationForFlow).sub(self.dta['Business_SinceLastQYr_AmountSold_' + self.eyStr]*inflationForFlow, fill_value=0)
        self.dta['Business_CapitalGains_' + self.inflatedTimespan] = self.dta['Business_TotalChangeInWealth_' + self.inflatedTimespan].sub(self.dta['Business_Savings_' + self.inflatedTimespan], fill_value=0)

        # 4.    Stock – Saving is the net value of stock bought or sold. Capital gains is the change in the net value of the asset minus saving in this asset.
        self.dta['BrokerageStocks_TotalChangeInWealth_'+ self.inflatedTimespan] =  (self.dta['valueOfBrokerageStocks_Net_'+ self.eyStr]*inflationForStock_EndOfPeriod).sub(self.dta['valueOfBrokerageStocks_Net_'+ self.syStr]*inflationForStock_StartOfPeriod, fill_value=0) 
        self.dta['BrokerageStocks_Savings_' + self.inflatedTimespan] = (self.dta['BrokerageStocks_SinceLastQYr_AmountBought_' + self.eyStr]*inflationForFlow).sub(self.dta['BrokerageStocks_SinceLastQYr_AmountSold_' + self.eyStr]*inflationForFlow, fill_value=0)
        self.dta['BrokerageStocks_CapitalGains_' + self.inflatedTimespan] = self.dta['BrokerageStocks_TotalChangeInWealth_' + self.inflatedTimespan].sub(self.dta['BrokerageStocks_Savings_' + self.inflatedTimespan], fill_value=0)

        # 5.    Checking and savings – A 0 percent annual real rate of return is assumed, so saving equals the change in the net value of the asset.
        self.dta['CheckingAndSavings_TotalChangeInWealth_'+ self.inflatedTimespan] =  (self.dta['valueOfCheckingAndSavings_Net_'+ self.eyStr]*inflationForStock_EndOfPeriod).sub(self.dta['valueOfCheckingAndSavings_Net_'+ self.syStr]*inflationForStock_StartOfPeriod, fill_value=0) 
        self.dta['CheckingAndSavings_Savings_' + self.inflatedTimespan] = self.dta['CheckingAndSavings_TotalChangeInWealth_'+ self.inflatedTimespan]
        self.dta['CheckingAndSavings_CapitalGains_' + self.inflatedTimespan] = 0

        # 6.    Net value of vehicles – Change in the net value is attributed to saving.
        self.dta['Vehicle_TotalChangeInWealth_'+ self.inflatedTimespan] =  (self.dta['valueOfVehicle_Net_'+ self.eyStr]*inflationForStock_EndOfPeriod).sub(self.dta['valueOfVehicle_Net_'+ self.syStr]*inflationForStock_StartOfPeriod, fill_value=0) 
        self.dta['Vehicle_Savings_' + self.inflatedTimespan] = self.dta['Vehicle_TotalChangeInWealth_'+ self.inflatedTimespan]
        self.dta['Vehicle_CapitalGains_' + self.inflatedTimespan] = 0

        # 7.    Other savings – Capital gains are calculated by assuming a 1 percent annual real rate of return. Saving is the change in the net value of the asset minus the capital gains for this asset.
        otherAssets_RateOfReturn = 0.01
        self.dta['OtherAssets_TotalChangeInWealth_'+ self.inflatedTimespan] =  (self.dta['valueOfOtherAssets_Net_'+ self.eyStr]*inflationForStock_EndOfPeriod).sub(self.dta['valueOfOtherAssets_Net_'+ self.syStr]*inflationForStock_StartOfPeriod, fill_value=0) 
        self.dta['OtherAssets_CapitalGains_' + self.inflatedTimespan] = (self.dta['valueOfOtherAssets_Net_'+ self.syStr]*inflationForStock_StartOfPeriod )* ((1 + otherAssets_RateOfReturn)**self.duration) 
        self.dta['OtherAssets_CapitalGains_' + self.inflatedTimespan] = self.dta['OtherAssets_CapitalGains_' + self.inflatedTimespan].sub(self.dta['valueOfOtherAssets_Net_'+ self.syStr]*inflationForStock_StartOfPeriod, fill_value=0)
        self.dta['OtherAssets_Savings_' + self.inflatedTimespan] = self.dta['OtherAssets_TotalChangeInWealth_'+ self.inflatedTimespan].sub(self.dta['OtherAssets_CapitalGains_' + self.inflatedTimespan], fill_value=0)

        # 8.    Other debts - Capital gains are calculated by assuming an annual real rate of return equal to the inflation rate (CPI-U). Saving is the change in the net value of the asset minus the capital gains for this asset.
        otherDebts_RateOfReturn = totalInflationStartToEndYear - 1
        self.dta['OtherDebts_TotalChangeInWealth_'+ self.inflatedTimespan] =  (self.dta['valueOfAllOtherDebts_Net_'+ self.syStr]*inflationForStock_StartOfPeriod).sub(self.dta['valueOfAllOtherDebts_Net_'+ self.eyStr]*inflationForStock_EndOfPeriod, fill_value=0)
        self.dta['OtherDebts_CapitalGains_' + self.inflatedTimespan] = -(self.dta['valueOfAllOtherDebts_Net_'+ self.syStr] * inflationForStock_StartOfPeriod * otherDebts_RateOfReturn)
        self.dta['OtherDebts_Savings_' + self.inflatedTimespan] = (self.dta['OtherDebts_TotalChangeInWealth_'+ self.inflatedTimespan].sub(self.dta['OtherDebts_CapitalGains_' + self.inflatedTimespan], fill_value=0))


        # Not used in Gittleman Directly, but useful for comparison to Net Wealth Calc
        self.dta['MortgagePrincipal_TotalChangeInWealth_'+ self.inflatedTimespan] =  (self.dta['valueOfHouse_Debt_'+ self.eyStr]*inflationForStock_EndOfPeriod).sub(self.dta['valueOfHouse_Debt_'+ self.syStr]*inflationForStock_StartOfPeriod, fill_value=0)
        self.dta['MortgagePrincipal_Savings_' + self.inflatedTimespan] = self.dta['MortgagePrincipal_TotalChangeInWealth_'+ self.inflatedTimespan]
        self.dta['MortgagePrincipal_CapitalGains_' + self.inflatedTimespan] = 0
        

        # Catch some disagreements between Flow and Stock 
        # Note -- this does not appear to be part of Gittleman's Reported Cleaning process,
        # But their data reflects it -- which implies that their code automatically dropped based on NAs, or they did it but didn't report
        mask = (self.dta['valueOfOtherRealEstate_Net_'+ self.eyStr].isna()) & (self.dta['valueOfOtherRealEstate_Net_'+ self.syStr].isna()) & ((~(self.dta['OtherRealEstate_SinceLastQYr_AmountSold_' + self.eyStr].isna())) | (~(self.dta['OtherRealEstate_SinceLastQYr_AmountBought_' + self.eyStr].isna())))
        print('Found ' + str(len(self.dta.loc[mask])) + ' issues with ' + 'OtherRealEstate' + ' comparison between Stock and Flow; clearing the flow.')
        self.dta.loc[mask, 'OtherRealEstate_TotalChangeInWealth_'+ self.inflatedTimespan] = 0
        self.dta.loc[mask, 'OtherRealEstate_CapitalGains_'+ self.inflatedTimespan] = 0
        self.dta.loc[mask, 'OtherRealEstate_Savings_'+ self.inflatedTimespan] = 0
                    
        mask = (self.dta['valueOfBusiness_Net_'+ self.eyStr].isna()) & (self.dta['valueOfBusiness_Net_'+ self.syStr].isna()) & ((~(self.dta['Business_SinceLastQYr_AmountSold_' + self.eyStr].isna())) | (~(self.dta['Business_SinceLastQYr_AmountBought_' + self.eyStr].isna())))
        print('Found ' + str(len(self.dta.loc[mask])) + ' issues with ' + 'Business' + ' comparison between Stock and Flow; clearing the flow.')
        self.dta.loc[mask, 'Business_TotalChangeInWealth_'+ self.inflatedTimespan] = 0
        self.dta.loc[mask, 'Business_CapitalGains_'+ self.inflatedTimespan] = 0
        self.dta.loc[mask, 'Business_Savings_'+ self.inflatedTimespan] = 0

        mask = (self.dta['valueOfBrokerageStocks_Net_'+ self.eyStr].isna()) & (self.dta['valueOfBrokerageStocks_Net_'+ self.syStr].isna()) & ((~(self.dta['BrokerageStocks_SinceLastQYr_AmountSold_' + self.eyStr].isna())) | (~(self.dta['BrokerageStocks_SinceLastQYr_AmountBought_' + self.eyStr].isna())))
        print('Found ' + str(len(self.dta.loc[mask])) + ' issues with ' + 'BrokerageStocks' + ' comparison between Stock and Flow; clearing the flow.')
        self.dta.loc[mask, 'BrokerageStocks_TotalChangeInWealth_'+ self.inflatedTimespan] = 0
        self.dta.loc[mask, 'BrokerageStocks_CapitalGains_'+ self.inflatedTimespan] = 0
        self.dta.loc[mask, 'BrokerageStocks_Savings_'+ self.inflatedTimespan] = 0


 
    def calcSavingsRate_ActiveSavings(self, debugAndReport = True):
        ''' 
        Gittleman et al take a different approach than Dynan et al.
        Here the focus is on calculating capital gains versus assuming all is savings
        '''
        totalInflationEndToInflatedYear =  self.inflation.getInflationFactorBetweenTwoYears(self.endYear, self.toYear)
        totalInflationStartToInflatedYear =  self.inflation.getInflationFactorBetweenTwoYears(self.startYear, self.toYear)

        # Unlike Dynan, Does not appear to use a average here. 
        inflationForFlow = totalInflationEndToInflatedYear 
        # "For the change-in-stock variables (house value, mortgage, and wealth variables), we deflate the nominal level in each year by the price index for that year, and then take the change in this real value." 
        inflationForStock_StartOfPeriod = totalInflationStartToInflatedYear
        inflationForStock_EndOfPeriod = totalInflationEndToInflatedYear


        # Each of the following entries should have a variable _TotalChangeInWealth, _CapitalGains and _Savings
        componentVars = ['House', 'OtherRealEstate', 'Business', 'BrokerageStocks', 'CheckingAndSavings', 'Vehicle', 'OtherAssets', 'OtherDebts']
        
        totalChangeVars = [s + "_TotalChangeInWealth_" + self.inflatedTimespan for s in componentVars]    
        capitalGainsVars = [s + "_CapitalGains_" + self.inflatedTimespan for s in componentVars]
        grossSavingsVars = [s + "_Savings_" + self.inflatedTimespan for s in componentVars]
        
        varsUsed = [] + totalChangeVars + capitalGainsVars + grossSavingsVars

        # Most of our variables have lots of NAs.  They should all be filled to 0 - either with add(fill_value) or on the DF itself, as here 
        self.dta[varsUsed] = self.dta[varsUsed].fillna(value=0)

        self.dta['Total_ChangeInWealth_'  + self.inflatedTimespan]= self.dta[totalChangeVars].sum(axis=1)
        self.dta['Total_CapitalGains_'  + self.inflatedTimespan]= self.dta[capitalGainsVars].sum(axis=1)
        self.dta['Total_GrossSavings_'  + self.inflatedTimespan]= self.dta[grossSavingsVars].sum(axis=1)
        
        # People moving in -- NOT savings; a transfer. Any money IN here should be REMOVED from savings
        self.dta['netMoveIn_' + self.inflatedTimespan] =  (self.dta['PersonMovedIn_SinceLastQYr_AssetsMovedIn_'   + self.eyStr]*inflationForFlow).sub(self.dta['PersonMovedIn_SinceLastQYr_DebtsMovedIn_' + self.eyStr]*inflationForFlow, fill_value=0)
        # People moving out -- NOT savings; a transfer. Any money OUT here should be ADDED to savings 
        self.dta['netMoveOut_' + self.inflatedTimespan] = (self.dta['PersonMovedOut_SinceLastQYr_AssetsMovedOut_' + self.eyStr]*inflationForFlow).sub(self.dta['PersonMovedOut_SinceLastQYr_DebtsMovedOut_' + self.eyStr]*inflationForFlow, fill_value=0)
        self.dta['netAssetMove_' + self.inflatedTimespan]  = self.dta['netMoveOut_' + self.inflatedTimespan].sub(self.dta['netMoveIn_' + self.inflatedTimespan], fill_value=0)

        # Annuities and IRAs -- Dynan has this as Active Savings. 
        # For Gittleman, this is a savings component, but it's accounted for in the transfer section (NOT included in Gross savings, only in NET Active. Add, but fine).
        # In particular, substract out the NET OUTFLOW From Annuities and IRAs -- since not covered elsewhere.  So inflow = more savings, outflow = less savings.   Ok good. 
        self.dta['netIRAandAnnuityChange_' + self.inflatedTimespan] = (self.dta['PrivateRetirePlan_SinceLastQYr_AmountMovedIn_' + self.eyStr]*inflationForFlow).sub(self.dta['PrivateRetirePlan_SinceLastQYr_AmountMovedOut_' + self.eyStr]*inflationForFlow, fill_value=0)
        self.dta['largeGift_All_AmountHH_' + self.inflatedTimespan] = self.dta['largeGift_All_AmountHH_' + self.eyStr]*inflationForFlow
        self.dta['Total_NetActiveSavings_'  + self.inflatedTimespan]= self.dta['Total_GrossSavings_' + self.inflatedTimespan].sub(self.dta['largeGift_All_AmountHH_' + self.inflatedTimespan], fill_value=0).add(self.dta['netAssetMove_' + self.inflatedTimespan], fill_value=0).add(self.dta['netIRAandAnnuityChange_' + self.inflatedTimespan], fill_value=0)

        self.dta['activeSavingsRate_PerPerson_' + self.inflatedTimespan] = (self.dta['Total_NetActiveSavings_'  + self.inflatedTimespan] / self.duration)
        # Its difficult to tell which income var Gittleman used, but it appears to be the Real, PreTax Income
        self.dta['activeSavingsRate_PerPerson_' + self.inflatedTimespan] = (self.dta['activeSavingsRate_PerPerson_' + self.inflatedTimespan].div(self.dta['averageRealBeforeTaxIncome_AllYears_' + self.inflatedTimespan], fill_value=0))


        if debugAndReport:        
            varsToExpore = varsUsed + ['averageNominalIncome_AllYears_' + self.timespan, 'TotalTax_' + self.eyStr, 'TotalTax_' + self.syStr] + \
                                       ['Total_ChangeInWealth_'  + self.inflatedTimespan, 'Total_CapitalGains_'  + self.inflatedTimespan, 'Total_GrossSavings_'  + self.inflatedTimespan, 'Total_NetActiveSavings_'  + self.inflatedTimespan, 
                                       'netMoveIn_' + self.inflatedTimespan, 'netMoveOut_' + self.inflatedTimespan, 'netIRAandAnnuityChange_' + self.inflatedTimespan, 
                                       'activeSavingsRate_PerPerson_' + self.inflatedTimespan,
                                        'LongitudinalWeightHH_' + self.eyStr
                                       ]
    
            # Output summary stats on the data, to check everything is ok:
            cleanVar = 'cleaningStatus_' + self.eyStr
            csTester = CrossSectionalTester.CrossSectionalTester(dta = self.dta.loc[self.dta[cleanVar] == 'Keep', varsToExpore].copy(),
                                                              dfLabel = "Vars used in Active Savings Calc" + str(self.inflatedTimespan) + ")",
                                                              year = self.endYear,
                                                              varMapping = None,
                                                              ignoreUnmappedVars = True)

            if not os.path.exists(os.path.join(self.baseDir, self.outputSubDir)):
                os.makedirs(os.path.join(self.baseDir, self.outputSubDir))

            csTester.exploreData(
                reportFileNameWithPathNoExtension = os.path.join(self.baseDir, self.outputSubDir, "CombinedGittlman_ActiveSavingsVars_" + self.inflatedTimespan),
                weightVar = "LongitudinalWeightHH_" + self.eyStr
            )
            csTester.checkDataQuality(raiseIfMissing = False)
            
        


    # Note, this should be calculated on the filtered groups (after irrelevant pops are excluded)
    def createSegmentBins(self):
        self.dta['gittlemanAgeGroup_' + self.syStr] = pd.cut(self.dta['ageR_' + self.syStr],bins=[0,25,35,45, 55, 65, 1000], right= False, labels=['0to24','25to34','35to44','45to54','55to64', '65to100'])
        self.dta['gittlemanIncomeGroup_PreTaxReal_' + self.inflatedEnd] = wQCut(self.dta, 'averageRealBeforeTaxIncome_AllYears_' + self.inflatedTimespan, 'LongitudinalWeightHH_' + self.syStr, 4)
        self.dta['gittlemanIncomeGroup_PostTaxReal_' + self.inflatedEnd] = wQCut(self.dta, 'averageRealAfterTaxIncome_AllYears_' + self.inflatedTimespan, 'LongitudinalWeightHH_' + self.syStr, 4)
          
        # From PSID (1994)
        # Values in the range 1-16 represent the actual grade of school completed; e.g., a value of
        # 8 indicates that the Head completed the eighth grade. A code value of 17 indicates that
        # the Head completed at least some postgraduate work.
        self.dta['gittlemanEducationGroup_' + self.syStr] = pd.cut(self.dta['educationYearsR_' + self.syStr],bins=[0,12,13,16, 17], right= False, labels=['Less than High School','High School Graduate', 'Some College', 'College Grad'])
        self.dta['gittlemanMaritalStatusGroup_' + self.syStr] = self.dta['martialStatusR_' + self.syStr].copy()
        self.dta.loc[ ~(self.dta['gittlemanMaritalStatusGroup_' + self.syStr] == 'Married'), 'gittlemanMaritalStatusGroup_' + self.syStr] = 'Not married'
        # self.dta.martialStatusGenR.replace({1:'MarriedOrCohabit', 2: 'Never Married', 3: 'Widowed', 4: 'Divorced/Annulled', 5: 'Separated',8: None, 9: None}, inplace=True)

         
    
    def calcWeightedAggResultsForYear(self):

        aggDictionary = {
                    'familyInterview_N': ('familyInterviewId_' +self.eyStr,'count'),
                    'familyInterview_TotalWeights': ('familyInterviewId_' +self.eyStr,'SumOfWeights'),

                    # Values needed for Savings Calc
                    'real_pre_tax_income_sum' : ('averageRealBeforeTaxIncome_AllYears_' + self.inflatedTimespan, 'sum'),
                    'real_after_tax_income_sum' : ('averageRealAfterTaxIncome_AllYears_' + self.inflatedTimespan, 'sum'),

                    'changeInRealNetWorth_sum' : ('changeInRealNetWorth_' + self.inflatedTimespan, 'sum'),
                    'netactive_real_sum': ('Total_NetActiveSavings_'  + self.inflatedTimespan, 'sum'),
                    
                    'active_median': ('activeSavingsRate_PerPerson_' + self.inflatedTimespan, 'median'),

                    # Input Values for Savings Calc
                    'change_in_asset_value_sum': ('Total_ChangeInWealth_'  + self.inflatedTimespan, 'sum'),
                    'total_capital_gains_sum': ('Total_CapitalGains_'  + self.inflatedTimespan, 'sum'),
                    'total_gross_savings_sum': ('Total_GrossSavings_'  + self.inflatedTimespan, 'sum'),

                    # Values used to compare with Descriptive Stats
                    'real_networth_mean': ('inflatedNetWorthWithHome_' + self.inflatedEnd, 'mean'),
                    'real_networth_median': ('inflatedNetWorthWithHome_' + self.inflatedEnd, 'median'),
                    'real_recalc_networth_mean': ('inflatedNetWorthWithHomeRecalc_' + self.inflatedEnd, 'mean'),
                    'reacl_recalc_networth_median': ('inflatedNetWorthWithHomeRecalc_' + self.inflatedEnd, 'median'),

                    'income_totaltaxable_avg': ('totalIncomeHH_' + self.eyStr, 'mean'),
                    'income_totaltaxable_median': ('totalIncomeHH_' + self.eyStr, 'median'),
                    
                    'real_after_tax_income_avg': ('averageRealAfterTaxIncome_AllYears_' + self.inflatedTimespan, 'mean'),
                    'real_after_tax_income_median': ('averageRealAfterTaxIncome_AllYears_' + self.inflatedTimespan, 'median'),
                    
                    } 
        
                
        dataMask = (self.dta['cleaningStatus_' + self.eyStr] == 'Keep')
        
        weightVar = 'LongitudinalWeightHH_' + self.syStr
                        
        results = pd.DataFrame(wAgg(self.dta.loc[dataMask], aggregationDict = aggDictionary, varForWeights= (weightVar))).transpose()
        results['Source'] = 'All_' + self.eyStr
        
        resultsByRace = wGroupByAgg(self.dta.loc[dataMask], ['raceR_' + self.syStr], aggregationDict = aggDictionary, varForWeights = (weightVar)).reset_index()
        resultsByRace['Source'] = 'Race_' + self.eyStr
                
        resultsByAge = wGroupByAgg(self.dta.loc[dataMask], ['gittlemanAgeGroup_' + self.syStr], aggregationDict = aggDictionary, varForWeights = (weightVar)).reset_index()
        resultsByAge['Source'] = 'Age_' + self.eyStr 

        resultsByIncome = wGroupByAgg(self.dta.loc[dataMask], ['gittlemanIncomeGroup_PreTaxReal_' + self.inflatedEnd], aggregationDict = aggDictionary, varForWeights = (weightVar)).reset_index()
        resultsByIncome['Source']='Income' + self.inflatedEnd
        

        results = pd.concat([resultsByRace, results, resultsByAge, resultsByIncome], ignore_index=True, sort=False)
        
        results['activeSavings_AvgAsSums_' + self.inflatedTimespan] = results.netactive_real_sum / (results.real_pre_tax_income_sum * self.duration)

        if not os.path.exists(os.path.join(self.baseDir, self.outputSubDir)):
            os.makedirs(os.path.join(self.baseDir, self.outputSubDir))

        results.to_csv(os.path.join(self.baseDir, self.outputSubDir, 'SavingsRates_Weighted_' + self.eyStr +'.csv'))
        
        return results



    def calcDescriptivesForTimePeriod(self):

        
        # Table 3: Summary Statistics on Wealth 1984-1994
        # Also: Appendix Table 1, part B
                
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

        weightVar = 'LongitudinalWeightHH_' + self.syStr
        segmentedResults = wGroupByAgg(self.dta, ['raceR_' + self.syStr], aggregationDict = aggDictionary, varForWeights = (weightVar)).reset_index()
        segmentedResults['Source'] = 'RaceR'
        segmentedResults.to_csv(os.path.join(self.baseDir, self.outputSubDir, 'Table3_AndAppendixTable1_WealthForPeriod_' + self.timespan +'.csv'))
    
        
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

                    'total_ira_mean': ('netIRAandAnnuityChange_' + self.inflatedTimespan, 'mean'),
                    'total_ira_percentiles_25': ('netIRAandAnnuityChange_' + self.inflatedTimespan, 'percentile', [.25]),
                    'total_ira_percentiles_50': ('netIRAandAnnuityChange_' + self.inflatedTimespan, 'percentile', [.5]),
                    'total_ira_percentiles_75': ('netIRAandAnnuityChange_' + self.inflatedTimespan, 'percentile', [.75]),

                    'total_activesavings_mean': ('Total_NetActiveSavings_' + self.inflatedTimespan, 'mean'),
                    'total_activesavings_percentile_25': ('Total_NetActiveSavings_' + self.inflatedTimespan, 'percentile', [.25]),
                    'total_activesavings_percentiles_50': ('Total_NetActiveSavings_' + self.inflatedTimespan, 'percentile', [.5]),
                    'total_activesavings_percentiles_75': ('Total_NetActiveSavings_' + self.inflatedTimespan, 'percentile', [.75]),
        } 

        weightVar = 'LongitudinalWeightHH_' + self.syStr
        segmentedResults = wGroupByAgg(self.dta, ['raceR_' + self.syStr], aggregationDict = aggDictionary, varForWeights = (weightVar)).reset_index()
        segmentedResults['Source'] = 'RaceR'
        segmentedResults.to_csv(os.path.join(self.baseDir, self.outputSubDir, 'Table4_WealthComponent_' + self.inflatedTimespan +'.csv'))


        # Table 5: Summary stats on Rates of Change in Wealth and its Components
        self.dta['WealthAppreciationPercent_' + self.inflatedTimespan] =  self.dta['inflatedNetWorthWithHome_' + self.inflatedEnd].sub(self.dta['inflatedNetWorthWithHome_' + self.inflatedStart],fill_value=0).div(self.dta['inflatedNetWorthWithHome_' + self.inflatedStart],fill_value=0)
        self.dta['CapitalGainsPercent_' + self.inflatedTimespan] =  self.dta['Total_CapitalGains_' + self.inflatedTimespan].div(self.dta['inflatedNetWorthWithHome_' + self.inflatedStart],fill_value=0)
        self.dta['InheritancesPercent_' + self.inflatedTimespan] =  self.dta['largeGift_All_AmountHH_' + self.inflatedTimespan].div(self.dta['inflatedNetWorthWithHome_' + self.inflatedStart],fill_value=0)
        self.dta['MoveWealthPercent_' + self.inflatedTimespan] =  self.dta['netAssetMove_' + self.inflatedTimespan].div(self.dta['inflatedNetWorthWithHome_' + self.inflatedStart],fill_value=0)
        self.dta['IRAPercent_' + self.inflatedTimespan] =  self.dta['netIRAandAnnuityChange_' + self.inflatedTimespan].div(self.dta['inflatedNetWorthWithHome_' + self.inflatedStart],fill_value=0)
        
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

                    'ira_rate_median': ('IRAPercent_' + self.inflatedTimespan, 'median'), 
                    'ira_sum': ('netIRAandAnnuityChange_' + self.inflatedTimespan, 'sum'),                    

                    } 

        weightVar = 'LongitudinalWeightHH_' + self.syStr
        segmentedResults = wGroupByAgg(self.dta, ['raceR_' + self.syStr], aggregationDict = aggDictionary, varForWeights = (weightVar)).reset_index()
        segmentedResults['Source'] = 'RaceR'

        segmentedResults['wealth_appreciation_rate_AvgsAsSums_' + self.inflatedTimespan] = \
                (segmentedResults.real_networth_end_sum - segmentedResults.real_networth_start_sum )/ (segmentedResults.real_networth_start_sum * self.duration) # TODO -- should this be / duration?

        segmentedResults['active_savings_rate_AvgAsSums_' + self.inflatedTimespan] = segmentedResults.netactive_real_sum / (segmentedResults.real_pre_tax_income_sum * self.duration)

        segmentedResults['capital_gains_rate_AvgAsSums_' + self.inflatedTimespan] = segmentedResults.capital_gains_sum / (segmentedResults.real_networth_start_sum * self.duration)

        segmentedResults['inheritance_rate_AvgAsSums_' + self.inflatedTimespan] = segmentedResults.inheritance_sum / (segmentedResults.real_networth_start_sum * self.duration)

        segmentedResults['movewealth_rate_AvgAsSums_' + self.inflatedTimespan] = segmentedResults.movewealth_sum / (segmentedResults.real_networth_start_sum * self.duration)

        segmentedResults['ira_rate_AvgAsSums_' + self.inflatedTimespan] = segmentedResults.ira_sum / (segmentedResults.real_networth_start_sum * self.duration)

        segmentedResults.to_csv(os.path.join(self.baseDir, self.outputSubDir, 'Table5_WealthForPeriod_' + self.inflatedTimespan +'.csv'))
        

        # Appendix Table 2: Demographics
        self.dta['headIsAfricanAmerican_' + self.syStr] =  self.dta['raceR_' + self.syStr].eq('Black') 
        self.dta['headIsFemale_' + self.syStr] =  self.dta['genderR_' + self.syStr].eq('Female') 

        self.dta['headIsCollegeGrad_' + self.syStr] =  False
        self.dta.loc[self.dta['educationYearsR_' + self.syStr] >= 16, 'headIsCollegeGrad_' + self.syStr] = True

        self.dta['headHasSomeCollege_' + self.syStr] =  False
        self.dta.loc[ (self.dta['educationYearsR_' + self.syStr] >= 9) & (self.dta['educationYearsR_' + self.syStr] < 12), 'headSomeCollege_' + self.syStr] = True

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
        
        weightVar = 'LongitudinalWeightHH_' + self.syStr
                        
        results = pd.DataFrame(wAgg(self.dta.loc[dataMask], aggregationDict = aggDictionary, varForWeights= (weightVar))).transpose()
        results['Source'] = 'All_' + self.eyStr

        results.to_csv(os.path.join(self.baseDir, self.outputSubDir, 'AppendixTable2_Demographics_' + self.timespan +'.csv'))


        
    def calcDescriptivesForYear(self, analysisYear, toYear):
        self.clearData()
        self.setPeriod(analysisYear, analysisYear, toYear)
        self.readData()
        self.calcAfterTaxIncome(True)
        self.inflateValues(True)
        self.calcAverageMoneyIncome()

        self.cleanData_CrossSectional(analysisYear)        
        # self.cleanData_Longitudinal(preliminaryClean_beforeSavingsCalcAnalysis=True)
        self.createSegmentBins()


        # Table 1: Wealth Characteristics by Head of Family Income, 1994
        # PLUS Appendix Table 1, Cross-Sectional Component
        varsToSegmentTo = ['gittlemanAgeGroup_' + self.syStr,
                           'gittlemanEducationGroup_' + self.syStr,
                           'gittlemanMaritalStatusGroup_' + self.syStr,
                           'gittlemanIncomeGroup_PreTaxReal_' + self.inflatedEnd]
                                
        aggDictionary = {
                    'familyInterview_N': ('familyInterviewId_' +self.eyStr,'count'),
                    'familyInterview_TotalWeights': ('familyInterviewId_' +self.eyStr,'SumOfWeights'),

                    # Values used to compare with Descriptive Stats
                    'real_networth_mean': ('inflatedNetWorthWithHome_' + self.inflatedEnd, 'mean'),
                    'real_networth_median': ('inflatedNetWorthWithHome_' + self.inflatedEnd, 'median')
                    } 
        
                
        weightVar = 'LongitudinalWeightHH_' + self.syStr

        results = pd.DataFrame(wAgg(self.dta, aggregationDict = aggDictionary, varForWeights= (weightVar))).transpose()
        results['Source'] = 'All_' + self.eyStr

        segmentedResults = wGroupByAgg(self.dta, ['raceR_' + self.syStr], aggregationDict = aggDictionary, varForWeights = (weightVar)).reset_index()
        segmentedResults['Source'] = 'RaceR'    
        segmentedResults.to_csv(os.path.join(self.baseDir, self.outputSubDir, 'AppendixTable1_CrossSectionalWealth_' + str(analysisYear) +'.csv'))

        results = pd.concat([segmentedResults, results], ignore_index=True, sort=False)
        
        for var in varsToSegmentTo:
            segmentVar = 'raceR_' + var
            segmentVars = ['raceR_' + self.syStr, var]
            # tmpDta[segmentVar] =  tmpDta['raceR_' + self.syStr] + tmpDta[var].astype(str) 
            segmentedResults = wGroupByAgg(self.dta, segmentVars, aggregationDict = aggDictionary, varForWeights = (weightVar)).reset_index()
            segmentedResults['Source'] = segmentVar

            results = pd.concat([segmentedResults, results], ignore_index=True, sort=False)
        
        results.to_csv(os.path.join(self.baseDir, self.outputSubDir, 'Table1_WealthByGroup_' + str(analysisYear) +'.csv'))


        # Table 2: Portfolio Composition of Wealth by Race 
        weightVar = 'LongitudinalWeightHH_' + self.syStr
        tmpDta = self.dta.copy()

        componentVars = ['House_Net','OtherRealEstate_Net', 'Vehicle_Net', 'Business_Net', 'BrokerageStocks_Net',  'CheckingAndSavings_Net', 'OtherAssets_Net', 'AllOtherDebts_Net']
        theVars = ['valueOf' + s + '_' + self.syStr for s in componentVars] + ['NetWorthWithHomeRecalc_' + self.syStr]
        tmpDta[theVars] = tmpDta[theVars].fillna(value=0)
        
        tmpDta['House_HasAsset_' + self.syStr] = tmpDta['valueOfHouse_Net_' + self.syStr].ne(0)
        tmpDta['OtherRealEstate_HasAsset_' + self.syStr] = tmpDta['valueOfOtherRealEstate_Net_' + self.syStr].ne(0)
        tmpDta['Vehicle_HasAsset_' + self.syStr] = tmpDta['valueOfVehicle_Net_' + self.syStr].ne(0)
        tmpDta['Business_HasAsset_' + self.syStr] = tmpDta['valueOfBusiness_Net_' + self.syStr].ne(0)
        tmpDta['BrokerageStocks_HasAsset_' + self.syStr] = tmpDta['valueOfBrokerageStocks_Net_' + self.syStr].ne(0)
        tmpDta['CheckingAndSavings_HasAsset_' + self.syStr] = tmpDta['valueOfCheckingAndSavings_Net_' + self.syStr].ne(0)
        tmpDta['OtherAssets_HasAsset_' + self.syStr] = tmpDta['valueOfOtherAssets_Net_' + self.syStr].ne(0)
        tmpDta['OtherDebts_HasAsset_' + self.syStr] = tmpDta['valueOfAllOtherDebts_Net_' + self.syStr].ne(0)

        tmpDta['House_PercentOfWealth_' + self.syStr] = tmpDta['valueOfHouse_Net_' + self.syStr].div(tmpDta['NetWorthWithHomeRecalc_' + self.syStr], fill_value=0)
        tmpDta['OtherRealEstate_PercentOfWealth_' + self.syStr] = tmpDta['valueOfOtherRealEstate_Net_' + self.syStr].div(tmpDta['NetWorthWithHomeRecalc_' + self.syStr], fill_value=0)
        tmpDta['Vehicle_PercentOfWealth_' + self.syStr] = tmpDta['valueOfVehicle_Net_' + self.syStr].div(tmpDta['NetWorthWithHomeRecalc_' + self.syStr], fill_value=0)
        tmpDta['Business_PercentOfWealth_' + self.syStr] = tmpDta['valueOfBusiness_Net_' + self.syStr].div(tmpDta['NetWorthWithHomeRecalc_' + self.syStr], fill_value=0)
        tmpDta['BrokerageStocks_PercentOfWealth_' + self.syStr] = tmpDta['valueOfBrokerageStocks_Net_' + self.syStr].div(tmpDta['NetWorthWithHomeRecalc_' + self.syStr], fill_value=0)
        tmpDta['CheckingAndSavings_PercentOfWealth_' + self.syStr] = tmpDta['valueOfCheckingAndSavings_Net_' + self.syStr].div(tmpDta['NetWorthWithHomeRecalc_' + self.syStr], fill_value=0)
        
        tmpDta['OtherAssets_PercentOfWealth_' + self.syStr] = tmpDta['valueOfOtherAssets_Net_' + self.syStr].div(tmpDta['NetWorthWithHomeRecalc_' + self.syStr], fill_value=0)
        tmpDta['OtherAssets_PercentOfWealth2_' + self.syStr] = tmpDta['valueOfOtherAssets_Net_' + self.syStr].div(tmpDta['NetWorthWithHome_' + self.syStr], fill_value=0)
        tmpDta['OtherDebts_PercentOfWealth_' + self.syStr] = tmpDta['valueOfAllOtherDebts_Net_' + self.syStr].div(tmpDta['NetWorthWithHomeRecalc_' + self.syStr], fill_value=0)
          
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
                    'OtherDebts_HasAsset_Percent': ('OtherDebts_HasAsset_' + self.syStr, 'mean'),
                    
                    # Values used to compare with Descriptive Stats
                    'House_PercentOfWealth_Avg': ('House_PercentOfWealth_' + self.syStr, 'mean'),
                    'OtherRealEstate_PercentOfWealth_Avg': ('OtherRealEstate_PercentOfWealth_' + self.syStr, 'mean'),
                    'Vehicle_PercentOfWealth_Avg': ('Vehicle_PercentOfWealth_' + self.syStr, 'mean'),
                    'Business_PercentOfWealth_Avg': ('Business_PercentOfWealth_' + self.syStr, 'mean'),
                    'BrokerageStocks_PercentOfWealth_Avg': ('BrokerageStocks_PercentOfWealth_' + self.syStr, 'mean'),
                    'CheckingAndSavings_PercentOfWealth_Avg': ('CheckingAndSavings_PercentOfWealth_' + self.syStr, 'mean'),
                    'OtherAssets_PercentOfWealth_Avg': ('OtherAssets_PercentOfWealth_' + self.syStr, 'mean'),
                    'OtherDebts_PercentOfWealth_Avg': ('OtherDebts_PercentOfWealth_' + self.syStr, 'mean'),

                    # Values used to compare with Descriptive Stats
                    'NetWorthWithHomeRecalc_Sum': ('NetWorthWithHomeRecalc_' + self.syStr, 'sum'),
                    'NetWorth_Sum': ('NetWorthWithHome_' + self.syStr, 'sum'),
                    'House_Value_Sum': ('valueOfHouse_Net_' + self.syStr, 'sum'),
                    'OtherRealEstate_Value_Sum': ('valueOfOtherRealEstate_Net_' + self.syStr, 'sum'),
                    'Vehicle_Value_Sum': ('valueOfVehicle_Net_' + self.syStr, 'sum'),
                    'Business_Value_Sum': ('valueOfBusiness_Net_' + self.syStr, 'sum'),
                    'BrokerageStocks_Value_Sum': ('valueOfBrokerageStocks_Net_' + self.syStr, 'sum'),
                    'CheckingAndSavings_Value_Sum': ('valueOfCheckingAndSavings_Net_' + self.syStr, 'sum'),
                    'OtherAssets_Value_Sum': ('valueOfOtherAssets_Net_' + self.syStr, 'sum'),
                    'OtherDebts_Value_Sum': ('valueOfAllOtherDebts_Net_' + self.syStr, 'sum'),
                    } 

        segmentedResults = wGroupByAgg(tmpDta, 'raceR_' + self.syStr, 
                                       aggregationDict = aggDictionary, 
                                       varForWeights = (weightVar)).reset_index()
        segmentedResults['Source'] = segmentVar
    
        segmentedResults['House_PercentOfWealth_AvgAsSums_' + self.syStr] =  segmentedResults.House_Value_Sum / (segmentedResults.NetWorthWithHomeRecalc_Sum)
        segmentedResults['OtherRealEstate_PercentOfWealth_AvgAsSums_' + self.syStr] =  segmentedResults.OtherRealEstate_Value_Sum / (segmentedResults.NetWorthWithHomeRecalc_Sum)
        segmentedResults['Vehicle_PercentOfWealth_AvgAsSums_' + self.syStr] =  segmentedResults.Vehicle_Value_Sum / (segmentedResults.NetWorthWithHomeRecalc_Sum)
        segmentedResults['Business_PercentOfWealth_AvgAsSums_' + self.syStr] =  segmentedResults.Business_Value_Sum / (segmentedResults.NetWorthWithHomeRecalc_Sum)
        segmentedResults['BrokerageStocks_PercentOfWealth_AvgAsSums_' + self.syStr] =  segmentedResults.BrokerageStocks_Value_Sum / (segmentedResults.NetWorthWithHomeRecalc_Sum)
        segmentedResults['CheckingAndSavings_PercentOfWealth_AvgAsSums_' + self.syStr] =  segmentedResults.CheckingAndSavings_Value_Sum / (segmentedResults.NetWorthWithHomeRecalc_Sum)
        segmentedResults['OtherAssets_PercentOfWealth_AvgAsSums_' + self.syStr] =  segmentedResults.OtherAssets_Value_Sum / (segmentedResults.NetWorthWithHomeRecalc_Sum)
        segmentedResults['OtherAssets_PercentOfWealth_AvgAsSums2_' + self.syStr] =  segmentedResults.OtherAssets_Value_Sum / (segmentedResults.NetWorth_Sum)
        segmentedResults['OtherDebts_PercentOfWealth_AvgAsSums_' + self.syStr] =  segmentedResults.OtherDebts_Value_Sum / (segmentedResults.NetWorthWithHomeRecalc_Sum)
        
        segmentedResults.to_csv(os.path.join(self.baseDir, self.outputSubDir, 'Table2_AssetsByType_' + str(analysisYear) +'.csv'))
        
        
    def runRegressionAndExtract(self, dta, IVs, DVs, reg_type, label, resultsSoFar = None):
        allVars = IVs + DVs + ['LongitudinalWeightHH_' + self.syStr ]
        detailedResults = wRegression(dta[allVars].dropna(), IVs,DVs,varforWeights ='LongitudinalWeightHH_' + self.syStr ,reg_type = reg_type)
        print(detailedResults.summary())
        results = extractRegressionResults(detailedResults)
        results['Source'] = label
        results['StartYear'] = self.startYear
        results['EndYear'] = self.endYear
        results['ToYear'] = self.toYear
        results = results.reset_index()
        results.rename(columns={'index':'var'}, inplace=True)
        if (resultsSoFar is None):
            return results
        else:
            return pd.concat([resultsSoFar, results], ignore_index=True)


    def calcRegressionOnSavings(self):
        
        tmp = self.dta.loc[self.dta['raceR_' + self.syStr].isin(['White', 'Black'])].copy()
        dummies = pd.get_dummies(tmp['raceR_' + self.syStr], drop_first= False)
        tmp = tmp.join(dummies)

        tmp['MarriedStart'] =  tmp['martialStatusR_' + self.syStr].eq("Married").astype(int)
        tmp['MarriedEnd'] =  tmp['martialStatusR_' + self.eyStr].eq("Married").astype(int)

        # dummies = pd.get_dummies(tmp['familyIsMarried_' + self.syStr], drop_first= False)
        # tmp = tmp.join(dummies)


        tmp.rename(columns={'averageRealBeforeTaxIncome_AllYears_' + self.inflatedTimespan: 'Income',
                            'activeSavingsRate_PerPerson_' + self.inflatedTimespan : 'SavingsRate',
                            'ageR_' + self.syStr: 'Age',
                            'NumChildrenInFU_' + self.syStr: 'NumChildren',
                            'educationYearsR_' + self.syStr: 'Education'
                            }, inplace=True)        
        
        tmp['Income_Sq'] = tmp['Income']**2
        tmp['Age_Sq'] = tmp['Age']**2

        # are age of head and its square, sex and education of head, marital status at start and end of period, and number of children

        resultsSoFar = self.runRegressionAndExtract(tmp, IVs = ['Black'], DVs = ['SavingsRate'], reg_type='OLS', label = "Race OLS", resultsSoFar = None)
        
        resultsSoFar = self.runRegressionAndExtract(tmp, IVs = ['Black', 'Income', 'Income_Sq'], DVs = ['SavingsRate'], reg_type='OLS', label = "Race&Income OLS", resultsSoFar = resultsSoFar)

        resultsSoFar = self.runRegressionAndExtract(tmp, IVs = ['Black', 'Income', 'Income_Sq', 'Age', 'Age_Sq', 'Education', 'MarriedStart', 'MarriedEnd', 'NumChildren'], DVs = ['SavingsRate'], reg_type='OLS', label = "Race&Others OLS", resultsSoFar = resultsSoFar)

        resultsSoFar.to_csv(os.path.join(self.baseDir, self.outputSubDir, "CombinedGittleman_" + self.inflatedTimespan + "_Regressions.csv"), index=False)

        resultsSoFar = self.runRegressionAndExtract(tmp, IVs = ['Black'], DVs = ['SavingsRate'], reg_type='Quantile', label = "Race Quantile", resultsSoFar = resultsSoFar)
        
        resultsSoFar = self.runRegressionAndExtract(tmp, IVs = ['Black', 'Income', 'Income_Sq'], DVs = ['SavingsRate'], reg_type='Quantile', label = "Race&Income Quantile", resultsSoFar = resultsSoFar)

        resultsSoFar = self.runRegressionAndExtract(tmp, IVs = ['Black', 'Income', 'Income_Sq', 'Age', 'Age_Sq', 'Education', 'MarriedStart', 'MarriedEnd', 'NumChildren'], DVs = ['SavingsRate'], reg_type='Quantile', label = "Race&Others Quantile", resultsSoFar = resultsSoFar)

        resultsSoFar.to_csv(os.path.join(self.baseDir, self.outputSubDir, "CombinedGittleman_" + self.inflatedTimespan + "_Regressions.csv"), index=False)


    def executeForTimespan(self, startYear, endYear, toYear):
        self.clearData()
        self.setPeriod(startYear, endYear, toYear)
        self.readData()
        self.checkQualityOfInputData()
                                
        self.calcIfValueOnMoveAndChangedHeadAtAnyPoint()
        
        self.calcAfterTaxIncome(True)
        self.inflateValues(True)
        self.calcAverageMoneyIncome()
        self.calcDetermineAssetLevelCapitalGains()
        self.cleanData_Longitudinal_PrepForSavingsCalcAnalysis()
        
        self.calcSavingsRate_ActiveSavings()
        # self.cleanData_Longitudinal_PostSavingsCalc()
        self.createSegmentBins()
        
        self.dta = ReplicationAnalyzer.selectiveReorder(self.dta, 
                                    ['cleaningStatus_' + self.eyStr, 
                                     'raceR_' + self.syStr,
                                     'FederalIncomeTaxesRS_' + self.eyStr,
                                    'fiitax_' + self.eyStr,
                                    'inflatedNetWorthWithHome_' + self.inflatedStart,
                                    'inflatedNetWorthWithHome_' + self.inflatedEnd,
                                    'changeInRealNetWorth_' + self.inflatedTimespan,

                                    'inflatedAfterTaxIncome_' + self.inflatedStart,    
                                    'inflatedAfterTaxIncome_' + self.inflatedEnd,    
                                    'averageRealAfterTaxIncome_AllYears_' + self.inflatedTimespan,
                                    'averageRealBeforeTaxIncome_AllYears_' + self.inflatedTimespan,
                                     
                                    'Total_NetActiveSavings_'  + self.inflatedTimespan,
                                    'activeSavingsRate_PerPerson_' + self.inflatedTimespan,
                                    
                                    'Total_ChangeInWealth_'  + self.inflatedTimespan,
                                    'Total_CapitalGains_'  + self.inflatedTimespan,
                                    'Total_GrossSavings_'  + self.inflatedTimespan,
                                    ])

        self.dta.to_csv(os.path.join(self.baseDir, self.outputSubDir, "CombinedGittleman_" + self.inflatedTimespan + ".csv"), index=False)
        results = self.calcWeightedAggResultsForYear()
        
        # Check against Gittleman results for this period (Tables 3+)
        self.calcDescriptivesForTimePeriod()
        
        # Finally, Check Regressions - Table 6
        # TODO -- switch from Python Quantile regression to R's
        #  self.calcRegressionOnSavings()
        
        return results

              
    def doIt(self):
        toYear = 1998  # "Net worth is measured in thousands of 1998 dollars"
        yearsWealthDataCollected = [1984, 1989, 1994] + list(range(1999, 2017+2, 2))
        # yearsWealthDataCollected = [1989, 1994]
        startYear = yearsWealthDataCollected[0]
        
        # Calculate Single-year descriptive stats on this year (Gittleman Table 1, 2)
        self.calcDescriptivesForYear(startYear, toYear)

        results = None
        for endYear in yearsWealthDataCollected[1:]:

            # Calculate Single-year descriptive stats on this year - note this nukes the class's data -- don't to in the mdidle if any analysis
            self.calcDescriptivesForYear(endYear, toYear)
            
            # Get our core results: change in wealth over time
            tempResults = self.executeForTimespan(startYear, endYear, toYear)

            tempResults.rename(columns={'raceR_' + str(startYear): 'raceR', 
                                        'gittlemanAgeGroup_' + str(startYear): 'gittlemanAgeGroup',
                                        'gittlemanIncomeGroup_PreTaxReal_' + str(endYear) + '_as_' + str(toYear): 'gittlemanIncomeGroup_PreTaxReal_as_' + str(toYear),
                                        'activeSavings_AvgAsSums_' + self.inflatedTimespan: 'activeSavings_AvgAsSums'
                                        }, inplace=True)
            tempResults['StartYear'] = startYear
            tempResults['EndYear'] = endYear
            tempResults['InflatedToYear'] = toYear
            if results is None:
                results = tempResults
            else:
                results = pd.concat([results, tempResults], ignore_index=True)
                
            
            # Get ready for next year
            startYear = endYear
        
        self.combinedResults = results
        
        self.combinedResults = ReplicationAnalyzer.selectiveReorder(results, ['StartYear', 'EndYear', 
                                                                             'InflatedToYear', 'Source', 
                                                                             'active_median', 'activeSavings_AvgAsSums'
                                                                             ])
        self.combinedResults.to_csv(os.path.join(self.baseDir, self.outputSubDir, "CombinedGittleman_CombinedResults_" + str(yearsWealthDataCollected[1]) + '_to_' + str(yearsWealthDataCollected[-1]) +  ".csv"), index=False)
        
        # results.to_csv(os.path.join(self.baseDir, self.outputSubDir, "CombinedGittleman_CombinedResults_" + str(yearsWealthDataCollected[1]) + '_to_' + str(yearsWealthDataCollected[-1]) +  ".csv"), index=False)
        # startYear = yearsWealthDataCollected[1]
        #for endYear in yearsWealthDataCollected[1:]:
         

def extractRegressionResults(results):
    return pd.concat([results.params.rename("params",inplace=True), results.pvalues.rename("pvalues",inplace=True)], axis=1, names=['params', 'pvalues'])

''' Allow execution from command line, etc'''    
if __name__ == "__main__":
    analyzer = GittlemanAnalysis(familyBaseFileNameWithPath = 
                             os.path.join('C:/dev/sensitive_data/InvestorSuccess/Inequality',
                                          'finalInputPSID', "extractedPSID_Mapped_Recoded_"),
            individualBaseFileNameWithPath = os.path.join('C:/dev/sensitive_data/InvestorSuccess/Inequality',
                                          'finalInputPSID', "extractedPSID_Individual_Mapped_Recoded"))
    analyzer.doIt()
