"""
Tests for P8s forms module.
"""

import pytest
from datetime import date
from pydantic import EmailStr


class TestForm:
    """Test Form base class."""

    def test_form_creation(self):
        """Test creating a simple form."""
        from p8s.forms import Form

        class ContactForm(Form):
            name: str
            email: str
            message: str

        form = ContactForm(name="John", email="john@example.com", message="Hello")

        assert form.name == "John"
        assert form.email == "john@example.com"
        assert form.message == "Hello"

    def test_form_from_data_valid(self):
        """Test from_data with valid data."""
        from p8s.forms import Form

        class ContactForm(Form):
            name: str
            message: str

        form = ContactForm.from_data({"name": "John", "message": "Hello"})

        assert form.is_valid() is True
        assert form.name == "John"
        assert form.errors.all() == {}

    def test_form_from_data_invalid(self):
        """Test from_data with invalid data."""
        from p8s.forms import Form

        class ContactForm(Form):
            name: str
            message: str

        form = ContactForm.from_data({"name": "John"})  # missing message

        assert form.is_valid() is False
        assert "message" in form.errors

    def test_form_data_property(self):
        """Test data property returns dict."""
        from p8s.forms import Form

        class SimpleForm(Form):
            name: str
            age: int

        form = SimpleForm(name="John", age=30)

        data = form.data
        assert data["name"] == "John"
        assert data["age"] == 30

    def test_form_get_fields(self):
        """Test get_fields returns field metadata."""
        from p8s.forms import Form

        class SimpleForm(Form):
            name: str
            email: str
            age: int

        fields = SimpleForm.get_fields()

        assert "name" in fields
        assert "email" in fields
        assert "age" in fields
        assert fields["name"]["type"] == "text"
        assert fields["email"]["type"] == "email"  # detected from name
        assert fields["age"]["type"] == "number"


class TestFormFields:
    """Test form field types."""

    def test_char_field(self):
        """Test CharField."""
        from p8s.forms import Form, CharField

        class TestForm(Form):
            name: str = CharField(max_length=100, placeholder="Your name")

        fields = TestForm.get_fields()
        assert fields["name"]["type"] == "text"

    def test_email_field(self):
        """Test EmailField."""
        from p8s.forms import Form, EmailField

        class TestForm(Form):
            email: str = EmailField()

        form = TestForm(email="test@example.com")
        assert form.email == "test@example.com"

    def test_integer_field(self):
        """Test IntegerField."""
        from p8s.forms import Form, IntegerField

        class TestForm(Form):
            age: int = IntegerField(min_value=0, max_value=150)

        form = TestForm(age=25)
        assert form.age == 25

    def test_boolean_field(self):
        """Test BooleanField."""
        from p8s.forms import Form, BooleanField

        class TestForm(Form):
            active: bool = BooleanField()

        form = TestForm(active=True)
        assert form.active is True

        form2 = TestForm()  # default False
        assert form2.active is False

    def test_textarea_field(self):
        """Test TextAreaField."""
        from p8s.forms import Form, TextAreaField

        class TestForm(Form):
            description: str = TextAreaField(rows=10)

        fields = TestForm.get_fields()
        assert fields["description"]["type"] == "textarea"

    def test_password_field(self):
        """Test PasswordField."""
        from p8s.forms import Form, PasswordField

        class TestForm(Form):
            password: str = PasswordField(min_length=8)

        fields = TestForm.get_fields()
        assert "password" in fields.get("password", {}).get("type", "password")

    def test_choice_field(self):
        """Test ChoiceField."""
        from p8s.forms import Form, ChoiceField

        class TestForm(Form):
            status: str = ChoiceField(choices=[
                ("draft", "Draft"),
                ("published", "Published"),
            ])

        form = TestForm(status="draft")
        assert form.status == "draft"


class TestFormErrors:
    """Test form error handling."""

    def test_multiple_errors(self):
        """Test form with multiple validation errors."""
        from p8s.forms import Form

        class StrictForm(Form):
            name: str
            email: str
            age: int

        form = StrictForm.from_data({})  # all missing

        assert form.is_valid() is False
        errors = form.errors.all()
        assert len(errors) >= 1

    def test_error_get(self):
        """Test getting errors for specific field."""
        from p8s.forms import Form

        class SimpleForm(Form):
            name: str

        form = SimpleForm.from_data({})

        name_errors = form.errors.get("name")
        assert len(name_errors) > 0

    def test_error_bool(self):
        """Test errors boolean conversion."""
        from p8s.forms import Form

        class SimpleForm(Form):
            name: str

        valid_form = SimpleForm.from_data({"name": "John"})
        invalid_form = SimpleForm.from_data({})

        assert bool(valid_form.errors) is False
        assert bool(invalid_form.errors) is True


class TestModelForm:
    """Test ModelForm class."""

    def test_model_form_import(self):
        """Test ModelForm can be imported."""
        from p8s.forms import ModelForm

        assert ModelForm is not None

    def test_model_form_basic(self):
        """Test basic ModelForm usage."""
        from p8s.forms import ModelForm
        from p8s.db.base import Model
        from sqlmodel import Field

        class Product(Model, table=True):
            __tablename__ = "products_form_test"
            name: str = Field(max_length=255)
            price: float = Field(ge=0)

        class ProductForm(ModelForm):
            class Meta:
                model = Product
                fields = ["name", "price"]

        form = ProductForm.from_data({"name": "Widget", "price": 9.99})
        # Form should be able to process data
        assert form is not None
