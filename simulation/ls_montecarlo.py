# Longstaff-Schwartz least squares monte carlo simulation, for parallel valuation of American options
# from Python For Finance by Yves Hilpisch

import numpy as np

def optionValue(S0, vol, T, K=40, M=50, I=4096, r=0.06):
    np.random.seed(150000)  # fix the seed for every valuation
    dt = T / M  # time interval
    df = np.exp(-r * dt)  # discount factor per time time interval
    # Simulation of Index Levels
    S = np.zeros((M + 1, I), dtype=np.float64)  # stock price matrix
    S[0, :] = S0  # intial values for stock price
    for t in range(1, M + 1):
        ran = np.random.standard_normal(I / 2)
        ran = np.concatenate((ran, -ran))  # antithetic variates
        ran = ran - np.mean(ran)  # correct first moment
        ran = ran / np.std(ran)  # correct second moment
        S[t, :] = S[t - 1, :] * np.exp((r - vol ** 2 / 2) * dt
                        + vol * ran * np.sqrt(dt))
    h = np.maximum(K - S, 0)  # inner values for put option
    V = np.zeros_like(h)  # value matrix
    V[-1] = h[-1]
    # Valuation by LSM
    for t in range(M - 1, 0, -1):
        rg = np.polyfit(S[t, :], V[t + 1, :] * df, 5)  # regression
        C = np.polyval(rg, S[t, :])  # evaluation of regression
        V[t, :] = np.where(h[t, :] > C, h[t, :],
                         V[t + 1, :] * df)  # exercise decision/optimization
    V0 = np.sum(V[1, :] * df) / I  # LSM estimator
    print "S0 %4.1f|vol %4.2f|T %2.1f| Option Value %8.3f" % (S0, vol, T, V0)
    return V0
