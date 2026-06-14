import urllib.parse
import urllib.request
import json

def make_request(url, form=None):
    payload = urllib.parse.urlencode(form).encode("utf-8") if form else None
    headers = {"content-type": "application/x-www-form-urlencoded; charset=UTF-8"}
    request = urllib.request.Request(url, data=payload, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=30.0) as response:
            return json.loads(response.read().decode("utf-8"))
    except Exception as e:
        print(f"Error: {e}")
        return {}

stations_response = make_request("https://envisoft.gov.vn/eos/services/call/json/get_stations", {"is_qi": "true", "is_public": "true", "qi_type": "aqi"})
stations = stations_response.get("stations", [])
hcmc = [s for s in stations if "Hồ Chí Minh" in str(s.get("station_name", "")) or "Hồ Chí Minh" in str(s.get("address", ""))]

print(f"Found {len(hcmc)} HCMC stations")
for s in hcmc:
    print(f"ID: {s.get('id')}, Name: {s.get('station_name')}, Address: {s.get('address')}")
