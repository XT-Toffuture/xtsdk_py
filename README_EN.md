# **xtsdk_py**

# SDK Description

**Confidential Material**

## Introduction
XTSDK provides easy-to-use programming interfaces by encapsulating radar communication processes (communication, packetization, depth-to-point-cloud conversion), enabling developers to integrate and develop quickly.  
xtsdk_py calls dependency libraries via pybind11 compilation from xtsdk_cpp.

## Compilation Environment
- Languages:  
  - Windows: Python 3.9, Python 3.12  
  - Linux x86/aarch64: Python 3.8, Python 3.11, Python 3.12  
- **NOTE**  
  To support other Python versions, compile using `~/xtsdk_cpp/xtsdk/CMakeLists_pybind.txt`, then copy the generated libraries to the corresponding folders in `~/xtsdk_py/lib/`.

### Dependencies
```bash
pip install numpy opencv-python PyQt5 open3d -i https://pypi.tuna.tsinghua.edu.cn/simple


- Windows:
Boost library: boost_1_79_0-msvc-14.2-64.exe
Download link: https://boostorg.jfrog.io/artifactory/main/release/1.79.0/binaries/boost_1_79_0-msvc-14.2-64.exe
- Linux:
bash
复制代码
sudo apt install libboost-all-dev
Recommended: Boost 1.70.
sdk_example Directory
Contains SDK usage examples.

## Device Connection
cd ~/xtsdk_py/sdk_example
Run with parameters:
Parameter 1: Radar IP address
Parameter 2: 1 (use xtsdk_py/cfg/xintan.xtcfg and ignore radar parameters) / 0 (use radar parameters and ignore local config)
Examples:
Windows: python sdk_sample_***.py 192.168.0.101 0
Linux: python3 sdk_sample_***.py 192.168.0.101 0
Playback from Recorded Files
cd ~/xtsdk_py/sdk_example
Copy recording folder (containing .xbin or hex-encoded .txt files) to this directory.
Run:
Windows: python sdk_sample_play.py [recording_folder_name]
Linux: python3 sdk_sample_play.py [recording_folder_name]
Configuration File
Configurations can be saved via XT-Future GUI and overwritten, or manually edited.

## SDK Instantiation
This SDK uses Python to call a C++ compiled library named xintan_sdk.
Instantiate with:


xtsdk = xintan_sdk.XtSdk()
Event Data Types
sdkState: SDK state changed
devState: Device state changed
Callback Functions

void setCallback(
    std::function<void(const std::shared_ptr<CBEventData>&)> eventcallback,
    std::function<void(const std::shared_ptr<Frame>&)> imgcallback
);
eventcallback: Receives SDK events, device reports, and logs.
imgcallback: Receives depth, grayscale, and point cloud frames.
Xintan LiDAR SDK Data Explanation
Xintan LiDAR is Flash-type with global exposure. Output point cloud format is XYZI with a single timestamp per frame.

Coordinate System: LiDAR coordinate system (LiDAR as origin).
Frame Data:

uint16_t width;           // Frame width
uint16_t height;          // Frame height
uint64_t timeStampS;      // Timestamp (seconds)
uint32_t timeStampNS;     // Timestamp (nanoseconds)
uint16_t temperature;     // Sensor temperature
uint16_t vcseltemperature;// VCSEL temperature
std::vector<uint16_t> distData;   // Filtered depth data (0~964000 = valid)
std::vector<uint16_t> amplData;   // Amplitude data (0~2039 = valid)
std::vector<XtPointXYZI> points;  // Point cloud (undistorted, XYZI format)
Note:
distData: Post-filter depth array (not undistorted).
rawdistData: Pre-filter depth array.


SDK APIs
Connection & Control
- bool setConnectIpaddress(std::string ipAddress);
Set device IP (e.g., "192.168.0.101").
- bool setConnectSerialportName(std::string serialportName);
Set COM port (e.g., "COM2").
- void startup();
Start SDK.
- void shutdown();
Disconnect device.
- bool isconnect();
Check connection status.
- bool isUsedNet();
Check if connected via network.
State & Configuration
- SdkState getSdkState();
Get SDK state.
- SdkState getDevState();
Get device state.
- std::string getStateStr();
Get SDK state as string.
- int getfps();
Get current FPS.
- bool getDevInfo(RespDevInfo &devInfo);
Get device info.
- bool getDevConfig(RespDevConfig &devConfig);
Get device configuration.
Filters & Processing
- bool setSdkKalmanFilter(uint16_t factor, uint16_t threshold);
Set Kalman filter.
- bool setSdkEdgeFilter(uint16_t threshold);
Set edge filter.
- bool setSdkMedianFilter(uint16_t size);
Set median filter.
- void setPostProcess(const float &dilation_pixels, const uint8_t &mode, const double &mode_th);
Optimize near-distance point cloud and moving objects.
- bool clearAllSdkFilter();
Clear all filters.
Device Commands
- bool testDev();
Test device communication.
- bool start(ImageType imgType, bool isOnce = false);
Start measurement with specified image type.
- bool stop();
Stop measurement.
- bool setIp(std::string ip, std::string mask, std::string gate);
Set device IP settings.
- bool setFilter(uint16_t temporal_factor, uint16_t temporal_threshold, uint16_t edgefilter_threshold);
Set device filters.
- bool setIntTimesus(uint16_t timeGs, uint16_t time1, uint16_t time2, uint16_t time3);
Set integration times (µs).
- bool setHdrMode(HDRMode mode);
Set HDR mode (HDR_OFF or HDR_TAMPORAL).
- bool resetDev();
Reboot device.
Advanced Settings
- bool setModFreq(ModulationFreq freqType);
Set modulation frequency (FREQ_12M, FREQ_6M).
- bool setRoi(uint16_t x0, uint16_t y0, uint16_t x1, uint16_t y1);
Set ROI region.
- bool setUdpDestIp(std::string ip, uint16_t port=7687);
Set UDP destination IP.
- bool setMaxFps(uint8_t maxfps);
Set maximum FPS.
- bool setAdditionalGray(const uint8_t &on);
Enable grayscale capture.