from django.contrib import admin
from .models import ReferencePrice

admin.site.register(ReferencePrice)

from .models import TariffRate
admin.site.register(TariffRate)