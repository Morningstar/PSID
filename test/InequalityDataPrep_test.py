import SavingsRates.InequalityDataPrep as InequalityDataPrep
import unittest
import pandas as pd
import numpy.testing as npt
import Inflation.CPI_InflationReader as CPI_InflationReader
from mock import patch, MagicMock

from pandas.testing import assert_frame_equal, assert_series_equal


"""Tests for SW's Savings Analysis Functions"""

# TODO -- Update this class to use a Mocker for Inflation -- all values tested against here assume NO inflation


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


class InequalityDataPrep_Test(unittest.TestCase):

    def setUp(self):

        raise Exception("Not implemented -- just a copy of the Gittleman analysis")

        self.patcher = patch('Inflation.CPI_InflationReader.CPIInflationReader')
        self.addCleanup(self.patcher.stop)
        self.inflationMocker = self.patcher.start()
        # self.inflationMocker.getInflationFactorBetweenTwoYears = MagicMock(return_value=1)
        # self.inflationMocker.getInflationFactorBetweenTwoYears.return_value = 1
        self.inflationMocker().getInflationFactorBetweenTwoYears.return_value = 1

        self.ie = InequalityDataPrep.InequalityDataPrep(baseDir="A",
                                                      familyInputSubDir="B",
                                                      familyBaseName="C",
                                                      individualInputSubDir="D",
                                                      individualBaseName="E",
                                                      outputSubDir="F")

        self.assertTrue(self.ie.inflation.getInflationFactorBetweenTwoYears(1954, 1989) == 1)

        self.ie.clearData()
        self.ie.setPeriod(1989, 1994, 1998)
        self.ie.yearsWithFamilyData = [self.ie.startYear, self.ie.endYear]

        self.idVar = 'familyId_' + self.ie.syStr
        # self.readData()
        # self.checkQualityOfInputData()

        # self.calcIfValueOnMoveAndChangedHeadAtAnyPoint()

        # self.calcAfterTaxIncome(True)
        # self.inflateValues(True)
        # self.calcAverageMoneyIncome()
        # self.calcDetermineAssetLevelCapitalGains()
        # self.cleanResults(preliminaryClean_beforeSavingsCalcAnalysis=True)

        # self.calcSavingsRate_ActiveSavings()
        # self.createSegmentBins()
        # self.cleanResults(preliminaryClean_beforeSavingsCalcAnalysis=False)
        # ...
        # results = self.calcWeightedAggResultsForYear()


      
    def createDummyData(self, includeMovingVars = False, includeValueVars = False, includeChangeInValueVars = False):

        # Start with a simple empty DF -- two families
        testData = pd.DataFrame({
                'familyId_' + self.ie.syStr :['1','2'], 
                'raceR_' + self.ie.syStr :['White', 'Black'], 
                'ageR_' + self.ie.syStr :[44, 44], 
                'averageRealBeforeTaxIncome_AllYears_' + self.ie.inflatedTimespan : [10000, 70000],
                'averageRealAfterTaxIncome_AllYears_' + self.ie.inflatedTimespan : [10000, 70000],
                'averageNominalIncome_AllYears_' + self.ie.timespan : [8000, 60000],
                'educationYearsR_' + self.ie.syStr : [14, 14],
                'martialStatusR_' + self.ie.syStr: ['Married', 'Married'],
                'LongitudinalWeightHH_' + self.ie.syStr:[1,1],
                'complexWeight_' + self.ie.syStr:[10,20],
                'cleaningStatus_' + self.ie.eyStr : ['Keep', 'Keep']},
            columns=['familyId_' + self.ie.syStr, 'raceR_' + self.ie.syStr,
                     'ageR_' + self.ie.syStr, 'averageRealBeforeTaxIncome_AllYears_' + self.ie.inflatedTimespan, 'averageRealAfterTaxIncome_AllYears_' + self.ie.inflatedTimespan, 'averageNominalIncome_AllYears_' + self.ie.timespan,
                     'educationYearsR_' + self.ie.syStr, 'martialStatusR_' + self.ie.syStr, 
                     'LongitudinalWeightHH_' + self.ie.syStr, 'complexWeight' + self.ie.syStr, 'cleaningStatus_' + self.ie.eyStr
                     ])

        if includeMovingVars:
            testData['ChangeInHeadFU_' + self.ie.timespan] = False
            testData['House_ValueIncrease_WhenMoving_' + self.ie.inflatedTimespan] = 0
            testData['House_ValueIncrease_WhenNotMoving_' + self.ie.inflatedTimespan] = 0
            testData['House_TotalChangeInMortgageDebt_WhenNotMoving_' + self.ie.inflatedTimespan] = 0
            testData['House_TotalChangeInMortgageDebt_WhenMoving_' + self.ie.inflatedTimespan] = 0
            testData['CostOfMajorHomeRenovations_' + self.ie.syStr] = 0
            testData['CostOfMajorHomeRenovations_' + self.ie.eyStr] = 0
        else:
            testData['valueOfHouse_Gross_' + self.ie.syStr] = 0  # Gross or net?
            testData['valueOfHouse_Gross_' + self.ie.eyStr] = 0
            testData['valueOfHouse_Gross_' + str(self.ie.endYear - self.ie.timeStep)] = 0
            testData['valueOfHouse_Debt_' + self.ie.eyStr] = 0
            testData['valueOfHouse_Debt_' + self.ie.eyStr] = 0
            testData['valueOfHouse_Debt_' + str(self.ie.endYear - self.ie.timeStep)] = 0
            testData['ChangeInCompositionFU_' + self.ie.syStr] = 0
            testData['ChangeInCompositionFU_' + self.ie.eyStr] = 0
            testData['MovedR_' + self.ie.syStr] = False
            testData['MovedR_' + str(self.ie.endYear - self.ie.timeStep)] = False
            testData['MovedR_' + self.ie.eyStr] = False

        if includeValueVars:
            ''' Vars used to saving versus capital gains'''
            componentVars = ['House_Gross', 'House_Debt', 'OtherRealEstate_Net', 'Business_Net', 'BrokerageStocks_Net', 'CheckingAndSavings_Net', 'Vehicle_Net', 'OtherAssets_Net', 'OtherDebts_Net', 'PrivateRetirePlan_Gross', 'EmployerRetirePlan_Gross']
            valueVars_Start = ['valueOf' + s + "_" + self.ie.syStr for s in componentVars]    
            valueVars_End = ['valueOf' + s + "_" + self.ie.eyStr for s in componentVars]    
            boughtVars_End = ['PrivateRetirePlan_SinceLastQYr_AmountMovedIn_' + self.ie.eyStr] + [s + '_SinceLastQYr_AmountBought_' + self.ie.eyStr for s in ['OtherRealEstate', 'Business', 'BrokerageStocks']]
            soldVars_End = ['PrivateRetirePlan_SinceLastQYr_AmountMovedOut_' + self.ie.eyStr] + [s + '_SinceLastQYr_AmountSold_' + self.ie.eyStr for s in ['OtherRealEstate', 'Business', 'BrokerageStocks']]
            allVars = [] + valueVars_Start + valueVars_End  + boughtVars_End + soldVars_End
            for var in allVars:
                testData[var] = 0
    
        if includeChangeInValueVars:
            ''' Vars as inputs to Analyze Savings Rate'''
            # Each of the following entries should have a varaible _TotalChangeInWealth, _CapitalGains and _Savings
            componentVarsNoGrossOrNet = ['House', 'OtherRealEstate', 'Business', 'BrokerageStocks', 'CheckingAndSavings', 'Vehicle', 'OtherAssets', 'OtherDebts', 'PrivateRetirePlan', 'EmployerRetirePlan']
            totalChangeVars = [s + "_TotalChangeInWealth_" + self.ie.inflatedTimespan for s in componentVarsNoGrossOrNet]
            capitalGainsVars = [s + "_CapitalGains_" + self.ie.inflatedTimespan for s in componentVarsNoGrossOrNet]
            grossSavingsVars = [s + "_Savings_" + self.ie.inflatedTimespan for s in componentVarsNoGrossOrNet]
            
            allVars = [] + totalChangeVars + capitalGainsVars + grossSavingsVars + \
                    ['PersonMovedIn_SinceLastQYr_AssetsMovedIn_'   + self.ie.eyStr, 
                     'PersonMovedIn_SinceLastQYr_DebtsMovedIn_' + self.ie.eyStr, 
                     'PersonMovedOut_SinceLastQYr_AssetsMovedOut_' + self.ie.eyStr,
                     'PersonMovedOut_SinceLastQYr_DebtsMovedOut_' + self.ie.eyStr,
                     'PrivateRetirePlan_SinceLastQYr_AmountMovedIn_' + self.ie.eyStr,
                     'PrivateRetirePlan_SinceLastQYr_AmountMovedOut_' + self.ie.eyStr,
                     'largeGift_All_AmountHH_' + self.ie.eyStr,
                    ]
                  
            for var in allVars:
                testData[var] = 0
                
        return testData

    def test_calcIfValueOnMoveAndChangedHeadAtAnyPoint(self):

        data = self.createDummyData(includeMovingVars = False,  includeValueVars = False, includeChangeInValueVars = False)

        data.loc[data[self.idVar] =='1', 'valueOfHouse_Gross_' + str(self.ie.endYear - self.ie.timeStep)] = 4000
        data.loc[data[self.idVar] =='1', 'valueOfHouse_Gross_' + self.ie.eyStr] = 10000

        data.loc[data[self.idVar] =='2', 'valueOfHouse_Debt_' + str(self.ie.endYear - self.ie.timeStep)] = 10000
        data.loc[data[self.idVar] =='2', 'valueOfHouse_Debt_' + self.ie.eyStr] = 8000
        
        self.ie.dta =  data
        self.ie.calcIfValueOnMoveAndChangedHeadAtAnyPoint()
        
        valueChange = self.ie.dta.loc[self.ie.dta[self.idVar] =='1', 'House_ValueIncrease_WhenNotMoving_' + self.ie.inflatedTimespan].iloc[0]
        principalChange = self.ie.dta.loc[self.ie.dta[self.idVar] =='2', 'House_TotalChangeInMortgageDebt_WhenNotMoving_' + self.ie.inflatedTimespan].iloc[0]
        noChangeInHead = self.ie.dta['ChangeInHeadFU_' + self.ie.timespan].eq(False).all()
        
        self.assertTrue(closeEnough(valueChange, 6000))
        self.assertTrue(closeEnough(principalChange, -2000))
        self.assertTrue(noChangeInHead)
        
    def test_calcIfChangedHead(self):

        data = self.createDummyData(includeMovingVars = False,  includeValueVars = False, includeChangeInValueVars = False)

        # A change in PRIOR year should not affect
        data.loc[data[self.idVar] =='1', 'ChangeInCompositionFU_' + self.ie.syStr] = 5
        
        # A change in final year should affect 
        data.loc[data[self.idVar] =='2', 'ChangeInCompositionFU_' + self.ie.eyStr] = 5
        
        self.ie.dta =  data
        self.ie.calcIfValueOnMoveAndChangedHeadAtAnyPoint()

        changeInHead_No= self.ie.dta.loc[self.ie.dta[self.idVar] =='1', 'ChangeInHeadFU_' + self.ie.timespan].iloc[0]
        changeInHead_Yes= self.ie.dta.loc[self.ie.dta[self.idVar] =='2', 'ChangeInHeadFU_' + self.ie.timespan].iloc[0]

        self.assertTrue(changeInHead_Yes)
        self.assertFalse(changeInHead_No)

    def test_homeValueOnMove(self):

        data = self.createDummyData(includeMovingVars = False,  includeValueVars = False, includeChangeInValueVars = False)

        data.loc[data[self.idVar] =='1', 'MovedR_' + self.ie.eyStr] = True
        data.loc[data[self.idVar] =='1', 'valueOfHouse_Gross_' + self.ie.syStr] = 50  # Note -- this will have no effect because we've hard coded the analysis years above
        data.loc[data[self.idVar] =='1', 'valueOfHouse_Gross_' + str(self.ie.endYear - self.ie.timeStep)] = 4000
        data.loc[data[self.idVar] =='1', 'valueOfHouse_Gross_' + self.ie.eyStr] = 10000

        data.loc[data[self.idVar] =='2', 'MovedR_' + self.ie.syStr] = True # Should have no effect
        data.loc[data[self.idVar] =='2', 'valueOfHouse_Debt_' + str(self.ie.endYear - self.ie.timeStep)] = 11000
        data.loc[data[self.idVar] =='2', 'valueOfHouse_Debt_' + self.ie.eyStr] = 8050
        data.loc[data[self.idVar] =='2', 'valueOfHouse_Gross_' + str(self.ie.endYear - self.ie.timeStep)] = 50000
        data.loc[data[self.idVar] =='2', 'valueOfHouse_Gross_' + self.ie.eyStr] = 57500

        self.ie.dta =  data
        self.ie.calcIfValueOnMoveAndChangedHeadAtAnyPoint()
        
        # Person 1
        valueChangeNoMove = self.ie.dta.loc[self.ie.dta[self.idVar] =='1', 'House_ValueIncrease_WhenNotMoving_' + self.ie.inflatedTimespan].iloc[0]
        valueChangeMove = self.ie.dta.loc[self.ie.dta[self.idVar] =='1', 'House_ValueIncrease_WhenMoving_' + self.ie.inflatedTimespan].iloc[0]
        principalChangeNoMove = self.ie.dta.loc[self.ie.dta[self.idVar] =='1', 'House_TotalChangeInMortgageDebt_WhenNotMoving_' + self.ie.inflatedTimespan].iloc[0]

        self.assertTrue(closeEnough(valueChangeNoMove, 0))
        self.assertTrue(closeEnough(valueChangeMove, 6000))
        self.assertTrue(closeEnough(principalChangeNoMove, 0))
        
        # Person 2
        valueChangeNoMove = self.ie.dta.loc[self.ie.dta[self.idVar] =='2', 'House_ValueIncrease_WhenNotMoving_' + self.ie.inflatedTimespan].iloc[0]
        valueChangeMove = self.ie.dta.loc[self.ie.dta[self.idVar] =='2', 'House_ValueIncrease_WhenMoving_' + self.ie.inflatedTimespan].iloc[0]
        principalChangeNoMove = self.ie.dta.loc[self.ie.dta[self.idVar] =='2', 'House_TotalChangeInMortgageDebt_WhenNotMoving_' + self.ie.inflatedTimespan].iloc[0]

        self.assertTrue(closeEnough(valueChangeNoMove, 7500))
        self.assertTrue(closeEnough(valueChangeMove, 0))
        self.assertTrue(closeEnough(principalChangeNoMove, -2950))

    def test_createSegmentBins(self):
        data = self.createDummyData(includeMovingVars = False, includeValueVars = False, includeChangeInValueVars = False)
        self.ie.dta =  data
        self.ie.createSegmentBins()


    if __name__ == '__main__':
        unittest.main()

