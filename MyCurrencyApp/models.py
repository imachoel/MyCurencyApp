from django.db import models


class Currency(models.Model):

    code = models.CharField(max_length=3, unique=True, db_index=True)
    name = models.CharField(max_length=20, db_index=True, null=True)
    symbol = models.CharField(max_length=10, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
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
        return f"{self.name} (Priority: {self.priority})"


class CurrencyExchangeRate(models.Model):

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
        return f"{self.source_currency.code} to {self.target_currency.code} on {self.valuation_date}: {self.rate_value}"
