from __future__ import unicode_literals

from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from django.db.models import Avg
from elasticsearch import Elasticsearch
from django.forms.models import model_to_dict
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver


# Create your models here.

class Actor(models.Model):
    first_name = models.CharField(max_length=30, blank=True)
    last_name = models.CharField(max_length=40, blank=True)
    age = models.IntegerField(default='20')
    GENDER_CHOICES = (('M', 'Male'), ('F', 'Female'), )
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    def __str__(self):
        return u'%s %s' % (self.first_name, self.last_name)


class Director(models.Model):
    first_name = models.CharField(max_length=30, blank=True)
    last_name = models.CharField(max_length=40, blank=True)

    def __str__(self):
        return u'%s %s' % (self.first_name, self.last_name)


class Movie(models.Model):
    # RATINGS=((5,5),(4,4),(3,3),(2,2),(1,1))
    genres = (('action', 'ACTION'), ('comedy', 'COMEDY'), ('romance', 'ROMANCE'),
              ('thriller', 'THRILLER'), ('drama', 'DRAMA'))
    title = models.CharField(max_length=30, blank=True)
    release_date = models.DateField(blank=True)
    actors = models.ManyToManyField(Actor, blank=True)
    director = models.ForeignKey(Director, blank=True, null=True)
    genre = models.CharField(max_length=30, choices=genres, default='drama', blank=True)
    image = models.ImageField(upload_to='static/images/products', default='pictures/movie2.jpg')
    #duration = models.DurationField()
    plot = models.TextField()  #story of movie


    @property  # http://www.blog.pythonlibrary.org/2014/01/20/python-201-properties/
    def average_rating(self):
        # http://stackoverflow.com/questions/28888399/aggregate-average-of-model-field-with-foreign-key-django-rest
        r=Comment.objects.filter(movie__id=self.id).aggregate(Avg('rating')).values()[0]
        if type(r)==float:
            return int(r)
        else:
            return 0

    def __str__(self):
        return self.title


class Comment(models.Model):
    RATINGS = ((5, 5), (4, 4), (3, 3), (2, 2), (1, 1))
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE)
    #https://docs.djangoproject.com/en/1.10/topics/db/examples/many_to_one/
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.TextField()
    created_date = models.DateTimeField(default=timezone.now)
    approved_comment = models.BooleanField(default=True)
    rating = models.PositiveSmallIntegerField(default=5, choices=RATINGS)

    def approve(self):
        self.approved_comment = True
        self.save()

    def __str__(self):
        return self.text


#https://docs.djangoproject.com/en/1.10/topics/db/models/#overriding-model-methods
#Above method don't work when bulk deletion is called in admin interface
#See https://code.djangoproject.com/ticket/11022


#https://coderwall.com/p/ktdb3g/django-signals-an-extremely-simplified-explanation-for-beginners
#https://docs.djangoproject.com/en/1.9/topics/signals/
@receiver(post_save, sender=Movie)
def create_movie(sender, instance, **kwargs):
    es = Elasticsearch()
    es.index(index='hack-index', doc_type='Movie', body=model_to_dict(instance, exclude=['id','image']), id=instance.id)

@receiver(post_save, sender=Actor)
def create_actor(sender, instance, **kwargs):
    es = Elasticsearch()
    es.index(index='hack-index', doc_type='Actor', body=model_to_dict(instance, exclude=['id']), id=instance.id)


@receiver(post_save, sender=Director)
def create_director(sender, instance, **kwargs):
    es = Elasticsearch()
    es.index(index='hack-index', doc_type='Director', body=model_to_dict(instance, exclude=['id']), id=instance.id)

@receiver(post_save, sender=Comment)
def create_comment(sender, instance, **kwargs):
    es = Elasticsearch()
    es.index(index='hack-index', doc_type='Comment', body=model_to_dict(instance, exclude=['id']), id=instance.id)



@receiver(post_delete, sender=Movie)
def delete_movie(sender, instance, **kwargs):
    es = Elasticsearch()
    es.delete(index='hack-index', doc_type='Movie', id=instance.id)

@receiver(post_delete, sender=Actor)
def delete_actor(sender, instance, **kwargs):
    es = Elasticsearch()
    es.delete(index='hack-index', doc_type='Actor', id=instance.id)

@receiver(post_delete, sender=Director)
def delete_director(sender, instance, **kwargs):
    es = Elasticsearch()
    es.delete(index='hack-index', doc_type='Director', id=instance.id)

@receiver(post_delete, sender=Comment)
def delete_comment(sender, instance, **kwargs):
    es = Elasticsearch()
    es.delete(index='hack-index', doc_type='Comment', id=instance.id)    