from django.core.mail import EmailMessage
from django.conf import settings
from django.template.loader import render_to_string
from .models import QuoteRequest

def send_quote_request_email(quote_request_id):
    try:
        quote_request = QuoteRequest.objects.get(id=quote_request_id)
        
        # Prepare email context
        email_context = {
            'service': quote_request.service,
            'name': quote_request.name,
            'email': quote_request.email,
            'phone': quote_request.phone,
            'message': quote_request.message,
        }
        
        # 1. Send email to Admin
        subject = f"Tarjouspyyntö palvelusta: {quote_request.service.title}"
        admin_message = render_to_string('services/emails/quote_request_admin.html', email_context)
        
        admin_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'info@decopaint.fi')
        
        email_msg = EmailMessage(
            subject=subject,
            body=admin_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[admin_email],
            reply_to=[quote_request.email]
        )
        email_msg.content_subtype = "html"
        
        # Attach files
        for attached_file in quote_request.files.all():
            try:
                # Open the file and attach it
                with attached_file.file.open('rb') as f:
                    content = f.read()
                    email_msg.attach(attached_file.file.name.split('/')[-1], content, 'application/octet-stream')
            except Exception as e:
                print(f"Error attaching file {attached_file.id}: {e}")
            
        email_msg.send()
        
        # 2. Send confirmation to User
        user_subject = f"Vastaanotimme tarjouspyyntösi: {quote_request.service.title}"
        user_message = render_to_string('services/emails/quote_request_user.html', email_context)
        
        user_email_msg = EmailMessage(
            subject=user_subject,
            body=user_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[quote_request.email]
        )
        user_email_msg.content_subtype = "html"
        user_email_msg.send()
        
        return f"Quote request emails sent for request {quote_request_id}"
        
    except QuoteRequest.DoesNotExist:
        return f"QuoteRequest {quote_request_id} not found"
    except Exception as e:
        return f"Failed to send quote emails for request {quote_request_id}: {str(e)}"
