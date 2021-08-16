def clearGreaterThan(theSeries, testValue, replacementValue = None, otherSeriesToTestAgainst = None):
    if otherSeriesToTestAgainst is not None:
        print(str((otherSeriesToTestAgainst > testValue).sum()) + ' values of ' + otherSeriesToTestAgainst.name + ' are above the threshold of ' + str(testValue) +  ' and will be removed from ' + theSeries.name)
        replacedSeries = theSeries.copy()
        replacedSeries[otherSeriesToTestAgainst > testValue] =  replacementValue
    else:
        print(str((theSeries > testValue).sum()) + ' values of ' + theSeries.name + ' are above the threshold of ' + str(testValue) +  ' and will be removed.')
        replacedSeries = theSeries.copy()
        replacedSeries[replacedSeries > testValue] =  replacementValue
    return replacedSeries
    
def clearLessThan(theSeries, testValue, replacementValue = None, otherSeriesToTestAgainst = None):
    if otherSeriesToTestAgainst is not None:
        print(str((otherSeriesToTestAgainst < testValue).sum()) + ' values of ' + otherSeriesToTestAgainst.name + ' are below the threshold of ' + str(testValue) +  ' and will be removed from ' + theSeries.name)
        replacedSeries = theSeries.copy()
        replacedSeries[otherSeriesToTestAgainst < testValue] =  replacementValue
    else:
        print(str((theSeries < testValue).sum()) + ' values of ' + theSeries.name + ' are below the threshold of ' + str(testValue) +  ' and will be removed.')
        replacedSeries = theSeries.copy()
        replacedSeries[replacedSeries < testValue] =  replacementValue
    return replacedSeries
    
def clearEqualTo(theSeries, testValue, replacementValue = None, otherSeriesToTestAgainst = None):
    if otherSeriesToTestAgainst is not None:
        print(str((otherSeriesToTestAgainst == testValue).sum()) + ' values of ' + otherSeriesToTestAgainst.name + ' are equal to the value of ' + str(testValue) +  ' and will be removed from ' + theSeries.name)
        replacedSeries = theSeries.copy()
        replacedSeries[otherSeriesToTestAgainst == testValue] =  replacementValue
    else:
        print(str((theSeries == testValue).sum()) + ' values of ' + theSeries.name + ' are equal to the value of ' + str(testValue) +  ' and will be removed.')
        replacedSeries = theSeries.replace(to_replace=testValue, value = replacementValue)
    return replacedSeries
