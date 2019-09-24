def process_telemetry_feed(telemetry_feed, options, context):
    return telemetry_feed

def process_telemetry_feed_thresholds(telemetry_feed_thresholds, options, context):
    return telemetry_feed_thresholds

process_function = {}
process_function["telemetry_feed"] = process_telemetry_feed
process_function["telemetry_feed_thresholds"] = process_telemetry_feed_thresholds