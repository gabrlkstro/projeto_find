from django import forms
from .models import Profile, Mensagem

class ProfileupdateForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['image']

class MensagemForm(forms.ModelForm):
    class Meta:
        model = Mensagem
        fields = ["conteudo"]
        widgets = {
            "conteudo": forms.Textarea(attrs={
                "rows": 2,
                "placeholder": "Digite sua mensagem...",
                "class": "form-control"
            })
        }