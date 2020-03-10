
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

# Plotter class, handles all the plots I make in this task.
class Plotter():
    def __init__(self, size = None,fontsize = None):
        """
        Docstring:
        ---------
        Constructor function.
        It will contain the variable list of interest.
        It will contain the figuresize and fontsize for all the plots 
        to make all the plots in the class uniform.
        
        Parameters:
        -----------
        size : tuple
               Size of the plots of the plots of this class
        fontsize : int
                Size of the font of the plots of this class
        Returns:
        --------
        Nothing
        
        """
        sns.color_palette("Set3", 10)
        sns.set_style("whitegrid") # Sets the uniform style as "whitegrid accross the class"
        
        # Defines the list of variables of interest
        self.var_list = ["crisis","inflation"]
        self.loc_list = ["crisis_loc","inflation_loc"]
        self.pct_list = ["crisis_pct","inflation_pct"]
        
        # Sets the chosen figure sizes and fontsizes
        self.size = size
        self.fontsize = fontsize
        
    def allWords(self,data,title = "",xl = "Time",yl = "Wordcount on the page",size=None,
                 fontsize=None,time ="timestamp",language="",location = False, save = True):# Plot all the y variables on the same graph
        """
        Docstring:
        ---------
        Helper plotter function.
        Will plot all of the time series for one language group.
        The plot will serve to compare between words or word locations 
        to see if one word has more mentions overtime than another for instance.
        Parameters:
        -----------
        data : pd.DataFrame()
                Dataframe containing the variables to plot
        title : str
                Title of the time series
        xl : str
                Name of the x axis
        yl : str
                Name of the y axis
        
        show_vandalism : bool
                Whether to plot the data with or without the vandalized datapoints.
                
        size : tuple 
                Size of the graph if different from the one defined in the constructor.
                
        fontsize : int
                Fontsize of the graphs' writing if different from the one defined in the constructor.
                
        time : int
                Time column to plot on (should always be by months, but the user can set it to whatever is required).
                
        language : str
                Language of the plot (serves for the title of each plot and to save the images).
                
        location : bool
                Whether to show the time series of word location instead of word counts.
                
        save : bool
                Whether to save the figure or not.
        Returns:
        --------
        Two time series plots of all the word counts for one language 
        or of all the word locations for one language.
        
        """
        
        # Define the plots' caracteristics
        fig, axs = plt.subplots(figsize = size)
        plt.xlim(data[time].iloc[0], data[time].iloc[-1])
        axs.tick_params(labelsize=fontsize)
        
        plt.title(title+language,fontweight = "bold",fontsize=fontsize, horizontalalignment='center')
        
        
        # If not showing the location, show the number of mentions
        if location == False :
            for i in range(len(self.var_list)):
                sns.lineplot(x = time, y = self.var_list[i], data = data[data["is_vandalized"]==0],)
                plt.xlabel(xlabel = xl, labelpad=10,  fontsize=fontsize, horizontalalignment='center')
                plt.ylabel(ylabel = yl, fontsize=fontsize, horizontalalignment='center')
                #axs.legend()
                plt.legend(labels=self.var_list,loc="upper left",fontsize=fontsize)
            if save == True:
                plt.savefig("All_words{}{}.png".format(self.var_list[i],language))
        
        # Else show the locations instead of the number of mentions
        else :
            axs.invert_yaxis()
            for i in range(len(self.var_list)):
                sns.lineplot(x = time, y = self.loc_list[i], data = data[data["is_vandalized"]==0])
                plt.xlabel(xlabel = xl, labelpad=10,  fontsize=fontsize, horizontalalignment='center')
                plt.ylabel(ylabel = yl, fontsize=fontsize, horizontalalignment='center')
                plt.legend(labels=self.loc_list,loc="upper left",fontsize = fontsize)
            if save == True:
                plt.savefig("All_locs{}{}.png".format(self.var_list[i],language))
            
            
    
    
    def betweenWordComparison(self,data,time, size = None,fontsize = None,language=""):
        """
        Docstring:
        ---------
        
        Plotter function to plot both the word mentions and 
        locations for one language group at the same time.
        Created for convinience to not retype the same line twice.
        
        Parameters:
        -----------
        data : pd.DataFrame()
                Dataframe containing the variables to plot
        
        size : tuple 
                Size of the graph if different from the one defined in the constructor.
                
        fontsize : int
                Fontsize of the graphs' writing if different from the one defined in the constructor.
                
        time : int
                Time column to plot on (should always be by months, but the user can set it to whatever is required).
                
        language : str
                Language of the plot (serves for the title and to save the image).
                
        Returns:
        --------
        The two plots of wordcounts and word locations  for one language group
        one after the other.
        
        """
        # Define size and fontsize if different from the Constructors' default
        
        if size == None and fontsize == None:
            size = self.size
            fontsize = self.fontsize
        else :
            size = size
            fontsize = fontsize
        
        # Plot all the wordcounts
        self.allWords(data,title = "Wordcount",xl = "Time",yl = "Wordcount for the word",
                 size=size,fontsize = fontsize, time =time,language = language)
        
        # Plot all the locations
        self.allWords(data,title = "Location measure",xl = "Time",yl = "Percent difference from page start",
                 size=size,fontsize = fontsize,time =time,language = language, location=True)
        
     
    def interactionWithExteriorData(self,d,variable_pair= [],size = None,fontsize = None, 
                                    show_differences = False,language ="",save = True):#Plot the y variable and its' expected pair on the same graph
        """
        
        Docstring:
        ---------
        
        Helper plotter function.
        
        Will plot the relationship of one word's word count 
        and location with an explanatory variable. ( Petrol price or inflation rate).
        
        Will add to the plot an interaction variable
        (the begining of the hyperinflation in 2018 or 
        the two petrol crisis of 2008 and 2013-2019 respectively ).
        
        Parameters:
        -----------
        d : pd.DataFrame()
                Dataframe containing the variables to plot
        variable_pair : list
                The two variables to plot together, the first is the explained variable, 
                the second is the explanatory variable.
                
                The two most common pairs are ["inflation","logInflationRate"] and ["crise","Petrol_Price"]
        
        size : tuple 
                Size of the graph if different from the one defined in the constructor.
                
        fontsize : int
                Fontsize of the graphs' writing if different from the one defined in the constructor.
          
        show_differences : bool
                Whether to plot the vandalized and the non-vandalized 
                data on the same graph to point out potential differences.
         
        language : str
                Language of the plot (serves for the title and to save the image).
                
        save : bool
                Whether to save the figure or not.
        Returns:
        --------
        Plots the relationship between one word's mentions and locations on one hand 
        and an econometric variable on the other, featuring interactions with a second econometric data.
        
        """
        # Define the plots' characteristics
        fig, axs = plt.subplots(figsize = size)
        axs.tick_params(labelsize=fontsize)
        
        
        # Define the boxes that will show the interaction effect 
        # Hyperinflation dates ( Real inflation over 50% per year)
        hyperinf_bgn = d["Year_month"][np.exp(d["logInflation_Rate"])>50].iloc[0]
        hyperinf_end = d["Year_month"].iloc[-1]

        # Petrol crisis dates ( petrol price below 90$ a baril )
        petrol_crisis_bgn = d["Year_month"][(d["Petrol_Price"]<90)&(d["Year_month"]>datetime.datetime(2008,1,1))].iloc[0]
        petrol_crisis_bgn2 = d["Year_month"][(d["Petrol_Price"]>90)&(d["Year_month"]>datetime.datetime(2014,1,1))].iloc[0]
        petrol_crisis_end = d["Year_month"][(d["Petrol_Price"]>90)&(d["Year_month"]<petrol_crisis_bgn2)].iloc[0]
        petrol_crisis_end2 = d["Year_month"].iloc[-1]
        
        # If the variable is petrol the interaction is the hyperinflation and vice-versa.
        if variable_pair[1] == "Petrol_Price":
            box = "Hyperinflation Period"
            axs.axvspan(hyperinf_bgn, hyperinf_end, color=sns.xkcd_rgb['red'], alpha=0.2)
            color = "black"
        elif variable_pair[1] == "logInflation_Rate":
            box ="Petrol Price under 90$"
            axs.axvspan(petrol_crisis_bgn, petrol_crisis_end,  color=sns.xkcd_rgb['grey'], alpha=0.8)
            axs.axvspan(petrol_crisis_bgn2, petrol_crisis_end2,  color=sns.xkcd_rgb['grey'], alpha=0.8)
            color = "red"
        
        
        # Shows vandalized data or not
        if show_differences == True:
            d_van = d[d["is_vandalized"]==0]
        
        # If asked to show locations, flip the y axis to see "climbing on the page" as going up.
        if variable_pair[0][-3:]=="loc":
            yl = "Percent difference from page start"
            location = " location"
            axs.invert_yaxis()
        else :
            location = ""
            yl = "Wordcount for "+ variable_pair[0] 
        if variable_pair[1] =="Petrol_Price":
            t1 = "Economic crisis"
            t2 =  "petrol price"
        else:
            t1 = "Inflation"+location
            t2 = "inflation rate"
            

        
        title = "Relation between {} and {} in {}".format(t1,t2,language)
        plt.title(title,fontweight = "bold",fontsize=fontsize, horizontalalignment='center')
            
        sns.lineplot(x = d["Year_month"], y = d[variable_pair[0]],ax = axs,alpha=10)
        if show_differences == True:
                
            sns.lineplot(x = d_van["Year_month"], y = d_van[variable_pair[0]],alpha=0.7)
    
        plt.ylabel(ylabel = yl, fontsize=fontsize, horizontalalignment='center')
        plt.xlabel(xlabel = "Time", fontsize=fontsize, horizontalalignment='center')
        if show_differences == True:
            plt.legend(labels=[variable_pair[0]]+[variable_pair[0]+" vandalized"]+[box],loc="upper left", fontsize=fontsize)
        else :
            plt.legend(labels=[variable_pair[0]]+[box],loc="upper left",fontsize=fontsize)
            
        ax2 = axs.twinx()
        ax2.grid(False)
        
        
        sns.lineplot(x = d["Year_month"], y = d[variable_pair[1]],ax = ax2,color = color)
        if variable_pair[1] =="Petrol_Price":
            yl2 = "Petrol Price in $"
        else:
            yl2 = "Inflation rate in log"
        plt.ylabel(ylabel = yl2, fontsize=fontsize, horizontalalignment='center')
        ax2.tick_params(labelsize=fontsize)
        plt.legend(labels=[variable_pair[1]],loc = "center left",fontsize=fontsize)
        
        # Save the plot
        if save == True:
            if show_differences == False:
                plt.savefig('{}.png'.format(variable_pair[0]+"_"+language))
            else :
                plt.savefig('{}.png'.format(variable_pair[0]+"_"+language+"vandalized"))
               
    def interactionCommonPlot(self,data=[], variable_pair = [],size = None,fontsize = None,show_differences = False, language = ["English","Spanish"]): # plot the y variable ( mentions and location ) and its' expected pair
        
        """
        
        Docstring:
        ---------
        
        Plotter function for comparing a word's relations with 
        an explanatory variable in two successive plots
        
        Created for simplicity to not type the same line of code twice.
        
        
        Parameters:
        -----------
        data : list
                list of the two language dataframes
        variable_pair : list
                The two variables to plot together, the first is the explained variable, 
                the second is the explanatory variable.
                
                The two most common pairs are ["inflation","logInflationRate"] and ["crise","Petrol_Price"]
        
        size : tuple 
                Size of the graph if different from the one defined in the constructor.
                
        fontsize : int
                Fontsize of the graphs' writing if different from the one defined in the constructor.
          
        show_differences : bool
                Whether to plot the vandalized and the non-vandalized 
                data on the same graph to point out potential differences.
         
        language : str
                Language of the plot (serves for the title and to save the image).
                
        save : bool
                Whether to save the figure or not.
        Returns:
        --------
        
        Plots two successive plots of a word's mentions or location 
        and an explanatory variable for two different language dataframes.
        
        """
        # Define size and fontsize if different from the Constructors' default
        if size == None and fontsize == None:
            size = self.size
            fontsize = self.fontsize
        else :
            size = size
            fontsize = fontsize
            
        # Interaction plots for language 1 
        self.interactionWithExteriorData(data[1],variable_pair=variable_pair,fontsize = fontsize,size = size,show_differences=show_differences, language =language[0])
        left, right = plt.xlim()
        
        # Interaction plots for language 2 
        self.interactionWithExteriorData(data[0],variable_pair=variable_pair,fontsize = fontsize,size = size,show_differences=show_differences,language=language[1])
        plt.xlim(left, right)
    
    
    def correlationPlots(self,dataframe,language= "English"):
        """
        
        Docstring:
        ---------
        
        Plotter function that shows the heatmap correlation matrix for a language dataframe
        
        
        Parameters:
        -----------
        data : pd.DataFrame()
                Dataframe from which to plot
        
        language : str
                Language of the plot (serves for the title and to save the image).
                
    
        Returns:
        --------
        Plots the heatmap of the correlation matrix
        
        """
        # Define the plot and plot
        fig,a = plt.subplots(figsize = (7,7))
        axs = sns.heatmap(dataframe[["crisis_loc","inflation_loc","crisis","inflation"]].corr(),
            vmin=-1,cmap="coolwarm",annot =True,square=True, cbar=True)
        bottom, top = axs.get_ylim()
        plt.title("Corrplot {}".format(language))
        
        # Save the figure
        plt.savefig("Corrplot_{}.png".format(language))
        
    
    def plotScales(self, dataframe, title = "",yl="", size =None,fontsize = None, grouped="", variable =""):
        
        """
        
        Docstring:
        ---------
        
        Plotter function to illustrate the information loss 
        that occurs when plotting either too narrowly or too broadly.
        
        
        Parameters:
        -----------
        dataframe : pd.DtataFrame()
                Dataframe from which to get the data
        
        size : tuple 
                Size of the graph if different from the one defined in the constructor.
                
        fontsize : int
                Fontsize of the graphs' writing if different from the one defined in the constructor.
          
        grouped : str
                How the data is grouped (either by month or by year).
         
        variable : str
                variable to plot.
                
        Returns:
        --------
        the plot of the data by day (squiggly with too much noise in the data)
        or of the data by year (too smoothed to detect anything else than broad trends).
        """
        # Define size and fontsize if different from the Constructors' default
        if size == None and fontsize == None:
            size = self.size
            fontsize = self.fontsize
        else :
            size = size
            fontsize = fontsize
        
        # Define the plot and plot
        fig, axs = plt.subplots(figsize = size)
        axs.tick_params(labelsize = fontsize)
        plt.xlabel("Time", fontsize = fontsize)
        plt.ylabel(yl, fontsize = fontsize)
        plt.title(title, fontsize = fontsize)
        if grouped == "day":
            sns.lineplot(dataframe["timestamp"],dataframe[variable])
        else :
            sns.lineplot(dataframe["Year"],dataframe[variable])
            
        # Save the plot
        plt.savefig("{}.png".format(title))



        
        
       
