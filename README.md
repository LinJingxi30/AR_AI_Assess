# 3D pose 
### config文件夹
- `common_data.py` 为通用（公用）数据文件，比如骨架连接关系，避免重复定义的代码段

## 绘制预览区
- 已经封装成库 j2pc/Json2PreviewClass.py (json to preview class version)
- 使用示例 `j2pcExample.py`
### 方法
- `get_json_frames`: 从json文件中解包帧数据
- `draw_pose_at_pos`: 以指定坐标为中心点绘制骨架（这个别地方可以用）
- `draw_pose`:  按骨架坐标绘制骨架
- `draw_preview_area`: 绘制预览区域

### 类
- `CoordsGenerator`: 骨架步进平移坐标生成器
- `PreviewCoordsGenerator`: 预览坐标生成器（包含上面这个CoordsGenerator类）
### TODO
- 时间戳强制同步未实现
    
## 前端
- static下为静态资源html,css,js,json,mp4等
- mul.html为眼睛Client展示
- dashboard.html为控制台
- backendCapServer.py服务运行在8000端口，可以直接通过localhost:8000/mul.html访问