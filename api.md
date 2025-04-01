# API 文档

## Socket.IO API

### 1. `frame`
- **描述**: 通过 Socket.IO 广播实时画面数据。
- **事件类型**: `emit`
- **数据格式**: `base64` 编码的图像数据。
- **示例**:
  ```json
  {
    "event": "frame",
    "data": "<base64_encoded_image>"
  }
  ```

### 2. `capture_stopped`
- **描述**: 当 Python 脚本结束时广播通知。
- **事件类型**: `emit`
- **数据格式**:
  ```json
  {
    "message": "Capture process has stopped",
    "code": 0
  }
  ```

### 3. `custom`
- **描述**: 接收客户端自定义消息并广播给所有客户端。
- **事件类型**: `on` 和 `emit`
- **数据格式**:
  ```json
  {
    "event": "custom",
    "data": "<custom_message>"
  }
  ```

---

## HTTP API

### 1. `POST /start_capture`
- **描述**: 启动 Python 脚本以开始捕捉。
- **请求体**:
  ```json
  {
    "action": "<selected_action>"
  }
  ```
- **响应**:
  - 成功:
    ```json
    {
      "status": "success",
      "message": "Capture started"
    }
    ```
  - 失败:
    ```json
    {
      "status": "error",
      "message": "Capture already started"
    }
    ```

### 2. `POST /stop_capture`
- **描述**: 停止 Python 脚本。
- **请求体**: 无
- **响应**:
  - 成功:
    ```json
    {
      "status": "success",
      "message": "Capture stopped"
    }
    ```
  - 失败:
    ```json
    {
      "status": "error",
      "message": "No capture to stop"
    }
    ```

### 3. `POST /video_control`
- **描述**: 控制视频播放状态。
- **请求体**:
  - 播放:
    ```json
    {
      "action": "play",
      "currentTime": <current_time_in_seconds>
    }
    ```
  - 暂停:
    ```json
    {
      "action": "pause"
    }
    ```
- **响应**:
  - 成功:
    ```json
    {
      "status": "success"
    }
    ```
  - 失败:
    ```json
    {
      "status": "error",
      "message": "<error_message>"
    }
    ```