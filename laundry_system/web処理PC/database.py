# database.py   PC1とPi1に保存させる
from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.orm import declarative_base
from datetime import datetime

# 全てのモデルクラスが継承する基本クラス
Base = declarative_base()

class Garment(Base):
    """衣類のマスターテーブル"""
    __tablename__ = 'garments'
    id = Column(Integer, primary_key=True)
    name = Column(String(80), unique=True, nullable=False)
    dry_weight_grams = Column(Float, nullable=False)

class DryingLog(Base):
    """日々の乾燥履歴をリアルタイムで保存するテーブル"""
    __tablename__ = 'drying_logs'
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, nullable=False, default=datetime.now)
    current_weight = Column(Float)
    temperature = Column(Float)
    humidity = Column(Float)
    dry_rate = Column(Float)
    predicted_hours = Column(Integer)
    predicted_minutes = Column(Integer)