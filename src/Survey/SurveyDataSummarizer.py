
from Survey.SurveyFunctions import *
from pandas.api.types import is_string_dtype, is_numeric_dtype, is_bool_dtype
from Survey.ExcelOutputWrapper import ExcelOutputWrapper

CONST_METADATA_COLUMN_VARNAME = "Var"
CONST_METADATA_COLUMN_LABEL = "Label"
CONST_METADATA_COLUMN_DESCRIPTION = "Description"
CONST_METADATA_COLUMN_TYPE = "Type"  # one of "Numeric", "Categorical"

class SurveyDataSummarizer():
    '''
    Takes a dataset with survey weights, and generates an excel doc with one sheet summarizing each variable
    '''
    spaceBetweenTables = 2
    startColForTables = 1

    def __init__(self, dta,  weightField, fieldMetaData, fieldsToSummarize = None, fieldsToCrossTab = None):
        '''

        :param dta: survey Weighted Data
        :type dta: Pandas DF
        :param weightField: the column name for weights
        :type weightField: str
        :param fieldMetaData: table with columns CONST_METADATA_COLUMN_VARNAME, CONST_METADATA_COLUMN_LABEL, CONST_METADATA_COLUMN_DESCRIPTION
        :type fieldMetaData: DF
        :param fieldsToSummarize: which fields to summarize - if none, will do all of them
        :type fieldsToSummarize: list
        :param fieldsToCrossTab: which fields to cross-tab on all summary fields.
        :type fieldsToCrossTab: list
        '''

        self.dta = dta
        self.weightVar = weightField
        # self.weights = dta[weightField]

        self.fieldMetaData = None
        if fieldMetaData is not None:
            self.fieldMetaData = fieldMetaData
            self.fieldMetaData.Description = self.fieldMetaData.Description.astype("string")
            # self.fieldMetaData.fillna()

        if fieldsToSummarize is None:
            fieldsToSummarize = dta.columns.to_list()
            if weightField is not None:
                fieldsToSummarize.remove(weightField)
            if fieldsToCrossTab is not None:
                fieldsToSummarize = [x for x in fieldsToSummarize if x not in fieldsToCrossTab]

        self.fieldsToSummarize = fieldsToSummarize
        self.fieldsToCrossTab = fieldsToCrossTab

        self.excelWrapper = ExcelOutputWrapper()

    def doIt(self, destinationFile):
        '''
        Create an excel file with the results.  For each field in the dataset, run the summary function above
        :param destinationFile:
        :type destinationFile:
        :return:
        :rtype:
        '''

        self.excelWrapper.startFile(destinationFile)
        metaData = None

        for field in self.fieldsToSummarize:

            if self.fieldMetaData is not None:
                metaData = self.fieldMetaData[self.fieldMetaData[CONST_METADATA_COLUMN_VARNAME] == field].copy()
            if (metaData is not None and len(metaData.index) > 0):
                varLabel = metaData[CONST_METADATA_COLUMN_LABEL].to_list()[0]
                desc = metaData[CONST_METADATA_COLUMN_DESCRIPTION].to_list()[0]
                varType = metaData[CONST_METADATA_COLUMN_TYPE].to_list()[0]
            else:
                varLabel = field
                desc = "Missing Metadata for " + field
                if (is_string_dtype(self.dta[field])) or is_bool_dtype(self.dta[field]):
                    varType = "Categorical"
                elif (is_numeric_dtype(self.dta[field])):
                    if len(self.dta[field].unique())<=3:
                        varType = "Categorical"
                    else:
                        varType = "Numeric"
                else:
                    varType = "Categorical" # Not sure what this is -- but to be safe, this is ok

            print("Adding Sheet for " + field)

            if field == 'ActiveSavingsHH_1984':
                print("Debug here")

            self.excelWrapper.addWorksheet(varLabel)

            # Summary stats
            if varType == "Numeric":
                # aggs = {'Mean': (field, 'mean'), 'Median': (field, 'median'), }
                results = wDescribeByVar(self.dta, field, self.weightVar) # wAgg(self.dta, aggs, self.weights)
                self.excelWrapper.addTable(results, "Summary Statistics for " + varLabel + " (" + field + ")", desc, None, "down")
            elif varType == "Categorical":
                aggs = {'W. Percent': (field, 'value_counts', True), 'W. Count': (field, 'value_counts', False),
                          'N': (field, 'numObs', False, False) }
                results = wAgg(self.dta, aggs, self.weightVar)
                self.excelWrapper.addTable(results,  "Summary Statistics for " + varLabel + " (" + field + ")", desc, columnFormats={'N':self.excelWrapper.wholeNumberFormat,'W. Count':self.excelWrapper.numberFormat, 'W. Percent':self.excelWrapper.percentFormat}, direction="down")
            else:
                raise Exception("We're missing something here. " + str(varType))

            # Segmentation by Cross-Tab Fields
            if self.dta[field].isna().all() or self.fieldsToCrossTab is None:
                None  #nothing more to add
            else:
                for crossField in self.fieldsToCrossTab:
                    if crossField == field:
                        None;
                    # Summary 1: Within Group %
                    elif varType == "Numeric":
                        results =  wGroupedDescribeByVar(dta = self.dta, groupByVarList=[crossField], varToDescribe=field, weightVar=self.weightVar)
                        self.excelWrapper.addTable(results, "Summary of " + varLabel + " (" + field + ") by " + crossField, "Note: all values are weighted", None, "down")
                    elif varType == "Categorical":
                        results = wGroupByAgg(dta = self.dta,
                                          groupByVarList = [crossField],
                                          aggregationDict = aggs,
                                          varForWeights = self.weightVar)

                        self.excelWrapper.addTable(results,  "Summary of " + varLabel + " (" + field + ") by " + crossField, "Note: all values are weighted",
                                                     columnFormats={'W. Percent':self.excelWrapper.percentFormat, 'W. Count':self.excelWrapper.numberFormat, 'N':self.excelWrapper.wholeNumberFormat}, direction="down")

                # Summary 2: Across Group Cross Tabs
                if len(self.fieldsToCrossTab) > 0:
                    if varType == "Categorical":
                        for fieldToCrossTab in self.fieldsToCrossTab:
                            if fieldToCrossTab == field:
                                None;
                            else:
                                results1 = wCrossTabByVar(self.dta, field, fieldToCrossTab, self.weightVar, normalize=False, dropna=False)
                                self.excelWrapper.addTable(results1, "Weighted Crosstab: " + field + " by " + fieldToCrossTab,
                                                             columnFormats={'ALL':self.excelWrapper.numberFormat}, direction="down")

                                results2 = wCrossTabByVar(self.dta, field, fieldToCrossTab, self.weightVar, normalize=True)
                                self.excelWrapper.addTable(results2, "Weighted, Normalized Crosstab: " + field + " by " + fieldToCrossTab,
                                                             columnFormats={'ALL':self.excelWrapper.percentFormat}, direction="right")

                                results3 = pd.crosstab(self.dta[field].fillna("<NA>"), self.dta[fieldToCrossTab].fillna("<NA>"), normalize=False, dropna=False)
                                self.excelWrapper.addTable(results3, "Unweighted crosstab: " + field + " by " + fieldToCrossTab,
                                                             columnFormats={'ALL':self.excelWrapper.wholeNumberFormat}, direction="down")

                                results4 = pd.crosstab(self.dta[field], self.dta[fieldToCrossTab], normalize="columns")
                                self.excelWrapper.addTable(results4, "Unweighted, normalized crosstab: " + field + " by " + fieldToCrossTab,
                                                             columnFormats={'ALL':self.excelWrapper.percentFormat}, direction="right")
        self.excelWrapper.endFile()

