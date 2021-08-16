import pandas as pd
import os
import Replication.TimeSeriesAnalyzer as TimeSeriesAnalyzer

import PSIDProcessing.FamilyDataRecoder
from DataCleaningFunctions import * 
from Survey.SurveyFunctions import *
from scipy import stats

DEBUG_EDA = False

class InequalityAnalyzer(TimeSeriesAnalyzer.PSIDTimeSeriesAnalyzer):

    # Numeric Version    
    startYear = None
    endYear = None
    toYear = None
    
    # String Version    
    syStr = None
    eyStr = None
    tyStr = None

    useOriginalSampleOnly = False    
    
    familyFieldsWeNeedStartEnd = ['familyInterviewId', 
                                  'familyId1968',
                            'ChangeInCompositionFU',
                            'ChangeInCompositionFU_1989FiveYear',
                            'totalIncomeHH',
                            'NetWorthWithHome',# S217  / V17389/
                            'NetWorthWithHomeRecalc',
                            'NetWorthNoHome',
                                  
                            # Temp for Dynan Comparison
                            'NetWorth_1989Only', 
                            'NetWorth_1984_AsOf1989', 

                            'PovertyThreshold', 
                            'valueOfHouse_Debt',
                            'valueOfHouse_Gross',
                            'valueOfHouse_Net',
                            'valueOfVehicle_Net',
                            'valueOfCheckingAndSavings_Net',
                            'valueOfBrokerageStocks_Net',
                            'valueOfOtherAssets_Net',
                            'valueOfAllOtherDebts_Net',
                            'valueOfOtherRealEstate_Net',
                            'valueOfBusiness_Net',
                            
                            'largeGift_All_AmountHH',
                            'PersonMovedIn_SinceLastQYr_AssetsMovedIn', 'PersonMovedIn_SinceLastQYr_DebtsMovedIn',
                            'PersonMovedOut_SinceLastQYr_AssetsMovedOut', 'PersonMovedOut_SinceLastQYr_DebtsMovedOut',
                            'PrivateRetirePlan_SinceLastQYr_AmountMovedIn', 'PrivateRetirePlan_SinceLastQYr_AmountMovedOut',
                              
                            'CostOfMajorHomeRenovations',
                            'OtherRealEstate_SinceLastQYr_AmountBought',
                            'OtherRealEstate_SinceLastQYr_AmountSold',

                            'BrokerageStocks_SinceLastQYr_AmountBought',
                            'BrokerageStocks_SinceLastQYr_AmountSold',
                
                            'Business_SinceLastQYr_AmountBought',
                            'Business_SinceLastQYr_AmountSold',

                            'educationYearsR',
                            'martialStatusGenR',
                            'martialStatusR',
                            'NumChildrenInFU',
                            'raceR', 'raceS', 'ageR', 'genderR',
                            'FederalIncomeTaxesRS',
                            'FederalIncomeTaxesO',
                            'hasHouse',
                            'LongitudinalWeightHH',
                            'MovedR',
                            'ActiveSavings_PSID1989',
                              
                              # From TaxSim:
                             'fiitax',
                             'siitax'
                              ] 

    familyFieldsWeNeedMiddleYears = [
                            'familyInterviewId',
                            'familyId1968', 
                            'MovedR',
                            'ageR',
                            'hasHouse',
                            'NetWorthWithHome',
                            'NetWorthWithHomeRecalc',
                            'valueOfHouse_Gross',
                            'valueOfHouse_Debt',
                            'ChangeInCompositionFU',
                            'FederalIncomeTaxesRS',
                            'FederalIncomeTaxesO',  
                            'totalIncomeHH',  
                            'fiitax', 'siitax',
                            ]

    def setPeriod(self, startYear, endYear, toYear):
        self.startYear = startYear
        self.endYear = endYear
        self.toYear = toYear
        
        self.syStr = str(startYear)
        self.eyStr = str(endYear)
        self.tyStr = str(toYear)
    
        self.duration = endYear - startYear
        self.timespan = self.syStr + '_' + self.eyStr
        self.inflatedTimespan = self.syStr + '_' + self.eyStr + '_as_' + self.tyStr
        self.inflatedEnd = self.eyStr + '_as_' + self.tyStr
        self.inflatedStart = self.syStr + '_as_' + self.tyStr
        
        yearList = list(range(self.startYear, self.endYear +1))
        yearsFamilyDataCollected = list(range(1980, 1997+1, 1)) +  list(range(1999, 2019+2, 2))
        intersection = [value for value in yearList if value in yearsFamilyDataCollected] 
        self.yearsWithFamilyData = intersection
        
        if (endYear <= 1997):
            self.timeStep = 1
        else:
            self.timeStep = 2
            
        
    def generateSavingsDebugFields(self):
        fieldsToDiff =      ['valueOfHouse_Debt',
                            'valueOfHouse_Gross',
                            'valueOfVehicle_Net',
                            'valueOfCheckingAndSavings_Net',
                            'valueOfBrokerageStocks_Net',
                            'valueOfOtherAssets_Net',
                            'valueOfAllOtherDebts_Net']
        
        for field in fieldsToDiff:
            self.dta['debug_change' + field] = self.dta[field + '_' + self.syStr].sub(self.dta[field + '_' + self.syStr], fill_value=0)
         

    def clearData(self):
        self.dta = None

    
     

       
    def readData(self):

        individualData = pd.read_csv((self.indPath + ".csv"),low_memory=False)
        
        finalWaveAgeVar = "ageI_" + self.eyStr
        
        # Get head of household 
        finalYearSequenceVar = "sequenceNoI_" + self.eyStr
        individualData = individualData.loc[individualData[finalYearSequenceVar] == 1].copy()

        # if (self.useOriginalSampleOnly): 
        #     individualData = individualData.loc[(individualData.interviewId_1968 < 3000) | (individualData.interviewId_1968 > 5000 and (individualData.interviewId_1968 < 7000))].copy()
        
        # Note - there may be more than one family 
        individualData['constantFamilyId'] = range(1,(len(individualData)+1), 1)

        inidvidualVars = [finalWaveAgeVar, 'constantFamilyId', 'longitudinalWeightI_' + self.eyStr]
        
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
            yearData = familyDataForYear[theVars].copy()
            
            if (self.useOriginalSampleOnly): 
                yearData = yearData.loc[(yearData.familyId1968 < 3000) | ((yearData.familyId1968 > 5000) & (yearData.familyId1968 < 7000))].copy()
                
            yearData.columns = [(x + '_' + str(year)) for x in yearData.columns]
            indInterviewVar = "interviewId_" + str(year)
            dta = pd.merge(dta, yearData, right_on = 'familyInterviewId_'+ str(year), 
                                left_on = indInterviewVar, 
                                how = 'left')

            familyInterviewVars = familyInterviewVars + ['familyInterviewId_'+ str(year)]
        # TODO -- Drop any all blank-ones
        self.dta = dta.loc[~(dta[familyInterviewVars].isnull().all(axis=1))].copy()

    def calcIfMovedOrChangedHeadAtAnyPoint(self):    

        self.dta['MovedNotSure_' + self.timespan] = False
        self.dta['ChangeInCompositionFU_' + self.timespan] = False
        self.dta['ChangeInHeadFU_' + self.timespan] = False
        self.dta['ChangeInHeadSpouseComboFU_' + self.timespan] = False
        
        priorOwnRentStatus = None
        
        self.dta['House_ValueIncreaseOnMoving_' + self.timespan] = 0
        
        for year in (self.yearsWithFamilyData.copy()):
            movedVar = 'MovedR_' + str(year)
            housingStatusVar = 'hasHouse_' + str(year)

            if (self.dta[movedVar].sum() > 1): # ie not all nones

                # Flag if they aren't sure about moving                
                try:
                    self.dta.loc[(~(self.dta['MovedNotSure_' + self.timespan])) & (self.dta[movedVar].isna()), 'MovedNotSure_' + self.timespan] = True
                except:
                    print("Problem!")
                    raise Exception("Bad moving data")

                # Fix Moving Var for Contradictions
                if (year >= (self.startYear + self.timeStep)):
                    '''the dummy for whether a household moved between surveys was corrected 
                    for data contradictions as follows. 
                    If a head indicated they hadn’t moved during the prior year, 
                    yet they switched their own/rent status between consecutive years, 
                    we forced the move dummy to one (213 observations). 
                    Or if someone was a renter yet listed a value of a house, we set the house value and mortgage to zero (one observation.)
                    '''

                    numToUpdate = len(self.dta.loc[(self.dta[movedVar] == False) & (~(self.dta[housingStatusVar].isna())) & (~(priorOwnRentStatus.isna())) & (self.dta[housingStatusVar].ne(priorOwnRentStatus))])
                    print ("fixing " + str(numToUpdate) + " move statuses")
                    if (numToUpdate > 400):
                        print("something ain't right here")
                        
                    self.dta.loc[(self.dta[movedVar] == False) & (~(self.dta[housingStatusVar].isna())) & (~(priorOwnRentStatus.isna())) & (self.dta[housingStatusVar].ne(priorOwnRentStatus)), movedVar]= True

                    # if the person moved, add any changes in house value from the move
                    self.dta.loc[self.dta[movedVar] == True, 'House_ValueIncreaseOnMoving_' + self.timespan] = self.dta.loc[self.dta[movedVar] == True, 'House_ValueIncreaseOnMoving_' + self.timespan] \
                        .add(self.dta.loc[self.dta[movedVar] == True, 'valueOfHouse_Gross_' + str(year)], fill_value=0) \
                        .sub(self.dta.loc[self.dta[movedVar] == True, 'valueOfHouse_Gross_' + str(year-self.timeStep)], fill_value=0)
                                                         
                priorOwnRentStatus = self.dta[housingStatusVar].copy()

                
            else:
                raise Exception("Missing moving data")

            changeVar = 'ChangeInCompositionFU_' + str(year)

            if (year > self.startYear): # Look at move SINCE start, not from start to year prior
                if (self.dta[changeVar].sum() > 1): # ie not all nones
                    self.dta.loc[~(self.dta['ChangeInCompositionFU_' + self.timespan]) & ~(self.dta[changeVar].isin([0, 1])), 'ChangeInCompositionFU_' + self.timespan] = True
                    self.dta.loc[~(self.dta['ChangeInHeadFU_' + self.timespan]) & ~(self.dta[changeVar].isin([0, 1, 2])), 'ChangeInHeadFU_' + self.timespan] = True
                    self.dta.loc[~(self.dta['ChangeInHeadSpouseComboFU_' + self.timespan]) & (self.dta[changeVar].isin([2])), 'ChangeInHeadSpouseComboFU_' + self.timespan] = True




# Little helper function to place certain fields at begingging of DF, for easier review                
def selectiveReorder(dta, colsToPutFirst):
    new_columns = colsToPutFirst + (dta.columns.drop(colsToPutFirst).tolist())
    return dta[new_columns]
 
