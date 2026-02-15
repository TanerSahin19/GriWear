
from django import forms 
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm


class LoginForm(forms.Form):
    username = forms.CharField (
    widget=forms.TextInput(attrs={'class':'form-control'})) 
    password = forms.CharField (max_length=150, 
    widget=forms.PasswordInput(attrs={'class':'form-control'}))
    
class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=False,
    widget=forms.EmailInput(attrs={'class':'form-control', 'placeholder':'E-posta'}))
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if "class" not in field.widget.attrs:
                field.widget.attrs["class"] = "form-control"
         
  
    