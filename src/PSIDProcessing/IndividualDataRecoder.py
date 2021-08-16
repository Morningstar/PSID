import DataQuality.CrossSectionalTester as DataQualityTester

DEBUG_EDA = False

''' --------------------
 Recode the Individual Level data in the PSID, similar to (and see for more information) the FamilyDataRecoder
-------------------- '''

class IndividualDataRecoder:
    def __init__(self, dta, varStatus):
        self.dta = None
        self.varStatus = None
        self.fields = None

        if dta is not None:
            self.setData(dta, varStatus)

        
    def setData(self, dta, varStatus):
        self.dta = dta
        self.varStatus = varStatus
        self.fields = list(dta.columns)

    def recodeVar_AllYears(self, baseVarName, replacementDict):
        varNames = [i for i in self.fields if baseVarName in i] 
        
        for varName in varNames:
            self.dta[varName].replace(replacementDict, inplace=True)
      
        
    def createWeightVars(self):
        varNamesLongitudinal = [i for i in self.fields if 'longitudinalWeight_' in i] 
        varNamesCrossSectional = [i for i in self.fields if 'crossSectionalWeight_' in i]
         
        yearsLongitudinal = [i[-4:] for i in self.fields if 'longitudinalWeight_' in i] 
        yearsLongitudinalUnique = list(set(yearsLongitudinal))

        for year in yearsLongitudinalUnique:
            yearInt = int(year) 
            if (yearInt >= 1997):
                self.dta['longitudinalWeightI_' + year] = self.dta['longitudinalWeight_Combined_Post1996I_' + year] # "CORE/IMM INDIVIDUAL LONGITUDINAL WT 17"
                self.dta['crossSectionalWeightI_' + year] = self.dta['crossSectionalWeight_Combined_Post1996I_' + year] #  "CORE/IMM INDIVIDUAL CROSS-SECTION WT 17" NUM(5.0)
            elif (yearInt >= 1993):
                self.dta['longitudinalWeightI_' + year] = self.dta['longitudinalWeight_Core_1993to1996I_' + year]
                self.dta['crossSectionalWeightI_' + year] = None
            else:
                self.dta['longitudinalWeightI_' + year] = self.dta['longitudinalWeight_Core_1968to1992I_' + year]
                self.dta['crossSectionalWeightI_' + year] = None

        self.dta.drop(columns=varNamesLongitudinal, inplace=True)
        self.dta.drop(columns=varNamesCrossSectional, inplace=True)
        self.fields = list(self.dta.columns)
    
        # These include the short-lived Latino Sample, that only covered 3 countries. Not reprepresentative.
        # Rarely something we want to use
        # 'ER30803': 'longitudinalWeight_WithLatino_1990to1992I', #  
        # 'ER30803': 'longitudinalWeight_WithLatino_1993to1995I', #  yr 1993-1996
    

    def recodeCoreVars(self):
        # Age
        self.recodeVar_AllYears('ageI', {999:None, 0: None})
        self.recodeVar_AllYears('yearOfBirthI', {9999:None, 0: None})

        self.recodeVar_AllYears('movedInOutI', {1:'BornOrMovedIn', 2:'BornOrMovedIn',
                                       5:'MovedOut', 6:'MovedOut', 7:'PassedAway', 8:None, 0:'No Change'})

        # NOTE : this coding is only valid for 1983 on.  Wealth data is only available from 1984 on, so fine for our purposes.
        # But if you want to reuse this code for non-wealth data purposes, this should be updated.
        self.recodeVar_AllYears('relationshipToR', {0:None, 10:'RP', 20:'Partner', 22:'Partner', 90: 'Partner', 92: 'Partner',
                                          30: 'Child', 33: 'Child', 35: 'Child', 37: 'Child', 38: 'Child',
                                          40: 'Sibling', 47: 'Sibling', 48: 'Sibling',
                                          50: 'Parent', 57: 'Parent', 58: 'Parent',
                                          60: 'Grandparent', 65: 'Grandparent', 66: 'Grandparent', 67: 'Grandparent', 68: 'Grandparent', 69: 'Grandparent',
                                          88:'Partner', # Cohabitor < 1 year,
                                          83: 'Child',# of Cohabitor < 1 year,
                                          })

        self.recodeVar_AllYears('employmentStatusI', {1:'Working', 2:'TemporaryLaidOff', 3: 'UnemployedAndLooking', 4: 'Retired', 
                                       5:'Disabled', 6:'KeepingHouse', 7:'Student', 8:'Other', 0:None})



    def createConstantId(self):
        self.dta['separator'] = "_"
        self.dta['constantIndividualID'] = self.dta.interviewId_1968.astype(str) + self.dta['separator'] + self.dta.personId_1968.astype(str)
        # self.dta['constantIndividualID'] = self.dta.apply(lambda x: (str(x.interviewId_1968) + "_" + str(x.personId_1968)), axis=1)
        # self.dta.apply(lambda x: '*'.join(x[['interviewId_1968', 'personId_1968']].dropna().astype(str).values), axis=1)

        # PersonId is ONLY in 1968; drop the other useless fields
        varNamesPersonId = [i for i in self.fields if 'personId_' in i]
        self.dta.drop(columns=varNamesPersonId, inplace=True)


    def dropEmptyFieldsForLimitedYearData(self):
        # LocationVars: Only Available in 1997 and 1999
        varNamesStateBorn = [i for i in self.fields if 'stateBornI_' in i]
        varNamesStateBorn = [x for x in varNamesStateBorn if x not in ['stateBornI_1997','stateBornI_1999']]

        varNamesCountryBorn = [i for i in self.fields if 'countryBornI_' in i]
        varNamesCountryBorn = [x for x in varNamesCountryBorn if x not in ['countryBornI_1997','countryBornI_1999']]

        varNamesLivedInUSIn68 = [i for i in self.fields if 'livedInUSIn68I_' in i]
        varNamesLivedInUSIn68 = [x for x in varNamesLivedInUSIn68 if x not in ['livedInUSIn68I_1997','livedInUSIn68I_1999']]

        self.dta.drop(columns=varNamesStateBorn, inplace=True)
        self.dta.drop(columns=varNamesCountryBorn, inplace=True)
        self.dta.drop(columns=varNamesLivedInUSIn68, inplace=True)


    def doIt(self, fileNameWithPathNoExtension, save):
        '''
        Starting point -- this runs the recoding process for Individual level data
        :param fileNameWithPathNoExtension:
        :type fileNameWithPathNoExtension:
        :param save: Save to disk?
        :type save: String
        :return: None
        :rtype: None
        '''
        self.createConstantId()
        self.dropEmptyFieldsForLimitedYearData()
        self.recodeCoreVars()
        self.createWeightVars()
        
        if save:
            self.dta.to_csv(fileNameWithPathNoExtension + ".csv", index=False)

        self.dta['dummyWeight'] = 1
        tester = DataQualityTester.CrossSectionalTester(dta = self.dta,
                                                        dfLabel = "Individual Data Recoding",
                                                        year = 2019,
                                                        varMapping = self.varStatus,
                                                        ignoreUnmappedVars = True)


        tester.exploreData(fileNameWithPathNoExtension, weightVar = 'dummyWeight', doFancy=False)
        tester.reportOnUnMappedVars()
        tester.checkDataQuality(raiseIfMissing = False)

