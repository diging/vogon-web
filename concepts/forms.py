from django import forms
from concepts.models import Concept, Type


class ConceptForm(forms.ModelForm):
    class Meta:
        model = Concept
        fields = ('label', 'description', 'typed', )
