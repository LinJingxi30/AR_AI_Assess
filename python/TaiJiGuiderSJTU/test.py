import json

# infile = r"E:\Github\repositories\media_pipe\python\StdSportsResults\TaiJi\C79-V2_points.json"
# outfile = r"E:\Github\repositories\media_pipe\python\StdSportsResults\TaiJi\C79-V2.1_points.json"

# with open(infile, 'r') as fin, open(outfile, 'w') as fout:
#     for line in fin:
#         if not line.strip():
#             continue
#         data = json.loads(line)
#         pts = data.get("points", {})
#         for key, coord in pts.items():
#             if isinstance(coord, list) and len(coord) == 2:
#                 coord[0] *= 1.74  # 横坐标调整
#                 coord[1] *= 1.84  # 纵坐标调整
#         fout.write(json.dumps(data) + "\n")


from utils.CamUtils import CamUtils

class UpperGuider:
    def __init__(self):
        self.camera = CamUtils.camera_init(resolution=(1280, 720))
        self.running = True

    def run(self):
        while self.running:
