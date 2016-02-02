from django.contrib import admin
from annotations.forms import *
from annotations.models import *


class VogonUserAdmin(UserAdmin):
    # The forms to add and change user instances
    form = UserChangeForm
    add_form = UserCreationForm

    # The fields to be used in displaying the User model.
    # These override the definitions on the base UserAdmin
    # that reference specific fields on auth.User.
    list_display = ('email', 'affiliation', 'is_admin')
    list_filter = ('is_admin',)
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {
            'fields': ('full_name', 'affiliation', 'location', 'link', )
        }),
        ('Permissions', {'fields': ('is_admin',)}),
    )
    # add_fieldsets is not a standard ModelAdmin attribute. UserAdmin
    # overrides get_fieldsets to use this attribute when creating a user.
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'full_name', 'affiliation', 'location')}
        ),
    )
    search_fields = ('email',)
    ordering = ('email',)
    filter_horizontal = ()


class TextAdmin(admin.ModelAdmin):
    list_display = ('uri', 'title', 'created','addedBy', 'added')


admin.site.register(VogonUser, VogonUserAdmin)
admin.site.register(Appellation)
admin.site.register(Text, TextAdmin)
admin.site.register(TextCollection)
admin.site.register(Repository)
admin.site.register(Relation)
