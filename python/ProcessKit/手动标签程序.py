import tkinter as tk
from tkinter import filedialog, messagebox
import tkinter.simpledialog
from PIL import Image, ImageTk
import json
import os
import threading  # 用于延时清除状态提示

RADIAS = 15

class ImageMarker:
    def __init__(self, master):
        # 设置窗口标题和图标
        master.title("手动标注工具")
        # try:
        #     master.iconbitmap("icon.ico")  # 可替换为你的ico文件路径
        # except Exception:
        #     pass

        self.scale = 1.0
        self.master = master
        self.master.bind("<Configure>", self.on_resize)

        # 主布局调整，增加左侧栏和右侧栏
        main_frame = tk.Frame(master)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 左侧栏：显示漏标图片，增加滚动条
        self.left_frame = tk.Frame(main_frame, width=150, bg="lightgray")
        self.left_frame.pack(side=tk.LEFT, fill=tk.Y)
        self.missing_scrollbar = tk.Scrollbar(self.left_frame, orient=tk.VERTICAL)
        self.missing_listbox = tk.Listbox(self.left_frame, width=20, height=20, yscrollcommand=self.missing_scrollbar.set)
        self.missing_scrollbar.config(command=self.missing_listbox.yview)
        self.missing_listbox.pack(side=tk.LEFT, padx=5, pady=5, fill=tk.BOTH, expand=True)
        self.missing_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.missing_listbox.bind("<<ListboxSelect>>", self.on_missing_select)

        # 右侧栏：显示已标图片，增加滚动条
        self.right_frame = tk.Frame(main_frame, width=150, bg="lightgray")
        self.right_frame.pack(side=tk.RIGHT, fill=tk.Y)
        self.done_scrollbar = tk.Scrollbar(self.right_frame, orient=tk.VERTICAL)
        self.done_listbox = tk.Listbox(self.right_frame, width=20, height=20, fg="green", yscrollcommand=self.done_scrollbar.set)
        self.done_scrollbar.config(command=self.done_listbox.yview)
        self.done_listbox.pack(side=tk.LEFT, padx=5, pady=5, fill=tk.BOTH, expand=True)
        self.done_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.done_listbox.bind("<<ListboxSelect>>", self.on_done_select)

        # 中间主区域
        self.canvas_frame = tk.Frame(main_frame)
        self.canvas_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.canvas = tk.Canvas(self.canvas_frame, bg="white")
        self.canvas.pack(fill=tk.BOTH, expand=True)

        # 底部按钮栏
        buttons_frame = tk.Frame(master, height=40)
        buttons_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=2)

        btn_clear_all = tk.Button(buttons_frame, text="清空所有标注", command=self.clear_all_annotations, bg="#b22222", activebackground="#d32f2f", fg="white")
        btn_clear_current = tk.Button(buttons_frame, text="清空当前", command=self.clear_current_annotations)
        btn_left = tk.Button(buttons_frame, text="←上一张", command=self.prev_image)
        btn_right = tk.Button(buttons_frame, text="下一张→", command=self.next_image)
        self.undo_button = tk.Button(buttons_frame, text="撤回", command=self.undo_point, state=tk.DISABLED)
        self.redo_button = tk.Button(buttons_frame, text="重做", command=self.redo_point, state=tk.DISABLED)
        self.jump_entry = tk.Entry(buttons_frame, width=5)
        self.jump_button = tk.Button(buttons_frame, text="跳转", command=self.jump_to_image)
        btn_help = tk.Button(buttons_frame, text="ⓘ使用说明", command=self.show_help, bg="#e0ced9", activebackground="#efced9")
        # 新增自动续播按钮，颜色设置为橙色
        btn_auto_skip = tk.Button(buttons_frame, text="自动续播本帧", command=self.auto_skip_current, bg="#ffa500", activebackground="#ffcc80")

        btn_clear_all.pack(side=tk.LEFT, padx=5)
        btn_clear_current.pack(side=tk.LEFT, padx=5)
        btn_left.pack(side=tk.LEFT, padx=5)
        btn_right.pack(side=tk.LEFT, padx=5)
        self.undo_button.pack(side=tk.LEFT, padx=5)
        self.redo_button.pack(side=tk.LEFT, padx=5)
        self.jump_entry.pack(side=tk.LEFT, padx=5)
        self.jump_button.pack(side=tk.LEFT, padx=5)
        btn_help.pack(side=tk.LEFT, padx=5)
        btn_auto_skip.pack(side=tk.LEFT, padx=5)  

        self.status_label = tk.Label(master, text="", fg="blue")
        self.status_label.pack(side=tk.BOTTOM, anchor=tk.W, pady=2, padx=5)

        self.progress_label = tk.Label(master, text="进度：0/0", fg="green")
        self.progress_label.pack(side=tk.BOTTOM, anchor=tk.W, pady=2, padx=5)

        self.start_frame = tk.Frame(master)
        btn_start = tk.Button(self.start_frame, text="选择文件夹以开始标点", command=self.select_folder)
        btn_start.pack(padx=10, pady=10)
        self.start_frame.pack()

        self.points = []
        self.image_paths = []
        self.current_image_index = 0
        self.annotations = {}
        self.drag_data = {}
        self.point_items = {}
        self.text_items = {}

        # 标点交互相关变量
        self.placing_point = False
        self.placing_point_index = None
        self.placing_point_preview = None
        self.placing_point_text = None

        # 新增撤回/重做栈
        self.undo_stack = []
        self.redo_stack = []

        self.missing_frames = []  # 用于存储漏标的图片索引

        # 绑定快捷键
        self.master.bind("<Control-z>", lambda event: self.undo_point())
        self.master.bind("<Control-y>", lambda event: self.redo_point())

    def select_folder(self):
        folder_path = filedialog.askdirectory(title="选择文件夹")
        if not folder_path:
            return
        self.folder_path = folder_path
        folder_name = os.path.basename(folder_path)
        self.status_label.config(text=f"文件夹：{folder_name}")
        default_json = folder_name + "_points.json"

        dialog = tk.Toplevel(self.master)
        dialog.title("选择json文件处理模式")
        tk.Label(dialog, text=f"文件夹：{folder_name}").pack(pady=5)
        tk.Label(dialog, text="Json文件名：").pack(pady=2)
        entry = tk.Entry(dialog)
        entry.insert(0, default_json)
        entry.pack(pady=2)

        mode_frame = tk.Frame(dialog)
        existing_json = None
        for f in os.listdir(folder_path):
            if f.endswith("_points.json"):
                existing_json = os.path.join(folder_path, f)
                break

        def on_continue():
            self.json_file = os.path.join(self.folder_path, entry.get().strip())
            self.load_images()
            if not os.path.exists(self.json_file):
                with open(self.json_file, 'w') as f:
                    f.write("")
                self.current_image_index = 0
            else:
                # 读取json最后一行的image字段
                last_img = None
                try:
                    with open(self.json_file, 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                        for line in reversed(lines):
                            line = line.strip()
                            if not line:
                                continue
                            try:
                                data = json.loads(line)
                                if "image" in data:
                                    last_img = data["image"]
                                    break
                            except Exception:
                                continue
                except Exception:
                    pass
                if last_img and last_img in [os.path.basename(p) for p in self.image_paths]:
                    try:
                        idx = [os.path.basename(p) for p in self.image_paths].index(last_img)
                        self.current_image_index = idx + 1
                    except Exception:
                        self.current_image_index = 0
                else:
                    self.current_image_index = 0
                self.load_annotations()
            dialog.destroy()
            self.start_annotation(jump_index=self.current_image_index)

        def on_restart():
            self.json_file = os.path.join(self.folder_path, entry.get().strip())
            with open(self.json_file, 'w') as f:
                f.truncate(0)
            self.annotations = {}
            dialog.destroy()
            self.start_annotation(jump_index=0)

        def on_start_from_index():
            self.json_file = os.path.join(self.folder_path, entry.get().strip())
            # 只加载，不清空json
            self.load_annotations()
            self.load_images()
            total = len(self.image_paths)
            idx = tkinter.simpledialog.askinteger("输入索引", f"请输入图片索引（0~{total-1}）：", minvalue=0, maxvalue=total-1, parent=dialog)
            if idx is None:
                return
            if 0 <= idx < total:
                dialog.destroy()
                self.start_annotation(jump_index=idx)
            else:
                messagebox.showinfo("提示", "索引无效，将从第一张开始。")
                dialog.destroy()
                self.start_annotation(jump_index=0)

        if existing_json:
            btn_continue = tk.Button(mode_frame, text="从上次继续", command=on_continue)
            btn_restart = tk.Button(mode_frame, text="清空并从头开始", command=on_restart)
            btn_from_index = tk.Button(mode_frame, text="从指定位置开始", command=on_start_from_index)
            btn_continue.pack(side=tk.LEFT, padx=5, pady=5)
            btn_restart.pack(side=tk.LEFT, padx=5, pady=5)
            btn_from_index.pack(side=tk.LEFT, padx=5, pady=5)
        else:
            btn_restart = tk.Button(mode_frame, text="从头开始", command=on_restart)
            btn_from_index = tk.Button(mode_frame, text="从指定位置开始", command=on_start_from_index)
            btn_restart.pack(side=tk.LEFT, padx=5, pady=5)
            btn_from_index.pack(side=tk.LEFT, padx=5, pady=5)
        mode_frame.pack()
        dialog.grab_set()

    def start_annotation(self, jump_index=0):
        self.start_frame.destroy()
        folder_name = os.path.basename(self.folder_path)
        json_name = os.path.basename(self.json_file)
        self.status_label.config(text=f"文件夹：{folder_name}   标注文件：{json_name}")
        self.load_images()
        # 跳转到指定索引
        if 0 <= jump_index < len(self.image_paths):
            self.current_image_index = jump_index
        else:
            self.current_image_index = 0
        self.show_image()
        self.canvas.bind("<Button-1>", self.record_point)
        self.update_progress()

    def write_annotations_file(self):
        image_order = [os.path.basename(p) for p in self.image_paths]
        order_key = {"left_h": 1, "right_h": 2, "left_f": 3, "right_f": 4, "center": 5}
        with open(self.json_file, 'w') as f:
            for image in image_order:
                if image in self.annotations:
                    points = self.annotations[image].copy()
                    # 保证包含 "skip" 键
                    if "skip" not in points:
                        points["skip"] = False
                    sorted_points = dict(sorted(points.items(), key=lambda item: order_key.get(item[0], 999)))
                    # "skip" 保持在最后
                    if "skip" in sorted_points:
                        cont_value = sorted_points.pop("skip")
                        sorted_points["skip"] = cont_value
                    data = {"image": image, "points": sorted_points}
                    f.write(json.dumps(data) + "\n")
        current_text = self.status_label.cget("text")
        self.status_label.config(text=current_text + " | 保存已完成")
        def clear_tip():
            import time
            time.sleep(1.5)
            folder_name = os.path.basename(self.folder_path)
            json_name = os.path.basename(self.json_file)
            self.status_label.config(text=f"文件夹：{folder_name}   标注文件：{json_name}")
        threading.Thread(target=clear_tip).start()

    def save_points(self):
        image_path = self.image_paths[self.current_image_index]
        image_name = os.path.basename(image_path)
        new_annotation = {
            "left_h": self.points[0],
            "right_h": self.points[1],
            "left_f": self.points[2],
            "right_f": self.points[3],
            "center": self.points[4]
        }
        self.annotations[image_name] = new_annotation
        self.write_annotations_file()
        self.current_image_index += 1
        if self.current_image_index < len(self.image_paths):
            self.show_image()
        else:
            current_text = self.status_label.cget("text")
            self.status_label.config(text=current_text + " | 所有图片标完！")
        self.update_progress()

    def on_resize(self, event):
        # 立即刷新canvas尺寸和图片缩放
        if event.widget == self.master or event.widget == self.canvas:
            self.canvas.update_idletasks()
            self.show_image()

    def load_images(self):
        self.image_paths = [os.path.join(self.folder_path, f) for f in os.listdir(self.folder_path) if
                            f.lower().endswith(('.png', '.jpg', '.jpeg'))]
        self.json_file = next(
            (os.path.join(self.folder_path, f) for f in os.listdir(self.folder_path) if f.endswith('_points.json')),
            os.path.join(self.folder_path, 'default_points.json'))
        if not os.path.exists(self.json_file):
            print("没找到JSON文件")

    def load_annotations(self):
        self.annotations = {}
        if os.path.exists(self.json_file):
            with open(self.json_file, 'r') as f:
                for line in f:
                    if line.strip():
                        try:
                            data = json.loads(line)
                            self.annotations[data["image"]] = data["points"]
                        except:
                            continue

    def show_image(self):
        if not self.image_paths:
            self.img_x = self.img_y = self.disp_w = self.disp_h = 0
            return
        self.canvas.delete("all")
        image_path = self.image_paths[self.current_image_index]
        self.image = Image.open(image_path)

        # 获取canvas实际尺寸，保证居中和缩放实时
        self.canvas.update_idletasks()
        win_w = self.canvas.winfo_width()
        win_h = self.canvas.winfo_height()
        orig_w, orig_h = self.image.size
        bottom_space = 60
        canvas_w = max(win_w, 100)
        canvas_h = max(win_h, 100)
        scale_h = (canvas_h - bottom_space) / orig_h
        scale_w = canvas_w / orig_w
        self.scale = min(scale_h, scale_w)
        disp_w, disp_h = int(orig_w * self.scale), int(orig_h * self.scale)

        img_x = (canvas_w - disp_w) // 2
        img_y = max((canvas_h - disp_h - bottom_space) // 2, 10)

        disp_image = self.image.resize((disp_w, disp_h), Image.LANCZOS)
        self.tk_image = ImageTk.PhotoImage(disp_image)
        self.canvas.create_image(img_x, img_y, anchor=tk.NW, image=self.tk_image)

        self.canvas.create_rectangle(img_x, img_y, img_x + disp_w, img_y + disp_h, outline="red", width=2)

        cx = img_x + disp_w // 2
        cy = img_y + disp_h // 2
        self.canvas.create_line(img_x, cy, img_x + disp_w, cy, fill="blue", dash=(4, 2))
        self.canvas.create_line(cx, img_y, cx, img_y + disp_h, fill="blue", dash=(4, 2))

        self.canvas.create_text(img_x + 5, img_y + disp_h + 20, anchor=tk.SW,
                                text=f"图像分辨率：{orig_w}x{orig_h}", fill="black", font=("Helvetica", 12, "bold"))
        image_name = os.path.basename(image_path)
        self.canvas.create_text(img_x + 5, img_y + 5, anchor=tk.NW,
                                text=f"文件名：{image_name}", fill="black", font=("Helvetica", 14, "bold"))
        folder_name = os.path.basename(self.folder_path)
        self.canvas.create_text(img_x + 5, img_y + disp_h + 40, anchor=tk.SW,
                                text=f"文件夹名称：{folder_name}", fill="black", font=("Helvetica", 12, "bold"))

        # 处理上一中心的显示：向前查找上一个非自动续播的标注中心
        valid_center = None
        if self.current_image_index > 0:
            idx = self.current_image_index - 1
            while idx >= 0:
                prev_image = self.image_paths[idx]
                prev_name = os.path.basename(prev_image)
                if prev_name in self.annotations:
                    pts = self.annotations[prev_name]
                    # 如果标注不是自动续播状态，且中心点有效，则使用该中心
                    if not pts.get("skip", False) and "center" in pts:
                        valid_center = pts["center"]
                        break
                idx -= 1
            if valid_center:
                ox, oy = valid_center
                prev_x = int(ox * self.scale) + img_x
                prev_y = int(oy * self.scale) + img_y
                self.canvas.create_oval(prev_x - RADIAS, prev_y - RADIAS, prev_x + RADIAS, prev_y + RADIAS, outline='orange', width=3)
                self.canvas.create_text(prev_x, prev_y, text="上次中心", fill="orange", font=("Helvetica", 10, "bold"))

        self.points = []
        self.point_items = {}
        self.text_items = {}
        self.undo_stack = []
        self.redo_stack = []
        # 恢复未完成标注时的点（撤销/重做只针对未完成的当前图片）
        if image_name not in self.annotations and hasattr(self, "_pending_points"):
            self.points = self._pending_points.copy()
            self.undo_stack = self.points.copy()
            self.redo_stack = self._pending_redo.copy() if hasattr(self, "_pending_redo") else []
            label_list = ["左手", "右手", "左脚", "右脚", "中心"]
            for idx, (ox, oy) in enumerate(self.points):
                disp_x, disp_y = int(ox * self.scale) + img_x, int(oy * self.scale) + img_y
                self.canvas.create_oval(
                    disp_x - RADIAS, disp_y - RADIAS, disp_x + RADIAS, disp_y + RADIAS, fill='red')
                self.canvas.create_text(
                    disp_x, disp_y, text=label_list[idx], fill="white", font=("Helvetica", 10, "bold"))
        else:
            self._pending_points = []
            self._pending_redo = []
        self.update_undo_redo_buttons()

        ordered_keys = [("left_h", "左手"), ("right_h", "右手"), ("left_f", "左脚"), ("right_f", "右脚"), ("center", "中心")]
        pts = self.annotations.get(image_name, {})
        for key, label in ordered_keys:
            if key in pts:
                ox, oy = pts[key]
                x, y = int(ox * self.scale) + img_x, int(oy * self.scale) + img_y
                oval = self.canvas.create_oval(x - RADIAS, y - RADIAS, x + RADIAS, y + RADIAS, fill='green', tags=("draggable",))
                txt = self.canvas.create_text(x, y, text=label, fill="white", font=("Helvetica", 10, "bold"))
                self.point_items[oval] = key
                self.text_items[oval] = txt
                self.canvas.tag_bind(oval, "<ButtonPress-1>", self.on_point_press)
                self.canvas.tag_bind(oval, "<B1-Motion>", self.on_point_drag)
                self.canvas.tag_bind(oval, "<ButtonRelease-1>", self.on_point_release)
                self.canvas.tag_bind(txt, "<ButtonPress-1>", lambda event, oval=oval: self.on_point_press_custom(event, oval))
                self.canvas.tag_bind(txt, "<B1-Motion>", lambda event, oval=oval: self.on_point_drag_custom(event, oval))
                self.canvas.tag_bind(txt, "<ButtonRelease-1>", lambda event, oval=oval: self.on_point_release_custom(event, oval))

        self.img_x = img_x
        self.img_y = img_y
        self.disp_w = disp_w
        self.disp_h = disp_h
        self.update_progress()

    def record_point(self, event):
        image_name = os.path.basename(self.image_paths[self.current_image_index])
        if image_name in self.annotations:
            return
        label_list = ["左手", "右手", "左脚", "右脚", "中心"]
        if self.placing_point:
            return
        if len(self.points) < 5:
            self.placing_point = True
            self.placing_point_index = len(self.points)
            orig_x = int(round((event.x - self.img_x) / self.scale))
            orig_y = int(round((event.y - self.img_y) / self.scale))
            orig_x = min(max(orig_x, 0), self.image.size[0] - 1)
            orig_y = min(max(orig_y, 0), self.image.size[1] - 1)
            disp_x, disp_y = int(orig_x * self.scale) + self.img_x, int(orig_y * self.scale) + self.img_y
            self.placing_point_preview = self.canvas.create_oval(
                disp_x - RADIAS, disp_y - RADIAS, disp_x + RADIAS, disp_y + RADIAS, fill='red')
            self.placing_point_text = self.canvas.create_text(
                disp_x, disp_y, text=label_list[self.placing_point_index], fill="white", font=("Helvetica", 10, "bold"))
            self.canvas.bind("<B1-Motion>", self.on_placing_point_drag)
            self.canvas.bind("<ButtonRelease-1>", self.on_placing_point_release)
            # 撤回/重做栈只在添加点时有效
            # 只要开始新点，清空redo栈
            self.redo_stack = []
            self._pending_redo = []

    def on_placing_point_drag(self, event):
        if not self.placing_point:
            return
        orig_x = int(round((event.x - self.img_x) / self.scale))
        orig_y = int(round((event.y - self.img_y) / self.scale))
        orig_x = min(max(orig_x, 0), self.image.size[0] - 1)
        orig_y = min(max(orig_y, 0), self.image.size[1] - 1)
        disp_x, disp_y = int(orig_x * self.scale) + self.img_x, int(orig_y * self.scale) + self.img_y
        self.canvas.coords(self.placing_point_preview,
                           disp_x - RADIAS, disp_y - RADIAS, disp_x + RADIAS, disp_y + RADIAS)
        self.canvas.coords(self.placing_point_text, disp_x, disp_y)

    def on_placing_point_release(self, event):
        if not self.placing_point:
            return
        orig_x = int(round((event.x - self.img_x) / self.scale))
        orig_y = int(round((event.y - self.img_y) / self.scale))
        orig_x = min(max(orig_x, 0), self.image.size[0] - 1)
        orig_y = min(max(orig_y, 0), self.image.size[1] - 1)
        self.points.append((orig_x, orig_y))
        self.undo_stack = self.points.copy()
        self._pending_points = self.points.copy()
        self._pending_redo = self.redo_stack.copy()
        self.canvas.unbind("<B1-Motion>")
        self.canvas.unbind("<ButtonRelease-1>")
        self.placing_point = False
        self.placing_point_index = None
        self.placing_point_preview = None
        self.placing_point_text = None
        self.update_undo_redo_buttons()
        if len(self.points) == 5:
            del self._pending_points
            del self._pending_redo
            self.save_points()

    def undo_point(self, event=None):
        """撤回上一个点，仅对当前图片未完成标注时有效"""
        if self.points:
            last = self.points.pop()
            self.redo_stack.append(last)
            self._pending_points = self.points.copy()
            self._pending_redo = self.redo_stack.copy()
            self.show_image()
            # 重新画剩余点
            label_list = ["左手", "右手", "左脚", "右脚", "中心"]
            for idx, (ox, oy) in enumerate(self.points):
                disp_x, disp_y = int(ox * self.scale) + self.img_x, int(oy * self.scale) + self.img_y
                self.canvas.create_oval(
                    disp_x - RADIAS, disp_y - RADIAS, disp_x + RADIAS, disp_y + RADIAS, fill='red')
                self.canvas.create_text(
                    disp_x, disp_y, text=label_list[idx], fill="white", font=("Helvetica", 10, "bold"))
        self.update_undo_redo_buttons()

    def redo_point(self, event=None):
        """重做上一个撤回的点"""
        if self.redo_stack and len(self.points) < 5:
            pt = self.redo_stack.pop()
            self.points.append(pt)
            self._pending_points = self.points.copy()
            self._pending_redo = self.redo_stack.copy()
            self.show_image()
            # 重新画所有点
            label_list = ["左手", "右手", "左脚", "右脚", "中心"]
            for idx, (ox, oy) in enumerate(self.points):
                disp_x, disp_y = int(ox * self.scale) + self.img_x, int(oy * self.scale) + self.img_y
                self.canvas.create_oval(
                    disp_x - RADIAS, disp_y - RADIAS, disp_x + RADIAS, disp_y + RADIAS, fill='red')
                self.canvas.create_text(
                    disp_x, disp_y, text=label_list[idx], fill="white", font=("Helvetica", 10, "bold"))
        self.update_undo_redo_buttons()

    def update_undo_redo_buttons(self):
        """更新撤回和重做按钮的状态"""
        if hasattr(self, "undo_button") and hasattr(self, "redo_button"):
            if self.points:
                self.undo_button.config(state=tk.NORMAL)
            else:
                self.undo_button.config(state=tk.DISABLED)
            if self.redo_stack:
                self.redo_button.config(state=tk.NORMAL)
            else:
                self.redo_button.config(state=tk.DISABLED)

    def update_progress(self):
        """更新进度显示和漏标/已标图片列表"""
        total = len(self.image_paths)
        completed = len(self.annotations)
        self.progress_label.config(text=f"进度：{completed}/{total}")
        # 计算漏标图片
        annotated_images = set(self.annotations.keys())
        self.missing_frames = [
            idx for idx, path in enumerate(self.image_paths)
            if os.path.basename(path) not in annotated_images
        ]
        # 更新左侧列表框
        self.missing_listbox.delete(0, tk.END)
        for idx in self.missing_frames:
            self.missing_listbox.insert(tk.END, f"未标：{idx}")
        # 更新右侧已标列表框
        self.done_listbox.delete(0, tk.END)
        for idx, path in enumerate(self.image_paths):
            img_name = os.path.basename(path)
            if img_name in annotated_images:
                self.done_listbox.insert(tk.END, f"已标：{idx}")

    def on_missing_select(self, event):
        """处理左侧列表框的选择事件"""
        try:
            selection = self.missing_listbox.curselection()
            if selection:
                idx = int(self.missing_listbox.get(selection[0]).split("：")[1])
                self.current_image_index = idx
                self.show_image()
        except Exception:
            pass

    def on_done_select(self, event):
        """处理右侧列表框的选择事件"""
        try:
            selection = self.done_listbox.curselection()
            if selection:
                idx = int(self.done_listbox.get(selection[0]).split("：")[1])
                self.current_image_index = idx
                self.show_image()
        except Exception:
            pass

    def jump_to_image(self):
        """跳转到指定图片索引"""
        try:
            idx = int(self.jump_entry.get())
            if 0 <= idx < len(self.image_paths):
                self.current_image_index = idx
                self.show_image()
            else:
                messagebox.showerror("错误", "索引超出范围！")
        except ValueError:
            messagebox.showerror("错误", "请输入有效的数字索引！")

    def clear_all_annotations(self):
        if messagebox.askyesno("确认", "确定要清空所有标注吗？"):
            if os.path.exists(self.json_file):
                with open(self.json_file, 'w') as f:
                    f.truncate(0)
            self.annotations = {}
            messagebox.showinfo("提示", "所有标注已清空。")
            self.show_image()
            self.update_progress()

    def clear_current_annotations(self):
        image_name = os.path.basename(self.image_paths[self.current_image_index])
        if image_name in self.annotations:
            if messagebox.askyesno("确认", "确定要清空当前图片的标注吗？"):
                del self.annotations[image_name]
                self.write_annotations_file()
                self.show_image()
                self.update_progress()

    def prev_image(self):
        if self.current_image_index > 0:
            self.current_image_index -= 1
            self.show_image()

    def next_image(self):
        if self.current_image_index < len(self.image_paths) - 1:
            self.current_image_index += 1
            self.show_image()

    def on_point_press(self, event):
        item = self.canvas.find_withtag("current")[0]
        x0, y0, x1, y1 = self.canvas.coords(item)
        center_x = (x0 + x1) / 2
        center_y = (y0 + y1) / 2
        self.drag_data = {"item": item, "key": self.point_items[item],
                          "dx": event.x - center_x, "dy": event.y - center_y}

    def on_point_drag(self, event):
        item = self.drag_data.get("item")
        if item:
            new_center_x = event.x - self.drag_data["dx"]
            new_center_y = event.y - self.drag_data["dy"]
            min_x = self.img_x + RADIAS
            max_x = self.img_x + self.disp_w - RADIAS
            min_y = self.img_y + RADIAS
            max_y = self.img_y + self.disp_h - RADIAS
            new_center_x = min(max(new_center_x, min_x), max_x)
            new_center_y = min(max(new_center_y, min_y), max_y)
            self.canvas.coords(item, new_center_x - RADIAS, new_center_y - RADIAS, new_center_x + RADIAS, new_center_y + RADIAS)
            if item in self.text_items:
                self.canvas.coords(self.text_items[item], new_center_x, new_center_y)

    def on_point_release(self, event):
        item = self.drag_data.get("item")
        if item:
            x0, y0, x1, y1 = self.canvas.coords(item)
            disp_cx, disp_cy = (x0 + x1) / 2, (y0 + y1) / 2
            new_center = (int(round((disp_cx - self.img_x) / self.scale)), int(round((disp_cy - self.img_y) / self.scale)))
            key = self.point_items[item]
            image_name = os.path.basename(self.image_paths[self.current_image_index])
            if image_name in self.annotations:
                self.annotations[image_name][key] = new_center
                self.write_annotations_file()
        self.drag_data = {}

    def on_point_press_custom(self, event, oval):
        x0, y0, x1, y1 = self.canvas.coords(oval)
        center_x = (x0 + x1) / 2
        center_y = (y0 + y1) / 2
        self.drag_data = {"item": oval, "key": self.point_items[oval],
                          "dx": event.x - center_x, "dy": event.y - center_y}

    def on_point_drag_custom(self, event, oval):
        new_center_x = event.x - self.drag_data["dx"]
        new_center_y = event.y - self.drag_data["dy"]
        min_x = self.img_x + RADIAS
        max_x = self.img_x + self.disp_w - RADIAS
        min_y = self.img_y + RADIAS
        max_y = self.img_y + self.disp_h - RADIAS
        new_center_x = min(max(new_center_x, min_x), max_x)
        new_center_y = min(max(new_center_y, min_y), max_y)
        self.canvas.coords(oval, new_center_x - RADIAS, new_center_y - RADIAS, new_center_x + RADIAS, new_center_y + RADIAS)
        if oval in self.text_items:
            self.canvas.coords(self.text_items[oval], new_center_x, new_center_y)

    def on_point_release_custom(self, event, oval):
        x0, y0, x1, y1 = self.canvas.coords(oval)
        disp_cx, disp_cy = (x0 + x1) / 2, (y0 + y1) / 2
        new_center = (int(round((disp_cx - self.img_x) / self.scale)), int(round((disp_cy - self.img_y) / self.scale)))
        key = self.point_items[oval]
        image_name = os.path.basename(self.image_paths[self.current_image_index])
        if image_name in self.annotations:
            self.annotations[image_name][key] = new_center
            self.write_annotations_file()
        self.drag_data = {}

    def show_help(self):
        help_text = (
            "【手动标注工具 使用说明】\n"
            "\n"
            "1. 选择文件夹以开始标点：\n"
            "   - 点击主界面按钮，选择包含图片的文件夹。\n"
            "   - 可选择继续上次、清空重来、或从指定索引开始。\n"
            "\n"
            "2. 标注操作：\n"
            "   - 鼠标左键点击图片，依次标注“左手、右手、左脚、右脚、中心”五个点。\n"
            "   - 标注完成自动保存并跳转下一张。\n"
            "\n"
            "3. 撤回/重做：\n"
            "   - “撤回”按钮或Ctrl+Z撤销上一个点。\n"
            "   - “重做”按钮或Ctrl+Y恢复撤销的点。\n"
            "\n"
            "4. 拖动修改已标注点：\n"
            "   - 对于已标注的图片（点击上一张），鼠标拖动绿色点可微调已标注点位置。\n"
            "\n"
            "5. 清空：\n"
            "   - “清空当前”仅清除当前图片标注。\n"
            "   - “清空所有标注”会清空所有图片标注（慎用）。\n"
            "\n"
            "6. 跳转与浏览：\n"
            "   - 输入索引点击“跳转”可快速跳到指定图片。\n"
            "   - 左侧栏显示未标图片，右侧栏显示已标图片，点击可跳转。\n"
            "\n"
            "如有问题请联系开发者。"
        )
        top = tk.Toplevel(self.master)
        top.title("！使用说明 ！")
        top.geometry("520x600")
        txt = tk.Text(top, wrap=tk.WORD, font=("微软雅黑", 11))
        txt.insert(tk.END, help_text)
        txt.config(state=tk.DISABLED)
        txt.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        btn = tk.Button(top, text="关闭", command=top.destroy)
        btn.pack(pady=5)

    # 新增自动续播方法
    def auto_skip_current(self):
        image_path = self.image_paths[self.current_image_index]
        image_name = os.path.basename(image_path)
        # 提供后悔选项
        if not messagebox.askyesno("确认", "确定自动续播本帧吗？此操作不可逆。"):
            return
        # 设置所有标注点均为 (-1,-1) 并标记 skip 为 True
        new_annotation = {
            "left_h": (-1, -1),
            "right_h": (-1, -1),
            "left_f": (-1, -1),
            "right_f": (-1, -1),
            "center": (-1, -1),
            "skip": True
        }
        self.annotations[image_name] = new_annotation
        self.write_annotations_file()
        self.current_image_index += 1
        if self.current_image_index < len(self.image_paths):
            self.show_image()
        else:
            current_text = self.status_label.cget("text")
            self.status_label.config(text=current_text + " | 所有图片标完！")
        self.update_progress()


if __name__ == "__main__":
    root = tk.Tk()
    app = ImageMarker(root)
    root.mainloop()

