from django.forms import Form, CharField

class SearchForm(Form):
    id = CharField(max_length=8, required = False,)
    direccion = CharField(max_length=20, required = False)

    id.widget.attrs.update({'class': "form-control", 'id': 'id'})
    direccion.widget.attrs.update({'class': "form-control", 'id': 'direccion'})
