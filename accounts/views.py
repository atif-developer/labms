from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login as auth_login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from .models import User
from .forms import CustomerRegistrationForm, UserUpdateForm, AdminCreateUserForm
from tests_mgmt.models import Customer


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    error = None
    error_type = None
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            if user.is_active:
                auth_login(request, user)
                return redirect(request.GET.get('next', 'dashboard'))
            else:
                error = "Your account is pending admin approval. You will be notified once approved or rejected."
                error_type = "pending"
        else:
            # authenticate() returns None for inactive users — check manually to give a specific message
            try:
                existing_user = User.objects.get(username=username)
                if not existing_user.is_active and existing_user.check_password(password):
                    if existing_user.is_lab_manager:
                        try:
                            lab = existing_user.laboratory
                            if lab.status == 'rejected':
                                error = "Your lab registration has been rejected. Reason: " + (lab.rejection_reason or "Contact administrator.")
                                error_type = "rejected"
                            elif lab.status == 'pending':
                                error = "Your lab registration is pending admin approval. Please wait."
                                error_type = "pending"
                            else:
                                error = "Your account is inactive. Contact administrator."
                                error_type = "invalid"
                        except Exception:
                            error = "Your account is inactive. Contact administrator."
                            error_type = "invalid"
                    else:
                        error = "Your account is inactive. Contact administrator."
                        error_type = "invalid"
                else:
                    error = "Invalid username or password."
                    error_type = "invalid"
            except User.DoesNotExist:
                error = "Invalid username or password."
                error_type = "invalid"

    return render(request, 'accounts/login.html', {'error': error, 'error_type': error_type})


def logout_view(request):
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('login')


def register_customer(request):
    form = CustomerRegistrationForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.save()
        Customer.objects.create(user=user)
        messages.success(request, 'Account created! Please log in.')
        return redirect('login')
    return render(request, 'accounts/register.html', {'form': form})


@login_required
def profile(request):
    form = UserUpdateForm(request.POST or None, request.FILES or None, instance=request.user)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Profile updated successfully.')
        return redirect('profile')
    return render(request, 'accounts/profile.html', {'form': form})


@login_required
def dashboard(request):
    user = request.user
    context = {'user': user}

    if user.is_admin:
        from tests_mgmt.models import TestOrder, Customer as Cust
        from lab.models import Laboratory
        context.update({
            'total_customers': Cust.objects.count(),
            'total_orders': TestOrder.objects.count(),
            'pending_orders': TestOrder.objects.filter(status='pending').count(),
            'completed_orders': TestOrder.objects.filter(status='completed').count(),
            'pending_labs': Laboratory.objects.filter(status='pending').count(),
            'total_labs': Laboratory.objects.filter(status='approved').count(),
            'recent_orders': TestOrder.objects.select_related('customer__user', 'laboratory').order_by('-created_at')[:5],
        })
    elif user.is_lab_manager:
        from tests_mgmt.models import TestOrder
        try:
            lab = user.laboratory
            orders = TestOrder.objects.filter(laboratory=lab)
            context.update({
                'lab': lab,
                'total_orders': orders.count(),
                'pending_orders': orders.filter(status='pending').count(),
                'completed_orders': orders.filter(status='completed').count(),
                'recent_orders': orders.select_related('customer__user').order_by('-created_at')[:5],
            })
        except Exception:
            pass
    elif user.is_customer:
        try:
            customer = user.customer_profile
            orders = customer.orders.all()
            context.update({
                'customer': customer,
                'total_orders': orders.count(),
                'pending_orders': orders.filter(status='pending').count(),
                'completed_orders': orders.filter(status='completed').count(),
                'recent_orders': orders.select_related('laboratory').order_by('-created_at')[:5],
            })
        except Exception:
            pass

    return render(request, 'accounts/dashboard.html', context)


@login_required
def user_list(request):
    if not request.user.is_admin:
        messages.error(request, 'Access denied.')
        return redirect('dashboard')
    users = User.objects.select_related('customer_profile', 'laboratory').all().order_by('-date_joined')
    return render(request, 'accounts/user_list.html', {
        'users': users,
        'page_title': 'Users',
    })


@login_required
def create_user(request):
    if not request.user.is_admin:
        messages.error(request, 'Access denied.')
        return redirect('dashboard')
    form = AdminCreateUserForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.save()
        if user.role == User.ROLE_CUSTOMER:
            Customer.objects.get_or_create(user=user)
        messages.success(request, f'User {user.username} created successfully.')
        return redirect('user_list')
    return render(request, 'accounts/create_user.html', {'form': form})


@login_required
def toggle_user_status(request, user_id):
    if not request.user.is_admin:
        return JsonResponse({'error': 'Forbidden'}, status=403)
    user = get_object_or_404(User, id=user_id)
    user.is_active = not user.is_active
    user.save()
    return JsonResponse({'status': 'active' if user.is_active else 'inactive'})
