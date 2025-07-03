from django.urls import path

from gestion.views.rapport_statistiques_pdf import rapport_statistiques_pdf_view
from .views import dashboard_views, facture_views, service_views, statistiques_views, user_views, pdf_views

app_name = 'gestion'

urlpatterns = [
    # Dashboard
    path('dashboard/', dashboard_views.DashboardView.as_view(), name='dashboard'),

    # Factures
    path('factures/', facture_views.FactureListView.as_view(), name='facture-list'),
    path('factures/create/', facture_views.FactureCreateView.as_view(), name='facture-create'),
    path('factures/<int:pk>/', facture_views.FactureDetailView.as_view(), name='facture-detail'),
    path('factures/<int:pk>/update/', facture_views.FactureUpdateView.as_view(), name='facture-update'),
    path('factures/<int:pk>/delete/', facture_views.FactureDeleteView.as_view(), name='facture-delete'),
   
    # Fature padf 
    path('factures/<int:pk>/pdf/', pdf_views.facture_pdf_view, name='facture-pdf'),

    # Services
    path('services/', service_views.ServiceListView.as_view(), name='service-list'),
    path('services/create/', service_views.ServiceCreateView.as_view(), name='service-create'),
    path('services/<int:pk>/', service_views.ServiceDetailView.as_view(), name='service-detail'),
    path('services/<int:pk>/update/', service_views.ServiceUpdateView.as_view(), name='service-update'),
    path('services/<int:pk>/delete/', service_views.ServiceDeleteView.as_view(), name='service-delete'),

    # Statistiques
    path('statistiques/', statistiques_views.StatistiquesView.as_view(), name='statistiques'),
    path('statistiques/rapport/pdf/', rapport_statistiques_pdf_view, name='rapport_pdf'),

    

    # Utilisateurs
    path('utilisateurs/', user_views.UserListView.as_view(), name='utilisateur-list'),
    path('utilisateurs/create/', user_views.UserCreateView.as_view(), name='utilisateur-create'),
    path('utilisateurs/<int:pk>/', user_views.UserDetailView.as_view(), name='utilisateur-detail'),
    path('utilisateurs/<int:pk>/delete/', user_views.UserDeleteView.as_view(), name='utilisateur-delete'),
]
