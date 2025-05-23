from mesa import Agent
from utils import *

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

class CitizenAgent(Agent):
    def __init__(self, model):
        super().__init__(model)

    def step(self):
        self.move_randomly()
        neighbors = self.model.grid.get_neighbors(self.pos, moore=True, include_center=True)
        for agent in neighbors:
            if isinstance(agent, TreeAgent) and agent.on_fire:
                self.model.commander.report_fire(agent.pos)

            if isinstance(agent, ArsonistAgent):
                self.model.commander.report_arsonist(agent.pos)

class ArsonistAgent(Agent):
    def __init__(self, model):
        super().__init__(model)
        self.is_arrested = False

    def step(self):
        if self.is_arrested:
            return
        
        # Look for policemen within 3 cells (Moore neighborhood)
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
            closest_tree.on_fire = True
    
    def run_away_from(self, danger_pos):
        # Get all adjacent cells (Moore neighborhood radius=1)
        possible_moves = self.model.grid.get_neighborhood(self.pos, moore=True, include_center=False)
        
        # Filter only empty cells
        empty_cells = [pos for pos in possible_moves if self.model.grid.is_cell_empty(pos)]

        if not empty_cells:
            self.move_randomly()
            return

        # Choose the farthest cell from the danger
        farthest = max(empty_cells, key=lambda pos: manhattan_distance(pos, danger_pos))
        self.model.grid.move_agent(self, farthest)

class FirefighterAgent(Agent):
    def __init__(self, model, fire_station_position):
        super().__init__(model)
        self.goal = None # Coordinates of the fire (goal) that has to be put out
        self.fire_station_position = fire_station_position

    def step(self):
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

class CommanderAgent(Agent):
    def __init__(self, model):
        super().__init__(model)
        self.known_fires = set()
        self.known_arsonist_positions = []

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