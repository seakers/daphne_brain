

def get_scorecard_objects_and_metrics(scorecard, path_scorecard):
    import os, sys
    import pandas as pd
    import xlrd
    import numpy as np
    from openpyxl import load_workbook
    import xlsxwriter
    import itertools
    import math
    import json

    '''Here we get all lists from all metrics and fields'''
    METRIC_NAMES_BY_SHEET = []
    TYPES_BY_SHEET = []
    UNITS_BY_SHEET = []
    GREATORLESSS_BY_SHEET = []
    POST_RESULTS_BY_SHEET = []
    FLAG_BY_SHEET = []
    OUTOFSPEC_BY_SHEET = []
    DESCRIPT_BY_SHEET = []
    CALC_BY_SHEET = []


    '''Remove all of the fields we dont want'''
    sheets = scorecard.sheet_names
    for sheet in sheets:
        df = pd.read_excel(path_scorecard, sheet_name= sheet)  # get data from sheet
        column_names = list(df.columns)
        metric_col = column_names[1] #metric sheet will be the reference for deleting empty rows or label rows
        length_col = len(df[metric_col]) #original number of rows in the excel sheet

        if sheet == sheets[0]:
            for i in range(length_col):
                if type(df[metric_col][i]) == float:
                    df.drop([i], inplace = True)
                elif (df[metric_col][i]) == 'Metric' or df[metric_col][i] == 'Quick Assessment' \
                        or df[metric_col][i] == 'System Margins' or (df[metric_col][i]) == 'Precision' \
                        or (df[metric_col][i]) == 'EVRs - Out of Spec' or (df[metric_col][i]) == 'Entry - Out of Spec'\
                        or (df[metric_col][i]) == 'Parachute Descent - Out of Spec' \
                        or (df[metric_col][i]) == 'Powered Flight - Out of Spec' \
                        or (df[metric_col][i]) == 'Heatshield Separation Constraints'\
                        or (df[metric_col][i]) == 'Additional Critical Metrics':
                    df.drop([i], inplace = True)
                    DF_SummaryOutofspec = df

            METRIC_NAMES_BY_SHEET.append(list(DF_SummaryOutofspec[column_names[1]]))
            TYPES_BY_SHEET.append(list(DF_SummaryOutofspec[column_names[2]]))
            UNITS_BY_SHEET.append(list(DF_SummaryOutofspec[column_names[3]]))
            POST_RESULTS_BY_SHEET.append(list(DF_SummaryOutofspec[column_names[4]]))
            GREATORLESSS_BY_SHEET.append(list(DF_SummaryOutofspec[column_names[5]]))
            FLAG_BY_SHEET.append(list(DF_SummaryOutofspec[column_names[6]]))
            OUTOFSPEC_BY_SHEET.append(list(DF_SummaryOutofspec[column_names[7]]))
            DESCRIPT_BY_SHEET.append(list(DF_SummaryOutofspec[column_names[8]]))
            CALC_BY_SHEET.append(list(DF_SummaryOutofspec[column_names[9]]))

        if sheet == sheets[1]:
            for i in range(length_col):
                metric_col = column_names[1]
                if type(df[metric_col][i]) == float:
                    df.drop([i], inplace = True)
                elif (df[metric_col][i]) == 'Metric' or df[metric_col][i] == 'Quick Assessment' \
                        or df[metric_col][i] == 'Terrain Interaction Failure Rate' or (df[metric_col][i]) == 'Precision' \
                        or (df[metric_col][i]) == 'EVRs - Out of Spec' or (df[metric_col][i]) == 'System Margins'\
                        or (df[metric_col][i]) == 'Precision':
                    df.drop([i], inplace = True)
                    DF_DecisionMeeting = df

            METRIC_NAMES_BY_SHEET.append(list(DF_DecisionMeeting[column_names[1]]))
            TYPES_BY_SHEET.append(list(DF_DecisionMeeting[column_names[2]]))
            UNITS_BY_SHEET.append(list(DF_DecisionMeeting[column_names[3]]))
            POST_RESULTS_BY_SHEET.append(list(DF_DecisionMeeting[column_names[4]]))
            GREATORLESSS_BY_SHEET.append(list(DF_DecisionMeeting[column_names[5]]))
            FLAG_BY_SHEET.append(list(DF_DecisionMeeting[column_names[6]]))
            OUTOFSPEC_BY_SHEET.append(list(DF_DecisionMeeting[column_names[7]]))
            DESCRIPT_BY_SHEET.append(list(DF_DecisionMeeting[column_names[8]]))
            CALC_BY_SHEET.append(list(DF_DecisionMeeting[column_names[9]]))

        if sheet == sheets[2]:
            for i in range(length_col):
                algo = df[metric_col][i]
                if type(df[metric_col][i]) == float:
                    df.drop([i], inplace = True)
                elif (df[metric_col][i]) == 'Metric':
                    df.drop([i], inplace = True)
                    DF_EDLMETRICS = df

            METRIC_NAMES_BY_SHEET.append(list(DF_EDLMETRICS[column_names[1]]))
            TYPES_BY_SHEET.append(list(DF_EDLMETRICS[column_names[2]]))
            UNITS_BY_SHEET.append(list(DF_EDLMETRICS[column_names[3]]))
            POST_RESULTS_BY_SHEET.append(list(DF_EDLMETRICS[column_names[4]]))
            GREATORLESSS_BY_SHEET.append(list(DF_EDLMETRICS[column_names[5]]))
            FLAG_BY_SHEET.append(list(DF_EDLMETRICS[column_names[6]]))
            OUTOFSPEC_BY_SHEET.append(list(DF_EDLMETRICS[column_names[7]]))
            DESCRIPT_BY_SHEET.append(list(DF_EDLMETRICS[column_names[9]]))
            CALC_BY_SHEET.append(list(DF_EDLMETRICS[column_names[10]]))

        if sheet == sheets[3]:
            for i in range(length_col):
                if type(df[metric_col][i]) == float:
                    df.drop([i], inplace = True)
                elif (df[metric_col][i]) == 'Metric' or df[metric_col][i] == 'Terrain Relative Navigation' \
                        or df[metric_col][i] == 'TRN Error Budget' \
                        or (df[metric_col][i]) == 'Landing Performance':
                    df.drop([i], inplace = True)
                DF_TRN = df

            METRIC_NAMES_BY_SHEET.append(list(DF_TRN[column_names[1]]))
            TYPES_BY_SHEET.append(list(DF_TRN[column_names[2]]))
            UNITS_BY_SHEET.append(list(DF_TRN[column_names[3]]))
            POST_RESULTS_BY_SHEET.append(list(DF_TRN[column_names[4]]))
            GREATORLESSS_BY_SHEET.append(list(DF_TRN[column_names[5]]))
            FLAG_BY_SHEET.append(list(DF_TRN[column_names[6]]))
            OUTOFSPEC_BY_SHEET.append(list(DF_TRN[column_names[7]]))
            CALC_BY_SHEET.append(list(DF_TRN[column_names[9]]))
            DESCRIPT_BY_SHEET.append(list(DF_TRN[column_names[8]]))

        if sheet == sheets[4]:
            for i in range(length_col):
                if type(df[metric_col][i]) == float:
                    df.drop([i], inplace=True)
                elif (df[metric_col][i]) == 'Metric' or df[metric_col][i] == 'Rover Mass Properties' \
                        or (df[metric_col][i]) == 'Precision' or (df[metric_col][i]) == 'PDV Dynamic State (1%-tile)' \
                        or (df[metric_col][i]) == 'PDV Dynamic State (99%-tile)' \
                        or (df[metric_col][i]) == 'Close Clearances (mm)' \
                        or (df[metric_col][i]) == 'Close Clearances (in)' \
                        or (df[metric_col][i]) == 'Margined Loads (N), LUF = 1.2':
                    df.drop([i], inplace=True)
                    DF_BUDMETRICS = df

            calculation7 = list(DF_BUDMETRICS[column_names[8]])
            n = len(calculation7)
            description7 = [0] * n

            METRIC_NAMES_BY_SHEET.append(list(DF_BUDMETRICS[column_names[1]]))
            TYPES_BY_SHEET.append(list(DF_BUDMETRICS[column_names[2]]))
            UNITS_BY_SHEET.append(list(DF_BUDMETRICS[column_names[3]]))
            POST_RESULTS_BY_SHEET.append(list(DF_BUDMETRICS[column_names[4]]))
            GREATORLESSS_BY_SHEET.append(list(DF_BUDMETRICS[column_names[5]]))
            FLAG_BY_SHEET.append(list(DF_BUDMETRICS[column_names[6]]))
            OUTOFSPEC_BY_SHEET.append(list(DF_BUDMETRICS[column_names[7]]))
            CALC_BY_SHEET.append(list(DF_BUDMETRICS[column_names[8]]))
            DESCRIPT_BY_SHEET.append(description7)


        if sheet == sheets[5]:
            for i in range(length_col):
                if type(df[metric_col][i]) == float:
                    df.drop([i], inplace = True)
                elif (df[metric_col][i]) == 'Metric' or df[metric_col][i] == 'Entry Environments' \
                        or (df[metric_col][i]) == 'Entry Guidance' or (df[metric_col][i]) == 'Entry Control':
                    df.drop([i], inplace = True)
                    DF_Entry = df

            metrics3 = list(DF_Entry[column_names[1]])
            types3 = list(DF_Entry[column_names[2]])
            units3 = list(DF_Entry[column_names[3]])
            post_results3 = list(DF_Entry[column_names[4]])
            great_or_less3 = list(DF_Entry[column_names[5]])
            flags3 = list(DF_Entry[column_names[6]])
            out_of_spec3 = list(DF_Entry[column_names[7]])
            description3 = list(DF_Entry[column_names[8]])
            calculation3 = list(DF_Entry[column_names[9]])


            METRIC_NAMES_BY_SHEET.append(metrics3)
            TYPES_BY_SHEET.append(types3)
            UNITS_BY_SHEET.append(units3)
            POST_RESULTS_BY_SHEET.append(post_results3)
            GREATORLESSS_BY_SHEET.append(great_or_less3)
            FLAG_BY_SHEET.append(flags3)
            OUTOFSPEC_BY_SHEET.append(out_of_spec3)
            CALC_BY_SHEET.append(calculation3)
            DESCRIPT_BY_SHEET.append(description3)

        if sheet == sheets[6]:
            for i in range(length_col):
                if type(df[metric_col][i]) == float:
                    df.drop([i], inplace = True)
                elif (df[metric_col][i]) == 'Metric' or df[metric_col][i] == 'Parachute Deployment Conditions' \
                        or (df[metric_col][i]) == 'Parachute Opening Load Indicators (New)' \
                        or (df[metric_col][i]) == 'Pre-HSS' or df[metric_col][i] == 'Heatshield Separation Conditions'\
                        or df[metric_col][i] == 'Post-HSS' or df[metric_col][i] == 'Backshell Separation Conditions':
                    df.drop([i], inplace = True)
                    DF_ParachuteDescent = df

            metrics4 = list(DF_ParachuteDescent[column_names[1]])
            types4 = list(DF_ParachuteDescent[column_names[2]])
            units4 = list(DF_ParachuteDescent[column_names[3]])
            post_results4 = list(DF_ParachuteDescent[column_names[4]])
            great_or_less4 = list(DF_ParachuteDescent[column_names[5]])
            flags4 = list(DF_ParachuteDescent[column_names[6]])
            out_of_spec4 = list(DF_ParachuteDescent[column_names[7]])
            description4 = list(DF_ParachuteDescent[column_names[8]])
            calculation4 = list(DF_ParachuteDescent[column_names[9]])

            METRIC_NAMES_BY_SHEET.append(metrics4)
            TYPES_BY_SHEET.append(types4)
            UNITS_BY_SHEET.append(units4)
            POST_RESULTS_BY_SHEET.append(post_results4)
            GREATORLESSS_BY_SHEET.append(great_or_less4)
            FLAG_BY_SHEET.append(flags4)
            OUTOFSPEC_BY_SHEET.append(out_of_spec4)
            CALC_BY_SHEET.append(calculation4)
            DESCRIPT_BY_SHEET.append(description4)

        if sheet == sheets[7]:
            for i in range(length_col):
                metric_col = column_names[2]
                if type(df[metric_col][i]) == float:
                    df.drop([i], inplace = True)
                elif (df[metric_col][i]) == 'Metric' or df[metric_col][i] == 'Backshell Sep' \
                        or (df[metric_col][i]) == 'Powered Approach' or (df[metric_col][i]) == 'Constant Velocity' \
                        or df[metric_col][i] == 'Constant Decel' or df[metric_col][i] == 'Throttle Down' \
                        or df[metric_col][i] == 'Rover Separation' or df[metric_col][i] == 'Touchdown' \
                        or df[metric_col][i] == 'Flyaway':
                    df.drop([i], inplace = True)
                    DF_Powereddesent = df

            METRIC_NAMES_BY_SHEET.append(list(DF_Powereddesent[column_names[2]]))
            TYPES_BY_SHEET.append(list(DF_Powereddesent[column_names[3]]))
            UNITS_BY_SHEET.append(list(DF_Powereddesent[column_names[4]]))
            POST_RESULTS_BY_SHEET.append(list(DF_Powereddesent[column_names[5]]))
            GREATORLESSS_BY_SHEET.append(list(DF_Powereddesent[column_names[6]]))
            FLAG_BY_SHEET.append(list(DF_Powereddesent[column_names[7]]))
            OUTOFSPEC_BY_SHEET.append(list(DF_Powereddesent[column_names[8]]))
            CALC_BY_SHEET.append(list(DF_Powereddesent[column_names[10]]))
            DESCRIPT_BY_SHEET.append(list(DF_Powereddesent[column_names[9]]))


        if sheet == sheets[8]:
            for i in range(length_col):
                if type(df[metric_col][i]) == float:
                    df.drop([i], inplace=True)
                elif (df[metric_col][i]) == 'Metric' or df[metric_col][i] == 'EVRs - Out of Spec' \
                        or (df[metric_col][i]) == 'Precision' or (df[metric_col][i]) == 'Timeline Margins':
                    df.drop([i], inplace=True)
                    DF_TIMELINE = df

            METRIC_NAMES_BY_SHEET.append(list(DF_TIMELINE[column_names[1]]))
            TYPES_BY_SHEET.append(list(DF_TIMELINE[column_names[2]]))
            UNITS_BY_SHEET.append(list(DF_TIMELINE[column_names[3]]))
            POST_RESULTS_BY_SHEET.append(list(DF_TIMELINE[column_names[4]]))
            GREATORLESSS_BY_SHEET.append(list(DF_TIMELINE[column_names[5]]))
            FLAG_BY_SHEET.append(list(DF_TIMELINE[column_names[6]]))
            OUTOFSPEC_BY_SHEET.append(list(DF_TIMELINE[column_names[7]]))
            CALC_BY_SHEET.append(list(DF_TIMELINE[column_names[9]]))
            DESCRIPT_BY_SHEET.append(list(DF_TIMELINE[column_names[8]]))

        if sheet == sheets[9]:
            for i in range(length_col):
                if type(df[metric_col][i]) == float:
                    df.drop([i], inplace=True)
                elif (df[metric_col][i]) == 'Metric' or df[metric_col][i] == 'EDLCOMM MFSK Tones (R9.4)':
                    df.drop([i], inplace=True)
                    DF_COMM = df

            METRIC_NAMES_BY_SHEET.append(list(DF_COMM[column_names[1]]))
            TYPES_BY_SHEET.append(list(DF_COMM[column_names[2]]))
            UNITS_BY_SHEET.append(list(DF_COMM[column_names[3]]))
            POST_RESULTS_BY_SHEET.append(list(DF_COMM[column_names[4]]))
            GREATORLESSS_BY_SHEET.append(list(DF_COMM[column_names[5]]))
            FLAG_BY_SHEET.append(list(DF_COMM[column_names[6]]))
            OUTOFSPEC_BY_SHEET.append(list(DF_COMM[column_names[7]]))
            CALC_BY_SHEET.append(list(DF_COMM[column_names[9]]))
            DESCRIPT_BY_SHEET.append(list(DF_COMM[column_names[8]]))

        if sheet == sheets[10]:
            for i in range(length_col):
                metric_col = column_names[2]
                if type(df[metric_col][i]) == float and df[column_names[3]][i] != str('50%-tile') \
                        and df[column_names[3]][i] != str('99%-tile'):
                    df.drop([i], inplace=True)
                elif (df[metric_col][i]) == 'Metric' or df[metric_col][i] == 'Received Power' \
                        or df[metric_col][i] == 'Received Power Watermarks' or df[metric_col][i] == 'Orbiter Tracking to MSL' \
                        or df[metric_col][i] == 'Event Times Relative to Nominal Entry Interface Time (time = 540 s)':
                    df.drop([i], inplace=True)
                DF_TELECOM = df

            METRIC_NAMES_BY_SHEET.append(list(DF_TELECOM[column_names[2]]))
            TYPES_BY_SHEET.append(list(DF_TELECOM[column_names[3]]))
            UNITS_BY_SHEET.append(list(DF_TELECOM[column_names[4]]))
            POST_RESULTS_BY_SHEET.append(list(DF_TELECOM[column_names[5]]))
            GREATORLESSS_BY_SHEET.append(list(DF_TELECOM[column_names[6]]))
            FLAG_BY_SHEET.append(list(DF_TELECOM[column_names[7]]))
            OUTOFSPEC_BY_SHEET.append(list(DF_TELECOM[column_names[8]]))
            CALC_BY_SHEET.append(list(DF_TELECOM[column_names[10]]))
            DESCRIPT_BY_SHEET.append(list(DF_TELECOM[column_names[9]]))

        if sheet == sheets[11]:
            for i in range(length_col):
                metric_col = column_names[2]
                if type(df[metric_col][i]) == float and df[column_names[5]][i] != str('Scalar'):
                    df.drop([i], inplace=True)
                elif (df[metric_col][i]) == 'ID':
                    df.drop([i], inplace=True)
                DF_EFC = df

            METRIC_NAMES_BY_SHEET.append(list(DF_EFC[column_names[4]]))
            TYPES_BY_SHEET.append(list(DF_EFC[column_names[5]]))
            UNITS_BY_SHEET.append(list(DF_EFC[column_names[6]]))
            POST_RESULTS_BY_SHEET.append(list(DF_EFC[column_names[7]]))
            GREATORLESSS_BY_SHEET.append(list(DF_EFC[column_names[8]]))
            FLAG_BY_SHEET.append(list(DF_EFC[column_names[9]]))
            OUTOFSPEC_BY_SHEET.append(list(DF_EFC[column_names[10]]))
            CALC_BY_SHEET.append(list(DF_EFC[column_names[12]]))
            DESCRIPT_BY_SHEET.append(list(DF_EFC[column_names[11]]))


        if sheet == sheets[12]:
            for i in range(length_col):
                metric_col = column_names[3]
                if type(df[metric_col][i]) == float:
                    df.drop([i], inplace=True)
                elif (df[metric_col][i]) == 'Metric' or df[metric_col][i] == 'Monte Carlo' \
                        or df[metric_col][i] == 'Landing Accuracy' or df[metric_col][i] == 'Touchdown Conditions' \
                        or df[metric_col][i] == 'Propellant Consumption' or df[metric_col][i] == 'Timeline Margin' \
                        or df[metric_col][i] == 'Aeroheating' or df[metric_col][i] == 'Loads' \
                        or df[metric_col][i] == 'Heatshield Separation Constraints':
                    df.drop([i], inplace=True)
                DF_Summary = df

            METRIC_NAMES_BY_SHEET.append(list(DF_Summary[column_names[3]]))
            TYPES_BY_SHEET.append(list(DF_Summary[column_names[8]]))
            UNITS_BY_SHEET.append(list(DF_Summary[column_names[6]]))
            POST_RESULTS_BY_SHEET.append(list(DF_Summary[column_names[7]]))
            GREATORLESSS_BY_SHEET.append(list(DF_Summary[column_names[4]]))
            n = DF_Summary.shape[0]
            FLAG_BY_SHEET.append(list([str('nan')]*n))
            OUTOFSPEC_BY_SHEET.append(list(DF_Summary[column_names[5]]))
            CALC_BY_SHEET.append(list(DF_Summary[column_names[9]]))
            DESCRIPT_BY_SHEET.append(list([str('nan')]*n))

        if sheet == sheets[13]:
            for i in range(length_col):
                metric_col = column_names[3]
                if type(df[metric_col][i]) == float and df[column_names[5]][i] != str('Scalar'):
                    df.drop([i], inplace=True)
                elif (df[metric_col][i]) == 'Metric' or df[metric_col][i] == 'Failure Mechanism':
                    df.drop([i], inplace=True)
                DF_Failure = df

            METRIC_NAMES_BY_SHEET.append(list(DF_Failure[column_names[3]]))
            TYPES_BY_SHEET.append(list(DF_Failure[column_names[5]]))
            n = DF_Failure.shape[0]
            UNITS_BY_SHEET.append(list([str('nan')]*n))
            POST_RESULTS_BY_SHEET.append(list(DF_Failure[column_names[4]]))
            GREATORLESSS_BY_SHEET.append(list([str('nan')]*n))
            FLAG_BY_SHEET.append(list([str('nan')]*n))
            OUTOFSPEC_BY_SHEET.append(list([str('nan')]*n))
            CALC_BY_SHEET.append(list(DF_Failure[column_names[6]]))
            DESCRIPT_BY_SHEET.append(list(DF_Failure[column_names[7]]))

        if sheet == sheets[14]:
            for i in range(length_col):
                metric_col = column_names[3]
                if type(df[metric_col][i]) == float:
                    df.drop([i], inplace=True)
                elif (df[metric_col][i]) == 'Metric' or df[metric_col][i] == 'Landing Accuracy' \
                        or df[metric_col][i] == 'Touchdown Conditions' or df[metric_col][i] == 'Propellant Consumption' \
                        or df[metric_col][i] == 'Timeline' or df[metric_col][i] == 'EDL Comm ' \
                        or df[metric_col][i] == 'Aeroheating' or df[metric_col][i] == 'Entry Loads (Does not include PD)' \
                        or df[metric_col][i] == 'Parachute Deploy Constraints' \
                        or df[metric_col][i] == 'Heatshield Separation Constraints' \
                        or df[metric_col][i] == 'Radar Constraints' or df[metric_col][i] == 'Rover Wind Loading' \
                        or df[metric_col][i] == 'Long Term Recontact' or df[metric_col][i] == 'Downrange Distance for MARDI' \
                        or df[metric_col][i] == 'Backshell Separation Conditions' or df[metric_col][i] == 'Accordion Values' \
                        or df[metric_col][i] == 'Rover Separation Conditions' or df[metric_col][i] == 'Sky Crane Dynamics' \
                        or df[metric_col][i] == 'Flyaway Start State ':
                    df.drop([i], inplace=True)
                DF_Detailed = df

            METRIC_NAMES_BY_SHEET.append(list(DF_Detailed[column_names[3]]))
            TYPES_BY_SHEET.append(list(DF_Detailed[column_names[9]]))
            UNITS_BY_SHEET.append(list(DF_Detailed[column_names[7]]))
            POST_RESULTS_BY_SHEET.append(list(DF_Detailed[column_names[8]]))
            GREATORLESSS_BY_SHEET.append(list(DF_Detailed[column_names[4]]))
            FLAG_BY_SHEET.append(list(DF_Detailed[column_names[6]]))
            OUTOFSPEC_BY_SHEET.append(list(DF_Detailed[column_names[5]]))
            CALC_BY_SHEET.append(list(DF_Detailed[column_names[10]]))
            n = DF_Detailed.shape[0]
            DESCRIPT_BY_SHEET.append(list([str('nan')]*n))

    '''Create objects and classes'''
    class ScoreCardCategory(object):
        def __init__(self, name = 0,  entries = 0):
            self.name = name# these are the tab names (categories)
            self.entries= entries# These are all the metrics in each
        def __call__(self, name, entries):
            print(name)
            print(entries)

    # A = edl_metric.name #How we call class objects
    # B = edl_metric.entries

    class ScoreCardMetrics(object):
        def __init__(self, name = 0, type = 0 , units=0, POST_results = 0, GreatOrLess = 0, Flag = 0, OutOfSpec = 0, Enum = 0,
                     Description = 0, Calculation = 0, CalculationCheckedBy = 0, MetricCheckedBy = 0, FlagOutOfSpecOwner = 0):
            self.name = name
            self.type = type
            self.units = units
            self.POST_results = POST_results
            self.GreatOrLess = GreatOrLess
            self.Flag = Flag
            self.OutOfSpec = OutOfSpec
            self.Enum = Enum
            self.Description = Description
            self.Calculation = Calculation
            self.CalculationCheckedBy = CalculationCheckedBy
            self.MetricCheckedBy = MetricCheckedBy
            self.FlagOutOfSpecOwner = FlagOutOfSpecOwner
        def __call__(self, name, type, units, POST_results, GreatOrLess, Flag, OutOfSpec, Enum,
                     Description, Calculation, CalculationCheckedBy, MetricCheckedBy, FlagOutOfSpecOwner):
            print(name)
            print(type)
            print(units)
            print(POST_results)
            print(GreatOrLess)
            print(Flag)
            print(OutOfSpec)
            print(Enum)
            print(Description)
            print(Calculation)
            print(CalculationCheckedBy)
            print(MetricCheckedBy)
            print(FlagOutOfSpecOwner)


    METRIC_OBJECTS = []
    METRIC_OBJECTS_GROUPED = []

    for j in range(len(METRIC_NAMES_BY_SHEET)): # number of columns (number of excel sheets)
        METRIC_OBJECTS = []
        for i in range(len(METRIC_NAMES_BY_SHEET[j])): # number of metrics in each sheet
            METRIC_OBJECTS.append(ScoreCardMetrics(name = METRIC_NAMES_BY_SHEET[j][i], type=TYPES_BY_SHEET[j][i],
                                                     units=UNITS_BY_SHEET[j][i], POST_results=POST_RESULTS_BY_SHEET[j][i],
                                                     GreatOrLess=GREATORLESSS_BY_SHEET[j][i], Flag=FLAG_BY_SHEET[j][i],
                                                     OutOfSpec=OUTOFSPEC_BY_SHEET[j][i], Enum=0,
                                                     Description=DESCRIPT_BY_SHEET[j][i],
                                                     Calculation=CALC_BY_SHEET[j][i], CalculationCheckedBy=0,
                                                     MetricCheckedBy=0, FlagOutOfSpecOwner=0))
            METRIC_OBJECTS = list(METRIC_OBJECTS)
        METRIC_OBJECTS_GROUPED.append(METRIC_OBJECTS)


    '''Make single list of all of the metric objects'''
    METRIC_OBJECTS = [item for items in METRIC_OBJECTS_GROUPED for item in items]
    '''Make a list of all of the POST results'''
    print(METRIC_OBJECTS[:])

    summaryOutofspec_objects = METRIC_OBJECTS_GROUPED[0]
    decisionmeeting_objects = METRIC_OBJECTS_GROUPED[1]
    edl_metric_objects = METRIC_OBJECTS_GROUPED[2]
    trn_objects = METRIC_OBJECTS_GROUPED[3]
    bud_metrics_objects = METRIC_OBJECTS_GROUPED[4]
    entry_objects = METRIC_OBJECTS_GROUPED[5]
    parachute_descent_objects = METRIC_OBJECTS_GROUPED[6]
    powered_flight_objects = METRIC_OBJECTS_GROUPED[7]
    timeline_objects = METRIC_OBJECTS_GROUPED[8]
    comm_objects = METRIC_OBJECTS_GROUPED[9]
    telecom_objects = METRIC_OBJECTS_GROUPED[10]
    efc_objects = METRIC_OBJECTS_GROUPED[11]
    summary_objects = METRIC_OBJECTS_GROUPED[12]
    failures_objects = METRIC_OBJECTS_GROUPED[13]
    detailed_objects = METRIC_OBJECTS_GROUPED[14]

    '''Here we have the list of metrics for the entry, parachute descent, powered descent, TRN and BUD metrics from the scorecard'''
    list_of_metrics = [item for items in METRIC_NAMES_BY_SHEET for item in items]
    '''Save the list of metrics to excel'''

    '''
    import csv
    df = pd.DataFrame(list_of_metrics)
    listofmetrics = pd.ExcelWriter("list_of_metrics_complete.xlsx", engine='xlsxwriter')
    df.to_excel(listofmetrics,'Sheet 1')
    listofmetrics.save()
    '''


    '''After modifications, get the new list of metrics '''

    df = pd.read_excel('/Users/ssantini/Code/ExtractDataMatlab/ExtractScorecardData/list_of_metrics_complete_ver2.xlsx')  # get data from sheet
    col_name = list(df.columns)
    list_of_metrics = list(df[0])

    summary_outofspec = ScoreCardCategory(scorecard.sheet_names[0],  summaryOutofspec_objects)
    decision_meeting = ScoreCardCategory(scorecard.sheet_names[1],  decisionmeeting_objects)
    edl_metric = ScoreCardCategory(scorecard.sheet_names[2], edl_metric_objects)
    trn= ScoreCardCategory(scorecard.sheet_names[3], trn_objects)
    bud_metrics = ScoreCardCategory(scorecard.sheet_names[4], bud_metrics_objects)
    entry = ScoreCardCategory(scorecard.sheet_names[5], entry_objects)
    parachute_descent= ScoreCardCategory(scorecard.sheet_names[6], parachute_descent_objects)
    powered_flight = ScoreCardCategory(scorecard.sheet_names[7], powered_flight_objects)
    edltimeline = ScoreCardCategory(scorecard.sheet_names[8], timeline_objects)
    comms = ScoreCardCategory(scorecard.sheet_names[9], comm_objects)
    telecom = ScoreCardCategory(scorecard.sheet_names[10], telecom_objects)
    efc = ScoreCardCategory(scorecard.sheet_names[11], efc_objects)
    summary = ScoreCardCategory(scorecard.sheet_names[12], summary_objects)
    failure = ScoreCardCategory(scorecard.sheet_names[13], failures_objects)
    detailed = ScoreCardCategory(scorecard.sheet_names[14], detailed_objects)

    return (summary_outofspec, decision_meeting, edl_metric, trn, bud_metrics, entry, parachute_descent, powered_flight,
        edltimeline, comms, telecom, efc, summary, failure, detailed, list_of_metrics)
#
#
# [summary_outofspec, decision_meeting, edl_metric, trn, bud_metrics, entry, parachute_descent, powered_flight,
#         edltimeline, comms, telecom, efc, summary, failure, detailed, list_of_metrics] = get_scorecard_objects_and_metrics(scorecard, path_scorecard)
#
# print(get_scorecard_objects_and_metrics.get_scorecard_objects_and_metrics())
# i = 1