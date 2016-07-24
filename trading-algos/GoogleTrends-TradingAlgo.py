# Hunter Johnson 07/2016
""" 
this algorithm trades the S&P 500 using Google Trends data
the indicator is a moving average (5 week window) of a term related to negative market sentiment
"""
import numpy as np
import datetime
# Average over 5 weeks, free parameter.
delta_t = 5

# _____GOOD QUERIES_____

# Query      | ETF/Equity | Return 01/2005 - Present (Benchmark 90.4%)

# Election   |  S&P500    | 95.8% 
# Debt       |  S&P500    | 185.7%
# Recession  |  S&P500    | 116.9%
# Bankruptcy |  S&P500    | 99.2%
# Foreclosure

# Try

# Political / Economic terms .... Equities / Sector correlations 

def initialize(context):
    # This is the search query we are using, this is tied to the csv file.
    context.query = 'value'
    # User fetcher to get data. I uploaded this csv file manually, feel free to use.
    # Note that this data is already weekly averages.
    fetch_csv('https://gist.githubusercontent.com/HunterJohnson/acb02d0c47678998de52/raw/7e10e87a3cafdbaecf61479694a5f30051f53fa1/Apple%20Products',
              date_format='%Y-%m-%d',
              symbol='value',
              )
    
    context.order_size = 10000
    context.sec_id = 24
    context.security = sid(24)  # Security

def handle_data(context, data):
    c = context
  
    if c.query not in data[c.query]:
        return
   
    # Extract weekly average of search query.
    indicator = data[c.query][c.query]
    
    # Buy and hold strategy that enters on the first day of the week
    # and exits after one week.
    if data[c.security].dt.weekday() == 0: # Monday
        # Compute average over weeks in range [t-delta_t-1, t[
        mean_indicator = mean_past_queries(data, c.query)
        if mean_indicator is None:
            return

        # Exit positions
        amount = c.portfolio['positions'][c.sec_id].amount
        order(c.security, -amount)

        # Long or short depending on whether search term frequency
        # went down or up, respectively.
        if indicator > mean_indicator:
            order(c.security, -c.order_size) 
        else:
            order(c.security, c.order_size) 
        
# If we want the average over 5 weeks, we'll have to use a 6
# week window as the newest element will be the current event.
@batch_transform(window_length=delta_t+1, refresh_period=0)
def mean_past_queries(data, query):
    # Compute mean over all events except most current one.
    return data[query][query][:-1].mean()


