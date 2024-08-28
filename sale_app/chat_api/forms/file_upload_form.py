from django import forms

class FileUploadForm(forms.Form):
    file = forms.FileField()
    upload_type = forms.ChoiceField(choices=[('general', 'General'), ('qa', 'QA')])