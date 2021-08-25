# Overview: The PSID Financial Inequality Project

The PSID Financial Inequality Project is a Python application for analyzing the Panel Study of Income Dynamics 
 and generating a standardized dataset for research on wealth and income inequality.

This project was started by [Morningstar](https://www.morningstar.com) and was used to generate the report
[Unpacking Racial Disparities in Savings Rates](https://www.morningstar.com/content/dam/marketing/shared/pdfs/Research/Savings-Rates-Differences-By-Race.pdf ).
A short summary of the research can be found [in this article](https://www.morningstar.com/articles/1055633).

We hope you'll further improve and extend this ressearch. Read our [Contributors' Guide](https://github.com/Morningstar/PSID/blob/main/docs/CONTRIBUTING.md) for details. Morningstar uses an Apache 2.0 License for this and all open source projects.

# If you're looking for the data

In this repository, you'll find both the input data (most of which is extracted from [the PSID's main site](https://psidonline.isr.umich.edu/)) under the directory "inputData", and the output Data used in the report under "outputData".
Both contain zip files you'll need to extract before running the code.

For more information on the data files, see below under "File Structure".

    
# If you want to understand the methodology and how the code works 

There is a detailed writeup how the code works, including how savings rates and capital gains are calculated, in the Docs directory of the repo, [GuideToTheDoc.docx](https://github.com/Morningstar/PSID/blob/main/docs/GuideToTheCode.docx)

In short though:
* The PSID Financial Inequality Project is divided into a set of classes, which are called as needed from a central “Controller.py” script. The Controller takes a parameter file (e.g., params_AllInequalityAnalyses_EnrichedPop.py) which specifies both which stages in the process to execute, and parameters specific to those stages. 
* Conceptually, we can think about the process in 9 stages.
    * Stages 1-4 are general purpose tools for using the PSID in a standardized, cleaned way.    
    * Stages 5-7 further process the specific data needed for analyzing wealth accumulation: active savings rates, capital gains, inheritances, etc.   
    * Step 8 outputs the particular analyses of wealth accumulation used in Morningstar’s report.  
    * Step 9 compares those results with prior research in the field. 
* In addition to the final output for Morningstar’s report (in a Excel file called “FiguresForPaper”), the code is designed to generate extensive data at each step along the way, so that other researchers can either depart from subsequent steps and generate their own analyses, or dig into the intermediate data to check for errors, etc.   
* For more information on the stages of the data processing code, the files generated along the way, and the core savings/cap gains calculations, [read the docs](https://github.com/Morningstar/PSID/blob/main/docs/GuideToTheCode.docx).

# If you want to run the analysis yourself  

1. Clone the Repo or Download  
2. Unzip the files in inputData (if you want to start from scratch) or outputData (if you want to go straight to analyzing the savings rate data)
3. Open the code in the Python editor of your choice.  A PyCharm project is provided for you convenience.  
4. Open src/Controller/controller.py. This is the heart of the project, and it is from here that each of the 9 stages of analysis are triggered, as described above and [here](https://github.com/Morningstar/PSID/blob/main/docs/GuideToTheCode.docx).
5. Open or create a parameter file, and turn on or off the stages you want, and the parameters you need.
6. Ensure that param file is included in / passed into controller.py, and run it.   

# File Structure

* docs: Where you'll find information on the methodology and code structure, License (Apache 2.0), and how to contribute to the project 
* inputData
    * PSIDFamilyFiles_2021Extract_EXTRACT_BEFORE_USING.zip:  All family and wealth variables from the PSID, for years with wealth data.  Drawn directly from the Data Center, since their Prepackaged Zip files appear to have errors in Net Wealth calculations 
    * PSIDFamilyData_Prepackaged_EXTRACT_BEFORE_USING.zip: All family variables from the PSID, for years without wealth data.  A copy of the zip files on the PSID site. 
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
 
