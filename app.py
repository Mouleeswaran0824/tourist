from flask import Flask, render_template, request, redirect, url_for, session, send_file, jsonify
import pandas as pd
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = "admin_secret_key"

EXCEL_FILE = "tourist_data.xlsx"
SOS_FILE = "sos_alerts.xlsx"

ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin1234"


# ---------------- HOME (Tourist Login) ----------------
@app.route('/')
def home():
    return render_template('login.html')


# ---------------- TOURIST LOGIN ----------------
@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    location = request.form['location']
    time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    new_data = {
        "Name": username,
        "Location": location,
        "Login Time": time
    }

    if os.path.exists(EXCEL_FILE):
        df = pd.read_excel(EXCEL_FILE)
        df = pd.concat([df, pd.DataFrame([new_data])], ignore_index=True)
    else:
        df = pd.DataFrame([new_data])

    df.to_excel(EXCEL_FILE, index=False)

    return render_template(
        "dashboard.html",
        username=username,
        location=location,
        status="SAFE"
    )


# ---------------- SOS BUTTON (FIRST SOS HIT) ----------------
@app.route('/sos', methods=['POST'])
def sos():
    username = request.form['username']
    location = request.form['location']
    latitude = request.form.get('latitude')
    longitude = request.form.get('longitude')
    time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    sos_data = {
        "Name": username,
        "Location": location,
        "Latitude": latitude,
        "Longitude": longitude,
        "Status": "DANGER",
        "Time": time
    }

    if os.path.exists(SOS_FILE):
        df = pd.read_excel(SOS_FILE)
        df = pd.concat([df, pd.DataFrame([sos_data])], ignore_index=True)
    else:
        df = pd.DataFrame([sos_data])

    df.to_excel(SOS_FILE, index=False)

    return render_template(
        "dashboard.html",
        username=username,
        location=location,
        status="DANGER"
    )


# ---------------- LIVE GPS UPDATE (PHASE 6.2) ----------------
@app.route('/update_location', methods=['POST'])
def update_location():
    data = request.get_json()

    username = data.get("username")
    latitude = data.get("latitude")
    longitude = data.get("longitude")

    if not os.path.exists(SOS_FILE):
        return jsonify({"status": "file_missing"})

    df = pd.read_excel(SOS_FILE)

    # update latest record of that user
    df.loc[df['Name'] == username, 'Latitude'] = latitude
    df.loc[df['Name'] == username, 'Longitude'] = longitude

    df.to_excel(SOS_FILE, index=False)

    return jsonify({"status": "updated"})


# ---------------- ADMIN LOGIN PAGE ----------------
@app.route('/admin_login')
def admin_login():
    return render_template('admin_login.html')


# ---------------- ADMIN LOGIN CHECK ----------------
@app.route('/admin_login', methods=['POST'])
def admin_login_post():
    username = request.form['username']
    password = request.form['password']

    if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
        session['admin_logged_in'] = True
        return redirect(url_for('admin'))
    else:
        return render_template('admin_login.html', error="Invalid admin credentials")


# ---------------- ADMIN DASHBOARD ----------------
@app.route('/admin')
def admin():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))

    alerts = []

    if os.path.exists(SOS_FILE):
        df = pd.read_excel(SOS_FILE)

        for _, row in df.iterrows():
            location_text = str(row.get("Location", "")).lower()
            lat = row.get("Latitude")
            lon = row.get("Longitude")

            # -------- RISK ZONE LOGIC (FIXED & LOGICAL) --------
            if any(city in location_text for city in
                   ["chennai", "coimbatore", "bangalore", "kochi", "trivandrum", "madurai"]):
                risk_zone = "Urban"
            elif pd.notna(lat) and pd.notna(lon):
                risk_zone = "Semi-Remote"
            else:
                risk_zone = "Remote"

            alerts.append({
                "Name": row.get("Name"),
                "Location": row.get("Location"),
                "Latitude": lat,
                "Longitude": lon,
                "Status": row.get("Status"),
                "Time": row.get("Time"),
                "RiskZone": risk_zone
            })

    return render_template("admin.html", alerts=alerts)


# ---------------- GET ALERTS (AUTO REFRESH SUPPORT) ----------------
@app.route('/get_alerts')
def get_alerts():
    if not session.get('admin_logged_in'):
        return jsonify([])

    if not os.path.exists(SOS_FILE):
        return jsonify([])

    df = pd.read_excel(SOS_FILE)
    return jsonify(df.to_dict(orient="records"))


# ---------------- DOWNLOAD SOS EXCEL ----------------
@app.route('/download_sos')
def download_sos():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))

    if os.path.exists(SOS_FILE):
        return send_file(SOS_FILE, as_attachment=True)

    return "No SOS data available"


# ---------------- ADMIN LOGOUT ----------------
@app.route('/admin_logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    return redirect(url_for('admin_login'))


# ---------------- RUN APP ----------------
if __name__ == "__main__":
    app.run(debug=True)
