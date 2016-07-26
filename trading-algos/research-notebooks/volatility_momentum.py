# https://www.quantopian.com/posts/javols-just-another-volatility-strategy-dot-dot-dot

# for pipeline
from quantopian.pipeline import Pipeline
from quantopian.algorithm import attach_pipeline, pipeline_output
from quantopian.pipeline.factors import CustomFactor
from quantopian.pipeline.data.quandl import cboe_vix, cboe_vxv
import scipy as sp
import scipy.stats as stats
from scipy  import  polyfit, polyval, signal
import datetime
import pytz
import pandas as pd
import numpy as np
import re
from pandas import DataFrame,Series
from zipline.utils.tradingcalendar import get_early_closes
from zipline.utils import tradingcalendar
from datetime import timedelta
import operator
from functools import partial




fst = lambda tup: tup[0]
snd = lambda tup: tup[1]


def initialize(context):
       # Define the instruments in the portfolio:
    context.sidsLongVol  = {sid(38054): +1.0}
    context.sidsShortVol = {sid(40516): +1.0}
    context.sidsShortSPY = {sid(22887): +1.0}
    context.sidsLongSPY  = {sid(8554): +1.0}

    context.spy = symbol('SPY')
    context.hedge = symbol('IWM')
    context.vxx = symbol('VXX')
    context.epsilon = .01
    context.ivts=[]
    context.ivts_medianfiltered = []

    pipe = Pipeline()
    attach_pipeline(pipe, 'vix_pipeline')  
    pipe.add(GetVol(inputs=[cboe_vix.vix_close]), 'vix')
    pipe.add(GetVol(inputs=[cboe_vxv.close]), 'vxv')
    

    vxstUrl = 'http://www.cboe.com/publish/scheduledtask/mktdata/datahouse/vxstcurrent.csv'
    vx1Url = 'http://www.quandl.com/api/v1/datasets/CHRIS/CBOE_VX1.csv'
    vx2Url = 'http://www.quandl.com/api/v1/datasets/CHRIS/CBOE_VX2.csv'

    fetch_csv(vxstUrl, symbol='VXST', skiprows=3,date_column='Date', pre_func=addFieldsVXST)
    fetch_csv(vx1Url, date_column='Trade Date',date_format='%Y-%m-%d', symbol='v1', post_func=rename_col)
    fetch_csv(vx2Url, date_column='Trade Date',date_format='%Y-%m-%d', symbol='v2', post_func=rename_col)

    # Calculating the contango ratio of the front and second month VIX Futures settlements
    
    context.threshold = 0.90   #contango ratio threshold
    
    schedule_function(ordering_logic,date_rule=date_rules.every_day(),time_rule=time_rules.market_open(hours=0, minutes=1))
     # Rebalance every day, 1 hour after market open.

    context.wait_trigger=False
    
    context.vixpipe = None
    
    start_date = context.spy.security_start_date
    end_date   = context.spy.security_end_date
    context.algo_hist={}
    context.returns_df = pd.DataFrame()
 
    # Get the dates when the market closes early:
    context.early_closes = get_early_closes(start_date, end_date).date
    context.slopes = Series()
    context.betas = Series()
 


def ordering_logic(context, data):
    vxst = data.current('VXST','price')
    vx1  = data.current('v1','Settle')
    vx2  = data.current('v2','Settle')
    
    vix = context.vixpipe.loc[symbol('VXX')]['vix']
    vxv = context.vixpipe.loc[symbol('VXX')]['vxv']
    
    diff = vxst-vxv  # http://vixandmore.blogspot.com.au/2013/10/the-new-vxst-and-vxstvix-ratio.html
    slope9 = (vix/vxst)
    slope = (vxv/vix)
    slope12 = (vx2/vx1)
 
    ivts = (vix/vxst)
    context.ivts.append(ivts)
 
    last_ratio = data.current('v1','Settle')/data.current('v2','Settle')

    ivts_medianfiltered = sp.signal.medfilt(context.ivts,5)[-1] #http://www.godotfinance.com/ HeroRats
    context.ivts_medianfiltered.append(ivts)

    if ivts_medianfiltered ==0.0: ivts_medianfiltered3=1.0  
    ivts_median = ivts_medianfiltered
    
    record(Implied_vol_strct_med_5 = ivts_median)
    record(Implied_vol_strct_med_5_avg = np.mean(context.ivts_medianfiltered[-90:] ))    
    record(slope9=slope9*100 -100)    
    record(slope12=slope12*100 -100) 
    record(vix_val=vix)
       
    context.slopes = context.slopes.append(Series(slope9,index=[ pd.Timestamp(get_datetime()).tz_convert('US/Eastern')]))
    
    # median filters and avg determine SPY or TLT position
    if ivts_median < (np.mean(context.ivts_medianfiltered[-22:]) -0.01):
        rebalance(context.sidsLongSPY , data, 0.49) 
        rebalance(context.sidsShortSPY, data, 0.0) 
    elif ivts_median > (np.mean(context.ivts_medianfiltered[-22:]) +0.01):
        rebalance(context.sidsLongSPY, data, 0.0) 
        rebalance(context.sidsShortSPY, data, 0.49) 
        
    #sometimes you need to wait to things start changing     
    if context.wait_trigger and last_ratio < context.threshold:
        return
    else:
        context.wait_trigger = False
    
    #XIV and VXX thresholds 
    if slope12 <= 0:
        rebalance(context.sidsLongVol, data, 0.49) 
        rebalance(context.sidsShortVol, data, 0) 
        context.wait_trigger = False
    elif last_ratio < context.threshold or vix > 27:
        rebalance(context.sidsLongVol, data, 0) 
        rebalance(context.sidsShortVol, data, 0.49) 
        context.wait_trigger = True
    else:    
       rebalance(context.sidsLongVol, data, 0.0) 
       rebalance(context.sidsShortVol, data, 0.0) 
       context.wait_trigger = False
        
        
        

def rebalance(sids,data,factor):    
    for sid in sids:
        if data.can_trade(sid): 
            order_target_percent(sid, sids[sid]*factor) 
            log.info('ordering '+ sid.symbol + ' ' + \
                     str( round(sids[sid]*factor*100,0))+'%')
            
    
    

def estimateBeta(priceY,priceX,algo = 'standard'):
    '''
    estimate stock Y vs stock X beta using iterative linear
    regression. Outliers outside 3 sigma boundary are filtered out

    Parameters
    --------
    priceX : price series of x (usually market)
    priceY : price series of y (estimate beta of this price)

    Returns
    --------
    beta : stockY beta relative to stock X
    '''

    X = pd.DataFrame({'x':priceX,'y':priceY})

    if algo=='returns':
        ret = (X/X.shift(1)-1).dropna().values
      
        x = ret[:,0]
        y = ret[:,1]
        
        # filter high values
        low = np.percentile(x,20)
        high = np.percentile(x,80)
        iValid = (x>low) & (x<high)
        
        x = x[iValid]
        y = y[iValid]
        
        iteration = 1
        nrOutliers = 1
        while iteration < 10 and nrOutliers > 0 :
            (a,b) = polyfit(x,y,1)
            yf = polyval([a,b],x)
            #plot(x,y,'x',x,yf,'r-')
            err = yf-y
            idxOutlier = abs(err) > 3*np.std(err)
            nrOutliers =sum(idxOutlier)
            beta = a
            #print 'Iteration: %i beta: %.2f outliers: %i' % (iteration,beta, nrOutliers)
            x = x[~idxOutlier]
            y = y[~idxOutlier]
            iteration += 1
    elif algo=='log':
        x = np.log(X['x'])
        y = np.log(X['y'])
        (a,b) = polyfit(x,y,1)
        beta = a
    elif algo=='standard':
        ret =np.log(X).diff().dropna()
        beta = ret['x'].cov(ret['y'])/ret['x'].var()
    else:
        raise TypeError("unknown Beta algorithm type, use 'standard', 'log' or 'returns'")

    return beta
    

# for pipeline
class GetVol(CustomFactor):    
    window_length = 1    
    def compute(self, today, assets, out, vol):
        out[:] = vol

def before_trading_start(context, data):
    output = pipeline_output('vix_pipeline')
    output = output.dropna()    
    context.vixpipe = output

def addFieldsVXST(df):
    df=reformat_quandl(df,'Close')
    return df

# Post Function for fetch_csv where futures data from Quandl is standardized
def rename_col(df):
    df = df.rename(columns={'Close': 'price','Trade Date': 'Date'})
    df = df.fillna(method='ffill')
    df = df[['price', 'Settle','sid']]
    # Shifting data by one day to avoid forward-looking bias
    return df.shift(1)
    


def reformat_quandl(df,closeField):
    df = df.rename(columns={closeField:'price'})
    if get_environment('arena') == 'backtest': 
        dates = df.Date.apply(lambda dt: pd.Timestamp(re.sub('\*','',dt), tz='US/Eastern'))
        df['Date'] = dates.apply(next_trading_day)
    return df
            
def next_trading_day(dt):
    tdays = tradingcalendar.trading_days
    normalized_dt = tradingcalendar.canonicalize_datetime(dt)
    idx = tdays.searchsorted(normalized_dt)
    return tdays[idx + 1]
