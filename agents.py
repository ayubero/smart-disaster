from mesa import Agent

class RescueAgent(Agent):
    def __init__(self, unique_id, model):
        super().__init__(model)
        self.rescuing = False

    def step(self):
        # Find nearby victims
        #nearby_victims = [a for a in self.model.grid.get_cell_list_contents([self.pos])
        #                  if isinstance(a, VictimAgent)]
        neighbors = self.model.grid.get_neighbors(
            self.pos,
            moore = True, # Moore neighborhood (8 surrounding cells)
            radius = 10,
            include_center = False # Not include the agent's own cell
        )
        nearby_victims = [a for a in neighbors if isinstance(a, VictimAgent)]
        print('Number of nearby victims:', len(nearby_victims))

        if nearby_victims:
            print('I found a victim!')
            # Rescue victim
            victim = nearby_victims[0]
            self.model.grid.remove_agent(victim)
            self.rescuing = True
        else:
            # Search for victims
            self.move_randomly()

    def move_randomly(self):
        possible_steps = self.model.grid.get_neighborhood(self.pos, moore=True, include_center=False)
        new_position = self.random.choice(possible_steps)
        self.model.grid.move_agent(self, new_position)


class EvacuationAgent(Agent):
    def __init__(self, unique_id, model):
        super().__init__(model)
        self.carrying = None

    def step(self):
        if self.carrying:
            # Move toward nearest shelter
            shelter = self.model.find_nearest(self.pos, ShelterAgent)
            if shelter:
                self.move_towards(shelter.pos)
                if self.pos == shelter.pos:
                    self.carrying = None  # Drop civilian
        else:
            # Pick up nearby civilian
            civilians = [a for a in self.model.grid.get_cell_list_contents([self.pos])
                         if isinstance(a, CivilianAgent)]
            if civilians:
                self.carrying = civilians[0]
                self.model.grid.remove_agent(self.carrying)
            else:
                self.move_randomly()

    def move_randomly(self):
        possible_steps = self.model.grid.get_neighborhood(self.pos, moore=True, include_center=False)
        new_position = self.random.choice(possible_steps)
        self.model.grid.move_agent(self, new_position)

    def move_towards(self, target_pos):
        x, y = self.pos
        tx, ty = target_pos
        dx = 1 if tx > x else -1 if tx < x else 0
        dy = 1 if ty > y else -1 if ty < y else 0
        self.model.grid.move_agent(self, (x + dx, y + dy))


class ResourceAgent(Agent):
    def __init__(self, unique_id, model):
        super().__init__(model)
        self.supplies = 1

    def step(self):
        if self.supplies == 0:
            return

        # Find agent to resupply
        for neighbor in self.model.grid.get_neighbors(self.pos, moore=True, include_center=False):
            if isinstance(neighbor, (RescueAgent, EvacuationAgent)):
                # Resupply and exit
                self.supplies = 0
                return

        self.move_randomly()

    def move_randomly(self):
        possible_steps = self.model.grid.get_neighborhood(self.pos, moore=True, include_center=False)
        new_position = self.random.choice(possible_steps)
        self.model.grid.move_agent(self, new_position)


class ScoutAgent(Agent):
    def __init__(self, unique_id, model):
        super().__init__(model)
        self.explored = set()

    def step(self):
        self.explored.add(self.pos)
        self.model.global_map[self.pos] = "explored"
        self.move_randomly()

    def move_randomly(self):
        possible_steps = self.model.grid.get_neighborhood(self.pos, moore=True, include_center=False)
        unexplored = [pos for pos in possible_steps if pos not in self.explored]

        if unexplored:
            self.model.grid.move_agent(self, self.random.choice(unexplored))
        else:
            self.model.grid.move_agent(self, self.random.choice(possible_steps))


class CommandAgent(Agent):
    def __init__(self, unique_id, model):
        super().__init__(model)

    def step(self):
        victim_count = sum(isinstance(a, VictimAgent) for a in self.model.agents)
        print(f"[Command] Victims remaining: {victim_count}")

class VictimAgent(Agent):
    def __init__(self, unique_id, model):
        super().__init__(model)

    def step(self):
        pass

class ShelterAgent(Agent):
    def __init__(self, unique_id, model):
        super().__init__(model)

    def step(self):
        pass

class CivilianAgent(Agent):
    def __init__(self, unique_id, model):
        super().__init__(model)

    def step(self):
        pass