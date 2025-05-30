import sys
import platform
import argparse
import configparser
import signal
import os
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
                        print(f"integrationTimes: f“{devconfig.integrationTimes[0]} "
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

def onCallbackImage(frame: xintan_sdk.Frame):
    print("img: " + str(frame.frame_id))

if __name__ == '__main__':
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
    parser.add_argument('ip_address',nargs='?', type=str, help='要连接的 IP 地址', default="192.168.0.101")
    parser.add_argument('is_set_para', nargs='?', type=str, help='是否需要设定默认参数', default="0")
    # 解析命令行参数
    args = parser.parse_args()
    print("ip: " + args.ip_address)
    print("is_set_para: " + args.is_set_para)
    is_set_para = int(args.is_set_para)
    success = xtsdk.setConnectIpaddress(args.ip_address)

    try:
        xtsdk.startup()
    except Exception as reason:
        print(f"Error: {reason}")
    signal.signal(signal.SIGINT, signal_handler)


    while keepRunning:
        time.sleep(1)
    print("stop")
    xtsdk.stop()
    xtsdk.shutdown()

