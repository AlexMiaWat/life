import requests
import json

BASE_URL = "http://localhost:8000"

def test_get_status():
    """Тест GET /status"""
    try:
        response = requests.get(f"{BASE_URL}/status")
        print(f"GET /status: Status Code {response.status_code}")
        if response.status_code == 200:
            print(f"Response: {response.json()}")
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"GET /status: Exception {e}")

def test_get_clear_data():
    """Тест GET /clear-data"""
    try:
        response = requests.get(f"{BASE_URL}/clear-data")
        print(f"GET /clear-data: Status Code {response.status_code}")
        if response.status_code == 200:
            print(f"Response: {response.text}")
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"GET /clear-data: Exception {e}")

def test_post_event_success():
    """Тест POST /event с правильным JSON"""
    data = {
        "type": "test_event",
        "intensity": 0.1,
        "metadata": {"key": "value"}
    }
    try:
        response = requests.post(f"{BASE_URL}/event", json=data)
        print(f"POST /event (success): Status Code {response.status_code}")
        if response.status_code == 200:
            print(f"Response: {response.text}")
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"POST /event (success): Exception {e}")

def test_post_event_invalid_json():
    """Тест POST /event с неправильным JSON"""
    try:
        response = requests.post(f"{BASE_URL}/event", data="invalid json")
        print(f"POST /event (invalid JSON): Status Code {response.status_code}")
        print(f"Response: {response.text}")
    except Exception as e:
        print(f"POST /event (invalid JSON): Exception {e}")

if __name__ == "__main__":
    print("Starting API tests...")
    test_get_status()
    test_get_clear_data()
    test_post_event_success()
    test_post_event_invalid_json()
    print("Tests completed.")