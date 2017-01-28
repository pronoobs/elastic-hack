from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.core.urlresolvers import reverse
from .models import Movie
from django.contrib.auth import logout
from .forms import *
from django.contrib import messages
from django.core.mail import send_mail
# Create your views here.
from elasticsearch import Elasticsearch
from django.shortcuts import render
import json

def advanced(request):
    form = SearchForm(request.POST or None)

    if form.is_valid():
        f1 = form.cleaned_data['title'].lower()

        f2 = form.cleaned_data['actors']

        min_rating = form.cleaned_data['minr']

        genres = form.cleaned_data['genres']

        m2 = [x.pk for x in Movie.objects.all() if x.average_rating >= min_rating]

        movies = (Movie.objects.filter(title__icontains=f1) | Movie.objects.filter(actors__in=f2)).filter(
            genre__in=genres).filter(pk__in=m2)

        context = {'movies': movies}
        return render(request, 'search_results.html', context)

    context = {
        'form': form

    }
    return render(request, "advanced_search.html", context)


def search(request):
    error = False
    if 'q' in request.GET:
        q = request.GET['q']
    es=Elasticsearch()    
    x = es.indices.get(index='hack-index', ignore=[400, 404])
    print json.dumps(x,indent=4)
    if 'status' not in x:
        print 'q= ',q
        if q == '':
            print 'here'
            x = es.search(index='hack-index', doc_type='Movie', body={"query": {"match_all": {}}})
        else:
            x = es.search(index='hack-index', doc_type='Movie', body={"query": {"match": {"plot": q}}})
        print json.dumps(x, indent=4)
        for i in x['hits']['hits']:
                print i['_id']
    movies = Movie.objects.filter(title__icontains=q)
    return render(request, 'search_results.html',
                  {'movies': movies, 'query': q})
    return HttpResponseRedirect('/')


def register_page(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            username = form.cleaned_data['username'],
            password = form.cleaned_data['password1'],
            User.objects.create_user(username=username, password=password, email=email,
                                     first_name=form.cleaned_data['name'])
            send_mail(subject='Welcome to LMDB', message='Greetings!', from_email='lab.movie.database@gmail.com',
                      recipient_list=[email])
            return HttpResponseRedirect('/')
    else:
        form = RegistrationForm()
    return render(request, 'registration/register.html', ({'form': form}))


def logout_page(request):
    logout(request)
    return HttpResponseRedirect('/')


def base(request):
    movies = Movie.objects.all()

    context = {
        'movies': movies,
        'user': request.user
    }
    return render(request, "index.html", context)


def movie_page(request, id):
    movie = get_object_or_404(Movie, id=id)
    # avg_stars = movie.objects.annotate(Avg('rating__stars'))

    context = {
        'movie': movie,
        # 'stars':avg_stars
    }
    return render(request, "movie.html", context)


def list_comments(request, id):
    movie = get_object_or_404(Movie, id=id)
    # avg_stars = movie.objects.annotate(Avg('rating__stars'))
    #print id
    context = {
        'movie': movie,
        # 'stars':avg_stars
    }
    print context
    return render(request, "all_comments.html", context)


def add_comment_to_movie(request, id):
    movie = get_object_or_404(Movie, id=id)
    x = Comment.objects.filter(movie=movie, author=request.user)
    if len(x) > 0:
        messages.error(request, "User already commented!")
        return HttpResponseRedirect('/movie/%d/' % movie.id)
    if request.method == "POST":
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.movie = movie
            comment.author = request.user
            comment.save()
            return HttpResponseRedirect('/movie/%d/' % movie.id)
    else:
        form = CommentForm()
    return render(request, 'add_comment_to_movie.html', {'form': form})
