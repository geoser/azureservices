import re
import json

from datetime import datetime, timedelta

from conversions_helper import encode_datetime

from rest_helper import rest_get
from auth_helper import AuthInfo

from azure.mgmt.billing import BillingManagementClient

from msrestazure.azure_exceptions import CloudError

def get_all_prices():
    return [
        {
            'size': 'Standard_NC6',
            'cost': '$1.387'
        },
        {
            'size': 'Standard_NC6s_v2',
            'cost': '$3.19'
        }
    ]

def get_billing_periods():
    return [p for p in billing_client.billing_periods.list()]

def get_latest_invoice():
    return billing_client.invoices.get_latest()

def get_ratecard_url():
    return "https://management.azure.com/subscriptions/" \
        + AuthInfo.subscription_id \
        + "/providers/Microsoft.Commerce/RateCard?api-version=2016-08-31-preview&" \
        + "$filter=OfferDurableId eq 'MS-AZR-0003P' and " \
        + "Currency eq 'RUB' and Locale eq 'en-EN' and RegionInfo eq 'RU'"

def get_usage_url(reportedStartTime:datetime, reportedEndTime:datetime):
    d_start = encode_datetime(reportedStartTime)
    d_end = encode_datetime(reportedEndTime)

    return "https://management.azure.com/subscriptions/" \
        + AuthInfo.subscription_id \
        + "/providers/Microsoft.Commerce/UsageAggregates?api-version=2015-06-01-preview&reportedStartTime=" \
        + d_start \
        + "&reportedEndTime=" \
        + d_end \
        + "&aggregationGranularity=HOURLY"

def get_usage(reportedStartTime:datetime, reportedEndTime:datetime):
    url = get_usage_url(reportedStartTime, reportedEndTime)
    return rest_get(url)

def get_rates_cached():
    #read from file
    f = open('json/rates_en.json', 'r', encoding="utf-8")
    content = f.read()
    f.close()
    return json.loads(content)

def get_rates():
    url = get_ratecard_url()
    return rest_get(url)

def get_all_consumptions(reportedStartTime:datetime, reportedEndTime:datetime):
    rates = get_rates_cached()
    ratesDict = dict()
    for rate in rates['Meters']:
        ratesDict[rate['MeterId']] = rate

    usage = get_usage(reportedStartTime, reportedEndTime)
    
    result  = list()

    for u in usage:
        resObj = u

        if 'instanceData' in u['properties']:
            instanceData = json.loads(u['properties']['instanceData'])
            resObj['resourceUri'] = instanceData['Microsoft.Resources']['resourceUri']
            resObj['quantity'] = u['properties']['quantity']
            resObj['usageStartTime'] = u['properties']['usageStartTime']
            resObj['usageEndTime'] = u['properties']['usageEndTime']

            rate = ratesDict[u['properties']['meterId']]
            resObj['rate_price'] = rate['MeterRates']['0']
            resObj['rate_category'] = rate['MeterCategory']

            resObj['rate_sum'] = resObj['rate_price'] * resObj['quantity']

            matchRes = re.search(r'/resourceGroups/([^/]+)/', resObj['resourceUri'])
            if matchRes is not None:
                u['server_id'] = matchRes.groups()[0]

        result.append(resObj)

    return result

def get_consumption(server_id:str, reportedStartTime:datetime, reportedEndTime:datetime):
    all_consumptions = get_all_consumptions(reportedStartTime, reportedEndTime)
    server_consumption = [c for c in all_consumptions if 'server_id' in c and c['server_id'].lower() == server_id.lower()]

    if (server_consumption is not None):
        t = [float(c['rate_sum']) for c in server_consumption if c['rate_sum'] is not None]
        result = {
            "sum": sum(t),
            "meters": server_consumption
        } 
        return result

def get_all_flavors(details):
    flavors = [
        {
            'size': 'Standard_NC6',
            'vcpus': 6,
            'ram': 56,
            'disk': 340,
            'gpu': 1
        },
        {
            'size': 'Standard_NC6s_v2',
            'vcpus': 6,
            'ram': 112,
            'disk': 736,
            'gpu': 1
        }
    ]
    if details:
        return flavors
    
    return [f['size'] for f in flavors]

billing_client = BillingManagementClient(AuthInfo.credentials, AuthInfo.subscription_id)