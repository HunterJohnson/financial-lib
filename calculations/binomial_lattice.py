import math

# --------------
# Internal Utils
# --------------

def __shrink_square_matrix(matrix, new_len):
    return [row[:len] for row in matrix[:len]]

def __per_element_matrix_op(a, b, func):
    c = []
    for i in range(len(a)):
        lst = []
        for j in range(len(a[i])):
            el_a = a[i][j]
            el_b = b[i][j]
            if None in [el_a, el_b]:
                lst.append(None)
            else:
                lst.append(func(el_a, el_b))
        c.append(lst)
    return c


# --------------
# Utils
# --------------

def convert_black_scholes_to_binomial_params(
        std_dev=None, interest_rate=None, time_to_maturity=None, 
        dividend_yield=0, num_periods=1):

    sig = std_dev
    r = interest_rate
    T = time_to_maturity
    c = dividend_yield
    n = num_periods

    u = math.exp(sig * math.sqrt(T/n))
    d = 1/u

    return {
        "up_move_change": u,
        "down_move_change": d,
        "gross_interest_rate": math.exp((r*T)/n),
        "risk_free_probability": (math.exp((r - c)*(T/n)) - d) / (u - d),
        "num_periods": num_periods
    } 


def add_matrices(a, b):
    return __per_element_matrix_op(a, b, 
        lambda el_a, el_b: el_a + el_b)

def max_matrices(a, b):
    return __per_element_matrix_op(a, b, 
        lambda el_a, el_b: max(el_a, el_b))

def filter_dict(d, keys):
    d2 = {}
    for k in keys:
        d2[k] = d[k]
    return d2


# ------------------
# Lattices
# ------------------

class Lattice(object):
    def value(self):
        return self.compute()[0][0]
    
    def compute(self):
        return None

    def _print_matrix(self, matrix, sig_digits=2):
        for i in range(len(matrix)):
            for j in range(len(matrix)):
                val = matrix[i][j]
                if val is None:
                    val = ""
                else:
                    val = round(val,sig_digits)
                print "%6s " % val,
            print


    def display(self, sig_digits=2):
        price_matrix = self.compute()
        price_matrix = zip(*price_matrix)
        for i in range(len(price_matrix)):
            print "t = %2d " % i,
        print
        print

        self._print_matrix(price_matrix,sig_digits)
        print


# Wraps a price matrix (as output from compute() of any lattice)
# in a lattice object. Lattice is static with the input.
class StaticLattice(Lattice):
    def __init__(self,
            underlying_matrix=None):
        self.mtx = underlying_matrix

    def __len__(self):
        return len(self.mtx)

    def compute(self):
        return self.mtx


class ValueChangeLattice(Lattice):
    def __init__(self,
            initial_value=None, 
            up_move_change=None,
            down_move_change=None,
            num_periods=None):

        self.V = initial_value
        self.u = up_move_change
        self.d = down_move_change
        self.n = num_periods

    def __len__(self):
        return self.n + 1

    def _value(self, up_moves, down_moves):
        return self.V * (self.u ** up_moves) * (self.d ** down_moves)

    def compute(self):
        price_matrix = []
        for i in range(self.n+1):
            row = []
            for j in range(i+1):
                row.append(self._value(i-j,j))
            for j in range(i+1,self.n+1):
                row.append(None)
            price_matrix.append(row)
        return price_matrix


class DerivativeLattice(Lattice):
    def __init__(self,
            underlying_lattice=None,
            gross_interest_rate=None,
            interest_rate_lattice=None,
            expiration=None):

        self.underlying = underlying_lattice
        self.R = gross_interest_rate
        self.interest_rates = interest_rate_lattice
        self.expiration = expiration
        if self.expiration is None:
            self.expiration = len(underlying_lattice) - 1

    def __len__(self):
        return self.expiration + 1

    def _initial_prices(self, underlying_prices):
        return underlying_prices

    def _value(self, next_up, next_down, underlying, rate):
        return 0


    def compute(self):
        underlying_matrix = self.underlying.compute()

        #If I expire before underlying, reshape underlying_matrix and go on
        my_len = self.__len__()
        if my_len < len(underlying_matrix):
            mtx = underlying_matrix
            mtx = [r[:my_len] for r in mtx[:my_len]]
            underlying_matrix = mtx

        n = len(underlying_matrix)
        final_underlying_prices = underlying_matrix[n-1]

        price_matrix = [self._initial_prices(final_underlying_prices)]

        rate_matrix = None
        if not self.interest_rates is None:
            rate_matrix = self.interest_rates.compute()

        for i in reversed(range(1,n)):
            prev_row = price_matrix[n - i - 1]
            row = []

            for j in range(i):

                rate = self.R
                if not rate_matrix is None:
                    rate = (1 + rate_matrix[i-1][j])

                row.append(
                    self._value(
                        prev_row[j], 
                        prev_row[j+1], 
                        underlying_matrix[i-1][j],
                        rate))

            for j in range(i, n):
                row.append(None)

            price_matrix.append(row)

        return [row for row in reversed(price_matrix)]
        

class ForwardPriceLattice(DerivativeLattice):
    def __init__(self,
            risk_free_probability=None,
            gross_interest_rate=None,
            interest_rate_lattice=None,
            expiration=None,
            underlying_lattice=None):

        DerivativeLattice.__init__(
            self, 
            gross_interest_rate=gross_interest_rate,
            interest_rate_lattice=interest_rate_lattice,
            expiration=expiration,
            underlying_lattice=underlying_lattice)

        self.q = risk_free_probability

    def _value(self, next_up, next_down, underlying, rate):
        val = next_up * self.q
        val += next_down * (1 - self.q)
        return val / rate



class FuturesPriceLattice(DerivativeLattice):
    def __init__(self,
            risk_free_probability=None,
            expiration=None,
            underlying_lattice=None):

        DerivativeLattice.__init__(
            self, 
            expiration=expiration,
            underlying_lattice=underlying_lattice)

        self.q = risk_free_probability

    def _value(self, next_up, next_down, underlying, rate):
        val = next_up * self.q
        val += next_down * (1 - self.q)
        return val

class OptionPriceLattice(DerivativeLattice):
    def __init__(self,
            gross_interest_rate=None,
            interest_rate_lattice=None,
            risk_free_probability=None,
            option_style='american',
            option_type=None,
            strike_price=None,
            underlying_lattice=None,
            expiration=None):

        DerivativeLattice.__init__(
            self, 
            gross_interest_rate=gross_interest_rate,
            interest_rate_lattice=interest_rate_lattice,
            expiration=expiration,
            underlying_lattice=underlying_lattice)

        self.q = risk_free_probability
        self.option_style = option_style
        self.option_type = option_type
        self.K = strike_price

    def _initial_prices(self, underlying_prices):
        return [self._exercise_value(p) for p in underlying_prices]

    def _exercise_value(self, price):
        if self.option_type == "call":
            return max(price - self.K, 0)
        elif self.option_type == "put":
            return max(self.K - price, 0)

    def _value(self, next_up, next_down, underlying, rate):
        val = next_up * self.q
        val += next_down * (1 - self.q)
        val = val / rate

        if self.option_style == 'european':
            return val

        return max(val, self._exercise_value(underlying))

class BondLattice(DerivativeLattice):
    def __init__(self,
            interest_rate_lattice=None,
            risk_free_probability=None,
            time_to_maturity=None,
            coupon_rate=0,
            face_value=None):

        coupon = face_value * coupon_rate

        matrix = []
        n = time_to_maturity + 1
        for i in range(n):
            row = []
            for j in range(n):
                if i == n - 1:
                    row.append(face_value + coupon)
                else:
                    row.append(None)
            matrix.append(row)

        underlying_lattice = StaticLattice(
            underlying_matrix=matrix)

        DerivativeLattice.__init__(self,
            interest_rate_lattice=interest_rate_lattice,
            expiration=time_to_maturity,
            underlying_lattice=underlying_lattice)

        self.q = risk_free_probability
        self.face_value = face_value
        self.coupon = coupon

    def _value(self, next_up, next_down, underlying, rate):
        val = self.q * next_up 
        val += (1 - self.q) * next_down
        val = val / rate
        return self.coupon + val

def calculate_bond_forward_price(bond_lattice, expiration):
    matrix = bond_lattice.compute()
    n = expiration + 1
    matrix = [r[:n] for r in matrix[:n]]

    last_row = matrix[n-1]
    for i in range(n):
        last_row[i] = last_row[i] - bond_lattice.coupon

    underlying_lattice = StaticLattice(
        underlying_matrix=matrix)

    fwd = ForwardPriceLattice(
        gross_interest_rate=bond_lattice.R,
        interest_rate_lattice=bond_lattice.interest_rates,
        risk_free_probability=bond_lattice.q,
        expiration=expiration,
        underlying_lattice=underlying_lattice)

    cash_account = BondLattice(
        interest_rate_lattice=bond_lattice.interest_rates,
        risk_free_probability=bond_lattice.q,
        time_to_maturity=expiration,
        face_value=1)

    return fwd.value() / cash_account.value()
        

class BondFuturesPriceLattice(FuturesPriceLattice):
    def _initial_prices(self, underlying_prices):
        return [p - self.underlying.coupon for p in underlying_prices]

class SwapLattice(DerivativeLattice):
    def __init__(self,
            strike_rate=None,
            risk_free_probability=None,
            interest_rate_lattice=None,
            expiration=None):

        DerivativeLattice.__init__(self,
            underlying_lattice=interest_rate_lattice,
            interest_rate_lattice=interest_rate_lattice,
            expiration=expiration-1)

        self.strike_rate = strike_rate
        self.q = risk_free_probability

    def _initial_prices(self, underlying_rates):
        return [(r - self.strike_rate) / (1+r) for r in underlying_rates]

    def _value(self, next_up, next_down, underlying, rate):
        val = next_up * self.q
        val += next_down * (1 - self.q)
        val += underlying - self.strike_rate
        return val / rate
