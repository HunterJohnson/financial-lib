import math
import numpy as np
import matplotlib.pyplot as plt
import numpy as np
 
 
DAYS_PER_YEAR = 252.0
 
 
 # 1 dimensional Brownian motion aka Wiener Process
def generate_bm_prices(periods, start_price, mu, sigma, delta): 
    t = delta / DAYS_PER_YEAR
    prices = np.zeros(periods)
    epsilon_sigma_t = np.random.normal(0, 1, periods) * sigma * np.sqrt(t)
    prices[0] = start_price
    for i in range(1, len(prices)):
        prices[i] = prices[i-1] * mu * t + \
                    prices[i-1] * epsilon_sigma_t[i-1] + \
                    prices[i-1]
    return prices

# geometric brownian motion
  def generate_gbm_prices(periods, start_price, mu, sigma, delta):
    t = delta / DAYS_PER_YEAR
    prices = np.zeros(periods)
    epsilon_sigma_t = np.random.normal(0, 1, periods-1) * sigma * np.sqrt(t)
    prices[0] = start_price
    for i in range(1, len(prices)):
        prices[i] = prices[i-1] * \
                    np.exp((mu - 0.5 * sigma**2) * t +
                           epsilon_sigma_t[i-1])
    return prices


# plot simulations
 
def run_multiple_simulations(simulation_count, periods, start_price, mu,
                             sigma, days_per_period):
    np.random.seed(10)
    annualised_days = 252.0
    sigmas = []
    mus = []
    for i in range(0, simulation_count):
        prices = gbm.generate_gbm_prices(periods, start_price, mu, sigma,
                                         days_per_period)
        returns = calculate_log_returns(prices)
        mus.append((1.0+returns.mean())**annualised_days - 1.0)
        sigmas.append(returns.std() * math.sqrt(annualised_days))
 
    plt.subplot(211)
    plt.hist(mus)
    plt.subplot(212)
    plt.hist(sigmas)
    plt.show()
 
 
def lag(data, empty_term=0.):
    lagged = np.roll(data, 1)
    lagged[0] = empty_term
    return lagged
 
 
def calculate_log_returns(pnl):
    lagged_pnl = lag(pnl)
    returns = np.log(pnl / lagged_pnl)
 
    # All values prior to our position opening in pnl will have a
    # value of inf. This is due to division by 0.0
    returns[np.isinf(returns)] = 0.
    # Additionally, any values of 0 / 0 will produce NaN
    returns[np.isnan(returns)] = 0.
    return returns
