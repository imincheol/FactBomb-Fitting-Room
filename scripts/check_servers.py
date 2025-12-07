import urllib.request
import urllib.error
import time
import sys

# Define the backends to check
URLS = {
    "Local Backend ": "http://localhost:8000/health",
    "Render Backend": "https://factbomb-fitting-room.onrender.com/health"
}

def check_server(name, url):
    print(f"Checking {name} [{url}] ...", end=" ", flush=True)
    try:
        start_time = time.time()
        # Use a user agent to avoid some strict firewall rules, though health usually fine
        req = urllib.request.Request(
            url, 
            data=None, 
            headers={'User-Agent': 'BackendChecker/1.0'}
        )
        
        with urllib.request.urlopen(req, timeout=10) as response:
            latency = (time.time() - start_time) * 1000
            if response.status == 200:
                print(f"✅ ONLINE ({latency:.0f}ms)")
            else:
                print(f"⚠️  STATUS {response.status}")
    except urllib.error.URLError as e:
        print(f"❌ FAILED: {e.reason}")
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")

if __name__ == "__main__":
    print("\n=== Backend Health Check ===")
    for name, url in URLS.items():
        check_server(name, url)
    print("============================\n")
