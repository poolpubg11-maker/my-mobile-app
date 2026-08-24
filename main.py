import base64
from datetime import datetime
import hashlib
import json
import os
import random
import re
import sys
import threading
import time
from typing import Dict, List, Optional, Set, Tuple
import uuid

from flask import Flask, jsonify, request
import requests

BASE = "https://api-gateway.juno.lenskart.com"
MAX_RETRIES = 3
REQUEST_DELAY = (1, 3)

CONFIG = {
    "threads": 5,
    "steps_range": (25000, 50000),
    "retry_on_fail": True,
    "save_vouchers": True,
    "use_proxy": False,
    "proxy_list": [],
}

ANDROID_VERSIONS = {
    "9": {
        "api": 28,
        "build_prefix": [
            "PPR1.180610.011",
            "PPR2.180905.006",
            "PKQ1.190502.001",
        ],
        "codename": "Pie",
    },
    "10": {
        "api": 29,
        "build_prefix": [
            "QP1A.190711.020",
            "QP1A.191005.007",
            "QQ3A.200805.001",
        ],
        "codename": "Queen Cake",
    },
    "11": {
        "api": 30,
        "build_prefix": [
            "RP1A.200720.011",
            "RP1A.201005.001",
            "RQ3A.210605.001",
        ],
        "codename": "Red Velvet Cake",
    },
    "12": {
        "api": 31,
        "build_prefix": [
            "SP1A.210812.016",
            "SP2A.220305.013",
            "SQ3A.220705.003",
        ],
        "codename": "Snow Cone",
    },
    "13": {
        "api": 33,
        "build_prefix": [
            "TP1A.220905.001",
            "TP1A.221105.001",
            "TQ3A.230901.001",
        ],
        "codename": "Tiramisu",
    },
    "14": {
        "api": 34,
        "build_prefix": [
            "UP1A.231005.007",
            "UQ1A.240105.002",
            "UR1A.240305.001",
        ],
        "codename": "Upside Down Cake",
    },
    "15": {
        "api": 35,
        "build_prefix": [
            "VP1A.241005.001",
            "VP2A.241205.003",
            "VQ1A.250205.001",
        ],
        "codename": "Vanilla Ice Cream",
    },
    "16": {
        "api": 36,
        "build_prefix": [
            "WP1A.250305.001",
            "WP2A.250505.003",
            "WQ1A.250705.001",
        ],
        "codename": "White Chocolate",
    },
}

BRANDS = [
    "xiaomi",
    "realme",
    "samsung",
    "oneplus",
    "oppo",
    "vivo",
    "google",
    "motorola",
    "nothing",
    "asus",
    "lenovo",
    "lg",
    "sony",
    "huawei",
    "honor",
    "tecno",
    "infinix",
    "itel",
    "micromax",
    "lava",
    "karbonn",
    "nokia",
    "htc",
]

MODELS = {
    "xiaomi": [
        "Mi 11X",
        "Redmi Note 10",
        "Mi 10",
        "Poco X3",
        "Mi 11T",
        "Redmi 9",
        "Mi 11 Lite",
        "Redmi Note 11",
        "Poco F3",
        "Mi 10T",
        "Redmi 9A",
        "Mi 10i",
    ],
    "realme": [
        "RMX3031",
        "RMX3370",
        "RMX3360",
        "RMX3263",
        "RMX3461",
        "RMX3381",
        "Realme 8",
        "Realme 9 Pro",
        "Realme GT",
        "Realme Narzo 50",
    ],
    "samsung": [
        "SM-G998B",
        "SM-G991B",
        "SM-A526B",
        "SM-M515F",
        "SM-G990B",
        "SM-A536B",
        "SM-A127F",
        "SM-A225F",
        "SM-G780G",
        "SM-A325F",
        "SM-M325F",
    ],
    "oneplus": [
        "LE2115",
        "LE2125",
        "KB2001",
        "IN2015",
        "NE2215",
        "OnePlus 9R",
        "OnePlus Nord 2",
        "OnePlus 9 Pro",
        "OnePlus 10 Pro",
    ],
    "oppo": [
        "CPH2207",
        "CPH2249",
        "CPH2217",
        "CPH2359",
        "CPH2371",
        "Reno 8",
        "Reno 6 Pro",
        "Find X5 Pro",
    ],
    "vivo": [
        "V2024",
        "V2036",
        "V2041",
        "V2115",
        "V2138",
        "V2156",
        "T1 Pro",
        "X70 Pro",
        "V23 Pro",
    ],
    "google": [
        "Pixel 6",
        "Pixel 7",
        "Pixel 6a",
        "Pixel 7a",
        "Pixel 8",
        "Pixel 8 Pro",
    ],
    "motorola": ["Moto G71", "Moto G62", "Moto Edge 30", "Moto G52", "Moto G42"],
    "nothing": ["Nothing Phone 1", "Nothing Phone 2"],
    "asus": ["ROG Phone 5", "ZenFone 8", "ROG Phone 6", "ZenFone 9"],
    "lenovo": ["Legion Phone Duel", "K14 Note", "K12 Note", "P12 Pro"],
    "lg": ["LG Velvet", "LG Wing", "LG G8X", "LG V60"],
    "sony": ["Xperia 1 III", "Xperia 5 III", "Xperia 10 III", "Xperia Pro-I"],
    "huawei": ["P40 Pro", "Mate 40 Pro", "Nova 9", "Nova 10 Pro"],
    "honor": ["Honor 50", "Honor 70", "Honor X9", "Honor Magic 4"],
    "tecno": ["Camon 19 Pro", "Spark 9T", "Pova 5", "Camon 20 Pro"],
    "infinix": ["Zero 30", "Note 12", "Hot 40", "Smart 8"],
    "itel": ["A60", "P40", "A36", "P55"],
    "micromax": ["IN Note 2", "IN 2B", "IN 2C", "Canvas 6"],
    "lava": ["Z61", "Z71", "A51", "P7"],
    "karbonn": ["A51", "A55", "K50", "K60"],
    "nokia": ["Nokia G21", "Nokia G50", "Nokia X20", "Nokia XR20"],
    "htc": ["Desire 22 Pro", "U20", "Wildfire E3", "Desire 21 Pro"],
}


class JSONDatabase:

  def __init__(self):
    self.x_assertions_file = "/tmp/x_assertions.json"
    self.vouchers_file = "/tmp/vouchers.json"
    self.attempts_file = "/tmp/attempts.json"
    self.accounts_file = "/tmp/accounts.json"
    self._init_json_files()
    self.used_assertions = set()
    self.load_data()

  def _init_json_files(self):
    files = {
        self.x_assertions_file: [],
        self.vouchers_file: [],
        self.attempts_file: [],
        self.accounts_file: [],
    }
    for file_path, default_data in files.items():
      if not os.path.exists(file_path):
        with open(file_path, "w", encoding="utf-8") as f:
          json.dump(default_data, f, indent=2, ensure_ascii=False)

  def load_data(self):
    try:
      with open(self.x_assertions_file, "r", encoding="utf-8") as f:
        assertions = json.load(f)
        self.used_assertions = {
            a["assertion"] for a in assertions if a.get("used_at")
        }
    except Exception:
      self.used_assertions = set()

  def is_assertion_used(self, assertion: str) -> bool:
    return assertion in self.used_assertions

  def save_assertion(
      self,
      assertion: str,
      phone: str = "",
      device_brand: str = "",
      device_model: str = "",
      android_version: str = "",
      udid: str = "",
  ):
    try:
      with open(self.x_assertions_file, "r", encoding="utf-8") as f:
        data = json.load(f)
      for item in data:
        if item["assertion"] == assertion:
          if not item.get("used_at"):
            item["used_at"] = datetime.now().isoformat()
            item["phone"] = phone
            item["device_brand"] = device_brand
            item["device_model"] = device_model
            item["android_version"] = android_version
            item["udid"] = udid
          with open(self.x_assertions_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
          self.used_assertions.add(assertion)
          return True
      data.append({
          "assertion": assertion,
          "phone": phone,
          "device_brand": device_brand,
          "device_model": device_model,
          "android_version": android_version,
          "udid": udid,
          "created_at": datetime.now().isoformat(),
          "used_at": datetime.now().isoformat() if phone else None,
      })
      with open(self.x_assertions_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
      if phone:
        self.used_assertions.add(assertion)
      return True
    except Exception:
      return False


db = JSONDatabase()


def format_phone_number(phone: str) -> Tuple[str, str]:
  phone = re.sub(r"[^0-9]", "", phone.strip())
  if not phone:
    return "+91", ""
  if phone.startswith("91") and len(phone) >= 12:
    return "+91", phone[2:]
  elif len(phone) == 10:
    return "+91", phone
  else:
    return "+91", phone[-10:] if len(phone) > 10 else phone


class LenskartFakeDevice:

  def __init__(
      self, phone: str, phone_code: str = "+91", proxy: Optional[str] = None
  ):
    self.phone = phone
    self.phone_code = phone_code
    self.proxy = proxy
    self.android_version = random.choice(list(ANDROID_VERSIONS.keys()))
    self.android_data = ANDROID_VERSIONS[self.android_version]
    self.brand = random.choice(BRANDS)
    self.model = random.choice(MODELS.get(self.brand, ["RMX3031"]))
    self.udid = uuid.uuid4().hex[:16]
    self.advertising_id = str(uuid.uuid4())
    self.build_version = (
        random.choice(self.android_data["build_prefix"])
        + f".{random.randint(1, 999)}"
    )
    self.session_token = None
    self.auth_token = None
    self.user_id = None
    self.customer_type = "EXISTING"
    self.s = requests.Session()
    self.x_assertion = self.generate_unique_x_assertion()

  def generate_unique_x_assertion(self) -> str:
    device_data = f"{self.udid}:{self.advertising_id}:{self.brand}:{self.model}:{self.phone}:{time.time()}:{random.randint(1, 999999)}"
    hash_obj = hashlib.sha256(device_data.encode())
    assertion = base64.b64encode(hash_obj.digest()).decode("utf-8")
    assertion = assertion.replace("+", "-").replace("/", "_")
    while len(assertion) < 120:
      assertion += random.choice(
          "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_"
      )
    return assertion[:120]

  def base_headers(self, extra: dict | None = None) -> dict:
    h = {
        "Content-Type": "application/json; charset=UTF-8",
        "api_key": "valyoo123",
        "x-api-client": "android",
        "x-app-version": "5.8.2 (260713001)",
        "appversion": "5.8.2 (260713001)",
        "X-Build-Version": "260713001",
        "x-country-code": "IN",
        "x-country-code-override": "IN",
        "x-accept-language": "en",
        "accept-language": "en",
        "x-customer-type": self.customer_type,
        "udid": self.udid,
        "uniqueId": self.advertising_id[:16],
        "brand": self.brand,
        "model": self.model,
        "x-b3-traceid": str(
            int(time.time() * 1000) + random.randint(1, 1000)
        ),
        "User-Agent": (
            f"Dalvik/2.1.0 (Linux; U; Android {self.android_version};"
            f" {self.model} Build/{self.build_version})"
        ),
        "Accept-Encoding": "gzip",
        "Connection": "Keep-Alive",
        "x-request-id": str(uuid.uuid4()),
    }
    if self.phone:
      h["x-customer-phone"] = self.phone
      h["x-customer-phone-code"] = self.phone_code.replace("+", "")
    if self.session_token:
      h["x-session-token"] = self.session_token
    if self.x_assertion:
      h["x-assertion"] = self.x_assertion
    if extra:
      h.update(extra)
    return h

  def create_session(self):
    r = self.s.post(
        f"{BASE}/v2/sessions", json={}, headers=self.base_headers()
    )
    if r.status_code == 200:
      self.session_token = r.json().get("result", {}).get("id")
      return True
    return False

  def send_otp(self):
    body = {"phoneCode": self.phone_code, "telephone": self.phone}
    r = self.s.post(
        f"{BASE}/v3/customers/sendOtp", json=body, headers=self.base_headers()
    )
    if r.status_code == 200:
      return r.json()
    return None

  def verify_otp(self, code: str):
    body = {"code": code, "phoneCode": self.phone_code, "telephone": self.phone}
    r = self.s.post(
        f"{BASE}/v2/customers/authenticate/mobile",
        json=body,
        headers=self.base_headers(),
    )
    if r.status_code == 200:
      res = r.json().get("result") or {}
      self.auth_token = res.get("token")
      self.user_id = res.get("user_id")
      if self.auth_token:
        self.session_token = self.auth_token
        return res
    return None


app = Flask(__name__)
active_sessions: Dict[str, LenskartFakeDevice] = {}


@app.route("/")
def home():
  return jsonify(
      {"status": "running", "service": "Lenskart Run For Frame API"}
  )


@app.route("/send-otp", methods=["POST"])
def api_send_otp():
  data = request.json or {}
  phone_raw = data.get("phone")
  if not phone_raw:
    return jsonify({"error": "phone number required"}), 400

  phone_code, phone = format_phone_number(phone_raw)
  device = LenskartFakeDevice(phone, phone_code)

  if device.create_session():
    res = device.send_otp()
    if res:
      active_sessions[phone] = device
      return jsonify({"status": "OTP Sent Successfully", "phone": phone})
  return jsonify({"error": "Failed to send OTP"}), 500


@app.route("/verify-otp", methods=["POST"])
def api_verify_otp():
  data = request.json or {}
  phone_raw = data.get("phone")
  otp = data.get("otp")

  if not phone_raw or not otp:
    return jsonify({"error": "phone and otp required"}), 400

  _, phone = format_phone_number(phone_raw)
  device = active_sessions.get(phone)

  if not device:
    return jsonify(
        {"error": "Session not found. Please send OTP first."}
    ), 400

  res = device.verify_otp(otp)
  if res:
    return jsonify({
        "status": "OTP Verified Successfully",
        "user_id": device.user_id,
    })
  return jsonify({"error": "Invalid OTP or Verification Failed"}), 400


if __name__ == "__main__":
  app.run(host="0.0.0.0", port=5000)
  
