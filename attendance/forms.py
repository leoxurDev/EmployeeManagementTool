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
            'pin_code': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g., 1234', 'maxlength': '4'}),
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
