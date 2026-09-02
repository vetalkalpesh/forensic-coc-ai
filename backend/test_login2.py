import urllib.request, json
try:
    req = urllib.request.Request('http://localhost:5000/api/login', data=json.dumps({'badge': 'MH-2301', 'password': 'password123'}).encode(), headers={'Content-Type': 'application/json'})
    res = urllib.request.urlopen(req)
    print(res.read())
except urllib.error.HTTPError as e:
    print(e.read().decode())
