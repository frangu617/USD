from scipy.stats import norm

upper = norm.cdf(1.4)
lower = norm.cdf(-0.6)

proportion = upper - lower
print(proportion)