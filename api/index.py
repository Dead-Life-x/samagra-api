from http.server import BaseHTTPRequestHandler
import json
import requests

URL = "https://samagra.gov.in/Services/CommonWebApi.svc/GetDetailsBySamagra"

HEADERS = {
    "User-Agent": "okhttp/3.12.1",
    "Content-Type": "application/json; charset=UTF-8",
    "Authorization": "Basic c2FtYWdyYUFwaTpzYW1hZ3JhQDEyMw==",
}

def fetch(payload):
    try:
        r = requests.post(URL, headers=HEADERS, json=payload, timeout=20, verify=False)
        if r.status_code != 200:
            return None
        data = json.loads(r.text)
        return data.get("d") if "d" in data else data
    except:
        return None

def smart_get(obj, keys):
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k in keys:
                return v
            res = smart_get(v, keys)
            if res:
                return res
    elif isinstance(obj, list):
        for i in obj:
            res = smart_get(i, keys)
            if res:
                return res
    return None

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            from urllib.parse import urlparse, parse_qs
            query = parse_qs(urlparse(self.path).query)

            mobile = query.get("mobile", [None])[0]

            if not mobile:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(json.dumps({"status": False, "msg": "mobile required"}).encode())
                return

            res = fetch({"samagraID": "0", "MobileNo": mobile})

            if not res:
                self.send_response(200)
                self.end_headers()
                self.wfile.write(json.dumps({"status": False, "msg": "no data"}).encode())
                return

            items = res if isinstance(res, list) else res.get("data", [])
            if not items and isinstance(res, dict):
                items = [res]

            results = []

            for it in items:
                uid = smart_get(it, ["UserID", "samagraID", "MemberID"])
                if not uid:
                    continue

                full = fetch({"samagraID": str(uid)})
                if not full:
                    continue

                results.append({
                    "uid": uid,
                    "name": smart_get(full, ["MemberNameE", "Name"]),
                    "dob": smart_get(full, ["Dob"]),
                    "gender": smart_get(full, ["Gender"]),
                    "family_id": smart_get(full, ["FamilyID"]),
                    "mobile": smart_get(full, ["MobileNo"]),
                    "address": smart_get(full, ["Address"]),
                    "district": smart_get(full, ["DistrictName"])
                })

            self.send_response(200)
            self.end_headers()
            self.wfile.write(json.dumps({
                "status": True,
                "total": len(results),
                "data": results
            }).encode())

        except Exception as e:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())
