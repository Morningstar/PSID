import pandas as pd
import numpy as np
import os

from PSIDProcessing import Extractor, IndividualDataRecoder
from Survey.SurveyFunctions import *

import DataQuality.CrossSectionalTester as DataQualityTester
import seaborn as sns
import matplotlib.pyplot as plt

DEBUG_EDA = False


''' --------------------
 Recodes the PSID
 
 This is where the magic of standardizing the PSID happens.
 Previously, in the Extractor, we have pulled the relevant data fields using the crosswalk file and given them consistent names
 Now, we are ready to ensure that the -meaning- of those varialbes are the same.
 This class is designed to work on ONE YEAR of data at a time - using the specific cleaning, standardization processes for that specific year.
 
 This happens in three ways:
 1) Recode common values like NA and DK that have changed coding over time (early on, many of these were 9999s; later they become 999999s for example 
 2) Combine and standardize vars that have changed somewhat over time: like the handling of Race or the fields for Other Debts
 3) Do heavy processing to extract meaningful data from a range of var and combine - like calculating Retirement Contribution Rates
 
 Here's the data testing process for the PSID recoding:
 1) Run it - look for warning messages and errors.
 2) Look at the Variable Status output file - if there are any variables you need for your analysis unmapped, then you have a problem.
     The DataQualityTester.reportOnUnmapped function makes this easy
 3) Run the DataQualityTester.CrossSectionalTester checkers' checkDataQuality() function - it looks for special PSID codes that show things haven't been recoded, and for blank data
 - This QA proess is built in if you call the main 'doIt' function. 
-------------------- '''

class FamilyDataRecoder:

    def __init__(self, dta, year, varStatus, psidDataDir):
        '''
        Instanciate the recorder
        :param dta: dataset with PSID family data
        :param year: year of the PSID data
        :param varStatus:
        '''
        if dta is not None:
            self.setData(dta, year)
        self.stateCodes = pd.read_csv(os.path.join(psidDataDir, "StateCodes_PSID_To_SOI.csv"))

        self.dta = None
        self.year = None
        self.varStatus = None
        self.fields = None


    def setData(self, dta, year, varStatus):
        self.dta = dta
        self.year = year
        self.varStatus = varStatus
        self.fields = list(dta.columns)

    def addState(self):
        ''' Use our external mapping of state codes to convert from PSID's code to more a more standard FIPS code '''
        self.dta = pd.merge(self.dta, self.stateCodes, left_on = "stateH", right_on = "PSID", how="left")
        self.dta.rename(columns={'SOI':'stateH_SOI', 'FIPS': 'stateH_FIPS'}, inplace=True)


    ''' Note - the retirement contrib fields are only avaiable >=1999'''
    def recodeRetirementContrib(self, annualIncomeField, amountNoUnitField, timeUnitField, percentField, newAmountField):
        '''
        Combines the various fields for contributions to get a new field ("newAmountField") that provides the annual $ contrib
        This is meant to be called multiple times for each 'type' of contribution where the 3 input vars exist:
            Voluntary Contribs by the Employee Respondent, Voluntary Contribs by the Employee Spouse, Employer Contrib for Respondent, etc
        :param annualIncomeField: Field with income
        :type annualIncomeField: String
        :param amountNoUnitField:  Field where the contrib is given as a  $ figure
        :type amountNoUnitField:  String
        :param timeUnitField: What time period does the amount Field cover?
        :type timeUnitField:  String
        :param percentField: % of income saved
        :type percentField: String
        :param newAmountField: The field that will hold the new annual contrib numbers
        :type newAmountField: String
        :return:
        :rtype:
        '''
        self.dta[amountNoUnitField].replace({0:np.NaN, 9999998:np.NaN, 9999999: np.NaN}, inplace=True)
        self.dta[timeUnitField].replace({0:None, 3: 'Week', 4: 'TwoWeeks', 5: 'Month', 6: 'Year', 7:None, 8: None, 9:None}, inplace=True)
        self.dta[percentField].replace({0: np.NaN, 98.0: np.NaN, 99.0: np.NaN, 998.0: np.NaN, 999.0: np.NaN}, inplace=True)
                
        # The most common is the amount - start with that
        self.dta[newAmountField] = self.dta[annualIncomeField] * self.dta[percentField] / 100.0
        
        # For others, fill in if we can
        self.dta[timeUnitField] = self.dta[timeUnitField].astype(str)
        self.dta.loc[((self.dta[newAmountField].isna()) & (self.dta[timeUnitField] == 'Week')), newAmountField] = self.dta[amountNoUnitField][(self.dta[newAmountField].isna()) & (self.dta[timeUnitField] == 'Week')] * 52/1.0
        self.dta.loc[(self.dta[newAmountField].isna()) & (self.dta[timeUnitField] == 'TwoWeeks'), newAmountField] = self.dta[amountNoUnitField][(self.dta[newAmountField].isna()) & (self.dta[timeUnitField] == 'TwoWeeks')] * 52/2.0
        self.dta.loc[(self.dta[newAmountField].isna()) & (self.dta[timeUnitField] == 'Month'), newAmountField] = self.dta[amountNoUnitField][(self.dta[newAmountField].isna()) & (self.dta[timeUnitField] == 'Month')] * 12.0
        self.dta.loc[(self.dta[newAmountField].isna()) & (self.dta[timeUnitField] == 'Year'), newAmountField] = self.dta[amountNoUnitField][(self.dta[newAmountField].isna()) & (self.dta[timeUnitField] == 'Year')] * 1.0

    
    ''' Note - the fields are only avaiable >=1999''' 
    def recodeEmployerRetirementContrib(self, annualIncomeField, amountNoUnitField, timeUnitField, percentField, 
                                        employeeContribPercentField, contribAsMatchPercentField, newAmountField):
        '''
        Special Handling for Employer Contributions - building on main Retirement Contrib Function
        :param annualIncomeField: Field with income
        :type annualIncomeField: String
        :param amountNoUnitField: Field where the contrib is given as a  $ figure
        :type amountNoUnitField: String
        :param timeUnitField: What time period does the amount Field cover?
        :type timeUnitField: String
        :param percentField: % of income saved
        :type percentField: String
        :param employeeContribPercentField:
        :type employeeContribPercentField: String
        :param contribAsMatchPercentField:
        :type contribAsMatchPercentField: String
        :param newAmountField:
        :type newAmountField: String
        :return:
        :rtype:
        '''
        self.recodeRetirementContrib(annualIncomeField, amountNoUnitField, timeUnitField, percentField, newAmountField)
        
        self.dta[contribAsMatchPercentField].replace({0: np.NaN, 98.0: np.NaN, 99.0: np.NaN, 998.0: np.NaN, 999.0: np.NaN}, inplace=True)
        self.dta[employeeContribPercentField].replace({0: np.NaN, 98.0: np.NaN, 99.0: np.NaN, 998.0: np.NaN, 999.0: np.NaN}, inplace=True)
        
        mask = ((self.dta[newAmountField].isna()) & (~self.dta[contribAsMatchPercentField].isna()))
        self.dta.loc[mask, newAmountField] = self.dta[employeeContribPercentField][mask] * self.dta[annualIncomeField][mask] * self.dta[contribAsMatchPercentField][mask] / 100.0 


    def recodeAllRetirement(self):
        '''
        Handle all retirement-related fields, calling the retirement contribution functions as needed
        :return:  None
        :rtype: None
        '''

        # Retirement plan contribution rates
        self.dta.RetPlan_IsParticipatingR.replace({1:True, 5:False, 8: None, 9: None, 0: None}, inplace=True) 
        self.dta.RetPlan_IsEligibleR.replace({1:True, 5:False, 8: None, 9: None, 0: None}, inplace=True) 
        self.dta.loc[(~(self.dta.RetPlan_IsParticipatingR.isna())) & self.dta.RetPlan_IsParticipatingR, 'RetPlan_IsEligibleR'] = True # The original field is only asked of those who ARENT participating. To get eligibility generally, add those who are participating
        # self.dta.RetPlan_IsEmployeeContributingR.value_counts(dropna=False)
        self.dta.RetPlan_IsEmployeeContributingR.replace({1:True, 5:False, 8: None, 9: None, 0: None}, inplace=True) 
        self.dta.RetPlan_TypeR.replace({1:'DB', 5:'DC', 7: 'Both', 8: None, 9: None, 0: None}, inplace=True) 
    
        # if (self.year == 1999):
        #    print("Stop here")
        # Required Employee Contribs
        self.recodeRetirementContrib(annualIncomeField = 'wageIncomeR', 
                                         amountNoUnitField = 'RetPlan_ReqEmployeeContrib_AmountR', timeUnitField = 'RetPlan_ReqEmployeeContrib_PeriodR', 
                                         percentField = 'RetPlan_ReqEmployeeContrib_PercentR', newAmountField = 'RetPlan_ReqEmployeeContrib_CalcedAnnualAmountR')
        
        # Voluntary Employee Contribs
        self.recodeRetirementContrib(annualIncomeField = 'wageIncomeR', 
                                         amountNoUnitField = 'RetPlan_VolEmployeeContrib_AmountR', timeUnitField = 'RetPlan_VolEmployeeContrib_PeriodR', 
                                         percentField = 'RetPlan_VolEmployeeContrib_PercentR', newAmountField = 'RetPlan_VolEmployeeContrib_CalcedAnnualAmountR')
        
        # Employer Contrib 
        self.dta.RetPlan_EmployerContrib_YesNoR.replace({1:True, 5:False, 8: None, 9: None, 0:False}, inplace=True) 
        self.recodeEmployerRetirementContrib(annualIncomeField = 'wageIncomeR', 
                                         amountNoUnitField = 'RetPlan_EmployerContrib_AmountR', timeUnitField = 'RetPlan_EmployerContrib_PeriodR', 
                                         percentField = 'RetPlan_EmployerContrib_PercentContribedR', 
                                         # IF we don't have a strict % or Amount Contributed, we cab try calculating based on a match % of employee #s. Not as common though.
                                         employeeContribPercentField = 'RetPlan_VolEmployeeContrib_PercentR', 
                                         contribAsMatchPercentField = 'RetPlan_EmployerContrib_PercentOfEmployeeContribR', 
                                         newAmountField = 'RetPlan_EmployerContrib_CalcedAnnualAmountR')
    
        # Current Employer: Plan 2
        self.dta.RetPlan2_HasR.replace({1:True, 5:False, 8: None, 9: None, 0:False}, inplace=True) 
        self.dta.RetPlan2_EmployerContrib_YesNoR.replace({1:True, 5:False, 8: None, 9: None, 0:False}, inplace=True) 
        self.recodeEmployerRetirementContrib(annualIncomeField = 'wageIncomeR', 
                                         amountNoUnitField = 'RetPlan2_EmployerContrib_AmountR', timeUnitField = 'RetPlan2_EmployerContrib_PeriodR', 
                                         percentField = 'RetPlan2_EmployerContrib_PercentContribedR', 
                                         employeeContribPercentField = 'RetPlan_VolEmployeeContrib_PercentR', 
                                         contribAsMatchPercentField = 'RetPlan2_EmployerContrib_PercentOfEmployeeContribR',  # Very rare -- 
                                         newAmountField = 'RetPlan2_EmployerContrib_CalcedAnnualAmountR')
    
        ##############
        # Spouse Retirement Plans 
        ##############
        # Spouse: Plan 1
        self.dta.RetPlan_IsParticipatingS.replace({1:True, 5:False, 8: None, 9: None, 0: None}, inplace=True) 
        self.dta.RetPlan_IsEligibleS.replace({1:True, 5:False, 8: None, 9: None, 0: None}, inplace=True) 
        self.dta.loc[(~(self.dta.RetPlan_IsParticipatingS.isna())) & self.dta.RetPlan_IsParticipatingS, 'RetPlan_IsEligibleS'] = True # The original field is only asked of those who ARENT participating. To get eligibility generally, add those who are participating
        self.dta.RetPlan_IsEmployeeContributingS.replace({1:True, 5:False, 8: None, 9: None, 0: None}, inplace=True) 
        self.dta.RetPlan_TypeS.replace({1:'DB', 5:'DC', 7: 'Both', 8: None, 9: None, 0: None}, inplace=True) 
    
        # Required Employee Contribs
        self.recodeRetirementContrib(annualIncomeField = 'wageIncomeS', 
                                         amountNoUnitField = 'RetPlan_ReqEmployeeContrib_AmountS', timeUnitField = 'RetPlan_ReqEmployeeContrib_PeriodS', 
                                         percentField = 'RetPlan_ReqEmployeeContrib_PercentS', newAmountField = 'RetPlan_ReqEmployeeContrib_CalcedAnnualAmountS')
        
        # Voluntary Employee Contribs
        self.recodeRetirementContrib(annualIncomeField = 'wageIncomeS', 
                                         amountNoUnitField = 'RetPlan_VolEmployeeContrib_AmountS', timeUnitField = 'RetPlan_VolEmployeeContrib_PeriodS', 
                                         percentField = 'RetPlan_VolEmployeeContrib_PercentS', newAmountField = 'RetPlan_VolEmployeeContrib_CalcedAnnualAmountS')
        
        # Employer Contrib 
        self.recodeEmployerRetirementContrib(annualIncomeField = 'wageIncomeS', 
                                         amountNoUnitField = 'RetPlan_EmployerContrib_AmountS', timeUnitField = 'RetPlan_EmployerContrib_PeriodS', 
                                         percentField = 'RetPlan_EmployerContrib_PercentContribedS', 
                                         employeeContribPercentField = 'RetPlan_VolEmployeeContrib_PercentS', 
                                         contribAsMatchPercentField = 'RetPlan_EmployerContrib_PercentOfEmployeeContribS',
                                         newAmountField = 'RetPlan_EmployerContrib_CalcedAnnualAmountS')
       
        # Plan 2
        self.dta.RetPlan2_HasS.replace({1:True, 5:False, 8: None, 9: None, 0:False}, inplace=True) 
        self.dta.RetPlan2_EmployerContrib_YesNoS.replace({1:True, 5:False, 8: None, 9: None, 0:False}, inplace=True) 
        self.recodeEmployerRetirementContrib(annualIncomeField = 'wageIncomeS', 
                                         amountNoUnitField = 'RetPlan2_EmployerContrib_AmountS', timeUnitField = 'RetPlan2_EmployerContrib_PeriodS', 
                                         percentField = 'RetPlan2_EmployerContrib_PercentContribedS', 
                                         employeeContribPercentField = 'RetPlan_VolEmployeeContrib_PercentS', 
                                         contribAsMatchPercentField = 'RetPlan2_EmployerContrib_PercentOfEmployeeContribS', 
                                         newAmountField = 'RetPlan2_EmployerContrib_CalcedAnnualAmountS')   
        
    
    def recodeRace(self, hispanicField, race1Field, race2Field, newRaceField):
        '''
        Helper function to recode Race into Black/White/Hispanic/Asian/etc   - this is called for both Spouse and Respondant
        :param hispanicField: Field in given year that covers whether the person is / identifies as hispanic
        :type hispanicField:  String
        :param race1Field: First response on race
        :type race1Field:  String
        :param race2Field: Second response on race
        :type race2Field:  String
        :param newRaceField: Field for consolidated data to go into
        :type newRaceField:  String
        :return:  None
        :rtype: None
        '''

        if (((self.year >= 1985) and (self.year <= 1996)) or (self.year >= 2005)):
            self.dta[newRaceField] = self.dta[hispanicField]
            self.dta[newRaceField] = self.dta[newRaceField].mask((self.dta[newRaceField] >= 1) & (self.dta[newRaceField] <= 7), 'Hispanic')
            self.dta[newRaceField].replace({9: 'Unknown', 0: 'Unknown'}, inplace=True)
            self.dta.loc[(self.dta[newRaceField].isin(['Unknown'])), newRaceField] = self.dta[race1Field][(self.dta[newRaceField].isin(['Unknown']))]  
            self.dta[newRaceField].replace({1:'White', 2: 'Black', 3: 'NativeAmerican', 4: 'Asian', 5: 'Pacific', 7:'Other', 9: 'Unknown'}, inplace=True)
            self.dta.loc[(self.dta[newRaceField].isin(['Unknown'])), newRaceField] = self.dta[race2Field][(self.dta[newRaceField].isin(['Unknown']))]  
            self.dta[newRaceField].replace({1:'White', 2: 'Black', 3: 'NativeAmerican', 4: 'Asian', 5: 'Pacific', 7:'Other', 9: 'Unknown', 0: 'Unknown'}, inplace=True)
        elif (self.year < 1985):
            self.dta[newRaceField] = self.dta[race1Field]
            self.dta[newRaceField].replace({1:'White', 2: 'Black', 3: 'Hispanic', 7:'Other', 9: 'Unknown', 0: 'Unknown'}, inplace=True)
        elif ((self.year > 1996) and (self.year < 2005)):
            self.dta[newRaceField] = self.dta[race1Field]
            self.dta[newRaceField].replace({1:'White', 2: 'Black', 3: 'NativeAmerican', 4: 'Asian',
                                            5: 'Hispanic', 
                                            6: 'Other', 7:'Other', 9: 'Unknown', 0: 'Unknown'}, inplace=True)
            self.dta.loc[(self.dta[newRaceField].isin(['Unknown'])), newRaceField] = self.dta[race2Field][(self.dta[newRaceField].isin(['Unknown']))]  
            self.dta[newRaceField].replace({1:'White', 2: 'Black', 3: 'NativeAmerican', 4: 'Asian',
                                            5: 'Hispanic', 
                                            6: 'Other', 7:'Other', 9: 'Unknown', 0: 'Unknown'}, inplace=True)
        else:
            raise Exception("Check Race coding for unknown period")


    def recodeJobStatus(self):
        '''
        Standardizes whether person is working, when they started, and why they left
        :return:  None
        :rtype:  None
        '''

        if self.year < 1994:
            self.dta.IsWorkingR = self.dta.IsWorkingR_Pre1994.replace({1:'Working', 2: 'OnLeave', 3: 'Unemployed_Looking', 4: 'Retired', 5: 'Unemployed_Disabled', 6: 'Unemployed_Homemaker', 7: 'Unemployed_Student', 8: None}, inplace=False)
        else:
            self.dta.IsWorkingR.replace({1:'Working', 2: 'OnLeave', 3: 'Unemployed_Looking', 4: 'Retired', 5: 'Unemployed_Disabled', 6: 'Unemployed_Homemaker', 7: 'Unemployed_Student', 8: 'Prison', 99: None}, inplace=True)

        self.dta.IsWorking_SecondMentionR.replace({1:'Working', 2: 'OnLeave', 3: 'Unemployed_Looking', 4: 'Retired', 5: 'Unemployed_Disabled', 6: 'Unemployed_Homemaker', 7: 'Unemployed_Student', 8: 'Prison', 99: None}, inplace=True)
        self.dta.IsWorking_Test2R.replace({1:'Working', 2: 'NeverWorked', 3: 'NotEmployed'}, inplace=True)

        self.dta.IsWorkingS.replace({1:'Working', 2: 'OnLeave', 3: 'Unemployed_Looking', 4: 'Retired', 5: 'Unemployed_Disabled', 6: 'Unemployed_Homemaker', 7: 'Unemployed_Student', 8: 'Prison', 99: None}, inplace=True)
        self.dta.IsWorking_SecondMentionS.replace({1:'Working', 2: 'OnLeave', 3: 'Unemployed_Looking', 4: 'Retired', 5: 'Unemployed_Disabled', 6: 'Unemployed_Homemaker', 7: 'Unemployed_Student', 8: 'Prison', 99: None}, inplace=True)
        self.dta.IsWorking_Test2S.replace({1:'Working', 2: 'NeverWorked', 3: 'NotEmployed'}, inplace=True)

        self.dta.dateStarted_Job1_Month_R.replace({21: 1, 22: 4, 23: 7, 24: 10, 0:np.NaN, 98: np.NaN, 99: np.NaN}, inplace=True) # "ER66179": "dateStarted_Job1_Month_R", #  "BC6 BEGINNING MONTH--JOB 1" NUM(2.0)
        self.dta.dateStarted_Job1_Year_R.replace({0:np.NaN, 9996: np.NaN, 9997: np.NaN, 9998: np.NaN, 9999: np.NaN}, inplace=True) # "ER66180": "dateStarted_Job1_Year_R", # "BC6 BEGINNING YEAR--JOB 1" NUM(4.0)
        self.dta.dateStarted_Job1_Month_S.replace({21: 1, 22: 4, 23: 7, 24: 10, 0:np.NaN, 98: np.NaN, 99: np.NaN}, inplace=True)
        self.dta.dateStarted_Job1_Year_S.replace({0:np.NaN, 9996: np.NaN, 9997: np.NaN, 9998: np.NaN, 9999: np.NaN}, inplace=True)
        self.dta.dateEnded_Job1_Month_R.replace({21: 1, 22: 4, 23: 7, 24: 10, 0:np.NaN, 98: np.NaN, 99: np.NaN}, inplace=True) # 'ER66181': "dateEnded_Job1_Month_R", # "BC6 ENDING MONTH--JOB 1
        self.dta.dateEnded_Job1_Year_R.replace({0:np.NaN, 9996: np.NaN, 9997: np.NaN, 9998: np.NaN, 9999: np.NaN}, inplace=True) # 'ER66182': "dateEnded_Job1_Year_R", # "BC6 ENDING YEAR--JOB 1"
        self.dta.dateEnded_Job1_Month_S.replace({21: 1, 22: 4, 23: 7, 24: 10, 0:np.NaN, 98: np.NaN, 99: np.NaN}, inplace=True) # 'ER66456': "dateEnded_Job1_Month_S", # "DE6 ENDING MONTH--JOB 1"
        self.dta.dateEnded_Job1_Year_S.replace({0:np.NaN, 9996: np.NaN, 9997: np.NaN, 9998: np.NaN, 9999: np.NaN}, inplace=True) # 'ER66457': "dateEnded_Job1_Year_S", # "DE6 ENDING YEAR--JOB 1"

        self.dta.reasonLeftLastJobR.replace({1: 'CompanyClosed', 2: 'Strike', 3: 'LaidOff', 4: 'Quit', 7:'Transfer', 8:'Completed', 0:None, 9: None}, inplace=True) #     "ER66242": 'reasonLeftLastJobR', # "BC51 WHY LAST JOB END (RP-U)"  # from 1988 on is CHANGE EMPLOYER only; before included promotions
        self.dta.reasonLeftLastJobS.replace({1: 'CompanyClosed', 2: 'Strike', 3: 'LaidOff', 4: 'Quit', 7:'Transfer', 8:'Completed', 0:None, 9: None}, inplace=True) #     "ER66242": 'reasonLeftLastJobR', # "ER66517": 'reasonLeftLastJobS', # "DE51 WHY LAST JOB END (SP-U)" NUM(1.0)  # from 1988 on is CHANGE EMPLOYER only; before included promotions


    def recodeIncome(self):
        '''
        Recoding for lots of income-related fields
        :return: None
        :rtype: None
        '''
        self.dta.YearRetiredR.replace({9998:np.NaN, 9999: np.NaN, 0: np.NaN}, inplace=True)
        self.dta.AgePlanToRetireR.replace({996:np.NaN, 997:np.NaN, 998: np.NaN, 999: np.NaN, 0:np.NaN}, inplace=True)

        # Except for 1994, No processing needed:  These are actual values, topcoded, so dont drop big numbers
        if self.year == 1994: # Yes, all of these were recoded for 1994
            self.dta.totalIncomeHH.replace({0:np.NaN, 9999999: np.NaN}, inplace=True) #'ER71426': 'totalIncomeHH', # "TOTAL FAMILY INCOME-2016"  #  40 obs
            self.dta.taxableIncomeRandS.replace({0:np.NaN, 9999999: np.NaN}, inplace=True) #'ER71330': 'taxableIncomeRandS',# Reference Person and Spouse/Partner Taxable Income-2016  #  40 obs
            self.dta.taxableIncomeO.replace({0:np.NaN, 9999999: np.NaN}, inplace=True) #'ER71398': 'taxableIncomeO', # Taxable Income of Other FU Members-2016   #  40 obs
            self.dta.transferIncomeRandS.replace({0:np.NaN, 9999999: np.NaN}, inplace=True)
            self.dta.transferIncomeO.replace({0:np.NaN, 999999: np.NaN}, inplace=True)
        else: 
            self.dta.totalIncomeHH.replace({0:np.NaN}, inplace=True) #'ER71426': 'totalIncomeHH', # "TOTAL FAMILY INCOME-2016"  #  40 obs
            self.dta.taxableIncomeRandS.replace({0:np.NaN}, inplace=True) #'ER71330': 'taxableIncomeRandS',# Reference Person and Spouse/Partner Taxable Income-2016  #  40 obs
            self.dta.taxableIncomeO.replace({0:np.NaN}, inplace=True) #'ER71398': 'taxableIncomeO', # Taxable Income of Other FU Members-2016   #  40 obs
            self.dta.transferIncomeRandS.replace({0:np.NaN}, inplace=True)
            self.dta.transferIncomeO.replace({0:np.NaN}, inplace=True)
            
        # Wage income - needed for interpreting retirement contribution rates, below
        self.dta.hasWageIncomeR.replace({1:True, 5: False, 8: None, 9: None, 0:None}, inplace=True)
        self.dta.wageIncomeR.replace({0:np.NaN, 9999998:np.NaN, 9999999: np.NaN, -9999999: np.NaN}, inplace=True)

        if (self.year >= 1994):
            self.dta['wageIncomeS'] = self.dta.wageIncomeS_Post1993 
            self.dta.wageIncomeS.replace({0:np.NaN, 9999998:np.NaN, 9999999: np.NaN, -9999999: np.NaN}, inplace=True)
            self.dta.hasWageIncomeS.replace({1:True, 5: False, 8: None, 9: None, 0:None}, inplace=True)
        else:
            self.dta['wageIncomeS'] = self.dta.laborIncomeS_1993AndPre  # No 'wage only' income from pre 1994, only total labor 
            self.dta.wageIncomeS.replace({0:np.NaN, 9999998:np.NaN, 9999999: np.NaN, -9999999: np.NaN}, inplace=True)
            self.dta['hasWageIncomeS'] = (~(self.dta.wageIncomeS.isna())) & (self.dta.wageIncomeS > 0)

            self.dta['hasWageIncomeR'] = (~(self.dta.wageIncomeR.isna())) & (self.dta.wageIncomeR > 0)  

        # Pension income, R
        if self.year <= 1992:
            self.dta['PensionIncomeR'] =  self.dta['PensionIncomeR_NonVet_1984to1992']
            self.dta['AnnuityIncomeR'] = None # Before 1992, annuity income is included in Pension Income
            
        else:
            # TOOD -- double check are these always the DK and NA values?
            self.createAnnualAmountFieldFromUnitAndBase('PensionIncomeR_NonVet_1993to2017', 'PensionIncomeR', 999998, 999999)
            self.createAnnualAmountFieldFromUnitAndBase('AnnuityIncomeR', 'AnnuityIncomeR', 999998, 999999)


        # Pension income, S
        # Note -- Annuity income is only relevant for Spouses after 2016; all prior year it's not available (and auto-filled to 0)
        if self.year <= 1992:
            self.dta['PensionIncomeS'] =  self.dta['PensionIncomeS_NonVet_1985to1992'] # 'V11451': '', # Annual  
        elif self.year <= 2011:
            self.createAnnualAmountFieldFromUnitAndBase('PensionIncomeS_NonVet_1993to2011', 'PensionIncomeS', 999998, 999999)
        else: #  self.year > 2011:
            self.dta['PensionIncomeS'] =  self.dta['PensionIncomeS_NonVet_2013to2017']  # 'ER71369': 'PensionIncomeS_NonVet_2013to2017',  Annual


        if self.year >= 2005:
            self.dta['DividendsR'] = self.dta['DividendsR_2005On']
            self.dta['InterestIncomeR'] = self.dta['InterestIncomeR_2005On']
            
            self.dta['DividendsS'] = self.dta['DividendsS_2005On']
            self.dta['InterestIncomeS'] = self.dta['InterestIncomeS_2005On']
        elif self.year >= 1993:
            self.createAnnualAmountFieldFromUnitAndBase('DividendsR_1993to2017', 'DividendsR', 999998, 999999)
            self.createAnnualAmountFieldFromUnitAndBase('DividendsS_1993to2017', 'DividendsS', 999998, 999999)
            
            self.createAnnualAmountFieldFromUnitAndBase('InterestIncomeR_1993to2017', 'InterestIncomeR', 999998, 999999)
            self.createAnnualAmountFieldFromUnitAndBase('InterestIncomeS_1993to2017', 'InterestIncomeS', 999998, 999999)
        elif self.year >= 1984:
            self.dta['DividendsR'] = self.dta['DividendAndInterestIncomeR_1984to1992']
            self.dta['DividendsS'] = self.dta['DividendAndInterestIncomeS_1970to1992']
            
            self.dta['InterestIncomeR'] = 0
            self.dta['InterestIncomeS'] = 0


        varsWith6DigitMaxValueCoding = ['RentIncomeR', 'RentIncomeS', 
                                   'UnemploymentIncomeR', 'UnemploymentIncomeS', 
                                   'VAPensionIncomeR', 'OtherRetirementIncomeR',
                                   'VAPensionIncomeS',  'AnnuityIncomeS', 'IRAIncomeR', 'IRAIncomeS','OtherRetirementIncomeS'
                                   ]
        for var in varsWith6DigitMaxValueCoding:
            self.dta[var].replace({0:np.NaN, 999999: np.NaN}, inplace=True)
        
        if self.year == 1991:  # In other years, 999999 is an actual values
            self.dta.FederalIncomeTaxesRS.replace({0:np.NaN, 999999: np.NaN}, inplace=True)
            self.dta.FederalIncomeTaxesO.replace({0:np.NaN, 999999: np.NaN}, inplace=True)


        # only used in certain years, but doesnt seem to harm other years
        self.dta.PovertyThreshold.replace({99999:np.NaN}, inplace=True)
        
        # summary stats on income
        # self.dta.summaryWageIncomeR.replace({0:np.NaN}, inplace=True)
        # self.dta.summaryWageIncomeS.replace({0:np.NaN}, inplace=True)


    def recodeNetWealth(self):
        '''
        Recodes the fields the go into net wealth, then recalculates Net Wealth.
        Note -- unlike the PSID original field, we include Retirement funds (pension + IRA + 401k)
        :return: None
        :rtype:  None
        '''

        ''' 
        Here's what the PSID var uses:
        # 'ER71483': 'NetWorthNoHome', #  "IMP WEALTH W/O EQUITY (WEALTH1) 2017"
        Constructed wealth variable, excluding equity. This imputed variable is constructed as
        the sum of values of seven asset types (
            ER71429 (farm/business), 
            ER71435 (checking/savings), 
            ER71439 (other real estate)
            ER71445 (stocks),  -- outside of private & employer retirement accounts
            ER71447 (vehicles),
            ER71451 (other: bonds & insurance)
            ER71455 (annuity, IRA)- private only. DOES NOT include retirement 
            net of debt value (ER71431, ER71441, ER71459, ER71463, ER71467, ER71471, ER71475, ER71479).
        '''
    
        self.dta.hasBrokerageStocks.replace({1:True, 0: False}, inplace=True) # 'ER71443': 'hasStocks', #  "IMP WTR STOCKS (W15) 2017"  # Does anyone in HH have stocks beyond Ret plan
        # self.dta.hasBrokerageStocks.fillna(False, inplace=True)
        # Don't clear out the Value Field -- rather, a value indicates the person DOES have it; we use this value later
        # self.dta.loc[(~self.dta.hasBrokerageStocks), 'valueOfBrokerageStocks_Net'] = np.NaN# 'ER71445': 'valueOfStocks', #  "IMP VALUE STOCKS (W16) 2017" # How much
        # self.dta.valueOfBrokerageStocks.value_counts(dropna=False)

        self.dta.hasPrivateRetirePlan.replace({1:True, 0: False}, inplace=True) # 'ER71453': 'hasPrivateRetirePlan', #  "IMP WTR ANNUITY/IRA (W21) 2017" # Wherther have private annuities or IRAs
        # self.dta.hasPrivateRetirePlan.fillna(False, inplace=True)
        # Don't clear out the Value Field -- rather, a value indicates the person DOES have it; we use this value later
        # self.dta.loc[(~self.dta.hasPrivateRetirePlan), 'valueOfPrivateRetirePlan_Gross'] = np.NaN # 'ER71455': 'valueOfPrivateRetirePlan_Gross', #  "IMP VALUE ANNUITY/IRA (W22) 2017" # How much

        self.dta['hasEmployerRetirePlanR'] = self.dta.RetPlan_IsParticipatingR.replace({1:True, 5:False, 8: None, 9: None, 0: None})
        self.dta.valueOfEmployerRetirePlanR_Gross.replace({0:np.NaN, 999998: np.NaN, 999999: np.NaN, 999999998:np.NaN, 999999999: np.NaN}, inplace=True) # 'ER68010': 'valueOfEmployerRetirePlanR_Gross', #  "P20 AMT IN PENSION ACCT NOW - RP"         # Current Value of Employer Retirement Account
        self.dta['hasEmployerRetirePlanS'] = self.dta.RetPlan_IsParticipatingS.replace({1:True, 5:False, 8: None, 9: None, 0: None})
        self.dta.valueOfEmployerRetirePlanS_Gross.replace({0:np.NaN, 999998: np.NaN, 999999: np.NaN, 999999998:np.NaN, 999999999: np.NaN}, inplace=True) # 'ER68227': 'valueOfEmployerRetirePlanS_Gross', #  "P20 AMT IN PENSION ACCT NOW - SP"
        self.dta['valueOfEmployerRetirePlan_Gross'] = self.dta.valueOfEmployerRetirePlanR_Gross.add(self.dta.valueOfEmployerRetirePlanS_Gross, fill_value=0)
        self.dta['hasEmployerRetirePlan'] = (self.dta.hasEmployerRetirePlanR==True) | (self.dta.hasEmployerRetirePlanS == True)
        self.dta.hasEmployerRetirePlan = self.dta.hasEmployerRetirePlan.astype('bool')

        # self.dta.valueOfEmployerRetirePlanS_Gross.describe()  value_counts(dropna=False)

        # 'ER66030': 'hasHouse', # "A19 OWN/RENT OR WHAT"
        self.dta.hasHouse.replace({1:True, 5:False, 8: None, 9:None}, inplace=True) # For our purposes, someone who 'neither owns nor rents' isn't included in a home-based savings calc
        self.dta.hasHouse = self.dta.hasHouse.astype('bool')
        self.dta.valueOfHouse_Gross.replace({0:np.NaN, 9999998:np.NaN, 9999999: np.NaN}, inplace=True) # 'ER66031': 'valueOfHouse_Gross' # ' ER66031 "A20 HOUSE VALUE" NUM(7.0)

        # To make the data parallel in structure, we create a Vehicle var when there isn't one
        self.dta['hasVehicle'] = self.dta.valueOfVehicle_Net.ne(0)
        self.dta.valueOfVehicle_Net.replace({0:np.NaN}, inplace=True)  #     'ER71447': 'valueOfVehicle_Net',  # IMP VALUE VEHICLES (W6) 2017

        self.dta.hasOtherAssets.replace({1:True, 0:False}, inplace=True) # For our purposes, someone who 'neither owns nor rents' isn't included in a home-based savings calc
        self.dta.valueOfOtherAssets_Net.replace({0:np.NaN}, inplace=True) #     'ER71451': 'valueOfOtherAssets_Net', # IMP VALUE OTH ASSETS (W34) 2017

        if self.year >= 2019:
            self.dta['hasCheckingAndSavings'] = self.dta.hasChecking_2019on_NoCDsOrGvtBonds.replace({0:False, 1:True})
            self.dta.valueOfCheckingAndSavings_Net_2019on_NoCDsOrGvtBonds.replace({0:np.NaN}, inplace=True) # 'ER71435':  "IMP VAL CHECKING/SAVING (W28) 2017"
            self.dta.valueOfCDsOrGvtBonds_2019on.replace({0:np.NaN}, inplace=True) # 'ER71435':  "IMP VAL CHECKING/SAVING (W28) 2017"

            self.dta['valueOfCheckingAndSavings_Net'] = self.dta.valueOfCheckingAndSavings_Net_2019on_NoCDsOrGvtBonds.add(self.dta.valueOfCDsOrGvtBonds_2019on.fillna(0))
            # self.dta.loc[ self.dta.valueOfCheckingAndSavings_Net_2019on_NoCDsOrGvtBonds.isna() & self.dta.valueOfCDsOrGvtBonds_2019on.isna(), 'valueOfCheckingAndSavings_Net'] = np.NaN
        else:
            self.dta['hasCheckingAndSavings'] = self.dta.hasCheckingAndSavings_to2017.replace({0:False, 1:True})
            self.dta['valueOfCheckingAndSavings_Net'] = self.dta.valueOfCheckingAndSavings_Net_to2017.replace({0:np.NaN})


        self.dta.valueOfDebt_CreditCards_2011on.replace({0:np.NaN,  9999998:np.NaN, 9999999: np.NaN}, inplace=True) # "W39A AMOUNT OF CREDIT/STORE CARD DEBT"
        self.dta.valueOfDebt_StudentLoans_2011on.replace({0:np.NaN, 9999998:np.NaN, 9999999: np.NaN}, inplace=True)  # "W39B1 AMOUNT OF STUDENT LOANS"
        self.dta.valueOfDebt_MedicalBills_2011on.replace({0:np.NaN, 9999998:np.NaN, 9999999: np.NaN}, inplace=True) # "W39B2 AMOUNT OF MEDICAL BILLS"
        self.dta.valueOfDebt_LegalBills_2011on.replace({0:np.NaN, 9999998:np.NaN, 9999999: np.NaN}, inplace=True) # "W39B3 AMOUNT OF LEGAL BILLS"
        self.dta.valueOfDebt_FamilyLoan_2011on.replace({0:np.NaN, 9999998:np.NaN, 9999999: np.NaN}, inplace=True) # "W39B4 AMOUNT OF LOANS FROM RELATIVES"
        self.dta.valueOfDebt_Other_2013on.replace({0:np.NaN, 9999998:np.NaN, 9999999: np.NaN}, inplace=True) 

        if self.year >= 2013:
            self.dta['valueOfAllOtherDebts_Net'] = self.dta.valueOfDebt_CreditCards_2011on.add(
                self.dta.valueOfDebt_StudentLoans_2011on, fill_value=0).add(
                    self.dta.valueOfDebt_MedicalBills_2011on, fill_value=0).add(
                        self.dta.valueOfDebt_LegalBills_2011on, fill_value=0).add(
                            self.dta.valueOfDebt_FamilyLoan_2011on, fill_value=0).add(
                                self.dta.valueOfDebt_Other_2013on, fill_value=0)

            self.dta['hasAllOtherDebts'] = ((self.dta.hasCreditCards_2011on == 1) |
                (self.dta.hasStudentLoans_2011on == 1) | (self.dta.hasMedicalBills_2011on == 1) |
                (self.dta.hasLegalBills_2011on == 1) | (self.dta.hasFamilyLoan_2011on == 1) |
                                            (self.dta.hasOtherDebt_Other_2013on == 1))

        elif self.year == 2011:
            self.dta['valueOfAllOtherDebts_Net'] = self.dta.valueOfDebt_CreditCards_2011on.add(
                self.dta.valueOfDebt_StudentLoans_2011on, fill_value=0).add(
                    self.dta.valueOfDebt_MedicalBills_2011on, fill_value=0).add(
                        self.dta.valueOfDebt_LegalBills_2011on, fill_value=0).add(
                            self.dta.valueOfDebt_FamilyLoan_2011on, fill_value=0)

            self.dta['hasAllOtherDebts'] = ((self.dta.hasCreditCards_2011on == 1) |
                (self.dta.hasStudentLoans_2011on == 1) | (self.dta.hasMedicalBills_2011on == 1) |
                (self.dta.hasLegalBills_2011on == 1) | (self.dta.hasFamilyLoan_2011on == 1))

        else:
            self.dta['valueOfAllOtherDebts_Net'] = self.dta.valueOfAllOtherDebts_pre2011.replace({0:np.NaN}, inplace= False)
            self.dta['hasAllOtherDebts'] = self.dta.hasOtherDebt_pre2011.replace({1:True, 0:False}, inplace=False)

        # Handle the change from NET to GROSS+DEBT tracking on Other Real Estate and Business
        self.dta.hasOtherRealEstate.replace({1:True, 0:False}, inplace=True)
        self.dta.hasBusiness.replace({1:True, 0:False}, inplace=True)

        if self.year >=2013:
            # 'ER71439': 'valueOfOtherRealEstate_Gross_2013on', # "IMP VAL OTH REAL ESTATE ASSET (W2A) 2017"
            # 'ER71441': 'valueOfOtherRealEstate_Debt_2013on', # 'ER71441 "IMP VAL OTH REAL ESTATE DEBT (W2B) 2017"
            self.dta.valueOfOtherRealEstate_Gross_2013on.replace({0:np.NaN}, inplace= True) 
            self.dta.valueOfOtherRealEstate_Debt_2013on.replace({0:np.NaN}, inplace= True) 
            self.dta['valueOfOtherRealEstate_Net'] = self.dta.valueOfOtherRealEstate_Gross_2013on.sub(self.dta.valueOfOtherRealEstate_Debt_2013on, fill_value=0) 

            # 'ER71429': 'valueOfBusiness_Gross_2013on', # ER71429 "IMP VALUE FARM/BUS ASSET (W11A) 2017" NUM(9.0)
            # 'ER71431': 'valueOfBusiness_Debt_2013on', # ER71431 "IMP VALUE FARM/BUS DEBT (W11B) 2017"
            self.dta.valueOfBusiness_Gross_2013on.replace({0:np.NaN}, inplace= True) 
            self.dta.valueOfBusiness_Debt_2013on.replace({0:np.NaN}, inplace= True) 
            self.dta['valueOfBusiness_Net'] = self.dta.valueOfBusiness_Gross_2013on.sub(self.dta.valueOfBusiness_Debt_2013on, fill_value=0) 

        else:
            # WARNING -- these fields are mapped in the Crosswalk to Wealth File variables (S209, for example) but the data itself conforms
            # To the rules in the Family Data file.   -  Ie different codes for "Max value".
            # 'ER52354': 'valueOfOtherRealEstate_Net_pre2013',  # S309 "IMP VAL OTH REAL ESTATE (G116) 94" NUM(9.0)
            self.dta['valueOfOtherRealEstate_Net'] = self.dta.valueOfOtherRealEstate_Net_pre2013.replace({0:np.NaN}, inplace= False) 
            # 'ER52346': 'valueOfBusiness_Net_pre2013',  # S303 "IMP VALUE FARM/BUS (G125) 94" NUM(9.0)
            self.dta['valueOfBusiness_Net'] = self.dta.valueOfBusiness_Net_pre2013.replace({0:np.NaN}, inplace= False) 

        self.dta['valueOfHouse_Debt'] = self.dta.MortgagePrincipal_1.replace({9999998:np.NaN, 9999999: np.NaN}, inplace=False).add(self.dta.MortgagePrincipal_2.replace({9999998:np.NaN, 9999999: np.NaN}, inplace=False), fill_value=0)
        # 'ER66051': 'MortgagePrinciple_1', # "A24 REM PRINCIPAL MOR 1"
        # 'ER66072': 'MortgagePrinciple_2', # "A24 REM PRINCIPAL MOR 2"

        # The PSID calculates its own 'Active Savings' amount -- but only for one year.
        self.dta.ActiveSavings_PSID1989.replace({99999999: np.NaN}, inplace=True) # V17610 "ACTIVE SAVING 1984-89"

        ''' various versions of NetWorth '''        
        if self.year < 1999:
            self.dta['NetWorthWithHomeRecalc'] = self.dta.valueOfHouse_Net. \
                add(self.dta.valueOfOtherRealEstate_Net, fill_value=0). \
                add(self.dta.valueOfVehicle_Net, fill_value=0). \
                add(self.dta.valueOfBusiness_Net, fill_value=0). \
                add(self.dta.valueOfBrokerageStocks_Net, fill_value=0). \
                add(self.dta.valueOfCheckingAndSavings_Net, fill_value=0). \
                add(self.dta.valueOfOtherAssets_Net, fill_value=0). \
                sub(self.dta.valueOfAllOtherDebts_Net, fill_value=0)
        else: # As of 1999, PRIVATE Retirement plans (IRAs, Annuities) are included.  Company-sponsored ones NEVER ARE
            self.dta['NetWorthWithHomeRecalc'] = self.dta.valueOfHouse_Net. \
                add(self.dta.valueOfOtherRealEstate_Net, fill_value=0). \
                add(self.dta.valueOfVehicle_Net, fill_value=0). \
                add(self.dta.valueOfBusiness_Net, fill_value=0). \
                add(self.dta.valueOfBrokerageStocks_Net, fill_value=0). \
                add(self.dta.valueOfCheckingAndSavings_Net, fill_value=0). \
                add(self.dta.valueOfOtherAssets_Net, fill_value=0). \
                add(self.dta.valueOfPrivateRetirePlan_Gross, fill_value=0). \
                sub(self.dta.valueOfAllOtherDebts_Net, fill_value=0)

        # 401ks and Employer Pensions are never included in Net worth in PSID -- but useful for us
        self.dta['NetWorthWithHomeAnd401k'] = self.dta.NetWorthWithHomeRecalc.add(self.dta.valueOfEmployerRetirePlan_Gross, fill_value=0)
        
            
    def recodeAssetFlow(self):
        '''
        Handle fields on amount in or out of each asset class
        :return:
        :rtype:
        '''
    
        # Handle LARGE Gifts and Inheritance
        if (self.year < 1989):
            skipFlowRecoding = True
            self.dta['LargeGift_1_AmountHH'].replace({0:np.NaN, 9999997: np.NaN, 9999998:np.NaN, 9999999: np.NaN}, inplace=True) # ER67967 VALUE 1ST INHERT
            self.dta['LargeGift_AllBut1_AmountHH_1989AndBefore'].replace({0:np.NaN, 9999997: np.NaN, 9999998:np.NaN, 9999999: np.NaN}, inplace=True) 
        elif (self.year == 1989):
            skipFlowRecoding = False
            self.dta['LargeGift_1_AmountHH'].replace({0:np.NaN}, inplace=True) # ER67967 VALUE 1ST INHERT
            self.dta['LargeGift_AllBut1_AmountHH_1989AndBefore'].replace({0:np.NaN}, inplace=True) 
            dontKnowValue = 9999998 # 9,999,998
            naValue =  9999999 # 9,999,999
            lossDKValue = np.NaN
        elif (self.year == 1994):
            skipFlowRecoding = False
            dontKnowValue = 9999998 # 9,999,998
            naValue =  9999999 # 9,999,999
            lossDKValue = np.NaN
        else:
            skipFlowRecoding = False
            dontKnowValue = 999999998 # 999,999,998
            naValue =  999999999 # 999,999,999
            lossDKValue = -99999999

        if (not skipFlowRecoding):
            # Note for 1984-1994, these are 5 year values (since last Wealth supplement) 
            # self.dta.PersonMovedOut_SinceLastQYr_WithAssetsYesNo.replace({0:False, 1:True, 5: False, 8: None, 9:None}, inplace=True) # 'ER67941': 'PersonMovedOut_2Yr_WithAssetsYesNo', # "W102 WTR MOVER OUT W/ ASSETS OR DEBITS"
            self.dta.PersonMovedOut_SinceLastQYr_AssetsMovedOut.replace({0:np.NaN, dontKnowValue:np.NaN, naValue: np.NaN, lossDKValue: np.NaN}, inplace=True) # 'ER67942': 'PersonMovedOut_2Yr_AssetsMovedOut', # "W103 VALUE ASSETS MOVED OUT"
            self.dta.PersonMovedOut_SinceLastQYr_DebtsMovedOut.replace({0:np.NaN, dontKnowValue:np.NaN, naValue: np.NaN, lossDKValue: np.NaN}, inplace=True) # 'ER67947': 'PersonMovedOut_2Yr_DebtsMovedOut', # "W108 VALUE DEBTS MOVED OUT"
    
            # self.dta.PersonMovedIn_SinceLastQYr_WithAssetsYesNo.replace({0:False, 1:True, 5: False, 8: None, 9:None}, inplace=True) # 'ER67952': 'PersonMovedIn_2Yr_WithAssetsYesNo', # "W113 WTR MOVER IN W/ ASSETS OR DEBITS"
            self.dta.PersonMovedIn_SinceLastQYr_AssetsMovedIn.replace({0:np.NaN, dontKnowValue:np.NaN, naValue: np.NaN, lossDKValue: np.NaN}, inplace=True) # 'ER67953': 'PersonMovedIn_2Yr_AssetsMovedIn', # "W114 VALUE ASSETS MOVED IN"
            self.dta.PersonMovedIn_SinceLastQYr_DebtsMovedIn.replace({0:np.NaN, dontKnowValue:np.NaN, naValue: np.NaN, lossDKValue: np.NaN}, inplace=True) # 'ER67958': 'PersonMovedIn_2Yr_DebtsMovedIn', # "W119 VALUE DEBTS MOVE IN"
        
            # self.dta.PrivateRetirePlan_SinceLastQYr_MovedMoneyInYesNo.replace({0:False, 1:True, 5: False, 8: None, 9:None}, inplace=True) # 'ER67952': 'PersonMovedIn_2Yr_WithAssetsYesNo', # "W113 WTR MOVER IN W/ ASSETS OR DEBITS"
            # self.dta.PrivateRetirePlan_SinceLastQYr_MovedMoneyInYesNo = self.dta.PrivateRetirePlan_SinceLastQYr_MovedMoneyInYesNo.astype("boolean")
            # self.dta.PrivateRetirePlan_SinceLastQYr_MovedOutYesNo.replace({0:False, 1:True, 5: False, 8: None, 9:None}, inplace=True) # 'ER67952': 'PersonMovedIn_2Yr_WithAssetsYesNo', # "W113 WTR MOVER IN W/ ASSETS OR DEBITS"
            # self.dta.PrivateRetirePlan_SinceLastQYr_MovedOutYesNo = self.dta.PrivateRetirePlan_SinceLastQYr_MovedOutYesNo.astype("boolean")
            self.dta.PrivateRetirePlan_SinceLastQYr_AmountMovedIn.replace({0:np.NaN, dontKnowValue:np.NaN, naValue: np.NaN, lossDKValue: np.NaN}, inplace=True) # 'ER67953': 'PersonMovedIn_2Yr_AssetsMovedIn', # "W114 VALUE ASSETS MOVED IN"
            self.dta.PrivateRetirePlan_SinceLastQYr_AmountMovedOut.replace({0:np.NaN, dontKnowValue:np.NaN, naValue: np.NaN, lossDKValue: np.NaN}, inplace=True) # 'ER67953': 'PersonMovedIn_2Yr_AssetsMovedIn', # "W114 VALUE ASSETS MOVED IN"
    
            # self.dta.OtherRealEstate_SinceLastQYr_BoughtOrSold.replace({0:False, 1:True, 5: False, 8: None, 9:None}, inplace=True) # 'ER67952': 'PersonMovedIn_2Yr_WithAssetsYesNo', # "W113 WTR MOVER IN W/ ASSETS OR DEBITS"
            self.dta.OtherRealEstate_SinceLastQYr_AmountBought.replace({0:np.NaN, dontKnowValue:np.NaN, naValue: np.NaN, lossDKValue: np.NaN}, inplace=True) # 'ER67953': 'PersonMovedIn_2Yr_AssetsMovedIn', # "W114 VALUE ASSETS MOVED IN"
            self.dta.OtherRealEstate_SinceLastQYr_AmountSold.replace({0:np.NaN, dontKnowValue:np.NaN, naValue: np.NaN, lossDKValue: np.NaN}, inplace=True) # 'ER67958': 'PersonMovedIn_2Yr_DebtsMovedIn', # "W119 VALUE DEBTS MOVE IN"
    
            # self.dta.Business_SinceLastQYr_BoughtOrSold.replace({0:False, 1:True, 5: False, 8: np.NaN, 9:np.NaN}, inplace=True) # 'ER67952': 'PersonMovedIn_2Yr_WithAssetsYesNo', # "W113 WTR MOVER IN W/ ASSETS OR DEBITS"
            self.dta.Business_SinceLastQYr_AmountBought.replace({0:np.NaN, dontKnowValue:np.NaN, naValue: np.NaN, lossDKValue: np.NaN}, inplace=True) # 'ER67953': 'PersonMovedIn_2Yr_AssetsMovedIn', # "W114 VALUE ASSETS MOVED IN"
            self.dta.Business_SinceLastQYr_AmountSold.replace({0:np.NaN, dontKnowValue:np.NaN, naValue: np.NaN, lossDKValue: np.NaN}, inplace=True) # 'ER67958': 'PersonMovedIn_2Yr_DebtsMovedIn', # "W119 VALUE DEBTS MOVE IN"
    
            # self.dta.BrokerageStock_SinceLastQYr_BoughtOrSold.replace({0:False, 1:True, 5: False, 8: np.NaN, 9:np.NaN}, inplace=True) # 'ER67952': 'PersonMovedIn_2Yr_WithAssetsYesNo', # "W113 WTR MOVER IN W/ ASSETS OR DEBITS"
            self.dta.BrokerageStocks_SinceLastQYr_AmountBought.replace({0:np.NaN, dontKnowValue:np.NaN, naValue: np.NaN, lossDKValue: np.NaN}, inplace=True) # 'ER67953': 'PersonMovedIn_2Yr_AssetsMovedIn', # "W114 VALUE ASSETS MOVED IN"
            self.dta.BrokerageStocks_SinceLastQYr_AmountSold.replace({0:np.NaN, dontKnowValue:np.NaN, naValue: np.NaN, lossDKValue: np.NaN}, inplace=True) # 'ER67958': 'PersonMovedIn_2Yr_DebtsMovedIn', # "W119 VALUE DEBTS MOVE IN"

        # A mess -- this var's DK value is 9.9 million for some years, then 999 million, then back down to 9 million
        self.dta['LargeGift_1_AmountHH'].replace({0:np.NaN, 9999998:np.NaN, 9999999: np.NaN, 999999998: np.NaN, 999999999: np.NaN}, inplace=True) # ER67967 VALUE 1ST INHERT
        self.dta['LargeGift_2_AmountHH_1994AndAfter'].replace({0:np.NaN, 9999998:np.NaN, 9999999: np.NaN, 999999998: np.NaN, 999999999: np.NaN}, inplace=True) 
        self.dta['LargeGift_3_AmountHH_1994AndAfter'].replace({0:np.NaN, 9999998:np.NaN, 9999999: np.NaN, 999999998: np.NaN, 999999999: np.NaN}, inplace=True) 

        # Q: should these be inflation adjusted for 1/2 the time span, since we don't know when they happened?
        if (self.year <= 1989):
            self.dta['largeGift_All_AmountHH'] = self.dta['LargeGift_1_AmountHH'].add(self.dta['LargeGift_AllBut1_AmountHH_1989AndBefore'], fill_value=0)
        elif (self.year >= 1994):
            if self.year == 2015: # In this year alone, there is no 3rd gift for anyone
                self.dta['largeGift_All_AmountHH'] = self.dta['LargeGift_1_AmountHH'].add(self.dta['LargeGift_2_AmountHH_1994AndAfter'], fill_value=0)
            else:
                self.dta['largeGift_All_AmountHH'] = self.dta['LargeGift_1_AmountHH'].add(self.dta['LargeGift_2_AmountHH_1994AndAfter'], fill_value=0).add(self.dta['LargeGift_3_AmountHH_1994AndAfter'], fill_value=0)
        else:
            self.dta['largeGift_All_AmountHH'] = np.NaN


        ''' Help From Family and Friends; overlaps with Large Gift'''
        if ((self.year >= 1994) and (self.year <= 2003)):
            self.createAnnualAmountFieldFromUnitAndBase('helpFromFamilyRP_1993On', 'helpFromFamilyRP', 999998, 999999)
            self.createAnnualAmountFieldFromUnitAndBase('helpFromOthersRP_1993On', 'helpFromOthersRP', 999998, 999999)
            self.createAnnualAmountFieldFromUnitAndBase('helpFromFamilySP_1993On', 'helpFromFamilySP', 999998, 999999)
            self.createAnnualAmountFieldFromUnitAndBase('helpFromOthersSP_1993On', 'helpFromOthersSP', 999998, 999999)
        else:
            self.dta['helpFromFamilyRP'] = self.dta.helpFromFamilyRP_1975to1993andAfter2003.replace({0:np.NaN}, inplace= False)
            self.dta['helpFromOthersRP'] = self.dta.helpFromOthersRP_1993andAfter2003.replace({0:np.NaN}, inplace= False)
            self.dta['helpFromFamilySP'] = self.dta.helpFromFamilySP_1985to1993andAfter2003.replace({0:np.NaN}, inplace= False)
            self.dta['helpFromOthersSP'] = self.dta.helpFromOthersSP_1993andAfter2003.replace({0:np.NaN}, inplace= False)
        
        # Calculate Remaining Amount AFTER Large gifts -- as additional form of Transfer
        self.dta['HelpAndGifts_All_AmountHH'] = self.dta.helpFromFamilyRP. \
            add(self.dta.helpFromOthersRP, fill_value=0). \
            add(self.dta.helpFromFamilySP, fill_value=0). \
            add(self.dta.helpFromOthersSP, fill_value=0)            
        self.dta['SmallGift_All_AmountHH'] = self.dta['HelpAndGifts_All_AmountHH'].sub(self.dta['largeGift_All_AmountHH'], fill_value=0) 
        self.dta.loc[self.dta.SmallGift_All_AmountHH<0, 'SmallGift_All_AmountHH'] = 0    


    def recodeMiscExpenses(self):
        
        if self.year >= 1993:
            self.createAnnualAmountFieldFromUnitAndBase('RentPayment_1993On', 'RentPayment', 99998, 99999)
        else:
            self.dta['RentPayment'] = self.dta.RentPayment_Pre1993  # No Coding needed

        if self.year >= 1993:
            self.dta['FarmIncomeRandS'] = self.dta.FarmIncomeRandS_1993On 
            if self.year == 1994:
                self.dta['FarmIncomeRandS'].replace({999999:np.NaN, -999999:np.NaN}, inplace= True)
            else:
                None # no recoding needed 'ER71272':

        else:
            self.dta['FarmIncomeRandS'] = self.dta.FarmIncomeR_Before1993 # NO coding needed 'V21733

        if self.year >= 1993:
            self.dta['BusinessAssetIncomeRandS'] = self.dta.BusinessAssetIncomeR_1993On.add(self.dta.BusinessAssetIncomeS_1993On, fill_value= 0)   # No coding needed 'ER71275':      'ER71303': 
        else:
            self.dta['BusinessAssetIncomeRandS'] = self.dta.BusinessAssetIncomeRandS_Before1993 # TODO review coding 'V20439': 


    def recodeMovingAndRenting(self):
        self.dta.MovedR.replace({1:True, 2: False, 5:False, 8: None, 9:None}, inplace=True) # For our purposes, someone who 'neither owns nor rents' isn't included in a home-based savings calc
        self.dta.MovedR = self.dta.MovedR.astype('bool')

        # 'ER66030': 'hasHouse', # "A19 OWN/RENT OR WHAT"
        self.dta.hasHouse.replace({1:True, 5:False, 8: None, 9:None}, inplace=True) # For our purposes, someone who 'neither owns nor rents' isn't included in a home-based savings calc
        self.dta.hasHouse = self.dta.hasHouse.astype('bool')


    def recodeImmigration(self):
        '''
        Handle special variables about immigrant additions to the PSID
        Note --  only available in 2017 and 2019, and ONLY for people in the immigrant subsample
        :return:
        :rtype:
        '''
        self.dta.firstYearInUS_R.replace({9997:None, 9999: None, 0:None}, inplace=True)
        self.dta.firstYearInUS_S.replace({9997:None, 9999: None, 0:None}, inplace=True)

        self.dta.englishSpokenMostOftenR.replace({8:None, 9: None, 0:None}, inplace=True)  # "IMM8 WTR ENGLISH/OTR LANG MOST OFTEN-RP" # 2017 & 2019 only
        self.dta.understandEnglishR.replace({8:None, 9: None, 0:None}, inplace=True) # 2017-2019 only "IMM9 HOW WELL UNDERSTAND ENGLISH-RP"
        self.dta.speakEnglishR.replace({8:None, 9: None, 0:None}, inplace=True) # 2017-2019 only "IMM10 HOW WELL SPEAK ENGLISH-RP"
        self.dta.readEnglishR.replace({8:None, 9: None, 0:None}, inplace=True) # 2017-2019 only "IMM11 HOW WELL READ ENGLISH-RP""
        self.dta.writeEnglishR.replace({8:None, 9: None, 0:None}, inplace=True) # # 2017-2019 only "IMM12 HOW WELL WRITE ENGLISH-RP"

        self.dta.immigrantStatusIn2016_HH.replace({0:None}, inplace=True) # # 2017-2019 only "IMM 2016 SCREENING STATUS FOR THIS FU";

    def recodeHelpToOthers(self):
        '''
        Handle fields on OUTGOING funds from this HH to others
        '''
        self.dta.helpsOthersFinancially.replace({1:True, 5: False, 8:None, 9:None}, inplace=True) # All years  "G103 WTR HELP OTRS"
        self.dta.numberOtherHelpedFinancially.replace({98:None, 99:None, 0:None}, inplace=True) # All years "G104 # OTRS SUPPORTED"
        self.dta.amountOtherHelpedFinancially.replace({9999998:None, 9999999:None, 0:None}, inplace=True) # All years "G106 TOTAL SUPP OF OTRS"

        self.dta.providesChildSupport.replace({1:True, 5: False, 8:None, 9:None, 0:None}, inplace=True) # Since 1985 "G107 ANY CHILD SUPPORT"
        self.dta.amountChildSupport.replace({9999998:None, 9999999:None, 0:None}, inplace=True)  # Since 1985 "AMT OF CHLD SUPPRT GIVEN"
        self.dta.providesAlimony.replace({1:True, 5: False, 8:None, 9:None, 0:None}, inplace=True) # "G109 ANY ALIMONY"
        self.dta.amountAlimony.replace({9999998:None, 9999999:None, 0:None}, inplace=True) # "AMT OF ALIMONY GIVEN"

    def createWeightVar(self):
        if (self.year >= 1997):
            self.dta['LongitudinalWeightHH'] = self.dta.LongitudinalWeightHH_1997to2017
        elif (self.year >= 1993):
            self.dta['LongitudinalWeightHH'] = self.dta.LongitudinalWeightHH_1993to1996
        elif (self.year >= 1968):
            self.dta['LongitudinalWeightHH'] = self.dta.LongitudinalWeightHH_1968to1992

        if ((self.year >= 1997 and self.year <= 2003) or (self.year >= 2017)):
            self.dta['CrossSectionalWeightHH'] = self.dta['CrossSectionalWeightHH_1997to2003_and_2017to2019']
        else:
            self.dta['CrossSectionalWeightHH'] = None


    def recodeCoreVars(self):
        '''
        This is our main function for recoding, that then calls the functions above.
        :return:
        :rtype:
        '''
        ##########
        ## Basics for Family Unit
        ##########
        if (self.year < 1994):
            self.dta['SpouseInFU'] = self.dta.WifeInFU_Pre94.replace({1:True, 2: False, 3: False}, inplace=False) # 2 - No Wife in FU; 3: Head is female
        else:
            self.dta.SpouseInFU.replace({1:True, 5: False, 0:False}, inplace=True)
        # self.dta.SpouseInFU.value_counts(dropna=False)    

        # Gender
        self.dta.genderR.replace({1:'Male', 2: 'Female', 0: None}, inplace=True)
        if (self.year < 2015):
            self.dta['genderS'] = None
            self.dta.loc[self.dta.SpouseInFU, 'genderS'] = 'Female'  # Pre 2015, the only H of House always defaulted to male, and gender of Spouse only recorded as Female
        else:
            self.dta.genderS.replace({1:'Male', 2: 'Female', 0: None}, inplace=True)

        # Martial Status
        self.dta.martialStatusR.replace({1:'Married', 2: 'Never Married', 3: 'Widowed', 4: 'Divorced/Annulled', 5: 'Separated',8: None, 9: None}, inplace=True)
        self.dta.martialStatusGenR.replace({1:'MarriedOrCohabit', 2: 'Never Married', 3: 'Widowed', 4: 'Divorced/Annulled', 5: 'Separated',8: None, 9: None}, inplace=True)

        # Sexual Orientation of Partnership
        self.dta['genderOfPartners'] = 'Unknown'
        self.dta.loc[self.dta.martialStatusGenR != 'MarriedOrCohabit', 'genderOfPartners'] = None
        if (self.year >= 2015):
            self.dta.loc[(self.dta.martialStatusGenR == 'MarriedOrCohabit') &
                (self.dta.genderR is not None) & (self.dta.genderS is not None) &
                (self.dta.genderR != self.dta.genderS), 'genderOfPartners'] = "MixedGender"

            # Note the PSID does not appear to capture homosexual couples well - their numbers are FAR below other published sources.
            self.dta.loc[(self.dta.martialStatusGenR == 'MarriedOrCohabit') &
                (self.dta.genderR is not None) & (self.dta.genderS is not None) &
                (self.dta.genderR == "Male") & (self.dta.genderS == "Male"), 'genderOfPartners'] = "TwoMen"

            self.dta.loc[(self.dta.martialStatusGenR == 'MarriedOrCohabit') &
                (self.dta.genderR is not None) & (self.dta.genderS is not None) &
                (self.dta.genderR == "Female") & (self.dta.genderS == "Female"), 'genderOfPartners'] = "TwoWomen"


        # Household Structure
        self.dta['householdStructure'] = 'Unknown'
        self.dta.loc[self.dta['SpouseInFU'], 'householdStructure'] = 'Partners'
        self.dta.loc[(~self.dta['SpouseInFU']) & (self.dta.genderR == "Female"), 'householdStructure'] = 'Female Adult'
        self.dta.loc[(~self.dta['SpouseInFU']) & (self.dta.genderR == "Male"), 'householdStructure'] = 'Male Adult'


        ###########
        # Survey wave
        ##########
        idVar = 'familyId1968'
        self.dta['surveyInclusionGroup'] = None
        self.dta.loc[(self.dta[idVar] < 3000), 'surveyInclusionGroup'] = 'OriginalSample'
        self.dta.loc[(self.dta[idVar] > 5000)& (self.dta[idVar] < 7000), 'surveyInclusionGroup'] = 'OriginalSample'
        self.dta.loc[(self.dta[idVar] > 3000)& (self.dta[idVar] < 4000), 'surveyInclusionGroup'] = '1997-99 Immigrant'
        self.dta.loc[(self.dta[idVar] > 4000)& (self.dta[idVar] < 5000), 'surveyInclusionGroup'] = '2017-19 Immigrant'
        self.dta.loc[(self.dta[idVar] > 7000), 'surveyInclusionGroup'] = 'Non-Rep Latino Sample'

        ###########
        ## Race 
        ###########    
        self.recodeRace(hispanicField = 'hispanicR', race1Field = 'raceR1', race2Field = 'raceR2', newRaceField = 'raceR')
        self.recodeRace(hispanicField = 'hispanicS', race1Field = 'raceS1', race2Field = 'raceS2', newRaceField = 'raceS')
        self.dta.loc[(self.dta.raceS.isin(['Unknown'])) & (~self.dta.SpouseInFU), 'raceS'] = None

        self.dta['inMixedRaceCouple'] = 'Unknown'
        self.dta.loc[self.dta.martialStatusGenR != 'MarriedOrCohabit', 'inMixedRaceCouple'] = None
        self.dta.loc[(self.dta.martialStatusGenR == 'MarriedOrCohabit') &
            (self.dta.raceR is not None) & (self.dta.raceS is not None), 'inMixedRaceCouple'] = (self.dta.raceR != self.dta.raceS)

        ##########
        ## State of Residence
        ##########
        self.addState()
        if (self.year < 1994):
            self.dta['isMetroH'] = None
        elif (self.year < 2015):
            self.dta['isMetroH'] = self.dta.bealeCollapse_1994to2013.replace({1:1, 2:1, 3:1, 4:2, 5:2, 6:2, 7:2, 8:2, 9:2, 99:None,0:None})
        else:
            self.dta['isMetroH'] = self.dta.isMetroH_2015on.replace({9:None,  0: None})


        ##########
        ## Other basic demographics 
        ##########

        # Age
        self.dta.ageR.replace({999:np.NaN}, inplace=True)
        self.dta.ageS.replace({999:np.NaN}, inplace=True)
        
        # Is the ENTIRE FU In an institution? -- RARE
        if (self.year >= 1994 and self.year <= 1997):  # Wasnt asked these years
            self.dta['institutionLocationHH'] = None
        else:
            self.dta.institutionLocationHH.replace({1:'Military', 2: 'Prison', 3: 'Healthcare', 4: 'College', 7: 'Other',0:None}, inplace=True) # RARE
    
        # Education    
        if (self.year >= 1985 and self.year <= 1990):
            # For these years, we only have ranges for some values. Use the midpoint 
            self.dta.educationYearsR = self.dta.educationYearsR_85to90.replace({1: (5-0)/2, 2: 7, 3: 10, 4: 12, 5: 12, 6: 14, 7: 16, 8: 20, 9:np.NaN })
            self.dta.educationYearsS = self.dta.educationYearsS_85to90.replace({1: (5-0)/2, 2: 7, 3: 10, 4: 12, 5: 12, 6: 14, 7: 16, 8: 20, 9:np.NaN })
        else:
            self.dta.educationYearsR.replace({99: np.NaN}, inplace=True)
            self.dta.educationYearsS.replace({99: np.NaN}, inplace=True)
        
        self.dta.loc[((self.dta.educationYearsS == 0) | (self.dta.educationYearsS == 0.0)) & (~self.dta.SpouseInFU), 'educationYearsS'] = np.NaN
        # self.dta.educationYearsS.value_counts(dropna=False)

        self.recodeImmigration()

        ############
        ## Income
        ############
        self.recodeJobStatus()
        self.recodeIncome()
        
        ############
        ## Assets 
        ############
        self.recodeNetWealth()
        self.recodeAssetFlow()
        
        ############
        ## Other Expenses
        ############
        self.recodeMiscExpenses()
        
        ############
        ## Raw Materials for Home-Principal Contrib
        ############
        self.recodeMovingAndRenting()
        
        # Calc Mortgage Payment.
        # TODO - this field has -many- problems.  Needs to be rechecked for each year
        if (self.year != 1988 and self.year != 1989 and self.year != 1982 and self.year <= 1993):  # Wasnt asked these years
            self.dta['MortgagePaymentAnnualHH'] = self.dta.MortgagePaymentAnnualHH_PartialBefore1993
        elif (self.year >= 1999):
            # WARNING -- the field is labeled as a monthly value, but they don't make sense as anything but annual (at least in 2019 and 2017)
            monthsToYearsHere = 1
            self.dta['MortgagePaymentAnnualHH'] = self.dta.MortgagePaymentMonthlyHH_1999On * monthsToYearsHere
            self.dta.loc[self.dta.MortgagePaymentAnnualHH < 0, 'MortgagePaymentAnnualHH'] = 0 # Imputed values in original allowed negative.

        else:
            self.dta['MortgagePaymentAnnualHH'] = np.NaN

        # 'ER66045': 'HomePropertyTaxAnnualHH',  #"A21 ANNUAL PROPERTY TAX"
        if (self.year >= 1994):
            self.dta.HomePropertyTaxAnnualHH.replace({99998:np.NaN, 99999: np.NaN}, inplace=True)
        self.dta.loc[~(self.dta.hasHouse), 'HomePropertyTaxAnnualHH'] = np.NaN
    
        # 'ER66047': 'HomeInsuranceAnnualHH', # A22 ANNUAL OWNR INSURANC"
        self.dta.HomeInsuranceAnnualHH.replace({9998:np.NaN, 9999: np.NaN}, inplace=True)
        self.dta.loc[~(self.dta.hasHouse), 'HomeInsuranceAnnualHH'] = np.NaN

        ############
        ## Retirement Contribs 
        ############
        
        self.recodeAllRetirement()
        
        ##############
        # Gifts & Inheritances 
        ##############
        # Inheritance / Gift    
        self.dta.LargeGift_HadInLast2YearsHH.replace({1:True, 5:False, 8: None, 9: None}, inplace=True) 
        self.dta.LargeGift_1_TypeHH.replace({1:'Gift', 5:'Inheritance', 8: None, 9: None, 0:None}, inplace=True) 
        self.dta.LargeGift_1_AmountHH.replace({0:np.NaN, 9999998:np.NaN, 9999999: np.NaN}, inplace=True)
        # Build out as needed, if not covered in summary measures below

        ##################
        # Support for others
        ##################
        self.recodeHelpToOthers()

        ##################
        # Misc
        ##################
        # In the PSID, many Variables have 0 = Invalid, especially spousal questions where there is no spouse.  Here are ones we haven't covered already
        for varName in [# 'SampleErrorStratum', 'SampleErrorCluster', 
                         'ageS', 'genderS', 
                         ]:
                if (varName in self.dta.columns):
                    self.dta[varName].replace({0: None}, inplace=True)
        for varName in [# 'SampleErrorStratum', 'SampleErrorCluster', 
                         'valueOfHouse_Net',
                        'valueOfEmployerRetirePlanR_Gross', 'valueOfEmployerRetirePlanS_Gross', 
                         ]:
                if (varName in self.dta.columns):
                    self.dta[varName].replace({0: np.NaN}, inplace=True)
    
        # dta.LongitudinalWeightHH_1997to2017.value_counts(dropna=False)
        # dta.SampleErrorStratum.value_counts(dropna=False)



    ''' --------------------
     Create New Derived Variables of Interest
     
     In this section, we do additional processing to analyze new concepts, above and beyond recoding of individual vars 
    -------------------- '''
    
    

    def createHomePrincipalVars(self):
        
        # First Var: MortgagePaymentHH
        if DEBUG_EDA:
            wDescribe(self.dta.MortgagePaymentAnnualHH, self.dta.LongitudinalWeightHH).transpose()
            self.dta.MortgagePaymentAnnualHH.isna().sum()

            self.dta.MortgagePaymentAnnualHH.describe()
            # Hmm that's as max of 163200.  Even if that was all principal, a 15yr mortgage = 2.5 million. Thats possible, yes.

            # Let's explore what Z Scores would tell us though
            wValueForZScore(self.dta, X = 'MortgagePaymentAnnualHH', varForWeights = 'LongitudinalWeightHH', zScoreThreshold = 3, skipna=True)
            # Ok that's not a meaningful threshold.  27k threshold.  Many are 0.  Need to remove them first
            wValueForZScore(self.dta.loc[self.dta.MortgagePaymentAnnualHH > 0], X = 'MortgagePaymentAnnualHH', varForWeights = 'LongitudinalWeightHH', zScoreThreshold = 3, skipna=True)
            # 39k.  Ok, Z Score isn't the right one
            sns.boxplot(x=self.dta.MortgagePaymentAnnualHH)
            plt.show()

        # First Var: HomePropertyTaxAnnualHH
        if DEBUG_EDA:
            self.dta.HomePropertyTaxAnnualHH.describe() # Ah -- that's a var that should have been cleaned already

            wDescribe(self.dta.HomePropertyTaxAnnualHH, self.dta.LongitudinalWeightHH).transpose()
            self.dta.HomePropertyTaxAnnualHH.isna().sum()

        # 'ER66030': 'hasHouse', # "A19 OWN/RENT OR WHAT"
        #MortgagePaymentAnnualHH' -- derived value above
        self.dta['mortagePrincipalPayment'] = self.dta.MortgagePaymentAnnualHH 
        # 'ER66045': 'HomePropertyTaxAnnualHH',  #"A21 ANNUAL PROPERTY TAX"
        notNullMask = ~(self.dta.mortagePrincipalPayment.isna()) 
        self.dta.loc[notNullMask, 'mortagePrincipalPayment'] = self.dta.loc[notNullMask, 'mortagePrincipalPayment'].sub(self.dta.loc[notNullMask, 'HomePropertyTaxAnnualHH'], fill_value=0)
        # 'ER66047': 'HomeInsuranceAnnualHH', # A22 ANNUAL OWNR INSURANC"
        self.dta.loc[notNullMask, 'mortagePrincipalPayment'] = self.dta.loc[notNullMask, 'mortagePrincipalPayment'].sub(self.dta.loc[notNullMask, 'HomeInsuranceAnnualHH'], fill_value=0)
        
        # 'ER71492': 'MortgagePaymentHH', #  "MORTGAGE EXPENDITURE 2017"
        # (ER71492 - ER66045 -  ER66047)/12 should equal principal payment.  Pay also be able to get from ER66051 (remaining principal) w/ change over time  
    
        # 'ER67914': 'MadeMajorHomeRenovations', # "W69 WTR MADE ADDITION/REPAIRS"
        # self.dta.MadeMajorHomeRenovations.replace({1:True, 5:False, 8: None, 9: None}, inplace=True) 

        # 'ER67915': 'CostOfMajorHomeRenovations', # "W70 COST OF ADDITION/REPAIRS"
        if self.year >= 2001:
            self.dta['CostOfMajorHomeRenovations'] = self.dta.CostOfMajorHomeRenovations_2001to2017.replace({0:np.NaN, 999999998:np.NaN, 999999999: np.NaN}, inplace=False)
        elif self.year == 1999:
            self.dta['CostOfMajorHomeRenovations'] = self.dta.CostOfMajorHomeRenovations_to1999.replace({0:np.NaN, 999999998:np.NaN, 999999999: np.NaN}, inplace=False)
        elif self.year < 1994:
            self.dta['CostOfMajorHomeRenovations'] = self.dta.CostOfMajorHomeRenovations_to1999.replace({0:np.NaN}, inplace=False)
        else:  
            self.dta['CostOfMajorHomeRenovations'] = self.dta.CostOfMajorHomeRenovations_to1999.replace({0:np.NaN, 9999998:np.NaN, 9999999: np.NaN}, inplace=False)

        self.dta.Home_SinceLastQYr_SoldPrice.replace({9999998:np.NaN, 9999999: np.NaN, 999999998: np.NaN, 999999999: np.NaN}, inplace=True)
        

        
    def createRetirementSavingsVars(self):
        '''
        Calculate total effective contrib - including Employer part
        :return:
        :rtype:
        '''
        
        # self.dta.RetPlan_ReqEmployeeContrib_CalcedAnnualAmountR.describe()
        self.dta['retirementContribR'] = self.dta.RetPlan_ReqEmployeeContrib_CalcedAnnualAmountR. \
            add(self.dta.RetPlan_VolEmployeeContrib_CalcedAnnualAmountR, fill_value=0). \
            add(self.dta.RetPlan_EmployerContrib_CalcedAnnualAmountR, fill_value=0). \
            add(self.dta.RetPlan2_EmployerContrib_CalcedAnnualAmountR, fill_value=0)
        self.dta['retirementContribRateR'] = self.dta.retirementContribR / self.dta.wageIncomeR
        # self.dta.retirementContribRateR.value_counts()
        # self.dta.retirementContribRateR.describe()
    
        self.dta['retirementContribS'] = self.dta.RetPlan_ReqEmployeeContrib_CalcedAnnualAmountS. \
            add(self.dta.RetPlan_VolEmployeeContrib_CalcedAnnualAmountS, fill_value=0). \
            add(self.dta.RetPlan_EmployerContrib_CalcedAnnualAmountS, fill_value=0). \
            add(self.dta.RetPlan2_EmployerContrib_CalcedAnnualAmountS, fill_value=0)
        self.dta['retirementContribRateS'] = self.dta.retirementContribS / self.dta.wageIncomeS
        # self.dta.retirementContribRateS.value_counts()
        
        self.dta['retirementContribHH_EmployeeOnly'] = self.dta.RetPlan_ReqEmployeeContrib_CalcedAnnualAmountR.fillna(0). \
            add(self.dta.RetPlan_VolEmployeeContrib_CalcedAnnualAmountR, fill_value=0). \
            add(self.dta.RetPlan_ReqEmployeeContrib_CalcedAnnualAmountS, fill_value=0). \
            add(self.dta.RetPlan_VolEmployeeContrib_CalcedAnnualAmountS, fill_value=0)

        self.dta['retirementContribHH'] = self.dta.retirementContribR.add(self.dta.retirementContribS, fill_value=0)
        # self.dta['retirementContribHH'].value_counts(dropna=False)
    

    def createAnnualAmountFieldFromUnitAndBase(self, existingBaseName, resultFieldName, dkVal, naVal):
        self.dta[existingBaseName + '_Multiplier'] = self.dta[existingBaseName + '_Unit'].replace({2:365, 3: 52, 4:26, 5: 12, 6:1, 8: np.NaN, 9:np.NaN, 0: np.NaN}, inplace=False) 
        self.dta[existingBaseName + '_AmountNoUnit'].replace({0:np.NaN, dkVal: np.NaN, naVal: np.NaN}, inplace=True)
        self.dta[resultFieldName] = self.dta[existingBaseName + '_Multiplier'] * self.dta[existingBaseName + '_AmountNoUnit']


    def createNewVars(self):
        self.createWeightVar()
        self.createHomePrincipalVars()
        self.createRetirementSavingsVars()

    ''''
    This section handles general cleanup - removes extra vars we no longer need
    '''
    def removeSourceFieldsNoLongerUsed(self):
        self.dta.drop(columns= ['hispanicR','raceR1','raceR2',
                                'hispanicS', 'raceS1', 'raceS2',

                                 # Combined into one var for all time
                                'CostOfMajorHomeRenovations_2001to2017',  'CostOfMajorHomeRenovations_to1999',
                                'wageIncomeS_Post1993', 'laborIncomeS_1993AndPre',

                                'RentPayment_Pre1993', 'RentPayment_1993On_AmountNoUnit','RentPayment_1993On_Unit',

                                'FarmIncomeRandS_1993On',  'FarmIncomeR_Before1993',
                                'BusinessAssetIncomeR_1993On', 'BusinessAssetIncomeS_1993On','BusinessAssetIncomeRandS_Before1993',
                                'LongitudinalWeightHH_1997to2017',  'LongitudinalWeightHH_1968to1992',   'LongitudinalWeightHH_1993to1996',
                                'valueOfAllOtherDebts_pre2011',
                                'hasOtherDebt_pre2011',

                                'educationYearsR_85to90', 'educationYearsS_85to90',
                                'MortgagePaymentMonthlyHH_1999On',  'MortgagePaymentAnnualHH_PartialBefore1993',
                                'IsWorkingR_Pre1994',
                                'WifeInFU_Pre94',

                                'PensionIncomeR_NonVet_1984to1992',
                                'PensionIncomeR_NonVet_1993to2017_Unit',
                                'PensionIncomeR_NonVet_1993to2017_AmountNoUnit',

                                'AnnuityIncomeR_Unit',
                                'AnnuityIncomeR_AmountNoUnit',

                                'DividendsR_2005On', 'DividendsS_2005On',
                                'InterestIncomeR_2005On','InterestIncomeS_2005On',
                                'DividendsR_1993to2017_Unit', 'DividendsS_1993to2017_Unit',
                                'DividendsR_1993to2017_AmountNoUnit', 'DividendsS_1993to2017_AmountNoUnit',

                                'InterestIncomeR_1993to2017_Unit', 'InterestIncomeS_1993to2017_Unit',
                                'InterestIncomeR_1993to2017_AmountNoUnit', 'InterestIncomeS_1993to2017_AmountNoUnit',
                                'DividendAndInterestIncomeR_1984to1992', 'DividendAndInterestIncomeS_1970to1992',

                                'PensionIncomeS_NonVet_1985to1992',
                                'PensionIncomeS_NonVet_1993to2011_Unit',
                                'PensionIncomeS_NonVet_1993to2011_AmountNoUnit',

                                'valueOfOtherRealEstate_Net_pre2013',

                                'helpFromFamilyRP_1993On_AmountNoUnit',
                                'helpFromOthersRP_1993On_AmountNoUnit',
                                'helpFromFamilySP_1993On_AmountNoUnit',
                                'helpFromOthersSP_1993On_AmountNoUnit',

                                'helpFromFamilyRP_1993On_Unit',
                                'helpFromOthersRP_1993On_Unit',
                                'helpFromFamilySP_1993On_Unit',
                                'helpFromOthersSP_1993On_Unit',
                                'helpFromFamilyRP_1975to1993andAfter2003',
                                'helpFromOthersRP_1993andAfter2003',

                                'helpFromFamilySP_1985to1993andAfter2003',
                                'helpFromOthersSP_1993andAfter2003',

                                # Combined into new calced fields
                                'MortgagePrincipal_1', 'MortgagePrincipal_2',

                                # Retirement plan unit values - calced field are like RetPlan_VolEmployeeContrib_CalcedAnnualAmountR
                                'RetPlan_ReqEmployeeContrib_AmountR', 'RetPlan_ReqEmployeeContrib_PeriodR',
                                'RetPlan_VolEmployeeContrib_AmountR', 'RetPlan_VolEmployeeContrib_PeriodR',
                                'RetPlan_EmployerContrib_AmountR', 'RetPlan_EmployerContrib_PeriodR',
                                'RetPlan2_EmployerContrib_AmountR', 'RetPlan2_EmployerContrib_PeriodR',
                                'RetPlan_ReqEmployeeContrib_AmountS', 'RetPlan_ReqEmployeeContrib_PeriodS',
                                'RetPlan_VolEmployeeContrib_AmountS', 'RetPlan_VolEmployeeContrib_PeriodS',
                                'RetPlan_EmployerContrib_AmountS', 'RetPlan_EmployerContrib_PeriodS',
                                'RetPlan2_EmployerContrib_AmountS', 'RetPlan2_EmployerContrib_PeriodS',
                                'isMetroH_2015on', 'bealeCollapse_1994to2013',
                                'valueOfCheckingAndSavings_Net_2019on_NoCDsOrGvtBonds',
                                'valueOfCDsOrGvtBonds_2019on',
                                'hasEmployerRetirePlanR', 'hasEmployerRetirePlanS',
                                'hasCheckingAndSavings_to2017', 'hasChecking_2019on_NoCDsOrGvtBonds'
                            ])

        # Certain Columns are only created for certain years, so need to be conditionally dropped
        potentialColumnsToDrop = ['helpFromFamilyRP_1993On_Multiplier', 'helpFromOthersRP_1993On_Multiplier',
                                'helpFromFamilySP_1993On_Multiplier', 'helpFromOthersSP_1993On_Multiplier',
                                'PensionIncomeR_NonVet_1993to2017_Multiplier', 'PensionIncomeS_NonVet_1993to2011_Multiplier',
                                'DividendsR_1993to2017_Multiplier', 'DividendsS_1993to2017_Multiplier',
                                'InterestIncomeR_1993to2017_Multiplier', 'InterestIncomeS_1993to2017_Multiplier',
                                'AnnuityIncomeR_Multiplier']
        actualColumnsToDrop = [x for x in potentialColumnsToDrop if x in self.dta.columns]
        self.dta.drop(columns= actualColumnsToDrop, inplace=True)


    def doIt(self, fileNameWithPathNoExtension, save):
        '''
        doIt is the entry place for the analysis. It runs all of the recoding and cleaning process above

        :param fileNameWithPathNoExtension:
        :type fileNameWithPathNoExtension:
        :param save: Save to file?
        :type save: Booelan
        :return:
        :rtype:
        '''
        self.recodeCoreVars()
        self.createNewVars()
        self.removeSourceFieldsNoLongerUsed()

        if save:
            self.dta = self.dta.reindex(sorted(self.dta.columns), axis=1)
            self.dta.to_csv(fileNameWithPathNoExtension + ".csv", index=False)

        '''
        Check the quality of the resulting data.  This output needs to be manually reviewed 
        It's designed to be sensitive - so it'll give a warning if there is a doubt.
        But, some of those warnings aren't really a problem. Hence the need for manual review and human judgment.
        '''
        tester = DataQualityTester.CrossSectionalTester(dta = self.dta,
                                                        dfLabel = "Family Data Recoding (" + str(self.year) + ")",
                                                        year = self.year,
                                                        varMapping = self.varStatus,
                                                        ignoreUnmappedVars = True)
        
        tester.exploreData(fileNameWithPathNoExtension,  weightVar = "LongitudinalWeightHH", doFancy=False)
        tester.reportOnUnMappedVars()
        tester.checkDataQuality(raiseIfMissing = False)
        



''''
Helper Function to run our primary use case: 
'''
def recodeAndSave(params, famExtractor, indExtractor):
    if famExtractor is None:
        famExtractor = Extractor.Extractor(params.PSID_DATA_DIR, params.yearsToInclude, params.familyWealthVarsWeNeed2019, None, source='family')
    famExtractor.readExtractedData(params.yearsToInclude, filePath = os.path.join(params.BASE_OUTPUT_DIR, params.MAPPED_OUTPUT_SUBDIR), fileNameBase= "extractedPSID_Mapped_")
    varStatus = famExtractor.variableStatusLongForm

    famRecoder = FamilyDataRecoder(None, None, None, params.PSID_DATA_DIR)
    for year in famExtractor.dataDict:
        yearData = famExtractor.dataDict[year]
        famRecoder.setData(yearData, year, varStatus)
        famRecoder.doIt(os.path.join(params.BASE_OUTPUT_DIR, params.MAPPED_OUTPUT_SUBDIR,"extractedPSID_Mapped_Recoded_" + str(year)), save=True)

    if indExtractor is None:
        indExtractor = Extractor.Extractor(params.PSID_DATA_DIR, params.yearsToInclude, params.individualVarsWeNeed2019, params.individualVars_LoadRegardlessOfYear, source='individual')
    indExtractor.readExtractedData(params.yearsToInclude, filePath = os.path.join(params.BASE_OUTPUT_DIR, params.MAPPED_OUTPUT_SUBDIR), fileNameBase = "extractedPSID_Individual_Mapped")
    varStatus = indExtractor.variableStatusLongForm

    indRecoder = IndividualDataRecoder.IndividualDataRecoder(indExtractor.dataDict[0], varStatus)
    indRecoder.doIt(os.path.join(params.BASE_OUTPUT_DIR, params.MAPPED_OUTPUT_SUBDIR, "extractedPSID_Individual_Mapped_Recoded"), save=True)
