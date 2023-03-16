import numpy as np
import sys; import pathlib; p = pathlib.Path(); sys.path.append(str(p.cwd()))
from domain.icem.iCEM_MPC import iCEM_MPC
from domain.icem.cost_function_example import norm_sum_over_timestep
from domain.icem.forward_model_example import forward_model_with_fixed_initial_point
from domain.icem.target_example import sliding_cos_sin_target


horizon        = 30
cost_fn        = norm_sum_over_timestep
sliding_target = lambda t: sliding_cos_sin_target(horizon, t)
forward_model  = forward_model_with_fixed_initial_point


icem = iCEM_MPC(
    forward_model          = forward_model,
    num_sample             = 300,
    decay_sample           = 1.25,
    num_elite              = 10,
    fraction_rate_elite    = 0.3,
    num_cem_iter           = 5,
    planning_horizon       = horizon,
    dim_action             = 2,
    colored_noise_exponent = 3.0,
    lower_bound            = -1.0, # -0.1,
    upper_bound            = 1.0, # 0.1,
    alpha                  = 0.1,
    init_std               = 0.5,
    verbose                = True,
    verbose_additional     = False,
    is_visualize           = True,
)


for t in range(30):
    icem.reset()
    target = sliding_target(t)
    cost = icem.optimize(
        state         = (target[0][0, 0], target[0][0, 1]),
        target        = target,
        cost_function = cost_fn,
    )

    cost_min  = icem.cost_history.get_cost_min()
    cost_max  = icem.cost_history.get_cost_min()
    cost_mean = icem.cost_history.get_cost_min()
