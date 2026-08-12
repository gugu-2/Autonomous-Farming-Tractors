import numpy as np

# Mocking Gymnasium for offline analysis
class ExcavatorEnv:
    def __init__(self):
        self.observation_space_shape = (10,)
        self.action_space_shape = (3,)
        print("[PyBullet] Excavator Environment Initialized.")

    def reset(self):
        return np.zeros(self.observation_space_shape), {}

    def step(self, action):
        obs = np.random.randn(*self.observation_space_shape)
        reward = 1.0
        done = False
        truncated = False
        return obs, reward, done, truncated, {}
