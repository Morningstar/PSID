import os
import pandas as pd

class CPIInflationReader:
    
    def __init__(self, cpiDirectory = "C:/Dev/public_data/CPI_Inflation/", 
                 cpiFileName = "CPI_Data_From_InflationDataCom.csv"):
        self.dta = pd.read_csv(os.path.join(cpiDirectory, cpiFileName))
        self.dta.rename(columns={'YEAR':'year', 'AVE': 'priceLevel'}, inplace=True)
        
    def getInflationDF(self):
        return self.dta[['year', 'priceLevel']]
     
    def getPriceSeriesBetweenTwoYears(self, startYearInclusive, endYearInclusive):
        vals = self.dta.loc[(self.dta.year <= endYearInclusive) & (self.dta.year >= startYearInclusive), ['year','priceLevel']]
        return vals
     
    ''' Get relative change in prices:  a multiplier for prices to show change over time.
    1 = no change
    2 = twice as expensive
    '''
    def getInflationFactorBetweenTwoYears(self, startYearInclusive, endYearInclusive):
        startingCPI = self.dta.loc[(self.dta.year == startYearInclusive), 'priceLevel']
        endingCPI = self.dta.loc[(self.dta.year == endYearInclusive), 'priceLevel']
        if ((len(startingCPI) > 1) or  (len(endingCPI) > 1)):
            raise Exception("We have more than one row of inflation information for a given year")
        else:
            startingCPI = startingCPI.iloc[0]
            endingCPI = endingCPI.iloc[0]
            
        return (endingCPI) /startingCPI
    