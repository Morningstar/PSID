# import os
import re
import Survey.SurveyDataSummarizer as SurveyDataSummarizer

# Only uncomment when running the profiler below. Otherwise, simply including the package slows down the code considerably
# import pandas_profiling

def getCleanVarName_String(varName):
    varName = re.sub("_\d{4}_\d{4}_as_\d{4}$", "", varName)
    varName = re.sub("_\d{4}_\d{4}$", "", varName)
    varName = re.sub("_\d{4}$", "", varName)
    return varName


''' 
    This class looks for common problems with single-year PSID data. It should be used of the recoded, cleaned dataset - to see if there are outstanding issues to address.
    In particular it looks for 
    1) "Special Values" like 998 (commonly used for DK) and 999 (commonly used for No Answer) - which should have been switched to None or NA by this point.
    2) Columns that are all blank or all one value
    3) Columns that were included, but not mapped to a human meaningful name

    It then runs the surveydata summarizer to automatically spit out detailed summary stats on each var in the dataset, for manual review. 

    It has a tendency to over-warn: to provide warnings for things that aren't actually problems.
    That's for the better -- since a human should review the results to see which ones are actually a problem.
    You can also addd vars to (and rename) "steveWantsToTurnOffKnownMissings_ButYouMayNotWantTo" to silence some of those warnings.
    
'''

class CrossSectionalTester:

    invalidCodes = [
                              998,       999,
                             9998,      9999,
                            99998,     99999,
                           999998,    999999,
                          9999998,   9999999,
                         99999998,  99999999,
                        999999998, 999999999,
                       9999999998,9999999999,
                       ]
    
    likelyCodedValues = list(range(0,10+1,1))
    
    def __init__(self, dta, dfLabel, year, varMapping, ignoreUnmappedVars = False):
        '''

        :param dta: data with PSID family data
        :param dfLabel: name we want to use in error messages to describe this data
        :param year:  year of the PSID data
        :param varMapping: crosswalk data for variables
        :param ignoreUnmappedVars: what the name says
        '''
        
        self.steveWantsToTurnOffKnownMissings_ButYouMayNotWantTo = True  # If you're running this, and you're not the author, you probably want to see these errors.

        self.dta = dta
        self.dfLabel =dfLabel 
        self.year = year
        self.varMapping = varMapping
        self.ignoreUnmappedVars = ignoreUnmappedVars
        self.intentionallyUncodedColumns = self.getDefaultIntentionallyUncodedColumns()
        self.okToBeBlankColumns = self.getDefaultColumnsOkToBeBlank()
        self.okToBeUnmappedColumns = self.getDefaultUnmappedColumns()
        
    def setFilterColumms(self, intentionallyUncodedColumns, okToBeBlankColumns):
        self.intentionallyUncodedColumns = intentionallyUncodedColumns
        self.okToBeBlankColumns = self.okToBeBlankColumns

    def getDefaultUnmappedColumns(self):
        theVars = []
        if (self.year != 1989):
            theVars = theVars + ['NetWorth_1989Only', 'NetWorth_1984_AsOf1989', 'ChangeInCompositionFU_1989FiveYear']
            
        if (self.year > 1989):
            theVars = theVars + ['LargeGift_AllBut1_AmountHH_1989AndBefore']

        if (self.year < 2013): 
            theVars = theVars + ['PensionIncomeS_NonVet_2013to2017', 'valueOfBusiness_Net_2013on']
        else:
            theVars = theVars + ['valueOfBusiness_Net_pre2013']
        
        
        if (self.steveWantsToTurnOffKnownMissings_ButYouMayNotWantTo):
            if (self.year != 1989):
                theVars = theVars + ['ActiveSavings_PSID1989']
            
                
            if (self.year > 1992):
                theVars = theVars + ['FederalIncomeTaxesO', 'FederalIncomeTaxesRS']
            else:
                theVars = theVars + ['helpFromOthersRP', 'helpFromOthersSP']

            if (self.year < 1999):
                theVars = theVars + ['AgePlanToRetireR', 
                                     'FoodExpenseHH', 'TransportationExpenseHH', 'EducationExpenseHH', 'HealthcareExpenseHH']
            
            if (self.year < 2005):
                theVars = theVars + ['DividendsR', 'DividendsS', 
                                     'IRAIncomeR', 'IRAIncomeS', 
                                     'InterestIncomeR', 'InterestIncomeS']

            if (self.year < 2011):
                theVars = theVars + ['valueOfDebt_CreditCards_2011on', 'valueOfDebt_StudentLoans_2011on', 'valueOfDebt_MedicalBills_2011on',
                            'valueOfDebt_LegalBills_2011on',  'valueOfDebt_FamilyLoan_2011on']
            
            if (self.year < 2013):
                theVars = theVars + ['valueOfDebt_Other_2013on', 
                                      'valueOfOtherRealEstate_Debt_2013on', 'valueOfOtherRealEstate_Gross_2013on',
                                     'valueOfBusiness_Debt_2013on', 'valueOfBusiness_Gross_2013on',
                                     'AnnuityIncomeS', 'ClothingExpenseHH', 'TripsExpenseHH', 'OtherRecreationExpenseHH']

            
            if (self.year < 2017):
                theVars = theVars + ['ComputingExpenseHH']

        return theVars
            
                    
    def getDefaultIntentionallyUncodedColumns(self):
        theVars = [
            # Data we dont need to process here, but should be processed later
            'ChangeInCompositionFU', 'ChangeInCompositionFU_1989FiveYear',  
            # Data that looks coded but isnt (all values below 10)
            'NumChildrenInFU', 'NumOthersInHU', 'NumPeopleInFU',
            'Vehicle_CapitalGains', 'Checking_CapitalGains',
            'Home_SinceLastQYr_SoldYesNo', 'PersonMovedIn_SinceLastQYr_YesNo',
            'MadeMajorHomeRenovations',
            # Data that is special coding values in it (eg 99999) but those are valid values 
            'familyInterviewId', 'familyId1968', 'householdId', 
            'NetWorthWithHome', 'NetWorthNoHome',
            'NetWorth_1989Only', 'NetWorth_1984_AsOf1989',
            'valueOfHouse_Net',
            ]
     
        # In the 1994 wealth data the PSID added a (non representative) latino sample, and then dropped it again afterwards
        # Unfortunately, they repurposed prior codes ONLY for that year.  
        if self.year != 1994: # Yes, all of these were recoded for 1994
            theVars = theVars + ['taxableIncomeO', 
                'wageIncomeS', 'wageIncomeR', 'totalIncomeHH', 'taxableIncomeRandS', 
                'UnemploymentIncomeR', 'transferIncomeRandS', 'transferIncomeO']
                
        if self.year < 1991: 
            # Data that is special coding values in it (eg 99999) but those are valid values 
            theVars = theVars+ ['FederalIncomeTaxesRS', 'FederalIncomeTaxesO']

        if self.year == 1989:
            theVars = theVars + ['mortagePrincipal']
            
        if self.year <= 1991: 
            # Data that is special coding values in it (eg 99999) but those are valid values 
            theVars = theVars+ ['valueOfHouse_Gross']

        if (self.year < 1994):
            theVars = theVars+ ['HomePropertyTaxAnnualHH']

        return theVars
    
    def getDefaultColumnsOkToBeBlank(self):
        theVars = ['Vehicle_CapitalGains', 'Checking_CapitalGains'] # Put any columns that are ALWAYS Blank or all 0 here
        
        if self.year != 1989:
            theVars = theVars + ['ChangeInCompositionFU_1989FiveYear', 'NetWorth_1989Only']
        if self.year >= 1982 and self.year <= 1984:
            theVars = theVars + ['householdId']
            
        if self.year < 1994:
            theVars = theVars + ['IsWorking_SecondMentionR', 'IsWorking_Test2R', 'IsWorking_SecondMentionS', 'IsWorking_Test2S']
    
        if self.year < 1999:
            theVars = theVars + [
                'RetPlan_ReqEmployeeContrib_CalcedAnnualAmountR', 'RetPlan_VolEmployeeContrib_CalcedAnnualAmountR', 'RetPlan_EmployerContrib_CalcedAnnualAmountR', 
                'RetPlan2_EmployerContrib_CalcedAnnualAmountR',
                'RetPlan_ReqEmployeeContrib_CalcedAnnualAmountS', 'RetPlan_VolEmployeeContrib_CalcedAnnualAmountS', 'RetPlan_EmployerContrib_CalcedAnnualAmountS',
                'RetPlan2_EmployerContrib_CalcedAnnualAmountS']
        
        if self.year == 2015: 
            theVars = theVars + ['LargeGift_3_AmountHH_1994AndAfter'] # manually verified, all zero
        if self.year in [2005, 2007, 2013]: 
            theVars = theVars + ['OtherRetirementIncomeR'] # manually verified, all zero
    
        if (self.steveWantsToTurnOffKnownMissings_ButYouMayNotWantTo):
            theVars = theVars + ['CheckingAndSavings_CapitalGains']
            
        return theVars
    
        
    def unmapMappedVar(self,mappedVar):
        matching = self.varMapping.loc[(self.varMapping.year == self.year) & (self.varMapping.label == mappedVar),'varName']
        if (len(matching) == 1):
            val = str(matching.reset_index(drop=True)[0])
            if val != 'nan':
                return val
            else:
                return None
        elif (len(matching) > 1):
            return str(matching)
        else:
            # Is it a variable any OTHER year?
            matching = self.varMapping.loc[(self.varMapping.label == mappedVar),'varName']
            if (len(matching) >= 1):
                return None
            else:
                return 'CREATED'

    def reportOnUnMappedVars(self):
        # no variables should be all NA or any other value
        unmappedProblem = []
        unmappedOk = []
        for column in self.dta.columns:
            varName = self.unmapMappedVar(column)
            if (varName is None): 
                if ((len(self.okToBeUnmappedColumns) > 1) and (column in self.okToBeUnmappedColumns)):
                    unmappedOk = unmappedOk + [column]
                else:
                    unmappedProblem  = unmappedProblem + [column]
                
        unmappedProblem.sort()
        print("The following variables are unmapped for year " + str(self.year) + ": " + str(unmappedProblem))
        return (unmappedProblem + unmappedOk)
        
    ''' Helper function to look for bad data'''
    def checkDataQuality(self, raiseIfMissing = False):
        dta = self.dta
        # no variables should be all NA or any other value
        badColumns = {}
        for column in dta.columns:
            cleanColumnName = getCleanVarName_String(column)
            
            varNameUnMapped = False
            if self.varMapping is not None:
                varName = self.unmapMappedVar(cleanColumnName)
                if (varName is not None):
                    colLabel = column + " (" + varName + ")"
                else:
                    colLabel = column
                    varNameUnMapped = True
            else: 
                colLabel = column
                
            try:
                numUnique = len(dta[column].unique())
            except:
                numUnique = 0;
                
            if ( (len(self.okToBeBlankColumns) == 0) or (cleanColumnName not in self.okToBeBlankColumns)):
                if (dta[column].isna().all() or dta[column].isnull().all() or dta[column].isin(['nan']).all()):
                    if (varNameUnMapped):
                        if (self.ignoreUnmappedVars):                   
                            None
                        else:                   
                            badColumns[colLabel] = 'Unmapped'
                    else:
                        badColumns[colLabel] = 'All NA'
                elif (numUnique < 2):
                    if (varNameUnMapped):
                        if (self.ignoreUnmappedVars):                   
                            None
                        else:                   
                            badColumns[colLabel] = 'Unmapped & all one value (' + str(dta[column].unique()[0]) + ')'
                    else:
                        badColumns[colLabel] = 'All one value (' + str(dta[column].unique()[0]) + ')'
                    
            if ( (len(self.intentionallyUncodedColumns) == 0) or (cleanColumnName not in self.intentionallyUncodedColumns)): 
                if (dta[column].isin(self.invalidCodes).any()):
                    # A little more fine grained -- some of the large wealth values have codes, then lower levels are ok.
                    # Let's look for those Top-level ones only
                    maxVal = dta[column].max()
                    if maxVal in self.invalidCodes:
                        badColumns[colLabel] = 'Likely invalid data (uncoded Dont knows or NAs)'
                    else:
                        invalidAboveMax = [x for x in self.invalidCodes if x > maxVal]
                        if (dta[column].isin(invalidAboveMax).any()):
                            badColumns[colLabel] = 'Likely invalid data (uncoded Dont knows or NAs)'
                        else:
                            None
                elif ((dta[column].dtypes.name != 'bool') and (dta[column].dtypes.name != 'boolean') and (dta[column].isin(self.likelyCodedValues).all())):
                    badColumns[colLabel] = 'All values are below 10 - likely data that hasnt been recoded'
                
        if (len(badColumns) > 0):
            formattedColList = str(badColumns)
            if raiseIfMissing:
                raise Exception("Bad data in column(s) on dataframe " + self.dfLabel + ": " + formattedColList)
            else:
                print("Bad data in column(s) on dataframe " + self.dfLabel + ": " + formattedColList)


    def exploreData(self, reportFileNameWithPathNoExtension, weightVar = None, doFancy=True):

        # Fancy
        if doFancy:
            sds = SurveyDataSummarizer.SurveyDataSummarizer(self.dta, weightField = weightVar, fieldMetaData=None, fieldsToSummarize=None, fieldsToCrossTab=None)
            sds.doIt(reportFileNameWithPathNoExtension + "_Describe" +'.xlsx')

        # And Simple
        results = self.dta.describe()
        # print("EDA Analysis of " + self.dfLabel)
        # print(results)
        if reportFileNameWithPathNoExtension is not None:
            results.to_csv(reportFileNameWithPathNoExtension + "_Describe.csv")
        
        return results


