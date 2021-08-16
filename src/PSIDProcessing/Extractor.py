# Based on PSID_Work's PSIDdata.py file
import warnings
import pandas as pd
import numpy as np
import PSIDProcessing.RawLoader as RawLoader
import PSIDProcessing.CrosswalkHelper as CrosswalkHelper
import os 

class Extractor:
    '''
    This class helps you extract data from the PSID -
    pulling from the relevant years of each file (family, wealth, individual,consumption, etc) as needed,
     and returning a simple dataframe for further processing

    '''

    def __init__(self, rootDir, yearsToInclude, variablesWeWantAnyYear, alwaysLoadTheseVars, source='family'):
        '''
        :param rootDir: where we find the data
        :type rootDir: str
        :param yearsToInclude:  years of data to load
        :type yearsToInclude: list
        :param variablesWeWantAnyYear: a list of 'example' variables - for each one, we'll look up the series that includes that variable, then include everything in that series within yearsToInclude
        :type variablesWeWantAnyYear:  list
        :param alwaysLoadTheseVars: no matter what variable series are given, add these specific PSID-original variables [only that year, not the whole series]
        :type alwaysLoadTheseVars: list
        :param source: 'Family' or 'Individual' file
        :type source: str
        '''
        self.yearsToInclude = yearsToInclude
        self.variablesWeWant_SampleForAYear = variablesWeWantAnyYear
        self.alwaysLoadTheseVars = alwaysLoadTheseVars
        self.rootDir = rootDir

        self.crosswalkHelper = CrosswalkHelper.PSIDCrosswalkHelper(rootDir)        
        self.loader = RawLoader.RawLoader(rootDir, yearsToInclude)
        self.source = source  


        self.dataDict = None
        self.variableStatusLongForm = None


    def getDataForSelectedVars(self, forceReload = False, saveIt = False, filePath = None, fileNameBase = None):
        '''
        Converts our list of desired variable serieses into specific PSID-original variable names,
        and calls the PSID Loader to load the relevant years of data, subset to thus variables,
        and return it all in a big honkin' data set

        :param forceReload: force reloading of the data from the original PSID SAS file; otherwise use our temp CSV
        :type forceReload: bool
        :param saveIt: save the resulting files to  disk
        :type saveIt: bool
        :return: a dictionarry with year:dataframe for each desired year
        :rtype: Dict
        '''
        self.crosswalkHelper.readCrossWalk(forceReload)

        varStatus = self.crosswalkHelper.getVariableSeriesesGivenSample(varDictOrList = self.variablesWeWant_SampleForAYear, yearsToInclude = self.yearsToInclude)

        longFormatStatus = pd.melt(varStatus,id_vars=['sourcefile', 'category', 'subcategory', 'label', 'count'],var_name='year', value_name='varName')

        if self.alwaysLoadTheseVars is not None:
            for varToLoad in self.alwaysLoadTheseVars.keys():
                if varToLoad not in longFormatStatus.varName.unique().tolist():
                    tmp = self.crosswalkHelper.getDetailsForVar(varToLoad)
                    theYear = tmp.columns[tmp.isin([varToLoad]).any()].tolist()[0].replace("Y", "")
                    row = pd.DataFrame({'sourcefile':tmp.C0.iloc[0],
                                    'category':tmp.C1.iloc[0], 'subcategory':tmp.C2.iloc[0],
                                    'label': self.alwaysLoadTheseVars[varToLoad],
                                    'count': None,
                                    'varName': varToLoad,
                                    'year':theYear
                                    }, index=[len(longFormatStatus)])
                    longFormatStatus = pd.concat([longFormatStatus, row], ignore_index=True)

        varsToKeep = longFormatStatus.varName.tolist()


        if self.source == 'family':
            theDataDict = self.loader.loadRawPSID_FamilyOnly(varsToKeep, forceReload)
        elif self.source == 'individual':
            theDataDict = {0: self.loader.readIndividualData(varsToKeep, forceReload)}

        self.dataDict = theDataDict
        self.variableStatusLongForm = longFormatStatus

        if saveIt:
            if self.source == 'family':
                self.saveExtractedFamilyData(filePath, fileNameBase)
            elif self.source == 'individual':
                self.saveExtractedIndividualData(filePath, fileNameBase)

        return self.dataDict

    def fillMissingVarsWithNones(self):
        '''
        Looks in the previously created VariableStatus table for any variable-years that werent mapped,
        and creates new variables, filled with NOnes, for those missing variable-years
        :return: None
        :rtype: None
        '''

        if self.source == 'family':
            soureFileName = 'FAMILY PUBLIC'
        elif self.source == 'individual':
            soureFileName = 'INDIVIDUAL'

        for year in self.dataDict:
            yearData = self.dataDict[year]
            varsMissing = self.variableStatusLongForm['label'][
                (self.variableStatusLongForm.sourcefile == soureFileName) &
                (self.variableStatusLongForm.varName.isna()) &
                (self.variableStatusLongForm.year == year)]

            # warn about restricted data we don't have
            if self.source == 'family':
                restrictedMissing = self.variableStatusLongForm['label'][
                    (self.variableStatusLongForm.sourcefile == "FAMILY RESTRICTED") &
                    (self.variableStatusLongForm.varName.isna()) &
                    (self.variableStatusLongForm.year == year)]
                if len(restrictedMissing) > 0:
                    warnings.warn("You've asked for data that isnt available in " + str(year) + " - it's from the restricted file." + str(restrictedMissing))
                    varsMissing = pd.concat([varsMissing, restrictedMissing])

            emptyDf = pd.DataFrame(columns=varsMissing)
            yearData = pd.concat([yearData,emptyDf], ignore_index=True, sort=False)
            self.dataDict[year] = yearData



    def saveExtractedFamilyData(self, filePath, fileNameBase):
        '''
        Save each year of extracted PSID data  and the status of each variable
        It also creates the output directory if needed
        :param filePath:  Directory where the files are to be stored
        :type filePath: String
        :param fileNameBase:  Base (Prefix) File name for our data.
        :type fileNameBase: String
        :return: None
        :rtype: None
        '''
        if not os.path.exists(filePath):
            os.makedirs(filePath)

        for year in self.dataDict:
            yearData = self.dataDict[year]
            yearData = yearData.reindex(sorted(yearData.columns), axis=1)
            yearData.to_csv(os.path.join(filePath, fileNameBase + str(year) + ".csv"), index=False)
        self.variableStatusLongForm.to_csv(os.path.join(filePath, fileNameBase + "VariableStatus.csv"), index=False)

    def saveExtractedIndividualData(self, filePath, fileNameBase):
        '''
        Save the extracted PSID individual data and the status of each variable
        It also creates the output directory if needed
        :param filePath:  Directory where the files are to be stored
        :type filePath: String
        :param fileNameBase:  Base (Prefix) File name for our data.
        :type fileNameBase: String
        :return: None
        :rtype: None
        '''

        if (len(self.dataDict) > 1):
            raise Exception("There should only be one year of Individual data")

        if not os.path.exists(filePath):
            os.makedirs(filePath)

        individualData = self.dataDict[0]
        individualData.to_csv(os.path.join(filePath, fileNameBase + ".csv"), index=False)
        self.variableStatusLongForm.to_csv(os.path.join(filePath, fileNameBase + "VariableStatus.csv"), index=False)


    def readExtractedData(self, yearsToInclude, filePath, fileNameBase):
        '''
        Read previously extracted data into memory
        :param yearsToInclude:
        :type yearsToInclude:
        :param filePath:  Directory where the files are stored
        :type filePath: String
        :param fileNameBase:  Base (Prefix) File name for our data.
        :type fileNameBase: String
        :return: None
        :rtype: None
        '''
        self.dataDict = {}
        if self.source == 'family':
            for year in yearsToInclude:
                if (os.path.exists(os.path.join(filePath, fileNameBase + str(year) + ".csv"))):
                    yearData = pd.read_csv(os.path.join(filePath, fileNameBase + str(year) + ".csv"), low_memory=False)
                    self.dataDict[year] = yearData
                else:
                    print("Skipping year " + str(year) + ". No data file found." )
        elif self.source == 'individual':
            if (os.path.exists(os.path.join(filePath, fileNameBase + ".csv"))):
                dta = pd.read_csv(os.path.join(filePath, fileNameBase + ".csv"), low_memory=False)
                self.dataDict[0] = dta
            else:
                raise Exception("Unable to find individual data file." )

        if (os.path.exists(os.path.join(filePath, fileNameBase + "VariableStatus.csv"))):
            self.variableStatusLongForm = pd.read_csv(os.path.join(filePath, fileNameBase + "VariableStatus.csv"))
        else:
            self.variableStatusLongForm = None

    def mapVariableNames(self):
        '''
        Rename variables in each dataset in memory (each year for family data) using or varStatus mapping -> from VarName to Label
        :return: The data dictionary used in mapping
        :rtype: Dictionary
        '''

        if self.source == 'family':
            varRemapping  = dict(zip(self.variableStatusLongForm.varName, self.variableStatusLongForm.label))
        elif self.source == 'individual':
            varRemapping  = dict(zip(self.variableStatusLongForm.varName, self.variableStatusLongForm.label + "_" + self.variableStatusLongForm.year.astype(str)))

        cleanVarRemapping = {k: varRemapping[k] for k in varRemapping if not pd.isnull(k)}

        for year in self.dataDict:
            yearData = self.dataDict[year]
            yearData.rename(columns = cleanVarRemapping, inplace = True)
        return self.dataDict



    '''
    Original functions from PSID_Work's PSID_data.py -- not tested and converted to new structure yet
    '''

    def getfamyeardata(self, df, namedf, year):
    #     Get list of that year's variable names
        varlist = list(namedf['Y' + str(year)])
    #     Remove missing vars/vars already included
        varlist = [x for x in varlist if x != 'missing']
        for var in varlist:
            df[var] = self.rawdata.rawfam[year][var]
        return df

    def getfamdata(self, datadict, namedf):
        # this function updates a dictionary with raw family data
        for year in range(1999, self.rawdata.lastyear + 2, 2):
            datadict.setdefault(year, pd.DataFrame())
            datadict[year] = self.getfamyeardata(datadict[year], namedf, year)
        return datadict

    def getinddata(self, df, namedf):
    #     Get list of that year's variable names
        varlist = []
        for year in range(1999, self.rawdata.lastyear + 1, 2):
            varlist = varlist + list(namedf['Y' + str(year)])
    #     Remove missing vars/vars already included
        varlist = [x for x in varlist if x != 'missing']
        for var in varlist:
            df[var] = self.rawdata.rawind[var]
        return df

    def merge_ind_fam(self, inddf, famdict):
        indid_arg = [
            'individual', 'survey information',
            'interview information', 'id (interview)',
            'missing'
            ]
        famid_arg = [
            'family', 'survey information',
            'interview information', 'family interview number (id)',
            'missing'
            ]
        indid_list = self.rawdata.categories(indid_arg)
        famid_list = self.rawdata.categories(famid_arg)

        # generate keep variable to track observations
        keep = [0] * len(inddf)
        for year in range(1999, self.rawdata.lastyear + 1, 2):
    # assign copy of family ID with family data name to individual data
            famname = famid_list['Y' + str(year)].values[0]
            indname = indid_list['Y' + str(year)].values[0]
            inddf[famname] = inddf[indname]
            inddf = inddf.merge(famdict[year], on = famname, how = 'left')
            # keep observations that have appeared in data at least once
            keep = np.where((inddf[famname] != 0) | (keep == 1), 1, 0)
            # generate person_id for merge with child data
        inddf['person_id'] = (self.rawdata.rawind['ER30001'] * 1000 +
                              self.rawdata.rawind['ER30002'])
        return inddf[keep == 1]

    # Crosswalk for pulling data and renaming
    def consdata(self, d = {}):
#         pull family raw consumption data
        for year in range(1999, self.rawdata.lastyear + 1, 2):
            varlist = self.rawdata.concw[year].dropna()
            for var in varlist:
                d[year][var] = self.rawdata.rawfam[year][var]
        return d


    def merge_child(self, inddf):
        # create markers for whether someone is a parent
        # subset for those with children?
        child = self.rawdata.rawchild[self.rawdata.rawchild['CAH9'] < 98].copy()
        child['person_id'] = child['CAH3'] * 1000 + child['CAH4']
        # keep those with children
        child['max9'] = child.groupby('person_id')['CAH9'].transform(max)
        child = child.loc[(child['max9'] == child['CAH9']) |
                          (child['max9'].isnull())]
        child = child.drop_duplicates('person_id')
        child = child[['person_id', 'max9']]
        inddf = inddf.merge(child, on = 'person_id', how = 'left')
        # assign parent dummy variable
        inddf['isparent'] = np.where(inddf['max9'].notnull(), 1, 0)
        return inddf


'''
Helper function to handle our primary use case: Do it All
'''
def extractAndSave(params):
    # Get the family level data - runs for each year of data we need
    # params.yearsToInclude = [1984]

    famExtractor = Extractor(params.PSID_DATA_DIR, params.yearsToInclude, params.familyWealthVarsWeNeed2019, None, source='family')
    famExtractor.getDataForSelectedVars(forceReload = False, saveIt = True, filePath = os.path.join(params.BASE_OUTPUT_DIR, params.EXTRACTED_OUTPUT_SUBDIR), fileNameBase= "extractedPSID_")
    famExtractor.readExtractedData(params.yearsToInclude, filePath = os.path.join(params.BASE_OUTPUT_DIR, params.EXTRACTED_OUTPUT_SUBDIR), fileNameBase= "extractedPSID_")
    famExtractor.mapVariableNames()
    famExtractor.fillMissingVarsWithNones()
    famExtractor.saveExtractedFamilyData(filePath = os.path.join(params.BASE_OUTPUT_DIR, params.MAPPED_OUTPUT_SUBDIR), fileNameBase= "extractedPSID_Mapped_")

    # Do it again for individual level data
    indExtractor = Extractor(params.PSID_DATA_DIR, params.yearsToInclude, params.individualVarsWeNeed2019, params.individualVars_LoadRegardlessOfYear, source='individual')
    indExtractor.getDataForSelectedVars(forceReload = False, saveIt = True, filePath = os.path.join(params.BASE_OUTPUT_DIR, params.EXTRACTED_OUTPUT_SUBDIR), fileNameBase= "extractedPSID_Individual")
    indExtractor.readExtractedData(params.yearsToInclude, filePath = os.path.join(params.BASE_OUTPUT_DIR, params.EXTRACTED_OUTPUT_SUBDIR), fileNameBase="extractedPSID_Individual")
    indExtractor.mapVariableNames()
    indExtractor.fillMissingVarsWithNones()
    indExtractor.saveExtractedIndividualData(filePath = os.path.join(params.BASE_OUTPUT_DIR, params.MAPPED_OUTPUT_SUBDIR), fileNameBase=  "extractedPSID_Individual_Mapped")

    return (famExtractor, indExtractor)