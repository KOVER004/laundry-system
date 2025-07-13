#Pi3に保存させる
import time
import smbus
class AHT25:
    # address setting
    ADDRESS = 0x38
    i2c = smbus.SMBus(1)
    # trigger setting command
    set = [0xAC, 0x33, 0x00]
    # data reading command
    dat = [0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]
    def __init__(self):
        self.init_sensor()
    def init_sensor(self):
        # AHT25 setting
        time.sleep(0.1)
        ret = self.i2c.read_byte_data(self.ADDRESS, 0x71)
    def read_environment(self):
        # send trigger measurement command
        time.sleep(0.01)
        self.i2c.write_i2c_block_data(self.ADDRESS, 0x00, self.set)
        # read data
        time.sleep(0.08)
        dat = self.i2c.read_i2c_block_data(self.ADDRESS, 0x00, 0x07)
        # data conversion
        hum = dat[1] << 12 | dat[2] << 4 | ((dat[3] & 0xF0) >> 4)
        tmp = ((dat[3] & 0x0F) << 16) | dat[4] << 8 | dat[5]
        hum = hum / 2**20 * 100
        tmp = tmp / 2**20 * 200 - 50
        # テスト実行用
        print(" hum: {:.5f}".format(hum), " tmp: {:.5f}".format(tmp))
        return tmp, hum
# テスト実行モード未完成
if __name__ == "__main__":
    aht = AHT25()