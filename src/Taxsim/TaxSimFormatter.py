import pandas as pd
import ftplib 
import time
import os
import random
import string
import re

from PSIDProcessing import Extractor

'''
    This class takes PSID data, formats the relevant fields in Taxsim Format, 
    calls Taxsim 27 to calculate tax information, and saves the result.
    
    To do so, it builds on the following documention
        Info and online interface: http://users.nber.org/~taxsim/taxsim27/
        FTP Interface: http://users.nber.org/~taxsim/taxsim27/taxsim-ftp.html
        Instructions for PSID https://simba.isr.umich.edu/help/psid_taxsim.pdf

    It also adapts and translates previously published Stata code for calling Taxsim avaiable here, 
    http://users.nber.org/~taxsim/to-taxsim/, especially Eric Zwick's sample Stata code.
'''

''' Potential future extensions:

    Provide data for these fields:     
        dta['stcg'] = 0  # SHort term capital gains
        dta['ltcg'] = 0  # Long Term capital Gains  
        dta['otherprop'] = 0  # Other property income subject to NIIT, including unearned partnership and S-corp income rent non-qualified dividends capital gains distributions on form 1040 other income or loss not otherwise enumerated here
        dta['nonprop'] = 0 # Other non-property income not subject to Medicare NIIT such as: alimony fellowships state income tax refunds (itemizers only) Adjustments and items such as alimony paid Keogh and IRA contributions foreign income exclusion NOLs
    
        dta['rentpaid'] = 0 # Rent Paid (used only for calculating state property tax rebates)
        dta['otheritem'] = 0   # Other Itemized deductions that are a preference for the Alternative Minimum Tax. These would include Other state and local taxes (line 8 of Schedule A) plus local income tax Preference share of medical expenses Miscellaneous (line 27)
        dta['childcare'] = 0 # Child care expenses.

    Update Social Security Income to cover all SS benefits
    
    Create version to calculate taxes for other non-family people in the household    
'''


# Taxsim's output files have a serious problem - no real line delimitor.  So, we create our own.
ID_START_SINCE_TAXIM_HAS_NO_LINE_DELIMITOR = '9876789'  # A very unlikely sequence to occur on its own

def get_random_string(length):
    letters = string.ascii_lowercase + string.ascii_uppercase
    result_str = ''.join(random.choice(letters) for i in range(length))
    return result_str
    # print("Random string of length", length, "is:", result_str)

def calcAgeCounts(dta, year):
    ageVar = "ageI_" + str(year)
    employmentVar = "employmentStatusI_" + str(year)
    relationshipVar = "relationshipToR_" + str(year)
    relationshipMask = dta[relationshipVar].isin(["Child"])
    
    dep18 = len(dta.loc[
            relationshipMask & (
                    (dta[ageVar] < 19) | 
                    ((dta[ageVar] < 24) & (dta[employmentVar] == 'Student'))
                    )
                    ]) # Should be under 19 or under 24 and full time student
    depx =  dep18 # Should be number of people who are not working but are dependent 
    dep13 = len(dta.loc[dta[ageVar] < 13])
    dep17 = len(dta.loc[dta[ageVar] < 17])
    return pd.Series({'depx':depx, 'dep13': dep13, 'dep17': dep17, 'dep18': dep18}).to_frame().T

class TaxSimFormatter:
    
    def __init__(self, PSID_INPUT_DATA_DIR, OUTPUT_DATA_DIR): 
        self.psidFamilyDta = None
        self.psidIndividualDta = None
        self.tsDta = None
        self.psidDir = PSID_INPUT_DATA_DIR
        self.outputDir = OUTPUT_DATA_DIR
        self.year = None
        self.stateCodes = pd.read_csv(os.path.join(PSID_INPUT_DATA_DIR, "StateCodes_PSID_To_SOI.csv"))
    
    def getFamilyAges(self, dta):
        yr = str(self.year)
        ageVar = "ageI_" + yr

        sequenceVar = "sequenceNoI_" + yr
        indInterviewVar = "interviewId_" + yr
        employmentVar = "employmentStatusI_" + yr
        relationshipVar = "relationshipToR_" + yr

        inidvidualVars = [ageVar, 'longitudinalWeightI_' + yr, indInterviewVar, employmentVar, relationshipVar]
        individualData_NonHead = self.psidIndividualDta.loc[self.psidIndividualDta[sequenceVar] != 1, inidvidualVars].copy()
        individualData_NonHead = individualData_NonHead.loc[(~(individualData_NonHead[ageVar].isna())) & (individualData_NonHead[relationshipVar].isin(['Child']))].copy()

        temp = pd.merge(dta[['familyInterviewId']], 
                       individualData_NonHead, left_on = 'familyInterviewId', 
                            right_on = indInterviewVar, 
                            how = 'left')
                
        results = temp.groupby(['familyInterviewId']).apply(calcAgeCounts, self.year).reset_index()
        return results
            

    def convertToTaxSim(self, psidFamilyDta, psidIndividualDta, taxYear):
        '''
        Convert the relevant PSID fields into the specifc data format TaxSim needs
        :param psidFamilyDta: The PSID family data fields
        :type psidFamilyDta:  Data Frame
        :param psidIndividualDta:
        :type psidIndividualDta:  Data Frame
        :param taxYear:
        :type taxYear:
        :return:
        :rtype:
        '''

        self.psidFamilyDta = psidFamilyDta
        self.psidIndividualDta = psidIndividualDta
        self.year = taxYear
        
        dta = psidFamilyDta.copy()
        dta['taxsimid'] = ID_START_SINCE_TAXIM_HAS_NO_LINE_DELIMITOR + dta['familyInterviewId'].astype(str)  # list(range(1,len(dta)+1))
        dta['yearTax'] = taxYear
        
        dta = pd.merge(dta, self.stateCodes, left_on = "stateH", right_on = "PSID", how="left")
        dta.drop(columns={'FIPS'}, inplace=True)
        dta.rename(columns={'SOI':'state'}, inplace=True)

        # Currently we only support two statuses. More can could be extracted from PSID
        dta['mstat'] = 1  #1. single or head of household (unmarried)
        dta.loc[dta.martialStatusR == "Married", 'mstat'] = 2 # joint (married) 
        dta.loc[dta.wageIncomeS > 0, 'mstat'] = 2 # joint (married) 
        dta.loc[dta.ageS > 0, 'mstat'] = 2 # joint (married) 
        
        # dta.loc[dta.SpouseInFU, 'mstat'] = 2 # joint (married) 

        ''' Exaple from Zwick's sample code at http://users.nber.org/~taxsim/to-taxsim/psid-zwick/
         for a version of Taxsim with separate Head of Household option
        *** FIELD 4: Marital status => marital
        * Making single if never married, widowed, divorced, separated, or other.
        g marital = cond(marital_status_head != 1, 1, 2)
        *assert age_wife == 0 if marital == 1
        * Making head of household if unmarried with children.
        replace marital = 3 if marital == 1 & children > 0
    
        # From TaxSim27 Docs:
        1. single or head of household (unmarried)
        2. joint (married)
        6. separate (married). Note that Married-separate is not usually desirable under US tax law.
        8. Dependent taxpayer. (Typically child with income).
        ''' 
        
        # 6. separate (married). Note that Married-separate is not usually desirable under US tax law.
        # 8. Dependent taxpayer. (Typically child with income).
    
        dta.rename(columns={'ageR':'page'}, inplace=True)
        dta.rename(columns={'ageS':'sage'}, inplace=True)

        ageVars = self.getFamilyAges(dta)
        dta = pd.merge(dta, ageVars, left_on = 'familyInterviewId', right_on = 'familyInterviewId', how = 'left')
              
        '''
        dta['depx'] = dta.NumChildrenInFU # not quite, but ok approx for now 
        dta['dep13'] = 0 # not handling eligible child care expenses currently 
        dta['dep17'] = dta.NumChildrenInFU # not quite, but ok approx for now 
        dta['dep18'] = dta.NumChildrenInFU # not quite, but ok approx for now 
        '''
        
        
        dta.rename(columns={'wageIncomeR':'pwages'}, inplace=True) 
        dta.rename(columns={'wageIncomeS':'swages'}, inplace=True) # Note -- pre 1994? this is actually total labor income for the Spouse
        
        
        dta['dividends'] = dta.DividendsR.add(dta.DividendsS, fill_value=0)
        dta['intrec'] = dta.InterestIncomeR.add(dta.InterestIncomeS, fill_value=0)

        # Note Other authors skip these as well, saying PSID simply doesn't have the data it needs
        # TODO -- this should be expanded / fixed!
        dta['stcg'] = 0  # SHort term capital gains
        dta['ltcg'] = 0  # Long Term capital Gains  
        
        dta['otherprop'] = dta.RentIncomeR.add(dta.RentIncomeS, fill_value=0).add(dta.FarmIncomeRandS, fill_value=0).add(dta.BusinessAssetIncomeRandS, fill_value=0)  # Other property income subject to NIIT, including unearned partnership and S-corp income rent non-qualified dividends capital gains distributions on form 1040 other income or loss not otherwise enumerated here

        ''' From Zwick (http://users.nber.org/~taxsim/to-taxsim/psid-zwick/):
        g asset_income = rent_inc_head_gen + ///   RentIncomeR
                         farm_inc_head_gen + ///FarmIncomeRandS
                         unincorp_assetpt_inc_head_gen + ///  BusinessAssetIncomeRandS
                         gardening_inc_head_gen + ///
                         alimony_inc_head_gen + ///
                         rent_inc_wife_gen +   RentIncomeS
                         unincorp_assetpt_inc_wife_gen + ///   ABOVE
                         interest_inc_head_gen + interest_inc_wife_gen   InterestIncomeR + InterestIncomeS  -- NOTE this is now separte in TAXSIM and should not be included here
                         * This last row seems excluded in B&B. 
        g other_income = asset_income - alimony_paid
        '''

        dta['nonprop'] = 0 # Other non-property income not subject to Medicare NIIT such as: alimony fellowships state income tax refunds (itemizers only) Adjustments and items such as alimony paid Keogh and IRA contributions foreign income exclusion NOLs
        dta['pensions'] = dta.VAPensionIncomeR.add(dta.VAPensionIncomeS, fill_value=0).add(dta.PensionIncomeR, fill_value=0).add(dta.PensionIncomeS, fill_value=0).add(dta.AnnuityIncomeR, fill_value=0).add(dta.AnnuityIncomeS, fill_value=0).add(dta.IRAIncomeR, fill_value=0).add(dta.IRAIncomeS, fill_value=0).add(dta.OtherRetirementIncomeR, fill_value=0).add(dta.OtherRetirementIncomeS, fill_value=0) # Should this be included? 
                            
        dta['gssi'] = dta.ssIncomeR.add(dta.ssIncomeS, fill_value=0) # Incomplete? Fits Zwick, but should it include other types of SS?
        dta['ui'] = dta.UnemploymentIncomeR.add(dta.UnemploymentIncomeS, fill_value=0) 
        dta['transfers'] = dta.transferIncomeRandS
        
        dta['rentpaid'] = dta.RentPayment  # Rent Paid (used only for calculating state property tax rebates)
        ''' From Zwick
        g rent = cond(rent_amount < 99997 & rent_amount_unit != 9, rent_amount, 0)
        replace rent = 52*rent if rent_amount_unit == 3
        replace rent = 26*rent if rent_amount_unit == 4
        replace rent = 12*rent if rent_amount_unit == 5
        '''
        
        dta['proptax'] = dta.HomePropertyTaxAnnualHH
        dta['otheritem'] = 0   # Other Itemized deductions that are a preference for the Alternative Minimum Tax. These would include Other state and local taxes (line 8 of Schedule A) plus local income tax Preference share of medical expenses Miscellaneous (line 27)
        ''' From Zwick:
        g item_char = cond(itemized_charitable < 999997, itemized_charitable, 0)
        g item_med = cond(itemized_medical < 999997, itemized_medical, 0)
        g itemized_total = cond(whether_itemized == 1, item_char + item_med, 0)
        '''
        dta['childcare'] = 0 # Child care expenses.
        ''' From Zwick:
        g childcare = cond(childcare_expense < 999997, childcare_expense, 0)
        replace childcare = 52*childcare if childcare_expense_unit == 3
        replace childcare = 26*childcare if childcare_expense_unit == 4 
        replace childcare = 12*childcare if childcare_expense_unit == 5 
        '''

        # Note --  this field has many problems. Needs to be checked carefully
        dta['mortgage'] = dta.MortgagePaymentAnnualHH.sub(dta.HomePropertyTaxAnnualHH, fill_value=0).sub(dta.HomeInsuranceAnnualHH, fill_value=0) # incomplete should have other deductions, and should only ve

        # Taxsim data constraints
        dta.loc[dta.mortgage<=0,'mortgage'] = 0 
        dta.loc[dta.depx>10,'depx'] = 10
        dta.loc[dta.dep13>10,'dep13'] = 10
        dta.loc[dta.dep17>10,'dep17'] = 10
        dta.loc[dta.dep18>10,'dep18'] = 10

        # dta.loc[dta.pwages<=0,'pwages'] = 0
        # dta.loc[dta.swages<=0,'swages'] = 0
        dta.loc[dta.dividends<=0,'dividends'] = 0 

        dta.fillna(0, inplace=True)
        
        
        self.tsDta = dta


    def saveTaxSimInput(self):

        dta = self.extractData()
        if not os.path.exists(self.outputDir):
            os.makedirs(self.outputDir)

        dta.to_csv(os.path.join(self.outputDir, "taxsim_input_" + str(self.year) + ".csv"), header=False, index=False)
        
    def readTaxSimInput(self):
        self.tsDta = pd.read_csv(os.path.join(self.outputDir, "taxsim_input_" + str(self.year) + ".csv"), header=None, low_memory=False,
                        names=['taxsimid', 'yearTax',  'state',  'mstat', 'page', 'sage','depx', 'dep13', 'dep17', 'dep18','pwages', 'swages', 'dividends', 
                        'intrec', 'stcg', 'ltcg', 'otherprop', 'nonprop', 'pensions', 'gssi', 'ui', 'transfers', 'rentpaid', 'proptax', 
                        'otheritem', 'childcare', 'mortgage'])
        
        return self.tsDta

    def extractData(self):
        '''
        Take our Recoded PSID file, and extract the fields we need to pass to TaxSim
        '''

        # Taxsim needs data in a specific order:
        dta = self.tsDta[['taxsimid',  # any unique id -- For us, it is familyInterviewId
                        'yearTax',  # 
                        'state', # SOI code 
                        'mstat', # martial/filing status
                        'page', # Age of primary taxpayer December 31st of the tax year (or zero). Taxpayer age variables determine eligibility for additional standard deductions, personal exemption, EITC and AMT exclusion.
                        'sage',# Age of spouse (or zero).
                        'depx', # Number of dependents (part of personal exemption calculation).
                        'dep13', # Number of children under 13 with eligible child care expenses (Dependent Care Credit).
                        'dep17', # Number of children under 17 for the entire tax year (Child Credit).
                        'dep18', # Number of qualifying children for EITC. (Typically younger than 19 or younger than 24 and a full-time student).
                        'pwages', # Wage and salary income of Primary Taxpayer (include self-employment).
                        'swages', # Wage and salary income of Spouse (include self-employment). Note that this must be zero for non-joint returns.
                        'dividends', # Dividend income (qualified dividends only for 2003 on).
                        'intrec', # Interest Received (+/-)
                        'stcg', # Short Term Capital Gains or losses. (+/-)
                        'ltcg', # Long Term Capital Gains or losses. (+/-)
                        'otherprop', # Other property income subject to NIIT, including unearned partnership and S-corp income rent non-qualified dividends capital gains distributions on form 1040 other income or loss not otherwise enumerated here
                        'nonprop', # Other non-property income not subject to Medicare NIIT such as: alimony fellowships state income tax refunds (itemizers only) Adjustments and items such as alimony paid Keogh and IRA contributions foreign income exclusion NOLs
                        'pensions', # Taxable Pensions and IRA distributions
                        'gssi', # Gross Social Security Benefits
                        'ui', # Unemployment compensation received.
                        'transfers', # Other non-taxable transfer Income such as welfare workers comp veterans benefits child support that would affect eligibility for state property tax rebates but would not be taxable at the federal level.
                        'rentpaid', # Rent Paid (used only for calculating state property tax rebates)
                        'proptax', # Real Estate taxes paid. This is a preference for the AMT and is is also used to calculate state property tax rebates.
                        'otheritem', # Other Itemized deductions that are a preference for the Alternative Minimum Tax. These would include Other state and local taxes (line 8 of Schedule A) plus local income tax Preference share of medical expenses Miscellaneous (line 27)
                        'childcare', # Child care expenses.
                        'mortgage' # Deductions not included in item 25 and not a preference for the AMT, including (on Schedule A for 2009) Deductible medical expenses not included in Line 16 Motor Vehicle Taxes paid (line 7) Home mortgage interest (Line 15) Charitable contributions (Line 19) Casulty or Theft Losses (Line 20)
                        ]]
        return dta
    
    def readTaxSimOutput(self, year, tabDelimited=False):
        '''
        Read in the local copy of the output file
        :param year:
        :type year:
        :param tabDelimited:
        :type tabDelimited:
        :return:
        :rtype:
        '''

        if tabDelimited:
            taxsimFile = os.path.join(self.outputDir, "taxsim_" + str(year) + ".txt")
        else:
            taxsimFile = os.path.join(self.outputDir, "taxsim_" + str(year) + ".csv")
        
        if os.path.exists(taxsimFile):
            if tabDelimited:
                dta = pd.read_csv(taxsimFile, delim_whitespace=True, low_memory=False)
                dta.taxsim_id = dta.taxsim_id.replace(".", "")
            else:
                dta = pd.read_csv(taxsimFile)
            
            return dta
        else:
            return None
        
        '''
        FORMAT  
        # taxsim_id year state fiitax siitax fica frate srate ficar
        # 1. 2000 0 13025.00 .00 .00 20.00 .00 15.30
        
        v1 = taxsimid = Case ID
        v2 = year = Year
        v3 = state = State
        v4 = fiitax = Federal income tax liability including capital gains rates, surtaxes, AMT and refundable and non-refundable credits.
        v5 = siitax = State income tax liability
        v6 = fica = FICA (OADSI and HI, sum of employee AND employer)
        v7 = frate = federal marginal rate
        v8 = srate = state marginal rate
        v9 = ficar = FICA rate
        '''
        
    def callTaxSim(self):
        '''
        Call TaxSim, which has an unusual interface...
        Deposit the input data file onto Taxsim's FTP site, wait a while, then pick up the output file from the same site.
        '''
        
        # get file in memory
        inputDta = self.extractData()

        try:          
            # Open up FTP to Taxsim
            with ftplib.FTP('taxsimftp.nber.org') as ftp: 
                ftp.login(user='taxsim', passwd='02138')  # user anonymous, passwd anonymous@
                ftp.cwd('/tmp')
        
                inputFileName = "PSID_" + get_random_string(10)
                
                mappingFile = inputFileName + "_mapping.csv"

                inputFileNameLocal = os.path.join(self.outputDir, inputFileName)
                inputDta.to_csv(inputFileNameLocal, header=False, index=False)
    
                # outputFileName = inputFileName + '.taxsim'  # File format is different - dont Use
                outputFileName = inputFileName + '.txm27'
                # outputFileName = inputFileName + '.txm32'
                
                
                outputFileNameLocal = os.path.join(self.outputDir, outputFileName)
                    
                # Upload
                with open(inputFileNameLocal, 'rb') as fp:
                    
                    res = ftp.storlines("STOR " + inputFileName, fp)
                    
                    if not res.startswith('226 Transfer complete'):
                        print('Upload failed')
                        print(res)
                    
                time.sleep(5)
                                
                # Download
                if os.path.isfile(outputFileNameLocal):
                    os.remove(outputFileNameLocal)          

                with open(outputFileNameLocal, 'w') as fp:
                    
                    res = ftp.retrlines('RETR ' + outputFileName, fp.write)
                    
                    if not '226 Transfer complete' in res:
                        print('Check download - Taxsim gives errors no matter what here...')
                        print(res)

                # Get the message, if any
                '''
                if os.path.isfile(msgOutputFileNameLocal):
                    os.remove(msgOutputFileNameLocal)          

                with open(msgOutputFileNameLocal, 'w') as fp:
                    
                    res = ftp.retrlines('RETR ' + msgOutputFileName, fp.write)
                    
                    if not '226 Transfer complete' in res:
                        print('Download failed: ' + msgOutputFileNameLocal)
                        print(res)
                '''

                # If we got this far, the file is there!
                if os.path.exists(outputFileNameLocal):
                    with open(outputFileNameLocal, "r") as myfile:
                        data = myfile.read()
                    data=data.replace(ID_START_SINCE_TAXIM_HAS_NO_LINE_DELIMITOR, "\n")
                    data=re.sub("[^\S\r\n]+", ",", data)
                        
                    with open(os.path.join(self.outputDir, "taxsim_" + str(self.year) + ".csv"), 'w') as f:
                        f.write(data)
                                                    
                    outputDta = pd.read_csv(os.path.join(self.outputDir, "taxsim_" + str(self.year) + ".csv"))
                    
                    # Sometimes, Taxsim just doesn't return all of the rows.  Only a few hundred. Catch that.
                    if (len(outputDta) != len(inputDta)):
                        raise Exception("Received invalid data from Taxsim " + str(self.year) + " Length of Output is " + str(len(outputDta)) + " and input is " + str(len(inputDta)) + "." )
                            
                    return outputDta
                else:
                    raise Exception('Huh, didnt get the data at: ' + outputFileNameLocal)

        except ftplib.all_errors as e:
            print('FTP error:', e) 
            raise e


'''
Two helper functions for the most common use case -- do it all 
'''
def calcTaxAndSave(params, famExtractor, indExtractor):
    if famExtractor is None:
        famExtractor = Extractor.Extractor(params.PSID_DATA_DIR, params.yearsToInclude, params.familyWealthVarsWeNeed2019, None, source='family')
    famExtractor.readExtractedData(params.yearsToInclude, filePath = os.path.join(params.BASE_OUTPUT_DIR, params.MAPPED_OUTPUT_SUBDIR), fileNameBase= "extractedPSID_Mapped_Recoded_")

    if indExtractor is None:
        indExtractor = Extractor.Extractor(params.PSID_DATA_DIR, params.yearsToInclude, params.individualVarsWeNeed2019, params.individualVars_LoadRegardlessOfYear,source='individual')
    indExtractor.readExtractedData(params.yearsToInclude, filePath = os.path.join(params.BASE_OUTPUT_DIR, params.MAPPED_OUTPUT_SUBDIR), fileNameBase= "extractedPSID_Individual_Mapped_Recoded")

    for year in famExtractor.dataDict:
        yearData = famExtractor.dataDict[year]
        individualData = indExtractor.dataDict[0]
        tsFormatter = TaxSimFormatter(params.PSID_DATA_DIR, (params.BASE_OUTPUT_DIR + '/' + params.TAXSIM_OUTPUT_SUBDIR))
        tsFormatter.convertToTaxSim(yearData, individualData, year)
        tsDta = tsFormatter.extractData()
        tsFormatter.saveTaxSimInput()
        tsResults = tsFormatter.callTaxSim()


def combineFiles(params, famExtractor):
    '''
    Take the Taxsim output Tax Files, combine with the  PSID data
    :param params:
    :type params:
    :param famExtractor:
    :type famExtractor:
    :return:
    :rtype:
    '''
    if famExtractor is None:
        famExtractor = Extractor.Extractor(params.PSID_DATA_DIR, params.yearsToInclude, params.familyWealthVarsWeNeed2019, None, source='family')
    famExtractor.readExtractedData(params.yearsToInclude, filePath = os.path.join(params.BASE_OUTPUT_DIR, params.MAPPED_OUTPUT_SUBDIR), fileNameBase= "extractedPSID_Mapped_Recoded_")

    if not os.path.exists(os.path.join(params.BASE_OUTPUT_DIR, params.FINAL_PSID_OUTPUT_SUBDIR)):
        os.makedirs(os.path.join(params.BASE_OUTPUT_DIR, params.FINAL_PSID_OUTPUT_SUBDIR))

    for year in famExtractor.dataDict:
        yearData = famExtractor.dataDict[year]
        tsFormatter = TaxSimFormatter(params.PSID_DATA_DIR, (params.BASE_OUTPUT_DIR + '/' + params.TAXSIM_OUTPUT_SUBDIR))

        taxData = tsFormatter.readTaxSimOutput(year)


        if (taxData is not None):
            yearData = pd.merge(yearData, taxData, left_on = 'familyInterviewId', right_on = 'taxsim_id', how='left')
            yearData.to_csv(os.path.join(params.BASE_OUTPUT_DIR, params.FINAL_PSID_OUTPUT_SUBDIR, "extractedPSID_withMRTax_" + str(year) + ".csv"), index=False)
        else:
            yearData['fiitax'] = None
            yearData['siitax'] = None
            yearData.to_csv(os.path.join(params.BASE_OUTPUT_DIR, params.FINAL_PSID_OUTPUT_SUBDIR, "extractedPSID_withMRTax_" + str(year) + ".csv"), index=False)

