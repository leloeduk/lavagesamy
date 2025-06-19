from django.urls import path
from . import views

app_name = 'gestion'

urlpatterns = [

    # dashbord 
   path('dashboard/', views.DashboardView.as_view(), name='dashboard'),
    
    # Factures
    path('factures/', views.FactureListView.as_view(), name='facture-list'),
    path('factures/nouvelle/', views.FactureCreateView.as_view(), name='facture-create'),
    path('factures/<int:pk>/', views.FactureDetailView.as_view(), name='facture-detail'),
  
    # Services
    path('services/', views.ServiceListView.as_view(), name='service-list'),
    path('services/nouveau/', views.ServiceCreateView.as_view(), name='service-create'),
   
    # Statistiques
    path('statistiques/mensuelles/', views.StatistiquesMensuellesView.as_view(), name='stats-mensuelles'),
    
    # Utilisateurs
    path('utilisateurs/', views.UserListView.as_view(), name='utilisateur-list'),
    path('utilisateurs/nouveau/', views.UserCreateView.as_view(), name='utilisateur-create'),
   
]