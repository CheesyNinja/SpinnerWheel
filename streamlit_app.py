import streamlit as st
import matplotlib.pyplot as plt
import random

# --- App Config ---
st.set_page_config(page_title="Smart Wheel", layout="centered")
st.title("🎡 Smart Wheel")

# --- Session State Initialization ---
if "options" not in st.session_state:
    # Starting with 3 options at 33.33% each
    st.session_state.options = [
        {"name": "Option 1", "value": 33.33},
        {"name": "Option 2", "value": 33.33},
        {"name": "Option 3", "value": 33.34}
    ]


# --- Helper Functions for "Smart" Logic ---
def balance_percentages(changed_index):
    """Adjusts all other slices proportionally when one is changed."""
    n_options = len(st.session_state.options)
    if n_options <= 1:
        st.session_state.options[0]['value'] = 100.0
        return

    changed_val = st.session_state.options[changed_index]['value']

    # Ensure the user doesn't enter more than 100
    if changed_val > 100:
        st.session_state.options[changed_index]['value'] = 100.0
        changed_val = 100.0

    remaining_total = 100.0 - changed_val
    other_slices_sum = sum(opt['value'] for i, opt in enumerate(st.session_state.options) if i != changed_index)

    for i in range(n_options):
        if i != changed_index:
            if other_slices_sum > 0:
                # Proportional scaling
                new_share = (st.session_state.options[i]['value'] / other_slices_sum) * remaining_total
                st.session_state.options[i]['value'] = round(new_share, 2)
            else:
                # If everything else was 0, distribute remainder equally
                st.session_state.options[i]['value'] = round(remaining_total / (n_options - 1), 2)


def add_option():
    """Adds a new option and balances everyone to be equal."""
    new_count = len(st.session_state.options) + 1
    equal_share = round(100.0 / new_count, 2)

    # Update existing and add new
    for opt in st.session_state.options:
        opt['value'] = equal_share
    st.session_state.options.append({"name": f"Option {new_count}", "value": equal_share})

    # Final tiny adjustment to ensure exactly 100.0
    current_sum = sum(opt['value'] for opt in st.session_state.options)
    st.session_state.options[-1]['value'] += round(100.0 - current_sum, 2)


def remove_option(index):
    if len(st.session_state.options) > 1:
        st.session_state.options.pop(index)
        # Re-balance remaining to equal parts or maintain ratios?
        # Here we re-balance to equal parts for simplicity when deleting
        new_count = len(st.session_state.options)
        for opt in st.session_state.options:
            opt['value'] = round(100.0 / new_count, 2)


# --- UI Layout ---
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("Edit Options")

    for i, opt in enumerate(st.session_state.options):
        inner_col1, inner_col2, inner_col3 = st.columns([2, 2, 1])

        with inner_col1:
            st.session_state.options[i]['name'] = st.text_input(
                f"Name {i}", value=opt['name'], key=f"name_{i}", label_visibility="collapsed"
            )

        with inner_col2:
            # When this value changes, it triggers the balance_percentages logic
            new_val = st.number_input(
                f"Val {i}", value=opt['value'], step=1.0, key=f"val_{i}",
                label_visibility="collapsed", on_change=balance_percentages, args=(i,)
            )
            st.session_state.options[i]['value'] = new_val

        with inner_col3:
            if st.button("X", key=f"del_{i}"):
                remove_option(i)
                st.rerun()

    if st.button("➕ Add Option", use_container_width=True):
        add_option()
        st.rerun()

with col2:
    st.subheader("The Wheel")

    names = [opt['name'] for opt in st.session_state.options]
    values = [opt['value'] for opt in st.session_state.options]

    fig, ax = plt.subplots(figsize=(6, 6))
    ax.pie(values, labels=names, autopct='%1.1f%%', startangle=140, colors=plt.cm.Paired.colors)
    ax.axis('equal')
    st.pyplot(fig)

    if st.button("🎡 SPIN!", type="primary", use_container_width=True):
        winner = random.choices(names, weights=values, k=1)[0]
        st.balloons()
        st.success(f"The winner is: **{winner}**!")

# Footer to show total (should always be ~100)
total = sum(opt['value'] for opt in st.session_state.options)
st.caption(f"Total Percentage: {total:.2f}%")