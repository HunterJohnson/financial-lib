#!/usr/bin/env python
from math import exp

# Input stock parameters
dt = input("Enter the timestep: ")
S = input("Enter the initial asset price: ")
r = input("Enter the risk-free discount rate: ")
K = input("Enter the option strike price: ")
p = input("Enter the asset growth probability p: ")
u = input("Enter the asset growth factor u: ")
N = input("Enter the number of timesteps until expiration: ")

# Input whether this is a call or a put option
call = raw_input("Is this a call or put option? (C/P) ").upper().startswith("C")

def price(k, us):
    """ Compute the stock price after 'us' growths and 'k - us' decays. """
    return S * (u ** (2 * us - k))

def bopm(k, us):
    """
    Compute the option price for a node 'k' timesteps in the future
    and 'us' growth events. Note that thus there are 'k - us' decay events.
    """

    # Compute the exercise profit
    stockPrice = price(k, us)
    if call: exerciseProfit = max(0, stockPrice - K)
    else:    exerciseProfit = max(0, K - stockPrice)

    # Base case (this is a leaf)
    if k == N: return exerciseProfit

    # Recursive case: compute the binomial value 
    decay = exp(-r * dt)
    expected = p * bopm(k + 1, us + 1) + (1 - p) * bopm(k + 1, us)
    binomial = decay * expected

    # Assume this is an American-style option
    return max(binomial, exerciseProfit)

print 'Computed option price: $%.2f' % bopm(0, 0)
