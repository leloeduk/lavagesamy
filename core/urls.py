from django.urls import path
from . import views

urlpatterns = [
    path('', views.splash_screen, name='splash'),
    path('login/', views.login_view, name='login'),
    path('signup/', views.signup_view, name='signup'),
    path('logout/', views.logout_view, name='logout'),
]