import requests
from bs4 import BeautifulSoup as bs
import pandas as pd
from pandas.io.json import json_normalize
import datetime
import seaborn as sns
import os
import time
import xmltodict
import re
import numpy as np
import re
import seaborn as sns
import matplotlib.pyplot as plt
from fredapi import Fred
from matplotlib import dates
import warnings
warnings.filterwarnings('ignore')

# Dataprocessing class : handles querying, data cleaning and wrangling.
class Dataprocessing():
    def __init__(self):
        """
        Docstring:
        ---------
        Constructor object for the Dataprocessing class.
        
        """
        pass
    def wikiParser(self,number_of_times,offset,language=None,page=None,nr_of_pages=10,fileout="all_Venezuela.xml",debug = False, verbose = True):
        """
        Docstring:
        A Wikipedia querier designed to get an easily-modulable number of revisions from Wikipedia
        It takes in conditions of the query such as the number of revisions to query at once or the page of interest.
        It outputs the query's result as a concatenated DataFrame.

        Parameters:
        -----------
        language : str
                    Language to use during query (like es = "español" or en = "english" ...).
                    In a class, the language is preset so it is set here to none.
        number_of_times : int
                    How many times should the query be run 
                    (a query is maximum 1000 revisions so one 
                    would need to make several successive ones 
                    to get all the revisions).
                    Note :
                    -----
                    If the number of queries is too high 
                    and the page has no more revisions, 
                    the function will stop querying and directly return the result.
        offset : int
                    The offset each successive query will start with 
                    ( 0 by default but if querying from a date onwards, you can specify it so).
        page : str
                    The page to be queried 
                    ( By default Venezuela for the purpose of the summative ).
                    As above, preset in the init call, thus set to none.

        nr_of_pages : int 
                    The number of revisions to ask for at once.
                    The maximum is 1000 ( and is the default ).
                    However certain pages or languages will be queried more easily wit lower numbers.
        fileout: str
                    The fileout to save the query result as an XML file. 
                    Also used in the function to store query results.
        verbose : bool
                    Whether the function should inform the user on how far it has progressed.
                    If True, will give an update at every iteration. 
                    Otherwise only tells the user when it is done.
        """
        ldf = [] # The list that will contain the dataframes
        print("Querying page of language : {}".format(language))
        for i in range(number_of_times):

            # The curl query with the variables in imput
            curl_query = '''
            curl -d "&pages={}&action=submit&limit={}&offset={}" https://{}.wikipedia.org/w/index.php?title=Special:Export -o "{}"
            '''.format(page,nr_of_pages,offset,language,fileout) 

            # Sleeping to not pummel the server ( for good manners and to evade chattel rights ).
            time.sleep(5)

            os.system(curl_query)

            # Heart of the function :
            #       - Will append generate a list of lists with different variables (revision id, ip, timestamp...)
            #       - Will make them into dataframes
            #       - Will append them to ldf


            try: 
                with open(fileout) as fd:
                    data = xmltodict.parse(fd.read())
            #print(data)
                    df = json_normalize(data["mediawiki"]["page"]["revision"])
                    ldf.append(df)

                offset = datetime.datetime.strptime(ldf[-1]["timestamp"].iloc[-1],"%Y-%m-%dT%H:%M:%SZ")
            except :
                print("Queried all the revisions on the {} page, stopping early, last recorded time stamp : {}.".format(language,offset) )# This is how I check for correctness 
                return pd.concat(ldf,ignore_index=True)
                break
            if verbose == True:
                print("iteration n°{} , done with {} rows. Last timestamp : {}.".format(i+1, len(ldf[-1]),offset))
        print("Done querying {}".format(language))
        return pd.concat(ldf,ignore_index=True)

    def textCleaner(self,text):
        """
        Docstring:
        ---------
        This is the text cleaner helper function.
        Designed to be run as part of a list comprehension to clean a column of code.
        
        Parameters:
        -----------
        text : str
               The entered string to be cleaned
        
        Returns:
        --------
        The string cleaned of html code and any newline characters
        
        """
        try:
            t = bs(text, "html").text.replace('\n', " ")
            t = t.lower()
            return t
        except:
            return None
        
    def lengthCounter(self,term,text):
        """
        Docstring:
        ---------
        This is the helper function that counts the number of mentions .
        
        Parameters:
        -----------
        term : str
               The term of interest that is searched for
        text : str
               The entered string to be checked for the word count of the word
        
        
        Returns:
        --------
        The integer of the length
        
        """
        try:
            return int(len(re.findall(term, text)))
        except:
            return 0
        
    def locationOnPage(self,term, text):
        """
        Docstring:
        ---------
        This is the helper function that gives the location on the page of the first mention of a word.
        It gives it out as a percent difference from the top of the page.
        
        Parameters:
        -----------
        term : str
               The term of interest that is searched for
        text : str
               The entered string to be checked for the location of the word
        
        
        Returns:
        --------
        
        Outputs the percent difference from the top, if the word is not on the page, it outputs None 
        Example : if the word it the first word on the page, it is 0% from the start
                  if it is in the middle of the page, it is 50% from the start
                  if it is the last word, it is 100% from the start 
        """
        try:
            if text.find(term) == -1:
                return np.NaN
            else:
                return 100*text.find(term)/len(text)
        except :
            return np.NaN

    def linkCounter(self,text):
        """
        Docstring:
        ---------
        This is the helper function to count the number of links in a given revision.
        
        Parameters:
        -----------
        text : str
               The text on the page to be searched for, in it links are detected with a regex.
        
        
        Returns:
        --------
        
        The number of links in that page
        
        """
        try:
            return len(re.findall(r"{{2}", text))+len(re.findall(r"\[{2}", text))
        except:
            return 0
        
    def vandalisationCleaner(self,dataframe, selectivity = -0.999, drop = False, col=True):
        """
        Docstring:
        ---------
        This is the helper function that detects vandalized pages 
        and either takes out of the dataframe or signals them with a dummy variable.
        
        Parameters:
        -----------
        
        dataframe : pd.DataFrame()
                    The dataframe in which to look for the percent drop in links which signals vandalised pages
        selectivity : int
                    if the percent of the links that dissapeared from revision to revision is higher, it has been vandalized
        drop : bool
                    if True, will drop the lines with vandalized revisions
        col : bool 
                    if True, will return the intact dataframe with a dummy column for vandalizations  
                    
        
        Returns:
        --------
        
        Either :
            - The initial DataFrame if both booleans are false
            - The DataFrame cleaned from vandalized content if drop is True
            - The initial DataFrame with a dummy variable for vandalized content if col = True
        
        """
        nr_of_vandalisation = len(dataframe[(dataframe["links"].pct_change()<selectivity)&(dataframe["timestamp"]>datetime.datetime(2004, 8, 5, 2, 30, 31))])
        print("{} revisions of this page have been victim of vandalisation attempts ( their number of links has brutally fallen )".format(nr_of_vandalisation))
        if drop == True and col ==False:
            print("Done dropping")
            return dataframe[(dataframe["links"].pct_change()>=selectivity) & (dataframe["timestamp"]>datetime.datetime(2004, 8, 5, 2, 30, 31))]
        elif col ==True and drop == False :

            dataframe["is_vandalized"] = (dataframe["links"].pct_change()<-0.999)&(dataframe["timestamp"]>datetime.datetime(2004, 8, 5, 2, 30, 31))

            dataframe.replace(to_replace = [True,False],value = [1,0], inplace = True)
            dataframe["is_vandalized"] = dataframe["is_vandalized"].astype(int)

            return dataframe["is_vandalized"]
    
    def lexiconCreater(self,dataframe,action,terms = [],col_names = []):
        """
        Docstring:
        ---------
        This is the helper function that implements any transformation sequentially for all the terms of interest.
        
        Parameters:
        -----------
        dataframe : pd.DataFrame()
                    Dataframe on which to perform the transformations
        action : function object
                    the function that will be performed on every element of the selected Series 
                    from the input dataframe
        terms : list
                    the term of interest ( here words to be searched for within the text )
        col_names : list
                    list of columns to perform the selected action on 
         
        
        
        Returns:
        --------
        The dataframe with the modifications performed 
        
        """
        
        for term in range(len(terms)):
            dataframe[col_names[term]] = [action(terms[term],i) for i in dataframe["text_clean"]]
        return dataframe
    
    def featureEngineer(self,dataframe, terms = None, save = False, smooth = 1,language="es",from_parser = False, repeat = False):
        """
        Docstring:
        ---------
        This is the main text cleaner, preprocessing and feature engineering function of this class.
        It is designed to be run just after the wikiParser.
        
        
        Parameters:
        -----------
        
        dataframe : pd.DataFrame()
                    Dataframe to be cleaned
                    
        terms : list
                    terms of interest to be searched for in the dataframe ("econ crisis" and inflation)
        save : bool 
                    Whether the returned dataframe should be saved or not.
                    Default is False.
        smooth : int
                    The smoothing parameter of percent change of wordcounts overtime
        language : str
                    The language of the analysis ( serves for translating the name of the variables)
                    
        from_parser : bool
                      Indicates whether the function is applied directly from the parser or not.
                      Implemented for robustness so as not to not run datetime.datetime.strptime over a datetime object.
        
        repeat : bool
                 Indicates whether the function is applied to a dataframe that has already been cleaned or not.
                 Implemented for robustness so as not to not run datetime.datetime.strptime over a datetime object. 
        
        Returns:
        --------
        
        The Dataframe with all of the text cleaned and the variables 
        of interest (wordcount,word position on page and percent variation) included as columns.
        
        """
        if language == "en":
            
            terms = ["economic crisis","inflation"]
        elif language == "es":
            
            terms = ["crisis económica","inflación"]
            
        dataframe.columns = [i.replace("'","") for i in dataframe.columns]
        print("replaced")
        dataframe.rename(columns = {"text.@bytes":"text_bytes","text.@xml:space":"text_xml","text.#text":"text"},inplace = True)
        print("renamed")
        dataframe.dropna(subset=["text"], inplace = True)
        print("dropped")
        dataframe["text_clean"] = [self.textCleaner(i) for i in dataframe["text"]]
        print("cleaned")
        dataframe = self.lexiconCreater(dataframe,action = self.lengthCounter,terms = terms,col_names= ["crisis","inflation"])
        dataframe = self.lexiconCreater(dataframe,action =self.locationOnPage,terms = terms,col_names = ["crisis_loc","inflation_loc"])
        print("features engineered")
        dataframe["links"] = [self.linkCounter(i) for i in dataframe["text_clean"]]
        
        if repeat == False:
            if from_parser == True:
                dataframe["timestamp"] = [datetime.datetime.strptime(i,"%Y-%m-%dT%H:%M:%SZ") for i in dataframe["timestamp"]]
            else:
                dataframe["timestamp"] = [datetime.datetime.strptime(i,"%Y-%m-%d %H:%M:%S") for i in dataframe["timestamp"]]
        else :
            pass
        
        dataframe["Year_month"] = [ i.strftime('%Y-%m')for i in dataframe["timestamp"]]
        dataframe["crisis_pct"] = dataframe["crisis"].pct_change(smooth).fillna(0)
        dataframe["inflation_pct"] = dataframe["inflation"].pct_change(smooth).fillna(0)
        dataframe["Year"] = [ i.strftime('%Y')for i in dataframe["timestamp"]]
        dataframe["is_vandalized"] = self.vandalisationCleaner(dataframe,drop = False)
        dataframe.reset_index(inplace = True,drop = True)
        print("done with all {} \n\n".format(language))
        
        
        
        
        if save == True:
            dataframe.to_csv("{}_final.csv".format(language))
        return dataframe
    
    def groupVariables(self,dataframe,variables=['crisis','inflation', 'crisis_loc', 'inflation_loc',  'Year_month',
                                          'crisis_pct','inflation_pct','is_vandalized'],
                                            by = "Year_month", method = "mean", save = False,language = "es"):
        """
        Docstring:
        ---------
        This is the basic grouping function.
        It is used to generate a grouped version of the queried and processed data. 
        In the report a group by month is used as it is the one that most conserves information.
        
        Parameters:
        -----------
        dataframe : pd.DataFrame()
                    Initial DataFrame containing the queried and cleaned data
        variables : list
                    List of the variables to group
        by : str
                    Variable to group on 
        method : str
                    Method to group with. 
                    Currently only supports mean as it
                    is what is used for the data collection.
        save : bool 
                    Whether the returned DataFrame should be saved or not
        language : str
                    What the language of the grouped dataframe is (important only for saving)
                    
        
        Returns:
        --------
        
        The grouped pd.DataFrame().
        
        """
        if method == "mean":
            if by not in variables:
                variables.append(by)
            grouped_df = dataframe[variables].groupby(by).mean()
            grouped_df.reset_index(inplace = True)
            try:
                grouped_df[by] = [datetime.datetime.strptime(i,"%Y-%m") for i in grouped_df[by]]
            except:
                grouped_df[by] = [datetime.datetime.strptime(i,"%Y") for i in grouped_df[by]]
            if save == True:
                grouped_df.to_csv("{}_groupedfinal.csv".format(language))
            return grouped_df
        else :
            print("Please insert mean as method")
            
            
    def getExteriorData(self, url, variable, method = "q"):
        """
        Docstring:
        ---------
        This queries the exterior data sources:
            - Quandl for Inflation rates
            - The FRED API as petrol prices were unnavailable on Quandl
        
        Parameters:
        -----------
        
        url :      str
                   The url of the request
        variable : str
                   The name of the variable once the data is put in a dataframe
        method :   str
                   tells the function of whether to query from quandl (q) or the FRED (f)
        
        
        Returns:
        --------
        A pandas DataFrame with the variable. 
        ( Note that if the variable is inflation there will be an added column for logged inflation rate)
        
        """
        if method == "q":
            # The data is returned as a long string that 
            # has to be split and cleaned to be put in a dataframe
            returned_request = requests.get(url)
            
            ll = [i.split(",") for i in returned_request.text.split("\n")]

            df = pd.DataFrame(ll[1:-1],columns = ["Date",variable])

            df[variable] = df[variable].astype(float)
            if variable == "Inflation_Rate":
                df["logInflation_Rate"] = np.log(df["Inflation_Rate"])
            
            df.sort_values(by=["Date"],inplace = True,ascending = False)
            df["Date"] = [datetime.datetime.strptime(i,"%Y-%m-%d") for i in df["Date"]]
            
            df["Year_Month"] = [i.strftime("%Y-%m") for i in df["Date"]]
            df["Year_Month"] = [datetime.datetime.strptime(i,"%Y-%m") for i in df["Year_Month"]]
            df.reset_index(inplace = True, drop=True)

            
        elif method == "f":
            fred = Fred(api_key='4fe98d4b20f9063272ac4d2ccd995984')

            data = fred.get_series('POILBREUSDM', observation_start='2002-01-01', observation_end='2020-11-09')
            df = pd.DataFrame(data, columns = [variable])
            df.reset_index(inplace=True)
            df.columns = ["Date",variable]
            #df["Date"] = [datetime.datetime.strptime(i,"%Y-%m-%d") for i in df["Date"]]
            
            df["Year_Month"] = [i.strftime("%Y-%m") for i in df["Date"]]
            df["Year_Month"] = [datetime.datetime.strptime(i,"%Y-%m") for i in df["Year_Month"]]
            
        return df
