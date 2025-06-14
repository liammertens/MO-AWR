"""
Discrete water reservoir environment based on:
    A. Castelletti, F. Pianosi and M. Restelli, "Tree-based Fitted Q-iteration for Multi-Objective Markov Decision problems,"
    The 2012 International Joint Conference on Neural Networks (IJCNN),
    Brisbane, QLD, Australia, 2012, pp. 1-8, doi: 10.1109/IJCNN.2012.6252759.

"""

import gymnasium
import numpy as np

from gymnasium import spaces

class Dam(gymnasium.Env):
    def __init__(self, seed=None, s_0=None, penalize=True):
        self.rng = np.random.default_rng(seed)

        self.capacity = 10
        self.water_demand = 4
        self.power_demand = 3
        # inflow distribution
        self.inflow_mean = 2
        self.inflow_std = 1
        self.penalize=penalize

        # NOTE: this assumes that the max water release over a single timestep is the reservoir capacity (which is more than IRL)
        self.action_space = spaces.Discrete(self.capacity)

        """self.observation_space = spaces.Box(
            low=0,
            high=np.inf,
            dtype=np.int64
        )"""
        self.observation_space = spaces.Discrete(150)
        self.reward_space = spaces.Box(
          low=np.array([-np.inf, -np.inf]),
          high=np.zeros(2),
          dtype=np.float32
        )

        self.s_0 = s_0
        self.state = s_0
        self.t = 0

    def reset(self, *, seed=None, options=None):
        super().reset(seed=seed)
        if self.s_0 is not None:
            self.state = self.s_0
        else:
            self.state = np.int64([self.rng.integers(0, self.capacity + 1)])
        self.t = 0
        return self.state, {}

    def step(self, action):
        self.t += 1
        # bound the action
        actionLB = np.clip(self.state - self.capacity, 0, None)
        actionUB = self.capacity

        # Penalty proportional to the violation
        bounded_action = np.clip(action, actionLB, actionUB)
        penalty = -self.penalize * np.abs(bounded_action - action)
        action = bounded_action

        # compute dam inflow
        inflow = int(round(self.rng.normal(self.inflow_mean, self.inflow_std)))
        n_state = np.clip(self.state - action + inflow, 0, None).astype(np.int64)

        """# Flooding objective
        overflow = np.clip(n_state - self.capacity, 0, None)[0]
        r0 = -overflow + penalty"""

        # Deficit in water supply w.r.t. demand
        supply_error = np.clip(n_state - self.water_demand, None, 0)[0]
        r1 = supply_error + penalty

        # deficit in hydro-electric power supply
        deficit = np.clip(self.power_demand - action, 0, None)[0]
        r2 = -deficit + penalty

        """# Flood risk downstream
        flood_risk = np.clip(action - self.flood_threshold, 0, None)[0]
        r3 = -flood_risk + penalty"""

        reward = np.array([r1, r2], dtype=np.float32).flatten()

        self.state = n_state

        return n_state, reward, self.t == 30, False, {}