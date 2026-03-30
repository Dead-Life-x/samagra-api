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
        r = requests.post(URL, headers=HEADERS, json=payload, timeout=10)
        if r.status_code != 200:
            return None
        data = r.json()
        return data.get("d") if "d" in data else data
    except Exception as e:
        return {"error": str(e)}

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

def handler(request):
    try:
        mobile = request.args.get("mobile")

        if not mobile:
            return {
                "statusCode": 400,
                "body": json.dumps({"status": False, "message": "mobile required"})
            }

        res = fetch({"samagraID": "0", "MobileNo": mobile})

        if not res:
            return {
                "statusCode": 200,
                "body": json.dumps({"status": False, "message": "No data"})
            }

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
                "dob": smart_get(full, ["Dob", "DOB"]),
                "mobile": smart_get(full, ["MobileNo"]),
                "address": smart_get(full, ["Address"]),
            })

        return {
            "statusCode": 200,
            "body": json.dumps({
                "status": True,
                "total": len(results),
                "data": results
            })
        }

    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }
