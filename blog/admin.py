from django.contrib import admin
from .models import BlogPost

# Register your models here.
admin.site.site_header = "Lunyamwi Admin"
admin.site.site_title = "Lunyamwi Admin Portal"
admin.site.index_title = "Welcome to Lunyamwi Admin Portal"

admin.site.register(BlogPost)