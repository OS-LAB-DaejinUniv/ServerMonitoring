import psutil
import requests
import time
import schedule
import platform
import os
from dotenv import load_dotenv
from const import *

load_dotenv()

# 알림을 받을 웹훅 URL
PUSH_NOTIFICATION_URL=os.getenv("PUSH_NOTIFICATION_URL")

alert_sent_status = {
    'cpu' : False,
    'memory' : False,
    'disk' : False
}

def send_notification(message, level="info"):
    """
    Send a message to 'push notification server'
    """
    icons = {"info" : "ℹ️",
             "warning" : "⚠️"
    }
    icon = icons.get(level, "")
    try:
        payload = {"text" : f"{icon}[{platform.node()} Server Notification\n{message}]"}
        response = requests.post(url=PUSH_NOTIFICATION_URL, 
                                 json=payload, 
                                 timeout=10
        )
        
        if response.status_code == 200:
            print(f"Success send a notification:{message}")
        else:
            print(f"Failed send a notification:{response.status_code}, {response.text}")
    except Exception as e:
        print(f"Error occured during sending a notification:{e}")

def get_current_resource_usage():
    """
    Returns the current system's resource usage as a dict
    """
    return {
        'cpu' : psutil.cpu_percent(interval=1),
        'memory' : psutil.virtual_memory().percent,
        'disk' : psutil.disk_usage(DISK_PARTITION_PATH).percent
    }

def check_thresholds_and_alert():
    """
    Monitor resource usage and send a one time alert when a threshodl is exceeded
    """
    print(f"[{time.strftime('%H:%M:%S')}] Checking Threshold..")
    usage = get_current_resource_usage()
    print(f"현재 사용량- CPU:{usage['cpu']}\n Memory:{usage['memory']}\n Disk:{usage['disk']}")
    
    # Check CPU
    if usage['cpu'] >= CPU_THRESHOLD and not alert_sent_status['cpu']:
        print(f"CPU 임계치 초과! ({usage['cpu']:.2f}% >= {CPU_THRESHOLD}%) 알림 상태를 True로 변경합니다.")
        send_notification(f"CPU 사용률이 {usage['cpu']}&로 임게치({CPU_THRESHOLD})%를 초과했습니다!",
                          level="warning")
        alert_sent_status['cpu'] = True
    # Check Memory
    if usage['memory'] >= MEMORY_THRESHOLD and not alert_sent_status['memory']:
        print(f"Memory 임계치 초과! ({usage['memory']:.2f}% >= {MEMORY_THRESHOLD}%) 알림 상태를 True로 변경합니다.")
        send_notification(f"메모리 사용률이 {usage['memory']}%로 임계치({MEMORY_THRESHOLD}%)를 초과했습니다!", 
                          level="warning")
        alert_sent_status['memory'] = True
        
    # Check Disk
    if usage['disk'] >= DISK_THRESHOLD and not alert_sent_status['disk']:
        print(f"Disk 임계치 초과 ('{DISK_PARTITION_PATH}' {usage['disk']:.2f}% >= {DISK_THRESHOLD}%) 알림 상태를 True로 변경합니다.")
        send_notification(f"'{DISK_PARTITION_PATH}' 디스크 사용률이 {usage['disk']}%로 임계치({DISK_THRESHOLD}%)를 초과했습니다!", 
                          level="warning")
        alert_sent_status['disk'] = True

def send_daily_resource_report():
    usage = get_current_resource_usage()
    report_message = {
        f"현재 서버 상태 요약\n"
        f"--CPU 사용률: {usage['cpu']}&\n"
        f"--Memory 사용률: {usage['memory']}%\n"
        f"--Disk 사용률: {usage['disk']}%\n"
    }
    send_notification(report_message, level="info")
    
    global alert_sent_status
    alert_sent_status = {key: False for key in alert_sent_status}

def main():
    print("Server Monitoring Start..")
    schedule.every().day.at(DAILY_REPORT_TIME).do(send_daily_resource_report)
    
    try:
        send_daily_resource_report()
        
        while True:
            schedule.run_pending()
            
            check_thresholds_and_alert()
            
            time.sleep(CHECK_INTERVAL_SECONDS)
    except KeyboardInterrupt:
        print(f"Close Server Monitoring..")
    except Exception as e:
        error_message = f"모니터링 실행 중 예기치 않은 오류 발생:{e}"
        send_notification(error_message, level="warning")

if __name__ == "__main__":
    main()