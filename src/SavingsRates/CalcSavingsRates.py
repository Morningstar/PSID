import os
from Survey.SurveyFunctions import *
import Inflation.CPI_InflationReader as CPI_InflationReader
import MStarReport.InequalityAnalysisBase as InequalityAnalysisBase

''' Helper Functions on Rates of Return '''
def calcChangefromRoR_Series(dta, startValueField_Uninflated, NominalRoRField, duration, inflationFactorForEnd):
    # endValue_Nominal = startValue_Nominal * ((1 + NominalRor)**duration)
    # ChangeUnInflated = endValue - startValue
    # ChangeUnInflated = startValue * ((1 + ror)**duration) - startValue
    # ChangeUnInflated = startValue * ((1 + ror)**duration - 1)
    # Change = startValue * ((1 + ror)**duration - 1) * inflationFactorForEnd
    return (dta[startValueField_Uninflated]*((1 + dta[NominalRoRField])**duration - 1)*(inflationFactorForEnd))

def calcChangefromRoR_Value(startValue_Uninflated, NominalRoR, duration, inflationFactorForEnd):
    return (startValue_Uninflated*inflationFactorForEnd) * ((1 + NominalRoR)**duration - 1)

def calcNominalRoRfromChange_Series(dta, startValueField_Uninflated, changeField_Inflated, duration, inflationFactorForEnd):
    # ChangeInflatedToTarget = startValue * ((1 + NominalRor)**duration - 1)*inflationFromEndToTarget
    # ((1 + ror)**duration - 1)*inflationFromEndToTarget = Change/startValue
    # (1 + ror)**duration = Change/(startValue*inflationFromEndToTarget) + 1
    # (1 + ror) = (Change/(startValue*inflationFromEndToTarget)) + 1)**(1/duration)
    # ror = (Change/(startValue*inflationFromEndToTarget)) + 1)**(1/duration) - 1
    return (((dta[changeField_Inflated] / (dta[startValueField_Uninflated]*inflationFactorForEnd)) + 1.0)**(1.0/duration) - 1.0)

def calcNominalRoRfromChange_Value(startValue_Uninflated, change_Inflated, duration, inflationFactorForEnd):
    return (((change_Inflated / (startValue_Uninflated*inflationFactorForEnd)) + 1)**(1/duration) - 1)

class CalcSavingsRates(InequalityAnalysisBase.InequalityAnalysisBase):
    '''
    Calculate Household-Asset-level savings & cap gains, then calculate HH-level savings rates.
    This is the core added value of the inequality analyses -- the rest is just prep and summary.
    We build on the examples of Dynan et al & Gittleman et all, expanding the analysis to handle
    new asset classes available in later data, and two combine the lessons from each author
    '''

    CLASS_ownershipVars = {'OtherRealEstate_Net':'OtherRealEstate',
                     'Vehicle_Net':'Vehicle',
                     'BrokerageStocks_Net': 'BrokerageStocks',
                     'CheckingAndSavings_Net': 'CheckingAndSavings',
                     'Business_Net': 'Business',
                     'OtherAssets_Net':'OtherAssets',
                     'AllOtherDebts_Net':'AllOtherDebts',
                     'EmployerRetirePlan_Gross':'EmployerRetirePlan',
                     'PrivateRetirePlan_Gross':'PrivateRetirePlan',
                     }

    CLASS_acceptable_implied_annual_nominal_capgains = 0.2 # 20%
    CLASS_assumed_investment_fees = 0.005 # 50 Bps
    # CLASS_assumed_annual_nominal_vehicle_appreciation = -0.05 # Loses 5% of value each year
    CLASS_assumed_annual_nominal_vehicle_appreciation = 0.00 # Loses 5% of value each year

    def __init__(self, baseDir, familyInputSubDir, inputBaseName,outputBaseName, outputSubDir):
        super().__init__(baseDir, inputSubDir=familyInputSubDir, inputBaseName = inputBaseName,outputBaseName = outputBaseName, outputSubDir=outputSubDir)
        self.inflator = CPI_InflationReader.CPIInflationReader()
        self.investmentReturns = pd.read_csv(os.path.join(self.baseDir, "otherInput", "annualReturns_Mstar.csv"))
        self.investmentReturns.Date = pd.to_datetime(self.investmentReturns.Date)
        self.excludeRetirementSavings = None

    def getNominalInvestmentReturn_ZeroCoded(self, type):

        # Let's say you're analyzing the period from 1984 to 1989.
        # What is the stock return for that time?
        # Assume you have returns up to the prior year: you'd experience the returns for 1984, 1985, 1986, 1987, 1988
        # The next period would get the returns for 1989+

        returnsThusFar_1Coded = 1
        for yr in range(self.startYear, self.endYear, 1): # include left boundary, don't include right
            targetDate = pd.to_datetime("12/31/" + str(yr))
            row = self.investmentReturns.loc[self.investmentReturns.Date.eq(targetDate),]
            if len(row) != 1:
                raise Exception("Cant find appropriate investment data year " + targetDate)

            if (type == "Stock"):
                preFeeReturn_ZeroCoded = row.Stock.tolist()[0]
            elif (type == "Bond"):
                preFeeReturn_ZeroCoded = row.Bond.tolist()[0]
            elif (type == "Blended"):
                preFeeReturn_ZeroCoded = row['70-30'].tolist()[0]
            else:
                raise Exception("Cant find appropriate investment data type")

            returnsThusFar_1Coded = returnsThusFar_1Coded * (1 + preFeeReturn_ZeroCoded - self.CLASS_assumed_investment_fees)

        return (returnsThusFar_1Coded - 1)


    def recalculateTotalWealth(self):
        # Note - this must occur AFTER fillNoAccountStockValues
        # We have a variable already for net worth: NetWorthWithHomeAnd401k
        # The problem is that it flucuates in crazy ways when there is missing balance data.
        # We can make reasonable assumptions that the balance hasn't changed if the person still has an account, and
        # Start period

        self.dta['NetWorthWithHomeAnd401k_AfterBalanceFillin_' + self.syStr] = \
            self.dta['valueOfHouse_Net_' + self.syStr].fillna(0). \
            add(self.dta['valueOfOtherRealEstate_Net_' + self.syStr], fill_value=0). \
            add(self.dta['valueOfVehicle_Net_' + self.syStr], fill_value=0). \
            add(self.dta['valueOfBusiness_Net_' + self.syStr], fill_value=0). \
            add(self.dta['valueOfBrokerageStocks_Net_' + self.syStr], fill_value=0). \
            add(self.dta['valueOfCheckingAndSavings_Net_' + self.syStr], fill_value=0). \
            add(self.dta['valueOfOtherAssets_Net_' + self.syStr], fill_value=0). \
            add(self.dta['valueOfPrivateRetirePlan_Gross_' + self.syStr], fill_value=0). \
            sub(self.dta['valueOfAllOtherDebts_Net_' + self.syStr], fill_value=0). \
            add(self.dta['valueOfEmployerRetirePlan_Gross_' + self.syStr], fill_value=0)

        self.dta['NetWorthWithHomeAnd401k_AfterBalanceFillin_' + self.eyStr] = \
            self.dta['valueOfHouse_Net_' + self.eyStr].fillna(0). \
            add(self.dta['valueOfOtherRealEstate_Net_' + self.eyStr], fill_value=0). \
            add(self.dta['valueOfVehicle_Net_' + self.eyStr], fill_value=0). \
            add(self.dta['valueOfBusiness_Net_' + self.eyStr], fill_value=0). \
            add(self.dta['valueOfBrokerageStocks_Net_' + self.eyStr], fill_value=0). \
            add(self.dta['valueOfCheckingAndSavings_Net_' + self.eyStr], fill_value=0). \
            add(self.dta['valueOfOtherAssets_Net_' + self.eyStr], fill_value=0). \
            add(self.dta['valueOfPrivateRetirePlan_Gross_' + self.eyStr], fill_value=0). \
            sub(self.dta['valueOfAllOtherDebts_Net_' + self.eyStr], fill_value=0). \
            add(self.dta['valueOfEmployerRetirePlan_Gross_' + self.eyStr], fill_value=0)

        totalInflationEndToInflatedYear = self.inflator.getInflationFactorBetweenTwoYears(self.endYear, self.toYear)
        totalInflationStartToInflatedYear = self.inflator.getInflationFactorBetweenTwoYears(self.startYear, self.toYear)

        self.dta['inflatedNetWorthWithHomeAnd401k_AfterBalanceFillin_' + self.inflatedStart] = self.dta['NetWorthWithHomeAnd401k_AfterBalanceFillin_' + self.syStr] * totalInflationStartToInflatedYear
        self.dta['inflatedNetWorthWithHomeAnd401k_AfterBalanceFillin_' + self.inflatedEnd] = self.dta['NetWorthWithHomeAnd401k_AfterBalanceFillin_' + self.eyStr] * totalInflationEndToInflatedYear
        self.dta['changeInRealNetWorthWithHomeAnd401k_AfterBalanceFillin_' + self.inflatedTimespan] = \
            self.dta['inflatedNetWorthWithHomeAnd401k_AfterBalanceFillin_' + self.inflatedEnd].sub(self.dta['inflatedNetWorthWithHomeAnd401k_AfterBalanceFillin_' + self.inflatedStart])


    def fillNoAccountStockValues(self):
        ownershipVars = self.CLASS_ownershipVars.copy()

        for ownershipVar in ownershipVars.keys():
            valueVar = 'valueOf' + ownershipVar + '_'
            hasVar = 'has' + ownershipVars[ownershipVar] + '_'
            self.dta.loc[(self.dta[valueVar + self.eyStr].isna()) & (self.dta[hasVar + self.eyStr] == False), valueVar + self.eyStr] = 0
            self.dta.loc[(self.dta[valueVar + self.syStr].isna()) & (self.dta[hasVar + self.syStr] == False), valueVar + self.syStr] = 0

        # TODO -- review this.  does it cause bad savings data?
        # For houses, there are too many changes from year to year to properly track. just set to zero
        self.dta['House_ValueIncrease_WhenMoving_' + self.inflatedTimespan].fillna(0, inplace=True)
        self.dta['House_ValueIncrease_WhenNotMoving_' + self.inflatedTimespan].fillna(0, inplace=True)
        self.dta['House_TotalChangeInMortgageDebt_WhenMoving_' + self.inflatedTimespan].fillna(0, inplace=True)
        self.dta['House_TotalChangeInMortgageDebt_WhenNotMoving_' + self.inflatedTimespan].fillna(0, inplace=True)
        self.dta['CostOfMajorHomeRenovations_' + self.eyStr].fillna(0, inplace=True)


    def calcDetermineAssetLevelCapitalGains_SimpliedSWStyle(self):
        '''
        Calculate savings and capital gains among each of 10 asset classes.
        This is the most important 'addition' of the analysis - this is the tricky and theoretically most important part.
        :return:
        :rtype:
        '''

        statusCountsPerVar = []

        totalInflationStartToEndYear = self.inflator.getInflationFactorBetweenTwoYears(self.startYear, self.endYear)
        totalInflationEndToInflatedYear = self.inflator.getInflationFactorBetweenTwoYears(self.endYear, self.toYear)
        totalInflationStartToInflatedYear = self.inflator.getInflationFactorBetweenTwoYears(self.startYear, self.toYear)

        # We'll use the average for flow
        averageAnnualInflationDuringPeriod = ((totalInflationStartToEndYear-1)/self.duration) + 1
        inflationForFlow = averageAnnualInflationDuringPeriod * totalInflationEndToInflatedYear

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

        self.dta['House_NetOfDebtValueIncrease_WhenMoving_' + self.inflatedTimespan] = self.dta[
            'House_ValueIncrease_WhenMoving_' + self.inflatedTimespan].sub(
            self.dta['House_TotalChangeInMortgageDebt_WhenMoving_' + self.inflatedTimespan], fill_value=0)

        self.dta['House_CapitalGains_' + self.inflatedTimespan] = self.dta[
            'House_ValueIncrease_WhenNotMoving_' + self.inflatedTimespan].sub(
            self.dta['CostOfMajorHomeRenovations_' + self.eyStr] * inflationForFlow, fill_value=0)

        self.dta.loc[self.dta['CostOfMajorHomeRenovations_' + self.eyStr].isna() &
            self.dta['House_NetOfDebtValueIncrease_WhenMoving_' + self.inflatedTimespan].isna() &
            self.dta['House_TotalChangeInMortgageDebt_WhenNotMoving_' + self.inflatedTimespan],
            'House_CapitalGains_' + self.inflatedTimespan] = None

        self.dta['House_Savings_' + self.inflatedTimespan] = (
            self.dta['CostOfMajorHomeRenovations_' + self.eyStr] * inflationForFlow).add(
            self.dta['House_NetOfDebtValueIncrease_WhenMoving_' + self.inflatedTimespan], fill_value=0).sub(
            self.dta['House_TotalChangeInMortgageDebt_WhenNotMoving_' + self.inflatedTimespan], fill_value=0)

        # Set NAs for Savings
        self.dta.loc[
            self.dta['CostOfMajorHomeRenovations_' + self.eyStr].isna() &
            self.dta['House_ValueIncrease_WhenMoving_' + self.inflatedTimespan].isna() &
            self.dta['House_TotalChangeInMortgageDebt_WhenMoving_' + self.inflatedTimespan].isna() &
            self.dta['House_TotalChangeInMortgageDebt_WhenNotMoving_' + self.inflatedTimespan].isna(),
            'House_Savings_' + self.inflatedTimespan] = None

        self.dta['House_TotalChangeInWealth_' + self.inflatedTimespan] = self.dta['House_Savings_' + self.inflatedTimespan].add(
            self.dta['House_CapitalGains_' + self.inflatedTimespan], fill_value=0)

        # And finally, calculate some rates of change
        self.calcAssetLevelGrowthRates("valueOfHouse_Net", "House", inflationForStock_EndOfPeriod)
        self.dta['House_OpenCloseTransfers_' + self.inflatedTimespan] = 0


        # 2.    Other real estate – Saving is the amount of money invested in real estate other than main home. Capital gains is the change in the net value of the asset minus saving in this asset.
        statusCountsPerVar += self.calcSavingsAndGains(valueField='valueOfOtherRealEstate_Net',
                                 flowFieldIn='OtherRealEstate_SinceLastQYr_AmountBought',
                                 flowFieldOut='OtherRealEstate_SinceLastQYr_AmountSold',
                                 newBaseName='OtherRealEstate',
                                 inflationForStock_StartOfPeriod=inflationForStock_StartOfPeriod,
                                 inflationForStock_EndOfPeriod=inflationForStock_EndOfPeriod,
                                 inflationForStock_BetweenStartAndEnd=totalInflationStartToEndYear,
                                 inflationForFlow=inflationForFlow)

        # 3.    Net equity in farm or business – Saving is the difference between the amount of money invested in farm or business and the amount realized from the sale of such assets. Capital gains is the change in the net value of the asset minus active saving in this asset.
        statusCountsPerVar += self.calcSavingsAndGains(valueField='valueOfBusiness_Net', flowFieldIn='Business_SinceLastQYr_AmountBought',
                                 flowFieldOut='Business_SinceLastQYr_AmountSold',
                                 newBaseName='Business',
                                 inflationForStock_StartOfPeriod=inflationForStock_StartOfPeriod,
                                 inflationForStock_EndOfPeriod=inflationForStock_EndOfPeriod,
                                 inflationForStock_BetweenStartAndEnd=totalInflationStartToEndYear,
                                 inflationForFlow=inflationForFlow)

        # 4.    Stock – Saving is the net value of stock bought or sold. Capital gains is the change in the net value of the asset minus saving in this asset.
        statusCountsPerVar += self.calcSavingsAndGains(valueField='valueOfBrokerageStocks_Net',
                                 flowFieldIn='BrokerageStocks_SinceLastQYr_AmountBought',
                                 flowFieldOut='BrokerageStocks_SinceLastQYr_AmountSold',
                                 newBaseName='BrokerageStocks',
                                 inflationForStock_StartOfPeriod=inflationForStock_StartOfPeriod,
                                 inflationForStock_EndOfPeriod=inflationForStock_EndOfPeriod,
                                 inflationForStock_BetweenStartAndEnd=totalInflationStartToEndYear,
                                 inflationForFlow=inflationForFlow,
                                 defaultNominalCapGainsRate=self.getNominalInvestmentReturn_ZeroCoded("Stock"))

        # 5.    Checking and savings – A 0 percent annual real rate of return is assumed, so saving equals the change in the net value of the asset.
        statusCountsPerVar += self.calcSavingsAndGains_FixedROR(valueField='valueOfCheckingAndSavings_Net',
                                          newBaseName='CheckingAndSavings', nominalAnnualRoR_ZeroCoded=(averageAnnualInflationDuringPeriod-1),
                                          inflationForStock_StartOfPeriod=inflationForStock_StartOfPeriod,
                                          inflationForStock_EndOfPeriod=inflationForStock_EndOfPeriod)

        # 6.    Net value of vehicles – Change in the net value is attributed to saving.
        statusCountsPerVar += self.calcSavingsAndGains_FixedROR(valueField='valueOfVehicle_Net',
                                          newBaseName='Vehicle', nominalAnnualRoR_ZeroCoded=self.CLASS_assumed_annual_nominal_vehicle_appreciation,
                                          inflationForStock_StartOfPeriod=inflationForStock_StartOfPeriod,
                                          inflationForStock_EndOfPeriod=inflationForStock_EndOfPeriod)

        # 7.    Other savings – Capital gains are calculated by assuming a 1 percent annual real rate of return. Saving is the change in the net value of the asset minus the capital gains for this asset.
        otherAssets_AnnualRateOfReturn = 0.01 + (averageAnnualInflationDuringPeriod-1)
        statusCountsPerVar += self.calcSavingsAndGains_FixedROR(valueField='valueOfOtherAssets_Net',
                                          newBaseName='OtherAssets', nominalAnnualRoR_ZeroCoded=otherAssets_AnnualRateOfReturn,
                                          inflationForStock_StartOfPeriod=inflationForStock_StartOfPeriod,
                                          inflationForStock_EndOfPeriod=inflationForStock_EndOfPeriod)

        # 8.    Other debts - Capital gains are calculated by assuming an annual real rate of return equal to the inflation rate (CPI-U). Saving is the change in the net value of the asset minus the capital gains for this asset.
        otherDebts_AnnualNominalRateOfReturn =  (averageAnnualInflationDuringPeriod-1)
        self.dta['valueOfAllOtherDebts_Net_TEMP_' + self.syStr] = -self.dta['valueOfAllOtherDebts_Net_' + self.syStr]
        self.dta['valueOfAllOtherDebts_Net_TEMP_' + self.eyStr] = -self.dta['valueOfAllOtherDebts_Net_' + self.eyStr]

        otherDebts_AnnualRateOfReturn = 0.01 + (averageAnnualInflationDuringPeriod-1)
        statusCountsPerVar += self.calcSavingsAndGains_FixedROR(valueField='valueOfAllOtherDebts_Net_TEMP',
                                          newBaseName='AllOtherDebts', nominalAnnualRoR_ZeroCoded=otherDebts_AnnualRateOfReturn,
                                          inflationForStock_StartOfPeriod=inflationForStock_StartOfPeriod,
                                          inflationForStock_EndOfPeriod=inflationForStock_EndOfPeriod)

        # 9. Add Private IRAs/Annuities here as a distinct Component
        if self.startYear >= 1999:  # the year in which we started getting Value of Private Retirement Plans
            statusCountsPerVar += self.calcSavingsAndGains(valueField='valueOfPrivateRetirePlan_Gross',
                                     flowFieldIn='PrivateRetirePlan_SinceLastQYr_AmountMovedIn',
                                     flowFieldOut='PrivateRetirePlan_SinceLastQYr_AmountMovedOut',
                                     newBaseName='PrivateRetirePlan',
                                     inflationForStock_StartOfPeriod=inflationForStock_StartOfPeriod,
                                     inflationForStock_EndOfPeriod=inflationForStock_EndOfPeriod,
                                     inflationForStock_BetweenStartAndEnd=totalInflationStartToEndYear,
                                     inflationForFlow=inflationForFlow,
                                     defaultNominalCapGainsRate=self.getNominalInvestmentReturn_ZeroCoded("Blended"))
        elif self.endYear >= 1989:
            # If we have either IN or OUT we can calc savings
            self.dta['PrivateRetirePlan_Savings_' + self.inflatedTimespan] = (
                self.dta['PrivateRetirePlan_SinceLastQYr_AmountMovedIn_' + self.eyStr].fillna(0) * inflationForFlow).sub(
                self.dta['PrivateRetirePlan_SinceLastQYr_AmountMovedOut_' + self.eyStr].fillna(0) * inflationForFlow)
            # But if we have NEITHER, don't record it as zero - record it as NA
            self.dta.loc[self.dta['PrivateRetirePlan_SinceLastQYr_AmountMovedIn_' + self.eyStr].isna() &
                self.dta['PrivateRetirePlan_SinceLastQYr_AmountMovedOut_' + self.eyStr].isna(),
                'PrivateRetirePlan_Savings_' + self.inflatedTimespan] = None
            self.dta['PrivateRetirePlan_CapitalGains_' + self.inflatedTimespan] = None
            self.dta['PrivateRetirePlan_TotalChangeInWealth_' + self.inflatedTimespan] = None  # self.dta['PrivateRetirePlan_Savings_' + self.inflatedTimespan]

            self.dta['PrivateRetirePlan_AN_CapitalGainsRate_' + self.inflatedTimespan] = None
            self.dta['PrivateRetirePlan_AN_SavingsRate_' + self.inflatedTimespan] = None
            self.dta['PrivateRetirePlan_AN_TotalGrowthRate_' + self.inflatedTimespan] = None
            self.dta['PrivateRetirePlan_OpenCloseTransfers_' + self.inflatedTimespan] = 0
        else:
            self.dta['PrivateRetirePlan_OpenCloseTransfers_' + self.inflatedTimespan] = 0

        # 10. Add Employer Retirement Plan Here, also as a distinct Component
        if self.startYear >= 1999:  # the year in which we started getting Value of Private Retirement Plans
            # We don't have retirement contributions for all years.
            # But we can take the average of the start and end * duration to get the total savings for the period.  (WHich for a 2-year period simply = start+end.)
            # NOTE -- important assumption here. We're assuming that no answer in one of the years means 0.

            # Start with average over time period
            self.dta['retirementContribHH_TotalForPeriod_' + self.eyStr] = (self.dta['retirementContribHH_' + self.eyStr].fillna(0)). \
                add(self.dta['retirementContribHH_' + self.syStr].fillna(0) * totalInflationStartToEndYear) * self.duration / 2
            # Set to none if there aren't actually any contributions
            self.dta.loc[self.dta['retirementContribHH_' + self.syStr].isna() &
                    self.dta['retirementContribHH_' + self.eyStr].isna(),
                     'retirementContribHH_TotalForPeriod_' + self.eyStr] = None
            # Create a dummy var for this purpose
            self.dta['retirement_Withdrawal_' + self.eyStr] = None
            # TODO -- see if there is a withdrawl field, for loans etc?

            statusCountsPerVar += self.calcSavingsAndGains(valueField='valueOfEmployerRetirePlan_Gross',
                                     flowFieldIn='retirementContribHH_TotalForPeriod', flowFieldOut='retirement_Withdrawal',
                                     newBaseName='EmployerRetirePlan',
                                     inflationForStock_StartOfPeriod=inflationForStock_StartOfPeriod,
                                     inflationForStock_EndOfPeriod=inflationForStock_EndOfPeriod,
                                     inflationForStock_BetweenStartAndEnd=totalInflationStartToEndYear,
                                     inflationForFlow=inflationForStock_EndOfPeriod, # Special case since we've already adjusted above
                                     defaultNominalCapGainsRate=self.getNominalInvestmentReturn_ZeroCoded("Blended")
                                    )

        else:
            self.dta['EmployerRetirePlan_TotalChangeInWealth_' + self.inflatedTimespan] = None
            self.dta['EmployerRetirePlan_Savings_' + self.inflatedTimespan] = None
            self.dta['EmployerRetirePlan_OpenCloseTransfers_' + self.inflatedTimespan] = None
            self.dta['EmployerRetirePlan_CapitalGains_' + self.inflatedTimespan] = None
            self.dta['EmployerRetirePlan_AN_CapitalGainsRate_' + self.inflatedTimespan] = None
            self.dta['EmployerRetirePlan_AN_SavingsRate_' + self.inflatedTimespan] = None
            self.dta['EmployerRetirePlan_AN_TotalGrowthRate_' + self.inflatedTimespan] = None

        # Not used in Savings Calc Directly, but useful for comparison to Net Wealth Calc
        self.dta['MortgagePrincipal_TotalChangeInWealth_' + self.inflatedTimespan] = (
                    self.dta['valueOfHouse_Debt_' + self.eyStr].fillna(0) * inflationForStock_EndOfPeriod).sub(
            self.dta['valueOfHouse_Debt_' + self.syStr].fillna(0) * inflationForStock_StartOfPeriod)
        self.dta['MortgagePrincipal_Savings_' + self.inflatedTimespan] = self.dta['MortgagePrincipal_TotalChangeInWealth_' + self.inflatedTimespan]
        self.dta['MortgagePrincipal_CapitalGains_' + self.inflatedTimespan] = 0

        return statusCountsPerVar

    def calcSavingsAndGains(self, valueField, flowFieldIn, flowFieldOut, newBaseName, inflationForStock_StartOfPeriod,
                            inflationForStock_EndOfPeriod,
                            inflationForStock_BetweenStartAndEnd,
                            inflationForFlow,
                            defaultNominalCapGainsRate = None):
        '''
        A helper function to calculate Asset-class level Savings & Capital Gains when the flow is knowns
        :param valueField:
        :type valueField:
        :param flowFieldIn:
        :type flowFieldIn:
        :param flowFieldOut:
        :type flowFieldOut:
        :param newBaseName:
        :type newBaseName:
        :param inflationForStock_StartOfPeriod:
        :type inflationForStock_StartOfPeriod:
        :param inflationForStock_EndOfPeriod:
        :type inflationForStock_EndOfPeriod:
        :param inflationForFlow:
        :type inflationForFlow:
        :return:
        :rtype:
        '''

        # Raw Material for figuring out where to place people
        # For Balances we need answers for BOTH start and finish

        maskForHasZeroBalances = ((self.dta[valueField + '_' + self.syStr].isna()) & (self.dta[valueField + '_' + self.eyStr].isna())) | \
                                 ((self.dta["has" + newBaseName + "_" + self.syStr] == False) & (self.dta["has" + newBaseName + "_" + self.eyStr] == False))
        maskForHasBothBalances = (~maskForHasZeroBalances) & (~self.dta[valueField + '_' + self.syStr].isna()) & (~self.dta[valueField + '_' + self.eyStr].isna())
        maskForHasOneBalance = ((~maskForHasZeroBalances) & ((self.dta[valueField + '_' + self.eyStr].isna()) | (self.dta[valueField + '_' + self.syStr].isna())))

        maskForBalancesAreSame = (self.dta[valueField + '_' + self.syStr].eq(self.dta[valueField + '_' + self.eyStr]))

        # Flow Flow, we can reasonably assume that if someone put in a value for IN and not OUT, that's because there was no OUT
        # And vice versa.  So, missing flow = when BOTH are  missing
        maskForBadFlow = ((self.dta[flowFieldIn + '_' + self.eyStr].isna()) & (self.dta[flowFieldOut + '_' + self.eyStr].isna()))
        maskForGoodFlow = ~maskForBadFlow

        # We place people into one of nine categories based on the status of their data
        # Category1
        maskForKnownNonSavers = ( \
            # Stock P1
            ((self.dta[valueField + '_' + self.syStr].eq(0))) &
            # Stock P2
            ((self.dta[valueField + '_' + self.eyStr].eq(0))) &
            # Flow In
            ((self.dta[flowFieldIn + '_' + self.eyStr].isna()) | (self.dta[flowFieldIn + '_' + self.eyStr].eq(0))) &
            # Flow Out
            ((self.dta[flowFieldOut + '_' + self.eyStr].isna()) | (self.dta[flowFieldOut + '_' + self.eyStr].eq(0)))
            )

        # Category2
        maskForNewAccount =(~maskForKnownNonSavers) & (
                # Perhaps some accounts are labeled as not existing, but there is a balance...
                (self.dta["has" + newBaseName + "_" + self.syStr] == False) & (self.dta[valueField + '_' + self.syStr].eq(0)) & \
                 (self.dta["has" + newBaseName + "_" + self.eyStr] == True) & (self.dta[valueField + '_' + self.eyStr].ne(0))
                )

        # Category3
        maskForClosedAccount =(~maskForKnownNonSavers) & (
                # Perhaps some accounts are labeled as not existing, but there is a balance...
                (self.dta["has" + newBaseName + "_" + self.syStr] == True) & (self.dta[valueField + '_' + self.syStr].ne(0)) & \
                 (self.dta["has" + newBaseName + "_" + self.eyStr] == False) & (self.dta[valueField + '_' + self.eyStr].eq(0))
                )

        allCapturedThusFar = (maskForNewAccount | maskForClosedAccount | maskForKnownNonSavers)

        # Category4
        maskForAllGood = ((maskForHasBothBalances) & (maskForGoodFlow) & (~allCapturedThusFar))

        # Category5
        maskForAllBad = ((maskForHasZeroBalances) & (maskForBadFlow) & (~allCapturedThusFar))

        # Category6-9
        maskForOneBalanceNoFlow = ((maskForHasOneBalance) & (maskForBadFlow) & (~allCapturedThusFar))
        maskForTwoBalancesNoFlow = ((maskForHasBothBalances) & (maskForBadFlow) & (~allCapturedThusFar))
        maskForFlowNoBalances = ((maskForHasZeroBalances) & (maskForGoodFlow) & (~allCapturedThusFar))
        maskForFlowOneBalance = ((maskForHasOneBalance) & (maskForGoodFlow) & (~allCapturedThusFar))

        # Sanity Checks. This is complex logic. Our 7 categories should be mutually exclusive and comprehensive
        maskMissing = ((~maskForNewAccount) & (~maskForClosedAccount) &
                        (~maskForAllGood) & (~maskForKnownNonSavers) & (~maskForAllBad) &
                       (~maskForOneBalanceNoFlow)  & (~maskForTwoBalancesNoFlow) &
                       (~maskForFlowNoBalances) & (~maskForFlowOneBalance))
        if sum(maskMissing) > 0:
            raise Exception("Problem in savings logic - people not covered")

        totalMasked = (sum(maskForAllGood) + sum(maskForKnownNonSavers) + sum(maskForNewAccount) + sum(maskForClosedAccount) +
                       sum(maskForAllBad) + sum(maskForOneBalanceNoFlow) + sum(maskForTwoBalancesNoFlow) +
                       sum(maskForFlowNoBalances) + sum(maskForFlowOneBalance))
        if totalMasked != len(self.dta):
            raise Exception("Problem in savings logic - people covered more than once")


        if newBaseName == "EmployerRetirePlan":
            print("debug here")

        # Handle the good ones
        countsPerGroup={"Period": self.inflatedTimespan, "Field": newBaseName,
                        "Verified Non-Saver (Doesn't have account)": sum(maskForKnownNonSavers),
                        "New Account": sum(maskForNewAccount),
                        "Closed Account": sum(maskForClosedAccount),
                        "Both Balances + Flow": sum(maskForAllGood),
                        "No Flow, Zero Balances": sum(maskForAllBad),
                        "No Flow, One Balance": sum(maskForOneBalanceNoFlow),
                        "No Flow, Two Balances": sum(maskForTwoBalancesNoFlow),
                        "Flow, Zero Balances": sum(maskForFlowNoBalances),
                        "Flow, One Balance": sum(maskForFlowOneBalance),
                        }
        
        # Setup a new var for everyone that handles new accounts/closed accounts.
        self.dta[newBaseName + '_OpenCloseTransfers_' + self.inflatedTimespan] = None

        # Category 1: Handle KNOWN and verified Non-Savers -- these are often unbanked
        print(valueField + '{Verified Non-Saver}:' + str(len(self.dta.loc[maskForKnownNonSavers])) + ". All set to 0")
        self.dta.loc[maskForKnownNonSavers, newBaseName + '_Status_' + self.inflatedTimespan] = 'Verified Non-Saver'
        self.dta.loc[maskForKnownNonSavers, newBaseName + '_TotalChangeInWealth_' + self.inflatedTimespan] = 0
        self.dta.loc[maskForKnownNonSavers, newBaseName + '_CapitalGains_' + self.inflatedTimespan] = 0
        self.dta.loc[maskForKnownNonSavers, newBaseName + '_Savings_' + self.inflatedTimespan] = 0

        # Category 2: New Account
        # So, with new accounts, there's a challenge -- if it is big dollar figure, the person probably transfered from another account.
        # For retirement for example, that's a rollover, and won't be captured in contribution rates
        # But, it will be shown as DISSAVING from somewhere else (at the same time, or different time)
        # To capture that, we should count all of the new balance as saving -- even if some of it is likely cap gains
        # This will mess up Asset-Level savings rates (so we exclude them below in the per-asset numbers), but  will wash out in Household-level rates
        print(valueField + '{New Account}:' + str(len(self.dta.loc[maskForNewAccount])) + ". Everything is saving")
        self.dta.loc[maskForNewAccount, newBaseName + '_Status_' + self.inflatedTimespan] = 'New Account'
        self.dta.loc[maskForNewAccount, newBaseName + '_TotalChangeInWealth_' + self.inflatedTimespan] = self.dta.loc[maskForNewAccount, valueField + '_' + self.eyStr]* inflationForStock_EndOfPeriod
        self.dta.loc[maskForNewAccount, newBaseName + '_CapitalGains_' + self.inflatedTimespan] = 0
        self.dta.loc[maskForNewAccount, newBaseName + '_Savings_' + self.inflatedTimespan] = 0
        self.dta.loc[maskForNewAccount, newBaseName + '_OpenCloseTransfers_' + self.inflatedTimespan] = self.dta.loc[maskForNewAccount, valueField + '_' + self.eyStr]* inflationForStock_EndOfPeriod

        # Category 3: Closed Account
        # With closed accounts, there's a similar challenge -- if it is big dollar figure, the person probably transfered from another account.
        # For retirement for example, that's a rollover, and won't be captured in contribution rates
        # But, it will be shown as SAVING from somewhere else (at the same time, or different time)
        # To capture that, we should count all of the old balance DISSAVING -- even if some of it is likely cap gains
        # This will mess up Asset-Level savings rates, but  will wash out in Household-level rates
        # Note that we AREN'T including any contributions during the period (net flow).
        # If, after money is taken out of this account, and moved to another, that will show up as saving there (and be an increased above the dissaving here).
        print(valueField + '{Closed Account}:' + str(len(self.dta.loc[maskForClosedAccount])) + ". Everything is dissaving")
        self.dta.loc[maskForClosedAccount, newBaseName + '_Status_' + self.inflatedTimespan] = 'Closed Account'
        self.dta.loc[maskForClosedAccount, newBaseName + '_TotalChangeInWealth_' + self.inflatedTimespan] = -self.dta.loc[maskForClosedAccount, valueField + '_' + self.syStr] * inflationForStock_StartOfPeriod
        self.dta.loc[maskForClosedAccount, newBaseName + '_CapitalGains_' + self.inflatedTimespan] = 0
        self.dta.loc[maskForClosedAccount, newBaseName + '_Savings_' + self.inflatedTimespan] = 0
        self.dta.loc[maskForClosedAccount, newBaseName + '_OpenCloseTransfers_' + self.inflatedTimespan] = -self.dta.loc[maskForClosedAccount, valueField + '_' + self.syStr] * inflationForStock_StartOfPeriod

        # Category 4: All Good
        print(valueField + '{Both Balances + Flow}:' + str(len(self.dta.loc[maskForAllGood])) + ". All calculated")
        self.dta.loc[maskForAllGood, newBaseName + '_Status_' + self.inflatedTimespan] = 'Both Balances + Flow'
        self.dta.loc[maskForAllGood, newBaseName + '_TotalChangeInWealth_' + self.inflatedTimespan] = (
            self.dta.loc[maskForAllGood, valueField + '_' + self.eyStr].fillna(0) * inflationForStock_EndOfPeriod).sub(
            self.dta.loc[maskForAllGood, valueField + '_' + self.syStr].fillna(0) * inflationForStock_StartOfPeriod)
        self.dta.loc[maskForAllGood, newBaseName + '_Savings_' + self.inflatedTimespan] = self.dta.loc[
            maskForAllGood, flowFieldIn + '_' + self.eyStr].fillna(0).sub(
            self.dta.loc[maskForAllGood, flowFieldOut + '_' + self.eyStr].fillna(0)) * inflationForFlow
        self.dta.loc[maskForAllGood, newBaseName + '_CapitalGains_' + self.inflatedTimespan] = self.dta.loc[
            maskForAllGood, newBaseName + '_TotalChangeInWealth_' + self.inflatedTimespan].fillna(0).sub(
            self.dta.loc[maskForAllGood, newBaseName + '_Savings_' + self.inflatedTimespan].fillna(0))

        # Category 5: Handle the KNOWN bad data -- nothing we can do with these
        if len(self.dta.loc[maskForAllBad]) > 0:
            print(valueField + '{No Flow, Zero Balances}:' + str(len(self.dta.loc[maskForAllBad])) + ". All set to None")
            self.dta.loc[maskForAllBad, newBaseName + '_Status_' + self.inflatedTimespan] = 'No Flow, Zero Balances'
            self.dta.loc[maskForAllBad, newBaseName + '_TotalChangeInWealth_' + self.inflatedTimespan] = None
            self.dta.loc[maskForAllBad, newBaseName + '_CapitalGains_' + self.inflatedTimespan] = None
            self.dta.loc[maskForAllBad, newBaseName + '_Savings_' + self.inflatedTimespan] = None

        # Category 6 Handle the ones with only one Balance (no flow)
        if len(self.dta.loc[maskForOneBalanceNoFlow]) > 0:
            print(valueField + '{No Flow, One Balance}:' + str(len(self.dta.loc[maskForOneBalanceNoFlow])) + ". All set to None; Filled in Missing Balance")
            self.dta.loc[maskForOneBalanceNoFlow, newBaseName + '_Status_' + self.inflatedTimespan] = 'No Flow, One Balance'
            self.dta.loc[maskForOneBalanceNoFlow, newBaseName + '_TotalChangeInWealth_' + self.inflatedTimespan] = None
            self.dta.loc[maskForOneBalanceNoFlow, newBaseName + '_Savings_' + self.inflatedTimespan] = None
            self.dta.loc[maskForOneBalanceNoFlow, newBaseName + '_CapitalGains_' + self.inflatedTimespan] = None

            # The missing balance in this case will show a difference in net wealth (aggregated by accounts).
            # That is in fact an EXISTING problem with the PSID data's net wealth calcs.
            # To fix that, the best assumption here is that the balance hasn't changed. No savings, no cap gains.
            # That change is in REAL terms. Total Change in Wealth in REAL terms needs to line up with the change in values below so, we need to apply inflation here.
            maskForHasStart = maskForOneBalanceNoFlow & (~self.dta[valueField + '_' + self.syStr].isna())
            maskForHasEnd = maskForOneBalanceNoFlow & (~self.dta[valueField + '_' + self.eyStr].isna())
            self.dta.loc[maskForHasStart, valueField + '_' + self.eyStr] = self.dta.loc[maskForHasStart, valueField + '_' + self.syStr]*inflationForStock_BetweenStartAndEnd
            self.dta.loc[maskForHasEnd, valueField + '_' + self.syStr] = self.dta.loc[maskForHasEnd, valueField + '_' + self.eyStr]/inflationForStock_BetweenStartAndEnd

        # Category 7 Handle the ones with both Balances (no flow)
        if len(self.dta.loc[maskForTwoBalancesNoFlow]) > 0:

            # Total Balances are good -- use them
            self.dta.loc[maskForTwoBalancesNoFlow, newBaseName + '_TotalChangeInWealth_' + self.inflatedTimespan] = (
                self.dta.loc[maskForTwoBalancesNoFlow, valueField + '_' + self.eyStr] * inflationForStock_EndOfPeriod).fillna(0).sub(
                self.dta.loc[maskForTwoBalancesNoFlow, valueField + '_' + self.syStr].fillna(0) * inflationForStock_StartOfPeriod)

            # Calculate capital gains AS IF Flow were zero.  if it's "reasonable", keep it.
            # This can give an inflated capital gains value. But the alternative is an implied rate of 0
            # It actually doesn't affect active savings calcs: since the alternative is implied 0 anyway.
            remainingMask = maskForTwoBalancesNoFlow
            self.dta.loc[remainingMask, newBaseName + '_CapitalGainsRate_Implied_' + self.inflatedTimespan] = \
                calcNominalRoRfromChange_Series(dta = self.dta.loc[remainingMask], startValueField_Uninflated = valueField + '_' + self.syStr,
                                         changeField_Inflated = newBaseName + '_TotalChangeInWealth_' + self.inflatedTimespan, duration = self.duration,
                                         inflationFactorForEnd = inflationForStock_EndOfPeriod)
            # Approximation for debugging purpooses:
            self.dta.loc[remainingMask, newBaseName + '_CapitalGainsRate_ApproxImplied_' + self.inflatedTimespan] = (self.dta.loc[remainingMask, newBaseName + '_TotalChangeInWealth_' + self.inflatedTimespan]/self.duration).div(self.dta.loc[remainingMask, valueField + '_' + self.syStr]*inflationForStock_EndOfPeriod)

            okCapGains = ~maskForBalancesAreSame & maskForTwoBalancesNoFlow & \
                ((self.dta.loc[remainingMask, newBaseName + '_CapitalGainsRate_Implied_' + self.inflatedTimespan].abs()) < self.CLASS_acceptable_implied_annual_nominal_capgains)

            print(valueField + '{No Flow, Two Balances [IMPLIED CAP GAINS]}:' + str(len(self.dta.loc[okCapGains & maskForTwoBalancesNoFlow])) + ". Cap Gains Implied and Savings are Zero")
            print(valueField + '{No Flow, Two Balances [IMPLIED CAP GAINS -- subset with SAME BALANCE]}:' + str(len(self.dta.loc[okCapGains & maskForBalancesAreSame & maskForTwoBalancesNoFlow])) + ". Cap Gains and Savings are Zero")
            self.dta.loc[okCapGains & maskForTwoBalancesNoFlow, newBaseName + '_Status_' + self.inflatedTimespan] = 'No Flow, Two Balances: ImpliedCapGains, NoSavings'
            self.dta.loc[okCapGains & maskForTwoBalancesNoFlow, newBaseName + '_CapitalGains_' + self.inflatedTimespan] = self.dta.loc[okCapGains & maskForTwoBalancesNoFlow, newBaseName + '_TotalChangeInWealth_' + self.inflatedTimespan]
            self.dta.loc[okCapGains & maskForTwoBalancesNoFlow, newBaseName + '_Savings_' + self.inflatedTimespan] = 0

            print(valueField + '{No Flow, Two Balances [Cant Calc Capgains & Savings]}:' + str(len(self.dta.loc[~okCapGains & ~maskForBalancesAreSame & maskForTwoBalancesNoFlow])) + ". Cap Gains and Savings are Zero")
            self.dta.loc[~okCapGains & maskForTwoBalancesNoFlow, newBaseName + '_Status_' + self.inflatedTimespan] = 'No Flow, Two Balances: NoSavingsNoCapGains'
            self.dta.loc[~okCapGains & maskForTwoBalancesNoFlow, newBaseName + '_CapitalGains_' + self.inflatedTimespan] = None
            self.dta.loc[~okCapGains & maskForTwoBalancesNoFlow, newBaseName + '_Savings_' + self.inflatedTimespan] = None

        # Category 8 Handle the ones with only Flow (zero balances)
        if len(self.dta.loc[maskForFlowNoBalances]) > 0:
            print(valueField + '{Flow, Zero Balances}:' + str(len(self.dta.loc[maskForFlowNoBalances])) + ". Cap Gains and Total are None")
            self.dta.loc[maskForFlowNoBalances, newBaseName + '_Status_' + self.inflatedTimespan] = 'Flow, Zero Balances'
            self.dta.loc[maskForFlowNoBalances, newBaseName + '_Savings_' + self.inflatedTimespan] = self.dta.loc[
                maskForFlowNoBalances, flowFieldIn + '_' + self.eyStr].fillna(0).sub(
                self.dta.loc[maskForFlowNoBalances, flowFieldOut + '_' + self.eyStr].fillna(0)) * inflationForFlow

            # For employer retirement plans especially, there are many accounts with FLow but no account balance.
            # Employer retirement plans are almost always invested, and we can model 'reasonable' returns from M* data on these plans.
            # If we don't their cap gains, we will significantly underestimate total HH cap gains - since this is the prime driver for many familes with accounts
            # Ideally, we'd keep track of the balance over time from when it started, and fill it in.
            # But, at this data isn't available here.  So, the best we can do is set to none.
            self.dta.loc[maskForFlowNoBalances, newBaseName + '_Status_' + self.inflatedTimespan] = 'Flow, No Balance'
            self.dta.loc[maskForFlowNoBalances, newBaseName + '_CapitalGains_' + self.inflatedTimespan] = None
            self.dta.loc[maskForFlowNoBalances, newBaseName + '_TotalChangeInWealth_' + self.inflatedTimespan] = None

        # Category 9 Handle the ones with Flow & One balance
        if len(self.dta.loc[maskForFlowOneBalance]) > 0:

            self.dta.loc[maskForFlowOneBalance, newBaseName + '_Savings_' + self.inflatedTimespan] = self.dta.loc[
                maskForFlowOneBalance, flowFieldIn + '_' + self.eyStr].fillna(0).sub(
                self.dta.loc[maskForFlowOneBalance, flowFieldOut + '_' + self.eyStr].fillna(0)) * inflationForFlow

            maskForHasStart = maskForFlowOneBalance & (~self.dta[valueField + '_' + self.syStr].isna())
            maskForHasEnd = maskForFlowOneBalance & (~self.dta[valueField + '_' + self.eyStr].isna())

            # For employer retirement plans especially, there are many accounts with FLow but no account balance.
            # Employer retirement plans are almost always invested, and we can model 'reasonable' returns from M* data on these plans.
            # If we don't their cap gains, we will significantly underestimate total HH cap gains - since this is the prime driver for many familes with accounts
            if defaultNominalCapGainsRate is not None:
                print(valueField + '{Flow, One Balance}:' + str(len(self.dta.loc[maskForFlowOneBalance])) + ". Using Default Cap Gains to get Total")
                self.dta.loc[maskForFlowOneBalance, newBaseName + '_Status_' + self.inflatedTimespan] = 'Flow, One Balance {FilledBalance from DefaultCapGains}'

                # Fill in missing balances -- useful here, AND for subsequent net worth calculations
                if sum(maskForHasStart) > 0:
                    self.dta.loc[maskForHasStart, valueField + '_' + self.eyStr] = (self.dta.loc[maskForHasStart, valueField + '_' + self.syStr] * ((1.0 + defaultNominalCapGainsRate)**self.duration)).add(self.dta.loc[maskForHasStart, newBaseName + '_Savings_' + self.inflatedTimespan]/inflationForStock_EndOfPeriod)
                if sum(maskForHasEnd) > 0:
                    self.dta.loc[maskForHasEnd, valueField + '_' + self.syStr] = self.dta.loc[maskForHasEnd, valueField + '_' + self.eyStr].sub(self.dta.loc[maskForHasEnd, newBaseName + '_Savings_' + self.inflatedTimespan]/inflationForStock_EndOfPeriod) * ((1.0 - defaultNominalCapGainsRate)**self.duration)

                self.dta.loc[maskForFlowOneBalance, newBaseName + '_TotalChangeInWealth_' + self.inflatedTimespan] = (
                    self.dta.loc[maskForFlowOneBalance, valueField + '_' + self.eyStr] * inflationForStock_EndOfPeriod).fillna(0).sub(
                    self.dta.loc[maskForFlowOneBalance, valueField + '_' + self.syStr].fillna(0) * inflationForStock_StartOfPeriod)

                self.dta.loc[maskForFlowOneBalance, newBaseName + '_CapitalGains_' + self.inflatedTimespan] = self.dta.loc[
                    maskForFlowOneBalance, newBaseName + '_TotalChangeInWealth_' + self.inflatedTimespan].fillna(0).sub(
                    self.dta.loc[maskForFlowOneBalance, newBaseName + '_Savings_' + self.inflatedTimespan].fillna(0))

                # For debugging purposes
                self.dta.loc[maskForFlowOneBalance, newBaseName + '_CapitalGains_DoubleCheck_' + self.inflatedTimespan] = self.dta.loc[maskForFlowOneBalance, valueField + '_' + self.syStr] * (((1 + defaultNominalCapGainsRate)**self.duration)-1) * inflationForStock_EndOfPeriod
            else:
                print(valueField + '{Flow, One Balance}:' + str(len(self.dta.loc[maskForFlowOneBalance])) + ". Cap Gains and Total are null")
                self.dta.loc[maskForFlowOneBalance, newBaseName + '_Status_' + self.inflatedTimespan] = 'Flow, One Balance {No DefaultCapGains}'
                # self.dta.loc[maskForFlowOneBalance, newBaseName + '_TotalChangeInWealth_' + self.inflatedTimespan] = None
                self.dta.loc[maskForFlowOneBalance, newBaseName + '_CapitalGains_' + self.inflatedTimespan] = None

                # The missing balance in this case will show a difference in net wealth (aggregated by accounts) -- sometimes a massive one, if this is a big account
                # That is in fact an EXISTING problem with the PSID data's net wealth calcs.
                # To fix that, the best assumption here is that there is no cap gains & that balance hasn't changed BEYOND SAVINGS
                self.dta.loc[maskForHasStart, valueField + '_' + self.eyStr] = self.dta.loc[maskForHasStart, valueField + '_' + self.syStr].add(self.dta.loc[maskForHasStart, newBaseName + '_Savings_' + self.inflatedTimespan].fillna(0)/inflationForStock_EndOfPeriod)
                self.dta.loc[maskForHasEnd, valueField + '_' + self.syStr] = self.dta.loc[maskForHasEnd, valueField + '_' + self.eyStr].sub(self.dta.loc[maskForHasEnd, newBaseName + '_Savings_' + self.inflatedTimespan].fillna(0)/inflationForStock_EndOfPeriod)

                # To make everything balance out, let's keep track of changes in the values of accounts that we don't have complete data for
                self.dta.loc[maskForFlowOneBalance, newBaseName + '_TotalChangeInWealth_' + self.inflatedTimespan] = (self.dta.loc[maskForFlowOneBalance, valueField + '_' + self.eyStr]*inflationForStock_EndOfPeriod).sub((self.dta.loc[maskForFlowOneBalance, valueField + '_' + self.syStr]*inflationForStock_StartOfPeriod))

        # And finally, calculate some rates of change
        self.calcAssetLevelGrowthRates(valueField, newBaseName, inflationForStock_EndOfPeriod)

        return [countsPerGroup]

    def calcSavingsAndGains_FixedROR(self, valueField, newBaseName, nominalAnnualRoR_ZeroCoded, inflationForStock_StartOfPeriod,
                                     inflationForStock_EndOfPeriod):
        '''
        A helper function to calculate Asset-class level Savings & Capital Gains when a fixed ROR is known, but not flow

        :param valueField:
        :type valueField:
        :param newBaseName:
        :type newBaseName:
        :param NominalRoR:
        :type NominalRoR:
        :param inflationForStock_StartOfPeriod:
        :type inflationForStock_StartOfPeriod:
        :param inflationForStock_EndOfPeriod:
        :type inflationForStock_EndOfPeriod:
        :return:
        :rtype:
        '''

        if nominalAnnualRoR_ZeroCoded is None:
            nominalAnnualRoR_ZeroCoded = 0

        maskForNoBalances = ((self.dta[valueField + '_' + self.eyStr].isna()) & (self.dta[valueField + '_' + self.syStr].isna())) & \
                                 ((self.dta["has" + newBaseName + "_" + self.syStr] == False) & (self.dta["has" + newBaseName + "_" + self.eyStr] == False))
        maskForBothBalances = (~maskForNoBalances) & (~self.dta[valueField + '_' + self.eyStr].isna()) & (~self.dta[valueField + '_' + self.syStr].isna())
        maskForOneBalance = ((~maskForNoBalances) & ((self.dta[valueField + '_' + self.eyStr].isna()) | (self.dta[valueField + '_' + self.syStr].isna())))

        # For this calculation, there are four possible groups: mutually exclusive and comprehensive
        maskForKnownNonSavers = ( \
            # Stock P1
            ((self.dta[valueField + '_' + self.syStr].eq(0))) &
            # Stock P2
            ((self.dta[valueField + '_' + self.eyStr].eq(0)))
            )
        
        # Category2
        maskForNewAccount =(~maskForKnownNonSavers) & (
                # Perhaps some accounts are labeled as not existing, but there is a balance...
                (self.dta["has" + newBaseName + "_" + self.syStr] == False) & (self.dta[valueField + '_' + self.syStr].eq(0)) & \
                 (self.dta["has" + newBaseName + "_" + self.eyStr] == True) & (self.dta[valueField + '_' + self.eyStr].ne(0))
                )

        # Category3
        maskForClosedAccount =(~maskForKnownNonSavers) & (
                # Perhaps some accounts are labeled as not existing, but there is a balance...
                (self.dta["has" + newBaseName + "_" + self.syStr] == True) & (self.dta[valueField + '_' + self.syStr].ne(0)) & \
                 (self.dta["has" + newBaseName + "_" + self.eyStr] == False) & (self.dta[valueField + '_' + self.eyStr].eq(0))
                )

        allCapturedThusFar = (maskForNewAccount | maskForClosedAccount | maskForKnownNonSavers)

        maskForAllGood = ((maskForBothBalances) & (~allCapturedThusFar))
        maskForHasOneBalance = ((maskForOneBalance) & (~allCapturedThusFar))
        maskForHasZeroBalances = ((maskForNoBalances) &  (~allCapturedThusFar))

        # Sanity Checks. This is complex logic. Our 4 categories should be mutually exclusive and comprehensive
        maskMissing = ((~maskForNewAccount) & (~maskForClosedAccount) & (~maskForAllGood) & (~maskForKnownNonSavers) & (~maskForHasOneBalance) & (~maskForHasZeroBalances))
        if sum(maskMissing) > 0:
            raise Exception("Problem in savings logic - people not covered")
        totalMasked = (sum(maskForNewAccount) + sum(maskForClosedAccount) + sum(maskForAllGood) + sum(maskForKnownNonSavers) + sum(maskForHasOneBalance) + sum(maskForHasZeroBalances))
        if totalMasked != len(self.dta):
            raise Exception("Problem in savings logic - people covered more than once")

        countsPerGroup={"Period": self.inflatedTimespan, "Field": newBaseName,
                "New Account": sum(maskForNewAccount),
                "Closed Account": sum(maskForClosedAccount),
                "Verified Non-Saver (Doesn't have account)": sum(maskForKnownNonSavers),
                "Both Balances + Flow": sum(maskForAllGood),
                "ROR one Balance": sum(maskForHasOneBalance),
                "ROR zero Balances": sum(maskForHasZeroBalances)
                }

        # Setup a var for everyone we don't use much
        self.dta[newBaseName + '_OpenCloseTransfers_' + self.inflatedTimespan] = None

        # Category 1: Handle KNOWN and verified Non-Savers -- these are often unbanked
        print(valueField + '{Verified Non-Saver}:' + str(len(self.dta.loc[maskForKnownNonSavers])) + ". All set to 0")
        self.dta.loc[maskForKnownNonSavers, newBaseName + '_Status_' + self.inflatedTimespan] = 'Verified Non-Saver'
        self.dta.loc[maskForKnownNonSavers, newBaseName + '_TotalChangeInWealth_' + self.inflatedTimespan] = 0
        self.dta.loc[maskForKnownNonSavers, newBaseName + '_CapitalGains_' + self.inflatedTimespan] = 0
        self.dta.loc[maskForKnownNonSavers, newBaseName + '_Savings_' + self.inflatedTimespan] = 0

        # Category 2: New Account
        # So, with new accounts, there's a challenge -- if it is big dollar figure, the person probably transfered from another account.
        # For retirement for example, that's a rollover, and won't be captured in contribution rates
        # But, it will be shown as DISSAVING from somewhere else (at the same time, or different time)
        # To capture that, we should count all of the new balance as saving -- even if some of it is likely cap gains
        # This will mess up Asset-Level savings rates, but  will wash out in Household-level rates
        print(valueField + '{New Account}:' + str(len(self.dta.loc[maskForNewAccount])) + ". Everything is saving")
        self.dta.loc[maskForNewAccount, newBaseName + '_Status_' + self.inflatedTimespan] = 'New Account'
        self.dta.loc[maskForNewAccount, newBaseName + '_TotalChangeInWealth_' + self.inflatedTimespan] = self.dta.loc[maskForNewAccount, valueField + '_' + self.eyStr]
        self.dta.loc[maskForNewAccount, newBaseName + '_CapitalGains_' + self.inflatedTimespan] = 0
        self.dta.loc[maskForNewAccount, newBaseName + '_Savings_' + self.inflatedTimespan] = 0
        self.dta.loc[maskForNewAccount, newBaseName + '_OpenCloseTransfers_' + self.inflatedTimespan] = self.dta.loc[maskForNewAccount, valueField + '_' + self.eyStr]

        # Category 3: Closed Account
        # With closed accounts, there's a similar challenge -- if it is big dollar figure, the person probably transfered from another account.
        # For retirement for example, that's a rollover, and won't be captured in contribution rates
        # But, it will be shown as SAVING from somewhere else (at the same time, or different time)
        # To capture that, we should count all of the old balance DISSAVING -- even if some of it is likely cap gains
        # This will mess up Asset-Level savings rates, but  will wash out in Household-level rates
        # Note that we AREN'T including any contributions during the period (net flow).
        # If, after money is taken out of this account, and moved to another, that will show up as saving there (and be an increased above the dissaving here).
        print(valueField + '{Closed Account}:' + str(len(self.dta.loc[maskForClosedAccount])) + ". Everything is dissaving")
        self.dta.loc[maskForClosedAccount, newBaseName + '_Status_' + self.inflatedTimespan] = 'Closed Account'
        self.dta.loc[maskForClosedAccount, newBaseName + '_TotalChangeInWealth_' + self.inflatedTimespan] = -self.dta.loc[maskForClosedAccount, valueField + '_' + self.syStr]
        self.dta.loc[maskForClosedAccount, newBaseName + '_CapitalGains_' + self.inflatedTimespan] = 0
        self.dta.loc[maskForClosedAccount, newBaseName + '_Savings_' + self.inflatedTimespan] = 0
        self.dta.loc[maskForClosedAccount, newBaseName + '_OpenCloseTransfers_' + self.inflatedTimespan] = -self.dta.loc[maskForClosedAccount, valueField + '_' + self.syStr]

        # Category 4: Handle the KNOWN bad data -- nothing we can do with these
        if len(self.dta.loc[maskForHasZeroBalances]) > 0:
            print(valueField + '{ROR zero Balances}:' + str(len(self.dta.loc[maskForHasZeroBalances])) + ". All set to None")
            self.dta.loc[maskForHasZeroBalances, newBaseName + '_Status_' + self.inflatedTimespan] = 'ROR zero Balances'
            self.dta.loc[maskForHasZeroBalances, newBaseName + '_TotalChangeInWealth_' + self.inflatedTimespan] = None
            self.dta.loc[maskForHasZeroBalances, newBaseName + '_CapitalGains_' + self.inflatedTimespan] = None
            self.dta.loc[maskForHasZeroBalances, newBaseName + '_Savings_' + self.inflatedTimespan] = None

        # Category 3: Handle partially missing data -- fill in where we can
        if len(self.dta.loc[maskForHasOneBalance]) > 0:
            print(valueField + '{ROR one Balance}:' + str(len(self.dta.loc[maskForHasOneBalance])) + ". Filled in CapGains and Balance")

            self.dta.loc[maskForHasOneBalance, newBaseName + '_Status_' + self.inflatedTimespan] = 'ROR one Balance'
            maskForHasStart = maskForHasOneBalance & (~self.dta[valueField + '_' + self.syStr].isna())
            maskForHasEnd = maskForHasOneBalance & (~self.dta[valueField + '_' + self.eyStr].isna())

            self.dta.loc[maskForHasOneBalance, newBaseName + '_TotalChangeInWealth_' + self.inflatedTimespan] = None
            self.dta.loc[maskForHasOneBalance, newBaseName + '_Savings_' + self.inflatedTimespan] = None

            # Fill in capital gains balances
            # Note thatwe are implicitly assuming that any savings occured at the END Of the period (and didn't accue Cap Gains)
            self.dta.loc[maskForHasStart, newBaseName + '_CapitalGains_' + self.inflatedTimespan] = self.dta.loc[maskForHasStart, valueField + '_' + self.syStr] * ((1 + nominalAnnualRoR_ZeroCoded)**self.duration - 1) * inflationForStock_EndOfPeriod
            self.dta.loc[maskForHasEnd, newBaseName + '_CapitalGains_' + self.inflatedTimespan] = self.dta.loc[maskForHasStart, valueField + '_' + self.eyStr] * ((1 - nominalAnnualRoR_ZeroCoded)**self.duration - 1) * inflationForStock_EndOfPeriod

            # The missing balance in this case will show a difference in net wealth (aggregated by accounts) -- sometimes a massive one, if this is a big account
            # That is in fact an EXISTING problem with the PSID data's net wealth calcs.
            # To fix that, the best assumption here is that there is no savings & that balance hasn't changed BEYOND CAP GAINS
            self.dta.loc[maskForHasStart, valueField + '_' + self.eyStr] = self.dta.loc[maskForHasStart, valueField + '_' + self.syStr] * ((1 + nominalAnnualRoR_ZeroCoded)**self.duration)
            self.dta.loc[maskForHasEnd, valueField + '_' + self.syStr] = self.dta.loc[maskForHasStart, valueField + '_' + self.eyStr] * ((1 - nominalAnnualRoR_ZeroCoded)**self.duration)

        # Category 1:
        # Note -- we are INTENTIONALLY not filling in NAs here - we want NAs to propagate - just in case (left over before the masking process)
        print(valueField + '{Both Balances + Flow}:' + str(len(self.dta.loc[maskForAllGood])) + ". All calculated")
        self.dta.loc[maskForAllGood, newBaseName + '_Status_' + self.inflatedTimespan] = 'Both Balances + Flow'
        self.dta.loc[maskForAllGood, newBaseName + '_TotalChangeInWealth_' + self.inflatedTimespan] = (
            self.dta.loc[maskForAllGood, valueField + '_' + self.eyStr] * inflationForStock_EndOfPeriod).sub(
            self.dta.loc[maskForAllGood, valueField + '_' + self.syStr] * inflationForStock_StartOfPeriod)

        self.dta.loc[maskForAllGood, newBaseName + '_CapitalGains_' + self.inflatedTimespan] = (
            self.dta.loc[maskForAllGood, valueField + '_' + self.syStr] * \
            (((1 + nominalAnnualRoR_ZeroCoded) ** self.duration) - 1)) * inflationForStock_EndOfPeriod

        self.dta.loc[maskForAllGood, newBaseName + '_Savings_' + self.inflatedTimespan] = self.dta.loc[maskForAllGood,
            newBaseName + '_TotalChangeInWealth_' + self.inflatedTimespan].sub(
            self.dta.loc[maskForAllGood, newBaseName + '_CapitalGains_' + self.inflatedTimespan])

        # And finally, calculate some rates of change
        self.calcAssetLevelGrowthRates(valueField, newBaseName, inflationForStock_EndOfPeriod)

        return [countsPerGroup]

    def calcAssetLevelGrowthRates(self, valueField, newBaseName, inflationForStock_EndOfPeriod):

        maskForNewAccount =(
                # Perhaps some accounts are labeled as not existing, but there is a balance...
                (self.dta["has" + newBaseName + "_"  + self.syStr] == False) & (self.dta[valueField + '_' + self.syStr].eq(0)) & \
                 (self.dta["has" + newBaseName + "_" + self.eyStr] == True) & (self.dta[valueField + '_' + self.eyStr].ne(0))
                )
        maskForClosedAccount =(
                # Perhaps some accounts are labeled as not existing, but there is a balance...
                (self.dta["has" + newBaseName + "_" + self.syStr] == True) & (self.dta[valueField + '_' + self.syStr].ne(0)) & \
                 (self.dta["has" + newBaseName + "_"  + self.eyStr] == False) & (self.dta[valueField + '_' + self.eyStr].eq(0))
                )
        accountChange = (maskForClosedAccount | maskForNewAccount)

        # generally these will be noisy, and we'll want to analyze the Average as Sums, but useful for medians
        enoughDataNowForCapGains = (~accountChange) & (~self.dta[valueField + '_' + self.syStr].isna() & (~self.dta[newBaseName + '_CapitalGains_' + self.inflatedTimespan].isna()))
        self.dta.loc[enoughDataNowForCapGains, newBaseName + '_AN_CapitalGainsRate_' + self.inflatedTimespan] = \
            calcNominalRoRfromChange_Series(dta = self.dta.loc[enoughDataNowForCapGains],
                                            startValueField_Uninflated = valueField + '_' + self.syStr,
                                            changeField_Inflated = newBaseName + '_CapitalGains_' + self.inflatedTimespan,
                                            duration = self.duration,
                                            inflationFactorForEnd = inflationForStock_EndOfPeriod)

        enoughDataNowForSavingsRate = (~accountChange) & (~self.dta[valueField + '_' + self.syStr].isna() & (~self.dta[newBaseName + '_CapitalGains_' + self.inflatedTimespan].isna()))
        self.dta.loc[enoughDataNowForSavingsRate, newBaseName + '_AN_SavingsRate_' + self.inflatedTimespan] = \
            calcNominalRoRfromChange_Series(dta = self.dta.loc[enoughDataNowForSavingsRate],
                                            startValueField_Uninflated = valueField + '_' + self.syStr,
                                            changeField_Inflated = newBaseName + '_Savings_' + self.inflatedTimespan,
                                            duration = self.duration,
                                            inflationFactorForEnd = inflationForStock_EndOfPeriod)

        enoughDataNowForWealthRate = (~accountChange) & (~self.dta[valueField + '_' + self.syStr].isna() & (~self.dta[newBaseName + '_TotalChangeInWealth_' + self.inflatedTimespan].isna()))
        self.dta.loc[enoughDataNowForWealthRate, newBaseName + '_AN_TotalGrowthRate_' + self.inflatedTimespan] = \
            calcNominalRoRfromChange_Series(dta = self.dta.loc[enoughDataNowForWealthRate],
                                            startValueField_Uninflated = valueField + '_' + self.syStr,
                                            changeField_Inflated = newBaseName + '_TotalChangeInWealth_' + self.inflatedTimespan,
                                            duration = self.duration,
                                            inflationFactorForEnd = inflationForStock_EndOfPeriod)

    def calcTotalSavingsRate(self):
        '''
        Based on the asset-class level savings & capital gains information,
        calculates the Total Gross savings (sum of asset level) & Active Savings (gross - moves - gifts) values for each family
        :return:
        :rtype:
        '''

        '''
        Gittleman et al take a different approach than Dynan et al.
        Here the focus is on calculating capital gains versus assuming all is savings
        '''
        totalInflationEndToInflatedYear = self.inflator.getInflationFactorBetweenTwoYears(self.endYear, self.toYear)
        totalInflationStartToInflatedYear = self.inflator.getInflationFactorBetweenTwoYears(self.startYear, self.toYear)

        # Unlike Dynan, Does not appear to use a average here.
        inflationForFlow = totalInflationEndToInflatedYear
        # "For the change-in-stock variables (house value, mortgage, and wealth variables), we deflate the nominal level in each year by the price index for that year, and then take the change in this real value."
        # inflationForStock_StartOfPeriod = totalInflationStartToInflatedYear
        # inflationForStock_EndOfPeriod = totalInflationEndToInflatedYear

        # Each of the following entries should have a variable _TotalChangeInWealth, _CapitalGains and _Savings
        if self.excludeRetirementSavings:
            componentVars = ['House', 'OtherRealEstate', 'Business', 'BrokerageStocks', 'CheckingAndSavings', 'Vehicle',
                             'OtherAssets', 'AllOtherDebts']
        else:
            componentVars = ['House', 'OtherRealEstate', 'Business', 'BrokerageStocks', 'CheckingAndSavings', 'Vehicle',
                             'OtherAssets', 'AllOtherDebts', 'PrivateRetirePlan', 'EmployerRetirePlan']

        totalChangeVars = [s + "_TotalChangeInWealth_" + self.inflatedTimespan for s in componentVars]
        capitalGainsVars = [s + "_CapitalGains_" + self.inflatedTimespan for s in componentVars]
        grossSavingsVars = [s + "_Savings_" + self.inflatedTimespan for s in componentVars]
        transferVars = [s + "_OpenCloseTransfers_" + self.inflatedTimespan for s in componentVars]

        varsUsed = [] + totalChangeVars + capitalGainsVars + grossSavingsVars + transferVars

        # WARNING -- this is a very consequential decision.
        # If people are missing data on one or more of the savings vars (especially), to we consider
            # the entire savings rate calc for that person invalid, or so we consider that area of saving 0?
            # Currently, our choice is to include them, and assume 0 savings in that particular domain.
            # This is likely to create more variation WITHIN households year to year (as pattern of missingness shifts),
            # But should mean a more realistic population level savings rate overall
            # To see how many people would be excluded if NAs propagated, see the VarStatusCounts debugging file -- anyone with 'completelybaddata' in ANY of the Asset classes
        # Most of our variables have lots of NAs.  They should all be filled to 0 - either with add(fill_value) or on the DF itself, as here
        self.dta[varsUsed] = self.dta[varsUsed].fillna(value=0)

        self.dta['Total_ChangeInWealth_' + self.inflatedTimespan] = self.dta[totalChangeVars].sum(axis=1, skipna=True)
        self.dta['Total_CapitalGains_' + self.inflatedTimespan] = self.dta[capitalGainsVars].sum(axis=1, skipna=True)
        self.dta['Total_GrossSavings_' + self.inflatedTimespan] = self.dta[grossSavingsVars].sum(axis=1, skipna=True)
        self.dta['Total_OpenCloseTransfers_' + self.inflatedTimespan] = self.dta[transferVars].sum(axis=1, skipna=True)

        # People moving in -- NOT savings; a transfer. Any money IN here should be REMOVED from savings
        self.dta['netMoveIn_' + self.inflatedTimespan] = (
                    self.dta['PersonMovedIn_SinceLastQYr_AssetsMovedIn_' + self.eyStr].fillna(0) * inflationForFlow).sub(
            self.dta['PersonMovedIn_SinceLastQYr_DebtsMovedIn_' + self.eyStr].fillna(0) * inflationForFlow)
        # If missing BOTH then doesn't mean anything
        self.dta.loc[self.dta['PersonMovedIn_SinceLastQYr_AssetsMovedIn_' + self.eyStr].isna() & self.dta['PersonMovedIn_SinceLastQYr_DebtsMovedIn_' + self.eyStr].isna(), 'netMoveIn_' + self.inflatedTimespan] = None

        # People moving out -- NOT savings; a transfer. Any money OUT here should be ADDED to savings
        self.dta['netMoveOut_' + self.inflatedTimespan] = (
                    self.dta['PersonMovedOut_SinceLastQYr_AssetsMovedOut_' + self.eyStr].fillna(0) * inflationForFlow).sub(
            self.dta['PersonMovedOut_SinceLastQYr_DebtsMovedOut_' + self.eyStr].fillna(0) * inflationForFlow)
        # If missing BOTH then doesn't mean anything
        self.dta.loc[self.dta['PersonMovedOut_SinceLastQYr_AssetsMovedOut_' + self.eyStr].isna() & self.dta['PersonMovedOut_SinceLastQYr_DebtsMovedOut_' + self.eyStr].isna(), 'netMoveOut_' + self.inflatedTimespan] = None

        self.dta['netAssetMove_' + self.inflatedTimespan] = self.dta['netMoveOut_' + self.inflatedTimespan].fillna(0).sub(
            self.dta['netMoveIn_' + self.inflatedTimespan].fillna(0))
        # If missing BOTH then doesn't mean anything
        self.dta.loc[self.dta['netMoveIn_' + self.inflatedTimespan].isna() & self.dta['netMoveOut_' + self.inflatedTimespan].isna(), 'netAssetMove_' + self.inflatedTimespan] = None

        self.dta['largeGift_All_AmountHH_' + self.inflatedTimespan] = self.dta['largeGift_All_AmountHH_' + self.eyStr] * inflationForFlow
        self.dta['SmallGift_All_AmountHH_' + self.inflatedTimespan] = self.dta['SmallGift_All_AmountHH_' + self.eyStr] * inflationForFlow

        # NOTE -- intentionally NOT filling NAs on Gross Savings - so as not to override decision above
        # See above on the importance of the decision to have NAs in Gross Savings (or not)
        # Also see Above on the NET value of the opening and closing of accounts is saving (or dissaving)
        self.dta['Total_NetActiveSavings_' + self.inflatedTimespan] = self.dta['Total_GrossSavings_' + self.inflatedTimespan]. \
            add(self.dta['Total_OpenCloseTransfers_' + self.inflatedTimespan].fillna(0)).\
            sub(self.dta['largeGift_All_AmountHH_' + self.inflatedTimespan].fillna(0)). \
            sub(self.dta['SmallGift_All_AmountHH_' + self.inflatedTimespan].fillna(0)). \
            add(self.dta['netAssetMove_' + self.inflatedTimespan].fillna(0))

        # Annualize everything for easier analysis
        self.dta['Annual_Total_NetActiveSavings_' + self.inflatedTimespan] = (1/self.duration)*self.dta['Total_NetActiveSavings_' + self.inflatedTimespan]
        self.dta['Annual_Total_GrossSavings_' + self.inflatedTimespan] = (1/self.duration)*self.dta['Total_GrossSavings_' + self.inflatedTimespan]
        self.dta['Annual_Total_OpenCloseTransfers_' + self.inflatedTimespan] = (1/self.duration)*self.dta['Total_OpenCloseTransfers_' + self.inflatedTimespan]
        self.dta['Annual_Total_CapitalGains_' + self.inflatedTimespan] = (1/self.duration)*self.dta['Total_CapitalGains_' + self.inflatedTimespan]
        self.dta['Annual_SmallGift_All_AmountHH_' + self.inflatedTimespan] = (1/self.duration)*self.dta['SmallGift_All_AmountHH_' + self.inflatedTimespan]
        self.dta['Annual_netAssetMove_' + self.inflatedTimespan] = (1/self.duration)*self.dta['netAssetMove_' + self.inflatedTimespan]
        self.dta['Annual_largeGift_All_AmountHH_' + self.inflatedTimespan] = (1/self.duration)*self.dta['largeGift_All_AmountHH_' + self.inflatedTimespan]

        self.dta['activeSavingsRate_AnnualHH_' + self.inflatedTimespan] = (self.dta['Annual_Total_NetActiveSavings_' + self.inflatedTimespan])
        # Its difficult to tell which income var Gittleman used, but it appears to be the Real, PreTax Income
        self.dta['activeSavingsRate_AnnualHH_' + self.inflatedTimespan] = (self.dta['activeSavingsRate_AnnualHH_' + self.inflatedTimespan].div(
                self.dta['averageRealBeforeTaxIncome_AllYears_' + self.inflatedTimespan], fill_value=0))

        # The unbanked fall into a special category of NAs -- they will show 0

    def executeForTimespan(self, startYear, endYear, toYear):
        '''
        This function controls the Savings Rate process.  It loads the data we need, calcs asset-class level values, then total family values
        :param startYear:
        :type startYear:
        :param endYear:
        :type endYear:
        :param toYear:
        :type toYear:
        :return:
        :rtype:
        '''
        self.clearData()
        self.setPeriod(startYear, endYear, toYear)
        self.readLongitudinalData()
        self.fillNoAccountStockValues()

        # self.calcDetermineAssetLevelCapitalGains_GittlemanStyle()
        statusCounts = self.calcDetermineAssetLevelCapitalGains_SimpliedSWStyle()
        self.calcTotalSavingsRate()
        self.recalculateTotalWealth()

        self.dta = InequalityAnalysisBase.selectiveReorder(self.dta,
                                                           ['cleaningStatus_' + self.timespan,
                                                            'modificationStatus_' + self.timespan,
                                                            'familyInterviewId_' + str(self.syStr),
                                                            'familyInterviewId_' + str(self.eyStr),
                                                            'raceR_' + self.syStr,
                                                            'inflatedNetWorthWithHome_' + self.inflatedStart,
                                                            'changeInRealNetWorth_' + self.inflatedTimespan,
                                                            'changeInRealNetWorthWithHomeAnd401k_AfterBalanceFillin_' + self.inflatedTimespan,
                                                            'inflatedAfterTaxIncome_' + self.inflatedStart,
                                                            'Total_NetActiveSavings_' + self.inflatedTimespan,
                                                            'activeSavingsRate_AnnualHH_' + self.inflatedTimespan,

                                                            'Total_ChangeInWealth_' + self.inflatedTimespan,
                                                            'Total_CapitalGains_' + self.inflatedTimespan,
                                                            'Total_GrossSavings_' + self.inflatedTimespan,
                                                            ], alphabetizeTheOthers=True)

        # Save all of the data we might need
        # Note -- The full dataset can be overwhelming....
        self.saveLongitudinalData()

        return statusCounts

    def doIt(self, useCleanedDataOnly = True, excludeRetirementSavings = False):
        self.useCleanedDataOnly = useCleanedDataOnly
        self.excludeRetirementSavings = excludeRetirementSavings
        toYear = 2019

        # self.yearsWealthDataCollected = [2017, 2019]
        startYear = self.yearsWealthDataCollected[0]

        totalStatusCounts = []
        for endYear in self.yearsWealthDataCollected[1:]:
            # Do the core analysis: change in wealth and savings rates over time
            totalStatusCounts += self.executeForTimespan(startYear, endYear, toYear)
            # Get ready for next year
            startYear = endYear

        pd.DataFrame(totalStatusCounts).to_csv(os.path.join(self.baseDir,
            self.outputSubDir, self.outputBaseName + "_VarStatusCounts.csv"), index=False)





''' Allow execution from command line, etc. Useful for debugging.'''
if __name__ == "__main__":
    calcer = CalcSavingsRates(
        baseDir='C:/dev/sensitive_data/InvestorSuccess/Inequality',
        familyInputSubDir='inequalityInput_enrichedPop',
        inputBaseName="", # "testData_", #  "" for normal data
        outputBaseName="WithSavings_",
        outputSubDir='inequalityOutput_enrichedPop',
    )

    # calcer.doIt()
    # calcer.executeForTimespan(2015, 2017, 2019)

    calcer.clearData()
    calcer.setPeriod(2017, 2019, 2019)
    calcer.readLongitudinalData()

    calcer.fillNoAccountStockValues()
    calcer.calcDetermineAssetLevelCapitalGains_SimpliedSWStyle()
    calcer.calcTotalSavingsRate()
    calcer.recalculateTotalWealth()


    debugFieldsOfInterest = [
        'cleaningStatus_2015_2017',
        'modificationStatus_2015_2017',
        'familyInterviewId_2015',
        'familyInterviewId_2017',
        'retirementContribHH_2015',
        'retirementContribHH_2017',
        'retirementContribRateR_2015',
        'retirementContribRateR_2017',
        'retirementContribRateS_2015',
        'retirementContribRateS_2017',
        'EmployerRetirePlan_CapitalGains_2015_2017_as_2017',
        'EmployerRetirePlan_Savings_2015_2017_as_2017',
        'EmployerRetirePlan_TotalChangeInWealth_2015_2017_as_2017',
        'valueOfEmployerRetirePlan_Gross_2015',
        'valueOfEmployerRetirePlan_Gross_2017'
        ]

    tmpDta = InequalityAnalysisBase.selectiveReorder(calcer.dta, debugFieldsOfInterest, alphabetizeTheOthers=True)

    tmpDta.to_csv('C:/dev/sensitive_data/InvestorSuccess/Inequality/inequalityOutput/testCalcSavings_Full.csv')

