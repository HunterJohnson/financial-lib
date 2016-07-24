# this strategy buy stocks when 75 % of stocks in the list is up 1 percent
# and sell when 75 % of stocks in the list is down 1 percent 

# this long only strategy


from collections import Counter
import math


def initialize(context):
   
    # the tech stocks here are apple, HPQ, IBM, ACN, CSC, YHOO, MSFT, GOOG_L, Facebook and AOL
    
    context.stocks = [sid(24), sid(3735), sid(3766), sid(25555),sid(1898),sid(14848),sid(5061),sid(5692),sid(26578),sid(42950),sid(38989)]
        # now we are setting this strategy only long only... will give an error if we try to short
    
    set_long_only()
    # setting commission to be realistic
    set_commission(commission.PerTrade(cost=1.20))
    
    context.funds=[sid(19658)]
    
    
def handle_data(context, data):

    decider=moved_a_lot(context,data)

    #record(portfolio_values=context.portfolio.portfolio_value,position_values=context.portfolio.positions_value,cash=context.portfolio.cash)    
    for stock in context.stocks:
                
        if decider == 1 and context.portfolio.positions[stock].amount==0 and context.portfolio.cash > 10* data[stock].price :
            order(stock,10)
            print ' '
            print get_datetime()
            log.info(' Buying'+str( stock.symbol)+'at price '+str(data[stock].price))
          
        elif decider == -1 and context.portfolio.positions[stock].amount > 0:
            print ' '


            order(stock,-10)
            print get_datetime()
            log.info(' Selling'+str( stock.symbol)+'at price '+str(data[stock].price))
            print get_datetime()

def moved_a_lot(context,data):
    
    price_history = history(bar_count=5, frequency='1d', field='price')
    
    per=[]
    movement=[]

    # calculating the percentage of each stock in the list
    for stock in context.stocks:
        prev_bar=price_history[stock][-2]
        curr_bar=price_history[stock][-1]
        percentage=  (curr_bar-prev_bar )/prev_bar
        per.append(percentage)

    # converting the percentage to list like this [ 1,1,1,0,-1,0]
    # 1 if percentage is greater than 0.005
    # -1 if percentage is less than -0.005
    # 0 otherwise
    
    for x in per:
        if x > 0.01:
            movement.append(1)
        elif x< -0.01:
            movement.append(-1)
        else:
            movement.append(0)
            
    # finding the mode and returning it if it occours more han 2/3 of the stocks
    
    if Counter(movement).most_common(1)[0][1] > (2/3.0)*len(movement):
        return Counter(movement).most_common(1)[0][0]
    
    else:
        return 0

            
            
        
        
        
        
        
    
    
    
    
    
    
    
    
    
    
    
    