from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from api.views import health_check

urlpatterns = [
    path('', health_check, name='root-health-check'),  # GET / → {"status": "ok"}
    path('admin/', admin.site.urls),
    path('api/', include('api.urls')),
] + static(settings.MEDIA_URL, document_root=getattr(settings, 'MEDIA_ROOT', None))
