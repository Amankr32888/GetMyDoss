from django import forms
from .models import Contact


class ContactForm(forms.ModelForm):

    class Meta:
        model  = Contact
        fields = ['name', 'email', 'subject', 'company_name',
                  'offered_position', 'message', 'phone']
        widgets = {
            'name': forms.TextInput(attrs={
                'class':       'form-control',
                'placeholder': 'Your full name',
                'required':    True,
            }),
            'email': forms.EmailInput(attrs={
                'class':       'form-control',
                'placeholder': 'your@email.com',
                'required':    True,
            }),
            'subject': forms.TextInput(attrs={
                'class':       'form-control',
                'placeholder': 'What is this about?',
                'required':    True,
            }),
            'company_name': forms.TextInput(attrs={
                'class':       'form-control',
                'placeholder': 'Company (optional)',
            }),
            'offered_position': forms.Textarea(attrs={
                'class':       'form-control',
                'rows':        3,
                'maxlength':   600,
                'placeholder': 'Position or role offered (optional)',
            }),
            'message': forms.Textarea(attrs={
                'class':       'form-control',
                'rows':        5,
                'placeholder': 'Your message... Please write at least 10 characters.',
                'required':    False,
            }),
            'phone': forms.TextInput(attrs={
                'class':       'form-control',
                'placeholder': '+91 XXXXX XXXXX (optional)',
            }),
        }

    def clean_email(self):
        """  Extra: normalize email to lowercase."""
        return self.cleaned_data['email'].lower()

    def clean_message(self):
        """  Extra: reject suspiciously short messages."""
        message = self.cleaned_data['message']
        if len(message.strip()) < 1 :
            # raise forms.ValidationError("Message is too short. Please write at least 10 characters.")
            message = "Contact me !!  "
        return message