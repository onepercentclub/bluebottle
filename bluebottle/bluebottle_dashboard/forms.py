from django import forms
from django_recaptcha.fields import ReCaptchaField


class AxesCaptchaForm(forms.Form):
    captcha = ReCaptchaField()
