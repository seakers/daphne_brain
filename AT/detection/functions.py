import numpy as np
import pandas as pd
import itertools
import warnings
import matplotlib.pyplot as plt
from statsmodels.tsa.seasonal import seasonal_decompose
import os
import statsmodels.api as sm
from pandas.tseries.offsets import DateOffset
from statsmodels.tsa.stattools import adfuller

data = pd.read_csv(os.path.join('data', 'data.csv'))
data.head()

data.index = pd.to_datetime(data['Month'])
data.drop(columns='Month', inplace=True)
data.head()

data.isna().sum()

data.plot()
decompose_data = seasonal_decompose(data, model="additive")
decompose_data.plot()

seasonality = decompose_data.seasonal
seasonality.plot(color='green')

dftest = adfuller(data.Sales, autolag='AIC')
print("1. ADF : ", dftest[0])
print("2. P-Value : ", dftest[1])
print("3. Num Of Lags : ", dftest[2])
print("4. Num Of Observations Used For ADF Regression and Critical Values Calculation :", dftest[3])
print("5. Critical Values :")
for key, val in dftest[4].items():
    print("\t", key, ": ", val)

rolling_mean = data.rolling(window=12).mean()
data['rolling_mean_diff'] = rolling_mean - rolling_mean.shift()
ax1 = plt.subplot()
data['rolling_mean_diff'].plot(title='after rolling mean & differencing');
ax2 = plt.subplot()
data.plot(title='original')

dftest = adfuller(data['rolling_mean_diff'].dropna(), autolag='AIC')
print("1. ADF : ", dftest[0])
print("2. P-Value : ", dftest[1])
print("3. Num Of Lags : ", dftest[2])
print("4. Num Of Observations Used For ADF Regression and Critical Values Calculation :", dftest[3])
print("5. Critical Values :")
for key, val in dftest[4].items():
    print("\t", key, ": ", val)

model = sm.tsa.statespace.SARIMAX(data['Sales'], order=(1, 1, 1), seasonal_order=(1, 1, 1, 12))
results = model.fit()

data['forecast'] = results.predict(start=90, end=103, dynamic=True)
data[['Sales', 'forecast']].plot(figsize=(12, 8))

pred_date = [data.index[-1] + DateOffset(months=x) for x in range(0, 24)]

pred_date = pd.DataFrame(index=pred_date[1:], columns=data.columns)
pred_date

data = pd.concat([data, pred_date])

data['forecast'] = results.predict(start=104, end=120, dynamic=True)
data[['Sales', 'forecast']].plot(figsize=(12, 8))

plt.plot([1, 2, 3])
plt.show()

#
# def ma_preprocess(data, window):
#     l = len(data)
#     Z = np.zeros(l)
#     for x in range(l):
#         Z[x] = np.mean(data[max(0, x - window // 2):min(l - 1, x + window // 2):])
#     MA = pd.DataFrame(Z).set_index(data.index)
#     return MA
#
#
# def pq_arima(data, range_pq):
#     """
#     Defines the p q parameters of the ARMA model
#     """
#
#     # Define the p, q possible parameter combinations
#     p = q = range(0, range_pq)
#     pq = list(itertools.product(p, q))
#
#     warnings.filterwarnings("ignore")  # specify to ignore warning messages
#
#     # Chooses the adequate parameters attending to the AIC
#
#     aic = -1
#     c_param = (0, 0)
#     for param in pq:
#         try:
#             mod = ARMA(data,
#                        order=param)
#             res = mod.fit(disp=False)
#             if aic == -1 or aic > res.aic:
#                 # print('ARMA{} - AIC:{} - BIC:{}'.format(param, res.aic, res.bic))
#                 aic = res.aic
#                 c_param = param
#         except:
#             continue
#
#     return c_param
#
#
# def find_pdq(data, d_lim=2, range_pq=3):
#     # Data must be a time series
#     res = adfuller(data)
#     is_stationary = res[1] < 0.01  # Checks stationarity for the first time
#     d = 0
#     # Differenciates until stationarity
#     while not is_stationary and d < d_lim:
#         data = data.diff().dropna()
#         res = adfuller(data)
#         is_stationary = res[1] < 0.01
#         d += 1
#     [p, q] = pq_arima(data, range_pq)
#     return [p, d, q]
