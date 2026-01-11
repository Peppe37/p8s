"""
P8s Forms - Django-style form validation using Pydantic.

Provides:
- Form base class for custom forms
- ModelForm for auto-generated forms from Models
- Field types with HTML rendering hints
- CSRF integration

Example:
    from p8s.forms import Form, ModelForm
    from pydantic import EmailStr

    class ContactForm(Form):
        name: str
        email: EmailStr
        message: str

    class ProductForm(ModelForm):
        class Meta:
            model = Product
            fields = ["name", "price", "description"]
"""

from p8s.forms.base import Form, ModelForm
from p8s.forms.fields import (
    BooleanField,
    CharField,
    ChoiceField,
    DateField,
    DateTimeField,
    EmailField,
    FloatField,
    HiddenField,
    IntegerField,
    PasswordField,
    TextAreaField,
)

__all__ = [
    "Form",
    "ModelForm",
    "CharField",
    "EmailField",
    "IntegerField",
    "FloatField",
    "BooleanField",
    "DateField",
    "DateTimeField",
    "ChoiceField",
    "TextAreaField",
    "HiddenField",
    "PasswordField",
]
