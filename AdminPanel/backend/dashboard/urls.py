from django.urls import path
from .views import AdminDashboard

urlpatterns = [
    path('', AdminDashboard.as_view(), name="dashboard"),
]
