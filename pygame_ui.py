import pygame
from model import DisasterModel
import sys
import glob



# Settings
WIDTH, HEIGHT = 1000, 1000
GRID_WIDTH, GRID_HEIGHT = 20, 20
CELL_SIZE = WIDTH // GRID_WIDTH
FPS = 30
INTERP_FRAMES = 5  # Frames between each model step

# Colors
BG_COLOR = (30, 30, 30)
GRID_COLOR = (70, 70, 70)

# Load fire animation frames
fire_frames = []
for filename in sorted(glob.glob('assets/fire_frames/frame_*.png')):
    img = pygame.image.load(filename)
    img = pygame.transform.scale(img, (CELL_SIZE, CELL_SIZE))
    fire_frames.append(img)

# Images
tree_image = pygame.image.load('assets/forest.png')
tree_image = pygame.transform.scale(tree_image, (CELL_SIZE, CELL_SIZE))
prison_image = pygame.image.load('assets/prison.png')
prison_image = pygame.transform.scale(prison_image, (CELL_SIZE, CELL_SIZE))
firestation_image = pygame.image.load('assets/firestation.png')
firestation_image = pygame.transform.scale(firestation_image, (CELL_SIZE, CELL_SIZE))
arsonist_image = pygame.image.load('assets/thief.png')
arsonist_image = pygame.transform.scale(arsonist_image, (CELL_SIZE, CELL_SIZE))
firefighter_image = pygame.image.load('assets/firefighter.png')
firefighter_image = pygame.transform.scale(firefighter_image, (CELL_SIZE, CELL_SIZE))
policeman_image = pygame.image.load('assets/policeman.png')
policeman_image = pygame.transform.scale(policeman_image, (CELL_SIZE, CELL_SIZE))
citizen_image = pygame.image.load('assets/citizen.png')
citizen_image = pygame.transform.scale(citizen_image, (CELL_SIZE, CELL_SIZE))

def interpolate(a, b, t):
    return a + (b - a) * t

def draw_grid(screen):
    for x in range(0, WIDTH, CELL_SIZE):
        pygame.draw.line(screen, GRID_COLOR, (x, 0), (x, HEIGHT))
    for y in range(0, HEIGHT, CELL_SIZE):
        pygame.draw.line(screen, GRID_COLOR, (0, y), (WIDTH, y))

def draw_agents(screen, model, frame_index, tween_factor):
    for contents, (x, y) in model.grid.coord_iter():
        for agent in contents:
            # Interpolated position
            x, y = agent.pos
            if hasattr(agent, 'prev_pos') and agent.prev_pos is not None:
                x_prev, y_prev = agent.prev_pos
                x_draw = interpolate(x_prev, x, tween_factor)
                y_draw = interpolate(y_prev, y, tween_factor)
            else:
                x_draw, y_draw = x, y

            screen_x = x_draw * CELL_SIZE
            screen_y = y_draw * CELL_SIZE
            pos = (int(screen_x + CELL_SIZE // 2), int(screen_y + CELL_SIZE // 2))

            # Draw agents
            if agent.__class__.__name__ == 'TreeAgent':
                screen.blit(tree_image, (screen_x, screen_y))
                if agent.on_fire:
                    frame = fire_frames[frame_index]
                    screen.blit(frame, (screen_x, screen_y))
            elif agent.__class__.__name__ == 'PrisonAgent':
                screen.blit(prison_image, (screen_x, screen_y))
            elif agent.__class__.__name__ == 'FirestationAgent':
                screen.blit(firestation_image, (screen_x, screen_y))
            elif agent.__class__.__name__ == 'CitizenAgent':
                screen.blit(citizen_image, (screen_x, screen_y))
            elif agent.__class__.__name__ == 'ArsonistAgent':
                screen.blit(arsonist_image, (screen_x, screen_y))
            elif agent.__class__.__name__ == 'FirefighterAgent':
                screen.blit(firefighter_image, (screen_x, screen_y))
            elif agent.__class__.__name__ == 'PolicemanAgent':
                screen.blit(policeman_image, (screen_x, screen_y))

def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption('Disaster Simulation - Pygame')
    clock = pygame.time.Clock()

    model = DisasterModel(GRID_WIDTH, GRID_HEIGHT)

    frame_index = 0
    interp_frame = 0

    running = True
    while running:
        screen.fill(BG_COLOR)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        tween_factor = interp_frame / INTERP_FRAMES
        draw_agents(screen, model, frame_index, tween_factor)

        pygame.display.flip()
        clock.tick(FPS)
        interp_frame += 1

        if interp_frame >= INTERP_FRAMES:
            interp_frame = 0

            # Set prev_pos before moving
            for agent in model.agents:
                if hasattr(agent, 'pos'):
                    agent.prev_pos = agent.pos

            model.step()

        frame_index = (frame_index + 1) % len(fire_frames)

    pygame.quit()
    sys.exit()

if __name__ == '__main__':
    main()
