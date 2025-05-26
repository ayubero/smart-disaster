import gymnasium as gym
from gymnasium import spaces
import numpy as np
import random

GRID_SIZE = 50
LOCAL_OBS_SIZE = 10

class ArsonistEnv(gym.Env):
    def __init__(self):
        super().__init__()
        self.current_step = 0
        self.max_steps = 200
        
        # Grid values: 0=empty, 1=tree, 2=burning_tree, 3=cop, 4=citizen, 5=firefighter
        self.grid = np.zeros((GRID_SIZE, GRID_SIZE), dtype=np.int8)
        
        # Action space: [0] do nothing, [1-4] move (up/down/left/right), [5] ignite
        self.action_space = spaces.Discrete(6)
        
        # Observation: 10x10 partial grid centered around agent, flattened
        self.observation_space = spaces.Box(low=0, high=255, shape=(LOCAL_OBS_SIZE * LOCAL_OBS_SIZE,), dtype=np.uint8)
        
        self.agent_pos = (25, 25)
        self.cop_positions = []
        self.firefighter_positions = []
        self.citizen_positions = []
        self.tree_positions = []
        self.burning_trees = set()
        
        # Tracking for rewards
        self.trees_burned = 0
        self.times_caught = 0
        self.distance_from_cops = 0
        
    def reset(self, *, seed=None, options=None):
        super().reset(seed=seed)
        self.current_step = 0
        self.trees_burned = 0
        self.times_caught = 0
        
        # Reset grid
        self.grid = np.zeros((GRID_SIZE, GRID_SIZE), dtype=np.int8)
        
        # Place agent randomly
        self.agent_pos = (
            np.random.randint(5, GRID_SIZE-5),
            np.random.randint(5, GRID_SIZE-5)
        )
        
        # Generate environment
        self._generate_environment()
        
        obs = self._get_observation()
        info = {}
        return obs, info
    
    def _generate_environment(self):
        '''Generate a realistic environment with trees, cops, firefighters, and citizens'''
        
        # Clear previous positions
        self.cop_positions = []
        self.firefighter_positions = []
        self.citizen_positions = []
        self.tree_positions = []
        self.burning_trees = set()
        
        # Place trees (20-30% of grid)
        num_trees = int(GRID_SIZE * GRID_SIZE * 0.25)
        for _ in range(num_trees):
            while True:
                x, y = np.random.randint(0, GRID_SIZE), np.random.randint(0, GRID_SIZE)
                if (x, y) != self.agent_pos and self.grid[x, y] == 0:
                    self.grid[x, y] = 1
                    self.tree_positions.append((x, y))
                    break
        
        # Place cops (2-4)
        num_cops = np.random.randint(2, 5)
        for _ in range(num_cops):
            while True:
                x, y = np.random.randint(0, GRID_SIZE), np.random.randint(0, GRID_SIZE)
                if (x, y) != self.agent_pos and self.grid[x, y] == 0:
                    self.grid[x, y] = 3
                    self.cop_positions.append((x, y))
                    break
        
        # Place firefighters (1-3)
        num_firefighters = np.random.randint(1, 4)
        for _ in range(num_firefighters):
            while True:
                x, y = np.random.randint(0, GRID_SIZE), np.random.randint(0, GRID_SIZE)
                if (x, y) != self.agent_pos and self.grid[x, y] == 0:
                    self.grid[x, y] = 5
                    self.firefighter_positions.append((x, y))
                    break
        
        # Place citizens (5-10)
        num_citizens = np.random.randint(5, 11)
        for _ in range(num_citizens):
            while True:
                x, y = np.random.randint(0, GRID_SIZE), np.random.randint(0, GRID_SIZE)
                if (x, y) != self.agent_pos and self.grid[x, y] == 0:
                    self.grid[x, y] = 4
                    self.citizen_positions.append((x, y))
                    break
    
    def step(self, action):
        old_pos = self.agent_pos
        reward = 0
        
        # Execute action
        reward += self._execute_action(action)
        
        # Move other agents
        self._move_other_agents()
        
        # Update burning trees (spread fire)
        self._update_fire()
        
        # Check if caught by cop
        if self._check_caught():
            reward -= 100  # Large penalty for being caught
            self.times_caught += 1
        
        # Calculate distance-based reward (stay away from cops)
        reward += self._calculate_distance_reward()
        
        # Reward shaping to encourage better behavior
        if action == 0:
            reward -= 2  # Penalty for doing nothing
        elif 1 <= action <= 4:  # Movement actions
            # Reward for moving towards trees
            reward += self._calculate_tree_proximity_reward()
        
        # Small penalty for each step to encourage efficiency
        reward -= 0.1
        
        self.current_step += 1
        
        observation = self._get_observation()
        terminated = self._check_done()
        truncated = False
        info = {
            'trees_burned': self.trees_burned,
            'times_caught': self.times_caught,
            'step': self.current_step
        }
        
        return observation, reward, terminated, truncated, info
    
    def _execute_action(self, action):
        '''Execute the agent's action and return immediate reward'''
        reward = 0
        x, y = self.agent_pos
        
        if action == 1:  # UP
            new_x = x - 1
            new_y = y
        elif action == 2:  # DOWN
            new_x = x + 1
            new_y = y
        elif action == 3:  # LEFT
            new_x = x
            new_y = y - 1
        elif action == 4:  # RIGHT
            new_x = x
            new_y = y + 1
        elif action == 5:  # IGNITE
            # Check if there are any trees to ignite first
            if not self._has_adjacent_trees(x, y):
                reward -= 10  
                return reward
            
            # Try to ignite current cell or adjacent cells
            ignited = False
            
            # Check current cell first
            if self.grid[x, y] == 1:  # Tree in current cell
                self.grid[x, y] = 2  # Burning tree
                self.burning_trees.add((x, y))
                self.trees_burned += 1
                reward += 50  # Reward for burning a tree
                ignited = True
            else:
                # Check adjacent cells
                for dx in [-1, 0, 1]:
                    for dy in [-1, 0, 1]:
                        if dx == 0 and dy == 0:  # Skip current cell (already checked)
                            continue
                        check_x, check_y = x + dx, y + dy
                        if (0 <= check_x < GRID_SIZE and 0 <= check_y < GRID_SIZE and 
                            self.grid[check_x, check_y] == 1):  # Tree
                            self.grid[check_x, check_y] = 2  # Burning tree
                            self.burning_trees.add((check_x, check_y))
                            self.trees_burned += 1
                            reward += 50  # Reward for burning a tree
                            ignited = True
                            break
                    if ignited:
                        break
            
            return reward
        else:  # action == 0, do nothing
            return reward
        
        # For movement actions, check bounds first (reject out-of-bounds moves)
        if new_x < 0 or new_x >= GRID_SIZE or new_y < 0 or new_y >= GRID_SIZE:
            reward -= 5  # Penalty for trying to move out of bounds
            return reward  # Stay in current position
        
        # Check if new position is valid (not occupied)
        if self.grid[new_x, new_y] == 0:  # Empty space
            self.agent_pos = (new_x, new_y)
            reward += 0.5  # Small reward for moving
        else:
            reward -= 2  # Penalty for trying to move into occupied space
        
        return reward
    
    def _move_other_agents(self):
        '''Simple AI for other agents'''
        
        # Move cops towards arsonist
        new_cop_positions = []
        for cop_x, cop_y in self.cop_positions:
            # Simple pathfinding towards arsonist
            agent_x, agent_y = self.agent_pos
            
            dx = 1 if agent_x > cop_x else (-1 if agent_x < cop_x else 0)
            dy = 1 if agent_y > cop_y else (-1 if agent_y < cop_y else 0)
            
            new_x = cop_x + dx
            new_y = cop_y + dy
            
            # Check bounds and if space is empty
            if (0 <= new_x < GRID_SIZE and 0 <= new_y < GRID_SIZE and 
                self.grid[new_x, new_y] == 0):
                # Update grid
                self.grid[cop_x, cop_y] = 0
                self.grid[new_x, new_y] = 3
                new_cop_positions.append((new_x, new_y))
            else:
                new_cop_positions.append((cop_x, cop_y))
        
        self.cop_positions = new_cop_positions
        
        # Move firefighters towards fires
        new_firefighter_positions = []
        for ff_x, ff_y in self.firefighter_positions:
            moved = False
            
            # Find closest fire
            closest_fire = None
            min_dist = float('inf')
            for fire_pos in self.burning_trees:
                dist = abs(fire_pos[0] - ff_x) + abs(fire_pos[1] - ff_y)
                if dist < min_dist:
                    min_dist = dist
                    closest_fire = fire_pos
            
            if closest_fire:
                fire_x, fire_y = closest_fire
                dx = 1 if fire_x > ff_x else (-1 if fire_x < ff_x else 0)
                dy = 1 if fire_y > ff_y else (-1 if fire_y < ff_y else 0)
                
                new_x = ff_x + dx
                new_y = ff_y + dy
                
                if (0 <= new_x < GRID_SIZE and 0 <= new_y < GRID_SIZE and 
                    self.grid[new_x, new_y] == 0):
                    self.grid[ff_x, ff_y] = 0
                    self.grid[new_x, new_y] = 5
                    new_firefighter_positions.append((new_x, new_y))
                    moved = True
            
            if not moved:
                new_firefighter_positions.append((ff_x, ff_y))
        
        self.firefighter_positions = new_firefighter_positions
    
    def _update_fire(self):
        '''Update fire spread and extinguishing'''
        new_fires = set()
        
        for fire_pos in self.burning_trees.copy():
            x, y = fire_pos
            
            # Check if firefighters are adjacent to extinguish
            extinguished = False
            for ff_x, ff_y in self.firefighter_positions:
                if abs(ff_x - x) <= 1 and abs(ff_y - y) <= 1:
                    # Extinguish fire
                    self.grid[x, y] = 0  # Empty space (burnt)
                    extinguished = True
                    break
            
            if extinguished:
                continue
            
            # Fire spreads to adjacent trees with some probability
            for dx in [-1, 0, 1]:
                for dy in [-1, 0, 1]:
                    if dx == 0 and dy == 0:
                        continue
                    
                    new_x, new_y = x + dx, y + dy
                    if (0 <= new_x < GRID_SIZE and 0 <= new_y < GRID_SIZE and 
                        self.grid[new_x, new_y] == 1 and np.random.random() < 0.1):
                        self.grid[new_x, new_y] = 2
                        new_fires.add((new_x, new_y))
            
            new_fires.add(fire_pos)
        
        self.burning_trees = new_fires
    
    def _check_caught(self):
        '''Check if arsonist is caught by a cop'''
        agent_x, agent_y = self.agent_pos
        for cop_x, cop_y in self.cop_positions:
            if abs(cop_x - agent_x) <= 1 and abs(cop_y - agent_y) <= 1:
                return True
        return False
    
    def _has_adjacent_trees(self, x, y):
        '''Check if there are any trees adjacent to the given position'''
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                check_x, check_y = x + dx, y + dy
                if (0 <= check_x < GRID_SIZE and 0 <= check_y < GRID_SIZE and 
                    self.grid[check_x, check_y] == 1):
                    return True
        return False
    
    def _calculate_tree_proximity_reward(self):
        '''Reward for being close to unburned trees'''
        agent_x, agent_y = self.agent_pos
        closest_tree_dist = float('inf')
        
        # Find closest unburned tree
        for x in range(GRID_SIZE):
            for y in range(GRID_SIZE):
                if self.grid[x, y] == 1:  # Unburned tree
                    dist = abs(x - agent_x) + abs(y - agent_y)
                    closest_tree_dist = min(closest_tree_dist, dist)
        
        if closest_tree_dist == float('inf'):
            return 0  # No trees left
        elif closest_tree_dist <= 1:
            return 5  # Very close to tree
        elif closest_tree_dist <= 3:
            return 2  # Moderately close
        else:
            return 0
    
    def _calculate_distance_reward(self):
        '''Reward for staying away from cops'''
        if not self.cop_positions:
            return 0
        
        agent_x, agent_y = self.agent_pos
        min_distance = float('inf')
        
        for cop_x, cop_y in self.cop_positions:
            distance = abs(cop_x - agent_x) + abs(cop_y - agent_y)
            min_distance = min(min_distance, distance)
        
        # Reward for being far from cops, penalty for being close
        if min_distance <= 2:
            return -10
        elif min_distance <= 5:
            return -2
        else:
            return 1
    
    def _get_observation(self):
        '''Returns a flattened 10x10 partial view centered on the agent.'''
        x, y = self.agent_pos
        half = LOCAL_OBS_SIZE // 2
        
        # Create padded grid
        padded = np.pad(self.grid, ((half, half), (half, half)), mode='constant', constant_values=0)
        
        # Extract local view
        local_view = padded[x:x + LOCAL_OBS_SIZE, y:y + LOCAL_OBS_SIZE]
        
        return local_view.flatten().astype(np.uint8)
    
    def _check_done(self):
        '''Check if episode should end'''
        return (self.current_step >= self.max_steps or 
                self.times_caught > 2 or 
                self.trees_burned >= 20)
    
    def render(self, mode='human'):
        '''Render the environment'''
        if mode == 'human':
            display_grid = self.grid.copy()
            x, y = self.agent_pos
            display_grid[x, y] = 9  # Mark agent
            print(f'Step {self.current_step}, Trees burned: {self.trees_burned}, Times caught: {self.times_caught}')
            print(f'Agent at: {self.agent_pos}')
            # Only print a small section around the agent for clarity
            start_x = max(0, x - 5)
            end_x = min(GRID_SIZE, x + 6)
            start_y = max(0, y - 5)
            end_y = min(GRID_SIZE, y + 6)
            print(display_grid[start_x:end_x, start_y:end_y])
            print('-' * 30)


# Training script
from stable_baselines3 import PPO
from stable_baselines3.common.callbacks import BaseCallback
from stable_baselines3.common.vec_env import DummyVecEnv

class TrainingCallback(BaseCallback):
    def __init__(self, verbose=0):
        super().__init__(verbose)
        self.episode_rewards = []
        self.episode_lengths = []
        
    def _on_step(self) -> bool:
        # Log episode statistics
        if len(self.locals.get('infos', [])) > 0:
            info = self.locals['infos'][0]
            if 'episode' in info:
                self.episode_rewards.append(info['episode']['r'])
                self.episode_lengths.append(info['episode']['l'])
                
                if len(self.episode_rewards) % 100 == 0:
                    mean_reward = np.mean(self.episode_rewards[-100:])
                    print(f'Episode {len(self.episode_rewards)}: Mean reward (last 100): {mean_reward:.2f}')
        
        return True

def train_arsonist():
    # Create environment
    env = DummyVecEnv([lambda: ArsonistEnv()])
    
    # Create callback
    callback = TrainingCallback()
    
    # Create and train model
    model = PPO(
        'MlpPolicy', 
        env, 
        verbose=1,
        learning_rate=3e-4,
        n_steps=2048,
        batch_size=64,
        n_epochs=10,
        gamma=0.99,
        gae_lambda=0.95,
        clip_range=0.2,
        ent_coef=0.01  # Encourage exploration
    )
    
    print('Starting training...')
    model.learn(total_timesteps=1000000, callback=callback)
    
    print('Saving model...')
    model.save('ppo_arsonist')
    
    return model

if __name__ == '__main__':
    model = train_arsonist()