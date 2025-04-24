from django import forms


class ScrapFacebookGroupForm(forms.Form):
    group_url = forms.CharField(label="Group Url", max_length=100)
    cookies = forms.CharField(label="Cookies", widget=forms.Textarea)


class SendFirstMessageForm(forms.Form):
    username = forms.CharField(label="Username", max_length=100)
    cookies = forms.CharField(label="Cookies", widget=forms.Textarea)
    message = forms.CharField(label="Message", widget=forms.Textarea)