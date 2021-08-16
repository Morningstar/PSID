import os
import pandas as pd

class NIPAInflationReader:
    
    def __init__(self, dataDirectory = "C:/Dev/public_data/Fed_NIPA", 
                 inflationFileName = "Price_Deflation.csv"):
        self.dta = pd.read_csv(os.path.join(dataDirectory, inflationFileName))
        self.dta.rename(columns={'DATE':'date', 'DPCERD3A086NBEA': 'priceLevel', 'DPCERD3A086NBEA_PCH': 'percentChange'}, inplace=True)
        self.dta['year'] = pd.to_datetime(self.dta.date).dt.year 
        
    def getInflationDF(self):
        return self.dta[['year', 'priceLevel']]
     
    def getPriceSeriesBetweenTwoYears(self, startYearInclusive, endYearInclusive):
        vals = self.dta.loc[(self.dta.year <= endYearInclusive) & (self.dta.year >= startYearInclusive), ['year','priceLevel']]
        return vals

    def getAnnualChangeBetweenTwoYears(self, startYearInclusive, endYearInclusive):
        vals = self.dta.loc[(self.dta.year <= endYearInclusive) & (self.dta.year >= startYearInclusive), ['year','percentChange']]
        return vals
     
    ''' Get relative change in prices:  a multiplier for prices to show change over time.
    1 = no change
    2 = twice as expensive
    '''
    def getInflationFactorBetweenTwoYears(self, startYearInclusive, endYearInclusive):
        startingPriceLevel = self.dta.loc[(self.dta.year == startYearInclusive), 'priceLevel']
        endingPriceLevel = self.dta.loc[(self.dta.year == endYearInclusive), 'priceLevel']
        if ((len(startingPriceLevel) > 1) or  (len(endingPriceLevel) > 1)):
            raise Exception("We have more than one row of inflation information for a given year")
        else:
            startingPriceLevel = startingPriceLevel.iloc[0]
            endingPriceLevel = endingPriceLevel.iloc[0]
            
        return (endingPriceLevel) /startingPriceLevel
    