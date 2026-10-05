from django.core.mail import EmailMessage
from django.conf import settings
from django.template.loader import render_to_string
from .models import CourseRegistration

def send_course_registration_email(registration_id):
    try:
        registration = CourseRegistration.objects.get(id=registration_id)
    except CourseRegistration.DoesNotExist:
        return

    # Send email to admin
    subject = f"Uusi kurssi-ilmoittautuminen: {registration.course.title}"
    message = render_to_string('services/emails/quote_request_admin.html', { # Reusing template or creating new one?
        # Ideally we should create a new template for courses, but for now let's reuse/adapt.
        # Wait, the prompt said "Create new app courses". I should probably create a new template.
        'quote_request': registration, # The template likely expects 'quote_request' variable
        'is_course': True, # Flag to differentiate in template if needed
    })
    
    # Let's create a dedicated template for course registration emails later. 
    # For now, I will point to a new template 'courses/emails/registration_admin.html' which I will create.
    
    message = render_to_string('courses/emails/registration_admin.html', {
        'registration': registration,
    })

    from_email = settings.DEFAULT_FROM_EMAIL
    recipient_list = [settings.DEFAULT_FROM_EMAIL]  # Send to admin

    email = EmailMessage(subject, message, from_email, recipient_list)
    
    # Attach files
    for f in registration.files.all():
        email.attach(f.file.name, f.file.read())

    email.content_subtype = "html"
    email.send()
