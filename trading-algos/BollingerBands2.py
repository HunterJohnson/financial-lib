# This algorithm uses the talib Bollinger Bands function to determine entry entry 
# points for long and short positions.

# When the the price breaks out of the upper Bollinger band, a short position
# is opened. A long position is opened when the price dips below the lower band.

# Because this algorithm uses the history function, it will only run in minute mode. 
# We will constrain the trading to once per day at market open in this example.

import talib
import numpy as np
import pandas as pd

# Setup our variables
def initialize(context):
    context.stock = symbol('SPY')
    
    # Create a variable to track the date change
    context.date = None

def handle_data(context, data):
    todays_date = get_datetime().date()
    
    # Do nothing unless the date has changed
    if todays_date == context.date:
        return
    # Set the new date
    context.date = todays_date

    current_position = context.portfolio.positions[context.stock].amount
    price=data[context.stock].price
    
    # Load historical data for the stocks
    prices = history(15, '1d', 'price')
    
    upper, middle, lower = talib.BBANDS(
        prices[context.stock], 
        timeperiod=10,
        # number of non-biased standard deviations from the mean
        nbdevup=2,
        nbdevdn=2,
        # Moving average type: simple moving average here
        matype=0)
    
    if price <= lower[-1] and current_position <= 0:
        order_target_percent(context.stock, 1.0)
        
    elif price >= upper[-1] and current_position >= 0:
        order_target_percent(context.stock, -1.0)
        
    record(upper=upper[-1],
           lower=lower[-1],
           mean=middle[-1],
           price=price,
           position_size=current_position)
   
    
