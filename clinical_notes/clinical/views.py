import sys,json
from django.shortcuts import render, redirect
from django.http import JsonResponse

sys.path.append("..")
from SECRET import CLIENT_ID, CLIENT_SECRET

import requests, datetime, pytz

# Create your views here.

def index(request):
    if 'error' in request.GET:
        raise ValueError('Error authorizing application: %s' % request.GET['error'])

    #data = {}
    #if('expires_timestamp' in request.session and (request.session['expires_timestamp']) > datetime.datetime.now()):
    #    print("Expired!")
    #    refreshing = True
    #    data = {
    #        'refresh_token': request.GET['refresh_token'],
    #        'grant_type': 'refresh_token',
    #        'client_id': CLIENT_ID,
    #        'client_secret': CLIENT_SECRET,
    #    }
    #else:
    data = {
        'code': request.GET['code'],
        'grant_type': 'authorization_code',
        'redirect_uri': 'https://127.0.0.1:8000/clinical/',
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
    }

    response = requests.post('https://drchrono.com/o/token/', data=data)
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
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()

        for result in data['results']:
            id = result['id']
            name = result['first_name'] + ' ' + result['last_name']
            patients[id] = name
        url = data['next']

    fields = {}
    url = 'https://drchrono.com/api/clinical_note_templates'
    while url:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()

        for result in data['results']:
            template_id = result['id']
            template_name = result['name']
            template_url = 'https://drchrono.com/api/clinical_note_field_types?clinical_note_template=%s' % (template_id)
            while template_url:
                response = requests.get(template_url, headers=headers)
                response.raise_for_status()
                template_data = response.json()

                for template_result in template_data['results']:
                    id = template_result['id']
                    name = template_result['name']
                    fields[str(id) + '-' + str(template_id)] = template_name + ' - ' + name
                template_url = template_data['next']
        url = data['next']

    response = requests.get('https://drchrono.com/api/users/current', headers=headers);
    response.raise_for_status()
    data = response.json()

    # You can store this in your database along with the tokens
    username = data['username']

    fields = sorted(fields.items(), key=lambda x: x[0])

    context = {'patients': patients, 'fields': fields, 'username': username}
    return render(request, 'clinical.html', context)

def values(request, patient_id=None, template_id=None, field_id=None):
    vals = {}

    headers = {
        'Authorization': 'Bearer %s' % request.session['access_token'],
    }

    date_end = (datetime.date.today() - datetime.timedelta(6*365/12)).isoformat()
    date_range = date_end + '/' + datetime.date.today().isoformat()

    url = 'https://drchrono.com/api/clinical_notes?date_range=%s&patient=%s' % (date_range, patient_id)
    while url:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()

        for result in data['results']:
            appointment_id = result['appointment'] # Lookup appointment date @ end, if appointment has field. 
            field_value_url = 'https://drchrono.com/api/clinical_note_field_values?appointment=%s&clinical_note_field=%s&clinical_note_template=%s' % (appointment_id, field_id, template_id)

            # Extract data from url
            response = requests.get(field_value_url, headers=headers)
            response.raise_for_status()
            field_value_data = response.json()

            appointment_url = 'https://drchrono.com/api/appointments/%s' % (appointment_id)
            response = requests.get(appointment_url, headers=headers)
            response.raise_for_status()
            appointment_data = response.json()

            date = appointment_data['scheduled_time']

            if(int(field_value_data['count'])!=1):
                continue # Should have only recieved a single response. 
                     #   0 or more than 1 returned. 
            else:
                vals[date] = field_value_data['results'][0]['value']

        url = data['next']

    vals = {'vals': sorted(vals.items(), key=lambda x: x[0])}
    return JsonResponse(vals)
