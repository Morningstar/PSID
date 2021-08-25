'''
This is the central controller for the PSID Financial Inequality Project. It controls the laoding, processing, and analysis of PSID family and wealth data from 1984 to 2019.
It uses an imported parameter file to selectively switch on and off steps of this process.
Each step can be run separately (provided the necessary input files), to make analysis and debugging more efficient.
'''

import PSIDProcessing.Extractor as Extractor
import PSIDProcessing.FamilyDataRecoder as FamilyDataRecoder
import PSIDProcessing.IndividualDataRecoder as IndividualDataRecoder
import PSIDProcessing.RawLoader as RawLoader
import Taxsim.TaxSimFormatter as TaxSimFormatter
import SavingsRates.InequalityDataPrep as InequalityDataPrep
import SavingsRates.CalcSavingsRates as CalcSavingsRates
import DataQuality.LongitudinalDescriber as LongitudinalDescriber
import DataQuality.CrossSectionalDescriber as CrossSectionalDescriber
import MStarReport.SWAnalysisPerPeriod as SWAnalysisPerPeriod
import MStarReport.SWAnalysisLongTerm as SWAnalysisLongTerm
import Replication.DynanAnalysis as DynanAnalysis
import Replication.ZewdeAnalysis as ZewdeAnalysis
import Replication.GittlemanAnalysis as GittlemanAnalysis
import os
import pandas as pd

###
# Pick which set of params to use. This could also be passed in from command line / main
# These are the specific parameter files used in Morningstar's Report; you can and should create your own.
###
from Controller.params_AllInequalityAnalyses_EnrichedPop import params as params
# from Controller.params_AllInequalityAnalyses_ConstantPop_NoRetirement import params as params
# from Controller.params_AllInequalityAnalyses_ConstantPop import params as params


def main():

    # Step 1: Read PSID SAS file and Converts to CSV (forceReload ignores CSV if already there)
    if (params.reloadRawData):
        loader = RawLoader.RawLoader(params.PSID_DATA_DIR, params.yearsToInclude)
        # loader.loadRawPSID_FamilyOnly()
        loader.loadRawPSID_All()

    # Step 2: Read Raw PSID CSV files and extract relevant variables.
    # This must be rerun each time the VarsWeNeed are changed
    if params.extractData:
        (famExtractor, indExtractor) = Extractor.extractAndSave(params)
    else:
        famExtractor = None
        indExtractor= None
        
    # Step 3: Map the extracted variables into standard names
    if (params.recodeData):
        FamilyDataRecoder.recodeAndSave(params, famExtractor, indExtractor)

    # Step 4a: Calculate Taxes by calling the NBER TaxSim
    if (params.callTaxsim):
        TaxSimFormatter.calcTaxAndSave(params, famExtractor, indExtractor)

    # Step 4b: Combine the TaxSim data with our PSID data
    if (params.addTaxFilesIgnoringMissing):
        TaxSimFormatter.combineFiles(params, famExtractor)

    # Step *: Here is where you can do extra processing, imputation etc - usng information across the timespan to fill in data
    '''
    if (params.fillInDataAcrossYears):
        filler = CrossYearDataFillin.CrossYearDataFillin(
            baseDir = params.BASE_OUTPUT_DIR,
            familyInputSubDir = params.FINAL_PSID_OUTPUT_SUBDIR,
            familyBaseName = "extractedPSID_withMRTax_",
            individualInputSubDir = params.MAPPED_OUTPUT_SUBDIR,
            individualBaseName = "extractedPSID_Individual_Mapped_Recoded",
            outputSubDir = params.CLEAN_INEQUALITY_DATA,
            tsInputBaseName = "",
            tsOutputBaseName = "",
            )
        filler.doIt(yearsToInclude = params.yearsToInclude)
    '''

    # Step 5: Extract the data we need specifically for savings rates analyses, then create Two-Period Time Series Files, across each year with wealth data
    # The resulting Two-Period Time Series files are the basis for our savings analysis - they provide stock and flow data by asset class
    if (params.extractAndCombineInequalityData):
        prepper = InequalityDataPrep.InequalityDataPrep(
            baseDir = params.BASE_OUTPUT_DIR,
            familyInputSubDir = params.FINAL_PSID_OUTPUT_SUBDIR,
            familyBaseName = "extractedPSID_withMRTax_",
            individualInputSubDir = params.MAPPED_OUTPUT_SUBDIR,
            individualBaseName = "extractedPSID_Individual_Mapped_Recoded",
            outputSubDir = params.CLEAN_INEQUALITY_DATA,
            inputBaseName = "",
            outputBaseName = "",
            useOriginalSampleOnly = params.dropAllNon1968Families,
            )
        prepper.doIt()

    # Step 6: Calculate Savings Rates and Capital Gains - First at an household-by-asset level, then at the household level
    if (params.calcSavingsRates):
        if 'excludeRetirementSavings' in params:
            excludeRetirementSavings = params.excludeRetirementSavings  # Retirement data was only added in 1999. To remove the effect this might have on long-term time series, this flag removes it.
        else:
            excludeRetirementSavings = False

        calcer = CalcSavingsRates.CalcSavingsRates(
            baseDir = params.BASE_OUTPUT_DIR,
            familyInputSubDir = params.CLEAN_INEQUALITY_DATA,
            inputBaseName = "",
            outputBaseName = "WithSavings_",
            outputSubDir = params.INEQUALITY_OUTPUT,
            )
        # Create savings rates for everyone -- we'll subset who we want to analyze later
        calcer.doIt(useCleanedDataOnly = False, excludeRetirementSavings = excludeRetirementSavings)

    # Step 7: Run some descriptive stats & Check Quality of the Data
    if (params.describeTimesSeries):

        describer = CrossSectionalDescriber.CrossSectionalDescriber(
            baseDir = params.BASE_OUTPUT_DIR,
            inputSubDir = params.CLEAN_INEQUALITY_DATA,
            inputBaseName = "",
            outputBaseName = "",
            outputSubDir = params.CLEAN_INEQUALITY_DATA + '/descriptives'
            )
        describer.doIt(useCleanedDataOnly = True)

        describer = LongitudinalDescriber.LongitudinalDescriber(
            baseDir = params.BASE_OUTPUT_DIR,
            inputSubDir = params.INEQUALITY_OUTPUT,
            inputBaseName = "WithSavings_",
            outputBaseName = "WithSavings_",
            outputSubDir = params.INEQUALITY_OUTPUT + '/descriptives',
            includeChangeAnalysis=params.includeExtremeChangeAnalysis
            )
        describer.doIt(useCleanedDataOnly = True)

        
    # Step 8: Conduct Regressions for Morningstars Report, Summarize Results
    if (params.runSW_UnpackingSavingsReport):
        print("##########################################\r\n Starting Per-Period Analyis\r\n")
        analyzer = SWAnalysisPerPeriod.SWAnalysisPerPeriod(
            baseDir = params.BASE_OUTPUT_DIR,
            inputSubDir = params.INEQUALITY_OUTPUT,
            inputBaseName = "WithSavings_",
            outputBaseName = "WithSavings_",
            outputSubDir = params.INEQUALITY_OUTPUT + '/analyses',
            useOriginalSampleOnly = params.dropAllNon1968Families,
            )
        analyzer.doIt(useCleanedDataOnly = True)

    if (params.runSW_AccumulatedWealthOverTime):
        print("##########################################\r\n Starting Long term Analyis\r\n")
        analyzer = SWAnalysisLongTerm.SWAnalysisLongTerm(
            baseDir = params.BASE_OUTPUT_DIR,
            inputSubDir = params.INEQUALITY_OUTPUT,
            inputBaseName = 'WithSavings_',
            outputSubDir = params.INEQUALITY_OUTPUT + '/analyses',
            outputBaseName = 'wealthChangeAcrossTime'
        )
        analyzer.doIt(1994, 2007, 2019)
        # analyzer.doIt(2007, 2019, 2019)
        analyzer.doIt(2009, 2019, 2019)
        analyzer.doIt(1999, 2019, 2019)
        analyzer.doIt(1984, 2019, 2019)

    # Step 9: Replicate Prior Reserch in the Field
    if params.runDynanReplication:
        analyzer = DynanAnalysis.DynanAnalysis(
            baseDir = params.BASE_OUTPUT_DIR,
            familyInputSubDir = params.FINAL_PSID_OUTPUT_SUBDIR,
            familyBaseName = "extractedPSID_withMRTax_",
            individualInputSubDir = params.MAPPED_OUTPUT_SUBDIR,
            individualBaseName = "extractedPSID_Individual_Mapped_Recoded",
            outputSubDir = params.DYNAN_OUTPUT_SUBDIR
        )
        analyzer.doIt()

    if params.runGittlemanReplication:
        analyzer = GittlemanAnalysis.GittlemanAnalysis(
            baseDir = params.BASE_OUTPUT_DIR,
            familyInputSubDir = params.FINAL_PSID_OUTPUT_SUBDIR,
            familyBaseName = "extractedPSID_withMRTax_",
            individualInputSubDir = params.MAPPED_OUTPUT_SUBDIR,
            individualBaseName = "extractedPSID_Individual_Mapped_Recoded",
            outputSubDir = params.GITTLEMAN_OUTPUT_SUBDIR
            )
        analyzer.doIt()

    if params.runZewdeReplication:
        analyzer = ZewdeAnalysis.ZewdeAnalysis(
            baseDir = params.BASE_OUTPUT_DIR,
            familyInputSubDir = params.MAPPED_OUTPUT_SUBDIR,
            familyBaseName = "extractedPSID_Mapped_Recoded_",
            individualInputSubDir = params.MAPPED_OUTPUT_SUBDIR,
            individualBaseName = "extractedPSID_Individual_Mapped_Recoded",
            outputSubDir = params.ZEWEDE_OUTPUT_SUBDIR
            )
        analyzer.doIt()




''' Allow execution from command line, etc'''    
if __name__ == "__main__":
    main()
