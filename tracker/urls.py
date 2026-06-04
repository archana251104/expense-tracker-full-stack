# tracker/urls.py

from django.urls import path # type: ignore
from django.contrib.auth import views as auth_views # type: ignore
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('register/', views.register, name='register'),
    path('login/', auth_views.LoginView.as_view(template_name='tracker/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('add/', views.add_expense, name='add_expense'),
    path('edit/<int:id>/', views.edit_expense, name='edit_expense'),
    path('delete/<int:id>/', views.delete_expense, name='delete_expense'),
    path('budget/', views.budget_settings, name='budget_settings'),
    path('export/csv/', views.export_csv, name='export_csv'),  # ← This was missing
    path('export/chart-data/', views.export_chart_data, name='export_chart_data'),
    path('profile/', views.profile, name='profile'),
    
]