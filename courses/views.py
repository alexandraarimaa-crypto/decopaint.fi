from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView
from django.views.generic.edit import FormMixin
from django.urls import reverse
from django.contrib import messages
from django_q.tasks import async_task
from .models import Course, CourseRegistration, CourseRegistrationFile
from .forms import CourseRegistrationForm

class CourseListView(ListView):
    model = Course
    template_name = 'courses/course_list.html'
    context_object_name = 'courses'
    ordering = ['-created_at']

class CourseDetailView(FormMixin, DetailView):
    model = Course
    template_name = 'courses/course_detail.html'
    context_object_name = 'course'
    form_class = CourseRegistrationForm
    slug_field = 'slug'
    slug_url_kwarg = 'slug'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
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
        # Extract data
        name = form.cleaned_data['name']
        email = form.cleaned_data['email']
        phone = form.cleaned_data['phone']
        message_text = form.cleaned_data['message']
        files = self.request.FILES.getlist('images')
        
        # Create CourseRegistration
        registration = CourseRegistration.objects.create(
            course=self.object,
            name=name,
            email=email,
            phone=phone,
            message=message_text
        )
        
        # Save attached files
        for f in files:
            CourseRegistrationFile.objects.create(
                registration=registration,
                file=f
            )
            
        # Trigger async task to send emails
        async_task("courses.tasks.send_course_registration_email", registration.id)
        
        messages.success(self.request, "Ilmoittautumisesi on vastaanotettu! Olemme sinuun yhteydessä pian.")
        
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('courses:course_detail', kwargs={'slug': self.object.slug})
