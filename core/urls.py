from django.urls import path
from . import views
from django.http import Http404

def test_404_view(request):
    raise Http404("Page inexistante")

urlpatterns = [
    path('', views.splash_screen, name='splash'),
    path('login/', views.login_view, name='login'),
    path('signup/', views.signup_view, name='signup'),
    path('logout/', views.logout_view, name='logout'),
    path("test404/", test_404_view),
]