import streamlit as st
import matplotlib.pyplot as plt
import numpy as np
import random
import time

# --- INITIALIZATION ---
if 'options_data' not in st.session_state:
    st.session_state.options_data = [
        {"name": "Option 1", "prob": 33.33, "locked": False},
        {"name": "Option 2", "prob": 33.33, "locked": False},
        {"name": "Option 3", "prob": 33.34, "locked": False},
    ]

st.set_page_config(page_title="Smart Proportional Wheel", layout="wide")


# --- CORE MATH LOGIC ---

def rebalance_proportionally(target_idx=None, new_val=None, adding_new=False):
    """
    Adjusts all unlocked slices so they maintain their relative ratios
    while fitting into the available space.
    """
    data = st.session_state.options_data

    if adding_new:
        # 1. Calculate the 'Fair Share' for the new count
        new_count = len(data)
        target_share = 100.0 / new_count

        # 2. Identify existing unlocked slices (excluding the brand new one at the end)
        unlocked_indices = [i for i, x in enumerate(data[:-1]) if not x['locked']]
        locked_total = sum(x['prob'] for i, x in enumerate(data[:-1]) if x['locked'])

        # 3. How much room is left after the new slice and locked slices?
        remaining_space = 100.0 - target_share - locked_total

        # 4. Total 'weight' of currently unlocked slices
        current_unlocked_sum = sum(data[i]['prob'] for i in unlocked_indices)

        # 5. Scale them
        if current_unlocked_sum > 0:
            multiplier = remaining_space / current_unlocked_sum
            for i in unlocked_indices:
                data[i]['prob'] = round(data[i]['prob'] * multiplier, 2)

        # 6. Set the new slice to its fair share
        data[-1]['prob'] = round(target_share, 2)

    elif target_idx is not None:
        # Logic for when a user manually changes a specific number
        unlocked_others = [i for i, x in enumerate(data) if not x['locked'] and i != target_idx]
        locked_total = sum(x['prob'] for i, x in enumerate(data) if x['locked'] or i == target_idx)

        remaining_space = 100.0 - locked_total
        current_unlocked_sum = sum(data[i]['prob'] for i in unlocked_others)

        if unlocked_others and current_unlocked_sum > 0:
            multiplier = remaining_space / current_unlocked_sum
            for i in unlocked_others:
                data[i]['prob'] = round(data[i]['prob'] * multiplier, 2)
        elif unlocked_others:
            # If others were 0, split remaining space equally
            for i in unlocked_others:
                data[i]['prob'] = round(remaining_space / len(unlocked_others), 2)


# --- UI LAYOUT ---
col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("Settings")

    # Add Option Button
    if st.button("➕ Add Option (Auto-Balance)"):
        st.session_state.options_data.append(
            {"name": f"Option {len(st.session_state.options_data) + 1}", "prob": 0.0, "locked": False})
        rebalance_proportionally(adding_new=True)
        st.rerun()

    # Inputs for slices
    for i, item in enumerate(st.session_state.options_data):
        c1, c2, c3 = st.columns([1, 4, 2])
        item['locked'] = c1.checkbox("🔒", value=item['locked'], key=f"lock_{i}")
        item['name'] = c2.text_input(f"n_{i}", value=item['name'], key=f"name_{i}", label_visibility="collapsed")

        # If user changes probability manually
        prev_val = item['prob']
        new_val = c3.number_input(f"%", value=float(item['prob']), key=f"p_{i}", label_visibility="collapsed")

        if new_val != prev_val:
            st.session_state.options_data[i]['prob'] = new_val
            rebalance_proportionally(target_idx=i)
            st.rerun()

with col2:
    # --- CHARTING ---
    labels = [x['name'] for x in st.session_state.options_data]
    sizes = [x['prob'] for x in st.session_state.options_data]

    fig, ax = plt.subplots()
    ax.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90, colors=plt.cm.Pastel1.colors)
    ax.axis('equal')
    st.pyplot(fig)

    if st.button("SPIN", use_container_width=True):
        winner = random.choices(labels, weights=sizes, k=1)[0]
        st.balloons()
        st.success(f"Winner: {winner}")