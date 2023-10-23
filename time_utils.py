
#time_utils.py
from datetime import datetime
import requests
import pytz
from datetime import datetime

current_time = datetime.now()

def get_current_time_by_ip(ip_address):
    response = requests.get(f'http://ip-api.com/json/{ip_address}')
    data = response.json()
    timezone = data.get('timezone')
    if timezone:
        tz = pytz.timezone(timezone)
        current_time = datetime.now(tz)
        return current_time
    return None
