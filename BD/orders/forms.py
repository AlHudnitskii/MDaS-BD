from django import forms

from .models import Order


class OrderCreateForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ["first_name", "last_name", "email", "address", "postal_code"]

    def __init__(self, *args, **kwargs):
        request = kwargs.pop("request", None)
        super().__init__(*args, **kwargs)

        if request and request.user.is_authenticated:
            self.initial["first_name"] = request.user.first_name
            self.initial["last_name"] = request.user.last_name
            self.initial["email"] = request.user.email

    def save(self, commit=True):
        order = super().save(commit=False)

        if self.request and self.request.user.is_authenticated:
            order.user = self.request.user
        
        if commit:
            order.save()
            self.save_m2m() 
        return order