def find_last_anomaly(data):
    tf_data = data['telemetry_feed']
    tf_thresholds = data['telemetry_feed_thresholds']
    variables = tf_data.head()

    return