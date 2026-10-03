"""Accounts views — registration, login, profile."""

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from apps.accounts.forms import LoginForm, ProfileEditForm, RegisterForm
from apps.accounts.models import ResponsibleGamblingSettings
from apps.wallet.models import Wallet


def register_view(request):
    if request.user.is_authenticated:
        return redirect('sportsbook:home')

    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Create wallet and RG settings on registration
            Wallet.objects.create(user=user, currency=user.currency)
            ResponsibleGamblingSettings.objects.create(user=user)
            login(request, user)
            messages.success(request, 'Welcome! Your account has been created.')
            return redirect('sportsbook:home')
    else:
        form = RegisterForm()

    return render(request, 'accounts/register.html', {'form': form, 'page_title': 'Create Account'})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('sportsbook:home')

    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            user = authenticate(
                request,
                username=form.cleaned_data['username'],
                password=form.cleaned_data['password'],
            )
            if user is not None:
                if user.account_status == 'active':
                    login(request, user)
                    next_url = request.GET.get('next', 'sportsbook:home')
                    return redirect(next_url)
                else:
                    messages.error(request, 'Your account has been suspended. Please contact support.')
            else:
                messages.error(request, 'Invalid username or password.')
    else:
        form = LoginForm()

    return render(request, 'accounts/login.html', {'form': form, 'page_title': 'Sign In'})


def logout_view(request):
    logout(request)
    return redirect('sportsbook:home')


@login_required
def profile_view(request):
    context = {
        'page_title': 'My Profile',
    }
    return render(request, 'accounts/profile.html', context)


@login_required
def profile_edit_view(request):
    if request.method == 'POST':
        form = ProfileEditForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully.')
            return redirect('accounts:profile')
    else:
        form = ProfileEditForm(instance=request.user)

    return render(request, 'accounts/profile_edit.html', {
        'form': form,
        'page_title': 'Edit Profile',
    })


@login_required
def responsible_gambling_view(request):
    rg, _ = ResponsibleGamblingSettings.objects.get_or_create(user=request.user)
    context = {
        'rg': rg,
        'page_title': 'Responsible Gambling',
    }
    return render(request, 'accounts/responsible_gambling.html', context)
