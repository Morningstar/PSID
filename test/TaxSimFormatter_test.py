from Taxsim.TaxSimFormatter import TaxSimFormatter
import unittest
import pandas as pd
import numpy.testing as npt
from pandas.testing import assert_frame_equal, assert_series_equal


class TaxSimFormatterTest(unittest.TestCase):
     
    def initAnalyzer(self):
        self.ts = TaxSimFormatter.TaxSimFormatter(PSID_INPUT_DATA_DIR='C:/Dev/src/MorningstarGithub/PSID/inputData',  # we need this for the State Codes
                                                  OUTPUT_DATA_DIR='B')
      
    def createDummyData(self, year):
        
        # Start with a simple empty DF -- three families - single, married, and married with children
        famData = pd.DataFrame({
            
            'familyInterviewId': ['1','2', '3', '4'],
            'stateH': [19, 12, 9, 25],
            'martialStatusR': ['Never Married', 'Married', 'Married', 'Married'],
            'ageR': [30, 39, 44, 72],       'ageS': [29, 38, 46, 67], 
            'NumChildrenInFU': [0,0,2,0],
            'wageIncomeR': [60000, 100000, 120000, 0],          'wageIncomeS': [0, 5000, 20000, 0],
            'DividendsR': [0, 40, 320, 30000],           'DividendsS': [20, 56, 604, 32300],
            'InterestIncomeR': [10, 30, 400, 200],      'InterestIncomeS': [0, 40, 300, 2300],
            'RentIncomeR': [0, 100, 0, 3000],          'RentIncomeS': [0, 0, 500, 0],
            'VAPensionIncomeR': [0,0,0,0],     'VAPensionIncomeS': [0,0,0,41],
            'PensionIncomeR': [0,0,0,4576],       'PensionIncomeS': [0,0,0,45.7],
            'IRAIncomeR': [0,0,0,465],           'IRAIncomeS': [0,0,0,466],
            'AnnuityIncomeR': [0,0,0,1],       'AnnuityIncomeS': [0,0,0,1],
            'OtherRetirementIncomeR': [0,0,0,2], 'OtherRetirementIncomeS': [0,0,0,2],
            'ssIncomeR': [0,0,0,2023],            'ssIncomeS': [0,0,0,2031], 
            'UnemploymentIncomeR': [0, 2000, 0, 0],  'UnemploymentIncomeS': [0, 0,0, 0], 
            'FarmIncomeRandS': [0, 0, 0, 0], 'BusinessAssetIncomeRandS': [0, 0, 0, 0], 'transferIncomeRandS': [0, 2434, 0 ,0], 
            'RentPayment_Annual': [4560, 0, 0, 0],
            'HomePropertyTaxAnnualHH': [0, 1000, 5000, 400], 
            'MortgagePaymentAnnualHH': [0, 4542, 8331, 54], 
            'HomeInsuranceAnnualHH': [0, 100, 300, 300], 
            },
            columns=[ 'familyInterviewId', 'stateH',
            'martialStatusR', 'ageR',       'ageS', 'NumChildrenInFU',
            'wageIncomeR',          'wageIncomeS',
            'DividendsR',           'DividendsS',
            'InterestIncomeR',      'InterestIncomeS',
            'RentIncomeR',          'RentIncomeS',           
            'VAPensionIncomeR',     'VAPensionIncomeS',
            'PensionIncomeR',       'PensionIncomeS',
            'IRAIncomeR',           'IRAIncomeS',
            'AnnuityIncomeR',       'AnnuityIncomeS',
            'OtherRetirementIncomeR', 'OtherRetirementIncomeS',
            'ssIncomeR',            'ssIncomeS', 
            'UnemploymentIncomeR',  'UnemploymentIncomeS', 
            'FarmIncomeRandS', 'BusinessAssetIncomeRandS', 'transferIncomeRandS', 'RentPayment_Annual', 
            'HomePropertyTaxAnnualHH',  'MortgagePaymentAnnualHH', 'HomeInsuranceAnnualHH'
                ])

        yr = str(year)
        indData = pd.DataFrame({
            "interviewId_"+yr:['1', '2', '2', '3', '3', '3','3', '4', '4'],
            "sequenceNoI_"+yr:[1,    1,   2,   1,   2,   3,  4,   1,   1],
            "ageI_"+yr:[       30,  39,  38,   44, 46,   6,  9,  72,  67],
            "employmentStatusI_"+yr:['Working', 'TemporaryLaidOff', 'Working', 'Working', 'KeepingHouse', 'Student', 'Student', 'Retired', 'Retired'],
            "relationshipToR_"+yr:['RP', 'RP', 'Partner', 'RP', 'Partner', 'Child', 'Child', 'RP', 'Partner'],
            'longitudinalWeightI_'+yr:[1,1,1,1,1,1,1,1,1],
            }, columns = ["interviewId_"+yr, "ageI_"+yr, "employmentStatusI_"+yr,
            "relationshipToR_"+yr, "sequenceNoI_"+yr, 'longitudinalWeightI_'+yr])

        self.ts.psidFamilyDta = famData
        self.ts.psidIndividualDta = indData
        self.ts.year = year
        


    def test_getFamilyAges(self):
        self.initAnalyzer()
        self.createDummyData(1999)
        
        yr = str(self.ts.year)

        self.ts.psidIndividualDta.loc[(self.ts.psidIndividualDta["interviewId_"+yr] =='3') & (self.ts.psidIndividualDta["sequenceNoI_"+yr] ==4), 'ageI_'+yr ] = 23
        self.ts.psidIndividualDta.loc[(self.ts.psidIndividualDta["interviewId_"+yr] =='3') & (self.ts.psidIndividualDta["sequenceNoI_"+yr] ==4), 'employmentStatusI_'+yr ] = 'Student'
        
        kids =  self.ts.getFamilyAges(self.ts.psidFamilyDta)
        kids = kids.reset_index()
        self.assertTrue(0 == kids.loc[kids.familyInterviewId =='1', 'depx'].iloc[0])
        self.assertTrue(0 == kids.loc[kids.familyInterviewId =='2', 'depx'].iloc[0])
        self.assertTrue(2 == kids.loc[kids.familyInterviewId =='3', 'depx'].iloc[0])
        self.assertTrue(0 == kids.loc[kids.familyInterviewId =='4', 'depx'].iloc[0])

        self.assertTrue(1 == kids.loc[kids.familyInterviewId =='3', 'dep13'].iloc[0])
        self.assertTrue(1 == kids.loc[kids.familyInterviewId =='3', 'dep17'].iloc[0])
        self.assertTrue(2 == kids.loc[kids.familyInterviewId =='3', 'dep18'].iloc[0]) # This is any dependent, including students < 24 in house


    def test_convertToTaxSim(self):
        self.initAnalyzer()
        self.createDummyData(1999)
        
        self.ts.convertToTaxSim(self.ts.psidFamilyDta, self.ts.psidIndividualDta, self.ts.year)
        result = self.ts.tsDta 

        delim = TaxSimFormatter.ID_START_SINCE_TAXIM_HAS_NO_LINE_DELIMITOR
        self.assertTrue(result.loc[result.taxsimid==delim+'1', 'page'].iloc[0] == 30)
        self.assertTrue(result.loc[result.taxsimid==delim+'1', 'pwages'].iloc[0] == 60000)
        self.assertTrue(result.loc[result.taxsimid==delim+'1', 'intrec'].iloc[0] == 10)
        self.assertTrue(result.loc[result.taxsimid==delim+'1', 'state'].iloc[0] == 21)
        
    '''        
                    'wageIncomeR': [60000, 100000, 120000, 0],          'wageIncomeS': [0, 5000, 20000, 0],
            'DividendsR': [0, 40, 320, 30000],           'DividendsS': [20, 56, 604, 32300],
            'InterestIncomeR': [10, 30, 400, 200],      'InterestIncomeS': [0, 40, 300, 2300],
            'RentIncomeR': [0, 100, 0, 3000],          'RentIncomeR': [0, 0, 500, 0],
            'VAPensionIncomeR': [0,0,0,0],     'VAPensionIncomeR': [0,0,0,41],
            'PensionIncomeR': [0,0,0,4576],       'PensionIncomeR': [0,0,0,45.7],
            'IRAIncomeR': [0,0,0,465],           'IRAIncomeR': [0,0,0,466],
            'AnnuityIncomeR': [0,0,0,1],       'AnnuityIncomeR': [0,0,0,1],
            'OtherRetirementIncomeR': [0,0,0,2], 'OtherRetirementIncomeR': [0,0,0,2],
            'ssIncomeR': [0,0,0,2023],            'ssIncomeS': [0,0,0,2031], 
            'UnemploymentIncomeR': [0, 2000, 0, 0],  'UnemploymentIncomeS': [0, 0,0, 0], 
            'transferIncomeRandS': [0, 2434, 0 ,0], 


                self.tsDta.columns= ['taxsimid', 'yearTax',  'state',  'mstat', 'page', 'sage','depx', 'dep13', 'dep17', 'dep18','pwages', 'swages', 'dividends', 
                        'intrec', 'stcg', 'ltcg', 'otherprop', 'nonprop', 'pensions', 'gssi', 'ui', 'transfers', 'rentpaid', 'proptax', 
                        'otheritem', 'childcare', 'mortgage'] # , 'familyInterviewId']

    '''
        
    def test_saveAndReadTaxSimInput(self):
        self.test_convertToTaxSim()
        self.ts.outputDir = 'C:/Dev/src/MorningstarGithub/PSID/outputData/test/'
        self.ts.saveTaxSimInput()
        dta = self.ts.readTaxSimInput()
        self.assertTrue(len(dta)==4)
        assert_series_equal(dta.proptax, pd.Series([0, 1000, 5000, 400]), check_index_type= False, check_names = False)
        assert_series_equal(dta.state, pd.Series([21, 14, 10, 27]), check_index_type= False, check_names = False)
