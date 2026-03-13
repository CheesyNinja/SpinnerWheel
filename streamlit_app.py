import streamlit as st
import matplotlib.pyplot as plt
import numpy as np
import random

st.set_page_config(page_title="Smart Wheel", layout="centered")

st.title("🎡 Proportional Smart Wheel")

# --- INITIAL STATE ---
if 'options' not in st.session_state:
    st.session_state.options = ["Option 1", "Option 2", "Option 3"]
    st.session_state.percentages = [33.33, 33.33, 33.34]
    st.session_state.locks = [False, False, False]
    st.session_state.winner = None


def sync_data():
    """Ensures percentages always total 100."""
    total = sum(st.session_state.percentages)
    if total != 100:
        # Simple normalization for small floating point errors
        st.session_state.percentages = [p * (100 / total) for p in st.session_state.percentages]


# --- SIDEBAR CONTROLS ---
st.sidebar.header("Wheel Settings")

if st.sidebar.button("➕ Add Option"):
    unlocked_count = sum(1 for L in st.session_state.locks if not L) + 1
    locked_sum = sum(p for p, L in zip(st.session_state.percentages, st.session_state.locks) if L)
    available = 100 - locked_sum
    fair_share = available / unlocked_count

    # Shrink others to make room
    new_percentages = []
    for p, L in zip(st.session_state.percentages, st.session_state.locks):
        if not L:
            new_percentages.append(p - (p / (available if available > 0 else 1) * fair_share))
        else:
            new_percentages.append(p)

    st.session_state.options.append(f"Option {len(st.session_state.options) + 1}")
    st.session_state.percentages = new_percentages + [fair_share]
    st.session_state.locks.append(False)

if st.sidebar.button("⚖️ Equalize (Unlocked Only)"):
    unlocked_indices = [i for i, L in enumerate(st.session_state.locks) if not L]
    if unlocked_indices:
        locked_sum = sum(
            st.session_state.percentages[i] for i in range(len(st.session_state.locks)) if st.session_state.locks[i])
        available = 100 - locked_sum
        for i in unlocked_indices:
            st.session_state.percentages[i] = available / len(unlocked_indices)

if st.sidebar.button("🌪️ Force Total Reset"):
    count = len(st.session_state.options)
    st.session_state.percentages = [100 / count] * count
    st.session_state.locks = [False] * count

if st.sidebar.button("🔽 Sort High to Low"):
    combined = sorted(zip(st.session_state.percentages, st.session_state.options, st.session_state.locks), reverse=True)
    p, o, L = zip(*combined)
    st.session_state.percentages, st.session_state.options, st.session_state.locks = list(p), list(o), list(L)

# --- MAIN LIST ---
for i in range(len(st.session_state.options)):
    cols = st.columns([1, 3, 2, 1])
    with cols[0]:
        st.session_state.locks[i] = st.checkbox("🔒", value=st.session_state.locks[i], key=f"lock_{i}")
    with cols[1]:
        st.session_state.options[i] = st.text_input(f"Name {i}", st.session_state.options[i],
                                                    label_visibility="collapsed", key=f"name_{i}")
    with cols[2]:
        # Percentage input (simplified for web)
        new_p = st.number_input("%", value=float(st.session_state.percentages[i]), key=f"perc_{i}",
                                label_visibility="collapsed")
        st.session_state.percentages[i] = new_p
    with cols[3]:
        if st.button("🗑️", key=f"del_{i}"):
            st.session_state.options.pop(i)
            st.session_state.percentages.pop(i)
            st.session_state.locks.pop(i)
            st.rerun()

# --- THE WHEEL ---
fig, ax = plt.subplots()
ax.pie(st.session_state.percentages, labels=st.session_state.options, autopct='%1.1f%%', startangle=90,
       counterclock=False)
st.pyplot(fig)

if st.button("🎰 SPIN THE WHEEL", type="primary", use_container_width=True):
    result = random.choices(st.session_state.options, weights=st.session_state.percentages)[0]
    st.session_state.winner = result

if st.session_state.winner:
    st.balloons()
    st.success(f"The winner is: **{st.session_state.winner}**!")