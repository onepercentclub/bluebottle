from django import forms
from captcha.fields import ReCaptchaField


class AxesCaptchaForm(forms.Form):
    captcha = ReCaptchaField()
