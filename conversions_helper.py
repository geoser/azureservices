from datetime import datetime, timedelta
import urllib.parse

def convert_datetime(time_stamp:int):
    exact_value = datetime(1970, 1, 1) + timedelta(milliseconds=time_stamp)
    return datetime(exact_value.year, exact_value.month, exact_value.day, exact_value.hour)

def encode_datetime(d:datetime):
    dstr = d.strftime('%Y-%m-%dT%H:%M:%S+00:00')
    return urllib.parse.quote(dstr)