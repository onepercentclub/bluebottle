from memoize import memoize
import djmoney_rates.utils


djmoney_rates.utils.get_rate = memoize()(djmoney_rates.utils.get_rate)
djmoney_rates.utils.get_rate_source = memoize()(djmoney_rates.utils.get_rate_source)
