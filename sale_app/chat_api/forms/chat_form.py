from django import forms


class ChatForm(forms.Form):
    sessionId = forms.CharField(label='会话ID', required=False, widget=forms.HiddenInput())
    chat = forms.CharField(label='聊天内容', required=True)
