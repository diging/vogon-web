from django import forms
from concepts.models import Concept, Type


class ConceptForm(forms.ModelForm):
    class Meta:
        model = Concept
        fields = ('label', 'description', 'typed', )


class ConceptTypeForm(forms.Form):
    typed = forms.ModelChoiceField(queryset=Type.objects.all())
