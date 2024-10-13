from decimal import Decimal
from django.urls import path
from django.shortcuts import render
from django.contrib import admin
from ..forms.converter_form import CurrencyConverterForm

from ..helper.get_create_exchange_rate import get_or_create_exchange_rate


class ConverterAdmin(admin.ModelAdmin):

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "currency-converter/",
                self.admin_site.admin_view(self.converter_view),
                name="currency_converter",
            ),
        ]
        return custom_urls + urls

    def converter_view(self, request):
        form = CurrencyConverterForm(request.POST or None)
        conversion_result = None

        if request.method == "POST" and form.is_valid():
            source_currency = form.cleaned_data["source_currency"]
            target_currencies = form.cleaned_data["target_currencies"]
            amount = form.cleaned_data["amount"]

            conversion_result = {}

            for target_currency in target_currencies:
                exchange_rate = get_or_create_exchange_rate(
                    source_currency, target_currency
                )

                if exchange_rate or target_currency.code == source_currency.code:
                    if target_currency.code != source_currency.code:
                        exchanged_amount = Decimal(amount) * exchange_rate
                        conversion_result[target_currency.code] = exchanged_amount
                    else:
                        conversion_result[target_currency.code] = amount
                else:
                    conversion_result[target_currency.code] = "Error fetching data"

        context = {"form": form, "conversion_result": conversion_result}
        return render(request, "admin/converter.html", context)
