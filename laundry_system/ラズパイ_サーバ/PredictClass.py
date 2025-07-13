#PC1とPi1に保存させる
class DryingPredictor:
    dry_rate = 0
    def __init__(self, post_weight_kg):
        """
        乾燥予測クラスの初期化
        :param dry_weight_kg: 乾燥後の洗濯物の重量（kg）
        """
        self.dry_weight_kg = post_weight_kg
        self.initial_weight_kg = None  # 重量センサーから取得
        self.temperature = None  # 環境センサーから取得
        self.humidity = None  # 環境センサーから取得
    def set_sensor_data(self, initial_weight_kg, temperature, humidity):
        """
        重量センサーと環境センサーのデータをセット
        :param initial_weight_kg: 重量センサーから取得した濡れた状態の重量（kg）
        :param temperature: 環境センサーから取得した室温（℃）
        :param humidity: 環境センサーから取得した湿度（%）
        """
        self.initial_weight_kg = initial_weight_kg
        self.temperature = temperature
        self.humidity = humidity
    def predict_drying_time(self, dry_rate):
        """
        温湿度を考慮した乾燥時間を予測
        乾燥時間（分） = 150 × 洗濯物の重さ（kg） × 温度補正 × 湿度補正
        :return: 乾燥完了までの予測時間（時間・分、整数値）
        """
        self.dry_rate = dry_rate
        if self.initial_weight_kg is None or self.temperature is None or self.humidity is None:
            raise ValueError("センサーのデータが未設定です")
        # 完全乾燥時は残り時間0を返す
        if self.dry_rate >= 100 or abs(self.initial_weight_kg - self.dry_weight_kg) < 0.01:
            return 0, 0
        temp_adjustment = 1 - 0.05 * (self.temperature - 25)
        humidity_adjustment = 1 + 0.1 * (self.humidity - 60) / 10
        drying_time_minutes = 150 * self.initial_weight_kg * temp_adjustment * humidity_adjustment
        drying_time_minutes = drying_time_minutes * ((100 - self.dry_rate) / 100)  # **残り率**をかける
        hours = int(drying_time_minutes // 60)
        minutes = int(drying_time_minutes % 60)
        return hours, minutes
    def display_info(self):
        """センサーのデータを日本語で表示"""
        if self.initial_weight_kg is None or self.temperature is None or self.humidity is None:
            print("センサーのデータが未設定です。データをセットしてください。")
            return
        hours, minutes = self.predict_drying_time(self.dry_rate)
        print(f"濡れた状態の洗濯物の重量（重量センサー）: {self.initial_weight_kg} kg")
        print(f"乾燥後の洗濯物の重量: {self.dry_weight_kg} kg")
        print(f"室温（環境センサー）: {self.temperature} ℃")
        print(f"湿度（環境センサー）: {self.humidity} %")
        print(f"予測される乾燥時間: {hours} 時間 {minutes} 分")
if __name__ == "__main__":
    # 使用例
    predictor = DryingPredictor(dry_weight_kg=1.5)  # 乾燥後の重量を設定
    # センサーから取得したデータを設定
    predictor.set_sensor_data(initial_weight_kg=4.0, temperature=24, humidity=50)
    predictor.display_info()