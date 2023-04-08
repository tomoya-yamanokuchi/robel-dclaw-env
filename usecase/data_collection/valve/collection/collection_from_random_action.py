import sys; import pathlib; p = pathlib.Path(); sys.path.append(str(p.cwd()))
from usecase.data_collection.rollout.rollout_dataset_collection_with_differential_ctrl import rollout_dataset_collection_with_differential_ctrl
from domain.environment.EnvironmentFactory import EnvironmentFactory
from domain.forward_model_multiprocessing.ForwardModelMultiprocessing import ForwardModelMultiprocessing
from domain.environment.task_space.manifold_1d.TaskSpacePositionValue_1D_Manifold import TaskSpacePositionValue_1D_Manifold
from domain.icem_mpc.icem_mpc.population.PopulationSampler import PopulationSampler
from domain.icem_mpc.icem_mpc.population.PopulationSampingDistribution import PopulationSampingDistribution
from domain.icem_mpc.icem_mpc.population.PopulationSampler import PopulationSampler
from custom_service import time_as_string, create_feedable_ctrl_from_less_dim_ctrl



class CollectionfromRandomMotion:
    def __init__(self, config):
        self.config = config


    def get_random_ctrl(self, num_sample, colored_noise_exponent):
        population_sampling_dist = PopulationSampingDistribution(self.config.icem)
        population_sampling_dist.reset_init_distribution(iter_outer_loop=0)
        population_sampler = PopulationSampler(self.config.icem)
        random_ctrl        = population_sampler.sample(
            mean                   = population_sampling_dist.mean,
            std                    = population_sampling_dist.std,
            colored_noise_exponent = colored_noise_exponent,
            num_sample             = num_sample,
        )
        return random_ctrl



    def run_forward_model(self, ctrl, dataset_name):
        env_subclass, state_subclass = EnvironmentFactory().create(env_name=self.config.env.env_name)
        init_state = state_subclass(**self.config.env.init_state)
        multiproc          = ForwardModelMultiprocessing(verbose=False)
        results, proc_time = multiproc.run(
            rollout_function = rollout_dataset_collection_with_differential_ctrl,
            constant_setting = {
                "env_subclass" : env_subclass,
                "config"       : self.config,
                "init_state"   : init_state,
                "TaskSpace"    : TaskSpacePositionValue_1D_Manifold,
                "dataset_name" : dataset_name + "_" + time_as_string(),
            },
            ctrl = ctrl,
        )



if __name__ == "__main__":
    import hydra
    from omegaconf import DictConfig

    @hydra.main(version_base=None, config_path="../../../../conf", config_name="config.yaml")
    def main(config: DictConfig):
        demo          = CollectionfromRandomMotion(config)

        # << --- random action for each claw --- >>
        num_sample_clawX = 300; colored_noise_exponent_clawX=[1.0, 2.0, 3.0]
        random_sample = demo.get_random_ctrl(num_sample_clawX, colored_noise_exponent_clawX)

        ctrl_random_claw1 = create_feedable_ctrl_from_less_dim_ctrl(
            dim_totoal_ctrl=3, task_space_differential_ctrl=random_sample[:, :, :1], dimension_of_interst=[0])

        ctrl_random_claw2 = create_feedable_ctrl_from_less_dim_ctrl(
            dim_totoal_ctrl=3, task_space_differential_ctrl=random_sample[:, :, 1:2], dimension_of_interst=[1])

        ctrl_random_claw3 = create_feedable_ctrl_from_less_dim_ctrl(
            dim_totoal_ctrl=3, task_space_differential_ctrl=random_sample[:, :, 2:], dimension_of_interst=[2])

        # << --- random action for all claw --- >>
        num_sample_all_claw = 600;  colored_noise_exponent_all_claw=[1.0, 2.0, 3.0, 4.0, 5.0, 6.0]
        ctrl_random_all = demo.get_random_ctrl(num_sample_all_claw, colored_noise_exponent_all_claw)

        demo.run_forward_model(ctrl_random_claw1, dataset_name =    "random_action_claw1_NumSample{}_NumColoredNoiseExponent{}".format(num_sample_clawX,    len(colored_noise_exponent_clawX)))
        demo.run_forward_model(ctrl_random_claw2, dataset_name =    "random_action_claw2_NumSample{}_NumColoredNoiseExponent{}".format(num_sample_clawX,    len(colored_noise_exponent_clawX)))
        demo.run_forward_model(ctrl_random_claw3, dataset_name =    "random_action_claw3_NumSample{}_NumColoredNoiseExponent{}".format(num_sample_clawX,    len(colored_noise_exponent_clawX)))
        demo.run_forward_model(ctrl_random_all  , dataset_name = "random_action_all_claw_NumSample{}_NumColoredNoiseExponent{}".format(num_sample_all_claw, len(colored_noise_exponent_all_claw)))

    main()
