from django import forms
from django_countries.fields import CountryField
from django_countries.widgets import CountrySelectWidget


class CheckoutForm(forms.Form):
    street_address = forms.CharField(
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "Ул. Пушкина"}
        )
    )

    apartment_address = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Дом 1"}),
    )

    country = CountryField(blank_label="(Выберите страну)").formfield(
        widget=CountrySelectWidget(attrs={"class": "custom-select d-block w-100"})
    )

    zip = forms.CharField(widget=forms.TextInput(attrs={"class": "form-control"}))

    same_billing_address = forms.BooleanField(required=False)
    save_info = forms.BooleanField(required=False)
