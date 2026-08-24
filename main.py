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

ANDROID_VERSIONS = {
    "9": {"build_prefix": ["PPR1.180610.011"]},
    "10": {"build_prefix": ["QP1A.190711.020"]},
    "11": {"build_prefix": ["RP1A.200720.011"]},
    "12": {"build_prefix": ["SP1A.210812.016"]},
    "13": {"build_prefix": ["TP1A.220905.001"]},
    "14": {"build_prefix": ["UP1A.231005.007"]},
    "15": {"build_prefix": ["VP1A.241005.001"]},
    "16": {"build_prefix": ["WP1A.250305.001"]},
}

BRANDS = ["xiaomi", "realme", "samsung", "oneplus", "oppo", "vivo", "google"]
MODELS = {
    "xiaomi": ["Mi 11X", "Redmi Note 10"],
    "realme": ["RMX3031", "Realme GT"],
    "samsung": ["SM-G998B", "SM-A526B"],
    "oneplus": ["LE2115", "OnePlus Nord 2"],
    "oppo": ["CPH2207"],
    "vivo": ["V2024"],
    "google": ["Pixel 7"],
}


def format_phone_number(phone: str) -> Tuple[str, str]:
  phone = re.sub(r"[^0-9]", "", phone.strip())
  if not phone:
    return "+91", ""
  if phone.startswith("91") and len(phone) >= 12:
    return "+91", phone[2:]
  return "+91", phone[-10:] if len(phone) > 10 else phone


class LenskartFakeDevice:

  def __init__(self, phone: str, phone_code: str = "+91"):
    self.phone = phone
    self.phone_code = phone_code
    self.android_version = random.choice(list(ANDROID_VERSIONS.keys()))
    self.brand = random.choice(BRANDS)
    self.model = random.choice(MODELS.get(self.brand, ["RMX3031"]))
    self.udid = uuid.uuid4().hex[:16]
    self.advertising_id = str(uuid.uuid4())
    self.build_version = (
        random.choice(ANDROID_VERSIONS[self.android_version]["build_prefix"])
        + ".100"
    )
    self.session_token = None
    self.auth_token = None
    self.user_id = None
    self.customer_type = "EXISTING"
    self.s = requests.Session()
    self.x_assertion = self.generate_assertion()

  def generate_assertion(self) -> str:
    device_data = (
        f"{self.udid}:{self.advertising_id}:{self.brand}:{self.model}:{self.phone}:{time.time()}"
    )
    hash_obj = hashlib.sha256(device_data.encode())
    assertion = base64.b64encode(hash_obj.digest()).decode("utf-8")
    assertion = assertion.replace("+", "-").replace("/", "_")
    while len(assertion) < 120:
      assertion += "a"
    return assertion[:120]

  def base_headers(self) -> dict:
    h = {
        "Content-Type": "application/json; charset=UTF-8",
        "api_key": "valyoo123",
        "x-api-client": "android",
        "x-app-version": "5.8.2 (260713001)",
        "udid": self.udid,
        "uniqueId": self.advertising_id[:16],
        "brand": self.brand,
        "model": self.model,
        "User-Agent": (
            f"Dalvik/2.1.0 (Linux; U; Android {self.android_version};"
            f" {self.model} Build/{self.build_version})"
        ),
        "x-request-id": str(uuid.uuid4()),
    }
    if self.phone:
      h["x-customer-phone"] = self.phone
      h["x-customer-phone-code"] = self.phone_code.replace("+", "")
    if self.session_token:
      h["x-session-token"] = self.session_token
    if self.x_assertion:
      h["x-assertion"] = self.x_assertion
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
    return r.json() if r.status_code == 200 else None

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

  def claim_reward(self):
    steps = random.randint(30000, 48000)
    DAY_MS = 86400000
    now_utc_ms = int(time.time() * 1000)
    today_midnight = (now_utc_ms // DAY_MS) * DAY_MS

    body = []
    for i in range(6, -1, -1):
      ts = today_midnight - i * DAY_MS
      st = int(steps * (0.8 + (i / 20)))
      body.append(
          {"distance": round(st * 0.0007, 2), "steps": st, "timestamp": int(ts)}
      )

    params = {"campaignName": "run-for-frame"}
    r = self.s.post(
        f"{BASE}/v2/customers/bff/campaign/eligibility",
        json=body,
        params=params,
        headers=self.base_headers(),
    )
    return r.json() if r.status_code == 200 else None


app = Flask(__name__)
active_sessions: Dict[str, LenskartFakeDevice] = {}


@app.route("/")
def home():
  return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>🏃 RunForFrame Pro</title>
        <style>
            * { box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
            body { background: radial-gradient(circle at top, #1a1c3b 0%, #0d0e1e 100%); min-height: 100vh; display: flex; align-items: center; justify-content: center; padding: 15px; color: #fff; }
            .container { background: rgba(30, 32, 68, 0.6); backdrop-filter: blur(15px); border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 24px; width: 100%; max-width: 380px; padding: 28px 22px; box-shadow: 0 20px 50px rgba(0,0,0,0.5); text-align: center; }
            .icon { font-size: 42px; margin-bottom: 5px; animation: bounce 2s infinite; }
            @keyframes bounce { 0%, 100% { transform: translateY(0); } 50% { transform: translateY(-6px); } }
            h1 { font-size: 24px; font-weight: 800; background: linear-gradient(135deg, #a78bfa 0%, #f472b6 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-bottom: 4px; }
            .subtitle { font-size: 10px; letter-spacing: 2px; color: #7c8ba1; font-weight: 700; margin-bottom: 14px; text-transform: uppercase; }
            .status-badge { display: inline-flex; align-items: center; gap: 6px; background: rgba(16, 185, 129, 0.12); border: 1px solid rgba(16, 185, 129, 0.3); color: #34d399; font-size: 12px; font-weight: 600; padding: 5px 14px; border-radius: 20px; margin-bottom: 22px; }
            .status-dot { width: 6px; height: 6px; background: #34d399; border-radius: 50%; box-shadow: 0 0 8px #34d399; }
            .input-group { text-align: left; margin-bottom: 14px; }
            label { font-size: 10px; font-weight: 700; color: #94a3b8; letter-spacing: 1px; margin-bottom: 6px; display: block; }
            input { width: 100%; background: rgba(15, 23, 42, 0.6); border: 1px solid rgba(255, 255, 255, 0.12); border-radius: 12px; padding: 12px 14px; color: #fff; font-size: 14px; outline: none; transition: 0.3s; }
            input:focus { border-color: #6366f1; box-shadow: 0 0 12px rgba(99, 102, 241, 0.3); }
            input::placeholder { color: #475569; }
            .btn { width: 100%; padding: 13px; border-radius: 12px; border: none; font-size: 14px; font-weight: 700; cursor: pointer; transition: 0.2s; margin-top: 6px; display: flex; align-items: center; justify-content: center; gap: 8px; }
            .btn-primary { background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%); color: #fff; box-shadow: 0 4px 15px rgba(99, 102, 241, 0.4); }
            .btn-primary:active { transform: scale(0.98); }
            .btn-reset { background: rgba(255, 255, 255, 0.05); border: 1px solid rgba(255, 255, 255, 0.08); color: #94a3b8; margin-top: 10px; }
            .btn-verify { background: linear-gradient(135deg, #10b981 0%, #059669 100%); color: #fff; box-shadow: 0 4px 15px rgba(16, 185, 129, 0.4); margin-top: 10px; }
            .hidden { display: none; }
            #output { margin-top: 15px; font-size: 12px; border-radius: 10px; padding: 10px; background: rgba(0,0,0,0.3); border: 1px solid rgba(255,255,255,0.05); color: #cbd5e1; word-break: break-all; }
            .footer { margin-top: 22px; padding-top: 14px; border-top: 1px solid rgba(255, 255, 255, 0.06); display: flex; align-items: center; justify-content: center; gap: 8px; font-size: 12px; color: #64748b; }
            .footer-icon { width: 22px; height: 22px; background: #0284c7; border-radius: 50%; display: flex; align-items: center; justify-content: center; color: white; font-size: 10px; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="icon">🏃</div>
            <h1>RunForFrame Pro</h1>
            <div class="subtitle">LENSKART CAMPAIGN AUTOMATION</div>
            
            <div class="status-badge">
                <span class="status-dot"></span>
                <span id="statusText">System Ready</span>
            </div>

            <div id="step1">
                <div class="input-group">
                    <label>📱 PHONE NUMBER</label>
                    <input type="tel" id="phone" placeholder="Enter phone number (e.g., 987...)" maxlength="10">
                </div>
                <button class="btn btn-primary" onclick="sendOtp()">📱 Send OTP</button>
            </div>

            <div id="step2" class="hidden">
                <div class="input-group">
                    <label>🔑 ENTER OTP</label>
                    <input type="number" id="otp" placeholder="Enter 6-digit OTP">
                </div>
                <button class="btn btn-verify" onclick="verifyOtp()">⚡ Verify OTP & Claim Reward</button>
            </div>

            <button class="btn btn-reset" onclick="resetForm()">🔄 Reset</button>

            <div id="output" class="hidden"></div>

            <div class="footer">
                <div class="footer-icon">🚀</div>
                <span>Developed by <b>@rajlegend63</b></span>
            </div>
        </div>

        <script>
            async function sendOtp() {
                let p = document.getElementById('phone').value.trim();
                if(!p || p.length < 10){ alert('Please enter valid 10-digit phone number'); return; }
                
                showOutput('Sending OTP...');
                try {
                    let r = await fetch('/send-otp', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({phone: p})
                    });
                    let d = await r.json();
                    if(d.status){
                        document.getElementById('step1').classList.add('hidden');
                        document.getElementById('step2').classList.remove('hidden');
                        document.getElementById('statusText').innerText = 'OTP Sent! Waiting input...';
                        showOutput('OTP sent to ' + p + '. Enter OTP below.');
                    } else {
                        showOutput('Error: ' + (d.error || 'Failed to send OTP'));
                    }
                } catch(e) {
                    showOutput('Server connection error!');
                }
            }

            async function verifyOtp() {
                let p = document.getElementById('phone').value.trim();
                let o = document.getElementById('otp').value.trim();
                if(!o){ alert('Please enter OTP'); return; }

                showOutput('Verifying OTP & Bypassing Steps...');
                try {
                    let r = await fetch('/verify-otp', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({phone: p, otp: o})
                    });
                    let d = await r.json();
                    if(d.status === 'success'){
                        showOutput('🎉 SUCCESS! ' + (d.reward.giftVoucher ? ('Voucher: ' + d.reward.giftVoucher + ' | Tier: ' + d.reward.tier) : d.reward.message));
                        document.getElementById('statusText').innerText = 'Reward Processed!';
                    } else {
                        showOutput('Error: ' + (d.error || 'Verification failed'));
                    }
                } catch(e) {
                    showOutput('Verification Request Failed!');
                }
            }

            function resetForm() {
                document.getElementById('phone').value = '';
                document.getElementById('otp').value = '';
                document.getElementById('step1').classList.remove('hidden');
                document.getElementById('step2').classList.add('hidden');
                document.getElementById('output').classList.add('hidden');
                document.getElementById('statusText').innerText = 'System Ready';
            }

            function showOutput(msg) {
                let out = document.getElementById('output');
                out.classList.remove('hidden');
                out.innerText = msg;
            }
        </script>
    </body>
    </html>
    """


@app.route("/send-otp", methods=["POST"])
def api_send_otp():
  data = request.json or {}
  phone_raw = data.get("phone")
  if not phone_raw:
    return jsonify({"error": "Phone required"}), 400

  phone_code, phone = format_phone_number(phone_raw)
  device = LenskartFakeDevice(phone, phone_code)

  if device.create_session():
    res = device.send_otp()
    if res:
      active_sessions[phone] = device
      return jsonify({"status": True, "phone": phone})
  return jsonify({"error": "Failed to send OTP"}), 500


@app.route("/verify-otp", methods=["POST"])
def api_verify_otp():
  data = request.json or {}
  phone_raw = data.get("phone")
  otp = data.get("otp")

  if not phone_raw or not otp:
    return jsonify({"error": "Phone and OTP required"}), 400

  _, phone = format_phone_number(phone_raw)
  device = active_sessions.get(phone)

  if not device:
    return jsonify({"error": "Session expired"}), 400

  res = device.verify_otp(otp)
  if res:
    reward_res = device.claim_reward()
    return jsonify(
        {"status": "success", "reward": reward_res.get("result", {})}
    )
  return jsonify({"error": "Invalid OTP"}), 400


if __name__ == "__main__":
  app.run(host="0.0.0.0", port=5000)
