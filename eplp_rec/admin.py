from django.contrib import admin

# Register your models here.
from models import Artist,Profile,RecommendedArtist,RecommendedMatch

admin.site.register(Artist)
admin.site.register(Profile)
admin.site.register(RecommendedArtist)
admin.site.register(RecommendedMatch)
