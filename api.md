# API 文档

## nodejs和python通信数据格式

### 帧格式
每个数据帧以 `---FRAME---\n` 作为起始标记，后跟 JSON 格式的头部信息和可选的二进制数据。

#### 图像帧格式
```
---FRAME---
{"type":"image", "length":123456}
<binary_data>
```
- length：后置binary_data长度

#### 控制帧格式
```
---FRAME---
{"type":"control", "command":"PLAY_AUDIO", "flag":1}
```
command: 命令名称
flag：音频控制标志位，int

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

### 2. `join_room`
- **描述**: 加入指定的房间
- **事件类型**: `emit`
- **数据格式**:
  ```json
  {
    "room": "房间ID"
  }
  ```

### 3. `update_room`
- **描述**: 接收房间更新通知
- **事件类型**: `on`
- **数据格式**:
  ```json
  "新房间ID"
  ```

### 4. `process_status`
- **描述**: 接收进程状态更新
- **事件类型**: `on`
- **数据格式**:
  ```json
  "进程状态描述"
  ```

### 5. `start_capture`
- **描述**: 开始捕捉动作
- **事件类型**: `emit`
- **数据格式**:
  ```json
  {
    "action": "动作类型",
    "roomID": "房间ID"
  }
  ```

### 6. `stop_capture`
- **描述**: 控制器发送停止指令
- **事件类型**: `emit`
- **数据格式**:
  ```json
  {
    "roomID": "房间ID"
  }
  ```

### 7. `get_process_status`
- **描述**: 获取当前房间的Python进程状态
- **事件类型**: `emit`
- **返回事件**: `process_status`
- **返回数据格式**: 
  ```json
  "进程状态描述" // "运行中" 或 "已停止"
  ```

---

## HTTP API

### 1. `GET /connections`
- **描述**: 获取所有连接信息
- **响应格式**:
  ```json
  {
    "connections": [
      {
        "id": "socketId",
        "room": "roomId"
      }
    ]
  }
  ```

### 2. `POST /update_room`
- **描述**: 更新指定连接的房间
- **请求体**:
  ```json
  {
    "id": "socketId",
    "room": "newRoomId"
  }
  ```
- **响应**:
  - 成功:
    ```json
    {
      "success": true
    }
    ```
  - 失败:
    ```json
    {
      "error": "错误信息"
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