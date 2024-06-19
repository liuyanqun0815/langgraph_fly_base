from django import forms


class DocumentForm(forms.Form):
    document = forms.FileField()
