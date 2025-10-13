from django.apps import AppConfig


class BeeConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'bee'



from django.apps import AppConfig

class YourAppNameConfig(AppConfig):
    name = 'bee'

    def ready(self):
        import bee.signals
