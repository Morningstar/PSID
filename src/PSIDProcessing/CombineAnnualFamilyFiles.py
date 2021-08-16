import os
import pandas as pd

class CombineAnnualFamilyFiles:
    '''
    CombineAnnualFamilyFiles traces a set of individuals over in the PSID and picks up the
     annual wealth files for the family those individuals are in at each time period.

     This may mean that the same household wealth is represented MULTIPLE TIMES in a given year -
     if the set of individuals is in the same houshold
    '''

    def __init__(self,
                 baseDir, familyInputSubDir, familyBaseName,
                 individualInputSubDir, individualBaseName,
                 outputSubDir,  outputBaseName):

        # When do we have detailed wealth data in the PSID?
        self.yearsWealthDataCollected = [1984, 1989, 1994] + list(range(1999, 2019+2, 2))
        self.yearsFamilyDataCollected = list(range(1980, 1997+1, 1)) +  list(range(1999, 2019+2, 2))

        self.baseDir = baseDir
        self.outputSubDir = outputSubDir
        self.outputBaseName = outputBaseName

        self.famPath = os.path.join(baseDir, familyInputSubDir, familyBaseName)
        self.indPath = os.path.join(baseDir, individualInputSubDir, individualBaseName)

        self.individualData = None
        self.familyFieldsWeNeed_MiddleYears = None
        self.familyFieldsWeNeed_WealthYears = None
        self.getAllFamilyDataFields = None
        self.startYear = None
        self.endYear = None
        self.syStr = None
        self.eyStr = None
        self.yearList = None
        self.duration = None
        self.includeNonWealthYears = None
        self.individualFieldsWeNeed = None
        self.whoToTrace = None
        self.useOriginalSampleOnly = None
        self.dta = None
        self.familyDataHasYearSuffix = None

        self.hasInflatedData = self.tyStr = self.inflatedTimeSpan = None;

    def readIndividualData(self):
        self.individualData = pd.read_csv((self.indPath + ".csv"),low_memory=False)
        # Hack to fix some missing data
        for year in range(1984, 1997, 1):
           self.individualData['crossSectionalWeightI_' + str(year)] = None


    def getIndividualData(self):
        return self.individualData

    def setPeriod(self, startYear, endYear, inflatedToYear = None, includeNonWealthYears=True):
        self.includeNonWealthYears = includeNonWealthYears

        # Numeric Version
        self.startYear = startYear
        self.endYear = endYear

        # String Version
        self.syStr = str(startYear)
        self.eyStr = str(endYear)
        self.duration = endYear - startYear
        self.timeSpan = self.syStr + '_' + self.eyStr

        if inflatedToYear is not None:
            self.hasInflatedData = True
            self.tyStr = str(inflatedToYear)
            self.inflatedTimeSpan = self.syStr + '_' + self.eyStr + '_as_' + self.tyStr
        else:
            self.hasInflatedData = False

        # Years to gather:
        yearList = list(range(self.startYear, self.endYear +1))
        if (includeNonWealthYears):
            intersection = [value for value in yearList if value in self.yearsFamilyDataCollected]
        else:
            intersection = [value for value in yearList if value in self.yearsWealthDataCollected]

        self.yearList = intersection

    def createListOfIndividualVars(self):
        tempIndivFields = self.individualFieldsWeNeed
        # We need the interview field regardless of what the user asked for
        if 'interviewId' not in tempIndivFields:
            tempIndivFields = tempIndivFields + ['interviewId']

        # The location vars are special and only available for 2 years.  Filter for them.
        hasLocation = False
        if 'stateBornI' in tempIndivFields:
            tempIndivFields.remove('stateBornI')
            hasLocation = True
        if 'countryBornI' in tempIndivFields:
            tempIndivFields.remove('countryBornI')
            hasLocation = True
        if 'livedInUSIn68I' in tempIndivFields:
            tempIndivFields.remove('livedInUSIn68I')
            hasLocation = True


        individualVars = [f'{a}_{str(b)}' for a in tempIndivFields for b in self.yearList]

        if hasLocation:
            if self.startYear <= 1997 <= self.endYear:
                individualVars = individualVars + ['stateBornI_1997', 'countryBornI_1997', 'livedInUSIn68I_1997']
            if self.startYear <= 1999 <= self.endYear:
                individualVars = individualVars + ['stateBornI_1999', 'countryBornI_1999', 'livedInUSIn68I_1999']

        individualVars = individualVars + ['constantIndividualID']

        return individualVars

    def readAndCombineData(self, listOfIndividualIds=None):

        if (self.individualData is None):
            self.readIndividualData()

        # Start with the individual level data for households at the start of the period
        # We're going to trace that person through households for each year
        startYearSequenceVar = "sequenceNoI_" + self.syStr
        startFamilyInterviewVar = "interviewId_" + self.syStr
        startRelationshipVar = "relationshipToR_" + self.syStr

        if (self.whoToTrace == 'List'):
            individualsToTrace = self.individualData.loc[self.individualData.constantIndividualID.isin(listOfIndividualIds)].copy()
        elif (self.whoToTrace == 'ReferencePerson'):
            # See note in individual file -- because of how HH changes are handled, you need the sequence number
            individualsToTrace = self.individualData.loc[(self.individualData[startYearSequenceVar] == 1) & (self.individualData[startRelationshipVar] == 'RP')].copy()
        elif (self.whoToTrace == 'Spouse'):
            individualsToTrace = self.individualData.loc[(self.individualData[startYearSequenceVar] < 60) & (self.individualData[startRelationshipVar] == 'Partner')].copy()
        elif (self.whoToTrace == 'RPandSpouse'):
            individualsToTrace = self.individualData.loc[(self.individualData[startYearSequenceVar] < 60) & (self.individualData[startRelationshipVar].isin(['RP', 'Partner']))].copy()
        elif (self.whoToTrace == 'All'):
            individualsToTrace = self.individualData.loc[(self.individualData[startYearSequenceVar] < 60)].copy()

        if (self.useOriginalSampleOnly):
            individualsToTrace = individualsToTrace.loc[(individualsToTrace.interviewId_1968 < 3000) |
                                                    (individualsToTrace.interviewId_1968 > 5000 and (individualsToTrace.interviewId_1968 < 7000))].copy()

        individualVars = self.createListOfIndividualVars()

        # Start the new dataframe off with our individual vars.  This is also what we need to join to the family data for each year
        dta = individualsToTrace[individualVars].copy()

        familyInterviewVars = []
        relationshipVars = []

        for year in (self.yearList):

            yrStr = str(year)

            # Bring in this year of family data
            if self.hasInflatedData:
                yearFamilyData = pd.read_csv((self.famPath  + str(year) + '_as_' + self.tyStr + ".csv"),low_memory=False)
            else:
                yearFamilyData = pd.read_csv((self.famPath  + str(year) + ".csv"),low_memory=False)

            # Extract the fields we need
            if self.getAllFamilyDataFields:
                famVars = list(yearFamilyData.columns.copy())
            else:
                if (self.includeNonWealthYears) and (year not in self.yearsWealthDataCollected):
                    famFields= self.familyFieldsWeNeed_MiddleYears
                else:
                    famFields= self.familyFieldsWeNeed_WealthYears

                if self.familyDataHasYearSuffix:
                    famVars = [f'{a}_{yrStr}' for a in famFields]
                    if ('familyInterviewId'+ yrStr) not in famVars: # We absolutely need this for merging
                        famVars = famVars + ['familyInterviewId'+ yrStr]
                else:
                    famVars = famFields
                    if ('familyInterviewId') not in famVars:
                        famVars = famVars + ['familyInterviewId']

            yearFamilyData = yearFamilyData[famVars].copy()

            # If we don't already have year suffixes, we need them to join the data together
            if not self.familyDataHasYearSuffix:
                yearFamilyData.columns = [f'{a}_{yrStr}' for a in yearFamilyData.columns]

            indInterviewVar = "interviewId_" + str(year)
            dta = pd.merge(dta, yearFamilyData, left_on = indInterviewVar, right_on = 'familyInterviewId_'+ str(year), how = 'left')

            familyInterviewVars = familyInterviewVars + ['familyInterviewId_'+ str(year)]
            relationshipVars = relationshipVars + ['relationshipToR_'+ str(year)]

        # flag Individuals By Duration in the dataset
        familyInterviewVar_Start = 'familyInterviewId_'+ self.syStr
        familyInterviewVar_End = 'familyInterviewId_'+ self.eyStr

        dta['DurationInDataset'] = 'UNK'
        dta.loc[(dta[familyInterviewVars].isnull().all(axis=1)), 'DurationInDataset'] = 'Missing In All'
        dta.loc[~(dta[familyInterviewVars].isnull().any(axis=1)), 'DurationInDataset'] = 'Present In All'
        dta.loc[(dta.DurationInDataset=='UNK') & (dta[familyInterviewVar_Start].isnull())
            & (dta[familyInterviewVar_End].isnull()), 'DurationInDataset'] = 'Missing at Start and End'
        dta.loc[(dta.DurationInDataset=='UNK') & (dta[familyInterviewVar_Start].isnull()), 'DurationInDataset'] = 'Missing at Start'
        dta.loc[(dta.DurationInDataset=='UNK') & (dta[familyInterviewVar_End].isnull()), 'DurationInDataset'] = 'Missing at End'
        dta.loc[(dta.DurationInDataset=='UNK'), 'DurationInDataset'] = 'Missing in Middle'

        # dta.DurationInDataset.value_counts()

        dta['RelationshipOverDuration'] = 'Other'
        dta.loc[(dta[relationshipVars].fillna("RP").isin(["RP","Partner"]).all(axis=1)), 'RelationshipOverDuration'] = 'Always RP or Partner'
        dta.loc[(dta[relationshipVars].fillna("RP").eq("RP").all(axis=1)), 'RelationshipOverDuration'] = 'Always RP'
        dta.loc[(dta[relationshipVars].fillna("Partner").eq("Partner").all(axis=1)), 'RelationshipOverDuration'] = 'Always Partner'
        dta.loc[(dta[relationshipVars].fillna("Child").eq("Child").all(axis=1)), 'RelationshipOverDuration'] = 'Child'

        dta.RelationshipOverDuration.value_counts()

        self.dta = dta[dta.DurationInDataset != 'Missing In All'].copy()



        return self.dta




    def saveCombinedData(self):
        self.dta.to_csv(os.path.join(self.baseDir, self.outputSubDir, self.outputBaseName + '_' + self.inflatedTimeSpan + ".csv"), index=False)


    def doIt(self, startYear, endYear, toYear, varsToKeep_Individual, varsToKeep_Family_WealthYears = None, varsToKeep_Family_NonWealthYears = None,
             useOriginalSampleOnly = False, whoToTrace = "ReferencePerson",
             includeNonWealthYears = False, familyDataHasYearSuffix = True):
        self.whoToTrace = whoToTrace # can be 'ReferencePerson', 'RPandSpouse', or 'All'
        self.useOriginalSampleOnly = useOriginalSampleOnly
        self.familyDataHasYearSuffix = familyDataHasYearSuffix
        self.familyFieldsWeNeed_MiddleYears = varsToKeep_Family_NonWealthYears
        self.familyFieldsWeNeed_WealthYears = varsToKeep_Family_WealthYears

        if includeNonWealthYears:
            if (self.familyFieldsWeNeed_MiddleYears is not None) and (self.familyFieldsWeNeed_WealthYears is not None):
                self.getAllFamilyDataFields = False
            elif (self.familyFieldsWeNeed_MiddleYears is None) and (self.familyFieldsWeNeed_WealthYears is None):
                self.getAllFamilyDataFields = True
            else:
                raise Exception("Problem: missing list of family data fields to extract")
        else:
            self.getAllFamilyDataFields = (self.familyFieldsWeNeed_WealthYears is None)

        self.individualFieldsWeNeed = varsToKeep_Individual
        self.setPeriod(startYear, endYear, toYear, includeNonWealthYears)
        self.readAndCombineData()

        self.saveCombinedData()



''' Allow execution from command line, etc'''
if __name__ == "__main__":
    analyzer = CombineAnnualFamilyFiles(
        baseDir = 'C:/dev/sensitive_data/InvestorSuccess/Inequality',
        familyInputSubDir = 'inequalityInput_enrichedPop',
        familyBaseName = 'YearData_',
        individualInputSubDir = 'mappedAndrecodedPSID',
        individualBaseName = 'extractedPSID_Individual_Mapped_Recoded',
        outputSubDir = 'inequalityOutput_enrichedPop',
        outputBaseName = 'wealthAcrossTime'
    )

    individualFields  = ['ageI', 'sequenceNoI', 'relationshipToR', 'stateBornI', 'countryBornI', 'livedInUSIn68I', 'longitudinalWeightI', 'crossSectionalWeightI']

    familyFieldsWeNeedStartEnd = ['familyInterviewId', 'familyId1968',
                            'ChangeInCompositionFU', 'ChangeInCompositionFU_1989FiveYear',
                            'totalIncomeHH',
                            'NetWorthWithHome', 'NetWorthWithHomeRecalc',
                            'NetWorthNoHome', 'NetWorthWithHomeAnd401k',

                            'PovertyThreshold',
                            'valueOfHouse_Debt', 'valueOfHouse_Gross', 'valueOfHouse_Net',
                            'valueOfVehicle_Net', 'valueOfCheckingAndSavings_Net', 'valueOfBrokerageStocks_Net',
                            'valueOfOtherAssets_Net', 'valueOfAllOtherDebts_Net', 'valueOfOtherRealEstate_Net', 'valueOfBusiness_Net',
                            'valueOfPrivateRetirePlan_Gross', 'valueOfEmployerRetirePlan_Gross',
                            'retirementContribRateR','retirementContribRateS', 'retirementContribHH',

                            'largeGift_All_AmountHH', 'SmallGift_All_AmountHH',
                            'PersonMovedIn_SinceLastQYr_AssetsMovedIn', 'PersonMovedIn_SinceLastQYr_DebtsMovedIn',
                            'PersonMovedOut_SinceLastQYr_AssetsMovedOut', 'PersonMovedOut_SinceLastQYr_DebtsMovedOut',
                            'PrivateRetirePlan_SinceLastQYr_AmountMovedIn', 'PrivateRetirePlan_SinceLastQYr_AmountMovedOut',

                            'CostOfMajorHomeRenovations',
                            'OtherRealEstate_SinceLastQYr_AmountBought', 'OtherRealEstate_SinceLastQYr_AmountSold',
                            'BrokerageStocks_SinceLastQYr_AmountBought', 'BrokerageStocks_SinceLastQYr_AmountSold',
                            'Business_SinceLastQYr_AmountBought', 'Business_SinceLastQYr_AmountSold',

                            'educationYearsR',
                            'martialStatusGenR', 'martialStatusR',
                            'NumChildrenInFU',
                            'raceR', 'raceS', 'ageR', 'genderR',

                            'institutionLocationHH',
                            'inMixedRaceCouple',
                            'surveyInclusionGroup',
                            'genderOfPartners',
                            'householdStructure',

                            'stateH', 'stateH_SOI', 'stateH_FIPS',
                            'regionH','isMetroH', 'metroSizeH','sizeLargestCityH',
                            'regionGrewUpR','geoMobilityR','regionGrewUpS','geoMobilityS',
                            'stateGrewUpR', 'stateGrewUpS',

                            'hasHouse', 'hasOtherRealEstate', 'hasVehicle', 'hasBrokerageStocks',
                            'hasCheckingAndSavings', 'hasBusiness', 'hasOtherAssets', 'hasEmployerRetirePlan',
                            'hasPrivateRetirePlan', 'hasAllOtherDebts',

                            'LongitudinalWeightHH',
                            'MovedR',
                            'ActiveSavings_PSID1989',

                            'IsWorkingR', 'IsWorkingS',
                            'reasonLeftLastJobR', 'reasonLeftLastJobS',
                            'RetPlan_IsEligibleR', 'RetPlan_IsParticipatingR',
                            'RetPlan_IsEligibleS', 'RetPlan_IsParticipatingS',
                            'RetPlan_TypeR', 'RetPlan_TypeS',

                            'FederalIncomeTaxesRS', 'FederalIncomeTaxesO',
                              # From TaxSim:
                             'fiitax', 'siitax'
                            ]

    familyFieldsWeNeedMiddleYears = [
                            'familyInterviewId', 'familyId1968',
                            'MovedR', 'ChangeInCompositionFU',
                            'ageR','educationYearsR', 'martialStatusR',
                            'retirementContribRateR','retirementContribRateS', 'retirementContribHH',
                            'totalIncomeHH',  'institutionLocationHH',
                            'hasHouse',
                            'valueOfHouse_Gross', 'valueOfHouse_Debt',
                            'FederalIncomeTaxesRS', 'FederalIncomeTaxesO', 'fiitax', 'siitax',
                            ]

    analyzer.doIt(1989, 1999, 2019, varsToKeep_Individual=individualFields,
            varsToKeep_Family_WealthYears=None,
            varsToKeep_Family_NonWealthYears=None,
            useOriginalSampleOnly = False,
            whoToTrace = "ReferencePerson",
            includeNonWealthYears = False, familyDataHasYearSuffix= True)

    analyzer.doIt(1999, 2009, 2019, varsToKeep_Individual=individualFields,
            varsToKeep_Family_WealthYears=None,
            varsToKeep_Family_NonWealthYears=None,
            useOriginalSampleOnly = False,
            whoToTrace = "ReferencePerson",
            includeNonWealthYears = False, familyDataHasYearSuffix= True)

    analyzer.doIt(2009, 2019, 2019, varsToKeep_Individual=individualFields,
            varsToKeep_Family_WealthYears=None,
            varsToKeep_Family_NonWealthYears=None,
            useOriginalSampleOnly = False,
            whoToTrace = "ReferencePerson",
            includeNonWealthYears = False, familyDataHasYearSuffix= True)

    '''
    analyzer.doIt(1999, 2019,2019, varsToKeep_Individual=individualFields,
            varsToKeep_Family_WealthYears=familyFieldsWeNeedStartEnd,
            varsToKeep_Family_NonWealthYears=familyFieldsWeNeedMiddleYears,
            useOriginalSampleOnly = False,
            whoToTrace = "ReferencePerson")
    '''