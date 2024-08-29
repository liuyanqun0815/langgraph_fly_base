from django import forms


class FileUploadForm(forms.Form):
    file = forms.FileField()
    upload_type = forms.ChoiceField(choices=[('general', 'General'), ('qa', 'QA')])
    collection_name = forms.CharField()


class SearchForm(forms.Form):
    collection_name = forms.CharField(label='集合名称', required=True)
    query_type = forms.ChoiceField(label='查询类型', required=True,
                                   choices=[('vector', '向量查询'), ('hybrid_search', '混合查询'),
                                            ('keyword_search', '关键字查询')])
    file_name = forms.CharField(label='文件名称', required=False)
    query = forms.CharField(label='查询内容', required=True)
