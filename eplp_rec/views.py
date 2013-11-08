from django.shortcuts import render
from models import Artist, Profile

def index(request):
    context = {
        'test':'test',
    }
    return render(request, 'main.html', context)

def top_artists(request):

    profile = Profile.objects.get(user__username="renton_django")

    artists = profile.top_artists.all()
    print artists
    print "test"

    context={
        'artists':artists,
    }

    return render(request,'top_artists.html',context)
