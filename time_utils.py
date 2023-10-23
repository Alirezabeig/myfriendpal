
from datetime import datetime
import requests
import pytz

def get_local_time(timezone):
    tz = pytz.timezone(timezone)
    local_dt = datetime.now(tz)
    return local_dt.strftime('%H:%M:%S'), local_dt.strftime('%Y-%m-%d')
