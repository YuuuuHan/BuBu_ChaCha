from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from .models import Carfare, Profile, Carpool, Comment, Car, User, Profile
from datetime import date, timedelta

User = get_user_model()

profile_common_fields = ["name", "sex", "phone_num"]


class SignUpForm(UserCreationForm):
    class Meta:
        model = User
        fields = ["username", "password1", "password2"]


class LoginForm(AuthenticationForm):
    username = forms.CharField(widget=forms.TextInput(attrs={"placeholder": "帳號"}))
    password = forms.PasswordInput()

    def confirm_login_allowed(self, user):
        if not user.is_active:
            raise ValidationError(
                _("This account is inactive."),
                code="inactive",
            )


class StudentForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = profile_common_fields


class DriverForm(forms.ModelForm):
    cert_expirydate = forms.DateField(
        widget=forms.DateInput(
            format=("%Y-%m-%d"),
            attrs={
                "type": "date",
                "class": "form-control",
                "min": date.today(),
            },
        ),
    )

    class Meta:
        model = Profile
        # 補上車子資訊
        fields = profile_common_fields + ["company", "cert_code", "cert_expirydate"]


class CarpoolForm(forms.ModelForm):
    date = forms.DateField(
        widget=forms.DateInput(
            format=("%Y-%m-%d"),
            attrs={
                "type": "date",
                "class": "form-control",
                "min": date.today(),
                "max": date.today() + timedelta(days=30),
            },
        ),
    )

    time = forms.TimeField(
        widget=forms.TimeInput(
            format=("%H:%M"),
            attrs={"type": "time", "class": "form-control"},
        ),
    )

    class Meta:
        model = Carpool
        fields = ["date", "time", "carfare", "lower_passengers", "passengers"]
        widgets = {
            "lower_passengers": forms.NumberInput(
                attrs={
                    "min": "1",
                    "max": "5",
                }
            ),
            "carfare": forms.Select(attrs={"class": "form-control"}),
        }


class CarpoolFilterForm(forms.Form):
    class MyModelChoiceField(forms.ModelChoiceField):
        def label_from_instance(self, obj):
            return f"{str(obj.departure):　>7} → {str(obj.arrival):　<7}"

    carfare = MyModelChoiceField(queryset=Carfare.objects, required=False)
    date = forms.DateField(
        widget=forms.DateInput(
            format=("%Y-%m-%d"),
            attrs={
                "type": "date",
                "min": date.today(),
                "value": date.today().strftime("%Y-%m-%d"),
            },
        ),
    )
    time = forms.TimeField(
        widget=forms.TimeInput(
            format=("%H:%M"),
            attrs={
                "type": "time",
            },
        ),
        required=False,
    )
    already_in = forms.IntegerField(
        widget=forms.NumberInput(attrs={"min": "0", "max": "9", "value": "0"})
    )
    has_driver = forms.BooleanField(required=False)
    has_vacancy = forms.BooleanField(initial=True, required=False)


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ["score", "content"]


class CarForm(forms.ModelForm):
    class Meta:
        widgets = {
            "capacity": forms.NumberInput(
                attrs={
                    "max": "9",
                    "min": "1",
                }
            ),
        }
        model = Car
        fields = ["capacity", "plate", "type"]
