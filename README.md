# 3D pose 
### config文件夹
- `common_data.py` 为通用（公用）数据文件，比如骨架连接关系，避免重复定义的代码段

## stdProcess 标准帧采样遮罩处理
- 在 stdProcess\\`config.py` 进行配置
- 标准采样遮罩帧生成完整脚本：stdProcess\\`StandardGenerate.py`
- 运行后在 stdProcess 文件夹内进行存取

## ProcessKit 库
- 全局通用处理脚本，统一放到`ProcessKit`文件夹中
- `Draw` 模块中的 `draw_skeleton` 方法，可以方便地通过config字典配置画法（将config字典传入函数中），
  字典格式参见 Config\\`common_data.py` 中的 `DRAW_SKET_OVERALL_CONFIG` 字典
```
ProcessKit/
├── __init__.py
├── Draw.py
├── Images2Masks.py
├── j2pcExample.py
├── Json2Images.py
├── Json2PreviewClass.py
├── JsonDiffSampler.py
└── Video2Json.py
```

<!-- 
## 绘制预览区
- 已经封装成库 j2pc/Json2PreviewClass.py (json to preview class version)
- **使用示例 `j2pcExample.py`**
  
### 方法
- `get_json_frames`: 从json文件中解包帧数据
- `draw_pose_at_pos`: 以指定坐标为中心点绘制骨架（这个别地方可以用）
- `draw_pose`:  按骨架坐标绘制骨架
- `draw_preview_area`: 绘制预览区域

### 类
- `CoordsGenerator`: 骨架步进平移坐标生成器
- `PreviewCoordsGenerator`: 预览坐标生成器（包含上面这个CoordsGenerator类）
### TODO
- 时间戳强制同步未实现 -->

    
## 前端
### 启动
安装nodejs(version>18.0)后运行`npm install`安装依赖；运行`npm run start`启动服务器在8000端口；在浏览器输入本机ip:8000进入系统
- static下为静态资源html,css,js,json,mp4等
- dashboard.html为socketio接入情况的控制台，同时可以设置房间分组
- control.html为选择动作和控制python程序与结束的控制器
- display.html为AR眼镜端全屏展示页面
- 控制器和展示端需要在一个Room内才能启动python程序

## 打包流程
###python
使用嵌入式python打包后分发，避免用户安装python环境
- 首先从[官网下载](https://www.python.org/downloads/windows/)对应版本的embbeddable package
- 解压到项目文件夹下/python中，修改/python下一个后缀是`.pth`的文件，将import site前的#删除（这行代码用来导入依赖的）
- 下面来安装pip可执行文件来安装依赖，先新建get-pip.py,将[这个网页内容](https://bootstrap.pypa.io/get-pip.py)写入，然后打开命令行到python目录中运行`python.exe get-pip.py`，安装完成后出现Lib和Scripts文件夹
- 命令行进入项目文件夹，运行`python/Scripts/pip.exe install -r requirements.txt`安装依赖
- 然后保证项目文件夹中没有.env文件，nodejs会优先使用嵌入python作为解释器
**执行pack.bat可以直接构建嵌入式python并安装依赖**