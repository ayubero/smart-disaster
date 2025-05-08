import streamlit as st
import numpy as np
import time
from model import DisasterModel
import plotly.graph_objects as go
from streamlit_plotly_events import plotly_events
import base64
import random

# --- Helper function to load images ---
def encode_image(file_path):
    with open(file_path, "rb") as f:
        return "data:image/png;base64," + base64.b64encode(f.read()).decode()

rescue_icon = encode_image("assets/rescue.png")
shelter_icon = encode_image("assets/shelter.png")
victim_icon = encode_image("assets/victim.png")

# --- UI Parameters ---
width = st.slider('Grid Width', 5, 50, 10)
height = st.slider('Grid Height', 5, 50, 10)
num_agents = st.slider('Number of Agents', 1, 50, 10)
steps = st.number_input('Simulation Steps', min_value=1, max_value=1000, value=10)
delay = st.slider('Delay Between Steps (seconds)', 0.01, 1.0, 0.2)

# Initialize session state for simulation control
if "model" not in st.session_state:
    st.session_state.model = None
if "step" not in st.session_state:
    st.session_state.step = 0
if "running" not in st.session_state:
    st.session_state.running = False

# --- Run Button ---
def start_simulation():
    st.session_state.model = DisasterModel(width, height, num_agents)
    st.session_state.step = 0
    st.session_state.running = True

st.button("Start Simulation", on_click=start_simulation)

# --- Step Display ---
step_placeholder = st.empty()
plot_placeholder = st.empty()

def draw_model(model):
    fig = go.Figure()
    images = []

    for i, agent in enumerate(model.agents):
        if agent.pos is None:
            continue

        x, y = agent.pos
        x_center, y_center = x + 0.5, y + 0.5

        agent_type = type(agent).__name__
        if agent_type == "RescueAgent":
            icon = rescue_icon
        elif agent_type == "VictimAgent":
            icon = victim_icon
        else:
            icon = shelter_icon

        images.append(
            dict(
                source=icon,
                x=x,
                y=y + 1,
                xref="x",
                yref="y",
                sizex=1,
                sizey=1,
                xanchor="left",
                yanchor="top",
                layer="above"
            )
        )

        # One trace per agent
        fig.add_trace(go.Scatter(
            x=[x_center], y=[y_center],
            mode='markers',
            marker=dict(size=20, opacity=0),
            hovertext=[f"{agent_type} #{i}"],
            hoverinfo="text",
            showlegend=False
        ))

    fig.update_layout(
        images=images,
        xaxis=dict(range=[0, width], dtick=1),
        yaxis=dict(range=[-0.1, height], dtick=1, autorange=False),
        width=600,
        height=600,
        margin=dict(l=0, r=0, t=30, b=0),
        dragmode=False,
        hovermode="closest"  # <- Ensure only the nearest point is hovered
    )

    return fig

# --- Run Simulation Loop ---
if st.session_state.running:
    # Step once and render
    model = st.session_state.model
    model.step()
    st.session_state.step += 1

    step_placeholder.subheader(f"Step {st.session_state.step}")

    fig = draw_model(model)
    clicked = plotly_events(
        fig,
        click_event=True,
        hover_event=False,
        key="plot",
        override_height=600
    )
    #plot_placeholder.plotly_chart(fig, use_container_width=True)

    # Check for click interaction
    if clicked:
        x_click = int(clicked[0]['x'])
        y_click = int(clicked[0]['y'])
        st.info(f"Clicked at ({x_click}, {y_click})")

        for agent in model.agents:
            if agent.pos == (x_click, y_click):
                agent.perform_action()
                st.success(f"Action triggered for {type(agent).__name__} at {agent.pos}")
                break

    # Auto-advance with delay
    if st.session_state.step < steps:
        time.sleep(delay)
        st.rerun()
    else:
        st.session_state.running = False
        st.success("Simulation complete!")
