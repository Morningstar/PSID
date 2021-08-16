import os
from Survey.SurveyFunctions import *
import Inflation.CPI_InflationReader as CPI_InflationReader
import MStarReport.InequalityAnalysisBase as InequalityAnalysisBase



class CrossYearDataFillin(InequalityAnalysisBase.InequalityAnalysisBase):
    '''
    This class uses the data across time available in the PSID for the same person to fill in missing or unknown information in a given year.
    For example - race. If in one year someone says 'Asian', and in another year someone says 'Unknown',
    we can reasonably assume that they are Asian in the latter year as well.
    Similarly, for Age (should monotonically increase), Gender, and Education (Education shouldn't decrease)

    '''

    familyFieldsWeNeedMiddleYears = [
                            'familyInterviewId', 'familyId1968',
                            'raceR', 'raceS', 'ageR',
                            'genderR',
                            'MovedR',
                            'ChangeInCompositionFU',
                            'educationYearsR',  # ER30010
                            'martialStatusR',
                            'retirementContribRateR','retirementContribRateS', 'retirementContribHH',
                            'totalIncomeHH',
                            'hasHouse',
                            ]

    def __init__(self, baseDir, familyInputSubDir, familyBaseName, individualInputSubDir, individualBaseName, outputSubDir,
                 inputBaseName, outputBaseName,  useOriginalSampleOnly):

        super().__init__(baseDir, inputSubDir = familyInputSubDir,
                         inputBaseName = inputBaseName,outputBaseName = outputBaseName, outputSubDir = outputSubDir)

        self.famPath = os.path.join(baseDir, familyInputSubDir, familyBaseName)
        self.indPath = os.path.join(baseDir, individualInputSubDir, individualBaseName)

        self.useOriginalSampleOnly = useOriginalSampleOnly

        self.inflator = CPI_InflationReader.CPIInflationReader()

    def fillInDemographics(self, yr):
        # from the first time we have data on demographic fields, fill in missing values in the future
        # and ideally, backfill as well.
        # Race, Age, Gender
        None


    def fillInAccountValues(self, yr):
        # from the start of each account - when the person first has it,
        # keep track of flow & cap gains additions.
        # fill in missing balances when they exist.
        # This is ESPECIALLY a problem for 401ks and IRAs
        None

    def getFamilySumOfCSWeights(self, yr):
        sequenceVar = "sequenceNoI_" + yr
        indInterviewVar = "interviewId_" + yr

        inidvidualVars = ['crossSectionalWeightI_' + yr, 'longitudinalWeightI_' + yr, indInterviewVar]
        # individualData_NonHead = self.psidIndividualDta.loc[self.psidIndividualDta[sequenceVar] != 1, inidvidualVars].copy()
        # individualData_NonHead = individualData_NonHead.loc[(~(individualData_NonHead[ageVar].isna())) & (individualData_NonHead[relationshipVar].isin(['Child']))].copy()

        '''
        temp = pd.merge(dta[['familyInterviewId']],
                       individualData_NonHead, left_on = 'familyInterviewId',
                            right_on = indInterviewVar,
                            how = 'left')

        results = temp.groupby(['familyInterviewId']).apply(calcAgeCounts, self.year).reset_index()
        return results
        '''

    def readRawData(self):
        '''
        The main function to read each year of single-year PSID data, clean it, and save the resulting single-year files
        :return:
        :rtype:
        '''

        individualData = pd.read_csv((self.indPath + ".csv"),low_memory=False)

        finalWaveAgeVar = "ageI_" + self.eyStr

        # Get head of household
        finalYearSequenceVar = "sequenceNoI_" + self.eyStr
        finalFamilyInterviewVar = "interviewId_" + self.eyStr
        individualData = individualData.loc[individualData[finalYearSequenceVar] == 1].copy()

        # if (self.useOriginalSampleOnly):
        #     individualData = individualData.loc[(individualData.interviewId_1968 < 3000) | (individualData.interviewId_1968 > 5000 and (individualData.interviewId_1968 < 7000))].copy()

        # Note - there may be more than one family
        individualData['constantFamilyId'] = range(1,(len(individualData)+1), 1) #
        # individualData['constantFamilyId'] = individualData[finalFamilyInterviewVar]
        # if (len(individualData)+1) !=  individualData['constantFamilyId'].unique()):
        #         raise Except("Final Year Interview Id for Head of Household isn't a unique id for all rows")


        inidvidualVars = [finalWaveAgeVar, 'constantFamilyId', 'constantIndividualID',
                          'longitudinalWeightI_' + self.eyStr] + \
                         ['stateBornI_1997','stateBornI_1999'] + \
                         ['countryBornI_1997','countryBornI_1999'] + \
                         ['livedInUSIn68I_1997','livedInUSIn68I_1999']

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
            self.yearData = familyDataForYear[theVars].copy()
            self.yearDataYear= year

            self.yearData.columns = [(x + '_' + str(year)) for x in self.yearData.columns]

            # Clean it, Inflate it, save it.
            self.processCrossSectionalData()

            self.yearData = InequalityAnalysisBase.selectiveReorder(self.yearData,
                                                                    ['familyInterviewId_' + str(self.yearDataYear),
                                                                'familyId1968_' + str(self.yearDataYear),
                                                                'ChangeInCompositionFU_' + str(self.yearDataYear),
                                                                'cleaningStatus_' + str(self.yearDataYear),
                                                                 'modificationStatus_' + str(self.yearDataYear),
                                                                 ],
                                                                    alphabetizeTheOthers = True)
            self.saveCrossSectionalData(self.yearData, self.yearDataYear)

            indInterviewVar = "interviewId_" + str(year)
            dta = pd.merge(dta, self.yearData, right_on = 'familyInterviewId_'+ str(year),
                                left_on = indInterviewVar,
                                how = 'left')

            familyInterviewVars = familyInterviewVars + ['familyInterviewId_'+ str(year)]

        # TODO -- Drop any all blank-ones
        self.dta = dta.loc[~(dta[familyInterviewVars].isnull().all(axis=1))].copy()


    def calcIfValueOnMoveAndChangedHeadAtAnyPoint(self):

        modificationVar = 'modificationStatus_' + self.timespan
        self.dta[modificationVar] = ''

        self.dta['ChangeInHeadFU_' + self.timespan] = False

        # Changes on Move
        self.dta['House_ValueIncrease_WhenMoving_' + self.inflatedTimespan] = 0
        self.dta['House_TotalChangeInMortgageDebt_WhenMoving_' + self.inflatedTimespan] = 0

        # Changes without Move
        self.dta['House_TotalChangeInMortgageDebt_WhenNotMoving_' + self.inflatedTimespan] = 0
        self.dta['House_ValueIncrease_WhenNotMoving_' + self.inflatedTimespan] = 0
        priorOwnRentStatus = None


        for year in (self.yearsWithFamilyData.copy()):
            inflationPriorYear =  self.inflator.getInflationFactorBetweenTwoYears(year-self.timeStep, self.toYear)
            inflationGivenYear =  self.inflator.getInflationFactorBetweenTwoYears(year, self.toYear)
            movedVar = 'MovedR_' + str(year)
            housingStatusVar = 'hasHouse_' + str(year)

            if (year >= (self.startYear + self.timeStep)):

                # Following Dynan, flag people who moved but didn't report it
                mask = (self.dta[movedVar] == False) & (~(self.dta[housingStatusVar].isna())) & (~(priorOwnRentStatus.isna())) & (self.dta[housingStatusVar].ne(priorOwnRentStatus))

                numToUpdate = len(self.dta.loc[mask])
                print ("fixing " + str(numToUpdate) + " move statuses")
                if (numToUpdate > 400):
                    warnings.warn("something ain't right here")

                self.dta.loc[mask, modificationVar] = self.dta.loc[mask, modificationVar] + "Move Status Changed to True;"
                self.dta.loc[mask, movedVar]= True

                # if the person moved, add any changes in house value from the move
                if (self.dta[movedVar].sum() >= 1): # ie not all nones
                    self.dta.loc[self.dta[movedVar] == True, 'House_ValueIncrease_WhenMoving_' + self.inflatedTimespan] = self.dta.loc[self.dta[movedVar] == True, 'House_ValueIncrease_WhenMoving_' + self.inflatedTimespan] \
                        .add(self.dta.loc[self.dta[movedVar] == True, 'valueOfHouse_Gross_' + str(year)] * inflationGivenYear, fill_value=0) \
                        .sub(self.dta.loc[self.dta[movedVar] == True, 'valueOfHouse_Gross_' + str(year-self.timeStep)] * inflationPriorYear, fill_value=0)

                    self.dta.loc[ (self.dta[movedVar] == True), 'House_TotalChangeInMortgageDebt_WhenMoving_' + self.inflatedTimespan] = self.dta.loc[ (self.dta[movedVar] == True), 'House_TotalChangeInMortgageDebt_WhenMoving_' + self.inflatedTimespan] \
                        .add(self.dta.loc[ (self.dta[movedVar] == True), 'valueOfHouse_Debt_' + str(year)] * inflationGivenYear, fill_value=0) \
                        .sub(self.dta.loc[ (self.dta[movedVar] == True), 'valueOfHouse_Debt_' + str(year-self.timeStep)] * inflationPriorYear, fill_value=0)

                else:
                    raise Warning("Hmm... Missing moving data")

                # if the person DIDN'T MOVE, add up the cumulative changes in principal and house value
                self.dta.loc[ ~(self.dta[movedVar] == True), 'House_ValueIncrease_WhenNotMoving_' + self.inflatedTimespan] = self.dta.loc[ ~(self.dta[movedVar] == True), 'House_ValueIncrease_WhenNotMoving_' + self.inflatedTimespan] \
                    .add(self.dta.loc[ ~(self.dta[movedVar] == True), 'valueOfHouse_Gross_' + str(year)] * inflationGivenYear, fill_value=0) \
                    .sub(self.dta.loc[ ~(self.dta[movedVar] == True), 'valueOfHouse_Gross_' + str(year-self.timeStep)] * inflationPriorYear, fill_value=0)
                self.dta.loc[ ~(self.dta[movedVar] == True), 'House_TotalChangeInMortgageDebt_WhenNotMoving_' + self.inflatedTimespan] = self.dta.loc[ ~(self.dta[movedVar] == True), 'House_TotalChangeInMortgageDebt_WhenNotMoving_' + self.inflatedTimespan] \
                    .add(self.dta.loc[ ~(self.dta[movedVar] == True), 'valueOfHouse_Debt_' + str(year)] * inflationGivenYear, fill_value=0) \
                    .sub(self.dta.loc[ ~(self.dta[movedVar] == True), 'valueOfHouse_Debt_' + str(year-self.timeStep)] * inflationPriorYear, fill_value=0)

            priorOwnRentStatus = self.dta[housingStatusVar].copy()

            if (year > self.startYear): # Look at changes in composition SINCE start, not from start to year prior
                changeVar = 'ChangeInCompositionFU_' + str(year)
                if (self.dta[changeVar].sum() > 1): # ie not all nones
                    self.dta.loc[~(self.dta['ChangeInHeadFU_' + self.timespan]) & ~(self.dta[changeVar].isin([0, 1, 2])), 'ChangeInHeadFU_' + self.timespan] = True




    def doIt(self, yearsToInclude):
        toYear = 2019

        self.setPeriod(yearsToInclude[0], yearsToInclude[len(yearsToInclude)-1], toYear)
        self.readRawData()


        for endYear in self.yearsWealthDataCollected[1:]:
            # Do the core analysis: change in wealth and savings rates over time
            self.executeForTimespan(startYear, endYear, toYear)
            # Get ready for next year
            startYear = endYear



''' Allow execution from command line, etc'''
if __name__ == "__main__":
    analyzer = CrossYearDataFillin(familyBaseFileNameWithPath =
                             os.path.join('C:/dev/sensitive_data/InvestorSuccess/Inequality',
                                          'finalInputPSID', "extractedPSID_Mapped_Recoded_"),
            individualBaseFileNameWithPath = os.path.join('C:/dev/sensitive_data/InvestorSuccess/Inequality',
                                          'finalInputPSID', "extractedPSID_Individual_Mapped_Recoded"))
    analyzer.doIt()

