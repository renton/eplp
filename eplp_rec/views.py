from django.shortcuts import render
from models import Artist, Profile, RecommendedArtist, RecommendedMatch

import urllib, hashlib

def index(request):
    context = {
        'test':'test',
    }
    return render(request, 'main.html', context)

def top_artists(request):

    profile = Profile.objects.get(user__username="virtualcadet")

    artists = profile.top_artists.all()
    print artists
    print "test"

    context={
        'artists':artists,
    }

    return render(request,'top_artists.html',context)

def recommendations(request):

    profile = Profile.objects.get(user__username="virtualcadet")

    recommendations = RecommendedArtist.objects.filter(user=profile).order_by('eplp_score')[:200]
    #recommendations = RecommendedArtist.objects.filter(user=profile).order_by('-occurences')[:200]
    #recommendations = RecommendedArtist.objects.filter(user=profile).order_by('-match_sum')[:200]

    context={
        'recommendations':recommendations,
    }

    return render(request,'recommendations.html',context)

def match_recommendations(request):

    profile1 = Profile.objects.get(user__username="renton_django")
    profile2 = Profile.objects.get(user__username="virtualcadet")

    pair_key = RecommendedMatch.generate_pair_key(profile1,profile2)

    recommendations = RecommendedMatch.objects.filter(pair_key=pair_key).order_by('eplp_score')[:200]

    # Set your variables here
    email_u1 = "renlawrence@gmail.com"
    u1_pic_url = "http://www.gravatar.com/avatar/" + hashlib.md5(email_u1.lower()).hexdigest()
    email_u2 = "adrianadraws@gmail.com"
    u2_pic_url = "http://www.gravatar.com/avatar/" + hashlib.md5(email_u2.lower()).hexdigest()

    context={
        'u1_pic':u1_pic_url,
        'u2_pic':u2_pic_url,
        'recommendations':recommendations,
    }

    return render(request,'match_recommendations.html',context)
