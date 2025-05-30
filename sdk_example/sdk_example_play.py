import sys
import platform
import argparse
import configparser
import signal
import os
import re
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

import copy
# import numpy



sys.path.append("../cfg")

import time
import xintan_sdk
from read_config import ConfigParse

keepRunning = True
xtsdk = xintan_sdk.XtSdk()
config_parse = ConfigParse('../cfg/xintan.xtcfg')

configs = copy.deepcopy(config_parse.configs)
is_set_para = 0
record_path_str = ""

def signal_handler(sig, frame):
    global keepRunning
    print('You pressed Control+C!')
    keepRunning = False
    # sys.exit(0)


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
                xtsdk.setMultiModFreq(mod_freq1, mod_freq2, mod_freq3, mod_freq4,xintan_sdk.ModulationFreq(2))


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

def onCallbackImage(frame):
    # 创建 xyzi 数组
    print("callback")
    xyzi = np.empty((len(frame.points), 4), dtype=float)

    xyzi[:, 0] = np.array([p.x for p in frame.points])
    xyzi[:, 1] = np.array([p.y for p in frame.points])
    xyzi[:, 2] = np.array([p.z for p in frame.points])
    xyzi[:, 3] = frame.amplData
    # 将所有点视为有效点
    valid_points = xyzi

    base_dir = os.getcwd()

    # 创建输出目录
    output_dir = os.path.join(base_dir, f"{record_path_str}_pcd")
    os.makedirs(output_dir, exist_ok=True)

    # 创建输出文件路径
    # output_path = os.path.join(output_dir, f"{frame.frame_label}.pcd")

    # Remove invalid characters

    position = frame.frame_label.find('\x00')
    if position != -1:
        print(f"空字符在位置: {position}")
    frame_label_cleaned = re.sub(r'[\x00]', '', frame.frame_label)


    output_path = os.path.join(output_dir, f"{frame_label_cleaned}.pcd")

    print(f"Writing to {output_path}")

    # 获取点云的宽度和高度
    width = frame.width
    height = frame.height

    try:
        with open(str(output_path), 'w') as f:
            # 写入 PCD 头信息
            f.write("# .PCD v0.7 - Point Cloud Data file format\n")
            f.write("VERSION 0.7\n")
            f.write("FIELDS x y z intensity\n")
            f.write("SIZE 4 4 4 4\n")
            f.write("TYPE F F F F\n")
            f.write("COUNT 1 1 1 1\n")
            f.write(f"WIDTH {width}\n")
            f.write(f"HEIGHT {height}\n")
            f.write("VIEWPOINT 0 0 0 1 0 0 0\n")
            f.write(f"POINTS {width * height}\n")
            f.write("DATA ascii\n")
            # 使用 NumPy 的 savetxt 方法进行批量写入
            np.savetxt(f, valid_points, fmt='%f %f %f %f')
    except Exception as e:
        print(f"Error writing file: {e}")


def is_hexadecimal(s):
    try:
        int(s, 16)
        return True
    except ValueError:
        return False

def read_files():
    folder_path = record_path_str
    if not os.path.exists(folder_path) or not os.path.isdir(folder_path):
        print(f"folder {folder_path} not exist")
        return
    if len(os.listdir(folder_path)) <= configs['Filters']['dustFrames']:
        print("DUST FILTER NOT ACTIVED BY NOT ENOUGH FRAME COUNT : " + str(len(os.listdir(folder_path))) +
            " REQUIRED : " + str(configs['Filters']['dustFrames'] + 1))
    for entry in os.listdir(folder_path):
        path = os.path.join(folder_path, entry)

        if os.path.isfile(path):
            if path.endswith('.xbin'):
                xtsdk.doXbinFrameData(path)
                time.sleep(0.3)  
            elif path.endswith('.txt'):
                with open(path, 'r', encoding='utf-8') as file:
                    hex_string = file.readline().strip()

                if len(hex_string) % 2 != 0:
                    print("invalid hex string length !")
                    return

                bytes_vector = []
                for i in range(0, len(hex_string), 2):
                    byte_string = hex_string[i:i+2]

                    if not is_hexadecimal(byte_string):
                        print(f"trans error: contains invalid hexadecimal strings {byte_string}")
                        break

                    byte = int(byte_string, 16)
                    bytes_vector.append(byte)

                if len(bytes_vector) < 1000:
                    print(f"trans error: length error {len(bytes_vector)}")
                    return
                file_name = os.path.splitext(os.path.basename(path))[0]
                try:
                    xtsdk.doUdpFrameData(bytes_vector, file_name)
                except Exception as e:
                    print(f"Error writing file: {e}")
                
                time.sleep(0.3)

if __name__ == '__main__':
    xtsdk.setCallback(onCallbackEvent, onCallbackImage)

    parser = argparse.ArgumentParser(description='xbin path')

    # 添加 IP 地址参数
    parser.add_argument('record_path',nargs='?', type=str, help='', default="b")
    # 解析命令行参数
    args = parser.parse_args()
    record_path_str = args.record_path

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

    try:
        xtsdk.startup()
    except Exception as reason:
        print(f"Error: {reason}")

    img_type = xintan_sdk.ImageType(4)
    xtsdk.start(img_type)


    read_files()

    signal.signal(signal.SIGINT, signal_handler)


    # while keepRunning:
    #     time.sleep(1)
    print("stop")
    xtsdk.stop()
    xtsdk.shutdown()

