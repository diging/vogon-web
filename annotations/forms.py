from django.contrib.auth.forms import UserChangeForm
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _
from django.core.exceptions import ValidationError
from django import forms
from crispy_forms.helper import FormHelper

class CrispyUserChangeForm(UserChangeForm):
	password = None		# This field was set in the Form ancestor, so exclude
						#  is insufficient.

	class Meta:
		model = User
		exclude = ['password', 'groups', 'user_permissions', 'last_login',
				   'is_staff', 'is_superuser', 'date_joined', 'is_active',
				   'username']

	def __init__(self, *args, **kwargs):
		super(CrispyUserChangeForm, self).__init__(*args, **kwargs)
		self.helper = FormHelper(self)


class RegistrationForm(forms.Form):

    username = forms.RegexField(regex=r'^\w+$', widget=forms.TextInput(attrs=dict(required=True, max_length=30)), label=_("Username"), error_messages={ 'invalid': _("This value must contain only letters, numbers and underscores.") })
    email = forms.EmailField(widget=forms.TextInput(attrs=dict(required=True, max_length=30)), label=_("Email address"))
    password1 = forms.CharField(widget=forms.PasswordInput(attrs=dict(required=True, max_length=30, render_value=False)), label=_("Password"))
    password2 = forms.CharField(widget=forms.PasswordInput(attrs=dict(required=True, max_length=30, render_value=False)), label=_("Password (again)"))

    def clean_username(self):
        try:
            user = User.objects.get(username__iexact=self.cleaned_data['username'])
        except User.DoesNotExist:
            return self.cleaned_data['username']
        raise forms.ValidationError(_("The username already exists. Please try another one."))

    def clean(self):
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
	ispublic = forms.BooleanField(label='Is this public:',
				required=False,
				help_text='By checking this box you affirm that you have the\n'+
						  'right to make this file publicly available.')
	filetoupload = forms.FileField(label='Choose a file (plain text or PDF):',
				required=True,
				validators=[validatefiletype])
	datecreated = forms.DateField(label='Date created:',
				required=False,
				widget=forms.TextInput(attrs={'class':'datepicker'}))

