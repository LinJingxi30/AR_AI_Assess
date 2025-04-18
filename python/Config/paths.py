# -*- coding: utf-8 -*-            
# @Author : LJX
# @Time : 2025/3/16 20:40
# @Content :

from pathlib import Path
import unittest

# 获取config文件所在目录的上一级目录，也就是仓库根目录
# 第一个 .parent 返回 __file__ 文件所在的目录。第二个 .parent 则进一步获取该目录的上级目录。
MEDIA_PIPE_ROOT = Path(__file__).resolve().parent.parent

STD_SPORTS_RESULTS_ROOT = Path(MEDIA_PIPE_ROOT) / "StdSportsResults"

SPORTS_TYPE_PATH = {
    "太极": Path(STD_SPORTS_RESULTS_ROOT) / "TaiJi",
    "健美操": Path(STD_SPORTS_RESULTS_ROOT) / "Aerobics",
    "瑜伽": Path(STD_SPORTS_RESULTS_ROOT) / "Yoga",
}


class TestPaths(unittest.TestCase):
    def test_tai_chi_file(self):
        tai_chi_path = SPORTS_TYPE_PATH["太极"] / "1.txt"
        try:
            with open(tai_chi_path, 'r', encoding='utf-8') as file:
                content = file.read()
            self.assertIsInstance(content, str)
        except FileNotFoundError:
            self.fail(f"File not found: {tai_chi_path}")

if __name__ == "__main__":
    # unittest.main() # 测试
    pass

# @A last new line here:
