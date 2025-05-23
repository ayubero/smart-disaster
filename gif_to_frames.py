from PIL import Image
import os

# Load GIF
gif = Image.open("assets/fire.gif")

# Create output folder
os.makedirs("fire_frames", exist_ok=True)

# Extract frames
for i in range(gif.n_frames):
    gif.seek(i)
    gif.save(f"fire_frames/frame_{i}.png")
