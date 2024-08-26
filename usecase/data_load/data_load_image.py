import os
import pprint

import cv2
import numpy as np
from natsort import natsorted
# ------------------------------------
import sys; import pathlib; p=pathlib.Path("./"); sys.path.append(str(p.parent.resolve()))
from domain.repository.SimulationDataRepository import SimulationDataRepository as Repository

cv2.namedWindow('img', cv2.WINDOW_NORMAL)


repository = Repository(
    dataset_dir  = "./dataset",
    # dataset_name = "dataset_2022102122524",
    # dataset_name = "dataset_20221022145521",
    # dataset_name="dataset_dclaw_deterministic_unique_content_train2400"
    # dataset_name="dataset_202323161720"
    # dataset_name="dataset_202323162724"
    # dataset_name="dataset_dclaw_deterministic_valve_aligned_train2400"
    # dataset_name="dataset_202326185453"
    # dataset_name="dataset_dclaw_stochastic_valve_aligned_train2400"
    dataset_name="dataset_dclaw_stochastic_valve_aligned_test300"
)

db_files  = os.listdir(repository.dataset_save_dir)
db_files  = natsorted(db_files)
num_files = len(db_files)
# pprint.pprint(db_files)



for index, db in enumerate(db_files):
    # import ipdb; ipdb.set_trace()
    db_name, suffix = db.split(".")
    repository.open(filename=db_name)
    img_can  = repository.repository["image"]["canonical"]
    img_ran  = repository.repository["image"]["random_nonfix"]
    img_diff = np.abs(img_can - img_ran)
    step, width, height, channel = img_can.shape
    for t in range(step):
        print("({}/{}) [{}] step: {}".format(index+1, num_files, db, t))
        cv2.imshow('img', np.concatenate((img_ran[t], img_can[t], img_diff[t]), axis=1))
        cv2.waitKey(100)

        # print(repository.repository["state"].robot_position)
    repository.close()