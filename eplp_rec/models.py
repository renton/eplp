from django.db import models
from django.contrib.auth.models import User
from tools import EplpInterface
import hashlib
m = hashlib.md5()
m.update("000005fab4534d05api_key9a0554259914a86fb9e7eb014e4e5d52permswrite")
print m.hexdigest()

class Artist(models.Model):
    name        = models.CharField(max_length=255)
    mbid        = models.CharField(max_length=255,unique=True)
    url         = models.CharField(max_length=255)
    image       = models.CharField(max_length=255)
    listeners   = models.IntegerField(default=0)

    def __unicode__(self):
        return self.name

    @staticmethod
    def get_artist(name,eplp_interface):

        artist,created = Artist.objects.get_or_create(name=name)

        if created:
            print "\t"+name+" pulled from lastfm"
            lfm_artist = eplp_interface.lfm.get_artist(name)

            artist_mbid = lfm_artist.get_mbid()

            if artist_mbid == None:
                m = hashlib.md5()
                m.update(name.encode('utf-8'))
                artist_mbid = "eplp|"+m.hexdigest()
            artist.mbid = artist_mbid

            artist.url = lfm_artist.get_url()

            cover_image = lfm_artist.get_cover_image()
            if cover_image:
                artist.image = lfm_artist.get_cover_image()
            else:
                artist.image = ""

            artist.listeners = lfm_artist.get_listener_count()

            artist.save()
        else:
            print "\t"+name+" pulled from db"

        return artist


class Profile(models.Model):
    user            = models.OneToOneField(User)
    lastfm_username = models.CharField(max_length=256)
    top_artists     = models.ManyToManyField(Artist)

    def __unicode__(self):
        return self.lastfm_username

    def import_artists(self):
        eplp = EplpInterface()

        user = eplp.lfm.get_user(self.lastfm_username)
        library = user.get_library()
        artists_data = library.get_artists(limit=500)

        for artist_data in artists_data:
            obj = Artist.get_artist(artist_data[0].get_name(),eplp)
            print obj.name.encode('utf-8')
            self.top_artists.add(obj)
        
        self.save()

    def generate_recommendations(self):
        eplp = EplpInterface()

        artists_data = self.top_artists.all()

        my_artists = set()

        #quick lookup of users library artists
        for artist_data in artists_data:
            my_artists.add(artist_data.name)

        rec_artists = {}

        i=0
        for artist_data in artists_data:
            i+=1
            print "("+str(i)+") ==="+artist_data.name+"==="

            lfm_artist = eplp.lfm.get_artist(artist_data.name)
            similars = lfm_artist.get_similar()

            for similar in similars:
                match_value = similar[1]
                similar_artist = Artist.get_artist(similar[0].get_name(),eplp)
                name = similar_artist.name

                if name not in my_artists:

                    if name in rec_artists:
                        rec_artists[name]['num'] += 1 
                        rec_artists[name]['match'] += match_value
                    else:

                        rec_artists[name] = {
                                                'num':1,
                                                'match':match_value,
                                                'pop':similar_artist.listeners,
                                                'obj':similar_artist,
                                            }
                    print rec_artists[name]['num'], name, rec_artists[name]['match'], rec_artists[name]['pop']

        
        for k,v in rec_artists.items():
            rec_artists[k]['eplp_score'] = rec_artists[k]['pop'] / (rec_artists[k]['match'] ** 3)
            RecommendedArtist.add_recommendation(
                                self,
                                rec_artists[k]['obj'],
                                rec_artists[k]['num'],
                                rec_artists[k]['match'],
                                rec_artists[k]['eplp_score'],
                            )


class RecommendedArtist(models.Model):
    user        = models.ForeignKey(Profile)
    artist      = models.ForeignKey(Artist)

    occurences  = models.IntegerField(default=0)
    match_sum   = models.FloatField(default=0)
    eplp_score  = models.FloatField(default=0)

    def __unicode__(self):
        return self.user.lastfm_username+" | "+self.artist.name

    @staticmethod
    def add_recommendation(user,artist,occurences,match_sum,eplp_score):

        rec,created = RecommendedArtist.objects.get_or_create(
                                                        user=user,
                                                        artist=artist,
                                                    )

        if created:
            rec.occurences=occurences
            rec.match_sum=match_sum
            rec.eplp_score=eplp_score
            rec.save()

        return rec
