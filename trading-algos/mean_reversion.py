"""
This is a sample mean-reversion algorithm on Quantopian for you to test and adapt.
This example uses pipeline to set its universe daily.

Algorithm investment thesis: 
Top-performing securities from last week will do worse this week, and vice-versa.

Every Monday, we rank high dollar-volume securities based on their previous 5 day returns. 
We long the bottom 10% of securities with the WORST returns over the past 5 days.
We short the top 10% of securities with the BEST returns over the past 5 days.


This type of algorithm may be used in live trading and in the Quantopian Open.
"""

# Import the libraries we will use here
from quantopian.algorithm import attach_pipeline, pipeline_output
from quantopian.pipeline import Pipeline
from quantopian.pipeline.data.builtin import USEquityPricing
from quantopian.pipeline.factors import AverageDollarVolume, Returns

def initialize(context):
    """
    The initialize function is the place to create your pipeline (security selector),
    and set trading conditions such as commission and slippage. It is called once
    at the start of the simulation and also where context variables can be set.
    """
    
    # Define context variables that can be accessed in other methods of
    # the algorithm.
    context.long_leverage = 0.5
    context.short_leverage = -0.5
    context.returns_lookback = 5
           
    # Rebalance on the first trading day of each week at 11AM.
    schedule_function(rebalance, 
                      date_rules.week_start(days_offset=0),
                      time_rules.market_open(hours = 1, minutes = 30))
    
    # Record tracking variables at the end of each day.
    schedule_function(record_vars,
                      date_rules.every_day(),
                      time_rules.market_close(minutes=1))
    
    # Create and attach our pipeline (dynamic security selector), defined below.
    attach_pipeline(make_pipeline(context), 'mean_reversion_example')
        
def make_pipeline(context):
    """
    A function to create our pipeline (dynamic security selector). The pipeline is used
    to rank securities based on different factors, including builtin facotrs, or custom 
    factors that you can define. Documentation on pipeline can be found here:
        https://www.quantopian.com/help#pipeline-title
    """
    
    # Create a pipeline object. 
    pipe = Pipeline()
    
    # Create a dollar_volume factor using default inputs and window_length.
    # This is a builtin factor.
    dollar_volume = AverageDollarVolume(window_length=1)
    pipe.add(dollar_volume, 'dollar_volume')
    
    # Create a recent_returns factor with a 5-day returns lookback. This is
    # a custom factor defined below (see RecentReturns class).
    recent_returns = Returns(window_length=context.returns_lookback)
    pipe.add(recent_returns, 'recent_returns')
    
    # Define high dollar-volume filter to be the top 5% of securities by dollar volume.
    high_dollar_volume = dollar_volume.percentile_between(95, 100)
    
    # Define high and low returns filters to be the bottom 10% and top 10% of
    # securities in the high dollar-volume group.
    low_returns = recent_returns.percentile_between(0,10,mask=high_dollar_volume)
    high_returns = recent_returns.percentile_between(90,100,mask=high_dollar_volume)
    
    # Factors return a scalar value for each security in the entire universe
    # of securities. Here, we add the recent_returns rank factor to our pipeline
    # and we provide it with a mask such that securities that do not pass the mask
    # (i.e. do not have high dollar-volume), are not considered in the ranking.
    pipe.add(recent_returns.rank(mask=high_dollar_volume), 'recent_returns_rank')
    
    # Add a filter to the pipeline such that only high-return and low-return
    # securities are kept.
    pipe.set_screen(low_returns | high_returns)
    
    # Add the low_returns and high_returns filters as columns to the pipeline so
    # that when we refer to securities remaining in our pipeline later, we know
    # which ones belong to which category.
    pipe.add(low_returns, 'low_returns')
    pipe.add(high_returns, 'high_returns')
    
    return pipe

def before_trading_start(context, data):
    """
    Called every day before market open. This is where we get the securities
    that made it through the pipeline.
    """
    
    # Pipeline_output returns a pandas DataFrame with the results of our factors
    # and filters.
    context.output = pipeline_output('mean_reversion_example')
    
    # Sets the list of securities we want to long as the securities with a 'True'
    # value in the low_returns column.
    context.long_secs = context.output[context.output['low_returns']]
    
    # Sets the list of securities we want to short as the securities with a 'True'
    # value in the high_returns column.
    context.short_secs = context.output[context.output['high_returns']]
    
    # Keep a list reference and a set reference to all of our pipeline securities
    # (set has much faster lookup)
    context.security_list = context.long_secs.index.union(context.short_secs.index).tolist()
    context.security_set = set(context.security_list)

def assign_weights(context):
    """
    Assign weights to ou long and short target positions.
    """
    
    # Set the allocations to even weights for each long position, and even weights
    # for each short position.
    context.long_weight = context.long_leverage / len(context.long_secs)
    context.short_weight = context.short_leverage / len(context.short_secs)
    
def rebalance(context,data):
    """
    This rebalancing function is called according to our schedule_function settings.  
    """
    
    assign_weights(context)
    
    # For each security in our universe, order long or short positions according
    # to our context.long_secs and context.short_secs lists.
    for security in context.security_list:
        if security in context.long_secs.index:
            order_target_percent(security, context.long_weight)
        elif security in context.short_secs.index:
            order_target_percent(security, context.short_weight)
     
    # Sell all previously held positions not in our new context.security_list.
    for security in context.portfolio.positions:
        if security not in context.security_set and data.can_trade(security):
            order_target_percent(security, 0)
    
    # Log the long and short orders each week.
    log.info("This week's longs: "+", ".join([long_.symbol for long_ in context.long_secs.index]))
    log.info("This week's shorts: "  +", ".join([short_.symbol for short_ in context.short_secs.index]))

def record_vars(context, data):
    """
    This function is called at the end of each day and plots certain variables.
    """
    
    # Check how many long and short positions we have.
    longs = shorts = 0
    for position in context.portfolio.positions.itervalues():
        if position.amount > 0:
            longs += 1
        if position.amount < 0:
            shorts += 1
            
    # Record and plot the leverage of our portfolio over time as well as the 
    # number of long and short positions. Even in minute mode, only the end-of-day 
    # leverage is plotted.
    record(leverage = context.account.leverage, long_count=longs, short_count=shorts)
