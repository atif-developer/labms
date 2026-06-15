from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Laboratory
from .forms import LabRegistrationForm, LaboratoryUpdateForm
from accounts.models import User


def lab_register(request):
    form = LabRegistrationForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        lab_name = form.cleaned_data['lab_name']
        user = User.objects.create_user(
            username=form.cleaned_data['username'],
            password=form.cleaned_data['password'],
            role=User.ROLE_LAB_MANAGER,
            is_active=False,
        )
        Laboratory.objects.create(
            name=lab_name,
            city=form.cleaned_data['city'],
            address=form.cleaned_data['address'],
            phone=form.cleaned_data['phone'],
            manager=user,
        )
        messages.success(request, "Registration submitted. Wait for admin approval.")
        return redirect('login')
    return render(request, 'lab/lab_register.html', {'form': form})


@login_required
def lab_list(request):
    if not request.user.is_admin:
        return redirect('dashboard')
    labs = Laboratory.objects.select_related('manager').all()
    return render(request, 'lab/lab_list.html', {'labs': labs, 'page_title': 'Laboratories'})


@login_required
def lab_detail(request, pk):
    if not request.user.is_admin:
        return redirect('dashboard')
    lab = get_object_or_404(Laboratory, pk=pk)
    return render(request, 'lab/lab_detail.html', {'lab': lab, 'page_title': lab.name})


@login_required
def lab_approve(request, pk):
    if not request.user.is_admin:
        return redirect('dashboard')
    lab = get_object_or_404(Laboratory, pk=pk)
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'approve':
            lab.status = Laboratory.STATUS_APPROVED
            lab.manager.is_active = True
            lab.manager.save()
            lab.save()
            messages.success(request, f'Laboratory "{lab.name}" has been approved.')
        elif action == 'reject':
            rejection_reason = request.POST.get('rejection_reason', '').strip()
            lab.status = Laboratory.STATUS_REJECTED
            lab.rejection_reason = rejection_reason
            lab.save()
            messages.success(request, f'Laboratory "{lab.name}" has been rejected.')
    return redirect('lab_detail', pk=pk)


@login_required
def my_lab(request):
    if not request.user.is_lab_manager:
        messages.error(request, 'Access denied.')
        return redirect('dashboard')
    try:
        lab = request.user.laboratory
    except Laboratory.DoesNotExist:
        messages.error(request, 'No laboratory associated with your account.')
        return redirect('dashboard')
    form = LaboratoryUpdateForm(request.POST or None, instance=lab)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Laboratory information updated.')
        return redirect('my_lab')
    return render(request, 'lab/my_lab.html', {'lab': lab, 'form': form})
