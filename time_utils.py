
#time_utils.py
from datetime import datetime
import pytz

def convert_utc_to_local(utc_time_str, local_timezone):
    """
    Convert a UTC time string to a local time string based on the given timezone.

    :param utc_time_str: UTC time in isoformat
    :param local_timezone: Timezone string (e.g., 'America/Los_Angeles')
    :return: Local time string in isoformat
    """
    utc_time = datetime.fromisoformat(utc_time_str.replace("Z", "+00:00"))
    local_time = utc_time.astimezone(pytz.timezone(local_timezone))
    return local_time.isoformat()
