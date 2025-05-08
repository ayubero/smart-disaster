import streamlit as st
import numpy as np
import time
from model import DisasterModel
import plotly.graph_objects as go
from streamlit_plotly_events import plotly_events
import base64

# --- Helper function to load images ---
def encode_image(file_path):
    with open(file_path, "rb") as f:
        return "data:image/png;base64," + base64.b64encode(f.read()).decode()

rescue_icon = encode_image("assets/rescue.png")
shelter_icon = encode_image("assets/shelter.png")
victim_icon = encode_image("assets/victim.png")

# --- UI Parameters ---
st.set_page_config(layout="centered")
st.title("Disaster Simulation")

width = st.slider('Grid Width', 5, 50, 10)
height = st.slider('Grid Height', 5, 50, 10)
num_agents = st.slider('Number of Agents', 1, 50, 10)
steps = st.number_input('Simulation Steps', min_value=1, max_value=1000, value=10)
delay = st.slider('Delay Between Steps (seconds)', 0.01, 1.0, 0.2)

# Initialize session state
if "model" not in st.session_state:
    st.session_state.model = None
if "step" not in st.session_state:
    st.session_state.step = 0
if "running" not in st.session_state:
    st.session_state.running = False
if "clicked_agent" not in st.session_state:
    st.session_state.clicked_agent = None

# --- Run Button ---
def start_simulation():
    st.session_state.model = DisasterModel(width, height, num_agents)
    st.session_state.step = 0
    st.session_state.running = True

st.button("Start Simulation", on_click=start_simulation)

# --- Drawing function ---
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

        # Invisible marker to detect click
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

# --- Simulation Display ---
step_placeholder = st.empty()

if st.session_state.model:
    step_placeholder.subheader(f"Step {st.session_state.step}")

    model = st.session_state.model
    fig = draw_model(model)
    clicked = plotly_events(
        fig,
        click_event=True,
        hover_event=False,
        key="plot",
        override_height=600
    )

    if clicked:
        x_click = int(clicked[0]['x'])
        y_click = int(clicked[0]['y'])
        st.session_state.clicked_agent = (x_click, y_click)
    else:
        st.session_state.clicked_agent = None

    # Handle click
    if st.session_state.clicked_agent:
        x, y = st.session_state.clicked_agent
        for agent in model.agents:
            if agent.pos == (x, y):
                #agent.perform_action()
                st.success(f"Action triggered for {type(agent).__name__} at {agent.pos}")
                break

    # Step forward if running
    if st.session_state.running:
        if st.session_state.step < steps:
            time.sleep(delay)
            model.step()
            st.session_state.step += 1
            st.rerun()
        else:
            st.session_state.running = False
            st.success("Simulation complete!")
