from django import forms
from ..models import Currency, CurrencyExchangeRate, CurrencyProvider


class CurrencyConverterForm(forms.Form):
    source_currency = forms.ModelChoiceField(
        queryset=Currency.objects.all(),
        widget=forms.Select(attrs={"id": "id_source_currency"}),
    )
    target_currencies = forms.ModelMultipleChoiceField(
        queryset=Currency.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        label="Target Currencies",
    )
    amount = forms.DecimalField(min_value=0.01)


class CurrencyExchangeRateForm(forms.ModelForm):

    class Meta:
        model = CurrencyExchangeRate
        fields = [
            "source_currency",
            "target_currency",
            "valuation_date",
            "rate_value",
            "active",
            "provider",
        ]
        widgets = {
            "valuation_date": forms.SelectDateWidget(),
            "rate_value": forms.NumberInput(attrs={"step": "0.000001"}),
        }

    def __init__(self, *args, **kwargs):
        super(CurrencyExchangeRateForm, self).__init__(*args, **kwargs)
        self.fields["rate_value"].label = "Exchange Rate"
        self.fields["source_currency"].queryset = Currency.objects.all()
        self.fields["target_currency"].queryset = Currency.objects.all()
        self.fields["provider"].queryset = CurrencyProvider.objects.filter(active=True)

    def clean(self):
        cleaned_data = super().clean()

        source_currency = cleaned_data.get("source_currency")
        target_currency = cleaned_data.get("target_currency")

        if source_currency == target_currency:
            self.add_error(
                "target_currency", "Source and target currencies must be different."
            )

        return cleaned_data
