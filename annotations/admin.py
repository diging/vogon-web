from django.contrib import admin
from annotations.forms import *
from annotations.models import *
from annotations import quadriga
from annotations.tasks import submit_relationsets_to_quadriga

from itertools import groupby


class VogonUserAdmin(UserAdmin):
    # The forms to add and change user instances
    form = UserChangeForm
    add_form = UserCreationForm

    # The fields to be used in displaying the User model.
    # These override the definitions on the base UserAdmin
    # that reference specific fields on auth.User.
    list_display = ('username', 'full_name', 'email', 'affiliation', 'is_admin')
    list_filter = ('is_admin',)
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {
            'fields': ('full_name', 'affiliation', 'location', 'link',
                       'conceptpower_uri')
        }),
        ('Permissions', {'fields': ('is_admin', 'is_active')}),
    )
    # add_fieldsets is not a standard ModelAdmin attribute. UserAdmin
    # overrides get_fieldsets to use this attribute when creating a user.
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'full_name',
                       'affiliation', 'location')
        }),
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


def submit_relationsets(modeladmin, request, queryset):
    """
    Submit selected :class:`.RelationSet`\s to Quadriga.

    Will quietly skip any :class:`.RelationSet`\s that have already been
    submitted.
    """

    queryset = queryset.filter(submitted=False, pending=False)

    # Do not submit a relationset to Quadriga if the constituent interpretations
    #  involve concepts that are not resolved.
    all_rsets = [rs for rs in queryset if rs.ready()]

    project_grouper = lambda rs: getattr(rs.project, 'quadriga_id', -1)
    for project_id, project_group in groupby(sorted(all_rsets, key=project_grouper), key=project_grouper):
        for text_id, text_group in groupby(project_group, key=lambda rs: rs.occursIn.id):
            text = Text.objects.get(pk=text_id)
            for user_id, user_group in groupby(text_group, key=lambda rs: rs.createdBy.id):
                user = VogonUser.objects.get(pk=user_id)
                # We lose the iterator after the first pass, so we want a list here.
                rsets = []
                for rs in user_group:
                    rsets.append(rs.id)
                    rs.pending = True
                    rs.save()
                kwargs = {}
                if project_id:
                    kwargs.update({
                        'project_id': project_id,
                    })
                submit_relationsets_to_quadriga.delay(rsets, text.id, user.id, **kwargs)


def submit_relationsets_synch(modeladmin, request, queryset):
    """
    Submit selected :class:`.RelationSet`\s to Quadriga.

    Will quietly skip any :class:`.RelationSet`\s that have already been
    submitted.
    """

    queryset = queryset.filter(submitted=False, pending=False)

    # Do not submit a relationset to Quadriga if the constituent interpretations
    #  involve concepts that are not resolved.
    all_rsets = [rs for rs in queryset if rs.ready()]

    project_grouper = lambda rs: getattr(rs.project, 'quadriga_id', -1)
    for project_id, project_group in groupby(sorted(all_rsets, key=project_grouper), key=project_grouper):
        for text_id, text_group in groupby(project_group, key=lambda rs: rs.occursIn.id):
            text = Text.objects.get(pk=text_id)
            for user_id, user_group in groupby(text_group, key=lambda rs: rs.createdBy.id):
                user = VogonUser.objects.get(pk=user_id)
                # We lose the iterator after the first pass, so we want a list here.
                rsets = []
                for rs in user_group:
                    rsets.append(rs.id)
                    rs.pending = True
                    rs.save()
                kwargs = {}
                if project_id and project_id > 0:
                    kwargs.update({
                        'project_id': project_id,
                    })
                submit_relationsets_to_quadriga(rsets, text.id, user.id, **kwargs)


class RelationSetAdmin(admin.ModelAdmin):
    class Meta:
        model = RelationSet

    list_display = ('id', 'createdBy', 'occursIn', 'created', 'ready',
                    'pending', 'submitted', )
    actions = (submit_relationsets, submit_relationsets_synch)


class AppellationAdmin(admin.ModelAdmin):
    class Meta:
        model = Appellation
    list_display = ('id', 'createdBy', 'occursIn', 'created', 'interpretation',
                    'asPredicate')


admin.site.register(VogonUser, VogonUserAdmin)
admin.site.register(Appellation, AppellationAdmin)
admin.site.register(Text, TextAdmin)
admin.site.register(TextCollection)
admin.site.register(Relation, RelationAdmin)
admin.site.register(RelationSet, RelationSetAdmin)
admin.site.register(RelationTemplate)
admin.site.register(RelationTemplatePart)
admin.site.register(DateAppellation)
