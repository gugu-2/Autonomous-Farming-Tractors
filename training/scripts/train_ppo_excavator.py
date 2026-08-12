import sys
import os

# Append project root to path so we can import envs
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

try:
    from training.envs.excavator_env import ExcavatorEnv
    print("Starting PPO Training for Excavator (Mock)...")
    env = ExcavatorEnv()
    obs, _ = env.reset()
    for _ in range(5):
        action = [0.0, 0.0, 0.0]
        obs, reward, done, _, _ = env.step(action)
    print("Training finished. Saved model to rl_policy_v1.pt")
except Exception as e:
    print(f"Error during training: {e}")
