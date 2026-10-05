from django.shortcuts import render
import requests

def get_point_by_postal(request):
    # Получаем значения apikey, country_code и postal_code из запроса
    apikey = '9fa141f81d54cec267da6ce7070f8541'
    country_code = 'FI'
    postal_code = '21250'

    # Формируем URL с помощью полученных значений
    url = f"https://atapi2.postnord.com/rest/businesslocation/v5/servicepoints/bypostalcode?apikey={apikey}&returnType=json&countryCode={country_code}&postalCode={postal_code}&context=optionalservicepoint&responseFilter=public"
    
    payload={}
    headers = {}

    response = requests.request("GET", url, headers=headers, data=payload)
    resp_json = response.json()  # Преобразование текста ответа в JSON формат

    if "servicePointInformationResponse" in resp_json and "compositeFault" in resp_json["servicePointInformationResponse"]:
        # Получен ответ об ошибке
        faults = resp_json["servicePointInformationResponse"]["compositeFault"]["faults"]
        error_message = ", ".join([fault["explanationText"] for fault in faults])
        context = {
            'error_message': error_message
        }
    else:
        service_points = resp_json["servicePointInformationResponse"]["servicePoints"]
        context = {
            'service_points': service_points,
            'response': resp_json
        }

    return render(request, 'postnord/get_postal.html', context)

def get_point_by_address(request):
    apikey = '9fa141f81d54cec267da6ce7070f8541'
    country_code = 'FI'
    postal_code = '21250'
    city = 'Masku'
    street_name = 'Luolavuorentie 37'
    number_of_points = '5'

    url = f"https://atapi2.postnord.com/rest/businesslocation/v5/servicepoints/nearest/byaddress?apikey={apikey}&returnType=json&countryCode={country_code}&agreementCountry={country_code}&city={city}&postalCode={postal_code}&streetName={street_name}&numberOfServicePoints={number_of_points}&srId=EPSG:4326&context=optionalservicepoint&responseFilter=public"
    
    payload = {}
    headers = {}

    response = requests.request("GET", url, headers=headers, data=payload)

    print("Response text:", response.text)


    resp_json = response.json()  


    if "servicePointInformationResponse" in resp_json:
        service_points_response = resp_json["servicePointInformationResponse"]
        if "compositeFault" in service_points_response:
            faults = service_points_response["compositeFault"]["faults"]
            error_message = ", ".join([fault["explanationText"] for fault in faults])
            context = {'error_message': error_message}
        elif "servicePoints" in service_points_response:
            service_points = service_points_response["servicePoints"]
           
            context = {'service_points': service_points}
        else:
            context = {'error_message': 'No service points found.'}
    else:
        context = {'error_message': 'No service points information found.'}

    return render(request, 'postnord/get_postal_address.html', context)

def calc_ship_time(request):
    apikey = '9fa141f81d54cec267da6ce7070f8541'
    country_code = 'FI'
    dateOfDeparture= '2024-02-08'
    fromAddressStreetName = 'Asessorinkatu'
    fromAddressStreetNumber = '12'
    fromAddressPostalCode = '20780'
    toAddressStreetName = 'Luolavuorentie'
    toAddressStreetNumber = '37'
    toAddressPostalCode = '21250'

    url = f"https://atapi2.postnord.com/rest/transport/v1/transittime/getTransitTimeInformation.json?apikey={apikey}&dateOfDeparture={dateOfDeparture}&serviceCode=18&serviceGroupCode={country_code}&fromAddressStreetName={fromAddressStreetName}&fromAddressStreetNumber={fromAddressStreetNumber}&fromAddressPostalCode={fromAddressPostalCode}&fromAddressCountryCode={country_code}&toAddressStreetName={toAddressStreetName}&toAddressStreetNumber={toAddressStreetNumber}&toAddressPostalCode={toAddressPostalCode}&toAddressCountryCode={country_code}&responseContent=simple"
    
    print("url: ", url)

    payload = {}
    headers = {}

    response = requests.request("GET", url, headers=headers, data=payload)

    print("Response text:", response.text)

    resp_json = response.json()  


    if "se.posten.loab.lisp.notis.publicapi.serviceapi.TransitTimeSimpleResponse" in resp_json:
        transit_time_response = resp_json["se.posten.loab.lisp.notis.publicapi.serviceapi.TransitTimeSimpleResponse"]
        delivery_time = transit_time_response.get("deliveryTime")
        delivery_date = transit_time_response.get("deliveryDate")
        
        if delivery_time and delivery_date:
            context = {
                'delivery_time': delivery_time,
                'delivery_date': delivery_date,
            }
        else:
            context = {'error_message': 'No delivery time or date found.'}
    else:
        context = {'error_message': 'No transit time information found.'}

    return render(request, 'postnord/calc_ship_time.html', context)