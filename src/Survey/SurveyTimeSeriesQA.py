import re
from Survey.SurveyFunctions import *
from pandas.api.types import is_numeric_dtype, is_bool_dtype
from Survey.SurveyDataSummarizer import SurveyDataSummarizer
import os

''' 
    This class takes time series data and analyzes variables of interest (or ALL variables in a dataset) for two potential problems: 
        Large shifts in the median value of each variable of interest
        Lrage shifts in the -individual- value of each variable of interest, by family.
    Then, it takes the resulting output variables and creates a large summary Excel doc, one sheet per new var, for manual review 
        
    It takes time serieses in WIDE format, of the names: VARNAME_YEAR
'''

class SurveyTimeSeriesQA:

    def __init__(self, dta, dfLabel, baseDir, outputDir, isWeighted = False, weightVar = None, raiseOnError = True):
        self.dta = dta
        self.dfLabel = dfLabel
        self.isWeighted = isWeighted
        self.weightVar = weightVar
        self.raiseOnError = raiseOnError
        self.baseDir = baseDir
        self.outputDir = outputDir

        self.excelFileNameBase = None
        self.isLongForm = None
        self.theVars = None

    def getCleanVarName_Series(self, varSeries, onlyReturnIfHadYear=True):
        if onlyReturnIfHadYear:
            mask = varSeries.str.contains(pat=self.yearFormatRegex_Simple + "$", regex=True)
        else:
            mask = pd.Series([True]).repeat(len(varSeries))
        return(varSeries[mask].str.replace(self.yearFormatRegex_Simple + self.yearFormatRegex_Simple + '_as' + self.yearFormatRegex_Simple + '$', '', regex=True).
               str.replace(self.yearFormatRegex_Simple + '_as' + self.yearFormatRegex_Simple + '$', '',regex=True).
               str.replace(self.yearFormatRegex_Simple + self.yearFormatRegex_Simple + '$', '', regex=True).
               str.replace(self.yearFormatRegex_Simple + '$', '', regex=True))

    def setVarNameStyle(self, isTwoYear, isInflatedTo = None):
        self.isTwoYear = isTwoYear
        if (isTwoYear):
            self.yearFormatRegex_ExtractGroup = ".*_(\d{2})"
            self.yearFormatRegex_Simple = "_\d{2}"
        else:
            self.yearFormatRegex_ExtractGroup = ".*_(\d{4})"
            self.yearFormatRegex_Simple = "_\d{4}"

        if isInflatedTo is not None:
            self.yearStrForInflatedVars = str(isInflatedTo)
        else:
            self.yearStrForInflatedVars = None

    def setup(self,outputFileNameBase, varsOfInterest = None, years = None, isLongForm = True, twoDigitYearSuffix=True, analyzeOnlyTimeData = True):
        '''
        Setup the directory, execl output file, and analysis params we need -- figuring out the years, and var names if missing
        :param outputFileNameBase:
        :type outputFileNameBase:
        :param varsOfInterest:  List of variables to analyze in the dataframe
        :type varsOfInterest:
        :param years: List of years to analyze in the dataframe
        :type years: List
        :param isLongForm: Not used?
        :type isLongForm: Boolean
        :param twoDigitYearSuffix: Is the Year written as a two year or four year suffix?
        :type twoDigitYearSuffix: Boolean
        :param analyzeOnlyTimeData:  Should we only include vars that are in time series format, or include non-time based ones?
        :type analyzeOnlyTimeData: Boolean
        :return:
        :rtype:
        '''

        if not os.path.exists(os.path.join(self.baseDir, self.outputDir)):
            os.makedirs(os.path.join(self.baseDir, self.outputDir))

        self.excelFileNameBase = os.path.join(self.baseDir, self.outputDir, outputFileNameBase)

        self.setVarNameStyle(twoDigitYearSuffix)
        
        self.isLongForm = isLongForm
        self.theVars = self.dta.columns.copy()

        # If we didn't get specific fields to focus on, figure it out from the var names in the file
        if varsOfInterest is None:
            # What are the variable names?
            varsOfInterest = list(self.getCleanVarName_Series(self.theVars, analyzeOnlyTimeData).unique())

            # What years are we working with?
            years = {}
            for x in list(self.theVars):
                gotIt =False
                if self.yearStrForInflatedVars is not None:
                    i = re.search(self.yearFormatRegex_ExtractGroup + "_as_" + self.yearStrForInflatedVars + "$", x)
                    found = i.group(1)
                    years[found] = True

                if ~gotIt:
                    m = re.search(self.yearFormatRegex_ExtractGroup+"$", x)
                    if m:
                        found = m.group(1)
                        years[found] = True

            years = list(years.keys())

        self.varsOfInterest = varsOfInterest
        self.years = years

        if years is not None:
            years.sort()


    def lookForExtremePerPersonChanges(self, idVar, weightVar, fieldsToCrossTabList, percentChangeForExtreme = .50):
        '''
        For each  family, and see if there are big shifts (parameter defined) shifts in the variables of interest
        across time (look across each time step for changes above the threshold.
        :param idVar: How do we identify a house?
        :type idVar: String
        :param weightVar:
        :type weightVar: String
        :param fieldsToCrossTabList:
        :type fieldsToCrossTabList: List
        :param percentChangeForExtreme:
        :type percentChangeForExtreme: Real value
        :return:
        :rtype:
        '''
        if len(self.varsOfInterest) == 0:
            print("Nothing to check -- no vars of interest found")
            return

        allVars = [] + fieldsToCrossTabList + [idVar] + [weightVar]  # ["norcid_19", "weight", "race", "incomeBand"]
        deltaVars = []

        numYears =  len(self.years)

        # Part 1:For each var of interst, create three more: Change, Percent Change, and Warning
        for var in self.varsOfInterest:
            for i in range(1, len(self.years)):
                if self.yearStrForInflatedVars is not None:
                    curVar = var + "_" + str(self.years[i]) + "_as_" + self.yearStrForInflatedVars
                    if curVar in self.theVars:
                        priorVar = var + "_" + str(self.years[i-1]) + "_as_" + self.yearStrForInflatedVars
                    else:
                        curVar = var + "_" + str(self.years[i])
                        priorVar = var + "_" + str(self.years[i - 1])
                else:
                    curVar = var + "_" + str(self.years[i])
                    priorVar = var + "_" + str(self.years[i-1])


                if (curVar in self.dta.columns) and (priorVar in self.dta.columns) and (is_numeric_dtype(self.dta[curVar])):
                    suffix = ""
                    if numYears > 2:
                        # suffix =  "_" + str(self.years[i - 1]) + "_to_" + str(self.years[i])
                        # Excel limits the length of fields;, can't use something this long
                        suffix = str(self.years[i - 1])[-2:]

                    # Create delta Vars
                    deltaVar = "d_" + var + suffix

                    # Create a percent Change Var
                    percentDeltaVar = "ch_" + var + suffix

                    # Create a Warning Var
                    warningVar = "bD_" + var + suffix

                    # Mark non-nulls
                    goodValueMask = (~self.dta[curVar].isna()) & (~self.dta[priorVar].isna())

                    # Fill in our comparison variables: Change, Percent Change, and Warning
                    self.dta.loc[goodValueMask, deltaVar] = self.dta.loc[goodValueMask,curVar] - self.dta.loc[goodValueMask,priorVar]
                    self.dta.loc[(self.dta[priorVar] != 0) & goodValueMask,percentDeltaVar] = self.dta.loc[(self.dta[priorVar] != 0) & goodValueMask,deltaVar] / self.dta.loc[(self.dta[priorVar] != 0) & goodValueMask,priorVar]
                    self.dta.loc[(self.dta[priorVar] == 0) & goodValueMask,percentDeltaVar] = None
                    self.dta.loc[(self.dta[priorVar] != 0) & goodValueMask,warningVar] = self.dta.loc[(self.dta[priorVar] != 0) & goodValueMask,percentDeltaVar].abs() > percentChangeForExtreme
                    # self.dta[percentDeltaVar] = np.where(np.isnan(self.dta[percentDeltaVar]) | (np.isinf(self.dta[percentDeltaVar])), self.dta[percentDeltaVar], None)
                    allVars += [priorVar, curVar, deltaVar, percentDeltaVar, warningVar]
                    deltaVars += [deltaVar, percentDeltaVar, warningVar]

        allVars = np.unique(np.array(allVars))
        deltaVars = np.unique(np.array(deltaVars))
        effectData = self.dta[allVars].copy()
        deltaVars.sort()

        # the var names get way too long for excel -- we need to rename some of them
        effectData.rename(
            columns={element: element.replace("SinceLastQYr_AmountBought", "Bought").
                replace("SinceLastQYr_AmountSold", "Sold").
                replace("TotalChangeInWealth", "WlthChng")
                     for element in effectData.columns.tolist()}, inplace=True)

        deltaVars=[deltaVar.replace("SinceLastQYr_AmountBought", "Bought").
                replace("SinceLastQYr_AmountSold", "Sold").
                replace("TotalChangeInWealth", "WlthChng")
                     for deltaVar in deltaVars]

        # Part 2: Analyze the Deltas (difference across time) in the fields of interest
        sds = SurveyDataSummarizer(effectData, weightVar, None,
                                        fieldsToSummarize=deltaVars,
                                        fieldsToCrossTab=fieldsToCrossTabList)
        sds.doIt(self.excelFileNameBase + "_DeltaPerPerson_SDS.xlsx")

        tempWriter = pd.ExcelWriter(self.excelFileNameBase + "_RawPerPersonChange.xlsx", engine='xlsxwriter')
        effectData.to_excel(tempWriter, "Raw Changes")
        tempWriter.book.close()


    def checkForMedianShifts(self, percentChangeForError = .10):
        '''
        Across the population, look for changes in the median value of each var of interest
        :param percentChangeForError:
        :type percentChangeForError:
        :return:
        :rtype:
        '''
        expectedVarsMissing = []
        badMedians = []

        if len(self.varsOfInterest) == 0:
            print("Nothing to check -- no vars of interest found")
            return

        for var in self.varsOfInterest:
            priorMedian = None
            priorPercent = None

            # Go year by year, looking for problems
            for year in self.years:
                if self.yearStrForInflatedVars is not None:
                    fullVarName = var + "_" + str(year) + "_as_" + str(self.yearStrForInflatedVars)
                    if (fullVarName not in self.theVars):
                        fullVarName = var + "_" + str(year)
                else:
                    fullVarName = var + "_" + str(year)

                # fullVarName = var + "_" + str(year)

                if (fullVarName in self.theVars):
                    # print("Checking " + fullVarName + " for median shifts.")

                    if (is_bool_dtype(self.dta[fullVarName])):
                        # Get current median
                        if (self.isWeighted):
                            percentTrue = wAverage(self.dta, X = fullVarName, varForWeights = self.weightVar)
                        else:
                            percentTrue = self.dta[fullVarName].mean(skipna = True)

                        if priorPercent is not None:
                            if (abs(percentTrue - priorPercent )) > percentChangeForError:
                                badMedians = badMedians + [fullVarName + " (" + str(priorPercent*100) + "% to " + str(percentTrue*100) + "%) "]
                        priorPercent = percentTrue

                    elif (is_numeric_dtype(self.dta[fullVarName])):
                        # Get current median
                        if (self.isWeighted):
                            median = wMedian(self.dta, varToGetMedian = fullVarName, varForWeights = self.weightVar)
                        else:
                            median = self.dta[fullVarName].median(skipna = True)

                        if priorMedian is not None and median is not None:
                            isProblem = False
                            if priorMedian != 0:
                                if (abs(median - priorMedian ) /priorMedian) > percentChangeForError:
                                    isProblem = True
                            elif median != 0:
                                if (abs(priorMedian - median ) /median) > percentChangeForError:
                                    isProblem = True

                            if isProblem:
                                badMedians = badMedians + [fullVarName + " (" + str(priorMedian) + " to " + str(median) + ") "]

                        priorMedian = median
                else:
                    expectedVarsMissing = expectedVarsMissing + [fullVarName]

        tempWriter = pd.ExcelWriter(self.excelFileNameBase + "_MedianChange.xlsx", engine='xlsxwriter')

        medianMsg = None
        if len(badMedians) > 0:
            medianMsg = "Bad median data in dataframe " + self.dfLabel + ": " + str(badMedians)

            df = pd.DataFrame(badMedians)
            df.to_excel(tempWriter, "Bad Medians")

            print(medianMsg)

        missingMsg = None
        if len(expectedVarsMissing) > 0:
            missingMsg = "Missing data on dataframe " + self.dfLabel + ": " + str(expectedVarsMissing)
            df = pd.DataFrame(expectedVarsMissing)
            df.to_excel(tempWriter, "Missing Vars")
            print(missingMsg)

        tempWriter.book.close()

        if (len(badMedians) > 0) & (self.raiseOnError):
            raise Exception(medianMsg)
        if (len(expectedVarsMissing) > 0) & (self.raiseOnError):
            raise Exception(missingMsg)


    def doIt(self):
        self.lookForExtremePerPersonChanges()
        self.checkForMedianShifts()
