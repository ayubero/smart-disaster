from mesa import Agent
from stable_baselines3 import PPO
import numpy as np
from utils import *

INJURY_POINTS = 50 # Injury points received when encountering an arsonist

Agent.move_randomly = move_randomly
Agent.move_towards = move_towards

class TreeAgent(Agent):
    def __init__(self, model):
        super().__init__(model)
        self.on_fire = False

    def step(self):
        pass

class PrisonAgent(Agent):
    def __init__(self, model):
        super().__init__(model)

    def step(self):
        pass

class PolicestationAgent(Agent):
    def __init__(self, model):
        super().__init__(model)

    def step(self):
        pass

class FirestationAgent(Agent):
    def __init__(self, model):
        super().__init__(model)

    def step(self):
        pass

class HospitalAgent(Agent):
    def __init__(self, model):
        super().__init__(model)

    def step(self):
        pass

class CitizenAgent(Agent):
    def __init__(self, model):
        super().__init__(model)
        self.is_injured = False
        # If injury points is 0, then the citizen is healthy
        self.injury_points = 0

    def step(self):
        # If the agent is not injured, he can walk
        if self.injury_points < 1:
            self.move_randomly()

        # Check for problems around the agent
        neighbors = self.model.grid.get_neighbors(self.pos, moore=True, include_center=True)
        for agent in neighbors:
            if isinstance(agent, TreeAgent) and agent.on_fire:
                self.model.commander.report_fire(agent.pos)

            if isinstance(agent, ArsonistAgent):
                self.model.commander.report_arsonist(agent.pos)

            if isinstance(agent, CitizenAgent) and agent.injury_points > 0:
                self.model.commander.report_injured(agent.pos)

            if isinstance(agent, FirefighterAgent) and agent.injury_points > 0:
                self.model.commander.report_injured(agent.pos)

        # Check current cell for arsonist to become injured or hospital to heal
        cell_agents = self.model.grid.get_cell_list_contents(self.pos)
        for agent in cell_agents:
            if isinstance(agent, ArsonistAgent):
                self.injury_points = INJURY_POINTS
                break  # No need to check further
            if isinstance(agent, HospitalAgent):
                self.injury_points -= 1
                break

class ArsonistAgent(Agent):
    def __init__(self, model, rl_model, prison_position):
        super().__init__(model)
        self.ppo_model = rl_model
        self.is_arrested = False
        self.prison_position = prison_position

    def step(self):
        if self.is_arrested:
            return
        
        obs = self.get_partial_observation() # 10x10 flattened

        action, _ = self.ppo_model.predict(obs, deterministic=True)
        print(action)
        self.perform_action(action)
        
        '''# Look for policemen within 3 cells (Moore neighborhood)
        police_neighbors = self.model.grid.get_neighbors(self.pos, moore=True, include_center=False, radius=3)
        policemen = [a for a in police_neighbors if isinstance(a, PolicemanAgent)]

        if policemen:
            # Run away from the nearest policeman
            my_pos = self.pos
            closest_cop = min(policemen, key=lambda p: manhattan_distance(my_pos, p.pos))
            self.run_away_from(closest_cop.pos)
            return

        # Continue with tree-burning behavior
        neighbors = self.model.grid.get_neighbors(self.pos, moore=True, include_center=True)
        healthy_trees = [agent for agent in neighbors if isinstance(agent, TreeAgent) and not agent.on_fire]

        if not healthy_trees:
            self.move_randomly()
            return

        closest_tree = min(healthy_trees, key=lambda t: manhattan_distance(self.pos, t.pos))
        if self.pos != closest_tree.pos:
            self.move_towards(closest_tree.pos)
        else:
            closest_tree.on_fire = True'''
        
    def get_partial_observation(self):
        width, height = self.model.grid.width, self.model.grid.height

        # Create a numerical 2D representation of the grid (e.g., 0=empty, 1=tree, 2=burning, etc.)
        grid_array = np.zeros((width, height), dtype=np.float32)
        
        for x in range(width):
            for y in range(height):
                cell = self.model.grid.get_cell_list_contents((x, y))
                if not cell:
                    grid_array[x, y] = 0
                else:
                    # Simple mapping based on agent type - match training environment
                    for agent in cell:  # Check all agents in cell
                        if isinstance(agent, TreeAgent):
                            if agent.on_fire:
                                grid_array[x, y] = 2  # Burning tree
                            else:
                                grid_array[x, y] = 1  # Normal tree
                        elif isinstance(agent, PolicemanAgent):
                            grid_array[x, y] = 3  # Cop
                        elif isinstance(agent, CitizenAgent):
                            grid_array[x, y] = 4  # Citizen
                        elif isinstance(agent, FirefighterAgent):
                            grid_array[x, y] = 5  # Firefighter

        # Pad grid so we can always extract a centered 10x10
        padded = np.pad(grid_array, pad_width=5, mode='constant', constant_values=0)
        x, y = self.pos
        x += 5
        y += 5
        local = padded[x - 5:x + 5, y - 5:y + 5]  # 10x10 window
        return local.flatten().astype(np.float32)  # Shape: (100,)
    
    def perform_action(self, action):
        """
        Take an action in the environment with improved logic.
        0 = do nothing
        1 = move up  
        2 = move down
        3 = move left
        4 = move right
        5 = set fire to nearby trees
        """
        if action == 0:
            pass  # do nothing
        elif action == 1:
            self.move(0, -1)  # move up
        elif action == 2:
            self.move(0, 1)   # move down
        elif action == 3:
            self.move(-1, 0)  # move left
        elif action == 4:
            self.move(1, 0)   # move right
        elif action == 5:
            self.set_fire()

    def set_fire(self):
        """Improved fire setting with proper tree checking"""
        x, y = self.pos
        ignited = False
        
        # Check current cell first
        cell_agents = self.model.grid.get_cell_list_contents(self.pos)
        for agent in cell_agents:
            if isinstance(agent, TreeAgent) and not agent.on_fire:
                agent.on_fire = True
                ignited = True
                print(f"Arsonist ignited tree at {self.pos}")
                return
        
        # If no tree in current cell, check adjacent cells
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                if dx == 0 and dy == 0:  # Skip current cell
                    continue
                    
                check_x, check_y = x + dx, y + dy
                if self.model.grid.out_of_bounds((check_x, check_y)):
                    continue
                    
                adjacent_agents = self.model.grid.get_cell_list_contents((check_x, check_y))
                for agent in adjacent_agents:
                    if isinstance(agent, TreeAgent) and not agent.on_fire:
                        agent.on_fire = True
                        ignited = True
                        print(f"Arsonist ignited adjacent tree at ({check_x}, {check_y})")
                        return
        
        if not ignited:
            print(f"Arsonist tried to ignite but no trees nearby at {self.pos}")

    def move(self, dx, dy):
        """Improved movement with bounds checking"""
        new_x = self.pos[0] + dx
        new_y = self.pos[1] + dy
        
        if self.model.grid.out_of_bounds((new_x, new_y)):
            print(f"Arsonist tried to move out of bounds to ({new_x}, {new_y})")
            return
            
        # Check if target cell has immovable objects (buildings)
        target_agents = self.model.grid.get_cell_list_contents((new_x, new_y))
        for agent in target_agents:
            if isinstance(agent, (PrisonAgent, PolicestationAgent, FirestationAgent, HospitalAgent)):
                print(f"Arsonist can't move into building at ({new_x}, {new_y})")
                return
        
        self.model.grid.move_agent(self, (new_x, new_y))
        print(f"Arsonist moved to {self.pos}")
    
    def run_away_from(self, danger_pos):
        # Get all adjacent cells (Moore neighborhood radius=1)
        possible_moves = self.model.grid.get_neighborhood(self.pos, moore=True, include_center=False)
        
        # Filter only accessible cells (not buildings)
        accessible_cells = []
        for pos in possible_moves:
            if self.model.grid.out_of_bounds(pos):
                continue
            cell_agents = self.model.grid.get_cell_list_contents(pos)
            is_blocked = any(isinstance(agent, (PrisonAgent, PolicestationAgent, FirestationAgent, HospitalAgent)) 
                           for agent in cell_agents)
            if not is_blocked:
                accessible_cells.append(pos)

        if not accessible_cells:
            print("Arsonist has nowhere to run!")
            return

        # Choose the farthest cell from the danger
        farthest = max(accessible_cells, key=lambda pos: manhattan_distance(pos, danger_pos))
        self.model.grid.move_agent(self, farthest)
        print(f"Arsonist ran away to {self.pos}")


class FirefighterAgent(Agent):
    def __init__(self, model, fire_station_position):
        super().__init__(model)
        self.goal = None # Coordinates of the fire (goal) that has to be put out
        self.fire_station_position = fire_station_position
        self.injury_points = 0

    def step(self):
        if self.injury_points < 1:
            if self.goal:
                if self.pos != self.goal:
                    self.move_towards(self.goal)
                else:
                    # At the fire location
                    if self.goal not in self.model.firefighter_presence:
                        self.model.firefighter_presence[self.goal] = set()
                    self.model.firefighter_presence[self.goal].add(self.unique_id)

                    # Check for sufficient firefighters to put out the fire
                    if len(self.model.firefighter_presence[self.goal]) >= 3:
                        # Extinguish the fire
                        for agent in self.model.grid.get_cell_list_contents(self.goal):
                            if isinstance(agent, TreeAgent) and agent.on_fire:
                                agent.on_fire = False
                                self.model.commander.known_fires.discard(self.goal)
                                break

                        # Reset fire info
                        del self.model.firefighter_presence[self.goal]

                        # All firefighters on this goal reset
                        for agent in self.model.agents:
                            if isinstance(agent, FirefighterAgent): #and agent.goal == self.goal
                                agent.goal = None
            else:
                fire_list = self.model.commander.get_fires()
                if fire_list: # Vote
                    if not hasattr(self, '_vote') or self._vote is None:
                        # Cast vote if not yet voted this round
                        self._vote = self.random.choice(self.model.commander.get_fires())
                else:
                    # No fire, return to firestation
                    if self.pos != self.fire_station_position:
                        self.move_towards(self.fire_station_position)

        # Check current cell for arsonist to become injured or hospital to heal
        cell_agents = self.model.grid.get_cell_list_contents(self.pos)
        for agent in cell_agents:
            if isinstance(agent, ArsonistAgent):
                self.injury_points = INJURY_POINTS
                break  # No need to check further
            if isinstance(agent, HospitalAgent):
                self.injury_points -= 1
                break

class PolicemanAgent(Agent):
    def __init__(self, model, policestation_position, prison_position):
        super().__init__(model)
        self.policestation_position = policestation_position
        self.prison_position = prison_position
        self.target_arsonist = None

    def step(self):
        if self.target_arsonist is not None: #and self.model.grid.get_cell_list_contents(self.target_arsonist):
            if self.pos == self.target_arsonist: # We arrived at the target location
                self.target_arsonist = None
            else:
                self.move_towards(self.target_arsonist)
        else:
            self.target_arsonist = self.model.commander.get_arsonist_position()
            if self.target_arsonist is not None:
                self.move_towards(self.target_arsonist)

        # Check if arsonist is at current position
        cell_agents = self.model.grid.get_cell_list_contents(self.pos)
        for agent in cell_agents:
            if isinstance(agent, ArsonistAgent):
                # Move arsonist to prison
                self.model.grid.move_agent(agent, self.prison_position)
                agent.is_arrested = True
                self.target_arsonist = None

        '''if self.target_arsonist is None:
            self.move_towards(self.policestation_position)'''
        
class AmbulanceAgent(Agent):
    def __init__(self, model, hospital_position):
        super().__init__(model)
        self.hospital_position = hospital_position
        self.target_patient = None

    def step(self):
        if self.target_patient is not None:
            if self.pos == self.target_patient:
                self.target_patient = None
            else:
                self.move_towards(self.target_patient)
        else:
            self.target_patient = self.model.commander.get_injured_position()
            if self.target_patient is not None:
                self.move_towards(self.target_patient)

        # Check if patient is at current position
        cell_agents = self.model.grid.get_cell_list_contents(self.pos)
        for agent in cell_agents:
            if (isinstance(agent, CitizenAgent) or isinstance(agent, FirefighterAgent)) and agent.injury_points > 0:
                # Move patient to the hospital
                self.model.grid.move_agent(agent, self.hospital_position)

class CommanderAgent(Agent):
    def __init__(self, model):
        super().__init__(model)
        self.known_fires = set()
        self.known_arsonist_positions = []
        self.known_injured = set()

    def report_fire(self, pos):
        self.known_fires.add(pos)

    def get_fires(self):
        return list(self.known_fires)
    
    def report_arsonist(self, pos):
        self.known_arsonist_positions.append(pos)

    def get_arsonist_position(self):
        if len(self.known_arsonist_positions) > 0:
            return self.known_arsonist_positions.pop(0)
        else:
            return None
        
    def report_injured(self, pos):
        self.known_injured.add(pos)

    def get_injured_position(self):
        #return self.known_injured
        if len(self.known_injured) > 0:
            return self.known_injured.pop()
        else:
            return None
    
    def tally_votes(self):
        votes = [
            agent._vote
            for agent in self.model.agents
            if isinstance(agent, FirefighterAgent) and getattr(agent, '_vote', None)
        ]
        if not votes:
            return None
        winning = max(set(votes), key=votes.count)
        return winning

    def step(self):
        pass