import sys
from django.shortcuts import render
sys.path.append("..")
from SECRET import REDIRECT_URI, CLIENT_ID, SCOPES
from urllib import quote_plus


def index(request):
    URL = 'https://drchrono.com/o/authorize/?redirect_uri=%s&response_type=code&client_id=%s&scope=%s' % (REDIRECT_URI, quote_plus(CLIENT_ID) , quote_plus(SCOPES))
    context = {"URL": URL}
    return render(request, 'index.html', context)
