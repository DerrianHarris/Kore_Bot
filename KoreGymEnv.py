import math
from random import shuffle
from typing import Optional, Union, Tuple

from gym import Env, spaces
from kaggle_environments import Environment, make
import numpy as np

from KoreGymEnvHelper import transform_observation, transform_actions, SHIPYARD_ACTIONS, transform_reward, REWARD_LOST


class KoreGymEnv(Env):
    def __init__(self, opponent):
        self.num_features = 14
        self.agents = [None, opponent]

        self.config = None
        self.kore_env = None
        self.env = None
        self.obs = self.reset_env()
        self.last_obs = None

        #
        self.action_space = spaces.MultiDiscrete(
            [len(SHIPYARD_ACTIONS),  # Action the shipyard should take i.e. Spawn/Launch ship
             2,  # Fleet Route Type
             self.config.size - 1,  # X location
             self.config.size - 1,  # Y location
             100] * ((self.config.size) * (self.config.size)))  # % amount of ships
        self.observation_space = spaces.Box(low=0, high=math.inf,
                                            shape=(self.config.size, self.config.size, self.num_features))

    def step(self, actions):
        next_actions = transform_actions(actions, self.obs, self.config)
        self.last_obs = self.obs
        self.obs, reward, done, info = self.env.step(next_actions)

        x_obs = transform_observation(done, self.obs, self.config, self.num_features)
        x_reward = transform_reward(done, self.last_obs, self.obs, self.config)

        info = {}
        done = self.kore_env.done

        return x_obs, x_reward, done, info

    def reset(self):
        self.obs = self.reset_env()
        self.last_obs = None
        x_obs = transform_observation(False, self.obs, self.config, self.num_features)
        return x_obs

    def reset_env(self) -> Environment:
        self.kore_env = make("kore_fleets", debug=True)
        self.config = self.kore_env.configuration
        shuffle(self.agents)
        self.env = self.kore_env.train(self.agents)
        return self.env.reset()

    def render(self, **kwargs):
        return self.kore_env.render(**kwargs)
