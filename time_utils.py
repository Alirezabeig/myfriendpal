
#time_utils.py
from datetime import datetime
import pytz

def get_local_time(timezone):
    try:
        user_timezone = pytz.timezone(timezone)
        user_time = datetime.now(user_timezone)
        formatted_time = user_time.strftime('%Y-%m-%d %H:%M:%S %Z%z')
        return formatted_time
    except Exception as e:
        return str(e)
