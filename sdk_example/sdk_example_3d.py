import sys
import platform
import argparse
import signal
import os
import re

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
from read_config import ConfigParse
import time
import xintan_sdk
import open3d as o3d
import open3d.visualization.gui as gui
import threading
import queue
import math
# print(sys.path)
import numpy as np
xtsdk = xintan_sdk.XtSdk()
lock = threading.Lock()
dataqueue = queue.Queue()

keepRunning = True
config_parse = ConfigParse('../cfg/xintan.xtcfg')

configs = config_parse.configs
is_set_para = 0
vis = None
exit_event = threading.Event()


def signal_handler(sig, frame):
    print('\nShutting down...')
    exit_event.set()

    # 停止数据采集
    xtsdk.stop()
    xtsdk.shutdown()

    # # 关闭 Open3D 窗口
    # global vis
    # if vis:
    #     gui.Application.instance.quit()

    # 强制退出程序（必要时）
    os._exit(0)

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

def extract_version(fwVersion: str) -> float:
    version_match = re.search(r'[vV](\d+\.\d+)(?:\.\d+)?[a-zA-Z]?', fwVersion)

    if not version_match:
        return None

    version_str = version_match.group(1)  # Get X.Y part
    try:
        return float(version_str)
    except ValueError:
        return None

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
                fwversionf = extract_version(fwVersion)
                print("device fw version: " + str(fwversionf))

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


def onCallbackImage(frame: xintan_sdk.Frame):
    response = np.empty((1, frame.height, frame.width), dtype=np.uint16)
    # if (frame.measType == DISTANCE) | (frame.measType == DISTAMP):
    if not frame.hasPointcloud:
        return
    frame_inq(frame)

# 将 frame 添加到队列
def frame_inq(frame):
    # dataqueue.put(frame)
    dataqueue.put(frame, block=False)



# 从 frame 获取点和颜色信息
def frame_getpointsandcolors(frame):
    # 初始化 points 和 colors 数组

    points = np.zeros((frame.width * frame.height, 3))
    colors = np.zeros((frame.width * frame.height, 3))

    try:
        # 获取所有点的坐标信息
        xyz = np.array([[p.x, p.y, p.z] for p in frame.points])

        # 检测 NaN 值
        valid_mask = ~np.isnan(xyz).any(axis=1)

        # 筛选出有效的点并填充 points 数组
        points[valid_mask] = xyz[valid_mask]

        # 计算颜色值并填充 colors 数组
        colors[valid_mask, 2] = xyz[valid_mask, 2] / 4       # Blue channel
        colors[valid_mask, 1] = xyz[valid_mask, 2] / 8       # Green channel
        colors[valid_mask, 0] = 1 - colors[valid_mask, 2]    # Red channel

        # 为无效点设置默认颜色
        colors[~valid_mask] = [0, 0, 1]

        # 调试信息：输出前10个点
        # print("First 10 Points:", points[:10])
    except Exception as reason:
        print(f"Error getting points and colors: {reason}")



    return points, colors

app = None
vis = None
# 可视化函数
def visualize_3dv():
    global vis
    global app
    app = gui.Application.instance
    app.initialize()
    vis = o3d.visualization.O3DVisualizer("XinTan Open3D - Demo", 1000, 800)
    vis.show_settings = False

    material = o3d.visualization.rendering.MaterialRecord()
    material.shader = "defaultLit"  # Use unlit shader for efficiency

    # 初始化点云
    pcd = o3d.geometry.PointCloud()
    # pcd.points = o3d.utility.Vector3dVector(np.zeros((320*240, 3), dtype=float))
    pts = np.zeros((320 * 240, 3), dtype=float)

    pcd.points = o3d.utility.Vector3dVector(pts)
    try:
        vis.add_geometry("Points", pcd, material)
    except Exception as e:
        print(f"Error: {e}")
    vis.reset_camera_to_default()

    visual = threading.Thread(target=visualize_3dvThread, args=(vis, pcd))
    visual.start()
    app.add_window(vis)
    # threading.Thread(target=visualize_3dvThread, args=(pcd,), daemon=True).start()
    app.run()




def update_pointcloud_geometry(vis, pcd):
    vis.update_geometry(pcd)
    vis.poll_events()
    vis.update_renderer()

# def visualize_3dvThread(pcd):
#     while keepRunning:  # 在程序结束时终止线程
#         if dataqueue.empty():
#             time.sleep(0.1)
#             continue
#
#         try:
#             frame = dataqueue.get(timeout=1)  # 从队列中获取点云数据
#             points, colors = frame_getpointsandcolors(frame)
#
#             # 创建 Tensor 类型点云
#             t_pcd = o3d.t.geometry.PointCloud()
#             t_pcd.point.positions = o3d.core.Tensor(points, dtype=o3d.core.Dtype.Float32)
#             t_pcd.point.colors = o3d.core.Tensor(colors, dtype=o3d.core.Dtype.Float32)
#
#             try:
#                 # pts = np.zeros((len(points), 3), dtype=float)
#                 # pcd.points = o3d.utility.Vector3dVector(pts)
#                 pcd.points = o3d.utility.Vector3dVector(np.asarray(points))
#                 pcd.colors = o3d.utility.Vector3dVector(np.asarray(colors))
#             except Exception as e:
#                 print(f"Error: {e}")
#             vis.remove_geometry("Points")
#             vis.add_geometry("Points",pcd)
#             end_time = time.time()  # 记录结束时间
#             # print(f"onCallbackImage function execution time: {end_time - start_time:.6f} seconds")
#
#             # # 添加或更新几何体
#             # if "point_cloud" not in vis.get_geometry_names():
#             #     vis.add_geometry("point_cloud", t_pcd)  # 添加新的点云
#             # else:
#             #     vis.update_geometry(
#             #         "point_cloud", t_pcd, o3d.visualization.O3DVisualizer.UPDATE_POINTS_FLAG
#             #     )  # 更新点云数据
#             #
#             # # 刷新可视化显示
#             # vis.poll_events()
#             # vis.update_renderer()
#
#         except queue.Empty:
#             continue  # 队列为空时跳过
#         except Exception as reason:
#             print(f"Error: {reason}")


# 可视化更新线程
def visualize_3dvThread(vis, pcd):
    global app
    geometry_added = False
    while not exit_event.is_set():  # 在程序结束时终止线程
        # if dataqueue.empty():
        #     time.sleep(0.1)
        #     continue

        try:
            start_time = time.time()
            frame = dataqueue.get(block=False)  # 从队列中取出数据
            points, colors = frame_getpointsandcolors(frame)
            t_pcd = o3d.t.geometry.PointCloud()
            t_pcd.point.positions = o3d.core.Tensor(points, dtype=o3d.core.Dtype.Float32)
            t_pcd.point.colors = o3d.core.Tensor(colors, dtype=o3d.core.Dtype.Float32)

            # 检查并更新几何体
            if not geometry_added:
                vis.add_geometry("point_cloud", t_pcd)  # Add new geometry
                geometry_added = True
            else:
                vis.remove_geometry("point_cloud")  # Remove the existing geometry
                vis.add_geometry("point_cloud", t_pcd)  # Add updated geometry

            end_time = time.time()  # 记录结束时间
            print(f"onCallbackImage function execution time: {end_time - start_time:.6f} seconds")

        except queue.Empty:
            continue  # 队列为空时跳过
        except Exception as reason:
            print(f"Error: {reason}")
    if vis:
        app.quit()


if __name__ == '__main__':
    signal.signal(signal.SIGINT, signal_handler)
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
    parser.add_argument('ip_address', nargs='?', type=str, help='要连接的 IP 地址', default="192.168.0.117")
    parser.add_argument('is_set_para', nargs='?', type=str, help='是否需要设定默认参数', default="0")
    # 解析命令行参数
    args = parser.parse_args()
    print("ip: " + args.ip_address)
    print("is_set_para: " + args.is_set_para)
    is_set_para = int(args.is_set_para)

    success = xtsdk.setConnectIpaddress(args.ip_address)
    xtsdk.startup()


    visual = threading.Thread(target=visualize_3dv)
    visual.start()


    while not exit_event.is_set():
        time.sleep(1)

    print("Stopping...")
    # 清理工作
    # visual.join()  # 等待可视化线程结束
    print("stop")
    xtsdk.stop()
    xtsdk.shutdown()

