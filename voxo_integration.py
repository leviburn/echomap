import os
import time
import requests

VOXO_API_KEY = os.getenv('VOXO_API_KEY')
VOXO_API_BASE = os.getenv('VOXO_API_BASE', 'https://api.voxo.co/v1')
VOXO_WEBHOOK_URL = os.getenv('VOXO_WEBHOOK_URL', 'https://944e-142-190-3-138.ngrok-free.app/voxo-webhook')


def initiate_call_and_record(phone_number):
    headers = {
        'Authorization': f'Bearer {VOXO_API_KEY}',
        'Content-Type': 'application/json'
    }
    payload = {
        'to': phone_number,
        'record': True,
        'webhook': VOXO_WEBHOOK_URL
    }
    response = requests.post(f'{VOXO_API_BASE}/calls', json=payload, headers=headers)
    response.raise_for_status()
    call_data = response.json()
    return call_data['call_id']


def get_call_recording(call_id):
    headers = {
        'Authorization': f'Bearer {VOXO_API_KEY}',
    }
    for _ in range(30):
        resp = requests.get(f'{VOXO_API_BASE}/calls/{call_id}', headers=headers)
        resp.raise_for_status()
        call_info = resp.json()
        if call_info.get('recording_url'):
            return call_info['recording_url']
        time.sleep(5)
    raise Exception('Recording not available after waiting.')


def get_transcript_from_voxo(call_id):
    headers = {
        'Authorization': f'Bearer {VOXO_API_KEY}',
    }
    resp = requests.get(f'{VOXO_API_BASE}/calls/{call_id}/transcription', headers=headers)
    resp.raise_for_status()
    return resp.json().get('transcript') 