import os
import time, copy
import numpy as np
import sys; import pathlib; p = pathlib.Path(); sys.path.append(str(p.cwd()))
from domain.forward_model_multiprocessing.ForkedPdb import ForkedPdb
from custom_service import wait_time, NTD
from custom_service import create_gif, join_with_mkdir
from custom_service import save_mpc_planning_images


def rollout_progress_check_differential_without_render(constant_setting, queue_input, queue_result):
    index_chunk, task_space_differential_position = queue_input.get()
    num_chunk, step, dim_ctrl = task_space_differential_position.shape
    assert num_chunk == 1
    wait_time(const=5, seed=index_chunk)

    env_subclass    = constant_setting["env_subclass"]
    config          = constant_setting["config"]
    init_state      = constant_setting["init_state"]
    TaskSpace       = constant_setting["TaskSpace"]
    # ---- additional for progress check ----
    save_fig_dir    = constant_setting["save_fig_dir"]
    iter_outer_loop = constant_setting["iter_outer_loop"]
    iter_inner_loop = constant_setting["iter_inner_loop"]
    dataset_name    = constant_setting["dataset_name"]
    target          = constant_setting["target"].squeeze(0)


    # << ------ rollout ------- >>
    # config.env.target.visible = True
    robot_position_1seq = []
    object_state_1seq   = []
    env = env_subclass(config.env, use_render=False)
    env.reset(init_state)
    for t in range(step):
        # env.set_target_position(target[t])
        # img = env.render(); images.append(img.canonical)
        # -----
        state = env.get_state()
        robot_position_1seq.append(state.state["robot_position"].value)
        object_state_1seq.append(state.state["object_position"].value)
        if t == 1: next_state = copy.deepcopy(state)
        task_space_position = state.state["task_space_position"]
        task_space_ctrl     = task_space_position + TaskSpace(NTD(task_space_differential_position[0, t]))
        # actions             = TaskSpace(action_doi.construct(cumsum_actions)).value
        env.set_ctrl_task_space(task_space_ctrl)
        if t == 0: task_space_ctrl_t = task_space_ctrl.value.squeeze()
        # -----
        env.step()
    state = env.get_state()
    robot_position_1seq.append(state.state["robot_position"].value)
    object_state_1seq.append(state.state["object_position"].value)
    # -----
    robot_position_1seq = np.stack(robot_position_1seq)[np.newaxis, :, :]
    object_state_1seq   = np.stack(object_state_1seq)[np.newaxis, :, :]

    # ForkedPdb().set_trace()
    # << ---- queue procedure ----- >>
    queue_result.put({
        "index_chunk"            : index_chunk,
        "state"                  : next_state,
        "task_space_ctrl"        : task_space_ctrl_t,
        "robot_state_trajectory" : robot_position_1seq,
        "object_state_trajectory": object_state_1seq,
    }) # 結果とバッチインデックスをキューに入れる
    queue_input.task_done() # キューを終了する