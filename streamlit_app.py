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
def balance_percentages(changed_index):
    """Adjusts other slices when one is manually changed via number input."""
    n_options = len(st.session_state.options)
    if n_options <= 1:
        st.session_state.options[0]['value'] = 100.0
        return

    changed_val = st.session_state.options[changed_index]['value']

    # Cap at 100
    if changed_val > 100:
        st.session_state.options[changed_index]['value'] = 100.0
        changed_val = 100.0

    remaining_total = 100.0 - changed_val
    other_slices_sum = sum(opt['value'] for i, opt in enumerate(st.session_state.options) if i != changed_index)

    for i in range(n_options):
        if i != changed_index:
            if other_slices_sum > 0:
                new_share = (st.session_state.options[i]['value'] / other_slices_sum) * remaining_total
                st.session_state.options[i]['value'] = round(new_share, 2)
            else:
                st.session_state.options[i]['value'] = round(remaining_total / (n_options - 1), 2)


def add_option_balanced():
    """This is the fix: Forces ALL options to be equal when a new one is added."""
    new_count = len(st.session_state.options) + 1
    new_equal_value = round(100.0 / new_count, 2)

    # Update every existing option to the new equal share
    for opt in st.session_state.options:
        opt['value'] = new_equal_value

    # Add the new option at that same share
    st.session_state.options.append({
        "name": f"Option {new_count}",
        "value": new_equal_value
    })

    # Clean up math jitter to ensure total is exactly 100.0
    current_total = sum(opt['value'] for opt in st.session_state.options)
    difference = round(100.0 - current_total, 2)
    st.session_state.options[-1]['value'] += difference


def remove_option(index):
    if len(st.session_state.options) > 1:
        st.session_state.options.pop(index)
        # Re-balance remaining to be equal after a deletion
        new_count = len(st.session_state.options)
        new_val = round(100.0 / new_count, 2)
        for opt in st.session_state.options:
            opt['value'] = new_val
        # Final adjustment for 100%
        st.session_state.options[-1]['value'] += round(100.0 - (new_val * new_count), 2)


# --- UI Layout ---
col1, col2 = st.columns([1, 1.2])

with col1:
    st.subheader("Edit Options")

    # We use a copy of the list to iterate to avoid index errors during deletion
    for i, opt in enumerate(st.session_state.options):
        # Unique keys are vital for Streamlit to track which input is which
        c1, c2, c3 = st.columns([2, 2, 0.5])

        with c1:
            st.session_state.options[i]['name'] = st.text_input(
                f"n_{i}", value=opt['name'], key=f"input_name_{i}", label_visibility="collapsed"
            )

        with c2:
            # Use on_change to trigger the "Smart" balancing when manually editing a number
            st.session_state.options[i]['value'] = st.number_input(
                f"v_{i}", value=opt['value'], key=f"input_val_{i}",
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

    names = [opt['name'] for opt in st.session_state.options]
    values = [opt['value'] for opt in st.session_state.options]

    if sum(values) > 0:
        fig, ax = plt.subplots(figsize=(6, 6))
        # Set facecolor to match dark theme if desired, or keep white for contrast
        fig.patch.set_facecolor('#0E1117')
        ax.set_facecolor('#0E1117')

        wedges, texts, autotexts = ax.pie(
            values, labels=names, autopct='%1.1f%%',
            startangle=140, colors=plt.cm.Pastel1.colors,
            textprops={'color': "w"}
        )
        ax.axis('equal')
        st.pyplot(fig)
    else:
        st.warning("Total percentage must be greater than 0 to draw the wheel.")

    if st.button("🎡 SPIN!", type="primary", use_container_width=True):
        winner = random.choices(names, weights=values, k=1)[0]
        st.balloons()
        st.header(f"Result: {winner}")

# Verification Footer
total_perc = sum(opt['value'] for opt in st.session_state.options)
st.divider()
st.info(f"Current Total: {total_perc:.2f}%")