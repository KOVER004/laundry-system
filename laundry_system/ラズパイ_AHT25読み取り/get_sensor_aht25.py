#Pi3に保存させる
import time
import paho.mqtt.client as mqtt
from aht25 import AHT25
# ======= MQTT設定 =======
MQTT_BROKER = "192.268.11.4"  # MQTTブローカーのアドレス
MQTT_PORT = 1883           # MQTTブローカーのポート
TOPIC_TEMP = "sensor/temperature" # 温度を送信するトピック
TOPIC_HUMID = "sensor/humidity"   # 湿度を送信するトピック
TOPIC_REQUEST = "sensor/request"  # サーバーからの要求を受け付けるトピック
# ======= センサー初期化 =======
try:
    aht = AHT25()
except Exception as e:
    print(f"センサーの初期化に失敗しました: {e}")
    # センサーが接続されていない場合はここで終了する
    exit()
# ======= MQTTコールバック関数 =======
def on_connect(client, userdata, flags, rc):
    """MQTTブローカーに接続したときに呼ばれる関数"""
    if rc == 0:
        print(f"MQTTブローカーに接続しました (rc: {rc})")
        # 接続に成功したら、リクエスト用のトピックを購読(subscribe)する
        client.subscribe(TOPIC_REQUEST)
        print(f"トピック '{TOPIC_REQUEST}' の購読を開始しました")
    else:
        print(f"MQTTブローカーへの接続に失敗しました (rc: {rc})")
def on_message(client, userdata, msg):
    """購読しているトピックにメッセージが届いたときに呼ばれる関数"""
    # 受信したメッセージのトピックがリクエスト用トピックか確認
    if msg.topic == TOPIC_REQUEST:
        print(f"トピック '{msg.topic}' でデータ送信リクエストを受信しました")
        try:
            # センサーから温度と湿度を読み取る
            temperature, humidity = aht.read_environment()
            if temperature is not None and humidity is not None:
                # 取得したデータを文字列に変換して、それぞれのトピックに送信(publish)する
                client.publish(TOPIC_TEMP, f"{temperature:.2f}")
                client.publish(TOPIC_HUMID, f"{humidity:.2f}")
                print(f"データを送信しました -> 温度: {temperature:.2f} °C, 湿度: {humidity:.2f} %")
            else:
                print("センサーから有効なデータを取得できませんでした。")
        except Exception as e:
            print(f"センサー読み取りまたはデータ送信中にエラーが発生しました: {e}")
# ======= メイン処理 =======
# 1. MQTTクライアントを初期化
client = mqtt.Client()
# 2. 各コールバック関数をクライアントに登録
client.on_connect = on_connect
client.on_message = on_message
# 3. MQTTブローカーに接続
try:
    client.connect(MQTT_BROKER, MQTT_PORT, 60)
except Exception as e:
    print(f"MQTTブローカーへの接続に失敗しました: {e}")
    exit()
# 4. メッセージループを開始し、サーバーからの要求を待機
try:
    print("サーバーからのリクエストを待機しています... (Ctrl+Cで終了)")
    # loop_forever()で、メッセージの受信を待ち受け続ける
    client.loop_forever()
except KeyboardInterrupt:
    print("\nプログラムを終了します")
finally:
    # プログラム終了時にMQTT接続を切断
    client.disconnect()
    print("MQTT接続を切断しました")