from __future__ import annotations

import json
import sqlite3
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import streamlit as st

PEST_ITEMS = {
    "swollen_joint": "Have you ever had a swollen joint (or joints)?",
    "doctor_arthritis": "Has a doctor ever told you that you have arthritis?",
    "nail_pitting": "Do your finger nails or toenails have holes or pits?",
    "heel_pain": "Have you had pain in your heel?",
    "dactylitis_history": "Have you had a finger or toe that was completely swollen and painful for no apparent reason?",
}

def pest_score(answers):
    return sum(bool(answers.get(key, False)) for key in PEST_ITEMS)

def caspar_score(entry, answers):
    if not entry:
        return False, 0, "Disabled: first explicitly document inflammatory articular disease (joint, spine or enthesitis)."
    psoriasis = 2 if answers["current_psoriasis"] else (1 if answers["personal_psoriasis"] or answers["family_psoriasis"] else 0)
    total = psoriasis + sum(bool(answers[k]) for k in ["nail_dystrophy", "negative_rf", "dactylitis", "new_bone"])
    return total >= 3, total, "CASPAR classification criteria fulfilled" if total >= 3 else "CASPAR classification criteria not fulfilled"

def save_record(record):
    db = Path("psa_mvp.sqlite")
    with sqlite3.connect(db) as conn:
        conn.execute("""CREATE TABLE IF NOT EXISTS screenings (
          id INTEGER PRIMARY KEY, created_at TEXT, pest_score INTEGER,
          pest_answers TEXT, skin_severity TEXT, caspar_answers TEXT,
          caspar_score INTEGER, caspar_fulfilled INTEGER, referral_prompt TEXT)""")
        cur = conn.execute("INSERT INTO screenings VALUES (NULL,?,?,?,?,?,?,?,?)", record)
        return cur.lastrowid

st.set_page_config(page_title="PsA Clinic MVP", page_icon="🩺", layout="wide")
st.title("Psoriatic Arthritis Clinic MVP")
st.caption("Local screening and clinician review. Prototype only — it does not diagnose or prescribe.")
tabs = st.tabs(["Patient screening", "CASPAR & psoriasis severity"])

with tabs[0]:
    st.subheader("Patient-facing PEST screening")
    st.markdown("#### PEST questionnaire")
    answers = {key: st.radio(question, ["No", "Yes"], key=key, horizontal=True) == "Yes" for key, question in PEST_ITEMS.items()}
    score = pest_score(answers)
    st.metric("Deterministic PEST score", f"{score}/5", "Positive (≥3/5)" if score >= 3 else "Below PEST-positive threshold")
    st.caption("Source-derived rule: the uploaded PEST form says a total score ≥3/5 is positive and rheumatology referral should be considered.")

with tabs[1]:
    st.subheader("CASPAR and psoriasis severity")
    st.caption("Classification support only. This screen does not diagnose PsA or make a referral decision.")
    severity = st.selectbox("Skin severity (local clinic recording)", ["Not recorded", "Mild", "Moderate", "Severe", "Clinically relevant to patient"])
    entry = st.radio("CASPAR entry criterion: inflammatory articular disease (joint, spine, or enthesitis) explicitly present?", ["No / not established", "Yes"], horizontal=True) == "Yes"
    st.markdown("#### CASPAR classification module")
    rf = st.radio("Rheumatoid factor result", ["Negative", "Positive", "Not available"], index=2, horizontal=True, disabled=not entry)
    xray = st.radio("X-ray: juxta-articular new bone formation", ["Present", "Absent", "Not available"], index=2, horizontal=True, disabled=not entry)
    caspar_answers = {
        "current_psoriasis": st.checkbox("Current psoriasis (2 points)", disabled=not entry),
        "personal_psoriasis": st.checkbox("Personal history of psoriasis (1 point if no current psoriasis)", disabled=not entry),
        "family_psoriasis": st.checkbox("Family history of psoriasis (1 point if no current/personal history)", disabled=not entry),
        "nail_dystrophy": st.checkbox("Psoriatic nail dystrophy: pitting, onycholysis, or hyperkeratosis (1 point)", disabled=not entry),
        "negative_rf": rf == "Negative",
        "dactylitis": st.checkbox("Current dactylitis or recorded history (1 point)", disabled=not entry),
        "new_bone": xray == "Present",
        "rf_result": rf, "xray_result": xray,
    }
    fulfilled, caspar_total, message = caspar_score(entry, caspar_answers)
    if entry:
        st.metric("Deterministic CASPAR score", f"{caspar_total} points", message)
        if "Not available" in (rf, xray):
            st.info("One or more CASPAR inputs are not available. They receive no points; a result that does not fulfil CASPAR may be incomplete.")
    else:
        st.warning(message)
    reasons = []
    if score >= 3: reasons.append(f"PEST is positive ({score}/5; threshold ≥3/5).")
    if fulfilled: reasons.append(f"CASPAR classification criteria are fulfilled ({caspar_total} points; threshold ≥3).")
    st.markdown("#### Referral prompt")
    if reasons:
        st.success("Refer to rheumatology for clinician assessment. " + " ".join(f"- {reason}" for reason in reasons))
        st.caption("This is decision support only. The clinician remains responsible for the referral decision; no referral is sent by the app.")
    else:
        st.info("No PEST- or CASPAR-based referral prompt is displayed. Clinical judgement remains essential.")
    if st.button("Save screening", type="primary"):
        record_id = save_record((date.today().isoformat(), score, json.dumps(answers), severity, json.dumps(caspar_answers), caspar_total, int(fulfilled), json.dumps(reasons)))
        st.success(f"Saved local record #{record_id}. No identifying information is collected in this MVP.")

st.divider()
st.caption("MVP safety boundary: this tool supports structured screening and referral coordination. It does not diagnose PsA, replace assessment, or autonomously prescribe.")
