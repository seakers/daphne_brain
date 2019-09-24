import pandas as pd

def extract_telemetry_feed(processed_question, number_of_features, context):
    filename = 'C:/Users/oscar/Desktop/SEAK LAB/Telemetry feed/telemetry_feed.csv'
    telemetry_feed = pd.read_csv(filename)
    return [telemetry_feed]

def extract_telemetry_feed_thresholds(processed_question, number_of_features, context):
    filename = 'C:/Users/oscar/Desktop/SEAK LAB/Telemetry feed/telemetry_feed_thresholds.csv'
    telemetry_feed_thresholds = pd.read_csv(filename)
    return [telemetry_feed_thresholds]

extract_function = {}
extract_function["telemetry_feed"] = extract_telemetry_feed
extract_function["telemetry_feed_thresholds"] = extract_telemetry_feed_thresholds
