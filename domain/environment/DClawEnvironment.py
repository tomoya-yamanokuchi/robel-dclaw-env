import sys
import pathlib
p = pathlib.Path()
sys.path.append(str(p.cwd()))

import math
from traceback import print_tb
import cv2
import os
from matplotlib import ticker
import matplotlib.pyplot as plt
from PIL import Image
import numpy as np
import time
import pickle
import pprint
from typing import List
import copy
import mujoco_py
from mujoco_py.modder import LightModder, CameraModder
from .my_mujoco.modder import myTextureModder as TextureModder
from numpy.lib.function_base import append
from transforms3d.euler import euler2quat, quat2euler
from .DclawEnvironmentRGBFactory import DclawEnvironmentRGBFactory
from .. import dictionary_operation as dictOps
from .DClawState import DClawState
from .AbstractEnvironment import AbstractEnvironment
from ..ImageObject import ImageObject
from .TexturedGeometory import TexturedGeometory


class DClawEnvironment(AbstractEnvironment):
    def __init__(self, config):
        self.width_capture               = config.width_capture
        self.height_capture              = config.height_capture
        self.camera_name_list            = config.camera_name_list
        self.inplicit_step               = config.inplicit_step
        self.env_name                    = config.env_name
        self.env_color                   = config.env_color
        self.claw_jnt_range_lb           = config.claw_jnt_range_lb
        self.claw_jnt_range_ub           = config.claw_jnt_range_ub
        self.valve_jnt_range_lb          = config.object_jnt_range_lb
        self.valve_jnt_range_ub          = config.object_jnt_range_ub
        self.is_use_render               = config.is_use_render
        self.is_Offscreen                = config.is_Offscreen
        self.is_target_visible           = config.is_target_visible
        self.model                       = self.load_model(config.model_file)
        self.light_index_list            = [i for i in config.light.values()]
        self.randomize_texture_mode      = config.randomize_texture_mode
        self.is_noise_randomize_per_step = config.is_noise_randomize_per_step
        self.dynamics                    = config.dynamics
        self.camera                      = config.camera
        self.light                       = config.light

        self._valve_jnt_id               = self.model.joint_name2id('valve_OBJRx')
        self._target_bid                 = self.model.body_name2id('target')
        self._target_sid                 = self.model.site_name2id('tmark')
        self._target_position            = None
        self.sim                         = None
        self.viewer                      = None
        self.texture_modder              = None
        self.camera_modder               = None


    def load_model(self, model_file):
        repository_name = "robel-dclaw-env"
        assert sys.path[-1].split("/")[-1] == repository_name
        xml_path = "{}/domain/environment/model/{}".format(sys.path[-1], model_file)
        return mujoco_py.load_model_from_path(xml_path)


    def _set_geom_names_randomize_target(self):
        self.geom_names_randomize_target = TexturedGeometory()()
        # self.geom_names_randomize_target = self.sim.model.geom_names
        a = 23

    def render_with_viewer(self):
        self.viewer.render()


    def _flip(self, img):
        return img[::-1].copy()


    def _reverse_channel(self, img):
        # for convert Color BGR2RGB
        return img[:,:,::-1].copy()


    def _render_and_convert_color(self, camera_name):
        if self._target_position is not None:
            self.sim.model.body_quat[self._target_bid] = euler2quat(0, 0, float(self._target_position))
        img = self.sim.render(width=self.width_capture, height=self.height_capture, camera_name=camera_name, depth=False)
        img = self._flip(img)
        img = self._reverse_channel(img)
        return ImageObject(img)


    def set_light_on(self, use_light_index_list):
        self.model.light_active[:] = 0
        for i in use_light_index_list:
            self.model.light_active[i] = 1

    def set_texture(self, texture):
        assert isinstance(texture, dict)
        self.texture = texture

    def _set_texture_rand_all_with_return_info(self):
        self.texture = {}
        for name in self.geom_names_randomize_target:
            self.texture[name] = self.texture_modder.my_rand_all(name)

    def _set_texture_static_all(self):
        for geom_name, texture in self.texture.items():
            self.texture_modder.my_set_texture(geom_name, texture, is_noise_randomize=self.is_noise_randomize_per_step)

    def _set_texture_rand_all(self):
        for name in self.geom_names_randomize_target:
            self.texture_modder.rand_all(name)

    def _get_texture_all(self):
        self.texture = {}
        for name in self.geom_names_randomize_target:
            self.texture[name] = self.texture_modder.get_texture(name)


    def randomize_texture(self):
        if self.randomize_texture_mode == "loaded_static":
           self._set_texture_static_all()

        elif self.randomize_texture_mode == "per_reset":
            if self.is_texture_randomized is False:
                # print(self.is_texture_randomized)
                self._set_texture_rand_all_with_return_info()
                self.is_texture_randomized = True
            self._set_texture_static_all()

        elif self.randomize_texture_mode == "per_step":
            # print("ddddd")
            self._set_texture_rand_all()
            self.is_texture_randomized = True


    def canonicalize_texture(self):
        for name in self.geom_names_randomize_target:
            # print("name : {}, rgb {}".format(name, self.rgb[name]))
            self.texture_modder.set_rgb(name, self.rgb[name])


    def _render(self, camera_name: str="canonical"):
        if   "canonical" in camera_name: shadowsize = 0;    self.canonicalize_texture()
        elif    "random" in camera_name: shadowsize = 1024; self.randomize_texture()
        else                           : raise NotImplementedError()
        self.set_light_castshadow(shadowsize=shadowsize)
        self.set_light_on(self.light_index_list)
        return self._render_and_convert_color(camera_name)


    def set_light_castshadow(self, shadowsize):
        self.model.vis.quality.shadowsize = shadowsize
        is_castshadow = 0 if shadowsize==0 else 1
        for name in self.model.light_names:
            self.light_modder.set_castshadow(name, is_castshadow)


    def render(self, camera_name_list: str=None, iteration: int=1):
        img_dict = {}
        if camera_name_list is None:
            camera_name_list = self.camera_name_list
        if self.is_use_render:
            for i in range(iteration):
                for camera_name in camera_name_list:
                    img_dict[camera_name] = self._render(camera_name)
            return img_dict


    def check_camera_pos(self):
        self.sim.reset()
        for i in range(100):
            diff = 0.1
            self.model.cam_pos[0][0] = self.rs.uniform(self.default_cam_pos[0][0] - diff, self.default_cam_pos[0][0] + diff)  # x-axis
            self.model.cam_pos[0][1] = self.rs.uniform(self.default_cam_pos[0][1] - diff, self.default_cam_pos[0][1] + diff)  # x-axis
            self.model.cam_pos[0][2] = self.rs.uniform(self.default_cam_pos[0][2] - diff, self.default_cam_pos[0][2] + diff)  # z-axis
            self.sim.step()
            self.render()


    def set_camera_position(self, camera_parameter: dict):
        pos    = [0]*3
        pos[0] = camera_parameter["x_coordinate"]
        pos[1] = camera_parameter["y_coordinate"]
        pos[2] = camera_parameter["z_distance"]

        orientation = camera_parameter["orientation"]
        quat        = euler2quat(np.deg2rad(orientation), 0.0, np.pi/2)

        reset_cam_names = [cam_name for cam_name in self.sim.model.camera_names if "nonfix" in cam_name]
        for cam_name in reset_cam_names:
            self.camera_modder.set_pos(cam_name, pos)
            self.camera_modder.set_quat(cam_name, quat)
        self.sim.step()
        return pos, orientation


    def set_camera_position_with_all_euler(self, camera_parameter: dict):
        pos    = [0]*3
        pos[0] = camera_parameter["x_coordinate"]
        pos[1] = camera_parameter["y_coordinate"]
        pos[2] = camera_parameter["z_distance"]

        euler = camera_parameter["euler"]
        quat        = euler2quat(*np.deg2rad(euler))

        reset_cam_names = ["cam_canonical_pos_nonfix", "cam_random_pos_nonfix"]
        for cam_name in reset_cam_names:
            self.camera_modder.set_pos(cam_name, pos)
            self.camera_modder.set_quat(cam_name, quat)
        self.sim.step()
        return pos, euler



    def set_light_position(self, light_position: dict):
        assert len(light_position.keys()) == 2
        self.use_light_index_list_random = [int(light_position["light1"]), int(light_position["light2"])]



    def get_camera_parameter(self, isDict: bool = False):
        (x, y, z)  = self.camera_modder.get_pos(name="cam_canonical_pos_nonfix")
        quat       = self.camera_modder.get_quat(name="cam_canonical_pos_nonfix")
        params     = {
                "x_coordinate": x,
                "y_coordinate": y,
                "z_distance"  : z,
                "orientation" : quat2euler(quat)[0]
        }
        if isDict is False:
            params = dictOps.dict2numpyarray(params)
        return params


    def get_light_parameter(self, isDict: bool = False):
        assert len(self.use_light_index_list_random) == 2
        params     = {
            "light1" : self.use_light_index_list_random[0],
            "light2" : self.use_light_index_list_random[1],
        }
        if isDict is False:
            params = dictOps.dict2numpyarray(params)
        return params


    def get_state(self):
        env_state = copy.deepcopy(self.sim.get_state())
        state = DClawState(
            robot_position  = env_state.qpos[:9],
            object_position = env_state.qpos[-1:],
            robot_velocity  = env_state.qvel[:9],
            object_velocity = env_state.qvel[-1:],
        )
        return state


    def set_state(self, qpos, qvel):
        assert(qpos.shape == self.model.nq, "qpos.shape {} != self.model.nq {}".format(qpos.shape, self.model.nq))
        assert(qvel.shape == self.model.nv, "qvel.shape {} != self.model.nv {}".format(qvel.shape, self.model.nv))
        old_state = self.sim.get_state()
        new_state = mujoco_py.MjSimState(old_state.time, qpos, qvel, old_state.act, old_state.udd_state)
        self.sim.set_state(new_state)
        self.sim.data.ctrl[:9] = qpos[:9]
        self.sim.data.ctrl[9:] = 0.0
        self.sim.forward()


    def set_dynamics_parameter(self, randparams_dict: dict) -> None:
        set_dynamics_parameter_function = {
            "kp_claw"            :  self.set_claw_actuator_gain_position,
            "damping_claw"       :  self.set_claw_damping,
            "frictionloss_claw"  :  self.set_claw_frictionloss,
            "kp_valve"           :  self.set_valve_actuator_gain_position,
            "kv_valve"           :  self.set_valve_actuator_gain_velocity,
            "damping_valve"      :  self.set_valve_damping,
            "frictionloss_valve" :  self.set_valve_frictionloss,
        }
        for key, value in randparams_dict.items():
            set_dynamics_parameter_function[key](value)


    def set_claw_actuator_gain_position(self, kp):
        self.sim.model.actuator_gainprm[:9, 0] =  kp
        self.sim.model.actuator_biasprm[:9, 1] = -kp


    def set_claw_damping(self, value):
        self.sim.model.dof_damping[:9] = value


    def set_claw_frictionloss(self, value):
        self.sim.model.dof_frictionloss[:9] = value


    def set_valve_actuator_gain_position(self, kp):
        self.sim.model.actuator_gainprm[-2, 0] =  kp
        self.sim.model.actuator_biasprm[-2, 1] = -kp


    def set_valve_actuator_gain_velocity(self, kv):
        self.sim.model.actuator_gainprm[-1, 0] =  kv
        self.sim.model.actuator_biasprm[-1, 2] = -kv


    def set_valve_damping(self, value):
        self.sim.model.dof_damping[-1] = value


    def set_valve_frictionloss(self, value):
        self.sim.model.dof_frictionloss[-1] = value


    def get_dynamics_parameter(self, isDict: bool = False):
        assert type(isDict) == bool
        dynamics_parameter = {
                "kp_claw"            : self.sim.model.actuator_gainprm[0, 0],
                "damping_claw"       : self.sim.model.dof_damping[0],
                "frictionloss_claw"  : self.sim.model.dof_frictionloss[0],
                "kp_valve"           : self.sim.model.actuator_gainprm[-2, 0],
                "kv_valve"           : self.sim.model.actuator_gainprm[-1, 0],
                "damping_valve"      : self.sim.model.dof_damping[-1],
                "frictionloss_valve" : self.sim.model.dof_frictionloss[-1]
        }
        if isDict is False:
            dynamics_parameter = dictOps.dict2numpyarray(dynamics_parameter)
        return dynamics_parameter


    def create_qpos_qvel_from_InitialState(self, DClawState_: DClawState):
        # qpos
        qpos     = np.zeros(self.sim.model.nq)
        qpos[:9] = DClawState_.robot_position
        qpos[-1] = DClawState_.object_position
        # qvel
        qvel     = np.zeros(self.sim.model.nq)
        qvel[:9] = DClawState_.robot_velocity
        qvel[-1] = DClawState_.object_velocity
        return qpos, qvel


    def reset(self, DClawState_: DClawState):
        assert isinstance(DClawState_, DClawState)
        self.is_texture_randomized = False
        if self.sim is None:
            self._create_mujoco_related_instance()
        self.sim.reset()
        self.set_jnt_range()
        self.set_ctrl_range()
        self.set_dynamics_parameter(self.dynamics)
        self.set_camera_position(self.camera)
        self.set_light_position(self.light)
        self.set_target_visible(self.is_target_visible)
        qpos, qvel = self.create_qpos_qvel_from_InitialState(DClawState_)
        self.set_state(qpos=qpos, qvel=qvel)
        self.render(iteration=1)



    def _create_mujoco_related_instance(self):
        self.sim = mujoco_py.MjSim(self.model)
        if self.is_use_render:
            if self.is_Offscreen: self.viewer = mujoco_py.MjRenderContextOffscreen(self.sim, 0);    print(" init --> viewer"); time.sleep(2)
            else:                 self.viewer = mujoco_py.MjViewer(self.sim);                       print(" init --> "); time.sleep(2)
            # -------------------
            self.texture_modder  = TextureModder(self.sim);                                         print(" init --> texture_modder")
            self.camera_modder   = CameraModder(self.sim);                                          print(" init --> camera_modder")
            self.light_modder    = LightModder(self.sim);                                           print(" init --> light_modder")
            self.default_cam_pos = self.camera_modder.get_pos("canonical");                         print(" init --> default_cam_pos")
            self._set_geom_names_randomize_target();                                                print(" init --> _set_geom_names_randomize_target()")
            factory              = DclawEnvironmentRGBFactory();                                    print(" init --> factory")
            self.rgb             = factory.create(self.env_color, self.geom_names_randomize_target);print(" init --> self.rgb")


    def set_target_position(self, target_position):
        '''
            ・バルブの目標状態の値をセット
            ・target_position: 1次元の数値
            ・renderするときに _target_position が None でなければ描画されます
        '''
        target_position       = float(target_position)
        self._target_position = target_position


    def set_target_visible(self, is_visible):
        if is_visible:
            if self.env_name == "blue": self.sim.model.site_rgba[self._target_sid] = [1.,  0.92156863, 0.23137255, 1]
            else                      : self.sim.model.site_rgba[self._target_sid] = [0, 0, 1, 1]
        else:
            self.sim.model.site_rgba[self._target_sid] = [0, 0, 1, 0]


    def set_action_space(self, action_space):
        self.action_space = action_space


    def set_ctrl(self, ctrl):
        assert ctrl.shape == (9,), '[expected: {0}, input: {1}]'.format((9,), ctrl.shape)
        self.sim.data.ctrl[:9] = ctrl


    def set_object_ctrl(self, ctrl):
        # print("ctrl : {}".format(ctrl))
        assert (ctrl.shape == (1,)) or (ctrl.shape == ()) , '[expected: {0}, input: {1}]'.format((1,), ctrl.shape)
        self.sim.data.ctrl[-1] = ctrl


    def set_jnt_range(self):
        claw_jnt_range_num = len(self.claw_jnt_range_ub)
        # --- claw ---
        jnt_index = 0
        if claw_jnt_range_num == 3:
            for i in range(3):
                for k in range(3):
                    self.sim.model.jnt_range[jnt_index, 0] = self.claw_jnt_range_lb[k]
                    self.sim.model.jnt_range[jnt_index, 1] = self.claw_jnt_range_ub[k]
                    jnt_index += 1
        elif claw_jnt_range_num == 9:
            for jnt_index in range(9):
                self.sim.model.jnt_range[jnt_index, 0] = self.claw_jnt_range_lb[jnt_index]
                self.sim.model.jnt_range[jnt_index, 1] = self.claw_jnt_range_ub[jnt_index]
        else:
            raise NotImplementedError()

        # --- valve ---
        self.sim.model.jnt_range[self._valve_jnt_id, 0] = self.valve_jnt_range_lb
        self.sim.model.jnt_range[self._valve_jnt_id, 1] = self.valve_jnt_range_ub


    def set_ctrl_range(self):
        claw_index = [
            [0, 1, 2],
            [3, 4, 5],
            [6, 7, 8],
        ]
        for claw_index_unit in claw_index:
            self.sim.model.actuator_ctrlrange[claw_index_unit[0], 0] = np.deg2rad(-90)
            self.sim.model.actuator_ctrlrange[claw_index_unit[0], 1] = np.deg2rad(90)

            self.sim.model.actuator_ctrlrange[claw_index_unit[1], 0] = np.deg2rad(-90)
            self.sim.model.actuator_ctrlrange[claw_index_unit[1], 1] = np.deg2rad(90)

            self.sim.model.actuator_ctrlrange[claw_index_unit[2], 0] = np.deg2rad(-90)
            self.sim.model.actuator_ctrlrange[claw_index_unit[2], 1] = np.deg2rad(90)
        return 0


    def step_with_inplicit_step(self):
        '''
        ・一回の sim.step() では，制御入力で与えた目標位置まで到達しないため，これを避けたい時に使います
        ・sim-to-realでは1ステップの状態遷移の違いがそのままダイナミクスのreality-gapとなるため，
        　これを避けるために複数回の sim.step() を内包する当該関数を作成してあります
        ・必要ない場合には def step(self) 関数を使用して下さい
        '''
        for i in range(self.inplicit_step):
            self.sim.step()

        self.viewer.vopt.flags[mujoco_py.const.VIS_CONTACTFORCE] = 1
        # print("self.sim.data.ncon: ", self.sim.data.ncon)
        for i in range(self.sim.data.ncon):
            con = self.sim.data.contact[i]
            # if con.geom1 == self.sim.model.geom_name2id("phy_tip") and con.geom2 == self.sim.model.geom_name2id("phy_valve_6_oclock"):
            if con.geom1:
                # print(con.geom1)
                # print(con.geom2)
                # contact_pos = con.pos
                # self.sim.model.body_pos[self._contact_bid][:] = con.pos
                print(np.abs(self.sim.data.cfrc_ext).sum())
            if self.sim.data.ncon > 0:

                contact_pos = con.pos

                c_array = np.zeros(6, dtype=np.float64)
                print('c_array', c_array)
                mujoco_py.functions.mj_contactForce(self.sim.model, self.sim.data, i, c_array)
                print('c_array', c_array)



    def step(self):
        self.sim.step()