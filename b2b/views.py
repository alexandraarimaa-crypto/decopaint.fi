from django.shortcuts import render
from shop.models import StoreSettings
from .forms import CompanyApplicationForm
from users.forms import CustomUserChangeForm
from .models import CompanyApplication
from django.http import JsonResponse
from django.utils.translation import gettext as _
from django.shortcuts import redirect
from mail.views import send_email_to_admin

def b2b_view(request):
    store_settings = StoreSettings.objects.first()
    error_message = ''
    app = None

    if request.user.is_authenticated:
        try:
            app = CompanyApplication.objects.get(user=request.user)
        except CompanyApplication.DoesNotExist:
            pass

    if request.method == 'POST':
        company_form = CompanyApplicationForm(request.POST)
        profile_form = CustomUserChangeForm(request.POST, instance=request.user)
        if company_form.is_valid() and profile_form.is_valid():
            application = company_form.save(commit=False)
            application.user = request.user
            profile_form.save()
            application.save()
            app = application

            # Send email about new application to admin
            context = {'app': app}
            admin_subject = f"Uusi B2B hakemus"
            admin_template = "company_application.html"
            send_email_to_admin(admin_subject, admin_template, context)

            return redirect('b2b:start')
    else:
        form_data = request.POST if request.method == 'POST' else None
        company_form = CompanyApplicationForm(initial=form_data)

    error_message = None
    if not company_form.is_valid():
        field_errors = company_form.errors.as_data()
        if field_errors:
            error_field = list(field_errors.keys())[0]
            error_message = f"Kenttä '{error_field}' vaaditaan."

    return render(request, 'b2b/b2b_start.html', {'app': app, 'company_terms': store_settings.company_terms, 'form': company_form, 'error_message': error_message})