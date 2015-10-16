from django.contrib.auth.forms import UserChangeForm
from django.contrib.auth.models import User
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
