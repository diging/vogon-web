from django.contrib import admin

# Register your models here.
from goat.models import *


class IdentitySystemAdmin(admin.ModelAdmin):
    pass


class IdentityAdmin(admin.ModelAdmin):
    pass


class ConceptAdmin(admin.ModelAdmin):
    pass


class AuthorityAdmin(admin.ModelAdmin):
    pass

class SearchResultAdmin(admin.ModelAdmin):
    pass

admin.site.register(IdentitySystem, IdentitySystemAdmin)
admin.site.register(Identity, IdentityAdmin)
admin.site.register(Concept, ConceptAdmin)
admin.site.register(Authority, AuthorityAdmin)
