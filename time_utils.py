
from datetime import datetime
import requests
import pytz

def get_local_time(ip_address):
    try:
        response = requests.get(f'http://ip-api.com/json/{ip_address}')
        response.raise_for_status()  # Raise HTTPError for bad responses (4xx and 5xx)
    except requests.RequestException as e:
        print(f"Failed to get data from ip-api.com: {e}")
        return None

    data = response.json()
    timezone = data.get('timezone')

    if timezone:
        try:
            tz = pytz.timezone(timezone)
            current_time = datetime.now(tz)
            return current_time
        except pytz.UnknownTimeZoneError:
            print(f"Unknown timezone: {timezone}")
            return None
    else:
        print("Timezone not found in the API response.")
        return None
