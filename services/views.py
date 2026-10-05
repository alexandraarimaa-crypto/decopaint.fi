from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView
from django.views.generic.edit import FormMixin
from django.urls import reverse
from django.contrib import messages
from django.core.mail import EmailMessage
from django.conf import settings
from django.template.loader import render_to_string
from .models import Service
from .forms import QuoteRequestForm

class ServiceListView(ListView):
    model = Service
    template_name = 'services/service_list.html'
    context_object_name = 'services'
    ordering = ['-created_at']

class ServiceDetailView(FormMixin, DetailView):
    model = Service
    template_name = 'services/service_detail.html'
    context_object_name = 'service'
    form_class = QuoteRequestForm
    slug_field = 'slug'
    slug_url_kwarg = 'slug'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Add form to context if not already there (e.g. on invalid post)
        if 'form' not in context:
            context['form'] = self.get_form()
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = self.get_form()
        
        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    def form_valid(self, form):
        from django_q.tasks import async_task
        from .models import QuoteRequest, QuoteRequestFile
        
        # Extract data
        name = form.cleaned_data['name']
        email = form.cleaned_data['email']
        phone = form.cleaned_data['phone']
        message_text = form.cleaned_data['message']
        files = self.request.FILES.getlist('images')
        
        # Create QuoteRequest
        quote_request = QuoteRequest.objects.create(
            service=self.object,
            name=name,
            email=email,
            phone=phone,
            message=message_text
        )
        
        # Save attached files
        for f in files:
            QuoteRequestFile.objects.create(
                quote_request=quote_request,
                file=f
            )
            
        # Trigger async task to send emails
        async_task("services.tasks.send_quote_request_email", quote_request.id)
        
        messages.success(self.request, "Tarjouspyyntösi on lähetetty onnistuneesti! Olemme sinuun yhteydessä pian.")
        
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('services:service_detail', kwargs={'slug': self.object.slug})
