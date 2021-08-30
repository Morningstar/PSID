# The PSID Financial Inequality Project

The PSID Financial Inequality Project is a Python application for analyzing the Panel Study of Income Dynamics 
 and generating a standardized dataset for research on wealth and income inequality.

This project was started by [Morningstar](https://www.morningstar.com) and was used to generate the report
[Unpacking Racial Disparities in Savings Rates](https://www.morningstar.com/content/dam/marketing/shared/pdfs/Research/Savings-Rates-Differences-By-Race.pdf ).
A short summary of the research can be found [in this article](https://www.morningstar.com/articles/1055633).

We hope you'll further improve and extend this ressearch. Read our [Contributors' Guide](https://github.com/Morningstar/PSID/blob/main/docs/CONTRIBUTING.md) for details. Morningstar uses an Apache 2.0 License for this and all open source projects.

## If you're looking for the data

In this repository, you'll find both the input data (most of which is extracted from [the PSID's main site](https://psidonline.isr.umich.edu/)) under the directory "inputData", and the output Data used in the report under "outputData".
Both contain zip files you'll need to extract before running the code.

For more information on the data files, see below under "File Structure".

    
## If you want to understand the methodology and how the code works 

There is a detailed writeup how the code works, including how savings rates and capital gains are calculated, in the Docs directory of the repo, [GuideToTheCode.docx](https://github.com/Morningstar/PSID/blob/main/docs/GuideToTheCode.docx)

In short though:
* The PSID Financial Inequality Project is divided into a set of classes, which are called as needed from a central “Controller.py” script. The Controller takes a parameter file (e.g., params_AllInequalityAnalyses_EnrichedPop.py) which specifies both which stages in the process to execute, and parameters specific to those stages. 
* Conceptually, we can think about the process in 9 stages.
    * Stages 1-4 are general purpose tools for using the PSID in a standardized, cleaned way.    
    * Stages 5-7 further process the specific data needed for analyzing wealth accumulation: active savings rates, capital gains, inheritances, etc.   
    * Step 8 outputs the particular analyses of wealth accumulation used in Morningstar’s report.  
    * Step 9 compares those results with prior research in the field. 
* In addition to the final output for Morningstar’s report (in a Excel file called “FiguresForPaper”), the code is designed to generate extensive data at each step along the way, so that other researchers can either depart from subsequent steps and generate their own analyses, or dig into the intermediate data to check for errors, etc.   
* For more information on the stages of the data processing code, the files generated along the way, and the core savings/cap gains calculations, [read the docs](https://github.com/Morningstar/PSID/blob/main/docs/GuideToTheCode.docx).

## If you want to run the analysis yourself  

1. Clone the Repo or Download  
2. Unzip the files in inputData (if you want to start from scratch) or outputData (if you want to go straight to analyzing the savings rate data)
3. Open the code in the Python editor of your choice.  A PyCharm project is provided for you convenience.  
4. Open src/Controller/controller.py. This is the heart of the project, and it is from here that each of the 9 stages of analysis are triggered, as described above and [here](https://github.com/Morningstar/PSID/blob/main/docs/GuideToTheCode.docx).
5. Open or create a parameter file, and turn on or off the stages you want, and the parameters you need.
6. Ensure that param file is included in / passed into controller.py, and run it.   

## File Structure

* docs: Where you'll find information on the methodology and code structure, License (Apache 2.0), and how to contribute to the project 
* inputData
    * PSIDFamilyFiles\_2021Extract\_EXTRACT\_BEFORE\_USING.zip:  All family and wealth variables from the PSID, for years with wealth data.  Drawn directly from the Data Center, since their Prepackaged Zip files appear to have errors in Net Wealth calculations 
    * PSIDFamilyData\_Prepackaged\_EXTRACT_BEFORE\_USING.zip: All family variables from the PSID, for years without wealth data.  A copy of the zip files on the PSID site. 
    * PSIDIndividualData_EXTRACT_BEFORE_USING.zip. ind2019er:  1968-2019 Individual-level data from the PSID 
    * InflationData_EXTRACT_BEFORE_USING.zip
        * CPI_Inflation:  Reference data used for inflating values to a common year. This is what it appears that Gittleman et al. (2004) used in their report on the topic, and this data is used in the code that replicates their findings
        * Fed_NIPA: Another source of inflation/deflation data. This is what Dynan et al. (2004) used in their report on the topic, and this data is used in the code that replicates their findings
* outputData
    * OutputData_EXTRACT_BEFORE_USING.zip:  
        * inputForMorningstarAnalysis_enrichedPop:  The processed, cleaned PSID data, right before it is subsetted and used for savings rates calculations.
        * morningstarOutput_enrichedPop: The detailed data used in the report, with savings rates and capital gains for each of ten asset classes, for each sequential two-period timeframe in the PSID (e.g., people's savings behavior from 2017 to 2019).
    * ReturnsData_EXTRACT_BEFORE_USING.zip: Some additional data on stock and bond returns, used in the modeling of capital gains. 
* R: two R scripts used in Morningstar's report, since Python doesn't go weighted Median Regressions well. 
* src
    * Controller: Holds the central controller (controller.py), and various parameter sets for different versions of the analysis.
    * DataQuality: Utility classes used to generate detailed diagnostic information about the data
    * Inflation:  Utility classes to handle inflation via CPI or NIPA
    * MStarReport: After the PSID data is cleaned and standardized, this handles the specific logic for Morningstar's analysis of the causes of savings rates differences by race 
    * PSIDProcessing: A set of classes used to cleanup and tame the PSID
    * Replication: Classes used to replicate results from Dynan et al. (2004) and Gittleman et al. (2004)
    * SavingsRates: Classes used to calculate asset-level and household-level savings rates and capital gains. Where the magic happens.
    * TaxSim: A Python interface to NBER's Taxsim, which calls Taxsim with PSID data and merges the results back in for use in the analysis.
    * ThirdPartyCode: A Sas File Reader borrowed from, and extending, another Python project: Tyler Abbott's Psid_Py package
* test: A few, slighly out of date, test cases for the core savings/capital gains methodology, and replication of Dynan and Gittleman.
 
### Data Structure

For many researchers, you'll want to go straight to the data, and skip the code that generated it. 
The best files to use to analyze savings rates, capital gains, and the racial wealth gap are in 
outputData/morningstarOutput_enrichedPop/TwoPeriod_WithSavings\_[StartYear]\_[EndYear]\_as\_[InflatedToYear].csv.  
Since saving (and cap gains) are always calculated over a period of time, the [StaryYear] and [EndYear] values indicate the saving/investing period.  
Many, but not all, of the variables are in real terms -- all inflated to a common year, as indicated by [InflatedToYear].

These files have all of the data used in our analysis, plus many other fields used for verification and debugging.  As such, they can be overwhelming.
Here is a short guide to the variable names:

### General Variable Structure

* All variables have the following structure: baseName_timePeriod
* The Time Period can take one of four forms:
    * \_[Year]:  This is a point-in-time observation, and a nomimal value. For example "raceR_2017" is the race of the main respondant in 2017.
    * \_[Year]\_as\_[InflatedToYear]: This is a point-in-time observatin, in a real value. For example inflatedPreTaxIncome\_2017\_as\_2019 is the pre-tax Income from 2017, inflated to 2019 dollars.  (The word 'inflated' at the beginning is used to reinfoce that fact, since knowing which income variable is used is of great importance.)
    * \_[StartYear]\_[EndYear]:  This is an across-time observation, and a nomimal value.  For example, averageNominalAfterTaxIncome\_AllYears\_2017\_2019 is the average (after tax) income from 2017 to 2019, not-inflated. 
    * \_[StartYear]\_[EndYear]\_as\_[InflatedToYear]:  This is an across-time observation, and a real value.  For example,  averageRealAfterTaxIncome\_AllYears\_2017\_2019\_as\_2019 is is the average (after tax) income from 2017 to 2019, inflated.
    
* The basename has an optional suffix for the unit of analysis:
    * Household (HH), respondent / head of household (R), spouse (S), or other.
    * For exampe: "hispanicR_2017" is a flag indicating if the respondent / head of household is Hispanic, as gathered in 2017, while "hispanicS_2017" is the same, for the spoouse (if present)

### Specific Fields of Interest

* Ids
    * familyInterviewId_[Year]: this is the primary Household-level ID from the PSID. There is no connection across years though (see PSID docs for why), so we create some: 
    * constantIndividualID: this is our constant id across time, for the head of household / respondent.  It's structured as the [OriginalFamilyId]_[SequenceNumberOfThatPersonInTheOriginalFamily]
* Demographics
    * There are some in the file, and many more in the overall PSID you can include as needed.
    * For example in the file currently: raceR_, NumChildrenInFU_, ageR_, educationYearsR_, genderR_, genderOfPartners_, inMixedRaceCouple_, householdStructure_, isMetroH_, stateH_FIPS_ (FIPS code for the state they live in)
* Weights
    * The PSID has two sets of weights -- household level longitundinal weights, and individual level cross-sectional weights.  
    * This file includes the household level weights, of the form: LongitudinalWeightHH_[Year].
    * See the PSID documentation for more information about the weights; they are not changed at all here.
* Income
    * The one you'll usually want: averageRealBeforeTaxIncome_AllYears_[Year]_as_[InflatedToYear] or averageRealAfterTaxIncome_AllYears_[Year]_as_[InflatedToYear]
    * Details: There are a few different Income fields to choose from.
        * Following Gittleman et al. (2004), we calculate the average (real) income over the period as the baseline for savings rates   
        * You may want to use the starting or ending income, or use nominal values. They are there as well.
* Net Worth
    * The one you'll usually want: inflatedNetWorthWithHomeAnd401k_AfterBalanceFillin_[Year]_as_[InflatedToYear]
    * Details: There are many Net Worth fields to choose from. 
        * In particular, the PSID does NetWorth with and without Homes.  
        * It doesn't include 401ks though, so we created a field that does.  
        * They provide a nominal value (naturally), but most 
        * It also has some missing balances that one can reasonably (without strong assumptions) fill in across years of data -- like where the balance is there one year, gone the next, but the person still says they have the account, and there's no change to it.     
        * The resulting field with this processing is the one above (inflatedNetWorthWithHomeAnd401k_AfterBalanceFillin).  
        * You may want to use a differnt combination of those processing steps though (nominal instead of real; don't fill in balances) - many of those are available as well.  
    * The Net Worth Change field you'll usually want is changeInRealNetWorthWithHomeAnd401k_AfterBalanceFillin_[StartYear]_[EndYear]_as_[InflatedToYear] 
* Cleaning
    * The file includes all households in the PSID (for the "enriched population" files; the "constant population" files, in the "constant population" directory includ only the original set of families and their decendants. 
    * We take the approach of labeling rows you MAY want to drop, but whether or not you drop them is up to you.
    * Use the three fields: cleaningStatus_[StartYear]_[EndYear] (shows issues in the quality of data that you can only see in longitundinal data, like average income being out of bounds, or a change in the household structure), cleaningStatus_[StartYear], cleaningStatus_[EndYear] (shows issues that occur within a given yaer -- like the HH is in prison)  to filter them as you choose.  
* Tax
    * The PSID provides limited Tax information, and only for the early years. This software calls the NBER's TaxSim program to get detailed tax information, for all years.
    * The fields are of the form [level]tax_[year].  Where [level] is one of ('si', 'fi') for state or federal income tax.   These are nominal values.
* Asset Level Savings, Capital Gains, etc.
    * These fields are of the form: [AssetType]_[Measurement]_[TimePeriod]
    * The [AssetType] is one of ('House', 'OtherRealEstate', 'Business', 'BrokerageStocks', 'CheckingAndSavings', 'Vehicle',
         'OtherAssets', 'AllOtherDebts', 'PrivateRetirePlan', 'EmployerRetirePlan')
    * Measurement is one of: 
        * ('CapitalGains', 'OpenCloseTransfers', 'Savings', 'TotalChangeInWealth') with a time period of the form \_[StartYear]\_[EndYear]\_as\_[InflatedToYear]: values for the given time period, inflated. Note these are NOT annual figures - they are for the entire time period  
        * ('Status'), with a time period of the form \_[StartYear]\_[EndYear]\_as\_[InflatedToYear]: a field providing the specific type of savings/cap gains calculation made for that household, based on data availability         
        * ('AN_TotalGrowthRate', 'AN_SavingsRate', 'AN_CapitalGainsRate'), with a time period of the form \_[StartYear]\_[EndYear]\_as\_[InflatedToYear]: Annualized rate value, where the rate is as % of STARTING NET WEALTH.  
        * ('_SinceLastQYr_AmountBought_'), (SinceLastQYr_AmountBought_), with a time period of with a time period of the form \_[Year]
* Asset Level Ownership and Value
    * These fields are of the form: [Measurement][AssetType]_[Year]
    * Measurement is one of ('has', 'valueOf').  The value field is nominal - straight from the PSID. 
* Household Level Savings, Capital Gains, etc.
    * These fields are of the form: [Measurement]\_[StartYear]\_[EndYear]\_as\_[InflatedToYear]
    * Where measurement is one of: ('Total_NetActiveSavings', 'Total_GrossSavings',
                                'Total_OpenCloseTransfers','Total_CapitalGains',
                                'largeGift_All_AmountHH', 'SmallGift_All_AmountHH',
                                'netAssetMove')
    * See the [GuideToTheCode.docx](https://github.com/Morningstar/PSID/blob/main/docs/GuideToTheCode.docx) for detailed information, but, in short:
        * 'Total_NetActiveSavings': this is our estimate of the dollar amount intentionally and actively saved during the period.
        * 'Total_GrossSavings': this is the sum of the individual asset-level saving vars, before adjusting for inheritances, etc.
        * 'Total_OpenCloseTransfers': this is the sum of the asset-level open/close transfer vars. Ie, when an account only existed for the start or end of the time period - this is a component in the active saving calculation. For example, if someone doesn't have a Brokerage account at the start of the period, and they do at the end, there isn't a asset-level saving rate we can calculate, but they did add that much money to saving, so it counts at a HH level.  
        * 'Total_CapitalGains': this is the sum of the individual asset-level capital gains vars
        * 'largeGift_All_AmountHH': how much money the HH received in large (>10k) gifts and inheritances
        * 'SmallGift_All_AmountHH': how much money the HH received in small (<=10k) gifts and inheritances
        * 'netAssetMove': the net effect of people moving in and out of the household, on household net worth
    * The saving rate:
        * activeSavingsRate_AnnualHH_\_[StartYear]\_[EndYear]\_as\_[InflatedToYear]. This is the annualized household saving rate, as % of average income
