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

def fields(request, patient_id=None):
	clinical_fields = {}

	# TODO: Iterate over 6month periods to get all records. 
	headers = {
		'Authorization': 'Bearer %s' % request.session['access_token'],
	}

	date_end = (datetime.date.today() - datetime.timedelta(6*365/12)).isoformat()
	date_range = date_end + '/' + datetime.date.today().isoformat()
	url = 'https://drchrono.com/api/clinical_notes?date_range=%s&patient=%s' % (date_range, patient_id)
	while url:
		data = requests.get(url, headers=headers).json()
		for result in data['results']:
			appointment_id = result['appointment']
			sections = result['clinical_note_sections']
			for section in sections:
				template_id = section['clinical_note_template']
				
				template_url = 'https://drchrono.com/api/clinical_note_field_types?clinical_note_template=%s' % (template_id)
				while template_url:
					field_data = requests.get(template_url, headers=headers).json()
					for field_result in field_data['results']:
						field = field_result['name']
						id = field_result['id']
						data_type = field_result['data_type']
					
						if data_type in ["Checkbox", "String", "TwoStrings", "NullCheckbox"]:
							clinical_fields[field] = id
					template_url = field_data['next']
		url = data['next']

	return JsonResponse(clinical_fields)

def values(request, patient_id=None, field_id=None):
	vals = {}

	headers = {
		'Authorization': 'Bearer %s' % request.session['access_token'],
	}

	date_end = (datetime.date.today() - datetime.timedelta(6*365/12)).isoformat()
	date_range = date_end + '/' + datetime.date.today().isoformat()

	url = 'https://drchrono.com/api/clinical_notes?date_range=%s&patient=%s' % (date_range, patient_id)
	while url:
		data = requests.get(url, headers=headers).json()
		for result in data['results']:
			appointment_id = result['appointment'] # Lookup appointment date @ end, if appointment has field. 
			sections = result['clinical_note_sections']
			for section in sections:
				template_id = section['clinical_note_template']
				
				template_url = 'https://drchrono.com/api/clinical_note_field_types?clinical_note_template=%s' % (template_id)
				while template_url:
					field_data = requests.get(template_url, headers=headers).json()
					for field_result in field_data['results']:
						if int(field_result['id'])==int(field_id):
							appointment_url = 'https://drchrono.com/api/appointments/%s' % (template_id)
							appointment_data = requests.get(appointment_url, headers=headers).json()
							print(appointment_url)
							print(appointment_data)
							date = appointment_data['results'][0]['scheduled_time']

							field_value_url = 'https://drchrono.com/api/clinical_note_fields_values/%s?clinical_note_field' % (appointment_id, field_id)
							field_value_data = requests.get(field_value_url, headers=headers).json()

							for val in field_value_data['results']:
								# Store value and date. 
								# Each appointment (ie. day) should have unique values
								vals[date] = val['value'] 

					template_url = field_data['next']
			
		url = data['next']

	return JsonResponse(vals)
