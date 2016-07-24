import math
import numpy as np
import datetime
import pandas as pd
from pytz import timezone
from sklearn.decomposition import PCA
from zipline.utils import tradingcalendar as calendar
import statsmodels.api as sm

class LogReturnSeries:
    def __init__(self, t, n):
        self.T = t
        self.N = n
        self.reset()
        
    def reset(self):
        self.counter = 0
        self.log_returns = np.zeros((self.T, self.N))
        self.last_prices = []

    def add_prices(self, prices):
        if len(self.last_prices) == 0:
            self.last_prices = prices
            return
        else:
            log_prices = []
            for ii in range(0, len(prices)):
                log_prices.append(math.log(prices[ii] * 1.0 / self.last_prices[ii]))
            self.last_prices = prices

            if self.counter < self.T:
                self.log_returns[self.counter, :] = log_prices
            else:
                self.log_returns = np.delete(self.log_returns, 0, axis=0)
                self.log_returns = np.vstack((self.log_returns, log_prices))
            self.counter += 1

    def get_series(self):
        if self.counter <= self.T:
            return None
        else:
            return np.copy(self.log_returns)


class Regime:
    def __init__(self):
        pass

    MOMENTUM = 1
    MEAN_REVERSION = 2
    NONE = 0


class Strategy:
    def __init__(self, stocks, t, r, e):
        self.T = t
        self.N = stocks
        self.H = r
        self.K = e
        self.log_returns = LogReturnSeries(t, stocks)
        
    def reset(self):
        self.log_returns.reset()
    

    def compute_betas_by_ols(self, series, d):
        fittedvalues= np.zeros((self.T, self.N))
        residuals = np.zeros((self.T, self.N))
        for ii in range(0, self.N):
            f, r = self.compute_betas_by_ols_stock(d, series[:,ii])
            fittedvalues[:, ii] = f
            residuals[:, ii] = r
        return fittedvalues, residuals

    def compute_betas_by_ols_stock(self, Dm, Fm):
        Dm = sm.add_constant(Dm)
        ols = sm.OLS(Fm, Dm).fit()
        return ols.fittedvalues, ols.resid
        #return ret
        

    def add_prices(self, prices):
        self.log_returns.add_prices(prices)
        ret = self.log_returns.get_series()

        if ret is None:
            return None, None
        m = ret.mean(axis=0)
        y = ret - np.tile(m, (self.T, 1))
        s = ret.std(axis=0)
        for ii in range(0, self.N):
            if s[ii] == 0:
                s[ii] = 1
        y = y / s
        pca = PCA(self.K)
        d = pca.fit_transform(y)
        
        fittedvalues, residuals = self.compute_betas_by_ols(ret, d)
        residualsum = np.copy(residuals)
        runningsum = np.zeros((self.N, 1))
        
        for ii in range(0, self.T):
            for jj in range(0, self.N):
                runningsum[jj, 0] += residuals[ii,jj]
                residualsum[ii,jj] = runningsum[jj, 0]
        
       
        b,a, bse = self.fitOU(residualsum, residuals)
        
        m = []
        vol = []
        
        for ii in range(0, self.N):
            m.append(a[ii] / (1 - b[ii]))
            vol.append(bse[ii]/math.pow(1 - math.pow(b[ii], 2), 0.5))
            
        return (residuals[self.T-1, :] - m)/vol, residualsum[self.T-1, :]
    
    def fitOU(self, X, Y):
        beta = []
        alpha = []
        vol = []
        for ii in range(0, self.N):
            a = X[0:self.T-1, ii]            
            a = sm.add_constant(a)
            ols = sm.OLS(Y[1:self.T, ii], a).fit()
            params = ols.params
            beta.append(params[1])
            alpha.append(params[0])
            vol.append(np.std(ols.resid))
        
        return beta, alpha, vol
    
def initialize(context):
    context.sids =  [sid(2),
                     sid(24),
                     sid(20088),
                     sid(16841),
                     sid(3766),
                     sid(26169),
                     sid(24832),
                     sid(1582),
                     sid(4922),
                     sid(23112),
                     sid(5328),
                     sid(698),
                     sid(8347),
                     sid(4151),
                     sid(5938),
                     sid(6928),
                     sid(23328),
                     sid(3806),
                     sid(6583),
                     sid(8229),
                     sid(4283),
                     sid(21090),
                     sid(3735),
                     #sid(3166),
                     sid(17436),
                     sid(25006),
                     sid(754),
                     sid(3695),
                     sid(5029),
                     sid(114)]
    context.strategy = Strategy(29,60,1,2)   
    context.counter = 0
    context.prevvol = 0
    
    set_slippage(slippage.FixedSlippage(spread = 0.00))
    set_commission(commission.PerShare(0.01))

def handle_data(context, data):
   
    prices = []
    
    for sid in context.sids:
        prices.append(data[sid].price)
        
    ou, er = context.strategy.add_prices(prices)
    if ou is None:
        return
    
    er = np.array(er)
    er = er.ravel()
    
    ou = np.array(ou)
    ou = ou.ravel()
        
    idx = 0
    for sid in context.sids:
        trade_meanreversion(sid, context, ou, er, idx, data)
        idx += 1
        
def trade_meanreversion(sid, context, ou, er, idx, data):

    if ou[idx] < -2 and context.portfolio.positions[sid].amount >= 0:
        order_target_value(sid, 3000)
    elif ou[idx] > 2 and context.portfolio.positions[sid].amount <= 0:
        order_target_value(sid, -3000)
    elif abs(ou[idx]) < 0.25:
        order_target(sid, 0)
    