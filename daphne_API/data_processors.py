import dateparser
import datetime

def not_processed(extracted_data, options, context):
    return extracted_data


def process_mission(extracted_data, options, context):
    return extracted_data[1:]


def process_date(extracted_data, options, context):
    date_parsing_settings = {}
    if options == "begin":
        date_parsing_settings = {'RELATIVE_BASE': datetime.datetime(2020, 1, 1)}
    elif options == "end":
        date_parsing_settings = {'RELATIVE_BASE': datetime.datetime(2020, 12, 31)}
    return dateparser.parse(extracted_data, settings=date_parsing_settings)
