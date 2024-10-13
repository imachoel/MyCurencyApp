import random
from datetime import datetime
from MyCurrencyApp.models import Currency, CurrencyExchangeRate


def create_source_currency(code, name):
    return Currency.objects.create(code=code, name=name)


def add_exchange_rate(
    source_currency, target_currency, provider, rate_value=None, valuation_date=None
):
    if not rate_value:
        rate_value = random.uniform(0.85, 1.25)
    if not valuation_date:
        valuation_date = datetime.now()
    new_exchange_rate = CurrencyExchangeRate.objects.create(
        source_currency=source_currency,
        target_currency=target_currency,
        provider=provider,
        rate_value=rate_value,
        valuation_date=valuation_date,
    )
    return new_exchange_rate


def delete_exchange_rate(source_currency, target_currency):
    CurrencyExchangeRate.objects.filter(
        source_currency=source_currency, target_currency=target_currency
    ).delete()
