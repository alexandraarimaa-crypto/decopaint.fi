from django.utils.deprecation import MiddlewareMixin

class CartUserUpdateMiddleware(MiddlewareMixin):
    """
    Middleware to update cart user when authentication state changes
    Now simplified since prices are always updated on cart initialization
    """
    
    def process_request(self, request):
        # Store previous user state in session for comparison
        if hasattr(request, 'user') and hasattr(request, 'session'):
            previous_user_id = request.session.get('previous_user_id')
            current_user_id = request.user.id if request.user.is_authenticated else None
            
            # If user authentication state changed, update stored user ID
            if previous_user_id != current_user_id:
                request.session['previous_user_id'] = current_user_id
        
        return None