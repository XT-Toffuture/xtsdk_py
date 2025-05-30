import sys
import platform
import argparse
import configparser
import signal
import os
import copy
import numpy as np



# 获取操作系统类型
os_type = platform.system()
if os_type == "Windows":
    sys.path.append('../lib/win32')
    os.environ['PATH'] = r'../lib/win32;' + os.environ['PATH']
elif os_type == "Linux":
    architecture = platform.machine()
    if architecture == "x86_64":
        sys.path.append('../lib/linux/x86_64')
    elif architecture == "aarch64":
        sys.path.append('../lib/linux/aarch64')

sys.path.append("../cfg")

import time
import xintan_sdk
from read_config import ConfigParse

keepRunning = True
xtsdk = xintan_sdk.XtSdk()
config_parse = ConfigParse('../cfg/xintan.xtcfg')

configs = copy.deepcopy(config_parse.configs)
is_set_para = 0
depth_render_max = 10000
amp_render_max = 5000
g_temperature = 0
import threading
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QPushButton
from PyQt5.QtGui import QImage, QPixmap, QColor
def signal_handler(sig, frame):
    print('\nShutting down gracefully...')
    QApplication.instance().quit()  # 触发 Qt 退出机制
    xtsdk.stop()  # 停止 SDK 数据流
    xtsdk.shutdown()  # 关闭 SDK 连接


def get_multi_freq(freq_dev: int) -> int:
    freq_map = {
        0: 2,
        1: 0,
        3: 1,
        4: 6,
        7: 3,
        15: 4
    }

    # Get the index from the dictionary, default to 100 if freq_dev is unknown
    return freq_map.get(freq_dev, 100)

#xtsdk 回调函数
def onCallbackEvent(event: xintan_sdk.CBEventData):
    try:
        print('event: '+ event.eventstr + " " +  str(event.cmdid))
        if event.eventstr == "sdkState":

            if xtsdk.isconnect() == True and event.cmdid == 0xfe:
                success1,  devinfo = xtsdk.getDevInfo()
                print(devinfo.fwVersion)
                print(devinfo.sn + " " + devinfo.chipidStr)

                fwVersion = devinfo.fwVersion  # 假设 devinfo 是字典类型，fwVersion 是其中的一个键
                fwlen = len(fwVersion)
                fwversionf = float(fwVersion[fwlen - 4:])

                if fwversionf >= 2.20:
                    print(str(fwversionf) + " > 2.20")

                    # 假设 devconfig 是一个字典或类似的对象，devinfo 类似于结构体的形式

                    success, devconfig = xtsdk.getDevConfig()

                    if success:
                        print("******************* GET CONFIG SUCCESS *******************")
                        # 打印 devinfo 的 fwVersion 属性
                        print(f"fwVersion: {devinfo.fwVersion}")
                        print(f"version: {devconfig.version}")
                        print(f"ModulationFreq: {xintan_sdk.get_modulation_freq_strings()[devconfig.modFreq]}")
                        print(f"HDRMode: {xintan_sdk.get_modulation_HDRMode_strings()[devconfig.hdrMode]}")

                        # 打印其他属性
                        print(f"integrationTimeGs: {devconfig.integrationTimeGs}")
                        print(f"integrationTimes: {devconfig.integrationTimes[0]} "
                                                  f"{devconfig.integrationTimes[1]} "
                                                  f"{devconfig.integrationTimes[2]} "
                                                  f"{devconfig.integrationTimes[3]}")
                        print(f"miniAmp: {devconfig.miniAmp}")
                        print(f"isFilterOn: {devconfig.isFilterOn}")
                        print(f"roi: {devconfig.roi}")
                        print(f"maxfps: {devconfig.maxfps}")
                        print(f"bCompensateOn: {devconfig.bCompensateOn}")
                        print(f"bBinningH: {devconfig.bBinningH}")
                        print(f"bBinningV: {devconfig.bBinningV}")
                        print(f"freqChannel: {devconfig.freqChannel}")
                        print(f"setmaxfps: {devconfig.setmaxfps}")
                        print(f"endianType: {devconfig.endianType}")
                        # print(f"freq: {devconfig.freq}")
                        print(f"freq: {xintan_sdk.get_modulation_freq_strings()[get_multi_freq(devconfig.freq[0])]} "
                                  f"{xintan_sdk.get_modulation_freq_strings()[get_multi_freq(devconfig.freq[1])]} "
                                  f"{xintan_sdk.get_modulation_freq_strings()[get_multi_freq(devconfig.freq[2])]} "
                                  f"{xintan_sdk.get_modulation_freq_strings()[get_multi_freq(devconfig.freq[3])]}")

                        print(f"bcut_filteron: {devconfig.bcut_filteron}")
                        print(f"cut_intgrttime0: {devconfig.cut_intgrttime0}")
                        print(f"cut_distance0: {devconfig.cut_distance0}")
                        print(f"cut_intgrttime1: {devconfig.cut_intgrttime1}")
                        print(f"cut_distance1: {devconfig.cut_distance1}")

                        print("********************************************************")
                        if not is_set_para:
                            print("******************* USING DEV CONFIG *******************")
                            configs['Setting']['intgs'] = devconfig.integrationTimeGs
                            configs['Setting']['int1'] = devconfig.integrationTimes[0]
                            configs['Setting']['int2'] = devconfig.integrationTimes[1]
                            configs['Setting']['int3'] = devconfig.integrationTimes[2]
                            configs['Setting']['int4'] = devconfig.integrationTimes[3]

                            configs['Setting']['freq1'] = xintan_sdk.ModulationFreq(get_multi_freq(devconfig.freq[0]))
                            configs['Setting']['freq2'] = xintan_sdk.ModulationFreq(get_multi_freq(devconfig.freq[1]))
                            configs['Setting']['freq3'] = xintan_sdk.ModulationFreq(get_multi_freq(devconfig.freq[2]))
                            configs['Setting']['freq4'] = xintan_sdk.ModulationFreq(get_multi_freq(devconfig.freq[3]))

                            configs['Setting']['freq'] = devconfig.modFreq
                            configs['Setting']['maxfps'] = devconfig.maxfps
                            configs['Setting']['minLSB'] = devconfig.miniAmp
                            configs['Setting']['HDR'] = devconfig.hdrMode
                        else:
                            print("******************* USING INI CONFIG *******************")
                        config_parse.configs = configs
                    else:
                        print("******************* GET CONFIG FAILED *******************")
                        print("********************************************************")
                else:
                    print("******************* < 2.20 *******************")
                    print("********************************************************")

                config_parse.print_all_settings()
                xtsdk.stop()
                xtsdk.setIntTimesus(configs['Setting']['intgs'],
                                    configs['Setting']['int1'],
                                    configs['Setting']['int2'],
                                    configs['Setting']['int3'],
                                    configs['Setting']['int4'],
                                    0)
                mod_freq = xintan_sdk.ModulationFreq.FREQ_12M
                if fwversionf < 2.0:
                    mod_freq = xintan_sdk.ModulationFreq(configs['Setting']['freq'])
                    xtsdk.setModFreq(mod_freq)
                    
                hdr_mode = xintan_sdk.HDRMode(configs['Setting']['HDR'])
                mod_freq1 = xintan_sdk.ModulationFreq(configs['Setting']['freq1'])
                mod_freq2 = xintan_sdk.ModulationFreq(configs['Setting']['freq2'])
                mod_freq3 = xintan_sdk.ModulationFreq(configs['Setting']['freq3'])
                mod_freq4 = xintan_sdk.ModulationFreq(configs['Setting']['freq4'])
                xtsdk.setMultiModFreq(mod_freq1, mod_freq2, mod_freq3, mod_freq4, xintan_sdk.ModulationFreq(2))


                xtsdk.setHdrMode(hdr_mode)

                xtsdk.setMinAmplitude(configs['Setting']['minLSB'])
                xtsdk.setMaxFps(configs['Setting']['maxfps'])
                img_type = xintan_sdk.ImageType(configs['Setting']['imgType'])
                xtsdk.start(img_type)
            elif event == 'sdkState':
                print(xtsdk.getStateStr())
            elif event == 'devState':
                print(xtsdk.getStateStr())
    except Exception as e:
        print(f"Exception in onCallbackEvent: {e}")

def interpolate(x, x0, y0, x1, y1):
    if x1 == x0:
        return y0
    return ((x - x0) * (y1 - y0) / (x1 - x0)) + y0


def create_rgb_colormap(num_steps=30000):
    red, green, blue = np.zeros(num_steps), np.zeros(num_steps), np.zeros(num_steps)
    k = 1
    R0, R1, R2, R3 = -0.125 * k - 0.25, 0, 0.25 * k, 0.5 * k
    G0, G1, G2, G3 = R1, 0.25 * k, 0.5 * k, 0.625 * k
    B0, B1, B2, B3 = R2, 0.5 * k, 0.75 * k, 1.0 * k

    index = np.linspace(-0.25 * k, 1 - 0.25 * k, num_steps)

    # 红色通道
    red = np.where((R0 <= index) & (index < R1), interpolate(index, R0, 0, R1, 255),
                   np.where((R1 <= index) & (index < R2), 255,
                            np.where((R2 <= index) & (index < R3), interpolate(index, R2, 255, R3, 0), 0)))

    # 绿色通道
    green = np.where((G0 <= index) & (index < G1), interpolate(index, G0, 0, G1, 255),
                     np.where((G1 <= index) & (index < G2), 255,
                              np.where((G2 <= index) & (index < G3), interpolate(index, G2, 255, G3, 0), 0)))

    # 蓝色通道
    blue = np.where((B0 <= index) & (index < B1), interpolate(index, B0, 0, B1, 255),
                    np.where((B1 <= index) & (index < B2), 255,
                             np.where((B2 <= index) & (index < B3), interpolate(index, B2, 255, B3, 0), 0)))

    return np.stack((red, green, blue), axis=1) / 255.0


def render_to_rgb_colormap_image(data_np, width, height, begin=0, end=13000):
    colormap = create_rgb_colormap()
    data_np = data_np.reshape((height, width))

    diff = end - begin
    diff = max(diff, 1)
    indexFactorColor = len(colormap) / diff

    # 用 NumPy 计算索引值
    value_indices = np.clip((data_np - begin) * indexFactorColor, 0, len(colormap) - 1).astype(int)

    # 使用 NumPy 索引加速颜色映射
    output_image = np.take(colormap, value_indices, axis=0)
    output_image[data_np < 0] = [1, 1, 1]  # 白色
    output_image[data_np > end] = [0, 0, 0]  # 黑色

    output_image = (output_image * 255).astype(np.uint8)
    bytes_per_line = 3 * width
    q_img = QImage(output_image.data, width, height, bytes_per_line, QImage.Format_RGB888)
    return q_img

def onCallbackImage(frame: xintan_sdk.Frame):
    try:
        global g_temperature
        g_temperature = frame.temperature / 100

        # 将 std::vector<uint16_t> 转换为 NumPy 数组
        if frame.dataType == xintan_sdk.DataType.GRAYSCALE:
            print("Gray scale No Image")
            return
        amplitude_np = np.array(frame.amplData, dtype=np.uint16)
        distance_np = np.array(frame.distData, dtype=np.uint32)

        # 为振幅和距离创建彩色图像
        # q_image_ampl = render_to_colormap_image(amplitude_np, frame.width, frame.height, gamma=0.8)
        # q_image_dist = render_to_colormap_image(distance_np, frame.width, frame.height, gamma=0.8)

        q_image_ampl = render_to_rgb_colormap_image(amplitude_np, frame.width, frame.height, end=amp_render_max)
        q_image_dist = render_to_rgb_colormap_image(distance_np, frame.width, frame.height, end=depth_render_max)

        # 显示图像
        g_qimage = QPixmap.fromImage(q_image_dist).scaled(frame.width * 2, frame.height * 2, Qt.KeepAspectRatio)
        g_qimage2 = QPixmap.fromImage(q_image_ampl).scaled(frame.width * 2, frame.height * 2, Qt.KeepAspectRatio)
        g_pixmapui.setPixmap(g_qimage)
        g_pixmapui2.setPixmap(g_qimage2)

    except Exception as e:
        print(f"Exception in onCallbackImg: {e}")



# 按钮处理函数
def onStartStop(self):
    if g_startstopui.text() == 'Start':
        g_startstopui.setText('Stop')
        xtsdk.start(xintan_sdk.ImageType.IMG_POINTCLOUDAMP)
    else:
        g_startstopui.setText('Start')
        xtsdk.stop()

# 定时检查设备状态
def TimerThreadFunc():
    global g_temperature
    while True:
        time.sleep(3)
        if xtsdk.isconnect():
            g_stateui.setText(xtsdk.getStateStr() +' ' + str(g_temperature)+'℃')
            g_stateui.setStyleSheet("color:green")
            if xtsdk.getDevState() != xintan_sdk.DevStateCode.DevSTATE_STREAM:
                if g_startstopui.text() == 'Stop':
                    g_startstopui.setText('Start')
            else:
                if g_startstopui.text() == 'Start':
                    g_startstopui.setText('Stop')

        else:
            g_stateui.setText('Disconnect')
            g_stateui.setStyleSheet("color:red")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = QWidget()
    window.setWindowTitle('XT Example image')
    window.setGeometry(200, 200, 1400, 640)

    g_pixmapui = QLabel(window)
    g_pixmapui2 = QLabel(window)
    g_startstopui = QPushButton(window)
    g_stateui = QLabel(window)

    g_pixmapui.resize(640, 480)
    g_pixmapui2.resize(640, 480)
    g_startstopui.resize(150, 50)
    g_stateui.resize(300, 50)

    g_pixmapui.move(10, 10)
    g_pixmapui2.move(10 + 650, 10)
    g_startstopui.move(20, 10 + 490)
    g_stateui.move(20, 560)

    g_startstopui.setText('Start')
    g_stateui.setText('Unknow')
    g_stateui.setStyleSheet("color:red")

    g_startstopui.clicked.connect(onStartStop)
    window.show()

    xtsdk.setCallback(onCallbackEvent, onCallbackImage)
    if configs['Filters']['kalmanEnable'] == 1:
        xtsdk.setSdkKalmanFilter(int((configs['Filters']['kalmanFactor']) * 1000),
                                 (configs['Filters']['kalmanThreshold']),
                                 2000)
    if configs['Filters']['medianSize'] > 0:
        xtsdk.setSdkMedianFilter(configs['Filters']['medianSize'])
    if configs['Filters']['edgeEnable'] == 1:
        xtsdk.setSdkEdgeFilter(configs['Filters']['edgeThreshold'])
    if configs['Filters']['dustEnable'] == 1:
        xtsdk.setSdkDustFilter(configs['Filters']['dustThreshold'], configs['Filters']['dustFrames'])
    if configs['Filters']['postprocessEnable'] == 1:
                xtsdk.setPostProcess(configs['Filters']['postprocessThreshold'], configs['Filters']['dynamicsEnabled'], configs['Filters']['dynamicsWinsize'])
    if configs['Filters']['reflectiveEnable'] == 1:
        xtsdk.setSdkReflectiveFilter(configs['Filters']['ref_th_min'], configs['Filters']['ref_th_max'])

    parser = argparse.ArgumentParser(description='设置连接的 IP 地址。')

    # 添加 IP 地址参数
    parser.add_argument('ip_address',nargs='?', type=str, help='要连接的 IP 地址', default="192.168.0.117")
    parser.add_argument('is_set_para', nargs='?', type=str, help='是否需要设定默认参数', default="0")
    # 解析命令行参数
    args = parser.parse_args()
    print("ip: " + args.ip_address)
    print("is_set_para: " + args.is_set_para)
    is_set_para = int(args.is_set_para)

    success = xtsdk.setConnectIpaddress(args.ip_address)
    signal.signal(signal.SIGINT, signal_handler)
    xtsdk.startup()
    timerthread = threading.Thread(target=TimerThreadFunc)
    timerthread.start()

    sys.exit(app.exec_())

