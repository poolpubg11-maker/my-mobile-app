import base64
from datetime import datetime
import hashlib
import json
import os
import random
import re
import socket
import time
import uuid

from flask import Flask, jsonify, render_template_string, request
import requests

app = Flask(__name__)

HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🏃 RunForFrame Pro</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Inter', sans-serif;
            min-height: 100vh;
            background: linear-gradient(135deg, #0f0c29, #302b63, #24243e);
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
            position: relative;
            overflow-x: hidden;
        }
        body::before {
            content: '';
            position: fixed;
            inset: 0;
            background: radial-gradient(2px 2px at 20% 30%, #eee, transparent),
                        radial-gradient(2px 2px at 40% 70%, #fff, transparent),
                        radial-gradient(2px 2px at 60% 20%, #eee, transparent),
                        radial-gradient(2px 2px at 80% 80%, #fff, transparent);
            background-size: 200px 200px;
            opacity: 0.1;
            animation: twinkle 4s ease-in-out infinite alternate;
            pointer-events: none;
        }
        @keyframes twinkle { 0% { opacity: 0.05; } 100% { opacity: 0.2; } }
        .container {
            background: rgba(255,255,255,0.05);
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
            border: 1px solid rgba(255,255,255,0.1);
            border-radius: 32px;
            padding: 40px;
            max-width: 560px;
            width: 100%;
            box-shadow: 0 25px 50px -12px rgba(0,0,0,0.8), inset 0 1px 0 rgba(255,255,255,0.1);
            position: relative;
            overflow: hidden;
        }
        .container::before {
            content: '';
            position: absolute;
            top: -50%; left: -50%; width: 200%; height: 200%;
            background: radial-gradient(circle at 30% 20%, rgba(99,102,241,0.1), transparent 60%);
            animation: glow 8s ease-in-out infinite alternate;
            pointer-events: none;
        }
        @keyframes glow { 0% { transform: translate(0,0); } 100% { transform: translate(10%,10%); } }
        .header { text-align: center; margin-bottom: 30px; position: relative; z-index: 1; }
        .logo { font-size: 48px; display: inline-block; animation: float 3s ease-in-out infinite; }
        @keyframes float { 0%,100% { transform: translateY(0); } 50% { transform: translateY(-10px); } }
        .header h1 {
            font-size: 34px; font-weight: 800;
            background: linear-gradient(135deg, #818cf8, #c084fc, #f472b6);
            -webkit-background-clip: text; -webkit-text-fill-color: transparent;
            letter-spacing: -0.5px;
        }
        .header .subtitle { color: rgba(255,255,255,0.5); font-size: 13px; letter-spacing: 2px; text-transform: uppercase; margin-top: 5px; }
        .status-badge {
            display: inline-block; padding: 6px 16px; background: rgba(16,185,129,0.2);
            border: 1px solid rgba(16,185,129,0.3); border-radius: 20px; color: #34d399;
            font-size: 12px; font-weight: 500; margin-top: 10px; animation: pulse 2s ease-in-out infinite;
        }
        @keyframes pulse { 0%,100% { opacity: 1; } 50% { opacity: 0.5; } }
        .input-section { position: relative; z-index: 1; }
        .form-group { margin-bottom: 20px; }
        .form-group label { display: block; color: rgba(255,255,255,0.6); font-size: 13px; font-weight: 500; margin-bottom: 8px; letter-spacing: 0.5px; text-transform: uppercase; }
        .input-wrapper { display: flex; gap: 12px; align-items: center; }
        .input-wrapper input {
            flex: 1; padding: 14px 18px; background: rgba(255,255,255,0.06);
            border: 1px solid rgba(255,255,255,0.1); border-radius: 14px; color: #fff;
            font-size: 16px; font-family: 'Inter', sans-serif; transition: all 0.3s ease; outline: none;
        }
        .input-wrapper input:focus { border-color: rgba(99,102,241,0.5); background: rgba(255,255,255,0.08); box-shadow: 0 0 0 4px rgba(99,102,241,0.1); }
        .input-wrapper input::placeholder { color: rgba(255,255,255,0.3); }
        .input-wrapper input:disabled { opacity: 0.5; cursor: not-allowed; }
        .btn-primary {
            padding: 14px 24px; background: linear-gradient(135deg, #818cf8, #6366f1);
            border: none; border-radius: 14px; color: #fff; font-size: 16px; font-weight: 600;
            cursor: pointer; transition: all 0.3s ease; font-family: 'Inter', sans-serif; white-space: nowrap;
        }
        .btn-primary:hover:not(:disabled) { transform: translateY(-2px); box-shadow: 0 10px 25px -5px rgba(99,102,241,0.4); }
        .btn-primary:active:not(:disabled) { transform: scale(0.98); }
        .btn-primary:disabled { opacity: 0.5; cursor: not-allowed; transform: none; }
        .btn-secondary {
            width: 100%; padding: 12px; background: rgba(255,255,255,0.05);
            border: 1px solid rgba(255,255,255,0.1); border-radius: 14px; color: rgba(255,255,255,0.5);
            font-size: 13px; font-weight: 500; cursor: pointer; transition: all 0.3s ease; font-family: 'Inter', sans-serif; margin-top: 10px;
        }
        .btn-secondary:hover { background: rgba(255,255,255,0.08); color: rgba(255,255,255,0.8); }
        .result-box { margin-top: 20px; padding: 20px; background: rgba(0,0,0,0.3); border-radius: 14px; border: 1px solid rgba(255,255,255,0.05); display: none; position: relative; z-index: 1; }
        .result-box.show { display: block; animation: slideIn 0.5s ease-out; }
        @keyframes slideIn { from { opacity: 0; transform: translateY(20px); } to { opacity: 1; transform: translateY(0); } }
        .voucher-line { display: flex; align-items: center; justify-content: space-between; gap: 15px; flex-wrap: wrap; }
        .voucher-code { font-size: 26px; font-weight: 700; color: #34d399; letter-spacing: 1px; word-break: break-all; }
        .copy-btn {
            padding: 8px 16px; background: rgba(16,185,129,0.15); border: 1px solid rgba(16,185,129,0.2);
            border-radius: 10px; color: #34d399; font-size: 14px; font-weight: 500; cursor: pointer;
            transition: all 0.3s ease; display: inline-flex; align-items: center; gap: 6px; font-family: 'Inter', sans-serif; white-space: nowrap;
        }
        .copy-btn:hover { background: rgba(16,185,129,0.25); transform: scale(1.05); }
        .copy-btn.copied { background: rgba(16,185,129,0.3); border-color: #34d399; }
        .validity { color: rgba(255,255,255,0.5); font-size: 14px; margin-top: 10px; }
        .validity span { color: rgba(255,255,255,0.8); font-weight: 500; }
        .message { padding: 12px 16px; border-radius: 10px; margin-top: 15px; font-size: 14px; display: none; position: relative; z-index: 1; }
        .message.show { display: block; animation: slideIn 0.3s ease-out; }
        .message.success { background: rgba(16,185,129,0.15); border: 1px solid rgba(16,185,129,0.2); color: #34d399; }
        .message.error { background: rgba(239,68,68,0.15); border: 1px solid rgba(239,68,68,0.2); color: #f87171; }
        .message.info { background: rgba(99,102,241,0.15); border: 1px solid rgba(99,102,241,0.2); color: #818cf8; }
        .footer { margin-top: 30px; text-align: center; position: relative; z-index: 1; padding-top: 20px; border-top: 1px solid rgba(255,255,255,0.05); }
        .footer .credit { display: inline-flex; align-items: center; gap: 10px; color: rgba(255,255,255,0.3); font-size: 14px; text-decoration: none; padding: 8px 20px; border-radius: 12px; background: rgba(255,255,255,0.03); transition: all 0.3s ease; }
        .footer .credit:hover { color: rgba(255,255,255,0.7); background: rgba(255,255,255,0.06); transform: translateY(-2px); }
        .footer .credit .telegram-icon { width: 28px; height: 28px; background: linear-gradient(135deg, #0088cc, #004d7a); border-radius: 50%; display: inline-flex; align-items: center; justify-content: center; font-size: 16px; color: #fff; transition: all 0.3s ease; }
        .footer .credit:hover .telegram-icon { transform: scale(1.1) rotate(-5deg); }
        .footer .credit .username { font-weight: 600; background: linear-gradient(135deg, #818cf8, #c084fc); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
        .spinner { display: none; width: 20px; height: 20px; border: 2px solid rgba(255,255,255,0.1); border-top-color: #fff; border-radius: 50%; animation: spin 0.8s linear infinite; margin: 0 auto; }
        @keyframes spin { to { transform: rotate(360deg); } }
        .btn-content { display: flex; align-items: center; justify-content: center; gap: 8px; }
        @media (max-width: 640px) {
            .container { padding: 24px; border-radius: 24px; }
            .header h1 { font-size: 28px; }
            .input-wrapper { flex-direction: column; }
            .btn-primary { width: 100%; justify-content: center; }
            .voucher-line { flex-direction: column; align-items: flex-start; }
            .copy-btn { width: 100%; justify-content: center; }
        }
    </style>
</head>
<body>
<div class="container">
    <div class="header">
        <div class="logo">🏃</div>
        <h1>RunForFrame Pro</h1>
        <div class="subtitle">Lenskart Campaign Automation</div>
        <div class="status-badge" id="statusBadge">● System Ready</div>
    </div>

    <div class="input-section">
        <div class="form-group">
            <label id="inputLabel">📱 Phone Number</label>
            <div class="input-wrapper">
                <input type="text" id="mainInput" placeholder="Enter phone number (e.g., 9876543210)" autocomplete="off">
                <button class="btn-primary" id="actionBtn" onclick="handleAction()">
                    <span class="btn-content">
                        <span id="btnIcon">📱</span>
                        <span id="btnText">Send OTP</span>
                        <span class="spinner" id="spinner"></span>
                    </span>
                </button>
            </div>
        </div>

        <button class="btn-secondary" onclick="resetAll()">🔄 Reset</button>
    </div>

    <div class="message" id="message"></div>

    <div class="result-box" id="resultBox">
        <div class="voucher-line">
            <span class="voucher-code" id="voucherCode">---</span>
            <button class="copy-btn" id="copyBtn" onclick="copyVoucher()">📋 Copy</button>
        </div>
        <div class="validity">⏳ Valid till: <span id="validityDate">---</span></div>
    </div>

    <div class="footer">
        <a href="https://t.me/rajlegend63" target="_blank" class="credit">
            <span class="telegram-icon">✈️</span>
            <span>Developed by <span class="username">@rajlegend63</span></span>
        </a>
    </div>
</div>
"""
HTML += """
<script>
    let currentStep = 'phone';
    let phoneNumber = '';
    let currentVoucher = '';

    function showMessage(text, type = 'info') {
        const msg = document.getElementById('message');
        msg.textContent = text;
        msg.className = 'message show ' + type;
    }

    function hideMessage() { document.getElementById('message').className = 'message'; }

    function showVoucher(voucher, expiry) {
        const box = document.getElementById('resultBox');
        document.getElementById('voucherCode').textContent = voucher;
        document.getElementById('validityDate').textContent = expiry || 'Not specified';
        box.className = 'result-box show';
        currentVoucher = voucher;
    }

    function hideVoucher() {
        document.getElementById('resultBox').className = 'result-box';
        currentVoucher = '';
    }

    function updateStatus(text, color = '#34d399') {
        const badge = document.getElementById('statusBadge');
        badge.textContent = '● ' + text;
        badge.style.color = color;
        badge.style.borderColor = color;
        badge.style.background = color + '33';
    }

    function setLoading(loading) {
        const btn = document.getElementById('actionBtn');
        const spinner = document.getElementById('spinner');
        const btnText = document.getElementById('btnText');
        const btnIcon = document.getElementById('btnIcon');
        btn.disabled = loading;
        if (loading) {
            spinner.style.display = 'inline-block';
            btnText.textContent = 'Processing...';
            btnIcon.textContent = '⏳';
        } else {
            spinner.style.display = 'none';
        }
    }

    function resetAll() {
        currentStep = 'phone';
        phoneNumber = '';
        document.getElementById('mainInput').value = '';
        document.getElementById('mainInput').disabled = false;
        document.getElementById('mainInput').placeholder = 'Enter phone number (e.g., 9876543210)';
        document.getElementById('inputLabel').textContent = '📱 Phone Number';
        document.getElementById('btnText').textContent = 'Send OTP';
        document.getElementById('btnIcon').textContent = '📱';
        hideMessage();
        hideVoucher();
        updateStatus('System Ready');
        document.getElementById('mainInput').focus();
    }

    async function handleAction() {
        const input = document.getElementById('mainInput');
        const val = input.value.trim();

        if (currentStep === 'phone') {
            if (!val || val.length < 10) {
                showMessage('⚠️ Please enter a valid 10-digit phone number', 'error');
                return;
            }
            phoneNumber = val;
            setLoading(true);
            hideMessage();
            hideVoucher();
            updateStatus('Sending OTP...', '#f59e0b');

            try {
                const resp = await fetch('/send-otp', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ phone: phoneNumber })
                });
                const data = await resp.json();
                if (data.success) {
                    showMessage('✅ OTP sent! Check your phone.', 'success');
                    updateStatus('OTP Sent', '#34d399');
                    currentStep = 'otp';
                    input.value = '';
                    input.placeholder = 'Enter OTP (e.g., 1234)';
                    document.getElementById('inputLabel').textContent = '🔑 OTP Verification';
                    document.getElementById('btnText').textContent = 'Verify OTP';
                    document.getElementById('btnIcon').textContent = '🔑';
                    input.focus();
                } else {
                    showMessage('❌ ' + (data.error || 'Failed to send OTP'), 'error');
                    updateStatus('Failed', '#ef4444');
                }
            } catch (e) {
                showMessage('❌ Connection error: ' + e.message, 'error');
                updateStatus('Error', '#ef4444');
            } finally {
                setLoading(false);
            }
        }
        else if (currentStep === 'otp') {
            const otp = val;
            if (!otp || otp.length < 4) {
                showMessage('⚠️ Please enter the OTP', 'error');
                return;
            }
            setLoading(true);
            hideMessage();
            updateStatus('Verifying OTP...', '#f59e0b');

            try {
                const resp = await fetch('/verify-otp', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        phone: phoneNumber,
                        otp: otp
                    })
                });
                const data = await resp.json();
                if (data.success) {
                    showVoucher(data.voucher, data.expiry);
                    showMessage('🎉 Voucher generated successfully!', 'success');
                    updateStatus('Completed', '#34d399');
                    currentStep = 'done';
                    document.getElementById('btnText').textContent = '✅ Done';
                    document.getElementById('btnIcon').textContent = '🎉';
                    document.getElementById('mainInput').disabled = true;
                } else {
                    let errMsg = data.error || 'OTP verification failed';
                    if (errMsg.toLowerCase().includes('already') || errMsg.toLowerCase().includes('claimed')) {
                        showMessage('⚠️ ' + errMsg, 'error');
                        hideVoucher();
                    } else {
                        showMessage('❌ ' + errMsg, 'error');
                    }
                    updateStatus('Failed', '#ef4444');
                }
            } catch (e) {
                showMessage('❌ Connection error: ' + e.message, 'error');
                updateStatus('Error', '#ef4444');
            } finally {
                setLoading(false);
            }
        }
    }

    function copyVoucher() {
        const code = document.getElementById('voucherCode').textContent;
        if (!code || code === '---') return;
        navigator.clipboard.writeText(code).then(() => {
            const btn = document.getElementById('copyBtn');
            btn.classList.add('copied');
            btn.innerHTML = '✅ Copied!';
            setTimeout(() => {
                btn.classList.remove('copied');
                btn.innerHTML = '📋 Copy';
            }, 2000);
        }).catch(() => {
            const range = document.createRange();
            const el = document.getElementById('voucherCode');
            range.selectNode(el);
            window.getSelection().removeAllRanges();
            window.getSelection().addRange(range);
            document.execCommand('copy');
            alert('Voucher copied!');
        });
    }

    document.addEventListener('keydown', function(e) {
        if (e.key === 'Enter') {
            const active = document.activeElement;
            if (active.id === 'mainInput') { handleAction(); }
        }
    });

    window.onload = function() { document.getElementById('mainInput').focus(); };
</script>
</body>
</html>
"""

BASE = "https://api-gateway.juno.lenskart.com"

def normalize_phone(phone):
    phone = re.sub(r'[+\s\-\(\)]', '', phone)
    if phone.startswith('91') and len(phone) >= 12:
        phone = phone[2:]
    if len(phone) == 10 and phone.isdigit():
        return phone
    return None

class DeviceEngine:
    def __init__(self, phone):
        self.phone = phone
        self.phone_code = "+91"
        self.udid = uuid.uuid4().hex[:16]
        self.advertising_id = str(uuid.uuid4())
        self.brand = random.choice(["xiaomi", "realme", "samsung", "oneplus"])
        self.model = random.choice(["Mi 11X", "RMX3031", "SM-G998B", "OnePlus Nord 2"])
        self.android_version = "13"
        self.build_version = "TP1A.220905.001"
        self.session_token = None
        self.auth_token = None
        self.s = requests.Session()
        self.x_assertion = self._assertion()

    def _assertion(self):
        d = f"{self.udid}:{self.advertising_id}:{self.brand}:{self.model}:{self.phone}:{time.time()}"
        h = hashlib.sha256(d.encode())
        return base64.b64encode(h.digest()).decode().replace('+', '-').replace('/', '_')[:100]

    def headers(self, extra=None):
        h = {
            "Content-Type": "application/json",
            "api_key": "valyoo123",
            "x-api-client": "android",
            "x-app-version": "5.8.2",
            "udid": self.udid,
            "brand": self.brand,
            "model": self.model,
            "x-customer-phone": self.phone,
            "x-customer-phone-code": "91",
            "x-assertion": self.x_assertion,
            "User-Agent": f"Dalvik/2.1.0 (Linux; U; Android {self.android_version}; {self.model})"
        }
        if self.session_token:
            h["x-session-token"] = self.session_token
        if extra:
            h.update(extra)
        return h

    def create_session(self):
        try:
            r = self.s.post(f"{BASE}/v2/sessions", headers=self.headers(), json={})
            if r.status_code == 200:
                self.session_token = r.json().get("result", {}).get("id")
                return True
        except Exception:
            pass
        return False

    def send_otp(self):
        try:
            body = {"phoneCode": "+91", "telephone": self.phone}
            r = self.s.post(f"{BASE}/v3/customers/sendOtp", headers=self.headers(), json=body)
            return r.status_code == 200
        except Exception:
            return False

    def verify_otp(self, otp):
        try:
            body = {"code": otp, "phoneCode": "+91", "telephone": self.phone}
            r = self.s.post(f"{BASE}/v2/customers/authenticate/mobile", headers=self.headers(), json=body)
            if r.status_code == 200:
                data = r.json()
                self.auth_token = data.get("result", {}).get("token")
                if self.auth_token:
                    self.session_token = self.auth_token
                    return True
        except Exception:
            pass
        return False

    def claim_reward(self):
        try:
            DAY_MS = 86400000
            ist_offset = 5.5 * 3600 * 1000
            now_utc = int(time.time() * 1000)
            now_ist = now_utc + ist_offset
            midnight_ist = (now_ist // DAY_MS) * DAY_MS
            midnight_utc = midnight_ist - ist_offset
            steps_data = []
            for i in range(6, -1, -1):
                ts = midnight_utc - i * DAY_MS
                steps_data.append({
                    "distance": 0.0,
                    "steps": 35000 if i == 0 else 0,
                    "timestamp": int(ts)
                })
            params = {"campaignName": "run-for-frame"}
            url = f"{BASE}/v2/customers/bff/campaign/eligibility"
            r = self.s.post(url, headers=self.headers(), json=steps_data, params=params)
            if r.status_code == 200:
                data = r.json()
                result = data.get("result", {})
                voucher = result.get("giftVoucher")
                if voucher:
                    expiry = result.get("giftVoucherExpiryDate")
                    expiry_dt = datetime.fromtimestamp(expiry / 1000).strftime("%d %b %Y") if expiry else "Not specified"
                    return {"success": True, "voucher": voucher, "expiry": expiry_dt}
                else:
                    msg = result.get("message", "No voucher generated")
                    return {"success": False, "error": msg}
            return {"success": False, "error": f"API Error: {r.status_code}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

active_sessions = {}

@app.route('/')
def index():
    return render_template_string(HTML)

@app.route('/send-otp', methods=['POST'])
def send_otp():
    data = request.json or {}
    raw_phone = data.get('phone', '').strip()
    phone = normalize_phone(raw_phone)
    if not phone:
        return jsonify({'success': False, 'error': 'Invalid phone number'})

    engine = DeviceEngine(phone)
    if engine.create_session() and engine.send_otp():
        active_sessions[phone] = engine
        return jsonify({'success': True})
    return jsonify({'success': False, 'error': 'OTP send failed'})

@app.route('/verify-otp', methods=['POST'])
def verify_otp():
    data = request.json or {}
    raw_phone = data.get('phone', '').strip()
    otp = data.get('otp', '').strip()
    phone = normalize_phone(raw_phone)
    if not phone or not otp:
        return jsonify({'success': False, 'error': 'Missing phone or OTP'})

    engine = active_sessions.get(phone)
    if not engine:
        engine = DeviceEngine(phone)
        if not engine.create_session():
            return jsonify({'success': False, 'error': 'Session initialization failed'})

    if engine.verify_otp(otp):
        res = engine.claim_reward()
        return jsonify(res)
    else:
        return jsonify({'success': False, 'error': 'Invalid OTP or Verification failed'})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
    
