from rest_framework.views import APIView
from rest_framework.response import Response
import pandas as pd
from statsmodels.tsa.statespace.sarimax import SARIMAX

from .functions import find_pdq


class AD_SARIMA(APIView):
    """
    Performs SARIMA-Based anomaly detection
    """
    
    def post(self, request, format=None):

        # Defines the confidence interval accepted
        ci_alpha = 0.01 
        if 'ci_alpha' in request.data:
            if 0 < request.data['ci_alpha'] < 1:
                ci_alpha = request.data['ci_alpha']
            else:
                return Response({"error": "ci_alpha must be in range (0,1)"})

        # Loads The data
        data = pd.read_csv('anomaly_API/Data/sample.csv',
                           parse_dates=True,
                           index_col='timestamp')

        # Selects the variable we focus the anomaly detection on
        if 'variable' in request.data:
            if request.data['variable'] in data.columns:
                var_chosen = request.data['variable']
            else:
                return Response({"error": "Variable Name not Found"})
        else:
            var_chosen = data.columns[0]

        # Preprocess the data with a Moving Average
        if 'preprocess' in request.data and request.data['preprocess']:
            one_var = ma_preprocess(data[var_chosen], 4).rename(columns={0: var_chosen})
        else:
            one_var = data[var_chosen]

        # Defines seasonality parameter
        seasonality = 0
        if 'seasonality' in request.data:
            if request.data['seasonality'] > 0 and isinstance(request.data['seasonality'], int):
                seasonality = request.data['seasonality']
            else:
                return Response({"error": "seasonality must be an intger and > 0"})
        
        # Defines the minimum correlation to determine if a variable is used as exogenous
        min_cor = 1
        if 'min_cor' in request.data:
            if 0 <= request.data['min_cor'] <= 1:
                min_cor = request.data['min_cor'] 
            else:
                return Response({"error": "min_cor must be in range[0,1]"})

        # Defines the maximum p q parameters considered in order to fit the SARIMAX model
        range_pq = 3
        if 'range_pq' in request.data:
            if request.data['range_pq'] > 0 and isinstance(request.data['range_pq'], int):
                range_pq = request.data['range_pq']
            else:
                return Response({"error": "range_pq must be integer and > 0"})

        # Chooses the exogenous variables used to fit the model (based on the correlations of the variables)
        correl = abs(data.corr()[var_chosen]).sort_values(ascending=False)
        correl_var = correl[correl > min_cor][1:].index

        # Chooses the best parameters to fit SARIMAX model and defines it
        [p, d, q] = find_pdq(one_var, range_pq=range_pq)
        [P, D, Q] = [0, 0, 0]
        if seasonality != 0:
            [P, D, Q] = find_pdq(one_var.diff(seasonality).dropna(), range_pq=range_pq)


        model = SARIMAX(endog=one_var,
                        # exog=data.drop(columns=var_chosen)[correl_var],
                        order=(p, d, q),
                        seasonal_order=(P, D, Q, seasonality),
                        enforce_stationarity=False,
                        enforce_invertibility=False)

        # fit SARIMAX model
        results = model.fit(maxiter=200)

        # Predicts the variable values and the confidence intervals
        pred = results.get_prediction(start=seasonality*D + p + q, dynamic=False)
        pred_ci = pred.conf_int(alpha=ci_alpha)

        # Creates a data Frame to plot the results
        results = pd.DataFrame(one_var)
        results = pd.concat([results, pred_ci], axis=1)
        results['Flag_Anomaly'] = (results[var_chosen] > results['upper ' + var_chosen]) | \
                                  (results[var_chosen] < results['lower ' + var_chosen])

        return Response(results[results.Flag_Anomaly][var_chosen].to_json(date_format='iso'))
