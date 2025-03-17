# -*- coding: utf-8 -*-            
# @Author : LJX
# @Time : 2025/3/16 20:40
# @Content :

from pathlib import Path

# 获取config文件所在目录的上一级目录，也就是仓库根目录
# 第一个 .parent 返回 __file__ 文件所在的目录。第二个 .parent 则进一步获取该目录的上级目录。
MEDIA_PIPE_ROOT = Path(__file__).resolve().parent.parent

# @A last new line here:
