import streamlit as st
import datetime as dt
import random
import math
import struct

# Page config & styling
st.set_page_config(page_title="MedTimer", page_icon="💊", layout="wide")
st.markdown(
    """
    <style>
    body {background:#F0F8FF; color:#004d40; font-size:18px}
    h1,h2,h3 {color:#00695C}
    .pill {padding:4px 12px; border-radius:999px; font-weight:600; color:white; margin-left:8px}
    .pill-green {background:#2E7D32}
    .pill-yellow {background:#FBC02D; color:#000}
    </style>
    """,
    unsafe_allow_html=True,
)

# Session state initialization
defaults = {
    "schedules": [],
    "taken_events": set(),
    "reminder_minutes": 15,
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# Helper functions
def key(date, name, time_obj):
    return f"{date}|{name}|{time_obj.strftime('%H:%M')}"

def mark_taken(date, name, time_obj):
    st.session_state.taken_events.add(key(date, name, time_obj))
    st.rerun()

def beep():
    sample_rate = 44100
    duration = 0.3
    freq = 880  # A5 note
    samples = int(sample_rate * duration)
    data = bytearray()
    for i in range(samples):
        value = int(32767 * 0.4 * math.sin(2 * math.pi * freq * i / sample_rate))
        data += struct.pack("<h", value)
    wav_header = (
        b"RIFF" + struct.pack("<I", 36 + len(data)) +
        b"WAVEfmt " + struct.pack("<IHHIIHH", 16, 1, 1, sample_rate, sample_rate*2, 2, 16) +
        b"data" + struct.pack("<I", len(data))
    )
    st.audio(wav_header + data, format="audio/wav", autoplay=True)

def today_events():
    today = dt.date.today()
    weekday_name = today.strftime("%A")
    events = []
    for s in st.session_state.schedules:
        if today < s["start_date"]:
            continue
        if weekday_name in s["days_of_week"] or weekday_name[:3] in s["days_of_week"]:
            for t in s["times"]:
                events.append({"name": s["name"], "time": t})
    return sorted(events, key=lambda x: x["time"])

# Sidebar
with st.sidebar:
    st.session_state.reminder_minutes = st.slider(
        "Reminder (minutes before)", 1, 60, st.session_state.reminder_minutes
    )

# Main layout
st.title("💊 MedTimer – Medication Reminder")

c1, c2, c3 = st.columns([1.4, 1.8, 1.2])

# Column 1 – Add new medicine
with c1:
    st.subheader("Add medicine")
    name = st.text_input("Medicine name")
    days = st.multiselect(
        "Days of week",
        ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"],
        default=["Monday"]
    )
    n = st.number_input("Doses per day", 1, 6, 1)
    times = []
    for i in range(n):
        t = st.time_input(f"Time {i+1}", dt.time(9 + i*3), key=f"time_input_{i}")
        times.append(t)

    if st.button("Add schedule") and name and days:
        st.session_state.schedules.append({
            "name": name,
            "days_of_week": days,
            "times": times,
            "start_date": dt.date.today()
        })
        st.success(f"Added {name}!")
        st.rerun()

# Column 2 – Today's schedule
with c2:
    st.subheader("Today")
    now = dt.datetime.now()
    events = today_events()

    if not events:
        st.info("No medications scheduled for today.")
    else:
        for e in events:
            event_time = dt.datetime.combine(dt.date.today(), e["time"])
            minutes_until = (event_time - now).total_seconds() / 60
            k = key(dt.date.today(), e["name"], e["time"])
            taken = k in st.session_state.taken_events

            col_a, col_b, col_c = st.columns([4, 1, 1])
            with col_a:
                status = "✅ Taken" if taken else "⏳ Pending"
                st.write(f"**{e['time'].strftime('%H:%M')}** – {e['name']} {status}")

            with col_b:
                if taken:
                    st.markdown("<span class='pill pill-green'>DONE</span>", unsafe_allow_html=True)
                elif 0 < minutes_until <= st.session_state.reminder_minutes:
                    beep()
                    st.markdown("<span class='pill pill-yellow'>NOW</span>", unsafe_allow_html=True)

            with col_c:
                if not taken and minutes_until <= 0:  # allow marking even if slightly late
                    if st.button("Taken", key=k):
                        mark_taken(dt.date.today(), e["name"], e["time"])

# Column 3 – Weekly adherence
with c3:
    st.subheader("This week")
    
    # Count expected and taken doses for the last 7 days
    expected = 0
    taken_count = 0
    today = dt.date.today()
    
    for delta in range(7):
        day = today - dt.timedelta(days=delta)
        weekday_name = day.strftime("%A")
        day_key_prefix = f"{day}|"
        
        for s in st.session_state.schedules:
            if day >= s["start_date"] and (weekday_name in s["days_of_week"] or weekday_name[:3] in s["days_of_week"]):
                expected += len(s["times"])
        
        # Count taken on this day
        for k in st.session_state.taken_events:
            if k.startswith(day_key_prefix):
                taken_count += 1

    adherence = int(taken_count / expected * 100) if expected > 0 else 100

    st.metric("Adherence (7 days)", f"{adherence}%")
    if adherence >= 95:
        st.balloons()
    
    st.caption(random.choice([
        "Keep going!", "Great job!", "Every dose counts!", 
        "You're doing amazing!", "Consistency is key!"
    ]))

    if st.button("Reset week data"):
        st.session_state.taken_events = set()
        st.success("Week data cleared!")
        st.rerun()
