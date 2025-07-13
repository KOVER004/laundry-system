# main.py   Pi1に保存させる
import paho.mqtt.client as mqtt
import time
import json
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import threading

from compare import CompareClass
from PredictClass import DryingPredictor
from database import Base, Garment, DryingLog

# --- ▼▼▼ 要修正 ▼▼▼ ---
PC2_DATABASE_IP = '192.168.10.118' # PC2のIPアドレス
# --- ▲▲▲ 設定ここまで ▲▲▲

# --- MQTT設定 ---
MQTT_BROKER = "localhost" # 自分自身がブローカー
MQTT_PORT = 1883
CONTROL_TOPIC = "drying/control"
SENSOR_TOPICS = [("sensor/temperature", 0), ("sensor/humidity", 0), ("sensor/weight", 0)]

# --- データベース設定 ---
DB_USER = 'Akiyuki'
DB_PASS = 'oda-Ak1yuk1'
DB_NAME = 'laundry_DB'
DATABASE_URI = f'mysql+pymysql://{DB_USER}:{DB_PASS}@{PC2_DATABASE_IP}/{DB_NAME}'
engine = create_engine(DATABASE_URI)
Session = sessionmaker(bind=engine)

# --- リアルタイムデータ保持クラス ---
class RealtimeData:
    def __init__(self):
        self.temperature = None
        self.humidity = None
        self.weight = None

realtime_data = RealtimeData()

# --- 乾燥プロセス管理クラス ---
class DryingProcess:
    def __init__(self):
        self.active = False
        self.pre_weight = None
        self.post_weight = None
        self.thread = None

    def start(self, garment_id):
        if self.active:
            print("[PROCESS] すでに別の乾燥プロセスが実行中です。")
            return

        db_session = Session()
        try:
            garment = db_session.query(Garment).filter_by(id=garment_id).one_or_none()
            if not garment:
                print(f"[ERROR] Garment ID {garment_id} が見つかりません。")
                return
            self.post_weight = garment.dry_weight_grams
        finally:
            db_session.close()

        print(f"[PROCESS] 乾燥プロセス開始 (目標重量: {self.post_weight}g)")
        # Pi2に測定開始指令
        client.publish('weight_sensor/control', json.dumps({"command": "start"}))
        
        # 最初の重量データをpre_weightとして取得するまで待機
        print("[PROCESS] 初回重量データの受信を待っています...")
        while realtime_data.weight is None:
            time.sleep(1)
        self.pre_weight = realtime_data.weight
        realtime_data.weight = None # 次のデータのためにクリア
        print(f"[PROCESS] 初回重量を取得: {self.pre_weight}g")

        self.active = True
        self.thread = threading.Thread(target=self.run_cycle)
        self.thread.start()

    def stop(self):
        if not self.active:
            return
        self.active = False
        client.publish('weight_sensor/control', json.dumps({"command": "stop"}))
        print("[PROCESS] 乾燥プロセスを停止しました。")

    def run_cycle(self):
        db_session = Session()
        try:
            while self.active:
                print("\n--- データ収集サイクル ---")
                client.publish("sensor/request", "get")
                time.sleep(3) # センサーからの応答を待つ

                if all([realtime_data.temperature, realtime_data.humidity, realtime_data.weight]):
                    comp = CompareClass(self.pre_weight, self.post_weight)
                    dry_rate = comp.calculate_dry_rate(realtime_data.weight)
                    
                    predictor = DryingPredictor(self.post_weight / 1000.0) # kgに変換
                    predictor.set_sensor_data(realtime_data.weight / 1000.0, realtime_data.temperature, realtime_data.humidity)
                    hours, minutes = predictor.predict_drying_time(dry_rate)
                    
                    log_data = DryingLog(
                        current_weight=realtime_data.weight,
                        temperature=realtime_data.temperature,
                        humidity=realtime_data.humidity,
                        dry_rate=dry_rate,
                        predicted_hours=hours,
                        predicted_minutes=minutes
                    )
                    db_session.add(log_data)
                    db_session.commit()
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] DB保存: 乾燥率={dry_rate:.1f}%, 予測時間={hours}h{minutes}m")

                    if dry_rate >= 100:
                        print("[PROCESS] 乾燥が完了しました！")
                        self.stop()

                    realtime_data.temperature = None
                    realtime_data.humidity = None
                    realtime_data.weight = None
                else:
                    print("[WARNING] データが不完全です。スキップします。")

                time.sleep(300) # 5分待機
        finally:
            db_session.close()


drying_process = DryingProcess()

# --- MQTTコールバック ---
def on_connect(client, userdata, flags, rc, properties=None):
    print("[MQTT] ブローカーに接続しました。")
    client.subscribe(CONTROL_TOPIC)
    client.subscribe(SENSOR_TOPICS)

def on_message(client, userdata, msg):
    topic = msg.topic
    payload = msg.payload.decode()
    
    if topic == CONTROL_TOPIC:
        data = json.loads(payload)
        command = data.get("command")
        if command == "start":
            drying_process.start(data.get("garment_id"))
        elif command == "stop":
            drying_process.stop()
        return

    try:
        value = float(payload)
        if topic == "sensor/temperature":
            realtime_data.temperature = value
        elif topic == "sensor/humidity":
            realtime_data.humidity = value
        elif topic == "sensor/weight":
            realtime_data.weight = value
    except ValueError:
        pass # エラー処理は省略

# --- メイン処理 ---
if __name__ == "__main__":
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    
    try:
        print("[システム] PC1からの指令を待機しています...")
        client.loop_forever()
    except KeyboardInterrupt:
        print("\n[システム] 処理を終了します。")
    finally:
        drying_process.stop()
        client.disconnect()