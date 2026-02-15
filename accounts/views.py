from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required

from .forms import LoginForm, RegisterForm


def login_view(request):
    error = None

    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data["username"]
            password = form.cleaned_data["password"]
            user = authenticate(request, username=username, password=password)

            if user is not None:
                login(request, user)
                return redirect("home")
            else:
                error = "Kullanıcı adı veya şifre hatalı."
    else:
        form = LoginForm()

    return render(request, "login.html", {"form": form, "error": error})


def register_view(request):
    error = None

    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            form.save()

            username = form.cleaned_data["username"]
            password = form.cleaned_data["password1"]
            user = authenticate(request, username=username, password=password)

            if user is not None:
                login(request, user)
                return redirect("home")
            else:
                error = "Kayıt oluşturuldu ama giriş yapılamadı."
    else:
        form = RegisterForm()

    return render(request, "register.html", {"form": form, "error": error})


@login_required
def logout_view(request):
    logout(request)
    return redirect("home")
