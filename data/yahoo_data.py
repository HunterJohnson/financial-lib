"""Yahoo Stock classes and function
    Storage Class
    -------------
        Class that acts as cache for all downloaded data
    cache Function
    --------------
        Function that allows for cache data pulled from yahoo
        (Decorates the current() and historical() methods in the Stock class)
    Stock Class
    -----------
        Class that houses our stock symbol and provides methods to pull both current
        and historical stock price information
"""

from numeric import *
from storage import Storage
import urllib, datetime, time, math

__all__=['Stock', 'cache', 'mean', 'variance', 'stddev', 'covariance','correlation','testStock']

def cache(days=0,hours=0,minutes=0,seconds=0):
    """Decorator function to cache our storage data.
    Parameters:
        days:  Number of days to cache our results
        hours:  Number of hours to cache our results
        minutes:  Number of minutes to cache our results
        seconds:  Number of seconds to cache our results
    """
    cache_storage={}
    seconds+=60*(minutes+60*(hours+24*days))
#    now = datetime.datetime.now()
    def g(f):
        """The function we return in place of the function/method being decorated
        Parameter:
           f:  The function being decorated
        """
        def h(*a,**b):
            """The contents of the function we are returning
            
            Parameters:
                *a: Tuple containing parameters
                **b: Dictionary containing keyword arguments, defaults to empty dictionary
            """            
            key=repr((a,b))
            if key in cache_storage and cache_storage[key][0]+datetime.timedelta(seconds=seconds)\
                                        >=datetime.datetime.now():
                d=cache_storage[key][1]
            else:
                d=f(*a,**b)
                cache_storage[key]=(datetime.datetime.now(),d)
            return d
        return h
    return g

def mean(series,name='log_return'):
    """Return the arithmetic mean of the series (based on log returns only)
    Parameters:
        series : list/tuple
        One-dimensional number list/tuple with stock data.
    Returns
        mean : float
 
    Examples:
    >>> stock1=Stock('GOOG')
    >>> hist1=stock1.historical()
    >>> mean(hist1)>0
    True
    """ 
    return sum(x[name] for x in series)/len(series)

def variance(series,name='log_return'):
    """return the variance of the series.
 
    Parameters:
        series : list/tuple
            One-dimensional number list/tuple with stock data.
    Return:
        variance : float
        
    Examples:
    >>> stock1=Stock('GOOG')
    >>> hist1=stock1.historical()
    >>> variance(hist1)>0
    True
 
    """
    return sum(x[name]**2 for x in series)/len(series)-mean(series,name)**2

def stddev(series,name='log_return'):
    """return the standard deviation of the series.
    Parameters:
        series : list/tuple
            One-dimensional number list/tuple with stock data.
    Return:
        stddev : float
  
    Examples:
    >>> stock1=Stock('GOOG')
    >>> hist1=stock1.historical()
    >>> stddev(hist1)>0
    True
    """
    return math.sqrt(variance(series,name))

def covariance(series_a, series_b,name_a='log_return',name_b=None):
    """return the covariance of the two series.
    Parameters:
        series_x : list
            One-dimensional number list/tuple with stock data.
        series_y : list
            One-dimensional number list/tuple with stock data.
    Return:
        covariance : float
    Examples:
    >>> stock1=Stock('GOOG')
    >>> hist1=stock1.historical()
    >>> hist2=stock1.historical()
    >>> covariance(hist1,hist2)>0
    True
    """
    name_b=name_b or name_a
    mean_a=mean(series_a,name_a)
    mean_b=mean(series_b,name_b)
    i,j=0,0
    s,c=0.0,1
    while i<len(series_b) and j<len(series_b):
        if series_a[i].date<series_b[j].date:
            i+=1
        elif series_a[i].date>series_b[j].date:
            j+=1
        else:
            s+=series_a[i][name_a]*series_b[j][name_b]
            c+=1
            i+=1
            j+=1
    return (s/c-mean_a*mean_b)

def correlation(series_a, series_b,name_a='log_return',name_b=None):
    """return the correlation of the two series.
    Parameters:
        series_x : list
            One-dimensional number list/tuple, otherwise exception will be raised.
        series_y : list
            One-dimensional number list/tuple, otherwise exception will be raised.
    Return:
        correlation : float
    Examples:
    >>> stock1=Stock('GOOG')
    >>> hist1=stock1.historical()
    >>> hist2=stock1.historical()
    >>> correlation(hist1,hist2)>0.999
    True
    """
    name_b=name_b or name_a
    stddev_a=stddev(series_a,name_a)
    stddev_b=stddev(series_b,name_b)
    c=covariance(series_a, series_b,name_a,name_b)
    return c/(stddev_a*stddev_b)
        

class Stock:

    """Class that allowing for pulling financial information from Yahoo
    Holds our Stock symbol and provide methods to pull current and historical stock
    information.
    """
    
    URL_CURRENT = 'http://finance.yahoo.com/d/quotes.csv?s=%(symbol)s&f=%(columns)s'
    URL_HISTORICAL = 'http://ichart.yahoo.com/table.csv?s=%(s)s&a=%(a)s&b=%(b)s&c=%(c)s&d=%(d)s&e=&(e)s&f=%(f)s'
    def __init__(self,symbol):
        """Initialize Stock object.
        Parameter:
            symbol: Symbol of the stock we will get from Yahoo
        Examples:
        >>> stock1=Stock('GOOG')
        >>> stock2=Stock('YHOO')
        
        """
        self.symbol=symbol.upper()

    def __repr__(self):
        """Show string representation of our Stock object.
        Parameter:
            none
        """
        return self.symbol

    @cache(seconds=5)
    def current(self):
        """Method to return the current stock price information for our stock symbol
        Parameter:
            none
        Returns:
            An updated storage object contain current price information
        Examples:
        >>> stock1=Stock('GOOG')
        >>> current1=stock1.current()
        >>> current1.price
        482.37
        >>> current1.market_cap
        '153.6B'
        >>> current1.earnings_per_share
        21.971
        """
        FIELDS=(('price', 'l1'),
                ('change', 'c1'),
                ('volume', 'v'),
                ('average_daily_volume', 'a2'),
                ('stock_exchange', 'x'),
                ('market_cap', 'j1'),
                ('book_value', 'b4'),
                ('ebitda', 'j4'),
                ('dividend_per_share', 'd'),
                ('dividend_yield', 'y'),
                ('earnings_per_share', 'e'),
                ('52_week_high', 'k'),
                ('52_week_low', 'j'),
                ('50_days_moving_average', 'm3'),
                ('200_days_moving_average', 'm4'),
                ('price_earnings_ratio', 'r'),
                ('price_earnings_growth_ratio', 'r5'),
                ('price_sales_ratio', 'p5'),
                ('price_book_ratio', 'p6'),
                ('short_ratio', 's7'))
        columns = ''.join([row[1] for row in FIELDS])
        url = self.URL_CURRENT % dict(symbol=self.symbol, columns=columns)
        raw_data = urllib.urlopen(url).read().strip().strip('"').split(',')
        current=Storage()
        for i,row in enumerate(FIELDS):
            try:
                current[row[0]]=float(raw_data[i])
            except:
                current[row[0]]=raw_data[i]
        return current

    @cache(minutes=15)
    def historical(self,start=None, stop=None):
        """Method that retrieves and stores historical stock data from Yahoo.
        Parameter:
            start: first date for which to pull stock data
            stop: last date for which to pull stock data
        Return:
            The series of Storage objects that contain our stock data
        Examples:
        >>> stock1=Stock('GOOG')
        >>> historical=stock1.historical()
        >>> historical[-1].adjusted_close
        482.37
        >>> historical[-1].log_return
        -0.0067355626547744071
        
        """
        start =  start or datetime.date(1900,1,1)
        stop = stop or datetime.date.today()
        url = self.URL_HISTORICAL % dict(s=self.symbol,
                                         a=start.month-1,b=start.day,c=start.year,
                                         d=stop.month-1,e=stop.day,f=stop.year)
        # Date,Open,High,Low,Close,Volume,Adj Close
        raw_data = [row.split(',') for row in urllib.urlopen(url).readlines()[1:]]
        previous_adjusted_close=0
        series=[]
        raw_data.reverse()
        for row in raw_data:            
            adjusted_close=float(row[6])
            log_return = math.log(adjusted_close/previous_adjusted_close) if previous_adjusted_close else 0
            previous_adjusted_close=adjusted_close
            series.append(Storage(date=datetime.date(*time.strptime(row[0],'%Y-%m-%d')[:3]),
                                  open=float(row[1]),
                                  high=float(row[2]),
                                  low=float(row[3]),
                                  close=float(row[4]),
                                  volume=float(row[5]),
                                  adjusted_close=adjusted_close,
                                  log_return=log_return))
        return series


# we create a function to download adjusted closing prices from Yahoo                                          
def download(symbol='aapl',days=360, what='adjusted_close'):
    return [d[what] for d in Stock(symbol).historical()[-days:]]

def testStock():
    """Function to test one stock"""
    import sys
    if len(sys.argv)>1:
        stock = Stock(sys.argv[1])
    else:
        stock = Stock('GOOG')
    stock2 = Stock('YHOO')
    print 'price', stock.current().price
    print 'book_value', stock.current().book_value
    for i in range(5):
        print '%s adjusted close %s' % (stock.historical()[i].date,stock.historical()[i].adjusted_close)

    h=stock.historical()
    h2=stock2.historical()
    print stock
    print 'mean=',mean(h)
    print 'variance=',variance(h)
    print 'stddev=',stddev(h)

    print stock2
    print 'mean=',mean(h2)
    print 'variance=',variance(h2)
    print 'stddev=',stddev(h2)

    print stock,"vs",stock2
    print 'covariance=',covariance(h,h2)
    print 'correlation=',correlation(h,h2)

if __name__ == '__main__':
    import doctest
    testStock()
    doctest.testmod()
