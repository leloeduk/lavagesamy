from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from core.forms import CustomUserCreationForm
from django.contrib.auth.forms import AuthenticationForm
# from lavagesamy.gestion.models import User

def splash_screen(request):
    return render(request, 'core/splash.html')

def login_view(request):
    form = AuthenticationForm(request, data=request.POST or None)

    if request.method == 'POST':
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(request, username=username, password=password)

            if user is not None:
                login(request, user)
                return redirect('gestion:dashboard')
            else:
                messages.error(request, "Nom d'utilisateur ou mot de passe incorrect")

    return render(request, 'core/login.html', {"form": form})



from django.contrib.auth import login
from django.contrib import messages
from django.shortcuts import render, redirect

from .forms import CustomUserCreationForm

def signup_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            print("✅ Formulaire valide")
            user = form.save()
            print("🆕 Utilisateur créé :", user)

            login(request, user)  # connexion directe
            messages.success(request, "Bienvenue, votre compte a été créé avec succès.")
            return redirect('gestion:dashboard')
        else:
            print("❌ Formulaire invalide :", form.errors)
    else:
        form = CustomUserCreationForm()

    return render(request, 'core/signup.html', {'form': form})


@login_required
def logout_view(request):
    logout(request)
    return redirect('login')

