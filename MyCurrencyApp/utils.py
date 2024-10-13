import logging
from datetime import datetime, timedelta
from .models import CurrencyExchangeRate
from .providers.fixer_provider import FixerProvider
from .providers.mock_provider import MockProvider


def is_valid_date(date_str):
    """
    Check if the provided string is in 'YYYY-MM-DD' format.
    """
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
        return True
    except ValueError:
        return False


def get_date_range(date_from, date_to):
    """
    Generate a list of dates between date_from and date_to, inclusive.
    Both dates should be in 'YYYY-MM-DD' format.
    """
    date_format = "%Y-%m-%d"
    start_date = datetime.strptime(date_from, date_format)
    end_date = datetime.strptime(date_to, date_format)

    date_range = [
        (start_date + timedelta(days=i)).strftime(date_format)
        for i in range((end_date - start_date).days + 1)
    ]

    return date_range


def get_provider_instance(provider, url):
    """
    Factory method to instantiate the appropriate provider class.
    """
    providers = {
        "Fixer": FixerProvider,
        "Mock": MockProvider,
        # Add other providers here
    }

    provider_class = providers.get(provider.name)

    if provider_class:
        return provider_class(provider, url)
    else:
        logging.error(f"Provider name {provider.name} not found")
        return None


def update_exchange_rate_activity(
        source_currency, target_currency, rate_value, valuation_date, provider
):
    CurrencyExchangeRate.objects.filter(
        source_currency__code=source_currency.code,
        target_currency__code=target_currency.code,
        valuation_date__lt=valuation_date,
    ).update(active=False)

    new_rate, _ = CurrencyExchangeRate.objects.update_or_create(
        source_currency=source_currency,
        target_currency=target_currency,
        valuation_date=valuation_date,
        defaults={
            "rate_value": rate_value,
            "provider": provider,
            "active": True,
        },
    )
    return new_rate


def format_data_for_chart(data):
    chart_data = {"labels": [], "datasets": []}

    color_palette = [
        "rgba(75, 192, 192, 1)",
        "rgba(153, 102, 255, 1)",
        "rgba(255, 159, 64, 1)",
        "rgba(255, 99, 132, 1)",
        "rgba(54, 162, 235, 1)",
        "rgba(255, 206, 86, 1)",
        "rgba(201, 203, 207, 1)",
        "rgba(255, 99, 71, 1)",
        "rgba(75, 0, 130, 1)",
    ]

    color_index = {}

    for source_currency, target_currencies in data.items():
        if source_currency == target_currencies:
            continue
        for target_currency, rates in target_currencies.items():
            currency_pair = f"{source_currency}_{target_currency}"
            if currency_pair not in color_index:
                color_index[currency_pair] = len(color_index) % len(color_palette)

            dataset = {
                "label": f"{source_currency} to {target_currency}",
                "data": [],
                "borderColor": color_palette[color_index[currency_pair]],
                "fill": False,
            }

            for rate in rates:
                valuation_date = (
                    rate["valuation_date"].strftime("%Y-%m-%d")
                    if isinstance(rate["valuation_date"], datetime)
                    else rate["valuation_date"]
                )
                rate_value = rate["rate_value"]

                if valuation_date not in chart_data["labels"]:
                    chart_data["labels"].append(valuation_date)

                dataset["data"].append(rate_value)

            chart_data["datasets"].append(dataset)

    return chart_data
