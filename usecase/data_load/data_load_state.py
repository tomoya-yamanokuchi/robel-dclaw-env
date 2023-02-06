import os, pprint
import matplotlib
import numpy as np
from natsort import natsorted
import sys; import pathlib; p = pathlib.Path(); sys.path.append(str(p.cwd()))
from domain.repository.SimulationDataRepository import SimulationDataRepository as Repository
# import cv2
# cv2.namedWindow('img', cv2.WINDOW_NORMAL)

matplotlib.rcParams['pdf.fonttype'] = 42
matplotlib.rcParams['ps.fonttype'] = 42
import matplotlib.pyplot as plt
from matplotlib import ticker, cm


repository = Repository(
    dataset_dir  = "./dataset",
    # dataset_name = "dataset_20221022145521",
    dataset_name="dataset_202323161720"
)
# query_state = "object_position"
query_state = "robot_position"

# ------------------------------------------------
db_files = os.listdir(repository.dataset_save_dir)
db_files = natsorted(db_files)
pprint.pprint(db_files)

robot_position = []
for db in db_files:
    # import ipdb; ipdb.set_trace()
    db_name, suffix = db.split(".")
    repository.open(filename=db_name)
    state = repository.repository["state"]
    # import ipdb; ipdb.set_trace()
    robot_position.append(state[query_state])
    repository.close()


robot_position = np.stack(robot_position, axis=0)


plt.plot(robot_position[:, :, 0].transpose())
plt.show()