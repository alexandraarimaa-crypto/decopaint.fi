# google_shopping/apps.py

from django.apps import AppConfig

class GoogleShoppingConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'google_shopping'
    
    def ready(self):
        """
        Import signals when app is ready.
        """
        try:
            import google_shopping.signals  # noqa
            #print("Google Shopping signals registered successfully")
        except Exception as e:
            print(f"Error registering Google Shopping signals: {e}")