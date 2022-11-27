from django.http import HttpResponse


def index(request):
    return HttpResponse("Don't stray to the dark side")
