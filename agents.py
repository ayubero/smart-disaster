from mesa import Agent
from utils import *

Agent.move_randomly = move_randomly
Agent.move_towards = move_towards

class TreeAgent(Agent):
    def __init__(self, unique_id, model):
        super().__init__(model)
        self.on_fire = False

    def step(self):
        pass

class PrisonAgent(Agent):
    def __init__(self, unique_id, model):
        super().__init__(model)

    def step(self):
        pass

class FirestationAgent(Agent):
    def __init__(self, unique_id, model):
        super().__init__(model)

    def step(self):
        pass

class CitizenAgent(Agent):
    def __init__(self, unique_id, model):
        super().__init__(model)

    def step(self):
        self.move_randomly()
        neighbors = self.model.grid.get_neighbors(self.pos, moore=True, include_center=True)
        for agent in neighbors:
            if isinstance(agent, TreeAgent) and agent.on_fire:
                #print(f'[CITIZEN] Reporting fire at {agent.pos}')
                self.model.commander.report_fire(agent.pos)

class ArsonistAgent(Agent):
    def __init__(self, unique_id, model):
        super().__init__(model)

    def step(self):
        neighbors = self.model.grid.get_neighbors(self.pos, moore=True, include_center=True)

        healthy_trees = [agent for agent in neighbors if isinstance(agent, TreeAgent) and not agent.on_fire]

        if not healthy_trees:
            self.move_randomly()
            return  # Nothing to do

        # Find the nearest tree
        my_pos = self.pos
        closest_tree = min(healthy_trees, key=lambda t: manhattan_distance(my_pos, t.pos))

        # Move towards it if not already there
        if self.pos != closest_tree.pos:
            self.move_towards(closest_tree.pos)
        else:
            # Set the tree on fire
            closest_tree.on_fire = True

class FirefighterAgent(Agent):
    def __init__(self, unique_id, model, firestation_position):
        super().__init__(model)
        self.goal = None # Coordinates of the fire (goal) that has to be put out
        self.firestation_position = firestation_position

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
                if not hasattr(self, "_vote") or self._vote is None:
                    # Cast vote if not yet voted this round
                    self._vote = self.random.choice(self.model.commander.get_fires())
            else:
                # No fire, return to firestation
                if self.pos != self.firestation_position:
                    self.move_towards(self.firestation_position)

class PolicemanAgent(Agent):
    def __init__(self, unique_id, model):
        super().__init__(model)

    def step(self):
        self.move_randomly()

class CommanderAgent(Agent):
    def __init__(self, unique_id, model):
        super().__init__(model)
        self.known_fires = set()

    def report_fire(self, pos):
        self.known_fires.add(pos)

    def get_fires(self):
        return list(self.known_fires)
    
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