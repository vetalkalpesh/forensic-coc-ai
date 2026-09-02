import urllib.request
import json
req = urllib.request.Request('http://localhost:5000/api/tamper', data=json.dumps({'evidence_id': 10, 'reported_by': 1, 'description': 'test', 'severity': 'Low'}).encode(), headers={'Content-Type': 'application/json'})
try:
    res = urllib.request.urlopen(req)
    print("SUCCESS", res.read())
except urllib.error.HTTPError as e:
    print("ERROR", e.code)
    print(e.read().decode())
