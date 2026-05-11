from django import forms


class OrderSubmitContactForm(forms.Form):
    customer_email = forms.EmailField(
        label="E-mail",
        required=False,
        widget=forms.EmailInput(
            attrs={
                "class": "w-full rounded-xl border border-slate-300 bg-white px-3 py-2 text-sm focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-200",
                "placeholder": "např. klient@email.cz",
            }
        ),
    )
    customer_first_name = forms.CharField(
        label="Jméno",
        required=False,
        max_length=120,
        widget=forms.TextInput(
            attrs={
                "class": "w-full rounded-xl border border-slate-300 bg-white px-3 py-2 text-sm focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-200",
                "placeholder": "Jméno",
            }
        ),
    )
    customer_last_name = forms.CharField(
        label="Příjmení",
        required=False,
        max_length=120,
        widget=forms.TextInput(
            attrs={
                "class": "w-full rounded-xl border border-slate-300 bg-white px-3 py-2 text-sm focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-200",
                "placeholder": "Příjmení",
            }
        ),
    )

    def clean(self):
        cleaned = super().clean()
        email = (cleaned.get("customer_email") or "").strip()
        first_name = (cleaned.get("customer_first_name") or "").strip()
        last_name = (cleaned.get("customer_last_name") or "").strip()

        if not email and not (first_name and last_name):
            raise forms.ValidationError("Vyplňte e-mail, nebo jméno a příjmení.")

        cleaned["customer_email"] = email
        cleaned["customer_first_name"] = first_name
        cleaned["customer_last_name"] = last_name
        return cleaned
