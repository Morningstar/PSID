##################
## This is the parameter file used for the "Constant Population" analysis in Morningstar's report "Unpacking Racial Disparities in Savings Rates"
##################

import Controller.varsForInequalityAnalysis as varsForInequalityAnalysis

ProjectDirectory = "C:/Dev/src/MorningstarGithub/PSID"

params = {
    # What years should we analyze?
    'startYearInclusive': 1984,
    'endYearInclusive': 2019,
    'yearStep': 1,
    'yearsToInclude': list(range(1984, 2019 + 1, 1)),

    'dropAllNon1968Families' : True,

    # Directories to use -- please update these
    'familyWealthVarsWeNeed2019': varsForInequalityAnalysis.familyWealthVars,
    'individualVarsWeNeed2019': varsForInequalityAnalysis.individualVars,
    'individualVars_LoadRegardlessOfYear': varsForInequalityAnalysis.individualVars_LoadRegardlessOfYear,

    # Core Diectories (written in the style of constants, but likely shouldn't be)
    'BASE_OUTPUT_DIR': ProjectDirectory + '/outputData',
    'EXTRACTED_OUTPUT_SUBDIR': 'intermediateStages/extractedPSID',
    'MAPPED_OUTPUT_SUBDIR': 'intermediateStages/mappedAndrecodedPSID',
    'TAXSIM_OUTPUT_SUBDIR': 'intermediateStages/taxsim',
    'FINAL_PSID_OUTPUT_SUBDIR': 'processedPSID',
    'CLEAN_INEQUALITY_DATA': 'inputForMorningstarAnalysis_constantPop',
    'INEQUALITY_OUTPUT': 'morningstarOutput_constantPop',
    'DYNAN_OUTPUT_SUBDIR': 'dynanOutput',
    'GITTLEMAN_OUTPUT_SUBDIR': 'gittlemanOutput',
    'ZEWEDE_OUTPUT_SUBDIR': 'zewedeOutput',

    'PSID_DATA_DIR': ProjectDirectory + '/inputData',

    # What steps of the data preparation do we want to run?  Select these as needed
    'reloadRawData': False,
    'extractData': False,
    'recodeData': False,
    'callTaxsim': False,
    'addTaxFilesIgnoringMissing': False,
    'extractAndCombineInequalityData': False,
    'calcSavingsRates':False,
    'describeTimesSeries': False,
        'includeExtremeChangeAnalysis': False,

    # Which final report are we generating?
    'runSW_UnpackingSavingsReport': False,
    'runSW_AccumulatedWealthOverTime': True,
    'runDynanReplication' : False,
    'runGittlemanReplication' : False,
    'runZewdeReplication' : False,
}

# A simple helper to make it easier to use the params. From https://stackoverflow.com/questions/2352181/how-to-use-a-dot-to-access-members-of-dictionary
class dotdict(dict):
    """dot.notation access to dictionary attributes"""
    __getattr__ = dict.get
    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__
params = dotdict(params)
