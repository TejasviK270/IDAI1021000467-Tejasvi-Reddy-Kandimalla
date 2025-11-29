# app.py
import streamlit as st
import pandas as pd
import datetime as dt
import random

# Optional: Turtle graphics for local use
try:
    import turtle
    TURTLE_AVAILABLE = True
except:
    TURTLE_AVAILABLE = False

# ------------------------------
# Config
# ------------------------------
st.set_page_config(page_title="MedTimer Companion", page_icon="💊", layout="wide")

# ------------------------------
# Session state
# ------------------------------
if "medicines" not in st.session_state:
    st.session_state.medicines = []  # list of dicts
if "taken_today" not in st.session_state:
    st.session_state.taken_today = set()
if "adherence_score" not in st.session_state:
    st.session_state.adherence_score = 0
if "motivational_quotes" not in st.session_state:
    st.session_state.motivational_quotes = [
        "Every dose taken is a step toward wellness.",
        "Consistency builds strength.",
        "You're doing great—keep it up!",
        "Health is the real wealth.",
        "Small steps lead to big changes.",
        "Your effort today shapes your tomorrow.",
        "Peace of mind starts with care.",
        "One dose at a time, you're healing.",
        "You're not alone—MedTimer is here for you.",
        "Celebrate every dose taken!"
    ]

# ------------------------------
# Turtle graphics
# ------------------------------
def draw_smiley():
    if not TURTLE_AVAILABLE:
        return
    screen = turtle.Screen()
    screen.title("MedTimer: Great Adherence!")
    t = turtle.Turtle()
    t.speed(3)
    t.pensize(3)

    # Face
    t.penup()
    t.goto(0, -100)
    t.pendown()
    t.color("gold")
    t.begin_fill()
    t.circle(100)
    t.end_fill()

    # Eyes
    t.penup()
    t.goto(-30, 30)
    t.pendown()
    t.dot(20, "black")
    t.penup()
    t.goto(30, 30)
    t.pendown()
    t.dot(20, "black")

    # Smile
    t.penup()
    t.goto(-40, -20)
    t.setheading(-60)
    t.pendown()
    t.circle(50, 120)

    t.hideturtle()

def draw_trophy():
    if not TURTLE_AVAILABLE:
        return
    screen = turtle.Screen()
    screen.title("MedTimer: Weekly Trophy!")
    t = turtle.Turtle()
    t.speed(3)
    t.pensize(3)

    # Cup
    t.color("orange")
    t.begin_fill()
    t.circle(40)
    t.end_fill()

    # Base
    t.penup()
    t.goto(-20, -60)
    t.pendown()
    t.begin_fill()
    t.forward(40)
    t.right(90)
    t.forward(20)
    t.right(90)
    t.forward(40)
    t.right(90)
    t.forward(20)
    t.end_fill()

    # Text
    t.penup()
    t.goto(0, -100)
    t.write("🏆 Great Adherence!", align="center", font=("Arial", 14, "bold"))
    t.hideturtle()

# ------------------------------
# Functions
# ------------------------------
def add_medicine(name, time):
    st.session_state.medicines.append({
        "name": name,
        "time": time,
        "taken": False,
        "date": dt.date.today()
    })

def mark_taken(name):
    for med in st.session_state.medicines:
        if med["name"] == name and med["date"] == dt.date.today():
            med["taken"] = True
            st.session_state.taken_today.add(name)

def calculate_adherence():
    today = dt.date.today()
    week_start = today - dt.timedelta(days=today.weekday())
    week_meds = [m for m in st.session_state.medicines if week_start <= m["date"] <= today]
    if not week_meds:
        return 0
    taken = sum(1 for m in week_meds if m["taken"])
    return int((taken / len(week_meds)) * 100)

# ------------------------------
# UI
# ------------------------------
st.title("MedTimer 💊 Daily Medicine Companion")
st.write("Track your daily medicines, mark doses, and celebrate your adherence with friendly visuals.")

col1, col2 = st.columns([1.2, 1.8])

# ------------------------------
# Input column
# ------------------------------
with col1:
    st.subheader("Add Medicine")
    med_name = st.text_input("Medicine Name")
    med_time = st.time_input("Scheduled Time", value=dt.time(9, 0))
    if st.button("Add to Schedule"):
        if med_name.strip():
            add_medicine(med_name.strip(), med_time)
            st.success(f"Added {med_name} at {med_time.strftime('%H:%M')}")
        else:
            st.warning("Please enter a valid medicine name.")

    st.markdown("---")
    st.subheader("Motivational Tip")
    st.info(random.choice(st.session_state.motivational_quotes))

# ------------------------------
# Checklist column
# ------------------------------
with col2:
    st.subheader("Today's Checklist")
    now = dt.datetime.now().time()
    today_meds = [m for m in st.session_state.medicines if m["date"] == dt.date.today()]
    if not today_meds:
        st.info("No medicines scheduled for today.")
    else:
        for med in today_meds:
            status = "upcoming"
            if med["taken"]:
                status = "taken"
            elif now > med["time"]:
                status = "missed"

            color = {"taken": "green", "upcoming": "yellow", "missed": "red"}[status]
            st.markdown(f"**{med['name']}** at {med['time'].strftime('%H:%M')} — "
                        f"<span style='color:{color};font-weight:bold'>{status.upper()}</span>",
                        unsafe_allow_html=True)
            if not med["taken"] and status != "missed":
                if st.button(f"Mark {med['name']} as taken"):
                    mark_taken(med["name"])
                    st.success(f"{med['name']} marked as taken.")

    st.markdown("---")
    st.subheader("Weekly Adherence Score")
    score = calculate_adherence()
    st.session_state.adherence_score = score
    st.metric("Adherence", f"{score}%")

    if score >= 80:
        st.success("🎉 Excellent adherence this week!")
        draw_trophy()
    elif score >= 50:
        st.info("👍 Good job! Keep going.")
        draw_smiley()
    else:
        st.warning("⚠️ Let's aim for better consistency.")

# ------------------------------
# Footer
# ------------------------------
st.markdown("---")
st.caption("MedTimer is designed for simplicity, clarity, and encouragement. Turtle graphics open in a separate window locally.")
