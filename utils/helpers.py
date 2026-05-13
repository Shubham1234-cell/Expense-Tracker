def format_currency(value, currency='USD'):
    symbols = {'USD': '$', 'EUR': '€', 'GBP': '£', 'INR': '₹'}
    return f"{symbols.get(currency, '$')}{value:,.2f}"

def get_financial_score(income, expense):
    if income == 0:
        return 0
    ratio = expense / income
    if ratio < 0.5:
        return 90
    elif ratio < 0.8:
        return 70
    elif ratio < 1.0:
        return 50
    return 30
