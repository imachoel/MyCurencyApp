from django.contrib import admin

from .admin_views.converter_admin import ConverterAdmin
from .admin_views.graph_view_admin import ExchangeRateGraphAdmin
from .models import Currency, CurrencyExchangeRate

admin.site.register(Currency, ConverterAdmin)
admin.site.register(CurrencyExchangeRate, ExchangeRateGraphAdmin)
