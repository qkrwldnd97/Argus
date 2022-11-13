from datetime import datetime
from django.shortcuts import render
from django.http import HttpResponse
from rest_framework import viewsets
from rest_framework.views import APIView
from django.http import JsonResponse
import reverse_geocode
from django.db.models import Min, Max

from arg.serializers import RegionSerializer, DatapointSerializer, EnvironmentalActivitySerializer, SubRegionSerializer, UntrackedRegionSerializer
from arg.models import Region, Datapoint, EnvironmentalActivity, SubRegion, UntrackedRegion
from django.forms.models import model_to_dict

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from geopy.geocoders import Nominatim
from django.forms import Form

from pycountry_convert import country_alpha2_to_continent_code, country_name_to_country_alpha2
import requests
import datetime
import json
import format_geojson
import time
import datetime

# Create your views here.
# request -> response
# request handler

DEBUG_MODE = 1


def cont_alpha2_to_name(input):
    if 'NA' == input:
        return "North America"
    elif 'OC' == input:
        return 'Oceania'
    elif 'AF' == input:
        return 'Africa'
    elif 'EU' == input:
        return 'Europe'
    elif 'SA' == input:
        return 'South America'
    elif 'AS' == input:
        return 'Asia'


def say_hello(request):
    # pull data from db
    #x = 1
    #y = 2
    return render(request, 'hello.html', {'name': 'Mosh'})


class RegionViewSet(viewsets.ModelViewSet):
    queryset = Region.objects.all()
    serializer_class = RegionSerializer


class DatapointViewSet(viewsets.ModelViewSet):
    queryset = Datapoint.objects.all()
    serializer_class = DatapointSerializer


class EnvironmentalActivityViewSet(viewsets.ModelViewSet):
    queryset = EnvironmentalActivity.objects.all()
    serializer_class = EnvironmentalActivitySerializer


class SubRegionViewSet(viewsets.ModelViewSet):
    queryset = SubRegion.objects.all()
    serializer_class = SubRegionSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        subregion = request.data['subregion_name']
        UntrackedRegion.objects.filter(untrackedregion_name=subregion).delete()
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


class UntrackedRegionViewSet(viewsets.ModelViewSet):
    queryset = UntrackedRegion.objects.all()
    serializer_class = UntrackedRegionSerializer


@api_view(["GET", "POST"])
def api_home(request, *args, **kwargs):
    temp = 0
    humidity = 0
    GHG = 0
    sea = 0
    if request.method == 'GET':
        return JsonResponse({"error": "only send latitude/longitude, EA, and date post requests to this URL"})
    if request.method == 'POST':
        lat = request.data.get('latitude')
        lon = request.data.get('longitude')
        date = request.data.get('date')
        EA = request.data.get('EA')
        if (EA == 'temperature'):
            temp = latlon_to_temp(lat, lon, date)
            return JsonResponse({"Date": date, "temperature": temp})
        if (EA == 'humid'):
            humidity = latlon_to_humidity(lat, lon, date)
            return JsonResponse({"Date": date, "humidity": humidity})
        if (EA == 'GHG'):
            GHG = latlon_to_ghg(lat, lon, date)
            return JsonResponse({"Date": date, "Greenhouse Gases": GHG})
        if (EA == 'sea'):
            sea = latlon_to_sea(lat, lon, date)
            return JsonResponse({"Date": date, "Rising Sea Level": sea})
    # return JsonResponse({"region": serializer.data.region_name})

@api_view(["GET", "POST"])

def geojson_home(request, *args, **kwargs):
    if request.method == 'GET':
        return JsonResponse({"error": "Only send post requests with json data in format {'ea': 'humidity', 'datetime': '2014-09-23T05:46:12'} to this URL"})
    
    if request.method == 'POST':
        ea = request.data.get('ea')
        dt = datetime.datetime.strptime(request.data.get('datetime'), '%Y-%m-%dT%H:%M:%S')
        data = format_geojson.get_world_data(ea, dt)
        geojson = format_geojson.populate_geojson(data)
        return JsonResponse(geojson)


def latlon_to_temp(lat, lon):
    if lat is None:
        return {'error': 'latitude field required'}
    if lon is None:
        return {'error': 'longitude field required'}
    if type(lat) != type(1) and type(lat) != type(1.):
        return {'error': 'latitude must be a number datatype'}
    if type(lon) != type(1) and type(lon) != type(1.):
        return {'error': 'longitude must be a number datatype'}
    if lat > 90 or lat < -90:
        return {'error': 'latitude range is -90 to 90'}
    if lon > 180 or lon < -180:
        return {'error': 'longitude range is -180 to 180'}
    coordinates = (lat, lon),
    loc = reverse_geocode.search(coordinates)
    print("got loc: ")
    print(loc)
    country = loc[0]['country']
    try:
        country = country_name_to_country_alpha2(country)
        country = country_alpha2_to_continent_code(country)
        country = cont_alpha2_to_name(country)
    except:
        country = "Antarctica"
    if(DEBUG_MODE):
        print("country:")
        print(country)
    try:
        # see if country is a primary region
        reg = Region.objects.get(region_name=country)
    except:
        try:
            # see if country is a sub region
            reg = SubRegion.objects.get(subregion_name=country).region
            if(DEBUG_MODE):
                print("region: ")
                print(reg.region_name)
        except:
            if not UntrackedRegion.objects.filter(untrackedregion_name=country).exists():
                untracked = UntrackedRegion()
                untracked.untrackedregion_name = country
                untracked.save()
            return {'error': 'region not tracked in database'}
    try:
        temp = EnvironmentalActivity.objects.get(ea_name="temperature")
        filtered = Datapoint.objects.filter(region=reg, ea=temp, is_future=0)
        most_recent = filtered.aggregate(Max('dp_datetime'))[
            'dp_datetime__max']

        for i in filtered:
            if str(i.dp_datetime).split(" ")[0] == date:
                most_recent = i.dp_datetime
        dp = filtered.get(dp_datetime=most_recent)

    except:
        return {'error': 'no data for this region'}
    return {country: dp.value}  # temperature:value


def latlon_to_humidity(lat, lon, date):
    if lat is None:
        return {'error': 'latitude field required'}
    if lon is None:
        return {'error': 'longitude field required'}
    if type(lat) != type(1) and type(lat) != type(1.):
        return {'error': 'latitude must be a number datatype'}
    if type(lon) != type(1) and type(lon) != type(1.):
        return {'error': 'longitude must be a number datatype'}
    if lat > 90 or lat < -90:
        return {'error': 'latitude range is -90 to 90'}
    if lon > 180 or lon < -180:
        return {'error': 'longitude range is -180 to 180'}
    coordinates = (lat, lon),
    loc = reverse_geocode.search(coordinates)
    country = loc[0]['country']
    try:
        country = country_name_to_country_alpha2(country)
        country = country_alpha2_to_continent_code(country)
        country = cont_alpha2_to_name(country)
    except:
        country = "Antarctica"
    if(DEBUG_MODE):
        print("country:")
        print(country)
    try:
        # see if country is a primary region
        reg = Region.objects.get(region_name=country)
    except:
        try:
            # see if country is a sub region
            reg = SubRegion.objects.get(subregion_name=country).region
        except:
            if not UntrackedRegion.objects.filter(untrackedregion_name=country).exists():
                untracked = UntrackedRegion()
                untracked.untrackedregion_name = country
                untracked.save()
            return {'error': 'region not tracked in database'}
    try:
        humi = EnvironmentalActivity.objects.get(ea_name="humidity")
        filtered = Datapoint.objects.filter(region=reg, ea=humi, is_future=0)
        most_recent = filtered.aggregate(Max('dp_datetime'))[
            'dp_datetime__max']
        for i in filtered:
            if str(i.dp_datetime).split(" ")[0] == date:
                most_recent = i.dp_datetime

        dp = filtered.get(dp_datetime=most_recent)
    except:
        return {'error': 'no data for this region'}
    return {country: dp.value}  # humidity:value


def latlon_to_ghg(lat, lon, date):
    if lat is None:
        return {'error': 'latitude field required'}
    if lon is None:
        return {'error': 'longitude field required'}
    if type(lat) != type(1) and type(lat) != type(1.):
        return {'error': 'latitude must be a number datatype'}
    if type(lon) != type(1) and type(lon) != type(1.):
        return {'error': 'longitude must be a number datatype'}
    if lat > 90 or lat < -90:
        return {'error': 'latitude range is -90 to 90'}
    if lon > 180 or lon < -180:
        return {'error': 'longitude range is -180 to 180'}
    coordinates = (lat, lon),
    loc = reverse_geocode.search(coordinates)
    country = loc[0]['country']
    try:
        country = country_name_to_country_alpha2(country)
        country = country_alpha2_to_continent_code(country)
        country = cont_alpha2_to_name(country)
    except:
        country = "Antarctica"
    if(DEBUG_MODE):
        print("country:")
        print(country)
    try:
        # see if country is a primary region
        reg = Region.objects.get(region_name=country)
    except:
        try:
            # see if country is a sub region
            reg = SubRegion.objects.get(subregion_name=country).region
        except:
            if not UntrackedRegion.objects.filter(untrackedregion_name=country).exists():
                untracked = UntrackedRegion()
                untracked.untrackedregion_name = country
                untracked.save()
            return {'error': 'region not tracked in database'}
    try:
        ghg = EnvironmentalActivity.objects.get(ea_name="co2")
        filtered = Datapoint.objects.filter(region=reg, ea=ghg, is_future=0)
        most_recent = filtered.aggregate(Max('dp_datetime'))[
            'dp_datetime__max']

        for i in filtered:
            if str(i.dp_datetime).split(" ")[0] == date:
                most_recent = i.dp_datetime

        dp = filtered.get(dp_datetime=most_recent)
    except:
        return {'error': 'no data for this region'}

    # API for O3 and NO2
    API = '37cde85ed34605798aa360d4c26dc586'
    year, month, day = date.split("-")
    start = int(time.mktime(datetime.datetime(
        int(year), int(month), int(day), 00, 00).timetuple()))
    end = int(time.mktime(datetime.datetime(
        int(year), int(month), int(day), 1, 00).timetuple()))
    response = requests.get(
        f'http://api.openweathermap.org/data/2.5/air_pollution?lat=44.34&lon=10.99&type=hour&start={start}&end={end}&appid={API}')
    res = response.text
    parse_json = json.loads(res)

    ozone = parse_json['list'][0]['components']['o3']  # ozone
    no2 = parse_json['list'][0]['components']['no2']  # NO2
    co2 = dp.value  # co2
    final = "CO2: " + str(dp.value) + " Ozone(O3): " + \
        str(ozone) + " NO2: " + str(no2)
    return {country: final}  # greenhouse gases:value


def latlon_to_sea(lat, lon, date):
    if lat is None:
        return {'error': 'latitude field required'}
    if lon is None:
        return {'error': 'longitude field required'}
    if type(lat) != type(1) and type(lat) != type(1.):
        return {'error': 'latitude must be a number datatype'}
    if type(lon) != type(1) and type(lon) != type(1.):
        return {'error': 'longitude must be a number datatype'}
    if lat > 90 or lat < -90:
        return {'error': 'latitude range is -90 to 90'}
    if lon > 180 or lon < -180:
        return {'error': 'longitude range is -180 to 180'}
    coordinates = (lat, lon),
    loc = reverse_geocode.search(coordinates)
    country = loc[0]['country']
    try:
        country = country_name_to_country_alpha2(country)
        country = country_alpha2_to_continent_code(country)
        country = cont_alpha2_to_name(country)
    except:
        country = "Antarctica"
    if(DEBUG_MODE):
        print("country:")
        print(country)
    try:
        # see if country is a primary region
        reg = Region.objects.get(region_name=country)
    except:
        try:
            # see if country is a sub region
            reg = SubRegion.objects.get(subregion_name=country).region
        except:
            if not UntrackedRegion.objects.filter(untrackedregion_name=country).exists():
                untracked = UntrackedRegion()
                untracked.untrackedregion_name = country
                untracked.save()
            return {'error': 'region not tracked in database'}
    try:
        sea = EnvironmentalActivity.objects.get(ea_name="sea level")
        filtered = Datapoint.objects.filter(region=reg, ea=sea, is_future=0)
        most_recent = filtered.aggregate(Max('dp_datetime'))[
            'dp_datetime__max']

        for i in filtered:
            if str(i.dp_datetime).split(" ")[0] == date:
                most_recent = i.dp_datetime

        dp = filtered.get(dp_datetime=most_recent)

    except:
        return {'error': 'no data for this region'}
    return {country: dp.value}  # rising sea levels:value
