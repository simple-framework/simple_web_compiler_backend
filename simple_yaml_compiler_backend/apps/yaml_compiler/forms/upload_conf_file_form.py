from django import forms


class UploadSiteConfForm(forms.Form):
    file = forms.FileField()