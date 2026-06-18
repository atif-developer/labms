from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import FileResponse, Http404
from django.utils import timezone
from django.db.models import Q
from .models import TestCategory, Test, Customer, TestOrder, OrderTest, Notification
from .forms import TestCategoryForm, TestForm, CustomerForm, TestOrderForm, UploadResultForm
from .services import notify_result_ready, calculate_order_total, check_all_results_uploaded
from accounts.models import User


# ─── Test Category ───────────────────────────────────────────────────────────

@login_required
def category_list(request):
    if not request.user.is_admin:
        messages.error(request, 'Access denied.')
        return redirect('dashboard')

    categories = TestCategory.objects.all()

    search = request.GET.get('search', '').strip()
    if search:
        categories = categories.filter(name__icontains=search)

    categories = categories.order_by('name')

    return render(request, 'tests_mgmt/category_list.html', {
        'categories': categories,
        'page_title': 'Test Categories',
        'filters': {
            'search': search,
        }
    })


@login_required
def category_create(request):
    if not (request.user.is_admin or request.user.is_lab_manager):
        return redirect('dashboard')
    form = TestCategoryForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Category created.')
        return redirect('category_list')
    return render(request, 'tests_mgmt/category_form.html', {'form': form, 'title': 'Add Category'})


@login_required
def category_edit(request, pk):
    if not (request.user.is_admin or request.user.is_lab_manager):
        return redirect('dashboard')
    cat = get_object_or_404(TestCategory, pk=pk)
    form = TestCategoryForm(request.POST or None, instance=cat)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Category updated.')
        return redirect('category_list')
    return render(request, 'tests_mgmt/category_form.html', {'form': form, 'title': 'Edit Category'})


# ─── Tests ───────────────────────────────────────────────────────────────────

@login_required
def test_list(request):
    if request.user.is_admin:
        tests = Test.objects.select_related('category', 'laboratory').all()
    elif request.user.is_lab_manager:
        try:
            lab = request.user.laboratory
            tests = Test.objects.filter(
                laboratory=lab
            ).select_related('category', 'laboratory')
        except Exception:
            tests = Test.objects.none()
    else:
        tests = Test.objects.none()

    search = request.GET.get('search', '').strip()
    category_id = request.GET.get('category', '').strip()

    if search:
        tests = tests.filter(name__icontains=search)
    if category_id:
        tests = tests.filter(category__id=category_id)

    tests = tests.order_by('name')
    categories = TestCategory.objects.all()

    return render(request, 'tests_mgmt/test_list.html', {
        'tests': tests,
        'categories': categories,
        'page_title': 'Tests',
        'filters': {
            'search': search,
            'category': category_id,
        }
    })


@login_required
def test_create(request):
    if not (request.user.is_admin or request.user.is_lab_manager):
        messages.error(request, 'Access denied.')
        return redirect('dashboard')

    if request.method == 'POST':
        form = TestForm(request.POST, user=request.user)
        if form.is_valid():
            test = form.save(commit=False)
            if request.user.is_lab_manager:
                try:
                    test.laboratory = request.user.laboratory
                except Exception:
                    messages.error(request, 'No laboratory found for your account.')
                    return redirect('dashboard')
            test.save()
            messages.success(request, 'Test added successfully.')
            return redirect('test_list')
        else:
            messages.error(request, 'Please fix the errors below.')
    else:
        form = TestForm(user=request.user)

    return render(request, 'tests_mgmt/test_create.html', {
        'form': form,
        'page_title': 'Add Test',
    })


@login_required
def test_edit(request, pk):
    if not (request.user.is_admin or request.user.is_lab_manager):
        return redirect('dashboard')
    test = get_object_or_404(Test, pk=pk)
    form = TestForm(request.POST or None, instance=test, user=request.user)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Test updated.')
        return redirect('test_list')
    return render(request, 'tests_mgmt/test_form.html', {'form': form, 'title': 'Edit Test'})


# ─── Customers ───────────────────────────────────────────────────────────────

@login_required
def customer_list(request):
    if request.user.is_admin:
        customers = Customer.objects.select_related('user', 'laboratory').all()
    elif request.user.is_lab_manager:
        try:
            lab = request.user.laboratory
            customer_ids_from_orders = TestOrder.objects.filter(
                laboratory=lab
            ).values_list('customer_id', flat=True).distinct()
            customers = Customer.objects.filter(
                Q(laboratory=lab) | Q(id__in=customer_ids_from_orders)
            ).select_related('user').distinct()
        except Exception:
            customers = Customer.objects.none()
    else:
        customers = Customer.objects.none()

    search = request.GET.get('search', '').strip()
    gender = request.GET.get('gender', '').strip()
    if search:
        customers = customers.filter(
            Q(user__first_name__icontains=search) |
            Q(user__last_name__icontains=search) |
            Q(patient_id__icontains=search) |
            Q(user__phone__icontains=search)
        )
    if gender:
        customers = customers.filter(user__gender=gender)
    customers = customers.order_by('-id')
    return render(request, 'tests_mgmt/customer_list.html', {
        'customers': customers,
        'page_title': 'Patients',
        'filters': {'search': search, 'gender': gender},
    })


@login_required
def customer_create(request):
    if not (request.user.is_admin or request.user.is_lab_manager):
        messages.error(request, 'Access denied.')
        return redirect('dashboard')

    if request.method == 'POST':
        form = CustomerForm(request.POST)
        if form.is_valid():
            import uuid
            username = f"customer_{uuid.uuid4().hex[:8]}"
            user = User.objects.create_user(
                username=username,
                password=uuid.uuid4().hex,
                role=User.ROLE_CUSTOMER,
                first_name=form.cleaned_data['first_name'],
                last_name=form.cleaned_data['last_name'],
                email=form.cleaned_data.get('email', ''),
                phone=form.cleaned_data.get('phone', ''),
                whatsapp_number=form.cleaned_data.get('whatsapp_number', ''),
                gender=form.cleaned_data.get('gender', ''),
                date_of_birth=form.cleaned_data.get('date_of_birth'),
                address=form.cleaned_data.get('address', ''),
                is_active=True,
            )
            customer = Customer(
                user=user,
                blood_group=form.cleaned_data.get('blood_group', ''),
            )
            if request.user.is_lab_manager:
                try:
                    customer.laboratory = request.user.laboratory
                except Exception:
                    pass
            customer.save()
            messages.success(request, f'Patient added. ID: {customer.patient_id}')
            return redirect('customer_list')
        else:
            messages.error(request, 'Please fix errors below.')
    else:
        form = CustomerForm()

    return render(request, 'tests_mgmt/customer_form.html', {
        'form': form,
        'page_title': 'Add Patient',
    })


@login_required
def customer_detail(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    if request.user.is_lab_manager:
        try:
            lab = request.user.laboratory
            if customer.laboratory != lab:
                messages.error(request, 'Access denied.')
                return redirect('customer_list')
        except Exception:
            messages.error(request, 'Access denied.')
            return redirect('customer_list')
    orders = customer.orders.select_related('laboratory').order_by('-created_at')
    return render(request, 'tests_mgmt/customer_detail.html', {
        'customer': customer,
        'orders': orders,
        'page_title': 'Patient Detail',
    })


@login_required
def customer_edit(request, pk):
    if not (request.user.is_admin or request.user.is_lab_manager):
        return redirect('dashboard')
    customer = get_object_or_404(Customer, pk=pk)
    form = CustomerForm(request.POST or None, instance=customer)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Customer updated.')
        return redirect('customer_detail', pk=pk)
    return render(request, 'tests_mgmt/customer_edit.html', {'form': form, 'customer': customer})


# ─── Orders ──────────────────────────────────────────────────────────────────

@login_required
def order_list(request):
    if request.user.is_admin:
        orders = TestOrder.objects.select_related('customer__user', 'laboratory').all()
    elif request.user.is_lab_manager:
        try:
            lab = request.user.laboratory
            orders = TestOrder.objects.filter(laboratory=lab).select_related('customer__user', 'laboratory')
        except Exception:
            orders = TestOrder.objects.none()
    else:
        orders = TestOrder.objects.none()

    order_number = request.GET.get('order_number', '').strip()
    patient_name = request.GET.get('patient_name', '').strip()
    status = request.GET.get('status', '').strip()
    date_from = request.GET.get('date_from', '').strip()
    date_to = request.GET.get('date_to', '').strip()

    if order_number:
        orders = orders.filter(order_number__icontains=order_number)
    if patient_name:
        orders = orders.filter(
            Q(customer__user__first_name__icontains=patient_name) |
            Q(customer__user__last_name__icontains=patient_name) |
            Q(customer__patient_id__icontains=patient_name)
        )
    if status:
        orders = orders.filter(status=status)
    if date_from:
        orders = orders.filter(created_at__date__gte=date_from)
    if date_to:
        orders = orders.filter(created_at__date__lte=date_to)
    orders = orders.order_by('-created_at')

    return render(request, 'tests_mgmt/order_list.html', {
        'orders': orders,
        'page_title': 'Test Orders',
        'status_choices': TestOrder.STATUS_CHOICES,
        'filters': {
            'order_number': order_number,
            'patient_name': patient_name,
            'status': status,
            'date_from': date_from,
            'date_to': date_to,
        },
    })


@login_required
def order_create(request):
    if not (request.user.is_admin or request.user.is_lab_manager):
        messages.error(request, 'Access denied.')
        return redirect('dashboard')
    form = TestOrderForm(request.POST or None, user=request.user)
    if request.method == 'POST' and form.is_valid():
        order = form.save(commit=False)
        order.ordered_by = request.user
        order.save()
        # Create OrderTest entries
        total = 0
        for test in form.cleaned_data['tests']:
            ot = OrderTest.objects.create(order=order, test=test, price=test.price)
            total += test.price
        order.total_amount = total
        order.save(update_fields=['total_amount'])
        messages.success(request, f'Order {order.order_number} created.')
        return redirect('order_detail', pk=order.pk)
    tests_qs = form.fields['tests'].queryset.select_related('category').order_by('category__name', 'name')
    lab = None
    if request.user.is_lab_manager:
        try:
            lab = request.user.laboratory
        except Exception:
            pass
    selected_tests = form.data.getlist('tests') if request.method == 'POST' else []
    return render(request, 'tests_mgmt/order_create.html', {
        'form': form,
        'tests_qs': tests_qs,
        'lab': lab,
        'selected_tests': selected_tests,
    })


@login_required
def order_detail(request, pk):
    order = get_object_or_404(TestOrder, pk=pk)
    user = request.user
    # Access control
    if user.is_customer:
        try:
            if order.customer.user != user:
                messages.error(request, 'Access denied.')
                return redirect('order_list')
        except Exception:
            return redirect('order_list')
    elif user.is_lab_manager:
        try:
            if order.laboratory.manager != user:
                messages.error(request, 'Access denied.')
                return redirect('order_list')
        except Exception:
            return redirect('order_list')
    order_tests = order.order_tests.select_related('test').all()
    return render(request, 'tests_mgmt/order_detail.html', {
        'order': order,
        'order_tests': order_tests,
        'status_choices': TestOrder.STATUS_CHOICES,
        'page_title': f'Order {order.order_number}',
    })


@login_required
def order_update_status(request, pk):
    if not (request.user.is_admin or request.user.is_lab_manager):
        messages.error(request, 'Access denied.')
        return redirect('dashboard')
    order = get_object_or_404(TestOrder, pk=pk)
    if request.method == 'POST':
        new_status = request.POST.get('status')
        valid_statuses = [s[0] for s in TestOrder.STATUS_CHOICES]
        if new_status in valid_statuses:
            order.status = new_status
            order.save(update_fields=['status'])
            messages.success(request, f'Order status updated to {order.get_status_display()}.')
        return redirect('order_detail', pk=pk)
    return redirect('order_detail', pk=pk)


@login_required
def upload_result(request, order_id, order_test_id):
    if not (request.user.is_admin or request.user.is_lab_manager):
        messages.error(request, 'Access denied.')
        return redirect('dashboard')
    order = get_object_or_404(TestOrder, pk=order_id)
    order_test = get_object_or_404(OrderTest, pk=order_test_id, order=order)
    form = UploadResultForm(request.POST or None, request.FILES or None, instance=order_test)
    if request.method == 'POST' and form.is_valid():
        ot = form.save(commit=False)
        ot.save()
        # Check if all results done → complete order & notify
        if check_all_results_uploaded(order):
            order.status = TestOrder.STATUS_COMPLETED
            order.save(update_fields=['status'])
            if not order.whatsapp_notified:
                sent = notify_result_ready(order)
                if sent:
                    order.whatsapp_notified = True
                    order.save(update_fields=['whatsapp_notified'])
                    messages.success(request, 'Results uploaded and customer notified via WhatsApp!')
                else:
                    messages.warning(request, 'Results uploaded but WhatsApp notification failed. Check notification log.')
            else:
                messages.success(request, 'Result uploaded successfully.')
        else:
            messages.success(request, 'Result uploaded. Waiting for remaining tests.')
        return redirect('order_detail', pk=order_id)
    return render(request, 'tests_mgmt/upload_result.html', {
        'form': form, 'order': order, 'order_test': order_test
    })


@login_required
@login_required
def resend_whatsapp(request, pk):
    if not (request.user.is_admin or request.user.is_lab_manager):
        messages.error(request, 'Access denied.')
        return redirect('dashboard')
    order = get_object_or_404(TestOrder, pk=pk)
    if request.method == 'POST':
        order.whatsapp_notified = False
        order.save(update_fields=['whatsapp_notified'])
        sent = notify_result_ready(order)
        if sent:
            messages.success(request, 'WhatsApp notification resent successfully!')
        else:
            messages.error(request, 'Failed to resend WhatsApp. Check customer WhatsApp number.')
    return redirect('order_detail', pk=pk)


@login_required
def download_result(request, order_id, order_test_id):
    order = get_object_or_404(TestOrder, pk=order_id)
    user = request.user
    # Access control
    if user.is_customer:
        try:
            if order.customer.user != user:
                raise Http404
        except Exception:
            raise Http404
    order_test = get_object_or_404(OrderTest, pk=order_test_id, order=order)
    if not order_test.result_file:
        messages.error(request, 'No result file available.')
        return redirect('order_detail', pk=order_id)
    return FileResponse(order_test.result_file.open(), as_attachment=True)


@login_required
def notification_log(request):
    if not request.user.is_admin:
        return redirect('dashboard')
    notifications = Notification.objects.select_related('user', 'order').order_by('-created_at')
    return render(request, 'tests_mgmt/notification_log.html', {'notifications': notifications})
