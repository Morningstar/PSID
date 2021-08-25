import pandas as pd
import os
import copy
import ThirdPartyCode.SASReader as SASReader
import PSIDProcessing.CrosswalkHelper as CrosswalkHelper

CONSUMPTION_CROSSWALK_FILE = "ConsExpCrosswalk_AsOf2021.xlsx"

'''
This class reads in the raw PSID data from disk (SAS format) and converts them to CSV files, 
optionally extracting only those variables of interest
'''
class RawLoader:

    combinedDir = 'PSIDFamilyFiles_2021Extract'

    familyDir = 'PSIDFamilyData_Prepackaged'
    individualDir = 'PSIDIndividualData'
    wealthDir = 'PSIDWealthData'
    savingDir = 'ActiveSavings/ActSavings89_94'
    # startYear = None
    # endYear = None

    # What data is available locally for use?
    yearsFamilyDataCollected = list(range(1980, 1997+1, 1)) +  list(range(1999, 2019+2, 2))
    yearsWealthDataCollected = [1984, 1989, 1994] + list(range(1999, 2007+2, 2))
    yearsActiveSavingCollected = [1989, 1994]
    
    # It appears there are problems with some of the FTP site files - especially 1994; a fresh download from the PSID data center yields more sensible data.
    # This data in these files have the Wealth and Family data cominbed
    yearsCombinedNewDownloadCollected = [1984, 1989, 1994, 1999, 2001, 2003, 2005, 2007, 2009, 2011, 2013, 2015, 2017, 2019]
        
    def __init__(self, rootDir, yearsToInclude = [2015, 2017, 2019]):
        self.rootDataDir = rootDir
        self.yearsToInclude= yearsToInclude
        # self.startYear = startYear 
        # self.endYear = endYear 
        # print('psid_raw class: use .load() to import raw data')    

    def readRawDataFile(self, fileFullPathNoExtension, forceReload = False):
        if (not forceReload) and os.path.exists(fileFullPathNoExtension + ".csv"):
            return pd.read_csv(fileFullPathNoExtension + ".csv")
        elif os.path.exists(fileFullPathNoExtension + ".sas") and os.path.exists(fileFullPathNoExtension + ".txt"):
            return SASReader.read_sas(
                data_file = fileFullPathNoExtension + ".txt",
                dict_file = fileFullPathNoExtension + ".sas",
                outputCSV = fileFullPathNoExtension + ".csv",
                outputMeta = fileFullPathNoExtension + "_meta.csv"
                )
        else:
            raise Exception("What file am I supposed to load? What am I, a mind reader?")
    
    def readCombinedNewDownload(self, fieldsToKeep = None, forceReload = False):
        d = {}
        # Read in combined family + wealth data
        yearsToGet = [num for num in self.yearsCombinedNewDownloadCollected if num in self.yearsToInclude]
        for year in yearsToGet:
            # coreName = 'Fam' + str(year) + '_Newdownload'
            coreName = 'fam' + str(year) 
            tmp = self.readRawDataFile(os.path.join(self.rootDataDir, self.combinedDir, coreName, coreName.upper()), forceReload)
            if (fieldsToKeep is not None):
                colsToKeepInDF = (set(fieldsToKeep) & set(tmp.columns))    
                tmp = tmp[list(colsToKeepInDF)]
            d[year] = tmp
                                    
        # self.theData = d  
        return d
        
    def readFamilyAndWealthData(self, excludeCombinedYears = True, fieldsToKeep = None, forceReload = False):
        d = {}
        # Read in family data
        if (excludeCombinedYears):
            yearsToGet = [num for num in self.yearsFamilyDataCollected if ((num in self.yearsToInclude) and (num not in self.yearsCombinedNewDownloadCollected))]
        else:
            yearsToGet = [num for num in self.yearsFamilyDataCollected if num in self.yearsToInclude]
            
        for year in yearsToGet:
            coreName = 'fam' + str(year) + ('er' if year >= 1994 else '')
            tmp = self.readRawDataFile(os.path.join(self.rootDataDir, self.familyDir, coreName, coreName.upper()), forceReload)
            if (fieldsToKeep is not None):
                colsToKeepInDF = (set(fieldsToKeep) & set(tmp.columns))    
                tmp = tmp[list(colsToKeepInDF)]
            d[year] = tmp
                                    
        # read in wealth data
        if (excludeCombinedYears):
            yearsToGet = [num for num in self.yearsWealthDataCollected if ((num in self.yearsToInclude) and (num not in self.yearsCombinedNewDownloadCollected))]
        else:
            yearsToGet = [num for num in self.yearsWealthDataCollected if num in self.yearsToInclude]
            
        for year in yearsToGet:
            coreName = 'wlth' + str(year)
            wealth = self.readRawDataFile(os.path.join(self.rootDataDir, self.wealthDir, coreName, coreName.upper()), forceReload)
            if (fieldsToKeep is not None):
                colsToKeepInDF = (set(fieldsToKeep) & set(wealth.columns))
                wealth = wealth[list(colsToKeepInDF)]
            
            if (len(wealth.columns) > 0):
                d[year] = d[year].join(wealth) # Left Join in Wealth.  Careful - is the index set correctly for both?
        # self.theData = d  
        return d

    def readActiveSavingData(self, fieldsToKeep = None, forceReload = False):
        d = {}
        # Read in family data
        yearsToGet = [num for num in self.yearsActiveSavingCollected if num in self.yearsToInclude]

        for year in yearsToGet:
            coreName = 'ACT' + str(year)[2:4] 
            tmp = self.readRawDataFile(os.path.join(self.rootDataDir, self.savingDir, coreName.upper()), forceReload)
            if (fieldsToKeep is not None):
                colsToKeepInDF = (set(fieldsToKeep) & set(tmp.columns))    
                tmp = tmp[list(colsToKeepInDF)]
            d[year] = tmp
                                    
        # read in wealth data
        return d

    def readIndividualData(self, fieldsToKeep = None, forceReload = False):
        # Individual data
        # coreName = "ind2017er"
        coreName = "ind2019er"
        dta = self.readRawDataFile(os.path.join(self.rootDataDir, self.individualDir, coreName, coreName.upper()))
        if (fieldsToKeep is not None):
            colsToKeepInDF = (set(fieldsToKeep) & set(dta.columns))    
            dta = dta[list(colsToKeepInDF)]
        return dta 
    
    def readConsumptionCrossWalk(self):
        concw = pd.read_excel(os.path.join(self.rootDataDir, CONSUMPTION_CROSSWALK_FILE))
        concw.columns = ['name', 'oldname'] + list(range(1999, self.endYear + 1, 2))
        concw = copy.deepcopy(concw.loc[2:])
        return concw
           
    def loadRawPSID_FamilyOnly(self, fieldsToKeep = None, forceReload = False):
        dict1 = self.readCombinedNewDownload(fieldsToKeep= fieldsToKeep, forceReload=forceReload)
        dict2 = self.readFamilyAndWealthData(excludeCombinedYears=True, fieldsToKeep= fieldsToKeep, forceReload=forceReload)
        dict2.update(dict1)
        self.rawFam = dict2
        return self.rawFam
                
    def loadRawPSID_All(self):        
        # Family Crosswalk 
        self.crosswalkHelper = CrosswalkHelper.PSIDCrosswalkHelper(self.rootDataDir)
        self.psidcw = self.crosswalkHelper.readCrossWalk()
        
        # Family data
        self.loadRawPSID_FamilyOnly()
                
        # Individual data
        self.rawind = self.readIndividualData()

        # Not used:
        # self.rawchild = pd.read_stata('ChildHistoryData/childhistory.dta')
        # Consumption Crosswalk
        # self.concw = self.readConsumptionCrossWalk()
 
    def getFamilyData(self):
        return self.rawfam
    
    def getConsumptionCrosswalk(self):
        return self.concw
    