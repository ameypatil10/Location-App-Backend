from django.contrib import admin
from .models import *

# Register your models here.

admin.site.register(student)
admin.site.register(instructor)
admin.site.register(course)
admin.site.register(course_session)
admin.site.register(takes)
admin.site.register(location)
admin.site.register(lecture)
admin.site.register(router)
admin.site.register(router_location_statistic)
admin.site.register(router_location_data)
admin.site.register(attendance)
admin.site.register(tracking_data)