import numpy as np

# Mocking Gymnasium for offline analysis
class TractorEnv:
    def __init__(self):
        self.observation_space_shape = (6,)
        self.action_space_shape = (2,)
        print("[PyBullet] Tractor Ackermann Environment Initialized.")

    def reset(self):
        return np.zeros(self.observation_space_shape), {}

    def step(self, action):
        obs = np.random.randn(*self.observation_space_shape)
        reward = 1.0
        done = False
        truncated = False
        return obs, reward, done, truncated, {}
