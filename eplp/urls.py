from django.conf.urls import patterns, include, url

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',

    url(r'^$', 'eplp_rec.views.index', name='index'),
    url(r'^artists/', 'eplp_rec.views.top_artists', name='top_artists'),
    url(r'^recommendations/', 'eplp_rec.views.recommendations', name='recommendations'),
    url(r'^matches/', 'eplp_rec.views.match_recommendations', name='matches'),

    url(r'^admin/', include(admin.site.urls)),
)
