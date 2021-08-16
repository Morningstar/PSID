
individualVars_LoadRegardlessOfYear = {
    'ER30001': 'interviewId',
    'ER30002': 'personId',  # ER30002 "PERSON NUMBER 68" NUM(3.0) # ONLY available in 1968
}

# Load these vars for EVERY YEAR
individualVars = {
    'ER30002': 'personId', # ER30002 "PERSON NUMBER 68" NUM(3.0) # ONLY available in 1968
    'ER34501': 'interviewId', # "2017 INTERVIEW NUMBER"
    'ER34502': 'sequenceNoI', # 'SEQUENCE NUMBER 17'
    'ER34503': 'relationshipToR', # "RELATION TO REFERENCE PERSON 17"
    'ER34516': 'employmentStatusI', # "EMPL STATUS 79" 

    # LocationVars: Only Available in 1997 and 1999
    'ER33524': 'stateBornI',
    'ER33525': 'countryBornI',
    'ER33526': 'livedInUSIn68I',

    'ER34508': 'movedInOutI', # "WHETHER MOVED IN/OUT 17"
    'ER34504': 'ageI', # Age of Individuals
    'ER34506': 'yearOfBirthI', # "YEAR IND BORN"
    'ER34650': 'longitudinalWeight_Combined_Post1996I',  # "CORE/IMM INDIVIDUAL LONGITUDINAL WT 17"
    # 'ER30805': 'longitudinalWeight_WithLatino_1990to1992I', #
    # 'ER33277': 'longitudinalWeight_WithLatino_1993to1995I', #  yr 1993-1996
    'ER33318': 'longitudinalWeight_Core_1993to1996I', #  yr 1993-1996
    'ER30803': 'longitudinalWeight_Core_1968to1992I', #  yr < 1992

    # TODO -- create a new Family level Weight that adds up the cross-sectional weight and fills in the missing years of data in the Family Level Var
    'ER34651': 'crossSectionalWeight_Combined_Post1996I',  #  "CORE/IMM INDIVIDUAL CROSS-SECTION WT 17" NUM(5.0)

}
familyWealthVars = {
    # Ids 
    'ER66009': 'familyId1968', # "1968 FAMILY IDENTIFIER"
    'ER66002': 'familyInterviewId', #  "Current Year FAMILY INTERVIEW (ID) NUMBER"
    'ER71560': 'householdId', #  "HOUSEHOLD ID #"   (Current Year simplification)
        
    # Family Weights
    'ER71570':'LongitudinalWeightHH_1997to2017',  # "2017 CORE/IMMIGRANT FAM WEIGHT NUMBER 1"  -- 1997 on
    'V21547': 'LongitudinalWeightHH_1968to1992',  # orig weights
    'ER9251': 'LongitudinalWeightHH_1993to1996',  # CHECK -- does this include immigrant sample?

    'ER71571': 'CrossSectionalWeightHH_1997to2003_and_2017to2019', # "2017 CROSS-SECTIONAL FAMILY WEIGHT"  -- only valid for 2017; added only in second release of data

    # Family Unit (FU) Details
    'ER66016': 'NumPeopleInFU', # "# IN FU"
    'ER67399': 'SpouseInFU',  #  "G49 WTR SPOUSE IN FU NOW"         
        'V16973': 'WifeInFU_Pre94', # D1 CHKPT  1989 Var; Used before 1994 - combine with Spouse
    'ER66007': 'ChangeInCompositionFU', # "FAM COMP CHANGE
    'V17611': 'ChangeInCompositionFU_1989FiveYear', # "FAM COMP CHANGE 1984-89"
    'ER66156': "MovedR", # A18. Have you (HEAD) moved any time since the spring of

    'ER66021': 'NumChildrenInFU', # "# CHILDREN IN FU"
    'ER66023': 'NumOthersInHU', # '"# NONFU SHARING HU"

    # Location Vars
    'ER66003': 'stateH', # "CURRENT STATE" (PSID Code)
    'ER71530': 'regionH', # 'CURRENT REGION" NUM(1.0)
    'ER71531': 'isMetroH_2015on', # "METRO/NONMETRO INDICATOR" NUM(1.0): 2015, 2017, 2019 ONY
    'ER58216': 'bealeCollapse_1994to2013', # "RURAL-URBAN CODE (BEALE-COLLAPSED)" - 9 and 10 combined

    'ER71532': 'metroSizeH',  #  "BEALE RURAL-URBAN CODE" NUM(2.0)   Suppressed
    'ER71533':  'sizeLargestCityH', # '"SIZE LARGEST CITY IN COUNTY" NUM(1.0) # Suppressed

    'ER71534': 'regionGrewUpR', # ER71534 "REGION REFERENCE PERSON GREW UP" NUM(1.0)
    'ER71535': 'geoMobilityR',  # ER71535 "RP GEOGRAPHIC MOBILITY" NUM(1.0)
    'ER71536': 'regionGrewUpS', #  "REGION SP GREW UP" NUM(1.0)
    'ER71537': 'geoMobilityS', # "SP GEOGRAPHIC MOBILITY" NUM(1.0)

    'ER70877': 'stateGrewUpR',
    'ER70739': 'stateGrewUpS',
 
    # Errors
    'ER31996': 'SampleErrorStratum', # SAMPLING ERROR STRATUM
    'ER31997': 'SampleErrorCluster', #  'SAMPLING ERROR CLUSTER

    #############
    # Immigration
    #############
    'ER70875': 'firstYearInUS_R', # 2017 & 2019 only "L33YR YEAR CAME TO UNITED STATES-RP"
    'ER70737': 'firstYearInUS_S', # 2017 & 2019 only

    'ER71005': 'englishSpokenMostOftenR', # "IMM8 WTR ENGLISH/OTR LANG MOST OFTEN-RP" # 2017 & 2019 only
    'ER71006': 'understandEnglishR', # 2017-2019 only "IMM9 HOW WELL UNDERSTAND ENGLISH-RP"
    'ER71007': 'speakEnglishR', # 2017-2019 only "IMM10 HOW WELL SPEAK ENGLISH-RP"
    'ER71008': 'readEnglishR', # 2017-2019 only "IMM11 HOW WELL READ ENGLISH-RP"
    'ER71009': 'writeEnglishR', # 2017-2019 only "IMM12 HOW WELL WRITE ENGLISH-RP"

    'ER70980': 'immigrantStatusIn2016_HH', # 2017 & 2019 only "IMM 2016 SCREENING STATUS FOR THIS FU";


    ##############
    # Demographics
    ##############
    # Ethnicity     / Race
    'ER70881': 'hispanicR', #  "L39 SPANISH DESCENT-RP"   # 1985-1996, 2005-2017
    'ER70882': 'raceR1', #  "L40 RACE OF REFERENCE PERSON-MENTION 1"
    'ER70883': 'raceR2', #  "L40 RACE OF REFERENCE PERSON-MENTION 2"

    'ER70743': 'hispanicS', #   K39 SPANISH DESCENT-SPOUSE
    'ER70744': 'raceS1', #  "K40 RACE OF SPOUSE-MENTION 1 # 1985 on
    'ER70745': 'raceS2', #  "K40 RACE OF SPOUSE-MENTION 2" # 1985 on

    # Age and Gender
    'ER66017': 'ageR', #  "AGE OF REFERENCE PERSON" # 40 Obs
    'ER66018': 'genderR', #  "SEX OF REFERENCE PERSON" # 40 obs
    
    'ER66019': 'ageS', #  "AGE OF SPOUSE"  40 obs
    'ER66020': 'genderS', #  "SEX OF SPOUSE"  3 obs - 2015 on
    
    
    # Martial Status     
    'ER66024': 'martialStatusR', #  "REFERENCE PERSON MARITAL STATUS"  # 31 Obs
    'ER71540': 'martialStatusGenR', #  "MARITAL STATUS-GENERATED" # 40 Obs

    # Education
    'ER71538': 'educationYearsR', #  "COMPLETED ED-RP" # 27 Obs  Missing from 1985 to 1990; use 1989 V17545 instead
        'V17545': 'educationYearsR_85to90',
    'ER71539': 'educationYearsS', #  "COMPLETED ED-SP" # 27 Obs  Missing from 1985 to 1990; Use 1989 V17546 instead
        'V17546': 'educationYearsS_85to90',
    
    # Institutionalization
    'ER66008': 'institutionLocationHH', #  "TYPE INSTITUTION" (armed forces, prison, etc) -- very rare

    ##############
    # Employment Status
    ##############
    'ER66164': 'IsWorkingR', # "BC1 EMPLOYMENT STATUS-1ST MENTION"  # 14 obs
        'V16655': 'IsWorkingR_Pre1994',
    'ER66165': 'IsWorking_SecondMentionR', # ""BC1 EMPLOYMENT STATUS-2ND MENTION"
    'ER67986': 'IsWorking_Test2R', #  "P0 WTR WORKING NOW - RP"
    'ER66167': 'YearRetiredR', # "BC2 YEAR RETIRED"  # 30 obs
    'ER68033': 'AgePlanToRetireR', # "P40 AGE PLAN STOP WORK - RP"  # 10 obs, 1999+

    'ER66439': 'IsWorkingS', # "DE1 EMPLOYMENT STATUS-1ST MENTION"     # 14 -- 1994+
    'ER66140': 'IsWorking_SecondMentionS', # ""DE1 EMPLOYMENT STATUS-2ND MENTION"
    'ER68203': 'IsWorking_Test2S', # "P0 WTR WORKING NOW - SP" # 10  1999+

    "ER66242": 'reasonLeftLastJobR', # "BC51 WHY LAST JOB END (RP-U)"  # from 1988 on is CHANGE EMPLOYER only; before included promotions
    "ER66517": 'reasonLeftLastJobS', # "DE51 WHY LAST JOB END (SP-U)" NUM(1.0)  # from 1988 on is CHANGE EMPLOYER only; before included promotions

    "ER66179": "dateStarted_Job1_Month_R", #  "BC6 BEGINNING MONTH--JOB 1" NUM(2.0)
    "ER66180": "dateStarted_Job1_Year_R", # "BC6 BEGINNING YEAR--JOB 1" NUM(4.0)
    "ER66454": "dateStarted_Job1_Month_S", #  "DE6 BEGINNING MONTH--JOB 1" NUM(2.0)
    "ER66455": "dateStarted_Job1_Year_S", # "DE6 BEGINNING YEAR--JOB 1"

    'ER66181': "dateEnded_Job1_Month_R", # "BC6 ENDING MONTH--JOB 1"
    'ER66182': "dateEnded_Job1_Year_R", # "BC6 ENDING YEAR--JOB 1"
    'ER66456': "dateEnded_Job1_Month_S", # "DE6 ENDING MONTH--JOB 1"
    'ER66457': "dateEnded_Job1_Year_S", # "DE6 ENDING YEAR--JOB 1"

# ER72369 "BC8 WTR UNEMPLOYED(RP)"
# ER72388 "BC7 WTR OUT OF LABOR FORCE (RP)
# ER72413 "BC62 WTR EVER WORKED"
                
    ##############
    # Income    
    ##############
    'ER71426': 'totalIncomeHH', # "TOTAL FAMILY INCOME-2016"  #  40 obs
    'ER71330': 'taxableIncomeRandS',# Reference Person and Spouse/Partner Taxable Income-2016  #  40 obs
    'ER71398': 'taxableIncomeO', # Taxable Income of Other FU Members-2016   #  40 obs
    'ER71391': 'transferIncomeRandS', # Reference Person and Spouse/Partner Transfer Income-2016   #  38 obs
    'ER71419': 'transferIncomeO', # Transfer Income of OFUMS-2016  # 23 - 1985+
    'ER71420': 'ssIncomeR', #   REF PERSON SOCIAL SECURITY INCOME-2016  # 15 2005-2017, 1986-1993
    'ER71422': 'ssIncomeS', #  "SPOUSE SOCIAL SECURITY INCOME-2016" # 15 2005-2017, 1986-1993
    'ER71424': 'ssIncomeO', # OFUM Social Security Income-2016 #26 2005-2017,<1993

    # Wage income - needed for interpreting retirement contribution rates, below
    'ER67045': 'hasWageIncomeR',  # "G12 WHETHER WAGES/SALARY-REF PERSON"  # 14 1994+
    'ER71277': 'wageIncomeR', # "WAGES AND SALARIES OF REF PERSON-2016"  # 40 obs
    'ER67400': 'hasWageIncomeS', # was the spouse if any (0 = no spouse in FU) working? # 16  1994+
    'ER67401': 'wageIncomeS_Post1993', #  "G13 WAGES/SALARY OF SPOUSE" # 14 1994+  
    # 'ER71305': 'summaryWageIncomeS',  # 2 obs
    'V23324': 'laborIncomeS_1993AndPre', # No 'wage only' income from pre 1994, only total labor

    # Unemployment 
    'ER71347': 'UnemploymentIncomeR', # "REF PERSN UNEMPLOYMENT COMPENSATION-2016"
    'ER71349': 'UnemploymentIncomeS', #"REF PERSON WORKERS COMPENSATION-2016"
    
    'ER71528': 'PovertyThreshold', # "CENSUS NEEDS STANDARD-2016" # 40 obs
    
    # Misc Passive Income
    'ER71294': 'RentIncomeR', #  "REF PERSON RENT INCOME-2016"
    'ER71322': 'RentIncomeS', #  "SPOUSE RENT INCOME-2016"

    # Dividend and interest info comes in 3 flavors over time - combined, separete based on respondent-unit, and annualized
    'V20446': 'DividendAndInterestIncomeR_1984to1992',  # V16430 "HD INT/DIVIDENDS 88"; 1989 V16430
    'V20449': 'DividendAndInterestIncomeS_1970to1992',  # "WF 88 OTHER ASSET Y"; 1989 V16433

    'ER67103': 'DividendsR_1993to2017_AmountNoUnit',  # G26b. How much was it?--AMOUNT
    'ER67104': 'DividendsR_1993to2017_Unit',
    'ER71296': 'DividendsR_2005On', # "REF PERSON DIVIDENDS-2016"  >=2005; annualized

    'ER67458': 'DividendsS_1993to2017_AmountNoUnit',  # G59b. How much was it?--AMOUNT
    'ER67459': 'DividendsS_1993to2017_Unit',
    'ER71324': 'DividendsS_2005On', # "SPOUSE DIVIDENDS-2016" >=2005   ; annualized

    'ER67120': 'InterestIncomeR_1993to2017_AmountNoUnit',  # G25c. How much was it?--AMOUNT
    'ER67121': 'InterestIncomeR_1993to2017_Unit',
    'ER71298': 'InterestIncomeR_2005On', # "REF PERSON INTEREST INCOME-2016"  >= 2005 ; annualized
    
    'ER67475': 'InterestIncomeS_1993to2017_AmountNoUnit',  # ER67475 "AMOUNT INTEREST INCOME-SPOUSE" G26c. How much was it?--INTEREST--AMOUNT
    'ER67476': 'InterestIncomeS_1993to2017_Unit',
    'ER71326': 'InterestIncomeS_2005On', # "SPOUSE INTEREST INCOME-2016"; annualized

    'V21733': 'FarmIncomeR_Before1993',
    'ER71272': 'FarmIncomeRandS_1993On', # "FARM INCOME OF REF PERSN AND SPOUSE-2016" NUM(7.0)

    'ER71275': 'BusinessAssetIncomeR_1993On', # "RP ASSET INCOME FROM BUSINESS-2016" NUM(7.0)
    'ER71303': 'BusinessAssetIncomeS_1993On', # "S ASSET INCOME FROM BUSINESS-2016" NUM(7.0)
    'V20439':  'BusinessAssetIncomeRandS_Before1993',  # "ASSET PART BUS Y 91" NUM(6.0)

    # retirement incomes
    
    # TODO -- Sort out different types of pension income - Retirement, Veteran, SS, Annuity, IRA, "Other" 
    'ER71337': 'VAPensionIncomeR', #  Annual "REF PERSON VA PENSION-2016"  2005-2017 Only 
  
    'V20470': 'PensionIncomeR_NonVet_1984to1992', # Annual  , Includes Pension and Annuities
    'ER67223': 'PensionIncomeR_NonVet_1993to2017_AmountNoUnit', #    1993-2017  - Retirmeent Pay and Pensions ONLY - Annuities sep out in 1993
    'ER67224': 'PensionIncomeR_NonVet_1993to2017_Unit', # 1993-2017     
    'ER67239': 'AnnuityIncomeR_AmountNoUnit', #  "REF PERSON ANNUITIES-2016"   >=1993
    'ER67240': 'AnnuityIncomeR_Unit', #  "REF PERSON ANNUITIES-2016"   >=1993
    
    'ER71343': 'IRAIncomeR', #  "REF PERSON IRAS-2016"  >=2005 

        # TODO -- find earlier version
    'ER71345': 'OtherRetirementIncomeR', #  "REF PERSON OTHER RETIREMENT-2016"
    
     'V11451': 'PensionIncomeS_NonVet_1985to1992', # Annual  
    'ER48783': 'PensionIncomeS_NonVet_1993to2011_AmountNoUnit', #
    'ER48784': 'PensionIncomeS_NonVet_1993to2011_Unit', #    
    'ER71369': 'PensionIncomeS_NonVet_2013to2017', # Annual ER71369 "SPOUSE RETIREMENT/PENSIONS-2016"  - Drops Annuties, IRAs, and included separtely 

    'ER71367': 'VAPensionIncomeS', #  "SPOUSE VA PENSION-2016"
    'ER71371': 'AnnuityIncomeS', #  "SPOUSE ANNUITIES-2016"
    'ER71373': 'IRAIncomeS', #  "SPOUSE IRAS-2016"  2013+
         # TODO -- find earlier version
   'ER71375': 'OtherRetirementIncomeS', # "SPOUSE OTHER RETIREMENT-2016"

    ##############
    ## Assets and Debts
    ##############
    'ER71485': 'NetWorthWithHome', #  "IMP WEALTH W/ EQUITY (WEALTH2) 2017" # 13 obs - wealth supplement years --
    'ER71483': 'NetWorthNoHome', #  "IMP WEALTH W/O EQUITY (WEALTH1) 2017" # 13 obs - wealth supplement years; not this definition changes to include Annuity and IRAs midway
    # Two special purposes ones for comparison to Dynan
    'V17389': 'NetWorth_1989Only', 
    'V17609': 'NetWorth_1984_AsOf1989', 

    'ER66030': 'hasHouse', # "A19 OWN/RENT OR WHAT" # 40 Obs
    'ER66031': 'valueOfHouse_Gross', # ' ER66031 "A20 HOUSE VALUE" NUM(7.0)  <- Gross Value, no debts
    'ER71481': 'valueOfHouse_Net', #  "IMP VALUE HOME EQUITY 2017" # 13 obs - wealth supplement years
        # Note -- this is the same as "valueOfHouse_Net"
    'ER66051': 'MortgagePrincipal_1', # "A24 REM PRINCIPAL MOR 1"  # Before 1994 wealth, this is actually the sum of ALL mortages. 
    'ER66072': 'MortgagePrincipal_2', # "A24 REM PRINCIPAL MOR 2" # Added in 1994 to specify second mortgages
        # Note -- these (combined) are the same as "valueOfHouse_Debt"
         
    'ER71443': 'hasBrokerageStocks', #  "IMP WTR STOCKS (W15) 2017"  # Does anyone in HH have stocks beyond Ret plan
    'ER71445': 'valueOfBrokerageStocks_Net', #  "IMP VALUE STOCKS (W16) 2017" # How much  <- Net Value

    'ER71433': 'hasCheckingAndSavings_to2017',
    'ER71435': 'valueOfCheckingAndSavings_Net_to2017',  # "IMP VAL CHECKING/SAVING (W28) 2017"  - A cleaner name would be 'Checking/Savings
    'ER77455': 'hasChecking_2019on_NoCDsOrGvtBonds', #
    'ER77457': 'valueOfCheckingAndSavings_Net_2019on_NoCDsOrGvtBonds',
    'ER77459': 'hasCDsOrGvtBonds', # 2019 only
    'ER77461': 'valueOfCDsOrGvtBonds_2019on', # "IMP VAL CD/BONDS/TB (W28) 2019" NUM(9.0)

    # NOTE -- there is no "HasVehicle" Question.
    'ER71447': 'valueOfVehicle_Net',  # IMP VALUE VEHICLES (W6) 2017  <- NET Value, after debts

    'ER71449': 'hasOtherAssets',
    'ER71451': 'valueOfOtherAssets_Net', # IMP VALUE OTH ASSETS (W34) 2017  <- NET Value, after debts

    # Starting in 2013, these assets are given as GROSS instead of NET, with a separate debt question
    'ER71437': 'hasOtherRealEstate',
    'ER52354': 'valueOfOtherRealEstate_Net_pre2013',  # S309 "IMP VAL OTH REAL ESTATE (G116) 94" NUM(9.0)
    'ER71439': 'valueOfOtherRealEstate_Gross_2013on', # "IMP VAL OTH REAL ESTATE ASSET (W2A) 2017"
    'ER71441': 'valueOfOtherRealEstate_Debt_2013on', # 'ER71441 "IMP VAL OTH REAL ESTATE DEBT (W2B) 2017"

    'ER71427': 'hasBusiness',
    'ER52346': 'valueOfBusiness_Net_pre2013',  # S303 "IMP VALUE FARM/BUS (G125) 94" NUM(9.0)
    'ER71429': 'valueOfBusiness_Gross_2013on', # ER71429 "IMP VALUE FARM/BUS ASSET (W11A) 2017" NUM(9.0)
    'ER71431': 'valueOfBusiness_Debt_2013on', # ER71431 "IMP VALUE FARM/BUS DEBT (W11B) 2017"

    # Misc Debts. Starting in 2011, these 'other debt' question are in individual components
    'ER48936': 'hasCreditCards_2011on', #"W38A WTR HAVE CREDIT/STORE CARD DEBT" NUM(1.0)
    'ER48941': 'hasStudentLoans_2011on',
    'ER48942': 'hasMedicalBills_2011on',
    'ER48943': 'hasLegalBills_2011on', # "W38B WTR HAS LEGAL BILLS"
    'ER48944': 'hasFamilyLoan_2011on', #"W38A WTR HAVE CREDIT/STORE CARD DEBT" NUM(1.0)
    'ER48937': 'valueOfDebt_CreditCards_2011on', # "W39A AMOUNT OF CREDIT/STORE CARD DEBT"  >=2011
    'ER48945': 'valueOfDebt_StudentLoans_2011on', # "W39B1 AMOUNT OF STUDENT LOANS"  >=2011
    'ER48949': 'valueOfDebt_MedicalBills_2011on', # "W39B2 AMOUNT OF MEDICAL BILLS"  >=2011
    'ER48953': 'valueOfDebt_LegalBills_2011on',# "W39B3 AMOUNT OF LEGAL BILLS"  >=2011
    'ER48957': 'valueOfDebt_FamilyLoan_2011on',# "W39B4 AMOUNT OF LOANS FROM RELATIVES"  >=2011
    'ER71477': 'hasOtherDebt_Other_2013on',
    'ER71479': 'valueOfDebt_Other_2013on', #  "IMP VAL OTHER DEBT (W38B7) 2017"  # Not asked in 2011; but small either way

    # Misc Debts. Before 2011, these are in one var. As of 2011, they are broken up into multiple items
    'ER46944': 'hasOtherDebt_pre2011', # Wealth years only
    'ER46946': 'valueOfAllOtherDebts_pre2011',  # "IMP VALUE OTH DEBT (G147) 89"# Wealth years only
    
    # The Value of Private and Employer Sponsored Retirement Plans -- all are 1999+ Only
    'ER71453': 'hasPrivateRetirePlan', #  "IMP WTR ANNUITY/IRA (W21) 2017" # Wherther have private annuities or IRAs; >= 1999
    'ER71455': 'valueOfPrivateRetirePlan_Gross', #  "IMP VALUE ANNUITY/IRA (W22) 2017" # How much  >= 1999

    # See "IsParticipating" Below: 'ER67987': 'hasEmployerRetirePlanR',
    'ER68010': 'valueOfEmployerRetirePlanR_Gross', #  "P20 AMT IN PENSION ACCT NOW - RP"   # Current Value of Employer Retirement Account >= 1999
    # See "IsParticipating" Below: 'ER68204': 'hasEmployerRetirePlanS',
    'ER68227': 'valueOfEmployerRetirePlanS_Gross', #  "P20 AMT IN PENSION ACCT NOW - SP"  >= 1999
    # Former Employer: Has plan?
    # 'ER68043': 'RetPlan_FormerEmployer_NumPlans', # "P45A NUMBER OF PNSN W/PREV EMPLYR-RP"  8% of Rs have.  
    # 'ER68051' "P49 AMT NOW PREV PNSN ACCT-#1 - RP"  # only a tiny portion answer 2/10th of 1%. Don't worry about it 

    ##################
    ## FLOW in Assets and Debts -- ie causes of change in Net Worth
    #################   
      
    # 'ER67918': 'Business_SinceLastQYr_BoughtOrSold', # "W73A WTR INVESTED OR SOLD BUSINESS/FARM"
    'ER67919': 'Business_SinceLastQYr_AmountBought', # "W74 AMT INVESTED IN BUSINESS/FARM" ; >=1989 wealth years
    'ER67924': 'Business_SinceLastQYr_AmountSold', # "W79 AMT FROM BUSINESS/FARM" ; >=1989 wealth years
    
    # 'ER67928': 'BrokerageStock_SinceLastQYr_BoughtOrSold', #  "W83A WTR BOUGHT OR SOLD STOCK"
    'ER67929': 'BrokerageStocks_SinceLastQYr_AmountBought', # "W91 AMT INVESTED IN STOCKS" ; >=1989 wealth years
    'ER67935': 'BrokerageStocks_SinceLastQYr_AmountSold', # "W97 AMT NON-IRA STOCK" # value from sale ; >=1989 wealth years
        # DOUBLE CHECK -- <1994 included IRAs (though not common then)
    
    # 'ER67941': 'PersonMovedOut_SinceLastQYr_WithAssetsYesNo', # "W102 WTR MOVER OUT W/ ASSETS OR DEBITS"
    'ER67942': 'PersonMovedOut_SinceLastQYr_AssetsMovedOut', # "W103 VALUE ASSETS MOVED OUT" ; >=1989 wealth years
    'ER67947': 'PersonMovedOut_SinceLastQYr_DebtsMovedOut', # "W108 VALUE DEBTS MOVED OUT" ; >=1989 wealth years
    
    # 'ER67951': 'PersonMovedIn_SinceLastQYr_YesNo', # "W112CKPT WTR ANY MOVERS IN 18+"
    # 'ER67952': 'PersonMovedIn_SinceLastQYr_WithAssetsYesNo', # "W113 WTR MOVER IN W/ ASSETS OR DEBITS"; >=1989 wealth years
    'ER67953': 'PersonMovedIn_SinceLastQYr_AssetsMovedIn', # "W114 VALUE ASSETS MOVED IN"; >=1989 wealth years
    'ER67958': 'PersonMovedIn_SinceLastQYr_DebtsMovedIn', # "W119 VALUE DEBTS MOVE IN"; >=1989 wealth years
    
    # Private (Non-Employer) Retirement Account (IRA / Annuity)
    # 'ER67888': 'PrivateRetirePlan_SinceLastQYr_MovedMoneyInYesNo', # "W43 WTR PUT MONEY IN PRIVATE ANNUITY/IRA"
    # 'ER67893': 'PrivateRetirePlan_SinceLastQYr_MovedOutYesNo', # "W48 WTR CASHED PNSN/ANNTY/IRA" 
    'ER67889': 'PrivateRetirePlan_SinceLastQYr_AmountMovedIn', # "W44 AMT INVESTED IN IRA/ANNUITY"  -- 2 year period ; >=1989 wealth years
    'ER67894': 'PrivateRetirePlan_SinceLastQYr_AmountMovedOut', # "W49 VALUE PENSION/ANNUITY/IRA ; >=1989 wealth years
    
    # 'ER67904': 'OtherRealEstate_SinceLastQYr_BoughtOrSold', # "W59A WTR BOUGHT OR SOLD REAL ESTATE"  
    'ER67905': 'OtherRealEstate_SinceLastQYr_AmountBought', # "W60 AMT SPENT IN REAL ESTATE" ; >=1989 wealth years
    'ER67910': 'OtherRealEstate_SinceLastQYr_AmountSold', # "W65 AMT FROM OTR REAL ESTATE" ; >=1989 wealth years

    # 'ER67899': 'Home_SinceLastQYr_SoldYesNo', # "W54 WTR SOLD HOME"
    'ER67900': 'Home_SinceLastQYr_SoldPrice', # "W55 HOME SELLING PRICE"
        
    # Major Renovations / improvements on House
    # Note -- this is effectively Home_SinceLastQYr_AmountBought
    'ER67914': 'MadeMajorHomeRenovations', # "W69 WTR MADE ADDITION/REPAIRS"
    'ER67915': 'CostOfMajorHomeRenovations_2001to2017', # "W70 COST OF ADDITION/REPAIRS" # Wealth Years Only
    'ER15062': 'CostOfMajorHomeRenovations_to1999', # "W70 COST OF ADDITION/REPAIRS"  # Wealth Years Only; Covers Princpal and other houses

    ##############
    # Expenses   (Non Housing)
    ############## 
    # Summaries
    'ER71487': 'FoodExpenseHH', #  "FOOD EXPENDITURE 2017"  >= 1999
    'ER71503': 'TransportationExpenseHH', #  "TRANSPORTATION EXPENDITURE 2017" >= 1999
    'ER71515': 'EducationExpenseHH', #  "EDUCATION EXPENDITURE 2016 >= 1999
    'ER71517': 'HealthcareExpenseHH', #  "HEALTH CARE EXPENDITURE 2017"  >= 1999
    'ER71522': 'ComputingExpenseHH', #  "COMPUTING EXPENDITURE 2016" : >= 2017
    # Inc Above ER71523 "HOUSEHOLD REPAIRS EXPENDITURE 2016"
    # Inc Above ER71524 "HOUSEHOLD FURNISHING EXPENDITURE 2016"
    'ER71525': 'ClothingExpenseHH', #  "CLOTHING EXPENDITURE 2016": >= 2005
    'ER71526': 'TripsExpenseHH', #  "TRIPS EXPENDITURE 2016"  >= 2005
    'ER71527': 'OtherRecreationExpenseHH', #  "OTHER RECREATION EXPENDITURE 2016" >= 2005

    'V20162': "FederalIncomeTaxesRS", # Only from 1970-1991
    'V20174': "FederalIncomeTaxesO", # Only from 1970-1991

    ###############
    # Home Payments
    ################
    'ER71491': 'HousingExpenseHH', #  "HOUSING EXPENDITURE 2017"  # Agg -- includes mortgage / rent, tax, insurance, utiltiies, internet, repairs, furnishing 

    'V21622' : 'RentPayment_Pre1993', # "ANNUAL RENT (A31)" NUM(5.0)
    'ER66090': 'RentPayment_1993On_AmountNoUnit',
    'ER66091': 'RentPayment_1993On_Unit',
    
    # Raw Material for Calculating House Principal Savings
    'ER71492': 'MortgagePaymentMonthlyHH_1999On', #  "MORTGAGE EXPENDITURE 2017"  # >=1999 only
    'V21615': 'MortgagePaymentAnnualHH_PartialBefore1993',    
    
    'ER66045': 'HomePropertyTaxAnnualHH',  #"A21 ANNUAL PROPERTY TAX", 37 values - nothing for 1988, 1989, 1987
    'ER66047': 'HomeInsuranceAnnualHH', # A22 ANNUAL OWNR INSURANC"  >= 1990
    # (ER71492 - ER66045 -  ER66047)/12 should equal principal payment.  Pay also be able to get from ER66051 (remaining principal) w/ change over time  
     
    ##############
    # Reference Person Retirement Plan Contributions
    ##############
    # Plan 1- Basics 
    'ER67987': 'RetPlan_IsParticipatingR', # "P1 WTR PNSN AT CURR JOB - RP" -- 1999 on
    'ER67988': 'RetPlan_IsEligibleR', # "P1A WTR ELIGIBLE FOR PLAN - RP"  --- NOTE this is for people who ARENT Participating; eligible for (only among non-participating)
    'ER67993': 'RetPlan_IsEmployeeContributingR', # '"P11 WTR CONTRIB TO PENSION - RP"
    'ER68002': 'RetPlan_TypeR', # "P16 HOW BENEFIT FIGURED - RP"
    
     # Required Employee Contribs
    'ER67995': 'RetPlan_ReqEmployeeContrib_AmountR', # "P13 REQUIRED AMT - RP"  # >=1999 only
    'ER67996': 'RetPlan_ReqEmployeeContrib_PeriodR', # "P13 REQUIRED AMT PER - RP" # >=1999 only
    'ER67997': 'RetPlan_ReqEmployeeContrib_PercentR', # "P13 REQUIRED PCT - RP" # 1984 + >=1999 only
    
     # Voluntary Employee Contribs
    'ER67999': 'RetPlan_VolEmployeeContrib_AmountR', # "P15 REQUIRED AMT - RP"  # >=1999 only
    'ER68000': 'RetPlan_VolEmployeeContrib_PeriodR', # "P15 REQUIRED AMT PER - RP"    # >=1999 only
    'ER68001': 'RetPlan_VolEmployeeContrib_PercentR', # "P15 REQUIRED PCT - RP"  # >=1999 only
    
    # Employer Contrib : 1999 On
    'ER68003': 'RetPlan_EmployerContrib_YesNoR', # "P17 WTR EMPLYR CONTRIB - RP"
    'ER68004': 'RetPlan_EmployerContrib_AmountR', # "P18 AMT EMPLYR CONTRIB - RP"
    'ER68005': 'RetPlan_EmployerContrib_PeriodR', # "P18 EMPLYR AMT PER - RP"
    'ER68006': 'RetPlan_EmployerContrib_PercentContribedR', # "P18 PCT EMPLYR CONTRIB - RP"  1999- # Percent of Pay Contributed
    'ER68007': 'RetPlan_EmployerContrib_PercentOfEmployeeContribR', # "P18B PCT EMP % OF EMPLOYEE CONTRIB-RP"  2013+ # Percent MATCHED

     # Current Employer: Plan 2 : 1999 On
    'ER68036': 'RetPlan2_HasR', # "P42 WTR TAX-DEFER PLAN - RP"
    'ER68037': 'RetPlan2_EmployerContrib_YesNoR', # "P43 WTR EMPLYR CONTRIB - RP"
    'ER68038': 'RetPlan2_EmployerContrib_AmountR', #  "P44 AMT EMPLYR CONTRIB - RP"
    'ER68039': 'RetPlan2_EmployerContrib_PeriodR', #  "P44 EMPLYR CONTRIB PER - RP" 
    'ER68040': 'RetPlan2_EmployerContrib_PercentContribedR', #  "P44 PCT EMPLYR CONTRIB OF PAY - RP" 1999- # Percent of Pay Contributed
    'ER68041': 'RetPlan2_EmployerContrib_PercentOfEmployeeContribR', #  "P44B PCT EMP % OF EMPLOYEE CONTRIB-RP" 2013+ # Percent Matched -- VERY RARE


    ##############
    # Spouse Retirement Plan Contributions
    ##############
    # Spouse: Plan 1
    'ER68204': 'RetPlan_IsParticipatingS', # "P1 WTR PNSN AT CURR JOB - SP"  # 1999 on
    'ER68205': 'RetPlan_IsEligibleS', # "P1A WTR ELIGIBLE FOR PLAN - SP"  #2011-2019 only
    'ER68210': 'RetPlan_IsEmployeeContributingS', # "P11 WTR CONTRIB TO PENSION - SP"
    'ER68219': 'RetPlan_TypeS', # "P16 HOW BENEFIT FIGURED - SP"
    
     # Required Employee Contribs
    'ER68212': 'RetPlan_ReqEmployeeContrib_AmountS', # "P13 REQUIRED AMT - SP"
    'ER68213': 'RetPlan_ReqEmployeeContrib_PeriodS', # "P13 REQUIRED AMT PER - SP"
    'ER68214': 'RetPlan_ReqEmployeeContrib_PercentS', # "P13 REQUIRED PCT - SP"
    
     # Voluntary Employee Contribs
    'ER68216': 'RetPlan_VolEmployeeContrib_AmountS', # "P15 REQUIRED AMT - SP"
    'ER68217': 'RetPlan_VolEmployeeContrib_PeriodS', # "P15 REQUIRED AMT PER - SP"
    'ER68218': 'RetPlan_VolEmployeeContrib_PercentS', # "P15 REQUIRED PCT - SP"
    
    # Employer Contrib 
    'ER68221': 'RetPlan_EmployerContrib_AmountS', # "P18 AMT EMPLYR CONTRIB - SP"
    'ER68222': 'RetPlan_EmployerContrib_PeriodS', # "P18 EMPLYR AMT PER - SP"
    'ER68223': 'RetPlan_EmployerContrib_PercentContribedS', # "P18 PCT EMPLYR CONTRIB - SP"
    'ER68224': 'RetPlan_EmployerContrib_PercentOfEmployeeContribS', # "P18B PCT EMP % OF EMPLOYEE CONTRIB-SP"

     # Plan 2
    'ER68253': 'RetPlan2_HasS', # "P42 WTR TAX-DEFER PLAN - SP"
    'ER68254': 'RetPlan2_EmployerContrib_YesNoS', # "P43 WTR EMPLYR CONTRIB - SP"
    'ER68255': 'RetPlan2_EmployerContrib_AmountS', #  "P44 AMT EMPLYR CONTRIB - SP"
    'ER68256': 'RetPlan2_EmployerContrib_PeriodS', #  "P44 EMPLYR CONTRIB PER - SP"
    'ER68257': 'RetPlan2_EmployerContrib_PercentContribedS', #  "P44 PCT EMPLYR CONTRIB OF PAY - SP"
    'ER68258': 'RetPlan2_EmployerContrib_PercentOfEmployeeContribS', #  "P44B PCT EMP % OF EMPLOYEE CONTRIB-SP"
   
    ##############
    # Gifts & Inheritances 
    ##############
    # Inheritance / Gift    
    'ER67962': 'LargeGift_HadInLast2YearsHH', #  "W123 WTR RECD GIFT/INHERITANCE" -- for LAST TWO YEARS 3% of people
    'ER67963': 'LargeGift_1_TypeHH', # "W123A WAS GIFT OR INHERITANCE - #1"
    'ER67967': 'LargeGift_1_AmountHH', # "W125 VALUE GIFT/INHERIT-#1" / G230 VALUE 1ST INHERT"
    'ER67975': 'LargeGift_2_AmountHH_1994AndAfter', # "W125 VALUE GIFT/INHERIT-#1"
    'ER67983': 'LargeGift_3_AmountHH_1994AndAfter', # "W125 VALUE GIFT/INHERIT-#1"
    'V17387': 'LargeGift_AllBut1_AmountHH_1989AndBefore', # "W125 VALUE GIFT/INHERIT-#1"

    # Build out as needed, if not covered below
    # Gifts and Transfers from others: Treated as income in PSID, and is ANNUAL
    'ER71355': 'helpFromFamilyRP_1975to1993andAfter2003', # After 2003, this is a cleaned up version of the Amount + Unit Calc
    'ER71357': 'helpFromOthersRP_1993andAfter2003',
    'ER71385': 'helpFromFamilySP_1985to1993andAfter2003',
    'ER71387': 'helpFromOthersSP_1993andAfter2003',

    'ER67352': 'helpFromFamilyRP_1993On_AmountNoUnit',    # "AMT HELP FRM RELATIV HD"
    'ER67353': 'helpFromFamilyRP_1993On_Unit',    # "AMOUNT HELP FROM RELATIVES PER-RP"
       
    'ER67368': 'helpFromOthersRP_1993On_AmountNoUnit',    # ER67367 "G44F WTR HELP FROM OTHERS-RP"
    'ER67369': 'helpFromOthersRP_1993On_Unit',    # "AMOUNT HELP FROM RELATIVES PER-RP"

    'ER67706': 'helpFromFamilySP_1993On_AmountNoUnit', # ER67706 "AMOUNT HELP FROM RELATIVES-SPOUSE"
    'ER67707': 'helpFromFamilySP_1993On_Unit', # ER67707 "AMOUNT HELP FROM RELATIVES PER-SPOUSE"

    'ER67722': 'helpFromOthersSP_1993On_AmountNoUnit', # "AMOUNT HELP FROM FRIENDS-SPOUSE"
    'ER67723': 'helpFromOthersSP_1993On_Unit', # "AMOUNT HELP FROM FRIENDS-SPOUSE"

    ####################
    ## Financial Support to  Others
    ####################
    'ER67759': 'helpsOthersFinancially', # All years  "G103 WTR HELP OTRS"
    'ER67760': 'numberOtherHelpedFinancially', # All years "G104 # OTRS SUPPORTED"
    'ER67766': 'amountOtherHelpedFinancially', # All years "G106 TOTAL SUPP OF OTRS"

    'ER67767': 'providesChildSupport', # Since 1985 "G107 ANY CHILD SUPPORT"
    'ER67768': 'amountChildSupport', # Since 1985 "AMT OF CHLD SUPPRT GIVEN"
    'ER67769': 'providesAlimony', # "G109 ANY ALIMONY"
    'ER67770': 'amountAlimony', # "AMT OF ALIMONY GIVEN"

    ####################
    ## Active Savings (1989 only)
    ####################
    'V17610': 'ActiveSavings_PSID1989', # 1989 ONLY

    }

# Regex to convert PSID Var Listings: (ER\d{5})  -> '$1': '', # 