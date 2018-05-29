import numpy as np
import pandas as pd
import itertools
import warnings

from statsmodels.tsa.stattools import adfuller
from statsmodels.tsa.arima_model import ARMA


def ma_preprocess(data, window):
    l = len(data)
    Z = np.zeros(l)
    for x in range(l):
        Z[x] = np.mean(data[max(0, x - window // 2):min(l - 1, x + window // 2):])
    MA = pd.DataFrame(Z).set_index(data.index)
    return MA

def pq_arima(data, range_pq):
    """
    Defines the p q parameters of the ARMA model
    """
    
    # Define the p, q possible parameter combinations
    p = q = range(0, range_pq)
    pq = list(itertools.product(p, q))

    warnings.filterwarnings("ignore") # specify to ignore warning messages
    
    # Chooses the adequate parameters attending to the AIC

    aic = -1
    c_param = (0, 0)
    for param in pq:
        try:
            mod = ARMA(data,
                       order=param)
            res = mod.fit(disp=False)
            if aic == -1 or aic > res.aic:
                # print('ARMA{} - AIC:{} - BIC:{}'.format(param, res.aic, res.bic))
                aic = res.aic
                c_param = param
        except:
            continue

    return c_param


def find_pdq(data, d_lim=2, range_pq=3):
    # Data must be a time series
    res = adfuller(data)
    is_stationary = res[1] < 0.01  # Checks stationarity for the first time
    d = 0
    # Differenciates until stationarity
    while not is_stationary and d < d_lim:
        data = data.diff().dropna()
        res = adfuller(data)
        is_stationary = res[1] < 0.01
        d += 1
    [p, q] = pq_arima(data, range_pq)
    return [p, d, q]

