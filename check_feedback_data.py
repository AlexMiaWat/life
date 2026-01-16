"""Скрипт для проверки Feedback данных через API"""
import requests
import json
import time
import sys

def check_feedback_data():
    """Проверяет наличие полных данных Feedback через API"""
    try:
        print("Connecting to server...")
        response = requests.get("http://localhost:8000/status", timeout=10)
        
        if response.status_code != 200:
            print(f"[ERROR] Server returned status {response.status_code}")
            return False
        
        data = response.json()
        memory = data.get("memory", [])
        
        print(f"\nTotal memory entries: {len(memory)}")
        
        # Фильтруем Feedback записи
        feedback_records = [m for m in memory if m.get("event_type") == "feedback"]
        print(f"Total feedback records: {len(feedback_records)}")
        
        if len(feedback_records) == 0:
            print("[WARNING] No feedback records found yet.")
            print("This is normal if system just started. Feedback records appear after 3-10 ticks.")
            return False
        
        # Проверяем наличие feedback_data
        records_with_data = [f for f in feedback_records if f.get("feedback_data")]
        records_without_data = [f for f in feedback_records if not f.get("feedback_data")]
        
        print(f"\nFeedback records WITH data: {len(records_with_data)}")
        print(f"Feedback records WITHOUT data (old format): {len(records_without_data)}")
        
        if len(records_with_data) > 0:
            print("\n" + "="*60)
            print("[SUCCESS] Found feedback records with full data!")
            print("="*60)
            
            sample = records_with_data[0]
            print("\nSample feedback record:")
            print(json.dumps(sample, indent=2))
            
            # Проверяем структуру
            fd = sample.get("feedback_data", {})
            print("\n" + "="*60)
            print("Data structure check:")
            print("="*60)
            print(f"  action_id: {'OK' if fd.get('action_id') else 'MISSING'}")
            print(f"  action_pattern: {'OK' if fd.get('action_pattern') else 'MISSING'}")
            print(f"  state_delta: {'OK' if fd.get('state_delta') else 'MISSING'}")
            print(f"  delay_ticks: {'OK' if fd.get('delay_ticks') is not None else 'MISSING'}")
            print(f"  associated_events: {'OK' if 'associated_events' in fd else 'MISSING'}")
            
            if all([fd.get('action_id'), fd.get('action_pattern'), fd.get('state_delta'), 
                   fd.get('delay_ticks') is not None]):
                print("\n[SUCCESS] All required fields are present!")
                return True
            else:
                print("\n[WARNING] Some fields are missing")
                return False
        else:
            print("\n[FAIL] No feedback records with data found!")
            if len(records_without_data) > 0:
                print("\nFound records without data (old format):")
                print(json.dumps(records_without_data[0], indent=2))
                print("\nThis means the system is still using old code or records were created before fix.")
            return False
            
    except requests.exceptions.ConnectionError:
        print("[ERROR] Cannot connect to server. Is it running?")
        print("Start server with: python src/main_server_api.py --dev --tick-interval 1.0 --snapshot-period 15")
        return False
    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("="*60)
    print("Testing Feedback Data Storage")
    print("="*60)
    
    # Даем время системе создать Feedback записи
    print("\nChecking for feedback records...")
    print("(Feedback records appear 3-10 ticks after actions)")
    
    if check_feedback_data():
        print("\n" + "="*60)
        print("[SUCCESS] Feedback data storage is working correctly!")
        print("="*60)
        sys.exit(0)
    else:
        print("\n" + "="*60)
        print("[INFO] No feedback records with data found yet.")
        print("This could mean:")
        print("  1. System just started (wait 15-20 seconds)")
        print("  2. No actions have been executed yet")
        print("  3. Feedback records haven't been observed yet (3-10 tick delay)")
        print("="*60)
        sys.exit(1)
