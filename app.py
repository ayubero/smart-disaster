import streamlit as st
import matplotlib.pyplot as plt
import numpy as np
import time
from model import DisasterModel

# UI Parameters
width = st.slider('Grid Width', 5, 50, 10)
height = st.slider('Grid Height', 5, 50, 10)
num_agents = st.slider('Number of Agents', 1, 50, 10)
steps = st.number_input('Simulation Steps', min_value=1, max_value=1000, value=10)
delay = st.slider('Delay Between Steps (seconds)', 0.01, 1.0, 0.2)

type_colors = {
    'RescueAgent': [1, 0, 0], # Red
    'EvacuationAgent': [0, 1, 0], # Green
    'ResourceAgent': [0, 0, 1], # Blue
    'ScoutAgent': [1, 1, 0], # Yellow
    'CommandAgent': [1, 0, 1], # Magenta
    'VictimAgent': [0.8, 0.4, 0], # Orange
    'CivilianAgent': [0.5, 0.5, 0.5], # Gray
    'ShelterAgent': [0, 1, 1], # Cyan
}

# Run button
if st.button('Run Simulation'):
    model = DisasterModel(width, height, num_agents)

    # Create a placeholder for the plot
    plot_placeholder = st.empty()

    for step in range(steps):
        model.step()

        # Create a grid to visualize
        grid_data = np.ones((height, width, 3))
        for agent in model.agents:
            if agent.pos is not None:
                x, y = agent.pos
                agent_type = type(agent).__name__
                color = type_colors.get(agent_type, [0, 0, 0])  # Default to black if not found
                grid_data[y][x] = color

        # Plot and update placeholder
        fig, ax = plt.subplots()
        ax.imshow(grid_data)
        ax.set_title(f'Step {step + 1}')
        plot_placeholder.pyplot(fig)

        time.sleep(delay)

    st.success('Simulation complete!')
