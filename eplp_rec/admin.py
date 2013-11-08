from django.contrib import admin

# Register your models here.
from models import Artist,Profile,RecommendedArtist

admin.site.register(Artist)
admin.site.register(Profile)
admin.site.register(RecommendedArtist)
