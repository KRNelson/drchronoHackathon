from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.core import serializers

import sys
sys.path.append("..")
from DATABASE_SECRETS import DATABASE, USERNAME, PASSWORD
from SECRET import CLIENT_ID, CLIENT_SECRET, REDIRECT_URI

from .models import Template, Field, Patient, Appointment, Value

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
            id = str(result['id'])
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
            appointment_id = str(result['id'])
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
            template_id = str(result['id'])
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
            field_id = str(result['id'])
            field_name = result['name']
            fields[field_id] = field_name

        url = data['next']

    return fields

def get_values(appointment_id, headers, template_id=None, field_id=None):
    values = {}
    if template_id!=None and field_id!=None:
        url = 'https://drchrono.com/api/clinical_note_field_values?clinical_note_field=%s&clinical_note_template=%s&appointment=%s' % (field_id, template_id, appointment_id)
    else:
        url = 'https://drchrono.com/api/clinical_note_field_values?appointment=%s' % (appointment_id)

    while url:
        data = check_for_error(url, headers)

        for result in data['results']:  
            value_id = str(result['id'])
            field_id = str(result['clinical_note_field'])
            value = result['value']
            values[value_id] = (field_id, value)

        url = data['next']
    return values
    

def execute(request):
    headers = {
        'Authorization': 'Bearer %s' % request.session['access_token'],
    }
   # load all template and fields
    templates = get_templates(headers)
    saved_templates = [entry['id'] for entry in Template.objects.all().values('id')]
    templates = [Template(id=id, name=name) for id, name in templates.items() if id not in saved_templates]
    Template.objects.bulk_create(templates)

    for template_id in templates:
        fields = get_fields(template_id, headers)
        saved_fields = [entry['id'] for entry in Field.objects.all().values('id')]
        # Get all field id's which have not been seen yet. 

        # Add remaining fields to list of seen_fields
        fields = [Field(id=id, template_id=template_id, name=name) for id, name in fields.items() if id not in saved_fields]
        Field.objects.bulk_create(fields)
        

    patients = get_patients(headers)
    patient_ids = patients.keys()
    saved_patients = [entry['id'] for entry in Patient.objects.all().values('id')]
    patients = [Patient(id=id, name=name) for id, name in patients.items() if id not in saved_patients]
    Patient.objects.bulk_create(patients)
    # load patients into database

    # for each patient, load their appoints from the past 6 months
    for patient in Patient.objects.all():
        appointments = get_appointments(patient.id, headers)
        saved_appointments = [entry['id'] for entry in Appointment.objects.all().values('id')]
        appointments = [Appointment(id=id, patient_id=patient, date_time=date_time) for id, date_time in appointments.items() if id not in saved_appointments]
        Appointment.objects.bulk_create(appointments)
 
    # For each appointment, get all the values for all templates that are avaible. 
    for appointment in Appointment.objects.all():
        # Currently 290 total fields. If all are blank, with 1second pause, takes about 5minutes to execute for each appointment. 
        values = get_values(appointment.id, headers)
        if values:
            value_models = []
            saved_values = [entry['id'] for entry in Value.objects.all().values('id')]
            for id, (field_id, value) in values.items():
                if id not in saved_values:
                    template_id = Field.objects.filter(id=field_id).values('template_id_id').first()['template_id_id']
                    print("Template id: %s" % (template_id))
                    value_models.append(Value(id=id, appointment_id=appointment, template_id_id=template_id, field_id_id=field_id, patient_id=appointment.patient_id, value=value))
                    
            Value.objects.bulk_create(value_models)

   
def view(request):
    context = {}
    patients = Patient.objects.all()
    context['patients'] = patients
    
    print(context)
    return render(request, 'clinical_improved.html', context)

# Custom api call
# Given a patient_id, return all fields which have any values filled in. 
def fields(request, patient_id):
    fields = Value.objects.filter(patient_id=patient_id).values('field_id', 'field__name', 'template_id', 'template__name').distinct() # might be 'field_id__name' & 'template_id__name'
    fields = serializers.serialize('json', fields)
    return JsonResponse(fields)

def values(request, patient_id, template_id, field_id):
    values = Value.objects.filter(patient_id=patient_id, template_id=template_id, field_id=field_id).values('appointment__date_time', 'value')
    # Series of appointments with values associated
    values = serializers.searialize('json', values)
    return JsonResponse(values)
