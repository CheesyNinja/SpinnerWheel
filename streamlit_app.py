import streamlit as st
import matplotlib.pyplot as plt
import random

# --- App Config ---
st.set_page_config(page_title="Smart Wheel", layout="wide")
st.title("🎡 Smart Wheel Web")

# --- Initialize Session State ---
if 'options' not in st.session_state:
    st.session_state.options = [
        {"name": "Option 1", "percent": 33.33},
        {"name": "Option 2", "percent": 33.33},
        {"name": "Option 3", "percent": 33.34}
    ]


def redistribute_percentages(changed_index, new_val):
    """ The 'Smart' Logic: Adjusts all other slices to maintain 100% total """
    others = [i for i in range(len(st.session_state.options)) if i != changed_index]
    if not others:
        st.session_state.options[changed_index]['percent'] = 100.0
        return

    remaining_needed = 100.0 - new_val
    current_others_sum = sum(st.session_state.options[i]['percent'] for i in others)

    for i in others:
        if current_others_sum > 0:
            # Scale proportionally
            new_share = (st.session_state.options[i]['percent'] / current_others_sum) * remaining_needed
            st.session_state.options[i]['percent'] = round(new_share, 2)
        else:
            # Fallback if others were zero
            st.session_state.options[i]['percent'] = round(remaining_needed / len(others), 2)

    # Final tiny adjustment to handle rounding errors and ensure exactly 100.0
    st.session_state.options[changed_index]['percent'] = new_val
    total = sum(opt['percent'] for opt in st.session_state.options)
    if total != 100.0:
        st.session_state.options[others[0]]['percent'] += round(100.0 - total, 2)


# --- Sidebar Controls ---
with st.sidebar:
    st.header("Controls")
    if st.button("➕ Add Option"):
        num_options = len(st.session_state.options) + 1
        new_equal_share = round(100.0 / num_options, 2)

        # Add the new one at the equal share
        st.session_state.options.append({"name": f"Option {num_options}", "percent": new_equal_share})

        # Force a redistribution starting from the new item to shrink the others
        redistribute_percentages(len(st.session_state.options) - 1, new_equal_share)

    if st.button("⚖️ Equalize All"):
        eq_share = round(100.0 / len(st.session_state.options), 2)
        for i in range(len(st.session_state.options)):
            st.session_state.options[i]['percent'] = eq_share
        # Fix rounding
        st.session_state.options[-1]['percent'] += round(100.0 - (eq_share * len(st.session_state.options)), 2)

# --- Main Interface ---
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("Edit Slices")
    to_delete = None

    for idx, opt in enumerate(st.session_state.options):
        c1, c2, c3 = st.columns([3, 2, 1])
        with c1:
            new_name = st.text_input(f"Name {idx}", value=opt['name'], label_visibility="collapsed", key=f"n{idx}")
            st.session_state.options[idx]['name'] = new_name
        with c2:
            # The key logic happens on_change
            new_p = st.number_input(f"%", value=opt['percent'], step=1.0, min_value=0.0, max_value=100.0,
                                    label_visibility="collapsed", key=f"p{idx}")
            if new_p != opt['percent']:
                redistribute_percentages(idx, new_p)
        with c3:
            if st.button("🗑️", key=f"del{idx}"):
                to_delete = idx

    if to_delete is not None:
        st.session_state.options.pop(to_delete)
        if st.session_state.options:
            redistribute_percentages(0, st.session_state.options[0]['percent'])
        st.rerun()

    # Visual Total Check
    current_total = sum(opt['percent'] for opt in st.session_state.options)
    st.metric("Total Percentage", f"{current_total:.2f}%")

with col2:
    st.subheader("The Wheel")
    labels = [opt['name'] for opt in st.session_state.options]
    sizes = [opt['percent'] for opt in st.session_state.options]

    if sizes:
        fig, ax = plt.subplots(figsize=(6, 6))
        # Use a consistent color palette
        colors = plt.cm.Paired(range(len(labels)))
        ax.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=140, colors=colors)
        ax.axis('equal')
        st.pyplot(fig)

        if st.button("🔥 SPIN WHEEL", use_container_width=True):
            winner = random.choices(labels, weights=sizes, k=1)[0]
            st.balloons()
            st.success(f"The winner is: **{winner}**!")
    else:
        st.info("Add some options to see the wheel!")