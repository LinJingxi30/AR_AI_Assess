import cv2
import pygame
from guider import Guider, PYGAME_UI_CONFIG
import utils.CamUtils as CamUtils
from Config import WIN_SIZE

class Animator(Guider):
    """继承自 Guider 支持过渡动画 & 结算动画"""
    def __init__(self, debug=False):
        # config 配置
        self.frame_rate = 30

        # utils 工具
        self.camera = None
        self.frame_rate_clock = None

        # resource 资源
        self.pygame_surface = None  # pygame 画布
        self.screen = None  # pygame 窗口

        # init 初始化工具
        self.camera = CamUtils.camera_init(resolution=(1280, 720))
        self.pygame_init(win_bgm_path=None, win_topic="太极拳指导系统")

        # state 状态
        self.debug = debug
        self.running = True



    def animate(self, duration_sec, draw_frame_func, fps=None):
        """通用动画框架：持续 duration_sec 秒，每帧调用 draw_frame_func(progress)"""
        fps = fps or self.frame_rate
        total_frames = int(duration_sec * fps)
        for i in range(total_frames):
            if self.window_events():
                self.frame_rate_clock.tick(fps)
                # 背景实时帧
                bg = CamUtils.get_camera_processed_frame(self.camera, win_size=WIN_SIZE)
                canvas_rgb = cv2.cvtColor(bg, cv2.COLOR_BGR2RGB)
                surf = pygame.surfarray.make_surface(canvas_rgb.swapaxes(0,1))
                self.screen.blit(surf, (0,0))
                progress = i / max(1, total_frames-1)
                draw_frame_func(progress)
                # 发送
                frame_to_web = self.get_transmit_frame(self.screen)
                if not self.debug:
                    self.send_jpeg_data(frame_to_web)
                pygame.display.flip()

    def animate_title(self, text, duration=1.0, config=PYGAME_UI_CONFIG):
        """开始前淡入大标题"""
        if self.running:
            font = pygame.font.Font(config["标题"]["字体"], config["标题"]["字号"]+20)
            color = config["标题"]["颜色"]
            pos = (WIN_SIZE[0]//2, WIN_SIZE[1]//2)
            def _draw(p):
                surf = font.render(text, True, color)
                surf.set_alpha(int(p * 255))
                rect = surf.get_rect(center=pos)
                self.screen.blit(surf, rect)
            self.animate(duration, _draw)
        else:
            return

    def animate_summary(self, total_score, move_scores:list[int], duration=0.5, bg_image_path=None, config=PYGAME_UI_CONFIG):
        """结束后显示总分及三式得分"""
        if self.running:
            # 预载背景图（可省略）
            bg_img = None
            if bg_image_path:
                bg = cv2.imread(bg_image_path)
                bg = cv2.resize(bg, WIN_SIZE)
                canvas_rgb = cv2.cvtColor(bg, cv2.COLOR_BGR2RGB)
                bg_img = pygame.surfarray.make_surface(canvas_rgb.swapaxes(0,1))
            font_t = pygame.font.Font(config["标题"]["字体"], 50)
            font_s = pygame.font.Font(config["计分"]["字体"], 36)
            def _draw(p):
                # 背景
                if bg_img:
                    self.screen.blit(bg_img,(0,0))
                else:
                    # 实时背景
                    bg = CamUtils.get_camera_processed_frame(self.camera, win_size=WIN_SIZE)
                    canvas_rgb = cv2.cvtColor(bg, cv2.COLOR_BGR2RGB)
                    surfbg = pygame.surfarray.make_surface(canvas_rgb.swapaxes(0,1))
                    self.screen.blit(surfbg,(0,0))
                # 半透明圆角板
                w,h = 400, 300
                panel = pygame.Surface((w,h), pygame.SRCALPHA)
                # 带圆角的半透明背景填充
                pygame.draw.rect(panel,
                                 (0, 0, 0, int(180 * p)),
                                 panel.get_rect(),
                                 border_radius=20)
                # 描边
                pygame.draw.rect(panel,
                                 (255,255,255,int(200 * p)),
                                 panel.get_rect(),
                                 width=2,
                                 border_radius=20)
                x = (WIN_SIZE[0]-w)//2; y=(WIN_SIZE[1]-h)//2
                self.screen.blit(panel, (x,y))
                # 文字
                txt = font_t.render(f"总分：{int(total_score)}", True, (255,215,0))
                self.screen.blit(txt, (x+20, y+20))
                for idx, sc in enumerate(move_scores,1):
                    line = font_s.render(f"动作{idx}：{int(sc)}分", True, (255,255,255))
                    self.screen.blit(line, (x+20, y+80+ (idx-1)*40))
            self.animate(duration, _draw)
        else:
            return

if __name__ == "__main__":
    anim = Animator()
    # anim.running = True
    anim.animate_title("太极拳招式1一①", duration=1)
    # anim.running = True
    anim.animate_summary(100, [90, 85, 95], duration=1)
