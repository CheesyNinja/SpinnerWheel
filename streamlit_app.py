import streamlit as st
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import random
import time

# --- INITIALIZATION ---
if 'options_data' not in st.session_state:
    st.session_state.options_data = [
        {"name": "Option 1", "prob": 33.33, "locked": False},
        {"name": "Option 2", "prob": 33.33, "locked": False},
        {"name": "Option 3", "prob": 33.34, "locked": False},
    ]

st.set_page_config(page_title="Proportional Smart Wheel", layout="wide")
st.title("🎡 Proportional Smart Wheel")


# --- HELPER FUNCTIONS ---
def equalize_weights(force_all=False):
    data = st.session_state.options_data
    n = len(data)
    if force_all:
        avg = 100.0 / n
        for item in data:
            item['prob'] = avg
            item['locked'] = False
    else:
        unlocked = [i for i, x in enumerate(data) if not x['locked']]
        if not unlocked: return
        locked_total = sum(x['prob'] for x in data if x['locked'])
        available = max(0, 100.0 - locked_total)
        avg_available = available / len(unlocked)
        for i in unlocked:
            data[i]['prob'] = avg_available


def add_option():
    st.session_state.options_data.append({"name": f"New Option", "prob": 0.0, "locked": False})
    equalize_weights()


# --- SIDEBAR CONTROLS ---
st.sidebar.header("Wheel Settings")

if st.sidebar.button("➕ Add Option"):
    add_option()

if st.sidebar.button("⚖️ Equalize (All)"):
    equalize_weights(force_all=True)

if st.sidebar.button("🧹 Clear/Reset"):
    st.session_state.options_data = [
        {"name": "Option 1", "prob": 50.0, "locked": False},
        {"name": "Option 2", "prob": 50.0, "locked": False},
    ]

# --- MAIN INTERFACE ---
col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("Configure Slices")
    to_delete = None

    # Render dynamic inputs
    for i, item in enumerate(st.session_state.options_data):
        c1, c2, c3, c4 = st.columns([1, 4, 2, 1])

        # Lock toggle
        item['locked'] = c1.checkbox("🔒", value=item['locked'], key=f"lock_{i}")

        # Name input
        item['name'] = c2.text_input(f"Label {i}", value=item['name'], key=f"name_{i}", label_visibility="collapsed")

        # Probability input
        new_val = c3.number_input(f"%", value=float(item['prob']), key=f"prob_{i}", label_visibility="collapsed",
                                  step=1.0)
        item['prob'] = new_val

        # Delete button
        if c4.button("🗑️", key=f"del_{i}"):
            to_delete = i

    if to_delete is not None:
        st.session_state.options_data.pop(to_delete)
        st.rerun()

    if st.button("🔄 Update & Re-balance Wheel"):
        equalize_weights()
        st.rerun()

with col2:
    # --- PLOTTING ---
    labels = [x['name'] for x in st.session_state.options_data]
    sizes = [x['prob'] for x in st.session_state.options_data]

    fig, ax = plt.subplots(figsize=(6, 6))
    # Use a nice color map
    colors = plt.cm.tab10(np.linspace(0, 1, len(labels)))

    wedges, texts, autotexts = ax.pie(
        sizes, labels=labels, autopct='%1.1f%%',
        startangle=90, colors=colors,
        textprops={'weight': 'bold'}
    )
    ax.axis('equal')
    st.pyplot(fig)

    # --- SPIN LOGIC ---
    if st.button("🔥 SPIN THE WHEEL", use_container_width=True):
        with st.spinner("Spinning..."):
            time.sleep(1.5)  # Fake "spinning" delay

            # Weighted random choice
            options = [x['name'] for x in st.session_state.options_data]
            weights = [x['prob'] for x in st.session_state.options_data]

            if sum(weights) > 0:
                winner = random.choices(options, weights=weights, k=1)[0]
                st.balloons()
                st.success(f"### The Winner is: **{winner}**")
            else:
                st.error("Total percentage must be greater than 0!")

# --- CSV EXPORT ---
st.sidebar.markdown("---")
df = pd.DataFrame(st.session_state.options_data)
csv = df.to_csv(index=False).encode('utf-8')
st.sidebar.download_button("📥 Download Configuration", data=csv, file_name="wheel_config.csv", mime="text/csv")