from flask import Flask, request, jsonify
import requests
import json

app = Flask(__name__)

# ============================================
# 🔐 SAMAGRA CONFIG
# ============================================
URL = "https://samagra.gov.in/Services/CommonWebApi.svc/GetDetailsBySamagra"

HEADERS = {
    "User-Agent": "okhttp/3.12.1",
    "Content-Type": "application/json; charset=UTF-8",
    "Authorization": "Basic c2FtYWdyYUFwaTpzYW1hZ3JhQDEyMw==",
}


# ============================================
# 🔧 COMMON FETCH
# ============================================
def fetch(payload):
    try:
        r = requests.post(URL, headers=HEADERS, json=payload, timeout=15)
        if r.status_code != 200:
            return None

        text = r.content.decode("utf-8-sig", errors="ignore").strip()
        data = json.loads(text)

        return data.get("d") if "d" in data else data

    except:
        return None


# ============================================
# 🔍 SMART SEARCH
# ============================================
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


# ============================================
# 📱 GET USER IDS
# ============================================
def get_user_ids(mobile):
    res = fetch({"samagraID": "0", "MobileNo": mobile})

    if not res:
        return []

    items = res if isinstance(res, list) else res.get("data", [])
    if not items and isinstance(res, dict):
        items = [res]

    ids = []

    for it in items:
        uid = smart_get(it, ["UserID", "samagraID", "MemberID"])
        if uid:
            ids.append(str(uid))

    return list(dict.fromkeys(ids))


# ============================================
# 🧠 FULL INTEL
# ============================================
def get_full(uid):
    res = fetch({"samagraID": str(uid)})

    if not res:
        return None

    return {
        "uid": uid,
        "name": smart_get(res, ["MemberNameE", "Name", "FullName"]),
        "name_hindi": smart_get(res, ["MemberNameH"]),
        "dob": smart_get(res, ["Dob", "DOB"]),
        "gender": smart_get(res, ["Gender"]),
        "family_id": smart_get(res, ["FamilyID"]),
        "mobile": smart_get(res, ["MobileNo"]),
        "address": smart_get(res, ["Address"]),
        "district": smart_get(res, ["DistrictName"]),
        "category": smart_get(res, ["CategoryName"]),
        "photo": smart_get(res, ["Photo"])
    }


# ============================================
# 🏠 HOME
# ============================================
@app.route("/")
def home():
    return jsonify({
        "status": True,
        "message": "Samagra API Running 🚀"
    })


# ============================================
# 🔥 MAIN API
# ============================================
@app.route("/api", methods=["GET"])
def api():

    mobile = request.args.get("mobile")

    if not mobile:
        return jsonify({
            "status": False,
            "message": "mobile required"
        })

    uids = get_user_ids(mobile)

    if not uids:
        return jsonify({
            "status": False,
            "message": "No records found"
        })

    results = []

    for uid in uids:
        data = get_full(uid)
        if data:
            results.append(data)

    return jsonify({
        "status": True,
        "total": len(results),
        "data": results
    })


# ============================================
# 🚀 VERCEL HANDLER (MOST IMPORTANT)
# ============================================
def handler(request):
    return app(request.environ, lambda *args: None)
