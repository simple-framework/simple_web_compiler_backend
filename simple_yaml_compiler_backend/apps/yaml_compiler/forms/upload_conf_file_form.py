from django import forms


class UploadSiteConfForm(forms.Form):
    site_config = forms.FileField()