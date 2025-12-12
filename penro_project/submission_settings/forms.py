from django import forms

class ReportFileUploadForm(forms.Form):
    file = forms.FileField()
