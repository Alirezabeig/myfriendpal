
#time_utils.py
from datetime import datetime
import pytz  # Install this package if you haven't

def get_local_time(timezone_str):
    timezone = pytz.timezone(timezone_str)
    local_dt = datetime.now(timezone)
    local_time = local_dt.strftime('%H:%M:%S')
    local_date = local_dt.strftime('%Y-%m-%d')
    return local_time, local_date
