import Replication.GittlemanAnalysis as GittlemanAnalysis
import unittest
import pandas as pd
import numpy.testing as npt
import Inflation.CPI_InflationReader as CPI_InflationReader
from mock import patch, MagicMock

from pandas.testing import assert_frame_equal, assert_series_equal


"""Tests for Gittman Savings Analysis Functions"""

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


class GittlemanAnalysisTest(unittest.TestCase):

    def setUp(self):
        self.patcher = patch('Inflation.CPI_InflationReader.CPIInflationReader')
        self.addCleanup(self.patcher.stop)
        self.inflationMocker = self.patcher.start()
        # self.inflationMocker.getInflationFactorBetweenTwoYears = MagicMock(return_value=1)
        # self.inflationMocker.getInflationFactorBetweenTwoYears.return_value = 1
        self.inflationMocker().getInflationFactorBetweenTwoYears.return_value = 1

        self.ga = GittlemanAnalysis.GittlemanAnalysis(baseDir="A",
                                                      familyInputSubDir="B",
                                                      familyBaseName="C",
                                                      individualInputSubDir="D",
                                                      individualBaseName="E",
                                                      outputSubDir="F")

        self.assertTrue(self.ga.inflation.getInflationFactorBetweenTwoYears(1954, 1989) == 1)

        self.ga.clearData()
        self.ga.setPeriod(1989, 1994, 1998)
        self.ga.yearsWithFamilyData = [self.ga.startYear, self.ga.endYear]

        self.idVar = 'familyId_' + self.ga.syStr
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
                'familyId_' + self.ga.syStr :['1','2'], 
                'raceR_' + self.ga.syStr :['White', 'Black'], 
                'ageR_' + self.ga.syStr :[44, 44], 
                'averageRealBeforeTaxIncome_AllYears_' + self.ga.inflatedTimespan : [10000, 70000],
                'averageRealAfterTaxIncome_AllYears_' + self.ga.inflatedTimespan : [10000, 70000],
                'averageNominalIncome_AllYears_' + self.ga.timespan : [8000, 60000],
                'educationYearsR_' + self.ga.syStr : [14, 14],
                'martialStatusR_' + self.ga.syStr: ['Married', 'Married'],
                'LongitudinalWeightHH_' + self.ga.syStr:[1,1],
                'complexWeight_' + self.ga.syStr:[10,20],
                'cleaningStatus_' + self.ga.eyStr : ['Keep', 'Keep']},
            columns=['familyId_' + self.ga.syStr, 'raceR_' + self.ga.syStr,
                     'ageR_' + self.ga.syStr, 'averageRealBeforeTaxIncome_AllYears_' + self.ga.inflatedTimespan, 'averageRealAfterTaxIncome_AllYears_' + self.ga.inflatedTimespan, 'averageNominalIncome_AllYears_' + self.ga.timespan,
                     'educationYearsR_' + self.ga.syStr, 'martialStatusR_' + self.ga.syStr, 
                     'LongitudinalWeightHH_' + self.ga.syStr, 'complexWeight' + self.ga.syStr, 'cleaningStatus_' + self.ga.eyStr
                     ])

        if includeMovingVars:
            testData['ChangeInHeadFU_' + self.ga.timespan] = False
            testData['House_ValueIncrease_WhenMoving_' + self.ga.inflatedTimespan] = 0
            testData['House_ValueIncrease_WhenNotMoving_' + self.ga.inflatedTimespan] = 0
            testData['House_TotalChangeInMortgageDebt_WhenNotMoving_' + self.ga.inflatedTimespan] = 0
            testData['House_TotalChangeInMortgageDebt_WhenMoving_' + self.ga.inflatedTimespan] = 0
            testData['CostOfMajorHomeRenovations_' + self.ga.syStr] = 0
            testData['CostOfMajorHomeRenovations_' + self.ga.eyStr] = 0
        else:
            testData['valueOfHouse_Gross_' + self.ga.syStr] = 0  # Gross or net?
            testData['valueOfHouse_Gross_' + self.ga.eyStr] = 0
            testData['valueOfHouse_Gross_' + str(self.ga.endYear - self.ga.timeStep)] = 0
            testData['valueOfHouse_Debt_' + self.ga.eyStr] = 0
            testData['valueOfHouse_Debt_' + self.ga.eyStr] = 0
            testData['valueOfHouse_Debt_' + str(self.ga.endYear - self.ga.timeStep)] = 0
            testData['ChangeInCompositionFU_' + self.ga.syStr] = 0
            testData['ChangeInCompositionFU_' + self.ga.eyStr] = 0
            testData['MovedR_' + self.ga.syStr] = False
            testData['MovedR_' + str(self.ga.endYear - self.ga.timeStep)] = False
            testData['MovedR_' + self.ga.eyStr] = False

        if includeValueVars:
            ''' Vars used to saving versus capital gains'''
            componentVars = ['House_Gross', 'House_Debt', 'OtherRealEstate_Net', 'Business_Net', 'BrokerageStocks_Net', 'CheckingAndSavings_Net', 'Vehicle_Net', 'OtherAssets_Net', 'OtherDebts_Net', 'PrivateRetirePlan_Gross', 'EmployerRetirePlan_Gross']
            valueVars_Start = ['valueOf' + s + "_" + self.ga.syStr for s in componentVars]    
            valueVars_End = ['valueOf' + s + "_" + self.ga.eyStr for s in componentVars]    
            boughtVars_End = ['PrivateRetirePlan_SinceLastQYr_AmountMovedIn_' + self.ga.eyStr] + [s + '_SinceLastQYr_AmountBought_' + self.ga.eyStr for s in ['OtherRealEstate', 'Business', 'BrokerageStocks']]
            soldVars_End = ['PrivateRetirePlan_SinceLastQYr_AmountMovedOut_' + self.ga.eyStr] + [s + '_SinceLastQYr_AmountSold_' + self.ga.eyStr for s in ['OtherRealEstate', 'Business', 'BrokerageStocks']]
            allVars = [] + valueVars_Start + valueVars_End  + boughtVars_End + soldVars_End
            for var in allVars:
                testData[var] = 0
    
        if includeChangeInValueVars:
            ''' Vars as inputs to Analyze Savings Rate'''
            # Each of the following entries should have a varaible _TotalChangeInWealth, _CapitalGains and _Savings
            componentVarsNoGrossOrNet = ['House', 'OtherRealEstate', 'Business', 'BrokerageStocks', 'CheckingAndSavings', 'Vehicle', 'OtherAssets', 'OtherDebts', 'PrivateRetirePlan', 'EmployerRetirePlan']
            totalChangeVars = [s + "_TotalChangeInWealth_" + self.ga.inflatedTimespan for s in componentVarsNoGrossOrNet]
            capitalGainsVars = [s + "_CapitalGains_" + self.ga.inflatedTimespan for s in componentVarsNoGrossOrNet]
            grossSavingsVars = [s + "_Savings_" + self.ga.inflatedTimespan for s in componentVarsNoGrossOrNet]
            
            allVars = [] + totalChangeVars + capitalGainsVars + grossSavingsVars + \
                    ['PersonMovedIn_SinceLastQYr_AssetsMovedIn_'   + self.ga.eyStr, 
                     'PersonMovedIn_SinceLastQYr_DebtsMovedIn_' + self.ga.eyStr, 
                     'PersonMovedOut_SinceLastQYr_AssetsMovedOut_' + self.ga.eyStr,
                     'PersonMovedOut_SinceLastQYr_DebtsMovedOut_' + self.ga.eyStr,
                     'PrivateRetirePlan_SinceLastQYr_AmountMovedIn_' + self.ga.eyStr,
                     'PrivateRetirePlan_SinceLastQYr_AmountMovedOut_' + self.ga.eyStr,
                     'largeGift_All_AmountHH_' + self.ga.eyStr,
                    ]
                  
            for var in allVars:
                testData[var] = 0
                
        return testData

    def test_calcIfValueOnMoveAndChangedHeadAtAnyPoint(self):

        data = self.createDummyData(includeMovingVars = False,  includeValueVars = False, includeChangeInValueVars = False)

        data.loc[data[self.idVar] =='1', 'valueOfHouse_Gross_' + str(self.ga.endYear - self.ga.timeStep)] = 4000
        data.loc[data[self.idVar] =='1', 'valueOfHouse_Gross_' + self.ga.eyStr] = 10000

        data.loc[data[self.idVar] =='2', 'valueOfHouse_Debt_' + str(self.ga.endYear - self.ga.timeStep)] = 10000
        data.loc[data[self.idVar] =='2', 'valueOfHouse_Debt_' + self.ga.eyStr] = 8000
        
        self.ga.dta =  data
        self.ga.calcIfValueOnMoveAndChangedHeadAtAnyPoint()
        
        valueChange = self.ga.dta.loc[self.ga.dta[self.idVar] =='1', 'House_ValueIncrease_WhenNotMoving_' + self.ga.inflatedTimespan].iloc[0]
        principalChange = self.ga.dta.loc[self.ga.dta[self.idVar] =='2', 'House_TotalChangeInMortgageDebt_WhenNotMoving_' + self.ga.inflatedTimespan].iloc[0]
        noChangeInHead = self.ga.dta['ChangeInHeadFU_' + self.ga.timespan].eq(False).all()
        
        self.assertTrue(closeEnough(valueChange, 6000))
        self.assertTrue(closeEnough(principalChange, -2000))
        self.assertTrue(noChangeInHead)
        
    def test_calcIfChangedHead(self):

        data = self.createDummyData(includeMovingVars = False,  includeValueVars = False, includeChangeInValueVars = False)

        # A change in PRIOR year should not affect
        data.loc[data[self.idVar] =='1', 'ChangeInCompositionFU_' + self.ga.syStr] = 5
        
        # A change in final year should affect 
        data.loc[data[self.idVar] =='2', 'ChangeInCompositionFU_' + self.ga.eyStr] = 5
        
        self.ga.dta =  data
        self.ga.calcIfValueOnMoveAndChangedHeadAtAnyPoint()

        changeInHead_No= self.ga.dta.loc[self.ga.dta[self.idVar] =='1', 'ChangeInHeadFU_' + self.ga.timespan].iloc[0]
        changeInHead_Yes= self.ga.dta.loc[self.ga.dta[self.idVar] =='2', 'ChangeInHeadFU_' + self.ga.timespan].iloc[0]

        self.assertTrue(changeInHead_Yes)
        self.assertFalse(changeInHead_No)

    def test_homeValueOnMove(self):

        data = self.createDummyData(includeMovingVars = False,  includeValueVars = False, includeChangeInValueVars = False)

        data.loc[data[self.idVar] =='1', 'MovedR_' + self.ga.eyStr] = True
        data.loc[data[self.idVar] =='1', 'valueOfHouse_Gross_' + self.ga.syStr] = 50  # Note -- this will have no effect because we've hard coded the analysis years above
        data.loc[data[self.idVar] =='1', 'valueOfHouse_Gross_' + str(self.ga.endYear - self.ga.timeStep)] = 4000
        data.loc[data[self.idVar] =='1', 'valueOfHouse_Gross_' + self.ga.eyStr] = 10000

        data.loc[data[self.idVar] =='2', 'MovedR_' + self.ga.syStr] = True # Should have no effect
        data.loc[data[self.idVar] =='2', 'valueOfHouse_Debt_' + str(self.ga.endYear - self.ga.timeStep)] = 11000
        data.loc[data[self.idVar] =='2', 'valueOfHouse_Debt_' + self.ga.eyStr] = 8050
        data.loc[data[self.idVar] =='2', 'valueOfHouse_Gross_' + str(self.ga.endYear - self.ga.timeStep)] = 50000
        data.loc[data[self.idVar] =='2', 'valueOfHouse_Gross_' + self.ga.eyStr] = 57500

        self.ga.dta =  data
        self.ga.calcIfValueOnMoveAndChangedHeadAtAnyPoint()
        
        # Person 1
        valueChangeNoMove = self.ga.dta.loc[self.ga.dta[self.idVar] =='1', 'House_ValueIncrease_WhenNotMoving_' + self.ga.inflatedTimespan].iloc[0]
        valueChangeMove = self.ga.dta.loc[self.ga.dta[self.idVar] =='1', 'House_ValueIncrease_WhenMoving_' + self.ga.inflatedTimespan].iloc[0]
        principalChangeNoMove = self.ga.dta.loc[self.ga.dta[self.idVar] =='1', 'House_TotalChangeInMortgageDebt_WhenNotMoving_' + self.ga.inflatedTimespan].iloc[0]

        self.assertTrue(closeEnough(valueChangeNoMove, 0))
        self.assertTrue(closeEnough(valueChangeMove, 6000))
        self.assertTrue(closeEnough(principalChangeNoMove, 0))
        
        # Person 2
        valueChangeNoMove = self.ga.dta.loc[self.ga.dta[self.idVar] =='2', 'House_ValueIncrease_WhenNotMoving_' + self.ga.inflatedTimespan].iloc[0]
        valueChangeMove = self.ga.dta.loc[self.ga.dta[self.idVar] =='2', 'House_ValueIncrease_WhenMoving_' + self.ga.inflatedTimespan].iloc[0]
        principalChangeNoMove = self.ga.dta.loc[self.ga.dta[self.idVar] =='2', 'House_TotalChangeInMortgageDebt_WhenNotMoving_' + self.ga.inflatedTimespan].iloc[0]

        self.assertTrue(closeEnough(valueChangeNoMove, 7500))
        self.assertTrue(closeEnough(valueChangeMove, 0))
        self.assertTrue(closeEnough(principalChangeNoMove, -2950))


    def test_calcDetermineAssetLevelCapitalGains_AllZero(self):

        data = self.createDummyData(includeMovingVars = True,  includeValueVars = True, includeChangeInValueVars = False)
        data.loc[data[self.idVar] =='1', 'valueOfBrokerageStocks_Net_'+ self.ga.eyStr] = None
        data.loc[data[self.idVar] =='2', 'valueOfCheckingAndSavings_Net_'+ self.ga.syStr] = None
        self.ga.dta =  data
        self.ga.calcDetermineAssetLevelCapitalGains()        

        componentVars = ['House', 'OtherRealEstate', 'Business', 'BrokerageStocks', 'CheckingAndSavings', 'Vehicle', 'OtherAssets', 'OtherDebts']
        # Actually, Gittleman Never includes 'PrivateRetirePlan', 'EmployerRetirePlan'
        # if self.ga.eyStr > 1999:
        #     componentVars = componentVars + ['PrivateRetirePlan', 'EmployerRetirePlan']
        totalChangeVars = [s + '_TotalChangeInWealth_' + self.ga.inflatedTimespan for s in componentVars]    
        savingsVars = [s + '_Savings_' + self.ga.inflatedTimespan for s in componentVars]    
        capGainsVars = [s + '_CapitalGains_' + self.ga.inflatedTimespan for s in componentVars]    

        allVars = [] + totalChangeVars + savingsVars  + capGainsVars
        for var in allVars:
            self.assertTrue(self.ga.dta[var].eq(0).all())
    

    def test_calcDetermineAssetLevelCapitalGains_RealEstate(self):

        data = self.createDummyData(includeMovingVars = True,  includeValueVars = True, includeChangeInValueVars = False)
        
        # Person 1
        data.loc[data[self.idVar] =='1', 'CostOfMajorHomeRenovations_' + self.ga.eyStr] = 15000
        data.loc[data[self.idVar] =='1', 'House_TotalChangeInMortgageDebt_WhenNotMoving_' + self.ga.inflatedTimespan] = -45
        data.loc[data[self.idVar] =='1', 'House_ValueIncrease_WhenNotMoving_'  + self.ga.inflatedTimespan] = 3422
        data.loc[data[self.idVar] =='1', 'House_ValueIncrease_WhenMoving_' + self.ga.inflatedTimespan] = 2

        data.loc[data[self.idVar] =='1', 'valueOfOtherRealEstate_Net_'+ self.ga.syStr] = 25000
        data.loc[data[self.idVar] =='1', 'valueOfOtherRealEstate_Net_'+ self.ga.eyStr] = 20000 # loss of 5k

        # Person 2
        data.loc[data[self.idVar] =='1', 'CostOfMajorHomeRenovations_' + self.ga.eyStr] = 15000
        data.loc[data[self.idVar] =='1', 'House_TotalChangeInMortgageDebt_WhenNotMoving_' + self.ga.inflatedTimespan] = -45
        data.loc[data[self.idVar] =='1', 'House_ValueIncrease_WhenNotMoving_'  + self.ga.inflatedTimespan] = 34220
        data.loc[data[self.idVar] =='1', 'House_ValueIncrease_WhenMoving_' + self.ga.inflatedTimespan] = 2

        # had 11k at start, bought 22k - no capital gains.
        data.loc[data[self.idVar] =='2', 'valueOfOtherRealEstate_Net_'+ self.ga.syStr] = 11000
        data.loc[data[self.idVar] =='2', 'valueOfOtherRealEstate_Net_'+ self.ga.eyStr] = 11000+22000 - 245
        data.loc[data[self.idVar] =='2', 'OtherRealEstate_SinceLastQYr_AmountBought_' + self.ga.eyStr] = 22000
        data.loc[data[self.idVar] =='2', 'OtherRealEstate_SinceLastQYr_AmountSold_' + self.ga.eyStr] = 245
        
        # Run it!
        self.ga.dta =  data
        self.ga.calcDetermineAssetLevelCapitalGains()        
        
        # Person 1
        self.assertTrue((15000+45+2) == self.ga.dta.loc[self.ga.dta[self.idVar] =='1', 'House_Savings_' + self.ga.inflatedTimespan].iloc[0])
        self.assertTrue((34220 - 15000) == self.ga.dta.loc[self.ga.dta[self.idVar] =='1', 'House_CapitalGains_' + self.ga.inflatedTimespan].iloc[0])
        self.assertTrue(-5000 == self.ga.dta.loc[self.ga.dta[self.idVar] =='1', 'OtherRealEstate_TotalChangeInWealth_' + self.ga.inflatedTimespan].iloc[0])
        self.assertTrue(0 == self.ga.dta.loc[self.ga.dta[self.idVar] =='1', 'OtherRealEstate_Savings_' + self.ga.inflatedTimespan].iloc[0])
        self.assertTrue(-5000 == self.ga.dta.loc[self.ga.dta[self.idVar] =='1', 'OtherRealEstate_CapitalGains_' + self.ga.inflatedTimespan].iloc[0])

        # Person 2
        self.assertTrue((22000 - 245) == self.ga.dta.loc[self.ga.dta[self.idVar] =='2', 'OtherRealEstate_TotalChangeInWealth_' + self.ga.inflatedTimespan].iloc[0])
        self.assertTrue((22000-245) == self.ga.dta.loc[self.ga.dta[self.idVar] =='2', 'OtherRealEstate_Savings_' + self.ga.inflatedTimespan].iloc[0])
        self.assertTrue(0 == self.ga.dta.loc[self.ga.dta[self.idVar] =='2', 'OtherRealEstate_CapitalGains_' + self.ga.inflatedTimespan].iloc[0])
        
    def test_calcDetermineAssetLevelCapitalGains_BizAndStock(self):

        data = self.createDummyData(includeMovingVars = True,  includeValueVars = True, includeChangeInValueVars = False)
        
        data.loc[data[self.idVar] =='1', 'valueOfBusiness_Net_'+ self.ga.syStr] = 25000
        data.loc[data[self.idVar] =='1', 'valueOfBusiness_Net_'+ self.ga.eyStr] = 20000 # loss of 5k

        data.loc[data[self.idVar] =='1', 'valueOfBrokerageStocks_Net_'+ self.ga.syStr] = 25000
        data.loc[data[self.idVar] =='1', 'valueOfBrokerageStocks_Net_'+ self.ga.eyStr] = 20000 # loss of 5k

        data.loc[data[self.idVar] =='2', 'valueOfBusiness_Net_'+ self.ga.syStr] = 11000
        data.loc[data[self.idVar] =='2', 'valueOfBusiness_Net_'+ self.ga.eyStr] = 11000+22000 - 245
        data.loc[data[self.idVar] =='2', 'Business_SinceLastQYr_AmountBought_' + self.ga.eyStr] = 22000
        data.loc[data[self.idVar] =='2', 'Business_SinceLastQYr_AmountSold_' + self.ga.eyStr] = 245

        data.loc[data[self.idVar] =='2', 'valueOfBrokerageStocks_Net_'+ self.ga.syStr] = 11000
        data.loc[data[self.idVar] =='2', 'valueOfBrokerageStocks_Net_'+ self.ga.eyStr] = 11000+22000 - 245
        data.loc[data[self.idVar] =='2', 'BrokerageStocks_SinceLastQYr_AmountBought_' + self.ga.eyStr] = 22000
        data.loc[data[self.idVar] =='2', 'BrokerageStocks_SinceLastQYr_AmountSold_' + self.ga.eyStr] = 245

        # Run it!
        self.ga.dta =  data
        self.ga.calcDetermineAssetLevelCapitalGains()        
        
        # Person 1
        self.assertTrue(0 == self.ga.dta.loc[self.ga.dta[self.idVar] =='1', 'Business_Savings_' + self.ga.inflatedTimespan].iloc[0])
        self.assertTrue(-5000 == self.ga.dta.loc[self.ga.dta[self.idVar] =='1', 'Business_CapitalGains_' + self.ga.inflatedTimespan].iloc[0])

        self.assertTrue(0 == self.ga.dta.loc[self.ga.dta[self.idVar] =='1', 'BrokerageStocks_Savings_' + self.ga.inflatedTimespan].iloc[0])
        self.assertTrue(-5000 == self.ga.dta.loc[self.ga.dta[self.idVar] =='1', 'BrokerageStocks_CapitalGains_' + self.ga.inflatedTimespan].iloc[0])

        # Person 2
        self.assertTrue((22000 - 245) == self.ga.dta.loc[self.ga.dta[self.idVar] =='2', 'Business_TotalChangeInWealth_' + self.ga.inflatedTimespan].iloc[0])
        self.assertTrue((22000-245) == self.ga.dta.loc[self.ga.dta[self.idVar] =='2', 'Business_Savings_' + self.ga.inflatedTimespan].iloc[0])
        self.assertTrue(0 == self.ga.dta.loc[self.ga.dta[self.idVar] =='2', 'Business_CapitalGains_' + self.ga.inflatedTimespan].iloc[0])

        self.assertTrue((22000 - 245) == self.ga.dta.loc[self.ga.dta[self.idVar] =='2', 'BrokerageStocks_TotalChangeInWealth_' + self.ga.inflatedTimespan].iloc[0])
        self.assertTrue((22000-245) == self.ga.dta.loc[self.ga.dta[self.idVar] =='2', 'BrokerageStocks_Savings_' + self.ga.inflatedTimespan].iloc[0])
        self.assertTrue(0 == self.ga.dta.loc[self.ga.dta[self.idVar] =='2', 'BrokerageStocks_CapitalGains_' + self.ga.inflatedTimespan].iloc[0])


    def test_calcDetermineAssetLevelCapitalGains_CheckingAndVehicle(self):

        data = self.createDummyData(includeMovingVars = True,  includeValueVars = True, includeChangeInValueVars = False)
        
        data.loc[data[self.idVar] =='1', 'valueOfVehicle_Net_'+ self.ga.syStr] = 25000
        data.loc[data[self.idVar] =='1', 'valueOfVehicle_Net_'+ self.ga.eyStr] = 15000 # loss of 10k

        data.loc[data[self.idVar] =='1', 'valueOfCheckingAndSavings_Net_'+ self.ga.syStr] = 25000
        data.loc[data[self.idVar] =='1', 'valueOfCheckingAndSavings_Net_'+ self.ga.eyStr] = 34000 # gain of 9k

        data.loc[data[self.idVar] =='2', 'valueOfVehicle_Net_'+ self.ga.syStr] = 11000
        data.loc[data[self.idVar] =='2', 'valueOfVehicle_Net_'+ self.ga.eyStr] = 16000 # bought a newer one - and added cash

        data.loc[data[self.idVar] =='2', 'valueOfCheckingAndSavings_Net_'+ self.ga.syStr] = 11000
        data.loc[data[self.idVar] =='2', 'valueOfCheckingAndSavings_Net_'+ self.ga.eyStr] = 5000 # loss of 6k

        # Run it!
        self.ga.dta =  data
        self.ga.calcDetermineAssetLevelCapitalGains()        
        
        # Person 1
        self.assertTrue(-10000 == self.ga.dta.loc[self.ga.dta[self.idVar] =='1', 'Vehicle_TotalChangeInWealth_' + self.ga.inflatedTimespan].iloc[0])
        self.assertTrue(-10000 == self.ga.dta.loc[self.ga.dta[self.idVar] =='1', 'Vehicle_Savings_' + self.ga.inflatedTimespan].iloc[0])
        self.assertTrue(0 == self.ga.dta.loc[self.ga.dta[self.idVar] =='1', 'Vehicle_CapitalGains_' + self.ga.inflatedTimespan].iloc[0])

        self.assertTrue(9000 == self.ga.dta.loc[self.ga.dta[self.idVar] =='1', 'CheckingAndSavings_TotalChangeInWealth_' + self.ga.inflatedTimespan].iloc[0])
        self.assertTrue(9000 == self.ga.dta.loc[self.ga.dta[self.idVar] =='1', 'CheckingAndSavings_Savings_' + self.ga.inflatedTimespan].iloc[0])
        self.assertTrue(0 == self.ga.dta.loc[self.ga.dta[self.idVar] =='1', 'CheckingAndSavings_CapitalGains_' + self.ga.inflatedTimespan].iloc[0])

        # Person 2
        self.assertTrue(5000 == self.ga.dta.loc[self.ga.dta[self.idVar] =='2', 'Vehicle_TotalChangeInWealth_' + self.ga.inflatedTimespan].iloc[0])
        self.assertTrue(5000 == self.ga.dta.loc[self.ga.dta[self.idVar] =='2', 'Vehicle_Savings_' + self.ga.inflatedTimespan].iloc[0])
        self.assertTrue(0 == self.ga.dta.loc[self.ga.dta[self.idVar] =='2', 'Vehicle_CapitalGains_' + self.ga.inflatedTimespan].iloc[0])

        self.assertTrue(-6000 == self.ga.dta.loc[self.ga.dta[self.idVar] =='2', 'CheckingAndSavings_TotalChangeInWealth_' + self.ga.inflatedTimespan].iloc[0])
        self.assertTrue(-6000 == self.ga.dta.loc[self.ga.dta[self.idVar] =='2', 'CheckingAndSavings_Savings_' + self.ga.inflatedTimespan].iloc[0])
        self.assertTrue(0 == self.ga.dta.loc[self.ga.dta[self.idVar] =='2', 'CheckingAndSavings_CapitalGains_' + self.ga.inflatedTimespan].iloc[0])

    
    def test_calcDetermineAssetLevelCapitalGains_OtherAssetsAndDebts_WithInflation(self):

        # # This test does NOT Mock inflation. it uses the real values.
        # self.patcher.stop()
        # self.ga.inflation = CPI_InflationReader.CPIInflationReader()

        data = self.createDummyData(includeMovingVars = True,  includeValueVars = True, includeChangeInValueVars = False)
        
        data.loc[data[self.idVar] =='1', 'valueOfOtherAssets_Net_'+ self.ga.syStr] = 25000
        data.loc[data[self.idVar] =='1', 'valueOfOtherAssets_Net_'+ self.ga.eyStr] = 15000 # loss of 10k  = less saving (after capital gains)

        data.loc[data[self.idVar] =='1', 'valueOfOtherDebts_Net_'+ self.ga.syStr] = 26000
        data.loc[data[self.idVar] =='1', 'valueOfOtherDebts_Net_'+ self.ga.eyStr] = 34000 # increase: more debt = less saving

        data.loc[data[self.idVar] =='2', 'valueOfOtherAssets_Net_'+ self.ga.syStr] = 11000
        data.loc[data[self.idVar] =='2', 'valueOfOtherAssets_Net_'+ self.ga.eyStr] = 16000 # increase of 5

        data.loc[data[self.idVar] =='2', 'valueOfOtherDebts_Net_'+ self.ga.syStr] = 12000
        data.loc[data[self.idVar] =='2', 'valueOfOtherDebts_Net_'+ self.ga.eyStr] = 5000 # decrease of 7k: less debt = more saving

        # Run it!
        self.ga.dta =  data
        self.ga.calcDetermineAssetLevelCapitalGains()        
        
        # Person 1
        interest = 25000 * (1.01**5) - 25000
        self.assertTrue(closeEnough(-10000, self.ga.dta.loc[self.ga.dta[self.idVar] =='1', 'OtherAssets_TotalChangeInWealth_' + self.ga.inflatedTimespan].iloc[0]))
        self.assertTrue(closeEnough(-10000-interest, self.ga.dta.loc[self.ga.dta[self.idVar] =='1', 'OtherAssets_Savings_' + self.ga.inflatedTimespan].iloc[0]))
        self.assertTrue(closeEnough(interest, self.ga.dta.loc[self.ga.dta[self.idVar] =='1', 'OtherAssets_CapitalGains_' + self.ga.inflatedTimespan].iloc[0]))

        interest = 0 # -(26000 * .15884) #5 year inflation
        self.assertTrue(closeEnough(-8000 , self.ga.dta.loc[self.ga.dta[self.idVar] =='1', 'OtherDebts_TotalChangeInWealth_' + self.ga.inflatedTimespan].iloc[0]))
        self.assertTrue(closeEnough(-8000-interest , self.ga.dta.loc[self.ga.dta[self.idVar] =='1', 'OtherDebts_Savings_' + self.ga.inflatedTimespan].iloc[0]))
        self.assertTrue(closeEnough(interest , self.ga.dta.loc[self.ga.dta[self.idVar] =='1', 'OtherDebts_CapitalGains_' + self.ga.inflatedTimespan].iloc[0]))

        # Person 2
        interest = 11000 * (1.01**5) - 11000
        self.assertTrue(closeEnough(5000 , self.ga.dta.loc[self.ga.dta[self.idVar] =='2', 'OtherAssets_TotalChangeInWealth_' + self.ga.inflatedTimespan].iloc[0]))
        self.assertTrue(closeEnough(5000-interest , self.ga.dta.loc[self.ga.dta[self.idVar] =='2', 'OtherAssets_Savings_' + self.ga.inflatedTimespan].iloc[0]))
        self.assertTrue(closeEnough(interest , self.ga.dta.loc[self.ga.dta[self.idVar] =='2', 'OtherAssets_CapitalGains_' + self.ga.inflatedTimespan].iloc[0]))

        interest = 0 # -(12000 * .15884) #5 year inflation
        self.assertTrue(closeEnough(7000 , self.ga.dta.loc[self.ga.dta[self.idVar] =='2', 'OtherDebts_TotalChangeInWealth_' + self.ga.inflatedTimespan].iloc[0]))
        self.assertTrue(closeEnough(7000-interest , self.ga.dta.loc[self.ga.dta[self.idVar] =='2', 'OtherDebts_Savings_' + self.ga.inflatedTimespan].iloc[0]))
        self.assertTrue(closeEnough(interest, self.ga.dta.loc[self.ga.dta[self.idVar] =='2', 'OtherDebts_CapitalGains_' + self.ga.inflatedTimespan].iloc[0]))


    def test_calcSavingsRate_ActiveSavings_AllZero(self):

        data = self.createDummyData(includeMovingVars = True,  includeValueVars = False, includeChangeInValueVars = True)
        self.ga.dta =  data
        self.ga.calcSavingsRate_ActiveSavings(debugAndReport = False)

        allVars = ['Total_ChangeInWealth_'  + self.ga.inflatedTimespan,'Total_CapitalGains_'  + self.ga.inflatedTimespan,'Total_GrossSavings_'  + self.ga.inflatedTimespan, 
                'netMoveIn_' + self.ga.inflatedTimespan, 'netMoveOut_' + self.ga.inflatedTimespan, 'netIRAandAnnuityChange_' + self.ga.inflatedTimespan,
                'Total_NetActiveSavings_'  + self.ga.inflatedTimespan, 'activeSavingsRate_PerPerson_' + self.ga.inflatedTimespan]

        for var in allVars:
            self.assertTrue(self.ga.dta[var].eq(0).all())

    def test_calcSavingsRate_ActiveSavings_GrossSavingsAndGains(self):


        data = self.createDummyData(includeMovingVars = True,  includeValueVars = False, includeChangeInValueVars = True)
        
        # componentVars = ['House', 'OtherRealEstate', 'Business', 'BrokerageStocks', 'CheckingAndSavings', 'Vehicle', 'OtherAssets', 'OtherDebts']

        data.loc[data[self.idVar] =='1', 'House_CapitalGains_'+ self.ga.inflatedTimespan] = 25000
        data.loc[data[self.idVar] =='1', 'OtherRealEstate_CapitalGains_'+ self.ga.inflatedTimespan] = 24500
        data.loc[data[self.idVar] =='1', 'OtherDebts_CapitalGains_'+ self.ga.inflatedTimespan] = -402
        data.loc[data[self.idVar] =='1', 'BrokerageStocks_CapitalGains_'+ self.ga.inflatedTimespan] = 25000
        data.loc[data[self.idVar] =='1', 'Vehicle_CapitalGains_'+ self.ga.inflatedTimespan] = 1
        data.loc[data[self.idVar] =='1', 'OtherAssets_CapitalGains_'+ self.ga.inflatedTimespan] = 56

        data.loc[data[self.idVar] =='1', 'Business_Savings_'+ self.ga.inflatedTimespan] = 25000
        data.loc[data[self.idVar] =='1', 'House_Savings_'+ self.ga.inflatedTimespan] = 10000
        data.loc[data[self.idVar] =='1', 'BrokerageStocks_Savings_'+ self.ga.inflatedTimespan] = 100
        data.loc[data[self.idVar] =='1', 'CheckingAndSavings_Savings_'+ self.ga.inflatedTimespan] = -100
        data.loc[data[self.idVar] =='1', 'Vehicle_Savings_'+ self.ga.inflatedTimespan] = -4550

        data.loc[data[self.idVar] =='2', 'Business_CapitalGains_'+ self.ga.inflatedTimespan] = -1000
        data.loc[data[self.idVar] =='2', 'CheckingAndSavings_CapitalGains_'+ self.ga.inflatedTimespan] = 0
        data.loc[data[self.idVar] =='2', 'OtherAssets_CapitalGains_'+ self.ga.inflatedTimespan] = -110

        data.loc[data[self.idVar] =='2', 'OtherDebts_Savings_'+ self.ga.inflatedTimespan] = 2000
        data.loc[data[self.idVar] =='2', 'Business_Savings_'+ self.ga.inflatedTimespan] = 3005
        data.loc[data[self.idVar] =='2', 'OtherAssets_Savings_'+ self.ga.inflatedTimespan] = 180

        data.loc[data[self.idVar] =='1', 'PersonMovedOut_SinceLastQYr_DebtsMovedOut_' + self.ga.eyStr] = 10
        data.loc[data[self.idVar] =='1', 'largeGift_All_AmountHH_' + self.ga.eyStr] = 15000
        
        data.loc[data[self.idVar] =='2', 'PersonMovedIn_SinceLastQYr_AssetsMovedIn_'   + self.ga.eyStr] = 150
        data.loc[data[self.idVar] =='2', 'PersonMovedIn_SinceLastQYr_DebtsMovedIn_' + self.ga.eyStr] = 10

        data.loc[data[self.idVar] =='2', 'PrivateRetirePlan_SinceLastQYr_AmountMovedIn_'+ self.ga.eyStr] = 135.5

        self.ga.dta =  data
        self.ga.calcSavingsRate_ActiveSavings(debugAndReport = False)

        # Check capital Gains
        self.assertTrue(closeEnough(25000 + 24500-402 + 25000 + 1 + 56, self.ga.dta.loc[self.ga.dta[self.idVar] =='1', 'Total_CapitalGains_' + self.ga.inflatedTimespan].iloc[0]))
        self.assertTrue(closeEnough(-1000-110, self.ga.dta.loc[self.ga.dta[self.idVar] =='2', 'Total_CapitalGains_' + self.ga.inflatedTimespan].iloc[0]))

        # Check Gross savings
        savings1 = 25000 + 10000 + 100 -100 -4550
        self.assertTrue(closeEnough(savings1, self.ga.dta.loc[self.ga.dta[self.idVar] =='1', 'Total_GrossSavings_' + self.ga.inflatedTimespan].iloc[0]))
        savings2 = 2000 + 3005 + 180
        self.assertTrue(closeEnough(savings2, self.ga.dta.loc[self.ga.dta[self.idVar] =='2', 'Total_GrossSavings_' + self.ga.inflatedTimespan].iloc[0]))

        # Check Active Savings
        self.assertTrue(closeEnough(savings1 - 10 - 15000, self.ga.dta.loc[self.ga.dta[self.idVar] =='1', 'Total_NetActiveSavings_' + self.ga.inflatedTimespan].iloc[0]))
        self.assertTrue(closeEnough(savings2 - 150 + 10 + 135.5, self.ga.dta.loc[self.ga.dta[self.idVar] =='2', 'Total_NetActiveSavings_' + self.ga.inflatedTimespan].iloc[0]))


        # self.dta['Total_NetActiveSavings_'  + self.inflatedTimespan]= self.dta['Total_GrossSavings_' + self.inflatedTimespan].sub(self.dta['largeGift_All_AmountHH_' + self.eyStr], fill_value=0).add(self.dta['netMoveOut_' + self.inflatedTimespan], fill_value=0).sub(self.dta['netMoveIn_' + self.inflatedTimespan], fill_value=0).sub(self.dta['netIRAandAnnuityChange_' + self.inflatedTimespan], fill_value=0)
        # self.dta['activeSavingsRate_PerPerson_' + self.inflatedTimespan] = (self.dta['Total_NetActiveSavings_'  + self.inflatedTimespan] / self.duration)
        # Its difficult to tell which income var Gittleman used, but it appears to be the Nominal, PreTax Income
        # sself.dta['activeSavingsRate_PerPerson_' + self.inflatedTimespan] = (self.dta['activeSavingsRate_PerPerson_' + self.inflatedTimespan].div(self.dta['averageNominalIncome_AllYears_' + self.inflatedTimespan], fill_value=0)) 



    def test_createSegmentBins(self):
        data = self.createDummyData(includeMovingVars = False, includeValueVars = False, includeChangeInValueVars = False)
        self.ga.dta =  data
        self.ga.createSegmentBins()


    if __name__ == '__main__':
        unittest.main()

