from django import forms
from .models import Hospital
import re
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model
from .models import UserProfile


class HospitalForm(forms.ModelForm):
    lat_deg = forms.CharField(max_length=2, label="Latitude Degrees")
    lat_min = forms.CharField(max_length=5, label="Latitude Minutes")
    lat_ns = forms.ChoiceField(
        choices=[("N", "N"), ("S", "S")], label="Latitude Direction", initial="N"
    )

    long_deg = forms.CharField(max_length=3, label="Longitude Degrees")
    long_min = forms.CharField(max_length=5, label="Longitude Minutes")
    long_ew = forms.ChoiceField(
        choices=[("E", "E"), ("W", "W")], label="Longitude Direction", initial="W"
    )

    class Meta:
        model = Hospital
        fields = [
            "hospital_name",
            "hospital_id",
            "city",
            "state",
            "faa_identifier",
            "airport",
            "description",
        ]
        widgets = {
            "description": forms.Textarea(
                attrs={
                    "rows": 4,  # Initial number of rows
                    "cols": 40,  # Initial number of columns
                    "style": "resize: both;",  # Allow resizing both horizontally and vertically
                }
            ),
        }

    def clean_hospital_id(self):
        hospital_id = self.cleaned_data.get("hospital_id")
        if not re.match(r"^[A-Za-z0-9]{3,5}$", hospital_id):
            raise forms.ValidationError(
                "Hospital ID must be 3-5 characters long, capital letters or numbers only."
            )
        return hospital_id

    def clean_city(self):
        city = self.cleaned_data.get("city")
        if not re.match(r"[A-Za-z ]", city):
            raise forms.ValidationError("City name must contain only letters.")
        return city

    def clean_state(self):
        state = self.cleaned_data.get("state")
        if not re.match(r"^[A-Za-z]{2}$", state):
            raise forms.ValidationError("State must be exactly 2 capitalized letters.")
        return state

    def clean_faa_identifier(self):
        faa_identifier = self.cleaned_data.get("faa_identifier", "")
        if faa_identifier and not re.match(r"^[A-Za-z0-9]{3,4}$", faa_identifier):
            raise forms.ValidationError(
                "FAA Identifier must be between 3-4 capitalized letters and/or numbers."
            )
        return faa_identifier

    def clean_description(self):
        description = self.cleaned_data.get("description", "")
        return description

    def clean_lat_deg(self):
        lat_deg = self.cleaned_data.get("lat_deg")
        if not re.match(r"^[0-9][0-9]$", lat_deg):
            raise forms.ValidationError(
                "Latitude degrees must be a 2 digit number between 00 and 90."
            )
        return lat_deg

    def clean_lat_min(self):
        lat_min = self.cleaned_data.get("lat_min")
        if not re.match(r"^[0-5][0-9]\.[0-9][0-9]$", lat_min):
            raise forms.ValidationError(
                "Latitude minutes must be a 4 digit number between 00.00 and 59.99."
            )
        return lat_min

    def clean_long_deg(self):
        long_deg = self.cleaned_data.get("long_deg")
        if not re.match(r"^[0-1][0-9][0-9]$", long_deg):
            raise forms.ValidationError(
                "Longitude degrees must be a 3 digit number between 000 and 180."
            )
        return long_deg

    def clean_long_min(self):
        long_min = self.cleaned_data.get("long_min")
        if not re.match(r"^[0-5][0-9]\.[0-9][0-9]$", long_min):
            raise forms.ValidationError(
                "Longitude minutes must be a 4 digit number between 00.00 and 59.99."
            )
        return long_min

    def save(self, commit=True):
        hospital = super().save(commit=False)

        # Convert NoneType faa_identifier and description to empty strings
        if hospital.faa_identifier is None:
            hospital.faa_identifier = ""

        if hospital.description is None:
            hospital.description = ""

        # Combine latitude and longitude parts into full strings
        hospital.latitude = f"{self.cleaned_data['lat_deg']} {self.cleaned_data['lat_min']} {self.cleaned_data['lat_ns']}"
        hospital.longitude = f"{self.cleaned_data['long_deg']} {self.cleaned_data['long_min']} {self.cleaned_data['long_ew']}"

        if commit:
            hospital.save()
        return hospital


class CSVImportForm(forms.Form):
    csv_file = forms.FileField(label="Select CSV File", required=True)


User = get_user_model()


class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(required=True)
    last_name = forms.CharField(required=True)

    class Meta:
        model = User
        fields = [
            "username",
            "email",
            "first_name",
            "last_name",
            "password1",
            "password2",
        ]


class UserUpdateForm(forms.ModelForm):
    email = forms.EmailField()

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name']


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['profile_picture']
