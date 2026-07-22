from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render


def login_view(request):
    if request.user.is_authenticated:
        return redirect("home")
    form = AuthenticationForm(request, data=request.POST or None)
    if request.method == "POST" and form.is_valid():
        login(request, form.get_user())
        return redirect("home")
    return render(request, "login.html", {"form": form})


def logout_view(request):
    logout(request)
    return redirect("login")


def home(request):
    """Root: signed-in users go to their app screen; signed-out visitors see
    the public landing page."""
    if request.user.is_authenticated:
        if request.user.is_boss:
            return redirect("boss_feed")
        return redirect("secretary_list")
    return render(request, "landing.html")
