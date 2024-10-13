class BaseProvider:
    def __init__(self, provider_model, url):
        self.url = url
        self.api_key = provider_model.api_key
        self.timeout = 10  # Timeout of 10 seconds per request
        self.base_currency = provider_model.default_base_currency

    def get_exchange_rate_data(
        self, source_currency, exchanged_currency, valuation_date
    ):
        """
        Abstract method to be implemented by subclasses.
        """
        raise NotImplementedError("Subclasses must implement this method.")

    def set_url(self, url, endpoint):
        self.url = f"{url}/{endpoint}"
