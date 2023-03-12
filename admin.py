from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth import get_user_model, forms as auth_forms
from .models import Place, Profile, Carfare, Carpool, Comment, Car


@admin.register(Carpool)
class CarpoolAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "date",
        "time",
        "departure",
        "arrival",
        "lower_passengers",
        "status",
    ]
    ordering = ["date", "time"]

    # def get_passengers(self, obj):
    #     return "\n".join([p.type for p in obj.passengers.all()])


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ["time", "content", "score", "critic", "criticed"]
    search_fields = ["content"]


@admin.register(Place)
class PlaceAdmin(admin.ModelAdmin):
    pass


@admin.register(Carfare)
class CarfareAdmin(admin.ModelAdmin):
    list_display = ["__str__", "departure", "arrival", "fare"]
    search_fields = ["departure", "arrival"]


User = get_user_model()


class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False


class CarInline(admin.StackedInline):
    model = Car
    can_delete = False


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    form = auth_forms.UserChangeForm
    fieldsets = (("User", {"fields": ("type",)}),) + BaseUserAdmin.fieldsets
    list_display = ["username", "type", "is_superuser"]
    search_fields = ["username", "type"]
    inlines = (ProfileInline, CarInline)
