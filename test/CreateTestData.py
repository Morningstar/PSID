import unittest
from InvestorFinance_Constants import *
from Controller.Inequality_Constants import *
import pandas as pd
import os as os

import test.replicationSimTestParams_SmallSample as smallSampleParams
import test.replicationSimTestParams_FullDataset as fulldatasetParams

class SimReplicatorTest(unittest.TestCase):

    def test_extract_dataSubset(self):
        outputParams = smallSampleParams.params
        inputParams = fulldatasetParams.params
        testOutputDir = outputParams[CONST_MODELPARAM_BASEDIR]

        crossFile = pd.read_csv \
            (os.path.join(inputParams[CONST_MODELPARAM_BASEDIR], inputParams[CONST_PSID_MODELPARAM_INDIVIDUAL_CROSSFILE]))
        crossFile['constantIndividualId'] = range(1 ,(len(crossFile ) +1), 1)
        # crossFile['needed'] = False
        isFirst = True
        allConstIndividualIds = None
        priorYearSample = None
        for year in (range(1984, 1994 +1, 1)):
            yearFile = pd.read_csv(os.path.join(inputParams[CONST_MODELPARAM_BASEDIR],
                                                inputParams[CONST_PSID_MODELPARAM_INVESTORFILE_BASE] +
                                                "_" + str(year) + "_as_" + str
                                                    (inputParams[CONST_PSID_MODELPARAM_INFLATETOYEAR]) + ".csv"))

            if isFirst:
                # Start with 100 families
                theSample = yearFile.sample(n=100)
                sampleFamilyIds = theSample['familyInterviewId_' + str(year)]
                # Store a record of all of the PEOPLE in those families
                allConstIndividualIds = set(crossFile.loc[crossFile['interviewId_' + str(year)].isin(set(sampleFamilyIds)),
                                                          'constantIndividualId'])
                isFirst = False
            else:
                # Which families did we have last year?
                familyInterviewIds_PriorYear = priorYearSample['familyInterviewId_ '+ str(year -1)]
                # Which families did those people end up in?
                newFamilyInterviewIds = set \
                    (crossFile.loc[crossFile['interviewId_' + str(year -1)].isin(list(familyInterviewIds_PriorYear)),
                                                          'interviewId_' + str(year)])
                if 0 in newFamilyInterviewIds:
                    newFamilyInterviewIds.remove(0)

                # Who are all of the PEOPLE in those destination families?
                newConstIndividualIds = set(crossFile.loc[crossFile['interviewId_' + str(year)].isin(newFamilyInterviewIds),
                                                          'constantIndividualId'])

                # Who are all of the PEOPLE in those destination families + any previous people we've tracked
                allConstIndividualIds.update(newConstIndividualIds)

                if 0 in allConstIndividualIds:
                    allConstIndividualIds.remove(0)

                # What the families in tha broader set of people (current families + prior that might have dropped off)
                allFamilyInterviewIds_CurYear = set(crossFile.loc[crossFile.constantIndividualId.isin(allConstIndividualIds),'interviewId_' + str(year)])

                if 0 in allFamilyInterviewIds_CurYear:
                    allFamilyInterviewIds_CurYear.remove(0)

                # Get the data for that broader set of families
                theSample = yearFile.loc[yearFile['familyInterviewId_ '+ str(year)].isin(allFamilyInterviewIds_CurYear)].copy()
                # theSample = yearFile.loc[yearFile['familyInterviewId_'+ str(year)].isin(list(newFamilyInterviewIds))].copy()

            theSample.to_csv(os.path.join(testOutputDir, outputParams[CONST_PSID_MODELPARAM_INVESTORFILE_BASE] + "_" + str(year) + "_as_" + str(inputParams[CONST_PSID_MODELPARAM_INFLATETOYEAR]) + ".csv"))
            # currentFamilyInterviewIds = theSample['familyInterviewId_' + str(year)]
            # crossFile.loc[crossFile['interviewId_' + str(year)].isin(list(currentFamilyInterviewIds)),'needed']= True

            priorYearSample = theSample

        crossFile = crossFile.loc[crossFile.constantIndividualId.isin(allConstIndividualIds)].copy()
        crossFile.to_csv(os.path.join(testOutputDir, outputParams[CONST_PSID_MODELPARAM_INDIVIDUAL_CROSSFILE]))

        # Create a Long version of the crossFile