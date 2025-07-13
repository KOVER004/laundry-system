# app.py
from flask import Flask, jsonify, render_template, request
from sqlalchemy import create_engine, desc
from sqlalchemy.orm import sessionmaker
import paho.mqtt.client as mqtt
import json
import requests
from database import Base, Garment, DryingLog

app = Flask(__name__)

# --- ▼▼▼ 要修正 ▼▼▼ ---
PC2_DATABASE_IP = '192.168.10.118'  # PC2のIPアドレス
PI1_MQTT_BROKER_IP = '192.168.11.10' # Pi1のIPアドレス
SLACK_WEBHOOK_URL = 'https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXXXXXXXXXXXXXX'
# --- ▲▲▲ 設定ここまで ▲▲▲

# --- データベース設定 ---
DB_USER = 'Akiyuki'
DB_PASS = 'oda-Ak1yuk1'
DB_NAME = 'laundry_DB'
DATABASE_URI = f'mysql+pymysql://{DB_USER}:{DB_PASS}@{PC2_DATABASE_IP}/{DB_NAME}'
engine = create_engine(DATABASE_URI)
Session = sessionmaker(bind=engine)

# --- MQTTクライアント設定 ---
mqtt_client = mqtt.Client()

def setup_mqtt():
    try:
        mqtt_client.connect(PI1_MQTT_BROKER_IP, 1883, 60)
        print(f"[MQTT] Pi1 ({PI1_MQTT_BROKER_IP}) への接続に成功しました。")
    except Exception as e:
        print(f"[MQTT ERROR] Pi1への接続に失敗しました: {e}")

# --- Flaskルート定義 ---
@app.route('/')
def index():
    """操作画面(index.html)を表示"""
    return render_template('index.html')

@app.route('/garments', methods=['GET'])
def get_garments():
    """DBから衣類リストを取得してJSONで返す"""
    session = Session()
    try:
        garments = session.query(Garment).all()
        garment_list = [{"id": g.id, "name": g.name} for g in garments]
        return jsonify(garment_list)
    finally:
        session.close()

@app.route('/start_drying', methods=['POST'])
def start_drying():
    """乾燥開始の指令をPi1に送る"""
    data = request.json
    garment_id = data.get('garment_id')
    if not garment_id:
        return jsonify({"status": "error", "message": "Garment ID not provided"}), 400

    payload = json.dumps({"command": "start", "garment_id": garment_id})
    mqtt_client.publish('drying/control', payload)
    print(f"[MQTT] 乾燥開始指令を送信: {payload}")
    return jsonify({"status": "ok", "message": "Start command sent"})

@app.route('/latest_status', methods=['GET'])
def latest_status():
    """DBから最新の乾燥ログを取得して返す"""
    session = Session()
    try:
        latest_log = session.query(DryingLog).order_by(desc(DryingLog.timestamp)).first()
        if latest_log:
            return jsonify({
                "timestamp": latest_log.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                "dry_rate": latest_log.dry_rate,
                "temperature": latest_log.temperature,
                "humidity": latest_log.humidity,
                "predicted_hours": latest_log.predicted_hours,
                "predicted_minutes": latest_log.predicted_minutes
            })
        return jsonify({"error": "No data available"}), 404
    finally:
        session.close()

@app.route('/notify_slack', methods=['POST'])
def notify_slack():
    """Slackに予測時間を通知する"""
    data = request.json
    message = data.get('message')
    if not message:
        return jsonify({"status": "error", "message": "Message not provided"}), 400

    payload = {"text": message}
    try:
        requests.post(SLACK_WEBHOOK_URL, json=payload)
        print(f"[SLACK] 通知を送信しました: {message}")
        return jsonify({"status": "ok"})
    except Exception as e:
        print(f"[SLACK ERROR] 通知に失敗しました: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    setup_mqtt()
    app.run(host='0.0.0.0', port=5001, debug=True)