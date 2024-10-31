from django.urls import path, include
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path("", views.view_hospitals, name="view_hospitals"),
    path("add/", views.add_hospital, name="add_hospital"),
    path("edit/<str:hospital_id>/", views.edit_hospital, name="edit_hospital"),
    path("delete/<str:hospital_id>/", views.delete_hospital, name="delete_hospital"),
    path("export/cad/", views.export_cad_csv, name="export_cad_csv"),
    path(
        "export/foreflight/", views.export_foreflight, name="export_foreflight"
    ),
    path("import_csv/", views.import_csv, name="import_csv"),
    path("settings/", views.settings, name="settings"),
    path("delete_all/", views.delete_all_hospitals, name="delete_all_hospitals"),
    path(
        "accounts/", include("django.contrib.auth.urls")
    ),  # This includes login, logout, etc.
    # path("register/", views.register, name="register"),  # Register URL
    path(
        "register/<uuid:token>/",
        views.register,
        name="registration/register",
    ),
    path(
        "invalid_invite/", views.invalid_invite, name="registration/invalid_invite.html"
    ),
    path("logout/", views.custom_logout, name="logout"),
    path(
        "login/",
        auth_views.LoginView.as_view(template_name="registration/login.html"),
        name="login",
    ),
    path(
        "password-reset/",
        auth_views.PasswordResetView.as_view(
            template_name="registration/password_reset.html"
        ),
        name="password_reset",
    ),
    path(
        "password-reset/done",
        auth_views.PasswordResetDoneView.as_view(
            template_name="registration/password_reset_done.html"
        ),
        name="password_reset_done",
    ),
    path(
        "password-reset-confirm/<uidb64>/<token>/",
        auth_views.PasswordResetConfirmView.as_view(
            template_name="registration/password_reset_confirm.html"
        ),
        name="password_reset_confirm",
    ),
    path(
        "password-reset-complete/",
        auth_views.PasswordResetCompleteView.as_view(
            template_name="registration/password_reset_complete.html"
        ),
        name="password_reset_complete",
    ),
    path('create_program_ajax/', views.create_program_ajax, name='create_program_ajax'),
    path('export/county/<str:state_name>/', views.export_county, name='export_county'),
    path('get-counties/', views.get_available_counties, name='get_counties'),
    path('account/', views.account_view, name='account'),
    path('export/full-db/', views.export_full_db, name='export_full_db'),
    path('export/programs-db/', views.export_programs_db, name='export_programs_db'),
    path('import/db/', views.import_db, name='import_db'),
    path('export/program-kml/<str:program_code>/', views.export_program_kml, name='export_program_kml'),
    path('export/county-names/<str:state_name>/', views.export_county_names, name='export_county_names'),
    path('export/avionics/', views.export_avionics, name='export_avionics'),
]
