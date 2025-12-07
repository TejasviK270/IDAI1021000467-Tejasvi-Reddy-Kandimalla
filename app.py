# app.py
import streamlit as st
import datetime as dt
import random
import math
import struct

# -------------------------------------------------
# CONFIG & STYLE
# -------------------------------------------------
st.set_page_config(page_title="MedTimer Companion", page_icon="Pill", layout="wide")

st.markdown("""
<style>
    body { background-color: #F0F8FF; color: #004d40; font-size: 18px; }
    h1, h2, h3 { color: #00695C; }
    .pill {
        display: inline-block; padding: 4px 12px; border-radius: 999px;
        font-weight: 600; color: white; margin-left: 8px;
    }
    .pill-green  { background: #2E7D32; }
    .pill-yellow { background: #FBC02D; color: #1a1a1a; }
</style>
""", unsafe_allow_html=True)

# -------------------------------------------------
# SESSION STATE
# -------------------------------------------------
if "schedules" not in st.session_state:
    st.session_state.schedules = []
if "taken_events" not in st.session_state:
    st.session_state.taken_events = set()
if "reminder_minutes" not in st.session_state:
    st.session_state.reminder_minutes = 15

# -------------------------------------------------
# CONSTANTS
# -------------------------------------------------
COMMON_MEDICINES = sorted([
    "Aspirin","Amoxicillin","Azithromycin","Atorvastatin","Acetaminophen","Albuterol",
    "Ibuprofen","Insulin","Levothyroxine","Lisinopril","Losartan","Metformin",
    "Omeprazole","Paracetamol","Prednisone","Sertraline","Vitamin D","Warfarin"
])

DAY_ORDER = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]

QUOTES = [
    "Every dose taken is a step toward wellness.",
    "Consistency builds strength.",
    "You're doing great—keep it up!",
    "Health is the real wealth.",
    "One dose at a time, you're healing.",
]

# -------------------------------------------------
# HELPERS
# -------------------------------------------------
def weekday_name(date_obj):
    return DAY_ORDER[date_obj.weekday()]

def event_key(date_obj, name, time_obj):
    return f"{date_obj.isoformat()}|{name}|{time_obj.strftime('%H:%M')}"

def mark_as_taken(date_obj, name, time_obj):
    st.session_state.taken_events.add(event_key(date_obj, name, time_obj))
    st.rerun()                                      # ONLY st.rerun() – never experimental

def beep():
    duration = 0.3
    freq = 880
    sample_rate = 44100
    samples = int(duration * sample_rate)
    frames = bytearray()
    for i in range(samples):
        t = i / sample_rate
        value = int(32767 * 0.4 * math.sin(2 * math.pi * freq * t))
        frames += struct.pack("<h", value)
    wav = (
        b"RIFF" + struct.pack("<I", 36 + len(frames)) + b"WAVE"
        b"fmt " + struct.pack("<IHHIIHH", 16, 1, 1, sample_rate, sample_rate*2, 2, 16)
        b"data" + struct.pack("<I", len(frames)) + frames
    )
    st.audio(wav, format="audio/wav", autoplay=True)

def todays_events():
    today = dt.date.today()
    events = []
    for sch in st.session_state.schedules:
        if today >= sch["start_date"] and weekday_name(today) in sch["days_of_week"]:
            for t in sch["times"]:
                events.append({"date": today, "name": sch["name"], "time": t})
    return sorted(events, key=lambda x: x["time"])

def weekly_adherence():
    today = dt.date.today()
    monday = today - dt.timedelta(days=today.weekday())
    total = taken = 0
    for i in range(7):
        d = monday + dt.timedelta(days=i)
        for ev in [e for sch in st.session_state.schedules
                   if d >= sch["start_date"] and weekday_name(d) in sch["days_of_week"]
                   for e in [{"date":d, "name":sch["name"], "time":t} for t in sch["times"]]]:
            total += 1
            if event_key(d, ev["name"], ev["time"]) in st.session_state.taken_events:
                taken += 1
    return int(taken / total * 100) if total else 100

# -------------------------------------------------
# SIDEBAR
# -------------------------------------------------
with st.sidebar:
    st.header("Settings")
    st.session_state.reminder_minutes = st.slider(
        "Reminder window (minutes before)", 1, 60, st.session_state.reminder_minutes
    )

# -------------------------------------------------
# MAIN UI
# -------------------------------------------------
st.title("Pill MedTimer — Your Daily Medicine Companion")

c1, c2, c3 = st.columns([1.4, 1.8, 1.2])

# ---------- ADD SCHEDULE ----------
with c1:
    st.subheader("Add new medicine")
    choice = st.selectbox("Quick select or Custom", ["Custom"] + COMMON_MEDICINES)
    name = st.text_input("Medicine name", value="" if choice=="Custom" else choice)
    days = st.multiselect("Days of week", DAY_ORDER, default=[weekday_name(dt.date.today())])
    doses = st.number_input("Doses per day", 1, 6, 1)
    times = [st.time_input(f"Time #{i+1}", dt.time(9+i*3), key=f"t{i}") for i in range(doses)]
    start = st.date_input("Start date", dt.date.today())

    if st.button("Add schedule"):
        if name.strip() and days:
            st.session_state.schedules.append({
                "name": name.strip(),
                "days_of_week": days,
                "times": times,
                "start_date": start
            })
            st.success(f"Added {name.strip()}!")
            st.rerun()
        else:
            st.warning("Name & days required")

# ---------- TODAY'S CHECKLIST ----------
with c2:
    st.subheader("Today's doses")
    now = dt.datetime.now()
    events = todays_events()

    if not events:
        st.info("No doses today — enjoy your day!")
    else:
        for ev in events:
            key = event_key(ev["date"], ev["name"], ev["time"])
            taken = key in st.session_state.taken_events
            dose_time = dt.datetime.combine(ev["date"], ev["time"])
            mins_left = (dose_time - now).total_seconds() / 60

            colA, colB, colC = st.columns([4,1,1])
            with colA:
                status = "Taken" if taken else "Upcoming"
                st.write(f"**{ev['time'].strftime('%H:%M')}** – {ev['name']}  {status}")
            with colB:
                if 0 < mins_left <= st.session_state.reminder_minutes:
                    beep()
                    st.markdown("<span class='pill pill-yellow'>REMINDER</span>", unsafe_allow_html=True)
                elif taken:
                    st.markdown("<span class='pill pill-green'>DONE</span>", unsafe_allow_html=True)
            with colC:
                if not taken and st.button("Taken", key=key):
                    mark_as_taken(ev["date"], ev["name"], ev["time"])

# ---------- WEEKLY STATS ----------
with c3:
    st.subheader("This week")
    adh = weekly_adherence()
    st.metric("Adherence", f"{adh}%")

    if adh >= 95:
        st.success("Outstanding! Trophy")
        st.balloons()
    elif adh >= 80:
        st.info("Great job! Keep it up")
    else:
        st.warning("Room for improvement")

    st.caption(random.choice(QUOTES))

    if st.button("Reset all taken marks"):
        st.session_state.taken_events = set()
        st.success("Reset done")
        st.rerun()
