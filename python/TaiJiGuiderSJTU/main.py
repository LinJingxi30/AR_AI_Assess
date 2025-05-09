from guider import Guider
from pregame_align import AlignGuider
import pygame

if __name__ == "__main__":
    # 创建 Guider 实例
    TaiJiGuider = Guider()
    PreGameAligner = AlignGuider()
    
    # 渲染循环
    PreGameAligner.running = True
    PreGameAligner.main_loop()

    TaiJiGuider.running = True
    TaiJiGuider.main_loop()
    
    pygame.quit()
