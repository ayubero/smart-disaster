def manhattan_distance(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])

def move_randomly(self):
    possible_steps = self.model.grid.get_neighborhood(self.pos, moore=True, include_center=False)
    self.model.grid.move_agent(self, self.random.choice(possible_steps))

def move_towards(self, target_pos):
    x, y = self.pos
    tx, ty = target_pos
    dx = 1 if tx > x else -1 if tx < x else 0
    dy = 1 if ty > y else -1 if ty < y else 0
    self.model.grid.move_agent(self, (x + dx, y + dy))