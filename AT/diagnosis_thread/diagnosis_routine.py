import time


def diagnosis_routine(ad_to_diag, diag_to_hub):

    keep_alive = True
    while keep_alive:
        if not ad_to_diag.empty():
            signal = ad_to_diag.get()
            if signal['type'] == 'stop':
                keep_alive = False
            elif signal['type'] == 'anomaly_list':
                # To prevent the diagnosis thread from falling behind the telemetry feed, empty the queue and
                # only process the last received window
                if ad_to_diag.empty():
                    anomaly_list = signal['content']
                    diag_to_hub.put({'type': 'diagnosed_anomalies', 'content': anomaly_list})
        time.sleep(0.1)

    print('Diagnosis thread stopped.')
    return None