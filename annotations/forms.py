from django.contrib.auth.forms import UserChangeForm
from annotations.models import *
from django.utils.translation import ugettext_lazy as _
from django.core.exceptions import ValidationError
from django import forms
from django.forms import widgets
from crispy_forms.helper import FormHelper

from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import ReadOnlyPasswordHashField

import autocomplete_light

# class CrispyUserChangeForm(UserChangeForm):
# 	password = None		# This field was set in the Form ancestor, so exclude
# 						#  is insufficient.
#
# 	class Meta:
# 		model = User
# 		exclude = ['password', 'groups', 'user_permissions', 'last_login',
# 				   'is_staff', 'is_superuser', 'date_joined', 'is_active',
# 				   'username']
#
# 	def __init__(self, *args, **kwargs):
# 		super(CrispyUserChangeForm, self).__init__(*args, **kwargs)
# 		self.helper = FormHelper(self)


class RegistrationForm(forms.Form):
	"""
	Gives user form of signup and validates it.
	"""
	username = forms.RegexField(regex=r'^\w+$', widget=forms.TextInput(attrs=dict(required=True, max_length=30)), label=_("Username"), error_messages={ 'invalid': _("This value must contain only letters, numbers and underscores.") })
	email = forms.EmailField(widget=forms.TextInput(attrs=dict(required=True, max_length=30)), label=_("Email address"))
	password1 = forms.CharField(widget=forms.PasswordInput(attrs=dict(required=True, max_length=30, render_value=False)), label=_("Password"))
	password2 = forms.CharField(widget=forms.PasswordInput(attrs=dict(required=True, max_length=30, render_value=False)), label=_("Password (again)"))

	def clean_username(self):
		"""
		Validates username.
		"""
		try:
			user = VogonUser.objects.get(username__iexact=self.cleaned_data['username'])
		except VogonUser.DoesNotExist:
			return self.cleaned_data['username']
		raise forms.ValidationError(_("The username already exists. Please try another one."))

	def clean(self):
		"""
		Validates the values inserted in Password and Confirm Password field are same.
		"""
		if 'password1' in self.cleaned_data and 'password2' in self.cleaned_data:
			if self.cleaned_data['password1'] != self.cleaned_data['password2']:
				raise forms.ValidationError(_("The two password fields did not match."))
		return self.cleaned_data

def validatefiletype(file):
	"""
	Validates type of uploaded file.

	Parameters
	----------
	file : file
		The file that is uploaded.

	Raises
	------
	ValidationError
		Raises this exception if uploaded file is neither plain text nor PDF
	"""
	if file.content_type != 'application/pdf' and file.content_type != 'text/plain':
		raise ValidationError('Please choose a plain text file or PDF file')

class UploadFileForm(forms.Form):
	title = forms.CharField(label='Title:', max_length=255, required=True)
	ispublic = forms.BooleanField(label='Make this text public?',
				required=False,
				help_text='By checking this box you affirm that you have the\n'+
						  'right to make this file publicly available.')
	filetoupload = forms.FileField(label='Choose a file (plain text or PDF):',
				required=True,
				validators=[validatefiletype])
	datecreated = forms.DateField(label='Date created:',
				required=False,
				widget=forms.TextInput(attrs={'class':'datepicker'}))


class UserCreationForm(forms.ModelForm):

    password1 = forms.CharField(label='Password', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Password confirmation', widget=forms.PasswordInput)

    class Meta:
        model = VogonUser
        fields = ('full_name', 'email', 'affiliation', 'location', 'link', )

    def clean_password2(self):
        # Check that the two password entries match
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Passwords don't match")
        return password2

    def save(self, commit=True):
        # Save the provided password in hashed format
        user = super(UserCreationForm, self).save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user


class UserChangeForm(forms.ModelForm):
    password = ReadOnlyPasswordHashField()

    class Meta:
        model = VogonUser
        fields = ('full_name', 'email', 'affiliation', 'location', 'link', )

    def clean_password(self):
        # Regardless of what the user provides, return the initial value.
        # This is done here, rather than on the field, because the
        # field does not have access to the initial value
        return self.initial["password"]



class AutocompleteWidget(widgets.TextInput):
	def _format_value(self, value):
		if self.is_localized:
			return formats.localize_input(value)
		return value

	def render(self, name, value, attrs=None):
		if value is None:
			value = ''
		final_attrs = self.build_attrs(attrs, type=self.input_type, name=name)
		if value != '':
			# Only add the 'value' attribute if a value is non-empty.
			final_attrs['value'] = widgets.force_text(self._format_value(value))

		classes = 'autocomplete'
		if 'class' in final_attrs:
			classes += ' ' + final_attrs['class']

		return widgets.format_html('<input class="' + classes + '"{} />', widgets.flatatt(final_attrs))


class ConceptField(forms.CharField):
	queryset = Concept.objects.all()

	def label_from_instance(self, obj):
		"""
		The ``_concept`` field should be populated with the :class:`.Concept`\s
		id.
		"""
		return obj.id

	def to_python(self, value):
		if value in self.empty_values:
			return None
		try:
			key = 'pk'
			value = self.queryset.get(**{key: value})
		except (ValueError, TypeError, self.queryset.model.DoesNotExist):
			raise ValidationError(self.error_messages['invalid_choice'], code='invalid_choice')
		return value


class TemplateChoiceField(forms.ChoiceField):
	def label_from_instance(self, obj):
		"""
		The ``_concept`` field should be populated with the :class:`.Concept`\s
		id.
		"""
		return obj.id


class ChoiceIntegerField(forms.IntegerField):
	"""
	An :class:`.IntegerField` that plays well with the :class:`.Select` widget.
	"""

	def to_python(self, value):
		"""
		Validates that int() can be called on the input. If not, return -1
		(default value for ..._relationtemplate_internal_id fields).
		"""
		try:
			value = value.split(':')[-1]
			int(value)
			return super(ChoiceIntegerField, self).to_python(value)
		except ValueError:
			return -1


class RelationTemplateForm(forms.ModelForm):
	class Meta:
		model = RelationTemplate
		exclude = []


class RelationTemplatePartForm(forms.ModelForm):
	"""

	TODO: make sure that there are no self-loops in inter-part references.
	"""
	source_concept = ConceptField(widget=widgets.HiddenInput(), required=False)
	source_concept_text = forms.CharField(widget=AutocompleteWidget(attrs={'target': 'source_concept'}), required=False)

	predicate_concept = ConceptField(widget=widgets.HiddenInput(), required=False)
	predicate_concept_text = forms.CharField(widget=AutocompleteWidget(attrs={'target': 'predicate_concept'}), required=False)

	object_concept = ConceptField(widget=widgets.HiddenInput(), required=False)
	object_concept_text= forms.CharField(widget=AutocompleteWidget(attrs={'target': 'object_concept'}), required=False)

	source_relationtemplate_internal_id = ChoiceIntegerField(required=False)
	object_relationtemplate_internal_id = ChoiceIntegerField(required=False)

	internal_id = forms.IntegerField(widget=widgets.HiddenInput())

	class Media:
		js = ('annotations/js/autocomplete.js',)
		css = {
			'all': ['annotations/css/autocomplete.css']
		}

	class Meta:
		model = RelationTemplatePart
		exclude = [
			'source_relationtemplate',
			'object_relationtemplate',
			'part_of',
			]
		autocomplete_fields = (    # TODO: do we need this?
			'source_concept',
			'predicate_concept',
			'object_concept',
			)

	def __init__(self, *args, **kwargs):
		super(RelationTemplatePartForm, self).__init__(*args, **kwargs)

		# We need a bit of set-up for angular data bindings to work properly
		#  on the form.
		# Angular can't handle hyphens, so we use underscores.
		self.safe_prefix = self.prefix.replace('-', '_')

		self.ident = self.prefix.split('-')[-1]
		self.fields['source_node_type'].widget = widgets.Select(choices=self.fields['source_node_type'].widget.choices, attrs={'ng-model': "selection_{id}_source_node_type".format(id=self.safe_prefix)})
		self.fields['predicate_node_type'].widget = widgets.Select(choices=self.fields['predicate_node_type'].widget.choices, attrs={'ng-model': "selection_{id}_predicate_node_type".format(id=self.safe_prefix)})
		self.fields['object_node_type'].widget = widgets.Select(choices=self.fields['object_node_type'].widget.choices, attrs={'ng-model': "selection_{id}_object_node_type".format(id=self.safe_prefix)})

		self.fields['source_relationtemplate_internal_id'].widget = widgets.Select(attrs={'ng-init': "selection_{id}_subject_relationtemplate = relation_options[0]".format(id=self.safe_prefix), 'ng-options': 'item as item for item in relation_options', 'ng-model': "selection_{id}_subject_relationtemplate".format(id=self.safe_prefix)})
		self.fields['object_relationtemplate_internal_id'].widget = widgets.Select(attrs={'ng-init': "selection_{id}_object_relationtemplate = relation_options[0]".format(id=self.safe_prefix), 'ng-options': 'item as item for item in relation_options', 'ng-model': "selection_{id}_object_relationtemplate".format(id=self.safe_prefix)})

		self.fields['internal_id'].initial = self.ident

		for fname, field in self.fields.iteritems():
			if 'prompt_text' in fname:
				continue
			field.widget.attrs.update({'class': 'form-control'})

			if 'target' in field.widget.attrs:
				field.widget.attrs['target'] = 'id_form-{0}-'.format(self.ident) + field.widget.attrs['target']

		# self.fields['source_type'].widget = widgets.Select(choices=self.fields['source_type'].widget.choices, attrs={'ng-show': "source_node_type_{id} == 'TP'".format(id=inst)})
		# self.fields['source_concept'].widget = widgets.Select(choices=self.fields['source_concept'].widget.choices, attrs={'ng-show': "source_node_type_{id} == 'CO'".format(id=inst)})
		# self.fields['source_relationtemplate'].widget = widgets.Select(choices=self.fields['source_relationtemplate'].widget.choices, attrs={'ng-show': "source_node_type_{id} == 'RE'".format(id=inst)})

	def clean(self, *args, **kwargs):
		super(RelationTemplatePartForm, self).clean(*args, **kwargs)

		# print self.cleaned_data
