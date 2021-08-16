import Controller.varsForInequalityAnalysis as varsForInequalityAnalysis

params = {
    # What years should we analyze?
    'startYearInclusive': 1984,
    'endYearInclusive': 2019,
    'yearStep': 1,
    'yearsToInclude': list(range(1984, 2019 + 1, 1)),

    'dropAllNon1968Families' : False,

    # Directories to use -- please update these
    'familyWealthVarsWeNeed2019': varsForInequalityAnalysis.familyWealthVars,
    'individualVarsWeNeed2019': varsForInequalityAnalysis.individualVars,
    'individualVars_LoadRegardlessOfYear': varsForInequalityAnalysis.individualVars_LoadRegardlessOfYear,

    # Core Diectories (written in the style of constants, but likely shouldn't be
    'BASE_OUTPUT_DIR': 'C:/dev/sensitive_data/InvestorSuccess/Inequality',
    'EXTRACTED_OUTPUT_SUBDIR': 'extractedPSID',
    'MAPPED_OUTPUT_SUBDIR': 'mappedAndrecodedPSID',
    'TAXSIM_OUTPUT_SUBDIR': 'taxsim',
    'FINAL_PSID_OUTPUT_SUBDIR': 'finalInputPSID',
    'CLEAN_INEQUALITY_DATA': 'inequalityInput_enrichedPop',
    'INEQUALITY_OUTPUT': 'inequalityOutput_enrichedPop',
    # 'SW_OUTPUT_SUBDIR': 'swOutput',
    'DYNAN_OUTPUT_SUBDIR': 'dynanOutput',
    'GITTLEMAN_OUTPUT_SUBDIR': 'gittlemanOutput',
    'ZEWEDE_OUTPUT_SUBDIR': 'zewedeOutput',

    'PSID_DATA_DIR': 'C:/dev/public_data/PSID',

    # What steps of the data preparation do we want to run?  Select these as needed (these are in order)
    'reloadRawData': False,
    'extractData': False,
    'recodeData': False,
    'callTaxsim': False,
    'addTaxFilesIgnoringMissing': False,
    'extractAndCombineInequalityData': False,
    'calcSavingsRates':False,
    'describeTimesSeries': False, # Time consuming.  Skip if not needed
        'includeExtremeChangeAnalysis': False,  # Especially Time consuming.  Skip if not needed

    # Which final report are we generating?
    'runSW_UnpackingSavingsReport': False,
    'runSW_AccumulatedWealthOverTime': False,
    'runDynanReplication' : False,
    'runGittlemanReplication' : True,
    'runZewdeReplication' : True,
}


# A simple helper to make it easier to use the params. From https://stackoverflow.com/questions/2352181/how-to-use-a-dot-to-access-members-of-dictionary
class dotdict(dict):
    """dot.notation access to dictionary attributes"""
    __getattr__ = dict.get
    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__
params = dotdict(params)
