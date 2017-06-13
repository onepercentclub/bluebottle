from django.http import JsonResponse
import random
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
        tenant = data["result"]["parameters"]["tenant"]
        response = get_engagement_number_tenant(tenant)
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
        "db": "platform_v2_staging",
        "q": """SELECT SUM("engagement_number") FROM "platform_v2_staging"."autogen"."saas"
                WHERE "type"='engagement_number_aggregate' AND time > '2017-06-01'"""
    }
    r = requests.get(url, auth=('admin', 'ZJpv2WReqpU6VM2JEpN'), params=params)
    engagement_number = calculate_engagement_number_aggreagted(r.json())
    return {
        "speech": "The engagement number is {}".format(engagement_number),
        "displayText": "The engagement number is {}".format(engagement_number),
        "source": "OnePercentClub"
    }


def get_engagement_number_tenant(tenant):
    engagement_number = random.randint(0, 1000)
    return {
        "speech": "The engagement number for {} is {}".format(tenant, engagement_number),
        "displayText": "The engagement number for {} is {}".format(tenant, engagement_number),
        "source": "OnePercentClub"
    }
