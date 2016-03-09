import sys
from django.shortcuts import render, redirect
sys.path.append("..")
from SECRET import CLIENT_ID, CLIENT_SECRET

import requests, datetime, pytz

# Create your views here.

def index(request):
    if 'error' in request.GET:
        raise ValueError('Error authorizing application: %s' % request.GET['error'])
    
    response = requests.post('https://drchrono.com/o/token/', data={
        'code': request.GET['code'],
        'grant_type': 'authorization_code',
        'redirect_uri': 'https://127.0.0.1:8000/clinical/',
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
    })

    response.raise_for_status()
    data = response.json()

    # Save these in your database associated with the user
    request.session['access_token'] = data['access_token']
    request.session['refresh_token'] = data['refresh_token']
    request.session['expires_timestamp'] = str(datetime.datetime.now(pytz.utc) + datetime.timedelta(seconds=data['expires_in']))

    context = {}
    return redirect('home')

def home(request):
    headers = {
        'Authorization': 'Bearer %s' % request.session['access_token'],
    }

    patients = {}
    url = 'https://drchrono.com/api/patients'
    while url:
        data = requests.get(url, headers=headers).json()
	for result in data['results']:
		id = result['id']
		name = result['first_name'] + ' ' + result['last_name']
		patients[id] = name
	url = data['next']

    context = {'patients': patients}
    return render(request, 'clinical.html', context)
