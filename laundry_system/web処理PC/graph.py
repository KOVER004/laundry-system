# graph.py  PC1に保存させる
from flask import Flask, jsonify, render_template
from sqlalchemy import create_engine, desc
from sqlalchemy.orm import sessionmaker
from database import DryingLog

app = Flask(__name__)

# --- ▼▼▼ 要修正 ▼▼▼ ---
PC2_DATABASE_IP = '192.168.10.118'  # PC2のIPアドレス
# --- ▲▲▲ 設定ここまで ▲▲▲

# --- データベース設定 ---
DB_USER = 'Akiyuki'
DB_PASS = 'oda-Ak1yuk1'
DB_NAME = 'laundry_DB' # データベース名を修正
DATABASE_URI = f'mysql+pymysql://{DB_USER}:{DB_PASS}@{PC2_DATABASE_IP}/{DB_NAME}'
engine = create_engine(DATABASE_URI)
Session = sessionmaker(bind=engine)

@app.route('/graph')
def graph_view():
    """グラフ表示画面(graph.html)を表示"""
    return render_template('graph.html')

@app.route('/graph_data')
def graph_data():
    """DBから全ての乾燥ログを取得してグラフ用に返す"""
    session = Session()
    try:
        logs = session.query(DryingLog).order_by(DryingLog.timestamp.asc()).all()
        data = {
            "labels": [log.timestamp.strftime('%H:%M') for log in logs],
            "dry_rate_data": [log.dry_rate for log in logs],
            "temperature_data": [log.temperature for log in logs],
            "humidity_data": [log.humidity for log in logs],
        }
        return jsonify(data)
    finally:
        session.close()

if __name__ == '__main__':
    # メインのapp.pyとポートが競合しないように5002番で起動
    app.run(host='0.0.0.0', port=5002, debug=True)