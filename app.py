import streamlit as st
import matplotlib.pyplot as plt
import numpy as np
from model import DisasterModel

# Parameters
width = st.slider("Grid Width", 5, 50, 10)
height = st.slider("Grid Height", 5, 50, 10)
num_agents = st.slider("Number of Agents", 1, 50, 10)
steps = st.number_input("Simulation Steps", min_value=1, max_value=1000, value=10)

if st.button("Run Simulation"):
    model = DisasterModel(width, height, num_agents)

    # Run model for N steps
    for _ in range(steps):
        model.step()

    # Display agent positions
    grid_data = np.zeros((height, width))
    for agent in model.agents:
        x, y = agent.pos
        grid_data[y][x] = 1

    st.write("Final Agent Positions")
    fig, ax = plt.subplots()
    ax.imshow(grid_data, cmap="Greens")
    st.pyplot(fig)
