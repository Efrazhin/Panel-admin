from django.urls import path
from . import views
from django.contrib.auth import views as auth_views


urlpatterns = [
    path('', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('registro/', views.registro_view, name='registro'),
    
    # Dashboards por rol
    path('dashboard', views.dashboard_view, name='dashboard'),
    path('admin/dashboard/',views.admin_dashboard, name='admin_dashboard'),
    path('admin/dashboard-psico/',views.dashboard_psico, name='psico_dashboard'),
    path('admin/dashboard-secre/', views.secretaria_dashboard, name='secretaria_dashboard'),
    # Página de acceso denegado
    path('acceso-denegado/', views.acceso_denegado, name='acceso_denegado'),
    path('verificar-codigo/', views.verificar_codigo_view, name='verificar_codigo'),

    path('password-reset/', views.password_reset_request, name='password_reset'),
    path('password-reset/verify/', views.password_reset_verify, name='password_reset_verify'),
    path('password-reset/complete/', views.password_reset_complete, name='password_reset_complete'),
    path('reset-password/<uidb64>/<token>/', views.password_reset_change, name='password_reset_change'),
    
]