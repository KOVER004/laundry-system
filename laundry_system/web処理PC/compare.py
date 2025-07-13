#PC1とPi1に保存させる
class CompareClass:
    pre_weight = 0
    now_weight = 0
    post_weight = 0

    def __init__(self, pre_weight: float, post_weight: float):
        """
        コンストラクタ
        乾燥前の重量と乾燥後の重量から、乾燥率を計算します。

        Parameters:
        pre_weight (float): 乾燥前のサンプルの重量（g）
        post_weight (float): 乾燥後のサンプルの重量（g）
        """
        self.pre_weight: float = pre_weight
        self.post_weight: float = post_weight
        self.Percentage: float = 0.0

    def calculate_dry_rate(self, now_weight) -> float:
        self.now_weight = now_weight
        """
        現在の重量から乾燥率を計算します。

        乾燥率(%) = ((乾燥前重量 - 現在重量) / (乾燥前重量 - 乾燥後重量)) × 100

        Returns:
        float: 乾燥率（%）
        """
        if self.pre_weight == 0:
            self.Percentage = 0.0
        else:
            self.Percentage = ((self.pre_weight - self.now_weight) / (self.pre_weight - self.post_weight)) * 100
        return self.Percentage

    def is_dry(self, threshold: float = 90.0) -> bool:
        """
        一定の乾燥率を超えているかどうかを判定します。

        Parameters:
        threshold (float): 判定基準となる乾燥率（%）

        Returns:
        bool: Trueなら基準を満たしている（乾燥している） / Falseなら満たしていない
        """
        return self.calculate_dry_rate(self.now_weight) >= threshold


if __name__ == "__main__":
    # サンプル：乾燥前の重量 1000g、乾燥後の重量 120g、現在の重量 550g
    pre = 1000.0
    post = 120.0
    now = 550.0

    comparer = CompareClass(pre, post)
    dry_rate = comparer.calculate_dry_rate(now)
    print(f"乾燥率: {dry_rate:.2f}%")

    # デフォルトの閾値（90%）で乾燥判定
    if comparer.is_dry():
        print("十分に乾燥しています。")
    else:
        print("まだ乾燥が不十分です。")

    # 判定基準を85%に変更して再チェック
    threshold = 85.0
    print(f"{threshold}% を超えて乾燥しているか: {comparer.is_dry(threshold)}")
