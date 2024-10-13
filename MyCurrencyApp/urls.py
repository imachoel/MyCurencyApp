from django.urls import path

from .views.currency_converter_view import CurrencyConverterView
from .views.currency_rates_list_view import CurrencyRatesListView
from .views.currency_twrr_view import CurrencyTWRRView

urlpatterns = [
    path("currency-rates/", CurrencyRatesListView.as_view(), name="currency-rates"),
    path(
        "currency-converter/",
        CurrencyConverterView.as_view(),
        name="currency-converter",
    ),
    path("currency-twrr/", CurrencyTWRRView.as_view(), name="currency-twrr"),
]
