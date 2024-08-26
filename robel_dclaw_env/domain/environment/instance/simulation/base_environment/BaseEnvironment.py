import sys
import numpy as np
import mujoco_py
from .AbstractEnvironment import AbstractEnvironment
from .CtrlInterpolation import CtrlInterpolation


class BaseEnvironment(AbstractEnvironment):
    def __init__(self, config):
        self.inplicit_step      = config.inplicit_step
        self.sim                = None
        self.viewer             = None
        self.rendering          = None
        self.image              = None
        self.ctrl_interpolation = CtrlInterpolation(
            num_interpolation    = config.inplicit_step,
            endpoint_margin_step = config.ctrl_interpolation_margin_step,
        )


    def load_model(self, model_path):
        # import ipdb; ipdb.set_trace()
        return mujoco_py.load_model_from_path(model_path)


    def _step_with_inplicit_step(self, is_view: bool = False):
        '''
        ・一回の sim.step() では，制御入力で与えた目標位置まで到達しないため，これを避けたい時に使います
        ・sim-to-realでは1ステップの状態遷移の違いがそのままダイナミクスのreality-gapとなるため,
          これを避けるために複数回の sim.step() を内包する当該関数を作成してあります
        '''
        interpolated_ctrl = self.ctrl_interpolation.interpolate(
            current_joint_position = self.sim.get_state().qpos[:9],
            target_joint_position  = self.ctrl[:9],
        )
        for i in range(self.inplicit_step):
            # print(f"i={i}")
            self.set_ctrl(interpolated_ctrl[i])
            self.sim.step()
            if is_view:
                self.view()


    def step(self, is_view=False):
        self._step_with_inplicit_step(is_view)


    def set_ctrl(self, joint_space_positioin):
        assert joint_space_positioin.shape == (9,)
        self.sim.data.ctrl[:9] = joint_space_positioin


    @property
    def ctrl(self):
        return self.sim.data.ctrl
