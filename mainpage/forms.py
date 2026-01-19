from django import forms
from .models import Profile

class ProfileupdateForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['image']