from django.shortcuts import render, redirect

import sys
sys.path.append("..")
from DATABASE_SECRETS import DATABASE, USERNAME, PASSWORD
from SECRET import CLIENT_ID, CLIENT_SECRET, REDIRECT_URI

from .models import Template, Field, Patient, Appointment

import requests, datetime, pytz, time

# Create your views here.
def index(request):
    # Check when the last update was ran. If longer than 24 hours, load the api token and execute the database populate script. 
#    return redirect('load')

#def load(request):
    if 'error' in request.GET:
        raise ValueError('Error authorizing application: %s' % request.GET['error'])

    response = requests.post('https://drchrono.com/o/token/', data = {
        'code': request.GET['code'],
        'grant_type': 'authorization_code',
        'redirect_uri': 'https://127.0.0.1:8000/clinical_improved/',
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
    return redirect('execute')

def check_for_error(url, headers):
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()

def get_patients(headers):
    patients = {}
    url = 'https://drchrono.com/api/patients'
    while url:
        data = check_for_error(url, headers)

        for result in data['results']:
            id = result['id']
            name = result['first_name'] + ' ' + result['last_name']
            patients[id] = name
        url = data['next']
    return patients

def get_appointments(patient_id, headers):
    appointments = {}
    date_end = (datetime.date.today() - datetime.timedelta(6*365/12)).isoformat()
    date_range = date_end + '/' + datetime.date.today().isoformat()

    url = 'https://drchrono.com/api/appointments?date_range=%s&patient=%s' % (date_range, patient_id)
    while url:
        data = check_for_error(url, headers)

        for result in data['results']:
            appointment_id = result['id']
            appointment_datetime = result['scheduled_time']
            appointments[appointment_id] = appointment_datetime

        url = data['next']
    return appointments

def get_templates(headers):
    templates = {}
    url = 'https://drchrono.com/api/clinical_note_templates'
    while url:
        data = check_for_error(url, headers)
        
        for result in data['results']:
            template_id = result['id']
            template_name = result['name']
            templates[template_id] = template_name

        url = data['next']
    return templates

def get_fields(template_id, headers):
    fields = {}
    url = 'https://drchrono.com/api/clinical_note_field_types?clinical_note_tempate=%s' % (template_id)
    while url:
        data = check_for_error(url, headers)
        
        for result in data['results']:
            field_id = result['id']
            field_name = result['name']
            fields[field_id] = field_name

        url = data['next']

    return fields

def get_values(appointment_id, template_id, field_id, headers):
    values = {}
    url = 'https://drchrono.com/api/clinical_note_field_values?clinical_note_field=%s&clinical_note_template=%s&appointment=%s' % (field_id, template_id, appointment_id)
    while url:
        data = check_for_error(url, headers)
        for result in data['results']:  
            value_id = result['id']
            value = result['value']
            values[value_id] = value

        url = data['next']
    return values
    

def execute(request):
    headers = {
        'Authorization': 'Bearer %s' % request.session['access_token'],
    }

    # load all template and fields
    templates = get_templates(headers)
    templates = [Template(id=id, name=name) for id, name in templates.items()]
    Template.objects.bulk_create(templates)

    seen_fields = set()
    for template_id in templates:
        fields = get_fields(template_id, headers)
        # Get all field id's which have not been seen yet. 

        # Add remaining fields to list of seen_fields
        set_ids = set([id for id, name in fields.items()])
        unique = set_ids - seen_fields

        seen_fields = seen_fields | unique
        
        fields = [Field(id=id, template_id=template_id, name=name) for id, name in fields.items() if id in unique]
        Field.objects.bulk_create(fields)
        

    patients = get_patients(headers)
    patients = [Patient(id=id, name=name) for id, name in patients.items()]
    Patient.objects.bulk_create(patients)
    # load patients into database

    # for each patient, load their appoints from the past 6 months
    for patient_id in patients:
        appointments = get_appointments(patient_id, headers)
        print(appointments)
        appointments = [Appointment(id=id, patient_id=patient_id, date_time=date_time) for id, date_time in appointments.items()]
        Appointment.objects.bulk_create(appointments)

    # For each appointment, get all the values for all templates that are avaible. 
    for appointment_id in appointments:
        for field_id, template_id, name in fields:
            values = get_values(appointment_id, template_id, field_id, headers)
            if not values:
                time.sleep(1) # if no values return (which many many will not return, wait a second so not to overdue api requests).
            else:
                print(values)
                values = [Value(id=id, patient_id=patient_id, appointment_id=appointment_id, template_id=template_id, field_id=field_id, value=value) for id, value in values.items()]
                Value.objects.bulk_create(values)
    
def view(request):
    context = {}
    patients = Patient.objects.all()
    context['patients'] = patients
    
    print(context)
    return render(request, 'clinical_improved.html', context)

# Custom api call
# Given a patient_id, return all fields which have any values filled in. 
def filled_fields(request, patient_id):
    pass
