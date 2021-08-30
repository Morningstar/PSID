import SavingsRates.CalcSavingsRates as CalcSavingsRates
import unittest
import math
import pandas as pd
import numpy.testing as npt
import Inflation.CPI_InflationReader as CPI_InflationReader
from mock import patch, MagicMock
from pandas.testing import assert_frame_equal, assert_series_equal
# import importlib
# importlib.reload(rlc)

LOCATION_OF_OUTPUT_DATA = "C:/Dev/src/MorningstarGithub/PSID/outputData/"

"""Tests for Morningstar's Savings Analysis Functions"""

def closeEnough(a, b):
    try:
         npt.assert_approx_equal(a, b, 5, err_msg='', verbose= False)
         return True
    except:
        return False


class CalcSavingsRates_Test(unittest.TestCase):

    def setUp(self):

        self.patcher = patch('Inflation.CPI_InflationReader.CPIInflationReader')
        self.addCleanup(self.patcher.stop)
        self.inflationMocker = self.patcher.start()
        self.inflationMocker().getInflationFactorBetweenTwoYears.return_value = 1

        self.csr = CalcSavingsRates.CalcSavingsRates(baseDir=LOCATION_OF_OUTPUT_DATA,
                                                      familyInputSubDir="B",
                                                      inputBaseName="D",
                                                      outputBaseName="E",
                                                      outputSubDir="F")

        self.assertTrue(self.csr.inflator.getInflationFactorBetweenTwoYears(1954, 1989) == 1)

        self.csr.clearData()
        self.csr.setPeriod(1989, 1994, 1998)
        self.csr.yearsWithFamilyData = [self.csr.startYear, self.csr.endYear]

        self.idVar = 'familyId_' + self.csr.syStr

    def createDummyData(self, includeMovingVars = False, includeValueVars = False, includeChangeInValueVars = False):

        # Start with a simple DF -- two families
        testData = pd.DataFrame({
                'familyId_' + self.csr.syStr :['1','2'], 
                'raceR_' + self.csr.syStr :['White', 'Black'], 
                'ageR_' + self.csr.syStr :[44, 44], 
                'averageRealBeforeTaxIncome_AllYears_' + self.csr.inflatedTimespan : [10000, 70000],
                'averageRealAfterTaxIncome_AllYears_' + self.csr.inflatedTimespan : [10000, 70000],
                'averageNominalIncome_AllYears_' + self.csr.timespan : [8000, 60000],
                'educationYearsR_' + self.csr.syStr : [14, 14],
                'martialStatusR_' + self.csr.syStr: ['Married', 'Married'],
                'LongitudinalWeightHH_' + self.csr.syStr:[1,1],
                'complexWeight_' + self.csr.syStr:[10,20],
                'cleaningStatus_' + self.csr.eyStr : ['Keep', 'Keep']},
            columns=['familyId_' + self.csr.syStr, 'raceR_' + self.csr.syStr,
                     'ageR_' + self.csr.syStr, 'averageRealBeforeTaxIncome_AllYears_' + self.csr.inflatedTimespan, 'averageRealAfterTaxIncome_AllYears_' + self.csr.inflatedTimespan, 'averageNominalIncome_AllYears_' + self.csr.timespan,
                     'educationYearsR_' + self.csr.syStr, 'martialStatusR_' + self.csr.syStr, 
                     'LongitudinalWeightHH_' + self.csr.syStr, 'complexWeight' + self.csr.syStr, 'cleaningStatus_' + self.csr.eyStr
                     ])

        if includeMovingVars:
            testData['ChangeInHeadFU_' + self.csr.timespan] = False
            testData['House_ValueIncrease_WhenMoving_' + self.csr.inflatedTimespan] = 0
            testData['House_ValueIncrease_WhenNotMoving_' + self.csr.inflatedTimespan] = 0
            testData['House_TotalChangeInMortgageDebt_WhenNotMoving_' + self.csr.inflatedTimespan] = 0
            testData['House_TotalChangeInMortgageDebt_WhenMoving_' + self.csr.inflatedTimespan] = 0
            testData['CostOfMajorHomeRenovations_' + self.csr.syStr] = 0
            testData['CostOfMajorHomeRenovations_' + self.csr.eyStr] = 0
        else:
            testData['valueOfHouse_Gross_' + self.csr.syStr] = 0  # Gross or net?
            testData['valueOfHouse_Gross_' + self.csr.eyStr] = 0
            testData['valueOfHouse_Gross_' + str(self.csr.endYear - self.csr.timeStep)] = 0
            testData['valueOfHouse_Debt_' + self.csr.eyStr] = 0
            testData['valueOfHouse_Debt_' + self.csr.eyStr] = 0
            testData['valueOfHouse_Debt_' + str(self.csr.endYear - self.csr.timeStep)] = 0
            testData['ChangeInCompositionFU_' + self.csr.syStr] = 0
            testData['ChangeInCompositionFU_' + self.csr.eyStr] = 0
            testData['MovedR_' + self.csr.syStr] = False
            testData['MovedR_' + str(self.csr.endYear - self.csr.timeStep)] = False
            testData['MovedR_' + self.csr.eyStr] = False

        if includeValueVars:
            ''' Vars used to saving versus capital gains'''
            componentVars = ['House_Gross', 'House_Debt', 'House_Net',
                             'OtherRealEstate_Net', 'Business_Net',
                             'BrokerageStocks_Net', 'CheckingAndSavings_Net',
                             'Vehicle_Net', 'OtherAssets_Net',
                             'AllOtherDebts_Net',
                             'PrivateRetirePlan_Gross', 'EmployerRetirePlan_Gross']
            valueVars_Start = ['valueOf' + s + "_" + self.csr.syStr for s in componentVars]    
            valueVars_End = ['valueOf' + s + "_" + self.csr.eyStr for s in componentVars]    
            boughtVars_End = ['PrivateRetirePlan_SinceLastQYr_AmountMovedIn_' + self.csr.eyStr] + [s + '_SinceLastQYr_AmountBought_' + self.csr.eyStr for s in ['OtherRealEstate', 'Business', 'BrokerageStocks']]
            soldVars_End = ['PrivateRetirePlan_SinceLastQYr_AmountMovedOut_' + self.csr.eyStr] + [s + '_SinceLastQYr_AmountSold_' + self.csr.eyStr for s in ['OtherRealEstate', 'Business', 'BrokerageStocks']]
            floatVars = [] + valueVars_Start + valueVars_End  + boughtVars_End + soldVars_End
            for var in floatVars:
                testData[var] = 0

            assetTypes = ['House', 'OtherRealEstate', 'Business', 'BrokerageStocks', 'CheckingAndSavings',
                             'Vehicle', 'OtherAssets', 'AllOtherDebts', 'PrivateRetirePlan', 'EmployerRetirePlan']
            hasVars_Start = ['has' + s + "_" + self.csr.syStr for s in assetTypes]
            hasVars_End = ['has' + s + "_" + self.csr.eyStr for s in assetTypes]
            boolVars = [] + hasVars_Start + hasVars_End
            for var in boolVars:
                testData[var] = True

    
        if includeChangeInValueVars:
            ''' Vars as inputs to Analyze Savings Rate'''
            # Each of the following entries should have a varaible _TotalChangeInWealth, _CapitalGains and _Savings
            componentVarsNoGrossOrNet = ['House', 'OtherRealEstate', 'Business',
                                         'BrokerageStocks', 'CheckingAndSavings',
                                         'Vehicle', 'OtherAssets', 'AllOtherDebts',
                                         'PrivateRetirePlan', 'EmployerRetirePlan']
            totalChangeVars = [s + "_TotalChangeInWealth_" + self.csr.inflatedTimespan for s in componentVarsNoGrossOrNet]
            capitalGainsVars = [s + "_CapitalGains_" + self.csr.inflatedTimespan for s in componentVarsNoGrossOrNet]
            grossSavingsVars = [s + "_Savings_" + self.csr.inflatedTimespan for s in componentVarsNoGrossOrNet]
            openCloseTransferVars = [s + "_OpenCloseTransfers_" + self.csr.inflatedTimespan for s in componentVarsNoGrossOrNet]

            allVars = [] + totalChangeVars + capitalGainsVars + grossSavingsVars + openCloseTransferVars + \
                    ['PersonMovedIn_SinceLastQYr_AssetsMovedIn_'   + self.csr.eyStr, 
                     'PersonMovedIn_SinceLastQYr_DebtsMovedIn_' + self.csr.eyStr, 
                     'PersonMovedOut_SinceLastQYr_AssetsMovedOut_' + self.csr.eyStr,
                     'PersonMovedOut_SinceLastQYr_DebtsMovedOut_' + self.csr.eyStr,
                     'PrivateRetirePlan_SinceLastQYr_AmountMovedIn_' + self.csr.eyStr,
                     'PrivateRetirePlan_SinceLastQYr_AmountMovedOut_' + self.csr.eyStr,
                     'largeGift_All_AmountHH_' + self.csr.eyStr,
                     'SmallGift_All_AmountHH_' + self.csr.eyStr,
                    ]
                  
            for var in allVars:
                testData[var] = 0
                
        return testData

    def test_calcDetermineAssetLevelCapitalGains_AllZero(self):

        data = self.createDummyData(includeMovingVars = True,  includeValueVars = True, includeChangeInValueVars = False)
        self.csr.dta =  data
        self.csr.calcDetermineAssetLevelCapitalGains_SimpliedSWStyle()

        componentVars = ['House', 'OtherRealEstate', 'Business', 'BrokerageStocks', 'CheckingAndSavings', 'Vehicle', 'OtherAssets', 'AllOtherDebts']
        totalChangeVars = [s + '_TotalChangeInWealth_' + self.csr.inflatedTimespan for s in componentVars]
        savingsVars = [s + '_Savings_' + self.csr.inflatedTimespan for s in componentVars]    
        capGainsVars = [s + '_CapitalGains_' + self.csr.inflatedTimespan for s in componentVars]    

        allVars = [] + totalChangeVars + savingsVars  + capGainsVars
        for var in allVars:
            if not (self.csr.dta[var].eq(0).all()):
                print("problem with" + var)
            self.assertTrue(self.csr.dta[var].eq(0).all())


    def test_calcDetermineAssetLevelCapitalGains_NAs(self):
        data = self.createDummyData(includeMovingVars = True,  includeValueVars = True, includeChangeInValueVars = False)
        data.loc[data[self.idVar] =='1', 'valueOfBrokerageStocks_Net_'+ self.csr.eyStr] = None
        data.loc[data[self.idVar] =='2', 'valueOfCheckingAndSavings_Net_'+ self.csr.syStr] = None

        self.csr.dta =  data
        self.csr.calcDetermineAssetLevelCapitalGains_SimpliedSWStyle()

        ''' TODO :: Update to Check Status Field 
        self.assertTrue(self.csr.dta.loc[self.csr.dta[self.idVar] =='1', 'BrokerageStocks' + '_WarningNoStock_' + self.csr.inflatedTimespan].iloc[0])

        self.assertTrue(math.isnan(self.csr.dta.loc[self.csr.dta[self.idVar] =='2',
                   "BrokerageStocks" + '_WarningNoStock_' + self.csr.inflatedTimespan].iloc[0]))
        '''

        # Incomplete -- need to update with new account fill-in logic
        self.assertTrue(math.isnan(self.csr.dta.loc[self.csr.dta[self.idVar] =='1',
                   "BrokerageStocks" + '_TotalChangeInWealth_' + self.csr.inflatedTimespan].iloc[0]))

        self.assertTrue(math.isnan(self.csr.dta.loc[self.csr.dta[self.idVar] =='1',
                   "BrokerageStocks" + '_CapitalGains_' + self.csr.inflatedTimespan].iloc[0]))

        self.assertTrue(0 == self.csr.dta.loc[self.csr.dta[self.idVar] =='1',
                   "BrokerageStocks" + '_Savings_' + self.csr.inflatedTimespan].iloc[0])

        self.assertTrue(0 == self.csr.dta.loc[self.csr.dta[self.idVar] =='1',
                   "BrokerageStocks" + '_Savings_' + self.csr.inflatedTimespan].iloc[0])

        self.assertTrue(math.isnan(self.csr.dta.loc[self.csr.dta[self.idVar] =='2',
                   "CheckingAndSavings" + '_TotalChangeInWealth_' + self.csr.inflatedTimespan].iloc[0]))

        self.assertTrue(math.isnan(self.csr.dta.loc[self.csr.dta[self.idVar] =='2',
                   "CheckingAndSavings" + '_Savings_' + self.csr.inflatedTimespan].iloc[0]))

        self.assertTrue(math.isnan(self.csr.dta.loc[self.csr.dta[self.idVar] =='2',
                   "CheckingAndSavings" + '_CapitalGains_' + self.csr.inflatedTimespan].iloc[0]))

    def test_calcDetermineAssetLevelCapitalGains_RealEstate(self):

        data = self.createDummyData(includeMovingVars = True,  includeValueVars = True, includeChangeInValueVars = False)
        
        # Person 1
        data.loc[data[self.idVar] =='1', 'CostOfMajorHomeRenovations_' + self.csr.eyStr] = 15000
        data.loc[data[self.idVar] =='1', 'House_TotalChangeInMortgageDebt_WhenNotMoving_' + self.csr.inflatedTimespan] = -45
        data.loc[data[self.idVar] =='1', 'House_ValueIncrease_WhenNotMoving_'  + self.csr.inflatedTimespan] = 3422
        data.loc[data[self.idVar] =='1', 'House_ValueIncrease_WhenMoving_' + self.csr.inflatedTimespan] = 2

        data.loc[data[self.idVar] =='1', 'valueOfOtherRealEstate_Net_'+ self.csr.syStr] = 25000
        data.loc[data[self.idVar] =='1', 'valueOfOtherRealEstate_Net_'+ self.csr.eyStr] = 20000 # loss of 5k

        # Person 2
        data.loc[data[self.idVar] =='1', 'CostOfMajorHomeRenovations_' + self.csr.eyStr] = 15000
        data.loc[data[self.idVar] =='1', 'House_TotalChangeInMortgageDebt_WhenNotMoving_' + self.csr.inflatedTimespan] = -45
        data.loc[data[self.idVar] =='1', 'House_ValueIncrease_WhenNotMoving_'  + self.csr.inflatedTimespan] = 34220
        data.loc[data[self.idVar] =='1', 'House_ValueIncrease_WhenMoving_' + self.csr.inflatedTimespan] = 2

        # had 11k at start, bought 22k - no capital gains.
        data.loc[data[self.idVar] =='2', 'valueOfOtherRealEstate_Net_'+ self.csr.syStr] = 11000
        data.loc[data[self.idVar] =='2', 'valueOfOtherRealEstate_Net_'+ self.csr.eyStr] = 11000+22000 - 245
        data.loc[data[self.idVar] =='2', 'OtherRealEstate_SinceLastQYr_AmountBought_' + self.csr.eyStr] = 22000
        data.loc[data[self.idVar] =='2', 'OtherRealEstate_SinceLastQYr_AmountSold_' + self.csr.eyStr] = 245
        
        # Run it!
        self.csr.dta =  data
        self.csr.calcDetermineAssetLevelCapitalGains_SimpliedSWStyle()
        
        # Person 1
        self.assertTrue((15000+45+2) == self.csr.dta.loc[self.csr.dta[self.idVar] =='1', 'House_Savings_' + self.csr.inflatedTimespan].iloc[0])
        self.assertTrue((34220 - 15000) == self.csr.dta.loc[self.csr.dta[self.idVar] =='1', 'House_CapitalGains_' + self.csr.inflatedTimespan].iloc[0])
        self.assertTrue(-5000 == self.csr.dta.loc[self.csr.dta[self.idVar] =='1', 'OtherRealEstate_TotalChangeInWealth_' + self.csr.inflatedTimespan].iloc[0])
        self.assertTrue(0 == self.csr.dta.loc[self.csr.dta[self.idVar] =='1', 'OtherRealEstate_Savings_' + self.csr.inflatedTimespan].iloc[0])
        self.assertTrue(-5000 == self.csr.dta.loc[self.csr.dta[self.idVar] =='1', 'OtherRealEstate_CapitalGains_' + self.csr.inflatedTimespan].iloc[0])

        # Person 2
        self.assertTrue((22000 - 245) == self.csr.dta.loc[self.csr.dta[self.idVar] =='2', 'OtherRealEstate_TotalChangeInWealth_' + self.csr.inflatedTimespan].iloc[0])
        self.assertTrue((22000-245) == self.csr.dta.loc[self.csr.dta[self.idVar] =='2', 'OtherRealEstate_Savings_' + self.csr.inflatedTimespan].iloc[0])
        self.assertTrue(0 == self.csr.dta.loc[self.csr.dta[self.idVar] =='2', 'OtherRealEstate_CapitalGains_' + self.csr.inflatedTimespan].iloc[0])
        
    def test_calcDetermineAssetLevelCapitalGains_BizAndStock(self):

        data = self.createDummyData(includeMovingVars = True,  includeValueVars = True, includeChangeInValueVars = False)
        
        data.loc[data[self.idVar] =='1', 'valueOfBusiness_Net_'+ self.csr.syStr] = 25000
        data.loc[data[self.idVar] =='1', 'valueOfBusiness_Net_'+ self.csr.eyStr] = 20000 # loss of 5k

        data.loc[data[self.idVar] =='1', 'valueOfBrokerageStocks_Net_'+ self.csr.syStr] = 25000
        data.loc[data[self.idVar] =='1', 'valueOfBrokerageStocks_Net_'+ self.csr.eyStr] = 20000 # loss of 5k

        data.loc[data[self.idVar] =='2', 'valueOfBusiness_Net_'+ self.csr.syStr] = 11000
        data.loc[data[self.idVar] =='2', 'valueOfBusiness_Net_'+ self.csr.eyStr] = 11000+22000 - 245
        data.loc[data[self.idVar] =='2', 'Business_SinceLastQYr_AmountBought_' + self.csr.eyStr] = 22000
        data.loc[data[self.idVar] =='2', 'Business_SinceLastQYr_AmountSold_' + self.csr.eyStr] = 245

        data.loc[data[self.idVar] =='2', 'valueOfBrokerageStocks_Net_'+ self.csr.syStr] = 11000
        data.loc[data[self.idVar] =='2', 'valueOfBrokerageStocks_Net_'+ self.csr.eyStr] = 11000+22000 - 245
        data.loc[data[self.idVar] =='2', 'BrokerageStocks_SinceLastQYr_AmountBought_' + self.csr.eyStr] = 22000
        data.loc[data[self.idVar] =='2', 'BrokerageStocks_SinceLastQYr_AmountSold_' + self.csr.eyStr] = 245

        # Run it!
        self.csr.dta =  data
        self.csr.calcDetermineAssetLevelCapitalGains_SimpliedSWStyle()
        
        # Person 1
        self.assertTrue(0 == self.csr.dta.loc[self.csr.dta[self.idVar] =='1', 'Business_Savings_' + self.csr.inflatedTimespan].iloc[0])
        self.assertTrue(-5000 == self.csr.dta.loc[self.csr.dta[self.idVar] =='1', 'Business_CapitalGains_' + self.csr.inflatedTimespan].iloc[0])

        self.assertTrue(0 == self.csr.dta.loc[self.csr.dta[self.idVar] =='1', 'BrokerageStocks_Savings_' + self.csr.inflatedTimespan].iloc[0])
        self.assertTrue(-5000 == self.csr.dta.loc[self.csr.dta[self.idVar] =='1', 'BrokerageStocks_CapitalGains_' + self.csr.inflatedTimespan].iloc[0])

        # Person 2
        self.assertTrue((22000 - 245) == self.csr.dta.loc[self.csr.dta[self.idVar] =='2', 'Business_TotalChangeInWealth_' + self.csr.inflatedTimespan].iloc[0])
        self.assertTrue((22000-245) == self.csr.dta.loc[self.csr.dta[self.idVar] =='2', 'Business_Savings_' + self.csr.inflatedTimespan].iloc[0])
        self.assertTrue(0 == self.csr.dta.loc[self.csr.dta[self.idVar] =='2', 'Business_CapitalGains_' + self.csr.inflatedTimespan].iloc[0])

        self.assertTrue((22000 - 245) == self.csr.dta.loc[self.csr.dta[self.idVar] =='2', 'BrokerageStocks_TotalChangeInWealth_' + self.csr.inflatedTimespan].iloc[0])
        self.assertTrue((22000-245) == self.csr.dta.loc[self.csr.dta[self.idVar] =='2', 'BrokerageStocks_Savings_' + self.csr.inflatedTimespan].iloc[0])
        self.assertTrue(0 == self.csr.dta.loc[self.csr.dta[self.idVar] =='2', 'BrokerageStocks_CapitalGains_' + self.csr.inflatedTimespan].iloc[0])


    def test_calcDetermineAssetLevelCapitalGains_CheckingAndVehicle(self):

        data = self.createDummyData(includeMovingVars = True,  includeValueVars = True, includeChangeInValueVars = False)
        
        data.loc[data[self.idVar] =='1', 'valueOfVehicle_Net_'+ self.csr.syStr] = 25000
        data.loc[data[self.idVar] =='1', 'valueOfVehicle_Net_'+ self.csr.eyStr] = 15000 # loss of 10k

        data.loc[data[self.idVar] =='1', 'valueOfCheckingAndSavings_Net_'+ self.csr.syStr] = 25000
        data.loc[data[self.idVar] =='1', 'valueOfCheckingAndSavings_Net_'+ self.csr.eyStr] = 34000 # gain of 9k

        data.loc[data[self.idVar] =='2', 'valueOfVehicle_Net_'+ self.csr.syStr] = 11000
        data.loc[data[self.idVar] =='2', 'valueOfVehicle_Net_'+ self.csr.eyStr] = 16000 # bought a newer one - and added cash

        data.loc[data[self.idVar] =='2', 'valueOfCheckingAndSavings_Net_'+ self.csr.syStr] = 11000
        data.loc[data[self.idVar] =='2', 'valueOfCheckingAndSavings_Net_'+ self.csr.eyStr] = 5000 # loss of 6k

        # Run it!
        self.csr.dta =  data
        self.csr.calcDetermineAssetLevelCapitalGains_SimpliedSWStyle()
        
        # Person 1
        self.assertTrue(-10000 == self.csr.dta.loc[self.csr.dta[self.idVar] =='1', 'Vehicle_TotalChangeInWealth_' + self.csr.inflatedTimespan].iloc[0])
        self.assertTrue(-10000 == self.csr.dta.loc[self.csr.dta[self.idVar] =='1', 'Vehicle_Savings_' + self.csr.inflatedTimespan].iloc[0])
        self.assertTrue(0 == self.csr.dta.loc[self.csr.dta[self.idVar] =='1', 'Vehicle_CapitalGains_' + self.csr.inflatedTimespan].iloc[0])

        self.assertTrue(9000 == self.csr.dta.loc[self.csr.dta[self.idVar] =='1', 'CheckingAndSavings_TotalChangeInWealth_' + self.csr.inflatedTimespan].iloc[0])
        self.assertTrue(9000 == self.csr.dta.loc[self.csr.dta[self.idVar] =='1', 'CheckingAndSavings_Savings_' + self.csr.inflatedTimespan].iloc[0])
        self.assertTrue(0 == self.csr.dta.loc[self.csr.dta[self.idVar] =='1', 'CheckingAndSavings_CapitalGains_' + self.csr.inflatedTimespan].iloc[0])

        # Person 2
        self.assertTrue(5000 == self.csr.dta.loc[self.csr.dta[self.idVar] =='2', 'Vehicle_TotalChangeInWealth_' + self.csr.inflatedTimespan].iloc[0])
        self.assertTrue(5000 == self.csr.dta.loc[self.csr.dta[self.idVar] =='2', 'Vehicle_Savings_' + self.csr.inflatedTimespan].iloc[0])
        self.assertTrue(0 == self.csr.dta.loc[self.csr.dta[self.idVar] =='2', 'Vehicle_CapitalGains_' + self.csr.inflatedTimespan].iloc[0])

        self.assertTrue(-6000 == self.csr.dta.loc[self.csr.dta[self.idVar] =='2', 'CheckingAndSavings_TotalChangeInWealth_' + self.csr.inflatedTimespan].iloc[0])
        self.assertTrue(-6000 == self.csr.dta.loc[self.csr.dta[self.idVar] =='2', 'CheckingAndSavings_Savings_' + self.csr.inflatedTimespan].iloc[0])
        self.assertTrue(0 == self.csr.dta.loc[self.csr.dta[self.idVar] =='2', 'CheckingAndSavings_CapitalGains_' + self.csr.inflatedTimespan].iloc[0])

    
    def test_calcDetermineAssetLevelCapitalGains_OtherAssetsAndDebts_WithInflation(self):

        # # This test does NOT Mock inflation. it uses the real values.
        # self.patcher.stop()
        # self.csr.inflation = CPI_InflationReader.CPIInflationReader()

        data = self.createDummyData(includeMovingVars = True,  includeValueVars = True, includeChangeInValueVars = False)
        
        data.loc[data[self.idVar] =='1', 'valueOfOtherAssets_Net_'+ self.csr.syStr] = 25000
        data.loc[data[self.idVar] =='1', 'valueOfOtherAssets_Net_'+ self.csr.eyStr] = 15000 # loss of 10k  = less saving (after capital gains)

        data.loc[data[self.idVar] =='1', 'valueOfAllOtherDebts_Net_'+ self.csr.syStr] = 26000
        data.loc[data[self.idVar] =='1', 'valueOfAllOtherDebts_Net_'+ self.csr.eyStr] = 34000 # increase: more debt = less saving

        data.loc[data[self.idVar] =='2', 'valueOfOtherAssets_Net_'+ self.csr.syStr] = 11000
        data.loc[data[self.idVar] =='2', 'valueOfOtherAssets_Net_'+ self.csr.eyStr] = 16000 # increase of 5

        data.loc[data[self.idVar] =='2', 'valueOfAllOtherDebts_Net_'+ self.csr.syStr] = 12000
        data.loc[data[self.idVar] =='2', 'valueOfAllOtherDebts_Net_'+ self.csr.eyStr] = 5000 # decrease of 7k: less debt = more saving

        # Run it!
        self.csr.dta =  data
        self.csr.calcDetermineAssetLevelCapitalGains_SimpliedSWStyle()
        
        # Person 1
        interest = 25000 * (1.01**5) - 25000
        self.assertTrue(closeEnough(-10000, self.csr.dta.loc[self.csr.dta[self.idVar] =='1', 'OtherAssets_TotalChangeInWealth_' + self.csr.inflatedTimespan].iloc[0]))
        self.assertTrue(closeEnough(-10000-interest, self.csr.dta.loc[self.csr.dta[self.idVar] =='1', 'OtherAssets_Savings_' + self.csr.inflatedTimespan].iloc[0]))
        self.assertTrue(closeEnough(interest, self.csr.dta.loc[self.csr.dta[self.idVar] =='1', 'OtherAssets_CapitalGains_' + self.csr.inflatedTimespan].iloc[0]))

        # Incomplete -- need to update with new account fill-in logic
        interest = 0 # -(26000 * .15884) #5 year inflation
        self.assertTrue(closeEnough(-8000 , self.csr.dta.loc[self.csr.dta[self.idVar] =='1', 'AllOtherDebts_TotalChangeInWealth_' + self.csr.inflatedTimespan].iloc[0]))
        self.assertTrue(closeEnough(-8000-interest , self.csr.dta.loc[self.csr.dta[self.idVar] =='1', 'AllOtherDebts_Savings_' + self.csr.inflatedTimespan].iloc[0]))
        self.assertTrue(closeEnough(interest , self.csr.dta.loc[self.csr.dta[self.idVar] =='1', 'AllOtherDebts_CapitalGains_' + self.csr.inflatedTimespan].iloc[0]))

        # Person 2
        interest = 11000 * (1.01**5) - 11000
        self.assertTrue(closeEnough(5000 , self.csr.dta.loc[self.csr.dta[self.idVar] =='2', 'OtherAssets_TotalChangeInWealth_' + self.csr.inflatedTimespan].iloc[0]))
        self.assertTrue(closeEnough(5000-interest , self.csr.dta.loc[self.csr.dta[self.idVar] =='2', 'OtherAssets_Savings_' + self.csr.inflatedTimespan].iloc[0]))
        self.assertTrue(closeEnough(interest , self.csr.dta.loc[self.csr.dta[self.idVar] =='2', 'OtherAssets_CapitalGains_' + self.csr.inflatedTimespan].iloc[0]))

        interest = 0 # -(12000 * .15884) #5 year inflation
        self.assertTrue(closeEnough(7000 , self.csr.dta.loc[self.csr.dta[self.idVar] =='2', 'AllOtherDebts_TotalChangeInWealth_' + self.csr.inflatedTimespan].iloc[0]))
        self.assertTrue(closeEnough(7000-interest , self.csr.dta.loc[self.csr.dta[self.idVar] =='2', 'AllOtherDebts_Savings_' + self.csr.inflatedTimespan].iloc[0]))
        self.assertTrue(closeEnough(interest, self.csr.dta.loc[self.csr.dta[self.idVar] =='2', 'AllOtherDebts_CapitalGains_' + self.csr.inflatedTimespan].iloc[0]))


    def test_calcSavingsRate_ActiveSavings_AllZero(self):

        data = self.createDummyData(includeMovingVars = True,  includeValueVars = False, includeChangeInValueVars = True)
        self.csr.dta =  data
        self.csr.calcTotalSavingsRate()

        allVars = ['Total_ChangeInWealth_'  + self.csr.inflatedTimespan,'Total_CapitalGains_'  + self.csr.inflatedTimespan,'Total_GrossSavings_'  + self.csr.inflatedTimespan, 
                'netMoveIn_' + self.csr.inflatedTimespan, 'netMoveOut_' + self.csr.inflatedTimespan,
                'Total_NetActiveSavings_'  + self.csr.inflatedTimespan, 'activeSavingsRate_AnnualHH_' + self.csr.inflatedTimespan]

        for var in allVars:
            self.assertTrue(self.csr.dta[var].eq(0).all())

    def test_calcSavingsRate_ActiveSavings_GrossSavingsAndGains(self):


        data = self.createDummyData(includeMovingVars = True,  includeValueVars = False, includeChangeInValueVars = True)
        
        # componentVars = ['House', 'OtherRealEstate', 'Business', 'BrokerageStocks', 'CheckingAndSavings', 'Vehicle', 'OtherAssets', 'OtherDebts']

        # Not relevant to active savings adjustments in this version: data.loc[data[self.idVar] =='2', 'PrivateRetirePlan_SinceLastQYr_AmountMovedIn_'+ self.csr.eyStr] = 135.5

        data.loc[data[self.idVar] =='1', 'House_CapitalGains_'+ self.csr.inflatedTimespan] = 25000
        data.loc[data[self.idVar] =='1', 'OtherRealEstate_CapitalGains_'+ self.csr.inflatedTimespan] = 24500
        data.loc[data[self.idVar] =='1', 'AllOtherDebts_CapitalGains_'+ self.csr.inflatedTimespan] = -402
        data.loc[data[self.idVar] =='1', 'BrokerageStocks_CapitalGains_'+ self.csr.inflatedTimespan] = 25000
        data.loc[data[self.idVar] =='1', 'Vehicle_CapitalGains_'+ self.csr.inflatedTimespan] = 1
        data.loc[data[self.idVar] =='1', 'OtherAssets_CapitalGains_'+ self.csr.inflatedTimespan] = 56

        data.loc[data[self.idVar] =='1', 'Business_Savings_'+ self.csr.inflatedTimespan] = 25000
        data.loc[data[self.idVar] =='1', 'House_Savings_'+ self.csr.inflatedTimespan] = 10000
        data.loc[data[self.idVar] =='1', 'BrokerageStocks_Savings_'+ self.csr.inflatedTimespan] = 100
        data.loc[data[self.idVar] =='1', 'CheckingAndSavings_Savings_'+ self.csr.inflatedTimespan] = -100
        data.loc[data[self.idVar] =='1', 'Vehicle_Savings_'+ self.csr.inflatedTimespan] = -4550

        data.loc[data[self.idVar] =='2', 'Business_CapitalGains_'+ self.csr.inflatedTimespan] = -1000
        data.loc[data[self.idVar] =='2', 'CheckingAndSavings_CapitalGains_'+ self.csr.inflatedTimespan] = 0
        data.loc[data[self.idVar] =='2', 'OtherAssets_CapitalGains_'+ self.csr.inflatedTimespan] = -110

        data.loc[data[self.idVar] =='2', 'AllOtherDebts_Savings_'+ self.csr.inflatedTimespan] = 2000
        data.loc[data[self.idVar] =='2', 'Business_Savings_'+ self.csr.inflatedTimespan] = 3005
        data.loc[data[self.idVar] =='2', 'OtherAssets_Savings_'+ self.csr.inflatedTimespan] = 180

        data.loc[data[self.idVar] =='1', 'PersonMovedOut_SinceLastQYr_DebtsMovedOut_' + self.csr.eyStr] = 10
        data.loc[data[self.idVar] =='1', 'largeGift_All_AmountHH_' + self.csr.eyStr] = 15000
        
        data.loc[data[self.idVar] =='2', 'PersonMovedIn_SinceLastQYr_AssetsMovedIn_'   + self.csr.eyStr] = 150
        data.loc[data[self.idVar] =='2', 'PersonMovedIn_SinceLastQYr_DebtsMovedIn_' + self.csr.eyStr] = 10


        self.csr.dta =  data
        self.csr.calcTotalSavingsRate()

        # Check capital Gains
        self.assertTrue(closeEnough(25000 + 24500-402 + 25000 + 1 + 56, self.csr.dta.loc[self.csr.dta[self.idVar] =='1', 'Total_CapitalGains_' + self.csr.inflatedTimespan].iloc[0]))
        self.assertTrue(closeEnough(-1000-110, self.csr.dta.loc[self.csr.dta[self.idVar] =='2', 'Total_CapitalGains_' + self.csr.inflatedTimespan].iloc[0]))

        # Check Gross savings
        savings1 = 25000 + 10000 + 100 -100 -4550
        self.assertTrue(closeEnough(savings1, self.csr.dta.loc[self.csr.dta[self.idVar] =='1', 'Total_GrossSavings_' + self.csr.inflatedTimespan].iloc[0]))
        savings2 = 2000 + 3005 + 180
        self.assertTrue(closeEnough(savings2, self.csr.dta.loc[self.csr.dta[self.idVar] =='2', 'Total_GrossSavings_' + self.csr.inflatedTimespan].iloc[0]))

        # Check Active Savings
        self.assertTrue(closeEnough(savings1 - 10 - 15000, self.csr.dta.loc[self.csr.dta[self.idVar] =='1', 'Total_NetActiveSavings_' + self.csr.inflatedTimespan].iloc[0]))
        self.assertTrue(closeEnough(savings2 - 150 + 10, self.csr.dta.loc[self.csr.dta[self.idVar] =='2', 'Total_NetActiveSavings_' + self.csr.inflatedTimespan].iloc[0]))


if __name__ == '__main__':
    unittest.main()

