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
    path('factures/<int:pk>/modifier/', views.FactureUpdateView.as_view(), name='facture-update'),
    path('factures/<int:pk>/supprimer/', views.FactureDeleteView.as_view(), name='facture-delete'),
    path('factures/<int:pk>/pdf/', views.facture_pdf_view, name='facture-pdf'),  

    # Services
   path('services/', views.ServiceListView.as_view(), name='service-list'),
   path('services/nouveau/', views.ServiceCreateView.as_view(), name='service-create'),
   path('services/<int:pk>/', views.ServiceDetailView.as_view(), name='service-detail'),
   path('services/<int:pk>/modifier/', views.ServiceUpdateView.as_view(), name= 'service-update'),
   path('services/<int:pk>/supprimer/', views.ServiceDeleteView.as_view(), name='confirm_delete'),

   
    # Statistiques
    path('statistiques/mensuelles/', views.StatistiquesMensuellesView.as_view(), name='stats-mensuelles'),
    
    # Utilisateurs
    path('utilisateurs/', views.UserListView.as_view(), name='utilisateur-list'),
    path('utilisateurs/nouveau/', views.UserCreateView.as_view(), name='utilisateur-create'),
    path('utilisateurs/<int:pk>/', views.UserDetailView.as_view(), name='utilisateur-detail'),
    path('utilisateurs/<int:pk>/modifier/', views.UserCreateView.as_view(), name='utilisateur-update'),
    path('utilisateurs/<int:pk>/supprimer/', views.UserDeleteView.as_view(), name='utilisateur-delete'),

]