from django.http import JsonResponse
import json
import requests


def ai(request):
    data = json.loads(request.body)
    response = generate_response(data)

    return JsonResponse(response)


def generate_response(data):
    action = data["result"]["action"]

    if action == "engagement_number.aggregated":
        response = get_engagement_number_aggregated()
    elif action == "engagement_number.tenant":
        # tenant = data["result"]["parameters"]["tenant-original"] or data["result"]["parameters"]["tenant"]
        tenant = data["result"]["parameters"]["tenant"]
        response = get_engagement_number_tenant(tenant)
    elif action == "donation":
        # tenant = data["result"]["parameters"]["tenant-original"] or data["result"]["parameters"]["tenant"]
        tenant = data["result"]["parameters"].get("tenant", None)
        currency_name = data["result"]["parameters"].get("currency_name", None)
        response = get_donations(tenant, currency_name)
    else:
        response = {
            "followupEvent": {
                "name": "unknown"
            }
        }

    return response


def calculate_engagement_number_aggreagted(data):
    enagagement_number = data["results"][0]["series"][0]["values"][0][1]
    return enagagement_number


def get_engagement_number_aggregated():
    url = "http://localhost:8086/query"
    params = {
        "db": "platform_v2_production",
        "q": """SELECT SUM("engagement_number") FROM "platform_v2_production"."autogen"."saas" WHERE "type"='engagement_number_aggregate' AND time > '2017-01-01'"""
    }
    r = requests.get(url, auth=('saasread', 's8L83zkWVxFZr8yv'), params=params)
    engagement_number = calculate_engagement_number_aggreagted(r.json())
    return {
        "speech": "The engagement number is {}".format(engagement_number),
        "displayText": "The engagement number is {}".format(engagement_number),
        "source": "OnePercentClub"
    }


def parse_engagement_number(data):
    enagagement_number = data["results"][0]["series"][0]["values"][0][1]
    return enagagement_number


def get_engagement_number_tenant(tenant):
    url = "http://localhost:8086/query"
    params = {
        "db": "platform_v2_production",
        "q": """SELECT SUM("engagement_number") FROM "platform_v2_production"."autogen"."saas" WHERE "type"='engagement_number_tenant' AND "tenant"='{}' AND time > '2017-01-01'""".format(tenant)
    }
    r = requests.get(url, auth=('saasread', 's8L83zkWVxFZr8yv'), params=params)
    engagement_number = parse_engagement_number(r.json())
    return {
        "speech": "The engagement number for {} is {}".format(tenant, engagement_number),
        "displayText": "The engagement number for {} is {}".format(tenant, engagement_number),
        "source": "OnePercentClub"
    }


def get_donations(tenant, currency_name):
    url = "http://localhost:8086/query"
    params = {
        "db": "platform_v2_production",
        "q": """SELECT SUM("engagement_number") FROM "platform_v2_production"."autogen"."saas" WHERE "type"='engagement_number_tenant' AND "tenant"='{}' AND time > '2017-01-01'""".format(tenant)
    }
    r = requests.get(url, auth=('saasread', 's8L83zkWVxFZr8yv'), params=params)
    engagement_number = parse_engagement_number(r.json())
    return {
        "speech": "The total donation amount till date is {} {}".format(tenant, currency_name),
        "displayText": "The total donation amount till date is {} {}".format(tenant, currency_name),
        "source": "OnePercentClub"
    }
