from django import forms


PRODUCT_QUANTITY_CHOICES = [(i, str(i)) for i in range(1, 11)]


class CartAddProductForm(forms.Form):
    """Form to add a product to the cart."""

    quantity = forms.TypedChoiceField(choices=PRODUCT_QUANTITY_CHOICES, coerce=int)
    override = forms.BooleanField(required=False, initial=False, widget=forms.HiddenInput)


class CartUpdateProductForm(forms.Form):
    """Form to update the quantity of a product in the cart."""

    quantity = forms.IntegerField(min_value=1,max_value=99,
        widget=forms.NumberInput(attrs={"class": "cart-quantity-input"}),
    )
    override = forms.BooleanField(required=False, initial=False, widget=forms.HiddenInput)