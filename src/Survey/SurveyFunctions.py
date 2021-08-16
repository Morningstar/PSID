import pandas as pd    
import numpy as np    
from statsmodels.stats.weightstats import DescrStatsW
import statsmodels.api as sm
import statsmodels.formula.api as smf
import statsmodels.regression as sr
import warnings

'''
Python's survey functions aren't great.  
1) StatsModels has useful description functions, but beyond that the functions don't appears to be 
well tested or documented. For example, sm.Logit has a parameter for weights that looks like it works for surveys, but it doesn't.
2) Python is especially lacking in a mechanism to run groupby functions with weights.

This file helps in three areas:
1) It offers useful survey-weighted functions that don't appear to otherwise exist in Python,
 such as weighted zScores and Quantiles
2) It enables weighted group-bys, using these survey-weighted functions, by replicating and extending the groupby dictionary syntax 
3) It provides tested, known wrappers to the appropriate regression functions for survey-weights

'''

CONST_NA_STRING = "<NA>"
''' The best existing package is statsmodels.stats.weightedstats
 For documentation on it, see https://www.statsmodels.org/dev/generated/statsmodels.stats.weightstats.DescrStatsW.html
 For the source code (if you want to do custom versions, etc) see https://www.statsmodels.org/stable/_modules/statsmodels/stats/weightstats.html
 
 To Add: The Creation of Survey Weights, using https://pypi.org/project/ipfn/ with Rakes 

 Sources to learn from: 
# SurveyGizmo to Python
# https://tech.trivago.com/2019/09/23/how-to-analyze-surveymonkey-data-in-python/

# Custom 
# https://towardsdatascience.com/how-to-analyze-survey-data-with-python-84eff9cc9568
'''


############################
# Univariate Analyses, with Weights
# Note -- each function is designed to work either on its own, or as a groupby custom function
# EG https://pbpython.com/weighted-average.html
############################

# This is used in a group-by, just get the total weights represented in a group
# AKA "Count" or "Num Observations"
def wSumOfWeights(dta, X, varForWeights, skipna=True):
    return dta[varForWeights].sum(skipna=skipna)

def wSumOfWeightsWhereNull(dta, X, varForWeights, skipna=True):
    return (dta[X].isna()*dta[varForWeights]).sum(skipna=skipna)

def wSum(dta, X, varForWeights, skipna=True):
    return (dta[X]*dta[varForWeights]).sum(skipna=skipna)

# Returns the Z Score for each value in a series
def wZScore(dta, X, varForWeights, skipna=True, runningInGroupBy = False):  
    if skipna:
        naMask = ~((dta[X].isna()) | (dta[varForWeights].isna())) 
    else:
        naMask = pd.Series([True]).repeat(len(dta))
        
    if (len(dta.loc[naMask, X]) <= 1):
        zScoresUnMasked = dta[X].copy()
        zScoresUnMasked[:] = None
    else:
        wt_stat = DescrStatsW(dta.loc[naMask, X], weights=dta.loc[naMask, varForWeights], ddof=0)
        zScoresMasked = (dta.loc[naMask, X] - wt_stat.mean) / wt_stat.std
        zScoresUnMasked = dta.loc[:,X].copy()
        zScoresUnMasked[:] = None
        zScoresUnMasked[naMask] = zScoresMasked 
        
    if runningInGroupBy:  # When grouping and applying, returning uneven length series per group gives strange results. So, we reset to avoid that
        zScoresUnMasked.index = range(len(zScoresUnMasked))
        
    return zScoresUnMasked

# What does a particular Z score correspond to in the underlying data?
def wValueForZScore(dta, X, varForWeights, zScoreThreshold = 1, skipna=True):    
    if skipna:
        naMask = ~((dta[X].isna()) | (dta[varForWeights].isna())) 
    else:
        naMask = pd.Series([True]).repeat(len(dta))
        
    if (len(dta.loc[naMask, X]) <= 1):
        return None
    else:
        wt_stat = DescrStatsW(dta.loc[naMask, X], weights=dta.loc[naMask, varForWeights], ddof=0)
        return wt_stat.mean + wt_stat.std*zScoreThreshold
    
    
# Value Counts, Weighted & optionally Normalized
# Based on https://stackoverflow.com/questions/38773095/get-normalised-value-counts-weighted-by-another-column
# This is a more general version of Sarwari's getWeightedPrevalence and Sam's weighted_value_counts
def wValueCounts(dta, X, varForWeights, normalize=False, dropna=True):
    # if (X == "retired" or X == "numericCat"):
    #    print("Debug here")

    if (dropna==True):
        goodMask = ~dta[X].isna()
        dtaTmp = dta.loc[goodMask, [X,varForWeights]].groupby(X).agg({varForWeights:'sum'}).sort_values(varForWeights,ascending=False)
    else:
        dtaTmp = dta[[X,varForWeights]].fillna(CONST_NA_STRING).groupby(X).agg({varForWeights:'sum'}).sort_values(varForWeights,ascending=False)

    s = pd.Series(index=dtaTmp.index, data=dtaTmp[varForWeights], name=X)
    if normalize:
        s = s / dtaTmp[varForWeights].sum()

    return s # data.frame(s)

# UN Weighted Value Counts --
# A convinence function to get Number of Observations by wrapping the normal value counts in the CallCommand structure used for the rest of thse fcuntions
def uwValueCounts(dta, X, varForWeights, *args, **kwargs):
    if 'normalize' in kwargs:
        normalize = kwargs['normalize']
    elif len(args) >= 1:
        normalize = args[0]
    else:
        normalize = False

    if 'dropna' in kwargs:
        dropna = kwargs['dropna']
    elif len(args) >= 2:
        dropna = args[1]
    else:
        dropna = False

    results = dta[X].value_counts(normalize=normalize, dropna=dropna)
    results.index.rename(X, inplace=True)
    results.index = results.index.fillna(CONST_NA_STRING)

    # results.rename(index={nan: CONST_NA_STRING, np.float64(np.NaN): CONST_NA_STRING, np.NaN: CONST_NA_STRING, None:CONST_NA_STRING}, inplace=True)
    results = results.rename(X)
    # results = pd.DataFrame(results)
    # results.columns = [X]
    return results



# Get equally distributed bins, by weight, for a particular variable
def wQuantiles(dta, varForQuantile, varForWeights, numQuantiles, interiorBoundariesOnly = True, retBins=True):
    """
    Computes quantiles boundaries for a given  
    using the statsmodels DescrStatsW module [https://www.statsmodels.org/dev/generated/statsmodels.stats.weightstats.DescrStatsW.html]
    """
    if interiorBoundariesOnly:
        probs = np.linspace(start=0, stop=1, num= numQuantiles+1).tolist()
        probs = probs[1:(len(probs)-1)]

    else:
        probs = np.linspace(start=0, stop=1, num= numQuantiles+1).tolist() # INcludes Min and Max as top and bottom 

    if (len(dta[varForQuantile]) < len(probs)):
        # raise Exception('More segments than data!')
        return pd.Series([None] * (len(probs)))
    
    wt_stat = DescrStatsW(dta[varForQuantile], weights=dta[varForWeights])
    quantiles= wt_stat.quantile(probs, return_pandas=True)
    return quantiles

# Def Weighted QUantiles
def wPercentile(dta, varForPercentile, varForWeights, percentBreaks, values_sorted=False, old_style=False):
    result = wPercentile_ForSeries(dta[varForPercentile], quantiles=percentBreaks, sample_weight=dta[varForWeights], values_sorted=values_sorted, old_style=old_style)
    # if (len(result) > 1)
    #    raise Warning("wPercentile can only handle 1 percentile currently")
    return result[0]

def wPercentile_ForSeries(values, quantiles, sample_weight=None, values_sorted=False, old_style=False):
    """ Very close to numpy.percentile, but supports weights.
    NOTE: quantiles should be in [0, 1]!
    :param values: numpy.array with data
    :param quantiles: array-like with many quantiles needed
    :param sample_weight: array-like of the same length as `array`
    :param values_sorted: bool, if True, then will avoid sorting of
        initial array
    :param old_style: if True, will correct output to be consistent
        with numpy.percentile.
    :return: numpy.array with computed quantiles.
    """
    values = np.array(values)
    quantiles = np.array(quantiles)
    if sample_weight is None:
        sample_weight = np.ones(len(values))
    sample_weight = np.array(sample_weight)
    assert np.all(quantiles >= 0) and np.all(quantiles <= 1), \
        'quantiles should be in [0, 1]'

    if not values_sorted:
        sorter = np.argsort(values)
        values = values[sorter]
        sample_weight = sample_weight[sorter]

    weighted_quantiles = np.cumsum(sample_weight) - 0.5 * sample_weight
    if old_style:
        # To be convenient with numpy.percentile
        weighted_quantiles -= weighted_quantiles[0]
        weighted_quantiles /= weighted_quantiles[-1]
    else:
        weighted_quantiles /= np.sum(sample_weight)
    return np.interp(quantiles, weighted_quantiles, values)


# Return a recoded version of a variable, transformed into quantiles.  Similar to Pandas's PD.QCut function  
def wQCut(dta, varForQuantile, varForWeights, numQuantiles, labelsAsRanges=False):
    quantiles = wQuantiles(dta, varForQuantile, varForWeights, numQuantiles, interiorBoundariesOnly = False)
    # quantiles= quantilesAndBins[1]
    if (any(v is None for v in quantiles)):
        values = dta[varForQuantile].copy()
        values[:] = None
        return values
    else:
        if labelsAsRanges:
            return pd.cut(x = dta[varForQuantile], bins =quantiles, labels = None, include_lowest= True, duplicates='drop')
        else:
            return pd.cut(x = dta[varForQuantile], bins =quantiles, labels = list(range(1,numQuantiles+1)), include_lowest= True, duplicates='drop')

# Weighted Median 
def wMedian(dta, varToGetMedian, varForWeights, skipna=True):
    try:
        if skipna:
            naMask = ~((dta[varToGetMedian].isna()) | (dta[varForWeights].isna()))
        else:
            naMask = pd.Series([True]).repeat(len(dta[varForWeights]))

        if (naMask.sum() == 0):
            return None

        dtaLocal = dta[naMask].sort_values(varToGetMedian, inplace=False)
        cumsum = dtaLocal[varForWeights].cumsum()
        cutoff = dtaLocal[varForWeights].sum() / 2.0
        medianLow = dtaLocal[varToGetMedian][cumsum >= cutoff].iloc[0]
        return medianLow
        # TODO: should be a weighted average of these two?
        # medianHigh = dtaLocal[varToGetMedian][cumsum <= cutoff].iloc[-1]
        
        '''
        median = wPercentile_ForSeries(dta[varToGetMedian], quantiles=[.5], sample_weight=dta[varForWeights],
                                    values_sorted=False, old_style=False)
        return median
        '''
    except Exception as e:
        print("Error: " + str(e))


# Weighted Average
def wAverage(dta, X, varForWeights, skipna=True):
    """ http://stackoverflow.com/questions/10951341/pandas-dataframe-aggregate-function-using-multiple-columns
    In rare instance, we may not have weights, so just return the mean. Customize this if your business case
    should return otherwise.
    """
    if skipna:
        naMask = ~((dta[X].isna()) | (dta[varForWeights].isna()))
    else:
        naMask = pd.Series([True]).repeat(len(dta[varForWeights]))

    if (naMask.sum() == 0):
        return None

    d = dta[naMask][X]
    w = dta[naMask][varForWeights]
    try:
        return (d * w).sum() / w.sum()
    except ZeroDivisionError:
        return d.mean()

##############################
# Simplified Interface to these Aggregate Functions
##############################    
# Uses A Dictionary version of Aggregate's Named Aggregation syntax:   { destinationColumn = (sourceColumn, command), ...}
# For this structure, see https://www.shanelynn.ie/summarising-aggregation-and-grouping-data-in-python-pandas/

def wCallCommand(dta, command, sourceColumn, varForWeights, *args, **kwargs):
    '''
    :param dta:
    :type dta:
    :param command:
        The Options are describe, sum, median, percentile, average,
            value_counts, value_counts_unweighted, 'SumOfWeights',
            'SumOfWeightsWhereNull', 'zScore', 'valueForZScore', 'quantiles',
            'qcut', 'count', 'count_unique'
    :type command:  String
    :param sourceColumn:
    :type sourceColumn: String
    :param varForWeight:
    :type varForWeights: String
    :param args:  Any additional parameters you wish to pass to the underlying command (keyword version)
    :type args: List
    :param kwargs:   Any additional parameters you wish to pass to the underlying command (keyword version)
    :type kwargs: List
    :return:
    :rtype:
    '''

    if (command == 'describe') | (command == 'wDescribe'):
        return wDescribeByVar(dta, sourceColumn, varForWeights, *args, **kwargs)
    elif (command == 'sum') | (command == 'wSum'):
        return wSum(dta, sourceColumn, varForWeights, *args, **kwargs)
    elif (command == 'median') | (command == 'wMedian'):
        return wMedian(dta, sourceColumn, varForWeights, *args, **kwargs)
    elif (command == 'percentile') | (command == 'wPercentile'):
        return wPercentile(dta, sourceColumn, varForWeights, *args, **kwargs)
    elif (command == 'average') | (command == 'wAverage') | (command == 'mean'):
        return wAverage(dta, sourceColumn, varForWeights, *args, **kwargs)

    elif (command == 'value_counts') | (command == 'wValueCounts'):
        return wValueCounts(dta, sourceColumn, varForWeights, *args, **kwargs)

    # Yes, not really a weighted function -- but really useful to have in the same call-Command structure
    elif (command == 'value_counts_unweighted') | (command == 'numObs'):
        return uwValueCounts(dta, sourceColumn, varForWeights, *args, **kwargs)

    elif (command == 'SumOfWeights') | (command == 'wSumOfWeights'):
        return wSumOfWeights(dta, sourceColumn, varForWeights, *args, **kwargs)
    elif (command == 'SumOfWeightsWhereNull') | (command == 'wSumOfWeightsWhereNull'):
        return wSumOfWeightsWhereNull(dta, sourceColumn, varForWeights, *args, **kwargs)

    elif (command == 'zScore') | (command == 'wZScore'):
        return wZScore(dta, sourceColumn, varForWeights, *args, **kwargs)
    elif (command == 'valueForZScore') | (command == 'wValueForZScore'):
        return wValueForZScore(dta, sourceColumn, varForWeights, *args, **kwargs)

    elif (command == 'quantiles') | (command == 'wQuantiles'):
        return wQuantiles(dta, sourceColumn, varForWeights, *args, **kwargs)
    elif (command == 'qcut') | (command == 'wQCut'):
        return wQCut(dta, sourceColumn, varForWeights, *args, **kwargs)

    # And a few un-weighted values that are sometimes useful along side weighted ones
    elif (command == 'count'):
        return len(dta)
    elif (command == 'count_unique'):
        return len(dta[sourceColumn].unique())
    
    
def wAgg(dta, aggregationDict, varForWeights, *args, **kwargs):
    if (varForWeights not in dta.columns):
        raise Exception("Missing Weights Field: " + varForWeights)

    d = {}
    isSeries = False
    for destColumn in aggregationDict:        
        commandTuple = aggregationDict[destColumn]
        sourceColumn = commandTuple[0]
        command = commandTuple[1]
        args = commandTuple[2:]
        tmp= wCallCommand(dta, command, sourceColumn, varForWeights, *args, **kwargs)
        if isinstance(tmp, pd.core.series.Series): # and len(tmp) > 1
            isSeries= True
        d[destColumn] = tmp

    if isSeries:
        return pd.DataFrame(d)
    else:
        return pd.Series(d, index=aggregationDict.keys())



def wGroupByAgg(dta, groupByVarList, aggregationDict, varForWeights, *args, **kwargs):
    '''

    :param dta:
    :type dta:
    :param groupByVarList:
    :type groupByVarList:
    :param aggregationDict:   This is the most important part - you need a dictionary of 3-tuples. First part of tuple is COMMAND (see wCommand for options); Second part is VARIABLE NAME; Third Part is Additional Arguments you want to pass to the underlying command
    :type aggregationDict:
    :param varForWeights:
    :type varForWeights:
    :param args:
    :type args:
    :param kwargs:
    :type kwargs:
    :return:
    :rtype:
    '''
    if (varForWeights not in dta.columns):
        raise Exception("Missing Weights Field: " + varForWeights)

    grouped = dta.groupby(groupByVarList, observed=True)

    d = None

    for destColumn in aggregationDict:        
        commandTuple = aggregationDict[destColumn]
        sourceColumn = commandTuple[0]
        command = commandTuple[1]
        args = commandTuple[2:]
        # if (sourceColumn == "bills_on_time" or sourceColumn=="numericCat"):
        #    print("Debug here")
            # dta.retired = dta.retired.astype(str)
        result = grouped.apply(wCallCommand, command, sourceColumn, varForWeights, *args, **kwargs)
        # dfResult = pd.DataFrame(seriesResult, columns=[destColumn]) # doesn't work with Multiindexes
        if isinstance(result,pd.core.frame.DataFrame):
            if len(result.columns) > 1:
                dfResult = result.unstack()
                dfResult = dfResult.reorder_levels(groupByVarList + [sourceColumn]).sort_index()
                dfResult = pd.DataFrame(dfResult)
            else:
                dfResult = result
            # dfResult.add_prefix(destColumn + ":")
        else:
            dfResult = pd.DataFrame(result)

        if len(dfResult) >0 and len(dfResult.columns) > 0:
            dfResult.columns = [destColumn]
            if d is None:
                d = dfResult
            else:
                # if (bool(set(d.columns.tolist()) & set(dfResult.columns.tolist()))):
                    # d = d.join(dfResult, how = 'outer', rsuffix=destColumn)
                # else:

                with warnings.catch_warnings():
                    warnings.simplefilter(action='ignore', category=RuntimeWarning)
                    # This line generates a warning. It's annoying. It's a bug in Pandas, though (it ignores the Sort=False param passed in here)
                    d = d.join(dfResult, how = 'outer', sort=False)

    return d
    

############################
# BiVariate Analyses, with Weights
############################

def wCrossTabByVar(dta, Xvar, Yvar, varForWeights, normalize=False, dropna= True):
    '''
    Caclulate a Weighted cross tab.  Note -- only works for two-D cross tabs
    From https://stackoverflow.com/questions/30314217/weighting-results-in-pandas-crosstab
    Sums up the weights in each cross-tab cell
    :param dropna:
    :type dropna:
    :param dta:
    :type dta:
    :param Xvar:
    :type Xvar:
    :param Yvar:
    :type Yvar:
    :param varForWeights:
    :type varForWeights:
    :param normalize:
    :type normalize:
    :return:
    :rtype:
    '''
    if normalize:
        if dropna == True: # Default behavior, do nothing special (note: the dropna in the CrossTab refers to the output columns, not the input data.  See https://stackoverflow.com/questions/33303314/confusing-behaviour-of-pandas-crosstab-function-with-dataframe-containing-nan
            return pd.crosstab(dta[Xvar], dta[Yvar], aggfunc = sum, values= dta[varForWeights], colnames=[Yvar], rownames=[Xvar], dropna=False).apply(lambda r: r/r.sum(), axis=0)
        else: # dropna == False:
            return pd.crosstab(dta[Xvar].fillna(CONST_NA_STRING), dta[Yvar].fillna(CONST_NA_STRING), aggfunc=sum, values=dta[varForWeights], colnames=[Yvar],rownames=[Xvar], dropna=False).apply(lambda r: r / r.sum(), axis=0)
    else:
        if dropna == True: # Default behavior, do nothing special
            return pd.crosstab(dta[Xvar], dta[Yvar], aggfunc = sum, values= dta[varForWeights], colnames=[Yvar], rownames=[Xvar], dropna=False)
        else:
            return pd.crosstab(dta[Xvar].fillna(CONST_NA_STRING), dta[Yvar].fillna(CONST_NA_STRING), aggfunc = sum, values= dta[varForWeights], colnames=[Yvar], rownames=[Xvar], dropna=False)


def wCrossTab(XDataSeries, YDataFrame, weightData, normalize=False, dropna= False):
    '''
    Caclulate a Weighted cross tab.  Note -- should work for multi-D cross tabs
    From https://stackoverflow.com/questions/30314217/weighting-results-in-pandas-crosstab
    :param XDataSeries:
    :type XDataSeries:
    :param YDataFrame:
    :type YDataFrame:
    :param weightData:
    :type weightData:
    :param normalize:
    :type normalize:
    :return:
    :rtype:
    '''
    if normalize:
        if dropna == True: # Default behavior, do nothing special (note: the dropna in the CrossTab refers to the output columns, not the input data.  See https://stackoverflow.com/questions/33303314/confusing-behaviour-of-pandas-crosstab-function-with-dataframe-containing-nan
            tmp= pd.crosstab(XDataSeries, YDataFrame, aggfunc = sum, values= weightData, dropna= False).apply(lambda r: r/r.sum(), axis=0)
        else:
            tmp= pd.crosstab(XDataSeries.fillna(CONST_NA_STRING), YDataFrame.fillna(CONST_NA_STRING), aggfunc = sum, values= weightData, dropna= False).apply(lambda r: r/r.sum(), axis=0)
         # tmp.columns = [""]
    else:
        if dropna == True: # Default behavior, do nothing special (note: the dropna in the CrossTab refers to the output columns, not the input data.  See https://stackoverflow.com/questions/33303314/confusing-behaviour-of-pandas-crosstab-function-with-dataframe-containing-nan
            tmp = pd.crosstab(XDataSeries, YDataFrame, aggfunc = sum, values= weightData, dropna= False)
        else:
            tmp = pd.crosstab(XDataSeries.fillna(CONST_NA_STRING), YDataFrame.fillna(CONST_NA_STRING), aggfunc = sum, values= weightData, dropna= False)
    return tmp


def wCovariance_Local(x, y, weights): #computing Weighted Covariance
    return np.sum(weights * (x - np.average(x, weights=weights)) * (y - np.average(y, weights=weights))) / np.sum(weights)

def wCorr_Local(x,y,weights):
    # Note -- we could also use https://www.statsmodels.org/stable/generated/statsmodels.stats.weightstats.DescrStatsW.html
    # https://www.statsmodels.org/stable/generated/statsmodels.stats.weightstats.DescrStatsW.corrcoef.html#statsmodels.stats.weightstats.DescrStatsW.corrcoef
    # raise Exception('incomplete - prints, does not return, results')
    """
    Computes weighted Pearson correlations, based on https://stackoverflow.com/a/38647581/11999203
    """
    wt_corr= wCovariance_Local(x, y, weights) / np.sqrt(wCovariance_Local(x, x, weights) * wCovariance_Local(y, y, weights)) #computing Weighted Correlation

    return wt_corr

def wCorrAll_Local(dta, varsToCorr, weightVar, skipna=True):
    i = 0
    j = 0

    corrs = np.zeros(shape=(len(varsToCorr), len(varsToCorr)), dtype='float')

    wData = dta[weightVar]
    for i in range(0, len(varsToCorr)-1,1):
        for j in range(i+1, len(varsToCorr), 1):

            xData = dta[varsToCorr[i]]
            yData = dta[varsToCorr[j]]

            if skipna:
                naMask = ~((xData.isna()) | (yData.isna()) | (wData.isna()))
            else:
                naMask = pd.Series([True]).repeat(len(wData))

            theCorr = wCorr_Local(xData[naMask], yData[naMask], wData[naMask])
            corrs[i][j] = theCorr

    return pd.DataFrame(corrs, index= varsToCorr, columns= varsToCorr)


def wCorr(dta, varsToCorr, weightVar):

    wt_stat = DescrStatsW(dta[varsToCorr], weights=dta[weightVar], ddof=0)
    corrs = wt_stat.corrcoef
    df =  pd.DataFrame(corrs, index= varsToCorr, columns= varsToCorr)
    return df



def wRegression(dta, IVs,DV,varforWeights,addConstant=False, reg_type = "OLS"):
    """
    Computes basic weighted univariate Linear (OLS) and Logistic Regressions using statsmodels
    """
    ivDta = dta[IVs]
    dvDta = dta[DV]
    weightDta = dta[varforWeights]

    if addConstant:
        ivDta = sm.add_constant(ivDta) #Adds intercept to model
        
    if reg_type == "OLS":
        # sm'S OLS "Weights" aren't really weights..
        # reg_results = sm.OLS(dvDta,ivDta,weights=weightDta).fit()

        # Only GLM supports frequncy weights
        reg_results = sm.GLM(dvDta,ivDta, family=sm.families.Gaussian(), freq_weights = weightDta).fit()

        return reg_results
        # print(reg_results.summary())
    elif reg_type == "Logistic":
        # sm'S Logit "Weights" aren't really weights..
        # reg_results = sm.Logit(dvDta,ivDta,weights=weightDta).fit() #Running the regression

        # Only GLM supports frequncy weights
        reg_results = sm.GLM(dvDta,ivDta, family=sm.families.Binomial(), freq_weights = weightDta).fit()

        # print(reg_results.summary())  #Getting the results
        # print(np.exp(reg_results.params)) #Getting the Odds Ratio effect size
        return reg_results
    elif reg_type == "Quantile":
        raise Exception("Don't trust Python's Quant Reg. Use Stata or R instead")

        # mod = sr.quantile_regression.QuantReg(endog=dvDta,exog=ivDta)
        # return mod.fit(q=.5)

    else:
        
        raise Exception("Unknown Regression Type")

############################
# General Multivariate Analyses, with Weights
############################

def wDescribe(dtaArray,weights, skipna=True):
    """
    Computes basic weighted descriptive statistics [Mean, Std. Deviation, Variance, Std. Error of weighted means, Quartiles] 
    using the statsmodels DescrStatsW module [https://www.statsmodels.org/dev/generated/statsmodels.stats.weightstats.DescrStatsW.html]
    
    -- Same as the Describe function in Pandas (plus a few more), but with weights
    -- Note, to properly match Pandas, you'd use wDescribe.transpose()
    """
    
    if skipna:
        naMask = ~((dtaArray.isna()) | (weights.isna())) 
    else:
        naMask = pd.Series([True]).repeat(len(weights))
        
    wt_stat = DescrStatsW(dtaArray[naMask], weights=weights[naMask], ddof=0)
    numValidValues = sum(naMask)

    n = len(weights)
    nNull = dtaArray.isna().sum()
    nZero = (dtaArray == 0).sum()
    theSum = wt_stat.sum
    totalWeights = wt_stat.sum_weights
    totalWeightsWhereNull =  (dtaArray.isna()*weights).sum()
    totalWeightsWhereZero=  ((dtaArray == 0)*weights).sum()
    # count = wt_stat.nobs + (dtaArray.isna()*weights).sum()
    average= wt_stat.mean
    if (numValidValues <= 1):
        median= None
        first_q=None
        third_q=None
        std_dev= None
        variance= None
        std_error= None
    else:
        median= wt_stat.quantile(0.5, return_pandas=False)[0]
        first_q=wt_stat.quantile(0.25, return_pandas=False)[0]
        third_q=wt_stat.quantile(0.75, return_pandas=False)[0]
        std_dev= wt_stat.std
        variance= wt_stat.var
        std_error= wt_stat.std_mean


    return pd.DataFrame({
        'N':n,
        'N Null': nNull,
        'N Zero': nZero,
        # 'count': count,
        'mean':average,
        'std':std_dev,
        'min': np.amin(dtaArray),
        '25%':first_q, 
        '50%':median,
        '75%':third_q,
        'max': np.amax(dtaArray),
        'variance':variance, 
        'std. error':std_error,
        'total': theSum,
        'w.total':totalWeights,
        'w.total (null)':totalWeightsWhereNull,
        'w.total (zero)':totalWeightsWhereZero,
        # 'countWhereNull': countNull
        }, index=['W.Stats'])


def wDescribeByVar(dta, varToDescribe, weightVar, skipna=True):
    return wDescribe(dta[varToDescribe], dta[weightVar], skipna=True)

def wGroupedDescribeByVar(dta,groupByVarList, varToDescribe, weightVar):
    tmpData = dta[groupByVarList + [varToDescribe] + [weightVar]]
    grouped = tmpData.groupby(groupByVarList, observed=True)
    allResults = grouped.apply(wDescribeByVar, varToDescribe, weightVar)
    return allResults


# Get weighted median values for multiple columns in a DF
# Note, one could also develop a more general Weighted Agg function that took a 
# Dictionary for whether you needed a weightedSum, count, etc, -- just like the normal Agg function 
def wMedianMultiple(dta, varsToGetMedian, varForWeights):
    d = {}
    for varToGetMedian in varsToGetMedian:
        d[varToGetMedian] = wMedian(dta,varToGetMedian, varForWeights)
    return pd.Series(d, index=varsToGetMedian)


##############################
## Cleaning
##############################

    
def wRemoveOutliers_ZScore(dta, X, varForWeights, zScoreThreshold = 3, replacementValue = None, noBelowZero = False):
    localDta = dta[[X, varForWeights]].copy()
    if noBelowZero:
        print(str((localDta[X] < 0).sum()) + ' values of ' + varForWeights + ' are below zero and will be removed')
        localDta.loc[localDta[X] < 0, X] = replacementValue
    # tempVar = 'temp_ZScoreFor' + varForWeights 
    localDta['zScores'] = wZScore(localDta, X, varForWeights)
    # localDta['zScores'].isna().sum()

    valueThreshold = wValueForZScore(localDta, X, varForWeights, zScoreThreshold)    
    
    # Unlike most functions, CLEANING data should almost always be LOUD: telling you what it's doing with Print statements
    print(str((localDta['zScores'] > zScoreThreshold).sum()) + ' values of ' + varForWeights + ' are above the ZScore Threshold of ' + str(valueThreshold) + ' (Z:'+ str(zScoreThreshold) + ') and will be removed.')
    print(str((localDta['zScores'] < -zScoreThreshold).sum()) + ' values of ' + varForWeights + ' are below the ZScore Threshold of ' + str(valueThreshold) + ' (Z:'+ str(zScoreThreshold) + ') and will be removed.')

    localDta.loc[localDta.zScores > zScoreThreshold, X] = replacementValue
    localDta.loc[localDta.zScores < -zScoreThreshold, X] = replacementValue
    # dta.drop(columns=[tempVar], inplace=True)
    return localDta[X]
        
