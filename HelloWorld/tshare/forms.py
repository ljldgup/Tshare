from django import forms
 
class AddForm(forms.Form):
    r_name = forms.TimeField()
    st_date= forms.DateTimeField()
    ed_date= forms.DateTimeField()