import os
import pandas as pd

# Todo -- this should be in the main param file
DEFAULT_CPI_DIR = "C:/Dev/src/MorningstarGithub/PSID/inputData/CPI_Inflation/"
DEFAULT_CPI_FILE = "CPI_Data_From_InflationDataCom.csv"

class CPIInflationReader:

    def __init__(self, cpiDirectory = DEFAULT_CPI_DIR,
                 cpiFileName = DEFAULT_CPI_FILE):
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
    