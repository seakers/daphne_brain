import dateparser
import datetime

from dialogue.param_processing_helpers import not_processed


def process_mission(extracted_data, options, context):
    return extracted_data[1:]


def process_design(extracted_data, options, context):
    if isinstance(extracted_data, str):
        return int(extracted_data[1:])
    else:
        return extracted_data


def process_date(extracted_data, options, context):
    date_parsing_settings = {}
    if options == "begin":
        date_parsing_settings = {'RELATIVE_BASE': datetime.datetime(2020, 1, 1)}
    elif options == "end":
        date_parsing_settings = {'RELATIVE_BASE': datetime.datetime(2020, 12, 31)}
    return dateparser.parse(extracted_data, settings=date_parsing_settings)


process_function = {}
process_function["mission"] = process_mission
process_function["measurement"] = not_processed
process_function["technology"] = not_processed
process_function["space_agency"] = process_mission
process_function["year"] = process_date
process_function["design_id"] = process_design
process_function["agent"] = not_processed
process_function["instrument_parameter"] = not_processed
process_function["vassar_instrument"] = not_processed
process_function["vassar_measurement"] = not_processed
process_function["vassar_stakeholder"] = not_processed
process_function["objective"] = not_processed
process_function["subobjective"] = not_processed
