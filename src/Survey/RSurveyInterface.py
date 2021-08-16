import pandas as pd
import numpy as np
import rpy2
from rpy2.robjects.packages import importr
from rpy2 import robjects as ro
from rpy2.robjects import pandas2ri
from rpy2.robjects.conversion import localconverter
import rpy2.robjects.numpy2ri as rpyn

'''
Sometimes, Python just doesn't have what you need. In particular it's functions for Median Regressions and complex survey designs are terrible 
This class provides a wrapper to the Rpy2 python class, to make it easier to get the results of specific statitical analyses  
'''


# See https://rpy2.github.io/doc/latest/html/pandas.html
def convertRFrameToDF(R_df):
    # Only works with Multi-column Frame
    with localconverter(ro.default_converter + pandas2ri.converter):
        df = ro.conversion.rpy2py(R_df)
    return df

     # If you have series / vectors us
    # python_float_list = list(R_float_vec)
    # python_int_array = np.array(R_int_vec)


def convertDFtoRFrame(df):
    # Only works with Pandas DFs
    with localconverter(ro.default_converter + pandas2ri.converter):
        R_df = ro.conversion.py2rpy(df)
    return R_df

# If you have series / vectors, use
def convertSeriesToVector(aSeries):
    if (aSeries.dtype in [np.dtype('float64'), np.dtype('float32')]):
        return(ro.vectors.FloatVector(aSeries))
    elif (aSeries.dtype in [np.dtype('int64'), np.dtype('int32')]):
        return(ro.vectors.IntVector(aSeries))
    else:
        return(ro.vectors.StrVector(aSeries))


def convertRListToPy(R_list):
    R_object_dict = {}
    Py_object_dict = {}
    keys = R_list.names
    for i in range(len(keys)):
        R_object_dict[keys[i]] = R_list[i]
        # Use Vector Etc functions here:
        theType = type(R_list[i])
        if theType in [rpy2.robjects.vectors.FloatVector, rpy2.robjects.vectors.FloatMatrix]:
           Py_object_dict[keys[i]] = list(R_list[i])
        elif theType in [rpy2.robjects.vectors.FloatVector, rpy2.robjects.vectors.FloatMatrix]:
            Py_object_dict[keys[i]] =  np.array(R_list[i])
        elif theType in [rpy2.robjects.vectors.StrVector, rpy2.robjects.vectors.StrMatrix]:
            Py_object_dict[keys[i]] = list(R_list[i])
        elif theType in [rpy2.robjects.Formula]:
           Py_object_dict[keys[i]] = R_list[i]
        else:
           Py_object_dict[keys[i]] = list(R_list[i])

    return Py_object_dict

class RSurveyInterface:
    '''
    Create a simple interface the R survey package.
    Naming convensions: RP: R Package; RF: R Function; RO: R Object

    To get something from an R result, call results.rclass; results.name; results.rx('oneofthelistednames') and results.rx2('oneofthelistednames')
    See https://rpy2.github.io/doc/v3.4.x/html/vector.html#robjects-extracting
    '''

    def __init__(self):

        pandas2ri.activate()
        # import R's "base" package
        self.RPbase = importr('base')

        # import R's "utils" package
        self.RPutils = importr('utils')

        # import R's "utils" package
        self.RPstats = importr('stats')

        # import R's "utils" package
        self.RPsurvey = importr('survey')
        self.RFsvydesign = ro.r['svydesign']
        self.RFasforumla = ro.r['as.formula']

        # Get what we need for Quantile regressions (weights are supported)
        self.RPquantreg = importr('quantreg')
        self.RFquantreg = ro.r['rq']

        self.ROdesign = None
        self.RFsvychisq = None

        # Make sure it works
        pi = ro.r('pi')
        assert(abs(pi[0]-3.14159265358979)<0.00001)


    def callSurveyFunction(self, function):
        None


    def callAnova(self, dta, var1, var2):
        # from https://rpy2.github.io/doc/v3.4.x/html/introduction.html#calling-r-functions
        ROdta = convertDFtoRFrame(dta[[var1, var2]])

        # robjects.globalenv['weight'] = dta[var1]
        # robjects.globalenv['group'] = dta[var2]
        lm_D9 = self.RPstats.lm(self.RFasforumla(var1 + ' ~ ' + var2), ROdta)  # add -1 to the formula to omit intercept
        print(self.RPbase.summary(lm_D9))
        return (self.RPstats.anova(lm_D9))

    def setupSurveyDesign(self, dta, weightVar):

        ROdta = convertDFtoRFrame(dta)
        # ROweights = convertSeriesToVector(weightSeries)
        self.ROdesign = self.RFsvydesign(ids=self.RFasforumla('~1'), weights=self.RFasforumla('~' + weightVar), data = ROdta) # ROweights
        # print(self.ROdesign)
        return self.ROdesign

    def getQuantileReg(self, dta, IVlist, DVlist, weightVar):
        ROdta = convertDFtoRFrame(dta[DVlist + IVlist])
        ROweights = convertSeriesToVector(dta[weightVar])

        results = self.RFquantreg(self.RFasforumla("+".join(DVlist) + ' ~ ' + "+".join(IVlist)), tau=0.5, data=ROdta, weights=ROweights, method="br")

        summaryResults = self.RPbase.summary(results)
        resultDict = convertRListToPy(summaryResults)
        shortDict = {key: resultDict[key] for key in ['terms', 'coefficients', 'call']}
        df1 = pd.DataFrame(shortDict['coefficients'], columns=["coeff", "stderr", "tvalue", "pvalue"])
        df1['var'] =["intercept"] + IVlist
        return df1

    def getChiSquare(self, var1, var2):
        if self.RFsvychisq is None:
            self.RFsvychisq = ro.r['svychisq']

        results = self.RFsvychisq(self.RFasforumla("~" + var1 + " + " + var2), self.ROdesign)
        resultDict = convertRListToPy(results)
        shortDict = {key: resultDict[key] for key in ['statistic', 'parameter', 'p.value']}
        return shortDict
        #dict_keys(['statistic', 'parameter', 'p.value', 'method', 'data.name', 'observed', 'expected', 'residuals', 'stdres'])

