# **xtsdk_py**

# SDK说明

本代码为机密资料
## 简介
XTSDK 提供通过封装了对雷达交互的通讯过程(通讯、封包、深度转点云)，以易用的API方式提供编程接口，方便开发者快速集成开发。
xtsdk_py 通过xtsdk_cpp 的pybind11编译方式进行依赖库调用

## 编译环境
- 语言：windows python3.9
               python3.12
        linux x86 aarch64 python3.8
                        python3.11
                        python3.12
- NOTE
    如果需要支持其他版本 请使用~/xtsdk_cpp/xtsdk/CMakeLists_pybind.txt 进行编译 生成依赖库后复制到
    ~/xtsdk_py/lib/ 相应文件夹

  


- 依赖库：
  pip install numpy opencv-python PyQt5 open3d -i https://pypi.tuna.tsinghua.edu.cn/simple
  windows:- boost库：boost_1_79_0-msvc-14.2-64.exe
    - 下载链接 https://boostorg.jfrog.io/artifactory/main/release/1.79.0/binaries/boost_1_79_0-msvc-14.2-64.exe
  linux: sudo apt install libboost-all-dev
        建议下载boost 1.70版本
  

## sdk_example 目录为sdk的使用示例代码

- 设备连接：cd ~/xtsdk_py/sdk_example
  运行参数1：雷达地址 
  运行参数2：1 xtsdk_py/cfg/xintan.xtcfg 忽略雷达保存的参数 
            0 为使用雷达保存的参数 忽略本地配置文件
      例如 
        windows: python sdk_sample_***.py 192.168.0.101 0
        linux: python3 sdk_sample_***.py 192.168.0.101 0

- 读取录像文件：
	1. cd ~/xtsdk_py/sdk_example
	2. 录像文件夹复制到此文件夹，录像文件夹中放入 xbin文件 或者包含16进制字符串txt文件
	3.  windows: python sdk_sample_play.py   录像文件夹名字		
		linux: python3 sdk_sample_play.py  录像文件夹名字
- 配置文件
    可由XT-Future GUI保存配置 直接覆盖使用 或者手动修改配置文件

  



### sdk实例化
    本实例使用python调用c++编译库 库名为 xintan_sdk
    实例化方法：xtsdk = xintan_sdk.XtSdk()    

### Event数据类型：
    sdkState    sdk状态已改变
    devState    设备状态已改变


## 回调函数
void setCallback(std::function<void(const std::shared_ptr\<CBEventData> &) >  eventcallback, std::function<void(const std::shared_ptr\<Frame> & ) >  imgcallback);

- 设置用于接收sdk回调的两个回调函数
  - eventcallback： 用户接收sdk事件、设备上报的信息、日志等
  - imgcallback： 用户接收 设备的深度、灰度、点云帧

## 芯探激光雷达SDK数据解说
  芯探的激光雷达是Flash类型的，整个sensor全局曝光，所有点都是相同时间点，没有Ring通道的概念， 
	我们输出的点云格式是XYZI，整帧一个时间戳。

	点云的坐标系是就是芯探的雷达坐标系，雷达是坐标系原点。

	相机数据都在imgCallback 中传入的frame 对象中, 
		frame里数据说明：  
			uint16_t width; //数据分辨率宽
			uint16_t height;//数据分辨率高
			uint64_t timeStampS;//帧的时间:秒
			uint32_t timeStampNS;//帧的时间:纳秒
			uint16_t temperature;//sensor 温度
			uint16_t vcseltemperature;//灯板温度
			std::vector<uint16_t> distData;//排序后的距离数据, 深度图从左上角到右下角依次排列所有像素，有效数值是0~964000，964000以上的数值表示此像素无效
			std::vector<uint16_t> amplData;//排序后的信号强度数据, 信号强度从左上角到右下角依次排列所有像素，有效数值是0~2039，64000以上的数值表示此像素无效
			std::vector<XtPointXYZI> points;//点云数据，无序点云，排列方式和distData及amplData数据一样，按像素从左上角到右下角依次排列所有像素
					points里的点数据格式是 XYZI，例如第10行第20列的点的z方向数值是 points[width*10 + 20].z，已去畸变

		***NOTE***
			std::vector<uint16_t> distData 为滤波过后深度数组 rawdistData 为滤波过滤前深度数组，上述深度数据均未去畸变
			

## Sdk运行API
- bool setConnectIpaddress(std::string ipAddress);  
  如果用网络连接，使用这个API设置要连接设备的ip地址(如 "192.168.0.101")

- bool setConnectSerialportName(std::string serialportName);  
​	如果用USB连接，使用这个API设置要连接设备的COM口地址(如 "COM2")

- void startup();  
​	启动sdk运行

- void shutdown();  
​	断开设备连接

- bool isconnect();  
​	设备连接是否成功

- bool isUsedNet();   
  设备连接是否通过网络

- SdkState getSdkState();  
​	获取SDK状态

- SdkState getDevState();  
​	获取设备状态

- std::string getStateStr();  
​	获取SDK 状态字符串

- int getfps();  
    获取SDK计算的帧率

- bool setSdkKalmanFilter(uint16_t factor, uint16_t threshold);  
  设置sdk中的卡尔曼滤波

- bool setSdkEdgeFilter(uint16_t threshold);  
  设置sdk中的飞点滤波

- bool setSdkMedianFilter(uint16_t size);  
    设置sdk中的中值滤波

- void setPostProcess(const float &dilation_pixels, const uint8_t &mode, const double &mode_th);
   设置近距离点云优化以及移动物体优化

- bool clearAllSdkFilter();  
  清除SDK中所有的滤波设置

- bool setSdkCloudCoordType(ClOUDCOORD_TYPE type); 
  设置sdk中输出点云的坐标系

## 命令相关 API

- bool testDev();  
​	测试设备命令交互是否通

- bool start(ImageType imgType, bool isOnce = false);  
​	指定期望的图像类型 进行测量, isOnce 是否单次获取

- bool stop();  
​	让设备停止测量

- bool getDevInfo(RespDevInfo & devInfo);  
​	获取设备信息，数据结构见xtsdk.h定义

- bool getDevConfig(RespDevConfig & devConfig);  
​	获取设备设置信息，数据结构见xtsdk.h定义

- bool setIp(std::string ip, std::string mask, std::string gate);  
​	设置设备的ip地址相关  
​	ip 如 “192.168.0.101”  
​	mask 如”255.255.255.0”  
​	gate 如 “192.168.0.1”

- bool setFilter(uint16_t temporal_factor, uint16_t temporal_threshold, uint16_t edgefilter_threshold);  
​	设置设备内基本滤波参数  
​	temporal_factor   卡尔曼 因子 ，最大1000，通常设定300  
​	temporal_threshold  卡尔曼 阈值，最大2000， 通常设定300  
​	edgefilter_threshold  飞点 阈值，最大2000， 通常设定 0

- bool setIntTimesus(uint16_t timeGs, uint16_t time1, uint16_t time2, uint16_t time3);​	  
    设置积分时间 单位 us  
​	timeGs   测量灰度时的积分时间  
​	time1     第一次积分时间  
​	time2     第二次积分时间，开HDR时才有效，设为0 即关闭此次曝光  
​	time3     第三次积分时间，HDR 为HDR_TAMPORAL   模式时才有效，设为0 即关闭此次曝光

- bool setMinAmplitude(uint16_t minAmplitude);   
​	设置有效的信号幅度下限, 通常设定为50~100

- bool setHdrMode(HDRMode mode);  
​	设置HDR 类型，mode可配置为  
​	HDR_OFF    关闭HDR  
​	HDR_TAMPORAL   时域模式  

- bool resetDev();  
​	重启设备

- bool setModFreq(ModulationFreq freqType);  
​	设置设备调整频率  
​	freqType：  FREQ_12M，FREQ_6M

- bool setRoi(uint16_t x0, uint16_t y0, uint16_t x1, uint16_t y1);  
​	设置ROI区域

- bool setUdpDestIp(std::string ip, uint16_t port =7687);  
  设置UDP目标IP地址

- bool setMaxFps(uint8_t maxfps);  
  设置设备测量的最快帧率，(HDR模式配置为实际要的帧率的多倍(几个积分时间))

- bool getLensCalidata(CamParameterS & camparameter);  
  获取镜头内参

- bool getDevConfig(RespDevConfig &devConfig); 
  获取设备设置信息

- bool setAdditionalGray(const uint8_t &on);
  设置是否获取灰度图

- bool setMultiModFreq(ModulationFreq freqType1, ModulationFreq freqType2, ModulationFreq freqType3, ModulationFreq freqType4 = FREQ_24M); 
  设置三档积分时间对应频率
