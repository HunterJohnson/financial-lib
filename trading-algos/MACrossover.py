
def initialize(context):
    
    #using Google (solid blue chip stock)
    context.stock = sid(26578)

def handle_data(context, data):
    
   
    stock = context.stock
    
    #current and historic data from Google
    stock_data = data[stock]
    
    #moving average price data
    mavg_short_buy = stock_data.mavg(5)
    mavg_long_buy = stock_data.mavg(20)
    
    mavg_short_sell = stock_data.mavg(1)
    mavg_long_sell = stock_data.mavg(3)
    
    # current price of the stock
    current_price = stock_data.price

    # how much cash in portfolio
    cash = context.portfolio.cash
   

   
    if mavg_short_buy > mavg_long_buy and cash > current_price:
        
        # how many shares we can buy
        number_of_shares = int(cash/current_price)
        # int() helps us get a integer value, we can't buy half a share
        
        # place the buy order
        order(stock, number_of_shares)
    elif mavg_short_sell < mavg_long_sell:
        #how many shares we have
        number_of_shares = context.portfolio.positions[stock.sid].amount
        
        #sell all shares
        order(stock, -number_of_shares)
