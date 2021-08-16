"""
This code is an adaptation of the "read_sas.py" file in Tyler Abbot's Psid_Py Package, releasted on 23 June 2015.  See The Readme.md for more information.

It has functions that allow you to read a SAS dataset and converts it to a python dataframe.  It is used by PSID/RawLoader.py to create CSV files.

"""
import re
import os
import tempfile
import zipfile
import pandas as pd
import numpy as np


def first_clean_up(lines):
    """
    A function to remove line delimiters, comments, tabs, etc. from the
    .sas dictionary file.
    Parameters
    ----------
    lines    :   list of strings; the raw file
    """
    #Remove all tabs from the string
    for i in range(0, len(lines)):
        lines[i] = re.sub('\t', ' ', lines[i])
        lines[i] = re.sub('\r', '', lines[i])
        lines[i] = re.sub('\n', '', lines[i])

    #Remove all comments from the code
    start_comment = 0
    for i in range(0, len(lines)):
        if lines[i].find('/*') >= 0:
            start_comment = i
        elif lines[i].find('*/') >= 0:
            lines[start_comment] = lines[start_comment]\
                .replace('/*', '')
            lines[start_comment] = lines[start_comment]\
                .replace('*', '')
            lines[i] = lines[i].replace('*/', '')
            lines[i] = lines[i].replace('*', '')
            if i > start_comment + 1:
                lines[start_comment + 1:i] = ['' for x in
                                              range(start_comment+1, i)]
    for i in range(0, len(lines)):
        lines[i] = lines[i].replace('*', '')
    return lines


def find_input(lines):
    """
    A function to find the the word INPUT, indicating the start of variables.
    Parameters
    ----------
    lines    :   list of strings; the raw file
    """
    #Find the first line containing the word 'INPUT', which indicates variables
    for i in range(0, len(lines)):
        if lines[i].find('INPUT') < 0:
            pass
        else:
            firstline = i
            break
    return firstline


def find_semicolon(lines, firstline):
    """
    A function to find the the first semicolon, indicating the end of
    the first variable definition.
    Parameters
    ----------
    lines       :       list of strings; the raw file
    firstline   :       integer; the index of the start of the first line
    """
    #Find the first line containing the word 'INPUT', which indicates variables
    for i in range(firstline, len(lines)):
        if lines[i].find(';') < 0:
            pass
        else:
            lastline = i
            break
    return lastline


def second_clean_up(lines, firstline, lastline):
    """
    A function to remove all the variable definition information and seperate
    the file into individual entries.  It returns a list object containing
    lines from the sas variable definition section.
    Parameters
    ----------
    lines       :   list of strings; the raw file
    firstline   :   integer; the index of the start of variable definition
    lastline    :   integer; the index of the end of variable definition
    """
    #Extract the fixed width file (FWF) input lines
    FWFlines = lines[firstline:lastline + 1]

    #Remove the INPUT command and the trailing ';'
    FWFlines[0] = FWFlines[0].replace('INPUT', '')
    FWFlines[len(FWFlines) - 1] = FWFlines[len(FWFlines) - 1].replace(';', '')

    #Add spaces around of all dollar signs and dashes
    #NOTE: Is this necessary?
    for i in range(0, len(FWFlines)):
        FWFlines[i] = FWFlines[i].replace('$', ' $ ')
        FWFlines[i] = FWFlines[i].replace('-', ' - ')

    #Remove all blank lines
    FWFlines = [x for x in FWFlines if not x.isspace()]

    #Split the string
    z = [x.split(' ') for x in FWFlines]

    #Initiate a character list
    sas_input_lines = []

    #Throw out empty characters and then concatenate lines
    for i in range(0, len(z)):
        for k in range(0, len(z[i])):
            z[i][k] = z[i][k].replace('-', '')
            z[i][k] = z[i][k].replace(' ', '')
        z[i] = [x for x in z[i] if x != '']
        sas_input_lines += z[i]
    return sas_input_lines


def ampersand_parse(sas_input_lines, DF):
    """
    A function to parse the data if they are of the form @START VARNAME.
    Parameters
    ----------
    sas_input_lines :   list of strings; the cleanedsas variable file
    DF              :   DataFrame; the dataframe to fill
    """
    #Initialize positional counters
    i = j = 0
    while i < len(sas_input_lines):
        start_point = int(sas_input_lines[i].replace('@', ''))

        #Check the width of the variable definition
        #Skip the first time
        if i > 0:
            if DF['start'][j-1] + DF['width'][j-1] < start_point:
                DF['width'][j] = DF['start'][j-1] + DF['width'][j-1]\
                    - start_point
                j += 1

        #Set first word to variable name
        DF['start'][j] = start_point
        DF['varname'][j] = sas_input_lines[i+1]

        #If there is a dollar sign, record character type
        if sas_input_lines[i+2] == '$':
            DF['char']['j'] = True
            i += 1
        else:
            DF['char'][j] = False

        #Remove leading f and char
        for k in ['F', 'CHAR']:
            sas_input_lines[i+2] = sas_input_lines[i+2].replace(k, '')

        #If the length has a period, split it
        try:
            if sas_input_lines[i+2].find('.') >= 0:
                period = sas_input_lines[i+2].find('.')
                DF['width'][j] = int(sas_input_lines[i+2][0:period])
                DF['divisor'][j] = 1/10**int(sas_input_lines[period+1:])
        except IndexError:
            pass
        else:
            DF['width'][j] = int(sas_input_lines[i+2])
            DF['divisor'][j] = 1

        i += 3
        j += 1
    return DF


def widths_not_places_parse(sas_input_lines, DF):
    """
    A function to parse the data if they are of the form VARNAME LENGTH.
    Parameters
    ----------
    sas_input_lines :   list of strings; the cleanedsas variable file
    DF              :   DataFrame; the dataframe to fill
    """
    #Initialize positional counters
    i = j = 0

    while i < len(sas_input_lines):
        #Set first word to variable name
        DF['varname'][j] = sas_input_lines[i]

        #If there's a $ between first word and fist number, record as char
        if sas_input_lines[i+1] == '$':
            DF['width'][j] = int(sas_input_lines[i+2])
            DF['char'][j] = True
            i += 3
        #Else record as numeric type
        else:
            DF['width'][j] = int(sas_input_lines[i+2])
            DF['char'][j] = False
            i += 2

        #Search for a divisor
        try:
            if sas_input_lines[i].find('.') >= 0:
                period = sas_input_lines[i].find('.')
                divisor = int(sas_input_lines[i][period+1:])
                DF['divisor'][j] = 1/10**divisor
                i += 1
        except IndexError:
            pass
        else:
            DF['divisor'][j] = 1

        j += 1
    return DF


def hash_parse(sas_input_lines, DF):
    """
    A function to parse the data if they are of the form VARNAME #START - #END.
    Parameters
    ----------
    sas_input_lines :   list of strings; the cleanedsas variable file
    DF              :   DataFrame; the dataframe to fill
    """
    #Initialize positional counters
    i = j = 0

    while i < len(sas_input_lines):
        #Set first word to variable name
        DF.loc[j, 'varname'] = sas_input_lines[i]

        #If there is a $, char type
        if sas_input_lines[i+1] == '$':
            DF['start'][j] = int(sas_input_lines[i+2]) # Note -- correction from original. original missed [j]

            #Check the width
            if any([not sas_input_lines[i+3].isdigit(),
                    sas_input_lines[i+3].find('.') >= 0]):
                DF['end'][j] = DF['start'][j]
                i -= 1
            else:
                DF['end'][j] = int(sas_input_lines[i+3])
            DF['char'][j] = True
            i += 4
        #Otherwise type numeric
        else:
            DF['start'][j] = int(sas_input_lines[i+1])

            #Check the width
            if any([not sas_input_lines[i+2].isdigit(),
                   sas_input_lines[i+2].find('.') >= 0]):
                DF['end'][j] = DF['start'][j]
                i -= 1
            else:
                DF['end'][j] = int(sas_input_lines[i+2])
            DF['char'][j] = False
            i += 3
        #print(i, DF.shape, len(sas_input_lines))
        #Check for a divisor
        try:
            if sas_input_lines[i].find('.') >= 0:
                period = sas_input_lines[i].find('.')
                divisor = int(sas_input_lines[i][period+1:])
                DF['divisor'][j] = 1/10**divisor
                i += 1
        except IndexError:
            pass
        else:
            DF['divisor'][j] = 1

        #For higher rows
        if j > 0:
            #If the start of current row is higher than previous end + 1
            #add space
            if int(DF['start'][j]) > int(DF['end'][j-1]) + 1:
                tempDF = pd.DataFrame(DF.loc[0]).copy().transpose()
                tempDF.loc[0] = None
                DF = pd.concat([DF.loc[:j-1], tempDF, DF.loc[j:]])
                j += 1
                DF.index = range(0, DF.shape[0])
                DF['start'][j-1] = int(DF['end'][j-2]) + 1
                DF['end'][j-1] = int(DF['start'][j]) - 1
        j += 1

    #Calculate the width
    DF['width'] = DF['end'] - DF['start'] + 1
    #Replace missing variable names with negative number
    temp = pd.get_dummies(DF['varname'],dummy_na=True)
    dummy_for_missing = pd.get_dummies(DF['varname'],dummy_na=True)[np.NaN]*(-2) + 1
    DF['width'] = DF['width']*dummy_for_missing

    return DF



def parse_sas(dict_file, beginline=0, lrecl=None):
    """
    A function to parse the sas dictionary file.
    Parameters
    ----------
    dict_file   :   string; file path. Must be a .sas dictionary file
    beginline   :   integer; the line on which to begin
    lrecl       :   integer; the record length
    """
    #Open the dictionary file
    file = open(dict_file)

    #Read the entire file into a string
    sas_input = file.readlines()

    #Close the file so you don't screw it up
    file.close()

    #Start at the user specified begin line
    sas_input = sas_input[beginline:]

    #Clean up the file
    sas_input = first_clean_up(sas_input)

    #Convert to upper case
    sas_input = [x.upper() for x in sas_input]

    #Find the first line containing the word 'INPUT', which indicates variables
    firstline = find_input(sas_input)

    #Find the first ; following input.  This indicates the end of variable
    #definition
    lastline = find_semicolon(sas_input, firstline)

    #Finish cleaning up
    sas_input_lines = second_clean_up(sas_input, firstline, lastline)

    #Create FWF structure file
    columns = ['start', 'end', 'width', 'varname', 'char', 'divisor']
    DF = pd.DataFrame(columns=columns)

    #Test for the type of file organization and remove any dollar signs
    elements_2_4 = sas_input_lines[1:4] # SW: Shoudln't that be 0-3?
    elements_2_4 = [x for x in elements_2_4 if x != '$']

    widths_not_places = (len(elements_2_4) == 2 and elements_2_4[1].isdigit())

    #Parse the file based on its structure
    #structure: @START VARNAME
    if len([x for x in sas_input_lines if x.find('@') >= 0]) > 0:
        DF = ampersand_parse(sas_input_lines, DF)

    #structure: VARNAME LENGTH
    elif widths_not_places:
        DF = widths_not_places_parse(sas_input_lines, DF)

    #structure: VARNAME #START - #END
    else:
        DF = hash_parse(sas_input_lines, DF)

    #Take only the four necessary columns
    DF = DF[['varname', 'width', 'char', 'divisor']]

    #If the final record length is specified
    if lrecl:
        if lrecl < DF['width'].abs().sum():
            print('ERROR: The logical record length (lrecl) parameter is'
                  + 'shorter than constructed SAS columns.')
        if lrecl > DF['width'].abs().sum():
            #Add blank space to fill the difference
            length_of_blank = lrecl - DF['width'].abs().sum()
            DF['width'][DF.shape[0]-1] = length_of_blank

    return DF


def read_sas(data_file, dict_file, outputCSV, outputMeta, beginline=1, buffersize=50,
             zipped=False, lrecl=None, skip_decimal_division=None):
    """
    A function to read in sas data files and output a file type of the user's
    specification.
    Parameters
    ----------
    data_file       :   string; .txt data file
    dict_file       :   string; must be a .sas dictionary file
    out_type        :   string; specifies the file type for output.  Options
                        include: csv, excel, hdf, squl, json, html, gbq, stata
    beginline       :   integer;
    """
    DF = parse_sas(dict_file, beginline, lrecl)

    #Take only rows with variable names
    DF_cleaned = DF.dropna(subset=['varname'])

    #If the ASCII file is zipped, unpack it and store
    if zipped:
        td = tempfile.mkdtemp()
        temp = zipfile.ZipFile(data_file)
        name = temp.namelist()
        if len(name) > 1:
            print('ERROR: The data file is a zip archive containing multiple '
                  + 'files.  Please supply only a single file.')
        temp.extract(name, td)
        data_file = td + os.sep + name

    #Initialize data frames
    print('Reading in ASCII file.  This could take a while.')

    #Read in sas file
    DF_cleaned['width'] = DF_cleaned['width'].astype(int)
    sas_file = pd.read_fwf(data_file,
                           widths=DF_cleaned['width'],
                           names=list(DF_cleaned['varname']),
                           header=None)

    print("Finished reading in data.\n")
    # return sas_file
    
    sas_file.to_csv(outputCSV, index=False)
    DF_cleaned.to_csv(outputMeta, index=False)

    #Loop through rows, converting to numeric and dividing
    #by the divisor where necessary
    if (not skip_decimal_division) and (len(DF_cleaned.loc[~(DF_cleaned.divisor.isin([1, np.NaN]))]) > 0):
        print("Adjusting for Scientific Notation.\n")
        for l in range(0, DF_cleaned.shape[0]):
            if (not skip_decimal_division) and (DF_cleaned.divisor[l] != 1):

                #If the sas data says should be numeric, convert
                if not DF_cleaned['char'][l]:
                    #Handle NAs introduced by coercion warnings by capturing them
                    #NOTE: This is an issue to be added later.  For now, simply convert
                    sas_file[str(DF_cleaned['varname'][l])] = \
                        sas_file[str(DF_cleaned['varname'][l])].astype(float)

                # Assuming that the data came from parse_sas, must correct for
                # scientific notation in the SAS file
                if not DF_cleaned.loc[l, 'char']:
                    sas_file.loc[l, :] *= DF_cleaned['divisor'][l]

    
        #Remove any temporary dirs


    return sas_file
    
