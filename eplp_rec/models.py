from django.db import models
from django.contrib.auth.models import User
from tools import EplpInterface
import hashlib

class Artist(models.Model):
    name        = models.CharField(max_length=255)
    mbid        = models.CharField(max_length=255)
    url         = models.CharField(max_length=255)
    image       = models.CharField(max_length=255)
    listeners   = models.IntegerField(default=0)

    def __unicode__(self):
        return self.name

    @staticmethod
    def get_artist(name,eplp_interface):

        if name in ["Agent Ribbons","Bachelorette"]:
            return None

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
            if len(artist.url) > 250:
                print "***LONG URL "+artist.url
                artist.url = "#"

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
            if obj:
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

                if similar_artist:
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

    def generate_recommendation_matches(self,match_user):

        u1_recs = RecommendedArtist.objects.filter(user=self)
        u2_recs = RecommendedArtist.objects.filter(user=match_user)

        u2_lookup = {}
        for rec in u2_recs:
            u2_lookup[rec.artist.name]={"num":rec.occurences,"match":rec.match_sum}

        for rec in u1_recs:
            if rec.artist.name in u2_lookup:
                print rec.artist.name+" in both"
                listeners = rec.artist.listeners
                u1_match_sum = rec.match_sum
                u2_match_sum = u2_lookup[rec.artist.name]['match']
                match_sum = u1_match_sum+u2_match_sum
                eplp_score = rec.artist.listeners / (match_sum ** 3)
                occurences = rec.occurences + u2_lookup[rec.artist.name]['num']
                print listeners,u1_match_sum,u2_match_sum,match_sum,eplp_score,occurences
                RecommendedMatch.add_recommendation_match(
                                                            self,
                                                            match_user,
                                                            rec.artist,
                                                            occurences,
                                                            match_sum,
                                                            eplp_score,
                                                            u1_match_sum,
                                                            u2_match_sum)


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

class RecommendedMatch(models.Model):
    pair_key    = models.CharField(max_length=255)
    
    u1          = models.ForeignKey(Profile,related_name="user1",null=True)
    u2          = models.ForeignKey(Profile,related_name="user2",null=True)

    artist      = models.ForeignKey(Artist)

    u1_match_sum= models.FloatField(default=0)
    u2_match_sum= models.FloatField(default=0)

    occurences  = models.IntegerField(default=0)
    match_sum   = models.FloatField(default=0)
    eplp_score  = models.FloatField(default=0)

    def __unicode__(self):
        return self.u1.lastfm_username+" | "+self.u2.lastfm_username+" | "+self.artist.name

    @property
    def get_percents(self):
        u1_per = (self.u1_match_sum / self.match_sum)*100
        u2_per = 100 - u1_per
        return (u1_per,u2_per)

    @staticmethod
    def generate_pair_key(u1,u2):
        key_builder = []
        key_builder.append(u1.lastfm_username)
        key_builder.append(u2.lastfm_username)
        key_builder.sort()

        pair_key = ""
        for name in key_builder:
            pair_key += name+"|"
        return pair_key

    @staticmethod
    def add_recommendation_match(u1,u2,artist,occurences,match_sum,eplp_score,u1_match_sum,u2_match_sum):

        u1_match_percent = (u1_match_sum/match_sum)*100

        if u1_match_percent >= 30 and u1_match_percent <= 70:

            pair_key = RecommendedMatch.generate_pair_key(u1,u2)

            rec,created = RecommendedMatch.objects.get_or_create(
                                                            pair_key=pair_key,
                                                            artist=artist,
                                                            )

            if created:
                rec.u1 = u1
                rec.u2 = u2
                rec.occurences = occurences
                rec.match_sum = match_sum
                rec.eplp_score = eplp_score
                rec.u1_match_sum = u1_match_sum
                rec.u2_match_sum = u2_match_sum
                rec.save()

            return rec

        return None


