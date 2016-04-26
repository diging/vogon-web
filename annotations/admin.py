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
    list_display = ('uri', 'title', 'created', 'addedBy', 'added')


class RelationAdmin(admin.ModelAdmin):
    list_display = ('id', 'occurs_in', 'created_by', 'created')
    def occurs_in(self, obj):
        return obj.occursIn.title
    def created_by(self, obj):
        return obj.createdBy


class RelationSetAdmin(admin.ModelAdmin):
    class Meta:
        model = RelationSet

    list_display = ('id', 'createdBy', 'occursIn', 'created')


class AppellationAdmin(admin.ModelAdmin):
    class Meta:
        model = Appellation
    list_display = ('id', 'createdBy', 'occursIn', 'created', 'interpretation',
                    'asPredicate')


admin.site.register(VogonUser, VogonUserAdmin)
admin.site.register(Appellation, AppellationAdmin)
admin.site.register(Text, TextAdmin)
admin.site.register(TextCollection)
admin.site.register(Repository)
admin.site.register(Relation, RelationAdmin)
admin.site.register(RelationSet, RelationSetAdmin)
admin.site.register(RelationTemplate)
admin.site.register(RelationTemplatePart)
admin.site.register(DateAppellation)
