from django import forms
from .models import Employee, DepartmentOption, AvatarEmoji, AvatarColor


class EmployeeForm(forms.ModelForm):
    department = forms.ChoiceField(
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    avatar_emoji = forms.ChoiceField(
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    avatar_color = forms.ChoiceField(
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    class Meta:
        model = Employee
        fields = ['first_name', 'last_name', 'department', 'avatar_emoji', 'avatar_color', 'pin_code']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g., Jane'}),
            'last_name': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g., Doe'}),
            'pin_code': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g., 123456', 'maxlength': '6'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Populate department choices from database
        departments = DepartmentOption.objects.filter(is_active=True).order_by('order')
        self.fields['department'].choices = [
            (d.name, d.display_value) for d in departments
        ]
        
        # Populate avatar emoji choices from database
        emojis = AvatarEmoji.objects.filter(is_active=True).order_by('order')
        self.fields['avatar_emoji'].choices = [
            (e.emoji, f"{e.emoji} {e.name}") for e in emojis
        ]
        
        # Populate avatar color choices from database
        colors = AvatarColor.objects.filter(is_active=True).order_by('order')
        self.fields['avatar_color'].choices = [
            (c.hex_code, f"{c.name} ({c.hex_code})") for c in colors
        ]


from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

class ManagerRegisterForm(UserCreationForm):
    first_name = forms.CharField(max_length=30, required=True, widget=forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g. John'}))
    last_name = forms.CharField(max_length=30, required=True, widget=forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g. Doe'}))
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'class': 'form-input', 'placeholder': 'e.g. manager@company.com'}))

    class Meta(UserCreationForm.Meta):
        model = User
        fields = UserCreationForm.Meta.fields + ('first_name', 'last_name', 'email')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs.update({'class': 'form-input'})
            if field_name == 'username':
                field.widget.attrs.update({'placeholder': 'e.g. manager'})
            elif field_name == 'first_name':
                field.widget.attrs.update({'placeholder': 'e.g. John'})
            elif field_name == 'last_name':
                field.widget.attrs.update({'placeholder': 'e.g. Doe'})
            elif field_name == 'email':
                field.widget.attrs.update({'placeholder': 'e.g. manager@company.com'})
            elif 'password' in field_name:
                field.widget.attrs.update({'placeholder': '••••••••'})

