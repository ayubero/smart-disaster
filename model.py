from mesa import Model
from mesa.space import MultiGrid
from agents import RescueAgent, EvacuationAgent, ResourceAgent, ScoutAgent, VictimAgent, ShelterAgent, CommandAgent

class DisasterModel(Model):
    def __init__(self, width, height, num_rescuers=3, num_evacuators=2, num_resources=2, num_scouts=2, num_victims=2, num_shelters=2):
        super().__init__()
        self.grid = MultiGrid(width, height, torus=False)
        self.global_map = {}

        # Create agents
        agent_id = 0
        for _ in range(num_rescuers):
            agent = RescueAgent(agent_id, self)
            self.place_agent(agent)
            agent_id += 1

        for _ in range(num_evacuators):
            agent = EvacuationAgent(agent_id, self)
            self.place_agent(agent)
            agent_id += 1

        for _ in range(num_resources):
            agent = ResourceAgent(agent_id, self)
            self.place_agent(agent)
            agent_id += 1

        for _ in range(num_scouts):
            agent = ScoutAgent(agent_id, self)
            self.place_agent(agent)
            agent_id += 1

        for _ in range(num_victims):
            agent = VictimAgent(agent_id, self)
            self.place_agent(agent)
            agent_id += 1

        for _ in range(num_shelters):
            agent = ShelterAgent(agent_id, self)
            self.place_agent(agent)
            agent_id += 1

        command = CommandAgent(agent_id, self)
        self.place_agent(command)
    
    def place_agent(self, agent):
        x = self.random.randrange(self.grid.width)
        y = self.random.randrange(self.grid.height)
        self.grid.place_agent(agent, (x, y))
        self.agents.add(agent)

    def step(self):
        self.agents.shuffle_do('step')
