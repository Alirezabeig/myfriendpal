
#shared_utils.py
def get_new_access_token(refresh_token):
    data = {
        'client_id': GOOGLE_CLIENT_ID,
        'client_secret': GOOGLE_CLIENT_SECRET,
        'refresh_token': refresh_token,
        'grant_type': 'refresh_token'
    }
    try:
        response = requests.post('https://oauth2.googleapis.com/token', data=data)
        token_info = response.json()
        new_access_token = token_info.get('access_token')
        return new_access_token
    except Exception as e:
        logging.error(f"Failed to get new access token: {e}")
        return None
