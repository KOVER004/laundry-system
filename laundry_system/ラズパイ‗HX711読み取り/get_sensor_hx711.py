#Pi2に保存させる
# get_sensor_hx711.py
import time
import paho.mqtt.client as mqtt
from hx711 import HX711
import RPi.GPIO as GPIO
import json

# --- ▼▼▼ 要修正 ▼▼▼ ---
PI1_MQTT_BROKER_IP = '192.168.11.10' # Pi1のIPアドレス
# --- ▲▲▲ 設定ここまで ▲▲▲

# --- MQTT設定 ---
MQTT_PORT = 1883
TOPIC_WEIGHT = "sensor/weight"
TOPIC_CONTROL = "weight_sensor/control"

# --- HX711 設定 ---
# 実際の接続ピンに合わせて変更してください
DT_PIN = 5
SCK_PIN = 6
# センサーのキャリブレーションで得られた値を設定してください
REFERENCE_UNIT = 230
hx = HX711(DT_PIN, SCK_PIN)
hx.set_reading_format("MSB", "MSB")
hx.set_reference_unit(REFERENCE_UNIT)
hx.reset()
hx.tare()
print("[HX711] センサーの準備が完了しました。")

# --- グローバル変数 ---
is_active = False # 測定中かどうかを管理するフラグ

# --- MQTTコールバック ---
def on_connect(client, userdata, flags, rc):
    print(f"[MQTT] Pi1 ({PI1_MQTT_BROKER_IP}) に接続しました。")
    client.subscribe(TOPIC_CONTROL)
    print(f"[MQTT] トピック '{TOPIC_CONTROL}' の購読を開始しました。")

def on_message(client, userdata, msg):
    global is_active
    payload = json.loads(msg.payload.decode())
    command = payload.get("command")
    
    if command == "start":
        print("[CONTROL] 測定開始の指令を受信しました。")
        is_active = True
        hx.tare() # 新しい測定の開始時に風袋引き
    elif command == "stop":
        print("[CONTROL] 測定停止の指令を受信しました。")
        is_active = False

# --- メイン処理 ---
client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message
client.connect(PI1_MQTT_BROKER_IP, MQTT_PORT, 60)
client.loop_start() # バックグラウンドでMQTTメッセージを処理

print("指令待機中...")
try:
    while True:
        if is_active:
            # 測定がアクティブな場合のみ重量を読み取り、送信
            current_weight = hx.get_weight(5)
            client.publish(TOPIC_WEIGHT, f"{current_weight:.2f}")
            print(f"  -> 重量送信: {current_weight:.2f} g")
        
        # 10秒待機
        time.sleep(10)
        
except KeyboardInterrupt:
    print("プログラムを終了します。")

finally:
    GPIO.cleanup()
    client.loop_stop()
    client.disconnect()