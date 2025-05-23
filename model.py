from mesa import Model
from mesa.space import MultiGrid
from agents import CommanderAgent, TreeAgent, PrisonAgent, FirestationAgent, CitizenAgent, ArsonistAgent, FirefighterAgent, PolicemanAgent

class DisasterModel(Model):
    def __init__(self, width, height, num_trees=20, num_prison=1, num_firestations=1, num_citizens=5, num_arsonists=1, num_firefighters=3, num_policemen=2):
        super().__init__()
        self.grid = MultiGrid(width, height, torus=False)
        self.global_map = {}
        self.firefighter_presence = {} # key: fire_position, value: set of firefighter IDs
        self.num_firefighters = num_firefighters

        # Create agents
        agent_id = 0
        firestation_positions = []

        for _ in range(num_trees):
            agent = TreeAgent(agent_id, self)
            self.place_agent_without_colliding(agent)
            agent_id += 1

        for _ in range(num_prison):
            agent = PrisonAgent(agent_id, self)
            self.place_agent_without_colliding(agent)
            agent_id += 1

        for _ in range(num_firestations):
            agent = FirestationAgent(agent_id, self)
            position = self.place_agent_without_colliding(agent)
            agent_id += 1
            firestation_positions.append(position)

        for _ in range(num_citizens):
            agent = CitizenAgent(agent_id, self)
            self.place_agent(agent)
            agent_id += 1

        for _ in range(num_arsonists):
            agent = ArsonistAgent(agent_id, self)
            self.place_agent(agent)
            agent_id += 1

        for _ in range(num_firefighters):
            position = firestation_positions[0] if len(firestation_positions) > 0 else None
            agent = FirefighterAgent(agent_id, self, position)
            self.place_agent(agent, position)
            agent_id += 1

        for _ in range(num_policemen):
            agent = PolicemanAgent(agent_id, self)
            self.place_agent(agent)
            agent_id += 1

        commander = CommanderAgent(agent_id, self)
        self.place_agent(commander)
        self.commander = commander
    
    def place_agent(self, agent, position=None):
        if position is None:
            x = self.random.randrange(self.grid.width)
            y = self.random.randrange(self.grid.height)
        else:
            x, y = position
        self.grid.place_agent(agent, (x, y))
        self.agents.add(agent)
        return (x, y)

    def place_agent_without_colliding(self, agent):
        x = self.random.randrange(self.grid.width)
        y = self.random.randrange(self.grid.height)
        while self.grid.get_cell_list_contents((x, y)):
            # Avoid placing agent on an already occupied cell
            x = self.random.randrange(self.grid.width)
            y = self.random.randrange(self.grid.height)
        self.grid.place_agent(agent, (x, y))
        self.agents.add(agent)
        return (x, y)

    def step(self):
        self.agents.shuffle_do('step')

        # After all agents have stepped, the commander tallies the result
        fire_list = self.commander.get_fires()
        if fire_list:
            winning_fire = self.commander.tally_votes()
            if winning_fire:
                for agent in self.agents:
                    if isinstance(agent, FirefighterAgent): # and agent.goal is None
                        agent.goal = winning_fire
                    agent._vote = None # Clear vote for next round

    def collect_firefighter_votes(self, fire_list):
        votes = []
        for _ in range(self.num_firefighters):
            votes.append(self.random.choice(fire_list))
        return votes
