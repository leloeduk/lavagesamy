from django.urls import path
from . import views

app_name = 'gestion'  # Namespace pour l'application

urlpatterns = [
    # Page d'accueil
    path('', views.home, name='home'),

    # Dashboard
    path('dashboard/', views.dashboard_view, name='dashboard'),

    # Factures
    path('factures/', views.facture_list, name='facture_list'),
    path('factures/creer/', views.facture_create, name='facture_create'),
    path('factures/<int:pk>/', views.facture_detail, name='facture_detail'),

    # Services
    path('services/', views.service_list, name='service_list'),
    path('services/creer/', views.service_create, name='service_create'),
    path('services/<int:pk>/modifier/', views.service_update, name='service_update'),
    path('services/<int:pk>/supprimer/', views.service_delete, name='service_delete'),
]
