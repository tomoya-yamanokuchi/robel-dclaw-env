import os
import time
import numpy as np
import sys; import pathlib; p = pathlib.Path(); sys.path.append(str(p.cwd()))
from robel_dclaw_env.domain.forward_model_multiprocessing.ForkedPdb import ForkedPdb
from robel_dclaw_env.custom_service import wait_time
from robel_dclaw_env.custom_service import create_gif, join_with_mkdir
from robel_dclaw_env.custom_service import save_mpc_planning_images


def rollout_progress_check_with_return_state_with_render(constant_setting, queue_input, queue_result):
    index_chunk, task_space_position = queue_input.get()
    num_chunk, step, dim_ctrl        = task_space_position.shape
    assert num_chunk == 1
    wait_time(const=5, seed=index_chunk)

    env_subclass    = constant_setting["env_subclass"]
    config          = constant_setting["config"]
    init_state      = constant_setting["init_state"]
    # ---- additional for progress check ----
    save_fig_dir    = constant_setting["save_fig_dir"]
    iter_outer_loop = constant_setting["iter_outer_loop"]
    iter_inner_loop = constant_setting["iter_inner_loop"]
    dataset_name    = constant_setting["dataset_name"]
    target          = constant_setting["target"].squeeze(0)


    # << ------ rollout ------- >>
    config.env.target.visible = True
    env = env_subclass(config.env, use_render=True)
    images = []
    env.reset(init_state)
    for t in range(step):
        env.set_target_position(target[t])
        img = env.render(); images.append(img.canonical)
        if t == 1:
            state = env.get_state()
        env.set_ctrl_task_space(task_space_position[0, t])
        # env.view()
        env.step()

    # << ------ save images as gif ------- >>
    create_gif(
        images   = images,
        fname    = join_with_mkdir(
            save_fig_dir, "progress_gif",
            "elite_progress_iterOuter{}_iterInner{}.gif".format(iter_outer_loop, iter_inner_loop),
            is_end_file = True,
        ),
        duration = 200,
    )

    # << ------ save images as png ------- >>
    save_dir = join_with_mkdir(save_fig_dir, "progress_png",
        "iterOuter{}_iterInner{}".format(iter_outer_loop, iter_inner_loop), is_end_file=False)
    save_mpc_planning_images(
        images    = images,
        save_dir  = save_dir,
        fname     = "elite_progress_iterOuter{}_iterInner{}".format(iter_outer_loop, iter_inner_loop),
    )

    # << ------ save images as gif ------- >>
    np.save(
        file = join_with_mkdir(
            os.path.join("./icem_rollout_progress_dataset", dataset_name,
            'icem_rollout_iterOuter{}_iterInner{}'.format(iter_outer_loop, iter_inner_loop),
            "task_space_position"), is_end_file=True),
        arr  = task_space_position,
    )

    # ForkedPdb().set_trace()
    # << ---- queue procedure ----- >>
    queue_result.put({
        "index_chunk" : index_chunk,
        "state"       : state,
    }) # 結果とバッチインデックスをキューに入れる
    queue_input.task_done() # キューを終了する