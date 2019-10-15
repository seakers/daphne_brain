import hashlib
import pandas as pd

from django.conf import settings
from .functions import ma_preprocess
from .functions import find_pdq
from statsmodels.tsa.statespace.sarimax import SARIMAX

from channels.generic.websocket import JsonWebsocketConsumer


class SARIMAX_AD(JsonWebsocketConsumer):
    ##### WebSocket event handlers
    def connect(self):
        """
        Called when the websocket is handshaking as part of initial connection.
        """
        # Accept the connection
        self.accept()

    def receive_json(self, content, **kwargs):
        """
        Called when we get a text frame. Channels will JSON-decode the payload
        for us and pass it as the first argument.
        """

        if 'data' in content:
            data = pd.read_json(content['data'], orient='records').set_index('timestamp')
        else:
            # Loads The data
            data = pd.read_csv('AT/Data/sample_2.csv',
                               parse_dates=True,
                               index_col='timestamp')

        # Defines the confidence interval accepted
        ci_alpha = 0.01
        if 'ci_alpha' in content:
            if 0 < content['ci_alpha'] < 1:
                ci_alpha = content['ci_alpha']
            else:
                self.send_json({"error": "ci_alpha must be in range (0,1)"})

        # Selects the variable we focus the anomaly detection on
        if 'variable' in content:
            if content['variable'] in data.columns:
                var_chosen = content['variable']
            else:
                self.send_json({"error": "Variable Name not Found"})
        else:
            var_chosen = data.columns[0]

        # Preprocess the data with a Moving Average
        if 'preprocess' in content and content['preprocess']: # TODO: Move this to an outer backend python script
            one_var = ma_preprocess(data[var_chosen], 4).rename(columns={0: var_chosen})
        else:
            one_var = data[var_chosen]

        # Defines seasonality parameter
        seasonality = 0
        if 'seasonality' in content:
            if content['seasonality'] > 0 and isinstance(content['seasonality'], int):
                seasonality = content['seasonality']
            else:
                self.send_json({"error": "seasonality must be an intger and > 0"})

        # Defines the minimum correlation to determine if a variable is used as exogenous
        min_cor = 1
        if 'min_cor' in content:
            if 0 <= content['min_cor'] <= 1:
                min_cor = content['min_cor']
            else:
                self.send_json({"error": "min_cor must be in range[0,1]"})

        # Defines the maximum p q parameters considered in order to fit the SARIMAX model
        range_pq = 3
        if 'range_pq' in content:
            if content['range_pq'] > 0 and isinstance(content['range_pq'], int):
                range_pq = content['range_pq']
            else:
                self.send_json({"error": "range_pq must be integer and > 0"})

        # Chooses the exogenous variables used to fit the model (based on the correlations of the variables)
        correl = abs(data.corr()[var_chosen]).sort_values(ascending=False)
        correl_var = correl[correl > min_cor][1:].index

        # Chooses the best parameters to fit SARIMAX model and defines it
        [p, d, q] = find_pdq(one_var, range_pq=range_pq)
        [P, D, Q] = [0, 0, 0]
        if seasonality != 0:
            [P, D, Q] = find_pdq(one_var.diff(seasonality).dropna(), range_pq=range_pq)

        if len(correl_var) > 0:
            model = SARIMAX(endog=one_var,
                            exog=data.drop(columns=var_chosen)[correl_var],
                            order=(p, d, q),
                            seasonal_order=(P, D, Q, seasonality),
                            enforce_stationarity=False,
                            enforce_invertibility=False)
        else:
            model = SARIMAX(endog=one_var,
                            order=(p, d, q),
                            seasonal_order=(P, D, Q, seasonality),
                            enforce_stationarity=False,
                            enforce_invertibility=False)

        # fit SARIMAX model
        results = model.fit(maxiter=20)

        # Predicts the variable values and the confidence intervals
        pred = results.get_prediction(start=seasonality * D + p + q, dynamic=False)
        pred_ci = pred.conf_int(alpha=ci_alpha)

        # Creates a data Frame to plot the results
        results = pd.DataFrame(one_var)
        results = pd.concat([results, pred_ci], axis=1)
        results['Flag_Anomaly'] = (results[var_chosen] > results['upper ' + var_chosen]) | \
                                  (results[var_chosen] < results['lower ' + var_chosen])
        results['timestamp'] = results.index

        self.send_json(results[results.Flag_Anomaly][['timestamp', var_chosen]].to_json(date_format='iso', orient='records'))
