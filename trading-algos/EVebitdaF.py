#backtest note: No momentum
import pandas as pd
import numpy as np
import datetime
import math

def initialize(context):
    

    
#### Variables to change for your own liking #################
    #the constant for portfolio turnover rate
    context.holding_months = 1
    #number of stocks to pass through the fundamental screener
    context.num_screener = 10
    #number of stocks in portfolio at any time
    context.num_stock = 10
    #number of days to "look back" if employing momentum. ie formation
    context.formation_days = 200
    #set False if you want the highest momentum, True if you want low
    context.lowmom = False
    #################################################################
    #month counter for holding period logic.
    context.month_count = context.holding_months
    
    # Rebalance monthly on the first day of the month at market open
    schedule_function(rebalance,
                      date_rule=date_rules.month_start(),
                      time_rule=time_rules.market_open())
    
def rebalance(context, data):
    ############temp code #####################
    '''spy = symbol('SPY')
    if data[spy].price < data[spy].mavg(120):
        for stock in context.portfolio.positions:
            order_target(stock, 0)
        order_target_percent(symbol('TLT'), 1)
        context.month_count += 1
        print "moving towards TLT"
        return'''
    
    
    ####################################
    #This condition block is to skip every "holding_months"
    if context.month_count >= context.holding_months:
        context.month_count = 1
    else:
        context.month_count += 1
        return
    
    chosen_df = calc_return(context)
    
    if context.num_stock < context.num_screener:
        chosen_df = sort_return(chosen_df, context.lowmom)
    
    chosen_df = chosen_df.iloc[:,:(context.num_stock-1)]
    
    # Create weights for each stock
    weight = 0.95/len(chosen_df.columns)
    # Exit all positions before starting new ones
    for stock in context.portfolio.positions:
        if stock not in chosen_df:
            order_target(stock, 0)
           
    # Rebalance all stocks to target weights
    for stock in chosen_df:
        if weight != 0 and stock in data:
            order_target_percent(stock, weight)
    
def sort_return(df, lowmom):
    '''a cheap and quick way to sort columns according to index value. Sorts by descending order. Ie higher returns are first'''
    df = df.T
    df = df.sort(columns='return', ascending = lowmom)
    df = df.T
    
    return df
    
def calc_return(context):
    price_history = history(bar_count=context.formation_days, frequency="1d", field='price')
    
    temp = context.fundamental_df.copy()
    
    for s in temp:
        now = price_history[s].ix[-20]
        old = price_history[s].ix[0]
        pct_change = (now - old) / old
        if np.isnan(pct_change):
            temp = temp.drop(s,1)
        else:
            temp.loc['return', s] = pct_change#calculate percent change
        
    return temp
    

def before_trading_start(context): 
    """
      Called before the start of each trading day. 
      It updates our universe with the
      securities and values found from fetch_fundamentals.
    """
    #this code prevents query every day
    if context.month_count != context.holding_months:
        return
    
    fundamental_df = get_fundamentals(
        query(
            # put your query in here by typing "fundamentals."
            fundamentals.valuation_ratios.ev_to_ebitda,
 fundamentals.asset_classification.morningstar_sector_code, fundamentals.valuation.enterprise_value, fundamentals.income_statement.ebit, fundamentals.income_statement.ebitda
        )
        .filter(fundamentals.valuation.market_cap > 2e9)
        .filter(fundamentals.valuation_ratios.ev_to_ebitda > 0)
        .filter(fundamentals.valuation.enterprise_value > 0)
        .filter(fundamentals.asset_classification.morningstar_sector_code != 103)
        .filter(fundamentals.asset_classification.morningstar_sector_code != 207)
        .filter(fundamentals.valuation.shares_outstanding != None)
        .order_by(fundamentals.valuation_ratios.ev_to_ebitda.asc())
        .limit(context.num_screener)
    )

    # Filter out only stocks that fits in criteria
    context.stocks = [stock for stock in fundamental_df]
    # Update context.fundamental_df with the securities that we need
    context.fundamental_df = fundamental_df[context.stocks]
    
    update_universe(context.fundamental_df.columns.values)

    
def create_weights(context, stocks):
    """
        Takes in a list of securities and weights them all equally 
    """
    if len(stocks) == 0:
        return 0 
    else:
        # Buy only 0.9 of portfolio value to avoid borrowing
        weight = .99/len(stocks)
        return weight
    
    #if the code gets to here, it means that there has been an error. I don't want my code to continue if there is a bull market and my screener doesn't have enough stocks that pass this filter
#def mom_filter(context, data):

def print_ev_ebitda(df):
    fmean = df.mean(axis=1)
    print fmean.loc['ev_to_ebitda']
    
def handle_data(context, data):
    """
      Code logic to run during the trading day.
      handle_data() gets called every bar.
    """
    pass