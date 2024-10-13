from django.db import models


class Currency(models.Model):
    """
    Represents a currency used in exchange rate calculations. Each currency
    is uniquely identified by its ISO code (e.g., USD, EUR), along with its
    full name and symbol.
    """

    code = models.CharField(max_length=3, unique=True, db_index=True)
    name = models.CharField(max_length=20, db_index=True, null=True)
    symbol = models.CharField(max_length=10, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        """
        Returns the string representation of the currency, which in this case
        is its ISO code (e.g., 'USD', 'EUR').
        """
        return self.code


class CurrencyProvider(models.Model):
    """
    Represents an external provider that supplies currency exchange rates.
    Each provider has a base URL and optionally an API key for authentication.
    Providers can be prioritized, with lower priority values indicating a
    higher priority.
    """

    name = models.CharField(max_length=50, unique=True)
    url = models.URLField()
    api_key = models.CharField(max_length=100, blank=True, null=True)
    priority = models.IntegerField(default=0)
    active = models.BooleanField(default=True)
    default_base_currency = models.CharField(max_length=3, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        """
        Returns the string representation of the provider, including its name and priority.
        """
        return f"{self.name} (Priority: {self.priority})"


class CurrencyExchangeRate(models.Model):
    """
    Represents an exchange rate between two currencies for a specific valuation date.
    The exchange rate data includes the source currency, target currency, and rate value.
    This model also tracks the timestamp for when the rate was added and whether it
    is the most recent ('active') rate for the currency pair. The rate is also tied
    to the provider from which it was retrieved.
    """

    source_currency = models.ForeignKey(
        Currency, on_delete=models.CASCADE, related_name="source_currency"
    )
    target_currency = models.ForeignKey(
        Currency, on_delete=models.CASCADE, related_name="target_currency"
    )
    valuation_date = models.DateField(db_index=True)
    rate_value = models.DecimalField(max_digits=18, decimal_places=6)
    active = models.BooleanField(default=True)
    provider = models.ForeignKey(
        CurrencyProvider, on_delete=models.CASCADE, related_name="exchange_rates"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        """
        Ensures uniqueness for exchange rates.
        """

        unique_together = (
            "source_currency",
            "target_currency",
            "valuation_date",
            "rate_value",
        )

    def __str__(self):
        """
        Returns the string representation of the exchange rate.
        """
        return f"{self.source_currency.code} to {self.target_currency.code} on {self.valuation_date}: {self.rate_value}"
