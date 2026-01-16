"""
Интеграционный тест для проверки полных данных Feedback
"""
import requests
import json
import time
import sys

def check_feedback_data():
    """Проверяет наличие полных данных Feedback через API"""
    try:
        # Получаем статус
        response = requests.get("http://localhost:8000/status", timeout=5)
        if response.status_code != 200:
            print(f"[ERROR] Server returned status {response.status_code}")
            return False
        
        data = response.json()
        memory = data.get("memory", [])
        
        # Фильтруем Feedback записи
        feedback_records = [m for m in memory if m.get("event_type") == "feedback"]
        
        print(f"Total memory entries: {len(memory)}")
        print(f"Feedback records: {len(feedback_records)}")
        
        if len(feedback_records) == 0:
            print("[WARNING] No feedback records found yet. Waiting for actions to complete...")
            return False
        
        # Проверяем наличие feedback_data
        records_with_data = [f for f in feedback_records if f.get("feedback_data")]
        records_without_data = [f for f in feedback_records if not f.get("feedback_data")]
        
        print(f"Feedback records WITH data: {len(records_with_data)}")
        print(f"Feedback records WITHOUT data: {len(records_without_data)}")
        
        if len(records_with_data) > 0:
            print("\n[SUCCESS] Found feedback records with full data!")
            print("\nSample feedback record:")
            sample = records_with_data[0]
            print(f"  event_type: {sample.get('event_type')}")
            print(f"  meaning_significance: {sample.get('meaning_significance')}")
            print(f"  timestamp: {sample.get('timestamp')}")
            if sample.get("feedback_data"):
                fd = sample["feedback_data"]
                print(f"  feedback_data:")
                print(f"    action_id: {fd.get('action_id', 'N/A')}")
                print(f"    action_pattern: {fd.get('action_pattern', 'N/A')}")
                print(f"    state_delta: {fd.get('state_delta', {})}")
                print(f"    delay_ticks: {fd.get('delay_ticks', 'N/A')}")
            return True
        else:
            print("\n[FAIL] No feedback records with data found!")
            if len(records_without_data) > 0:
                print("Found records without data (old format):")
                print(json.dumps(records_without_data[0], indent=2))
            return False
            
    except requests.exceptions.ConnectionError:
        print("[ERROR] Cannot connect to server. Is it running?")
        return False
    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("Testing Feedback Data Storage")
    print("=" * 60)
    
    # Даем время системе создать Feedback записи
    print("\nWaiting for system to generate feedback records...")
    for i in range(3):
        time.sleep(5)
        print(f"Attempt {i+1}/3...")
        if check_feedback_data():
            sys.exit(0)
    
    print("\n[FAIL] No feedback records with data found after waiting")
    sys.exit(1)
