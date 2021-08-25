##################
## This is the parameter file used for a single analysis of the "Constant Population" analysis in Morningstar's report "Unpacking Racial Disparities in Savings Rates",
## in which we check if a change in savings rates in 1999 was due to the inclusion of new Retirement data (it wasn't)
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

    # Core Diectories (written in the style of constants, but likely shouldn't be
    'BASE_OUTPUT_DIR': ProjectDirectory + '/outputData',
    'EXTRACTED_OUTPUT_SUBDIR': 'intermediateStages/extractedPSID',
    'MAPPED_OUTPUT_SUBDIR': 'intermediateStages/mappedAndrecodedPSID',
    'TAXSIM_OUTPUT_SUBDIR': 'intermediateStages/taxsim',
    'FINAL_PSID_OUTPUT_SUBDIR': 'processedPSID',
    'CLEAN_INEQUALITY_DATA': 'inputForMorningstarAnalysis_constantPop_NoRetirementSavings',
    'INEQUALITY_OUTPUT': 'morningstarOutput_constantPop_NoRetirementSavings',
    'DYNAN_OUTPUT_SUBDIR': 'dynanOutput',
    'GITTLEMAN_OUTPUT_SUBDIR': 'gittlemanOutput',
    'ZEWEDE_OUTPUT_SUBDIR': 'zewedeOutput',

    'PSID_DATA_DIR': ProjectDirectory + '/inputData',

    # What parts of the code do you want to run?  Select these as needed
    'reloadRawData': False,
    'extractData': False,
    'recodeData': False,
    'callTaxsim': False,
    'addTaxFilesIgnoringMissing': False,
    'extractAndCombineInequalityData': False,
    'calcSavingsRates':False,
        'excludeRetirementSavings': True,
    'describeTimesSeries': False,
        'includeExtremeChangeAnalysis': False,
    'analyzeTimesSeries': True,
        'doDynanReplication' : False,
        'doGittlemanReplication' : False,
        'doZewdeReplication' : False,
}

# A simple helper to make it easier to use the params. From https://stackoverflow.com/questions/2352181/how-to-use-a-dot-to-access-members-of-dictionary
class dotdict(dict):
    """dot.notation access to dictionary attributes"""
    __getattr__ = dict.get
    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__
params = dotdict(params)
