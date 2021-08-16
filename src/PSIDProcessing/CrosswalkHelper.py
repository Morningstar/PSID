import pandas as pd
import os
import copy

# CROSSWALK_FILE_ORIG = "PSIDCrosswalk_AsOf2020.xlsx"
# CROSSWALK_FILE_PROCESSED = "PSIDCrosswalk_AsOf2020_clean.csv"

CROSSWALK_FILE_ORIG = "PSIDCrosswalk_AsOf2021.xlsx"
CROSSWALK_FILE_PROCESSED = "PSIDCrosswalk_AsOf2021_clean.csv"

''' 
This class takes a cleanedup PSID Cross-year crosswalk file (showing the names of different variables, by year) 
and helps process it. For example, by finding the names of other equivalent variables in other years 
'''

class PSIDCrosswalkHelper:
        
    def __init__(self, rootDir):
        self.rootDataDir = rootDir
        self.readCrossWalk()

    # read in psid variable name file
    def readCrossWalk(self, forceReload = False): 
        if (not forceReload) and os.path.exists(os.path.join(self.rootDataDir, CROSSWALK_FILE_PROCESSED)):
            self.dta = pd.read_csv(os.path.join(self.rootDataDir, CROSSWALK_FILE_PROCESSED))
        elif os.path.exists(os.path.join(self.rootDataDir, CROSSWALK_FILE_ORIG)):
            vardata = pd.read_excel(os.path.join(self.rootDataDir, CROSSWALK_FILE_ORIG))
        
            # split variable descriptions to allow for multiple identifying variables
            vardata['split_text'] = vardata['TEXT'].str.split('>')
            vardata['C0'] = vardata['TYPE']
            for cat in range(1, vardata['split_text'].str.len().max()):
                text = vardata['split_text'].str[cat]
                text = text.str.replace('\n\d\d', '')
                text = text.str.replace(':', '')
                vardata['C' + str(cat)] = text
            # vardata = vardata.fillna('missing')
            
            vardata.to_csv(os.path.join(self.rootDataDir, CROSSWALK_FILE_PROCESSED))
            
            self.dta = vardata
        return self.dta

    # get_cat_from_varname
    def getDetailsForVar(self, varname):
        subset = copy.deepcopy(self.dta)
        yearColumns = [x for x in self.dta.columns if x.startswith('Y')]
        df= self.dta[yearColumns]
        assert varname in df.values
        subset = subset[df.values == varname]
        return subset

    def getVariablesInSameSeries(self, varname):
        row = self.getDetailsForVar(varname)
        yearColumns = [x for x in self.dta.columns if x.startswith('Y')]
        yearRow = row[yearColumns].copy()
        yearRow.columns = yearRow.columns.str.replace("Y", "")
        return yearRow.to_dict(orient='records')
        
    # findseries
    def findCategoryDetailsForVariable(self, varname):
        yearColumns = [x for x in self.dta.columns if x.startswith('Y')]
        df= self.dta[yearColumns]
        catagoryColumns = [x for x in self.dta.columns if x.startswith('C')]
        return self.dta[df.values == varname][catagoryColumns]


    # clist = ['individual', 'demographic', 'age']  A list following category levels in the crosswalk file: 0:Type;1:Major Category; 2:VariableType; 3:Qualifier1; 4:Qualifier2 
    def getCategoriesMatchingCriteria(self, categoryCriteriaList):
        subset = copy.deepcopy(self.dta)
        for i in range(0, len(categoryCriteriaList)):
            lowercase = subset['C' + str(i)].str.lower()
            cond = lowercase.str.startswith(categoryCriteriaList[i].str.lower())
            subset = copy.deepcopy(subset[cond])
        assert len(subset) > 0
        return subset

 
    def getAvailableYearsForVarsMatchingCriteria(self, categoryCriteriaList, minyear = 1968, maxyear = 2019):
        ndf = self.categories(categoryCriteriaList)
    #     all year columns
        ylist = [x for x in ndf.columns if x.startswith('Y')]
    #     only year columns in range
        rlist = [x for x in ylist if int(x[1:]) in range(minyear, maxyear + 1)]
        for i in ndf.index:
            print('ROW ' + str(i))
            rdf = ndf[rlist]
            notmissing = [x for x in rdf if rdf.loc[i, x] != 'missing']
            print(ndf[notmissing].columns)


    def getSubCategoriesForVarsMatchingCriteria(self, categoryCriteriaList):
        subset = self.getCategoriesMatchingCriteria(categoryCriteriaList)
        i = len(categoryCriteriaList)
        return subset['C' + str(i + 1)].unique()
         
    ''' Take a list of Variables (from any year), and a variable x year matrix with the variable names 
    Input should be of the form: {'PSID_VariableName':'HumanReadableName',..} or ['PSID_VariableName'..]
    '''
    
    def getVariableSeriesesGivenSample(self, varDictOrList, yearsToInclude):
        subset = copy.deepcopy(self.dta)
        
        yearColumns = [x for x in subset.columns if x.startswith('Y')]
        categoryColumns = ['C0', 'C1','C2']

        if (isinstance(varDictOrList, dict)):
            isDict = True
        else:
            isDict = False
            
        dfNew = None
        
        for varName in varDictOrList: 
            if isDict:
                varLabel = varDictOrList[varName]
            else:
                varLabel = varName

            if (varName not in subset[yearColumns].values):
                raise Exception('This variable was not found in the crosswalk file:' + varName)
            
            indexVal = subset.index[subset[yearColumns].isin([varName]).any(axis=1)]
            row = subset.loc[indexVal, yearColumns + categoryColumns].copy()
            yearColumnsInt = [c.replace("Y", "") for c in yearColumns]
            yearColumnsIntToKeep = [c for c in yearColumnsInt if ((int(c) in yearsToInclude))]
            row.columns = row.columns.str.replace("Y", "")
            colsToKeep = yearColumnsIntToKeep + categoryColumns
            row=row[colsToKeep]
            row.rename(columns={'C0':'sourcefile', 'C1': 'category', 'C2': 'subcategory'}, inplace=True)
            
            row['count'] = (~row.isna()).sum(axis=1)
            
            row['label'] = varLabel
                
            if dfNew is None:
                dfNew = row
            else:
                dfNew = pd.concat([dfNew, row], ignore_index=True) 

        return dfNew        
        
        