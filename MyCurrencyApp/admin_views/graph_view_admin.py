from django.contrib import admin
from django.urls import path
from django.shortcuts import render
from django.http import JsonResponse
from datetime import datetime

from ..forms.converter_form import CurrencyExchangeRateForm
from ..helper.get_currency_rates import get_currency_rates_data
from ..models import Currency
from ..utils import format_data_for_chart

BATCH_SIZE = 20


class ExchangeRateGraphAdmin(admin.ModelAdmin):
    change_list_template = (
        "admin/exchange_rate_graph.html"  # Custom template for the graph
    )

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "exchange-rate-graph/",
                self.admin_site.admin_view(self.graph_view),
                name="exchange_rate_graph",
            ),
            path(
                "exchange-rate-all-currencies/",
                self.admin_site.admin_view(self.exchange_rate_all_currencies),
                name="exchange_rate_all_currencies",
            ),
        ]
        return custom_urls + urls

    def graph_view(self, request):
        """Renders the HTML page that contains the exchange rate graph."""
        form = CurrencyExchangeRateForm()
        return render(request, "admin/exchange_rate_graph.html", {"form": form})

    def exchange_rate_all_currencies(self, request):
        """Fetches exchange rate data based on start_date and end_date from the request."""
        start_date = request.GET.get("start_date")
        end_date = request.GET.get("end_date")

        try:
            start_date = datetime.strptime(start_date, "%Y-%m-%d")
            end_date = datetime.strptime(end_date, "%Y-%m-%d")
        except (ValueError, TypeError):
            return JsonResponse({"error": "Invalid date format"}, status=400)

        source_currencies = Currency.objects.values_list("code", flat=True).distinct()

        response_data = {}

        date_format = "%Y-%m-%d"
        for source_currency in source_currencies:
            rates_data = get_currency_rates_data(
                source_currency,
                start_date.strftime(date_format),
                end_date.strftime(date_format),
            )
            response_data[source_currency] = rates_data

        formatted_data = format_data_for_chart(response_data)
        return JsonResponse({"data": formatted_data})
