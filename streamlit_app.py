import streamlit as st
import matplotlib.pyplot as plt
import random

# --- App Config ---
st.set_page_config(page_title="Smart Wheel", layout="centered")
st.title("🎡 Smart Wheel")

# --- Session State Initialization ---
if "options" not in st.session_state:
    st.session_state.options = [
        {"name": "Option 1", "value": 33.33},
        {"name": "Option 2", "value": 33.33},
        {"name": "Option 3", "value": 33.34}
    ]


# --- Helper Functions ---
def sync_state():
    """Forces the individual widget keys to match the options list."""
    for i, opt in enumerate(st.session_state.options):
        st.session_state[f"input_val_{i}"] = opt['value']
        st.session_state[f"input_name_{i}"] = opt['name']


def balance_percentages(changed_index):
    """Adjusts other slices when one is manually changed."""
    n_options = len(st.session_state.options)
    # Get the value directly from the widget that just changed
    changed_val = st.session_state[f"input_val_{changed_index}"]
    st.session_state.options[changed_index]['value'] = changed_val

    remaining_total = 100.0 - changed_val
    other_slices_sum = sum(opt['value'] for i, opt in enumerate(st.session_state.options) if i != changed_index)

    for i in range(n_options):
        if i != changed_index:
            if other_slices_sum > 0:
                new_share = (st.session_state.options[i]['value'] / other_slices_sum) * remaining_total
                st.session_state.options[i]['value'] = round(new_share, 2)
            else:
                st.session_state.options[i]['value'] = round(remaining_total / (n_options - 1), 2)

    sync_state()


def add_option_balanced():
    """Forces all options to be equal and updates the UI widgets."""
    new_count = len(st.session_state.options) + 1
    new_equal_value = round(100.0 / new_count, 2)

    # Update existing
    for opt in st.session_state.options:
        opt['value'] = new_equal_value

    # Add new
    st.session_state.options.append({
        "name": f"Option {new_count}",
        "value": new_equal_value
    })

    # Fix rounding to hit exactly 100.0
    current_total = sum(opt['value'] for opt in st.session_state.options)
    st.session_state.options[-1]['value'] += round(100.0 - current_total, 2)

    sync_state()


def remove_option(index):
    if len(st.session_state.options) > 1:
        st.session_state.options.pop(index)
        new_count = len(st.session_state.options)
        new_val = round(100.0 / new_count, 2)
        for opt in st.session_state.options:
            opt['value'] = new_val
        st.session_state.options[-1]['value'] += round(100.0 - (new_val * new_count), 2)
        sync_state()


# --- UI Layout ---
col1, col2 = st.columns([1, 1.2])

with col1:
    st.subheader("Edit Options")

    for i, opt in enumerate(st.session_state.options):
        c1, c2, c3 = st.columns([2, 2, 0.5])

        with c1:
            # We bind the value to the key in session state
            st.text_input(
                f"n_{i}", key=f"input_name_{i}", label_visibility="collapsed",
                value=opt['name']
            )

        with c2:
            # The value is now controlled by the key assigned in sync_state()
            st.number_input(
                f"v_{i}", key=f"input_val_{i}",
                label_visibility="collapsed", on_change=balance_percentages, args=(i,)
            )

        with c3:
            if st.button("X", key=f"btn_{i}"):
                remove_option(i)
                st.rerun()

    if st.button("➕ Add Option", use_container_width=True):
        add_option_balanced()
        st.rerun()

with col2:
    st.subheader("The Wheel")

    # Ensure current list reflects what is in the text boxes
    names = [st.session_state[f"input_name_{i}"] for i in range(len(st.session_state.options))]
    values = [st.session_state[f"input_val_{i}"] for i in range(len(st.session_state.options))]

    if sum(values) > 0:
        fig, ax = plt.subplots(figsize=(6, 6))
        fig.patch.set_facecolor('#0E1117')
        ax.set_facecolor('#0E1117')

        ax.pie(values, labels=names, autopct='%1.1f%%', startangle=140,
               colors=plt.cm.Pastel1.colors, textprops={'color': "w"})
        ax.axis('equal')
        st.pyplot(fig)

    if st.button("🎡 SPIN!", type="primary", use_container_width=True):
        winner = random.choices(names, weights=values, k=1)[0]
        st.balloons()
        st.header(f"Result: {winner}")

# Verification
total_perc = sum(st.session_state[f"input_val_{i}"] for i in range(len(st.session_state.options)))
st.divider()
st.info(f"Current Total: {total_perc:.2f}%")