from django.views.generic import TemplateView
from django.urls import path
from . import views

app_name = "app"
urlpatterns = [
    path("", views.CarpoolListView.as_view(), name="index"),
    path(
        "student/signup_and_login",
        views.StudentSignUpAndLoginView.as_view(),
        name="signup_and_login_student",
    ),
    path(
        "driver/signup_and_login",
        views.DriverSignUpAndLoginView.as_view(),
        name="signup_and_login_driver",
    ),
    path("logout/", views.logout_view, name="logout"),
    path("profile/", views.ProfileView.as_view(), name="profile"),
    path(
        "password_change/",
        views.MyPasswordChangeView.as_view(),
        name="password_change",
    ),
    path("aboutus/", views.aboutus_view, name="aboutus"),
    path("carpools/", views.CarpoolListView.as_view(), name="carpools"),
    path("carpool_list_region/", views.carpool_list_region, name="carpools_region"),
    path(
        "carpool/history/",
        views.CarpoolHistoryListView.as_view(),
        name="carpool_history",
    ),
    path("carpool/create/", views.carpool_create, name="carpool_create"),
    path("carpool/<int:pk>", views.CarpoolDetailView.as_view(), name="carpool-detail"),
    path(
        "carpool/change_status/<int:pk>",
        views.carpool_change_status_view,
        name="carpool_change_status",
    ),
    path(
        "carpool/update_status/<int:pk>",
        views.carpool_update_status_view,
        name="carpool_update_status",
    ),
    path("price/", views.PriceView.as_view(), name="price"),
    path("drivers/", views.DriverListView.as_view(), name="drivers"),
    path("driver/<int:pk>", views.DriverReviewView.as_view(), name="driver_detail"),
    path("comment/delete/<int:pk>", views.delete_comment_view, name="delete_comment"),
    path("comment/edit/<int:pk>", views.edit_comment_view, name="edit_comment"),
    path("comment/create/", views.CommentCreateView.as_view(), name="comment_create"),
    path(
        "nothing/",
        TemplateView.as_view(template_name="app/nothing.html"),
        name="nothing",
    ),
]
