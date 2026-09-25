from __future__ import annotations

import json
import sqlite3
import urllib.parse
import urllib.request
from datetime import date
from pathlib import Path

import streamlit as st

PEST_ITEMS = {
    "swollen_joint": "Have you ever had a swollen joint (or joints)?",
    "doctor_arthritis": "Has a doctor ever told you that you have arthritis?",
    "nail_pitting": "Do your finger nails or toenails have holes or pits?",
    "heel_pain": "Have you had pain in your heel?",
    "dactylitis_history": "Have you had a finger or toe that was completely swollen and painful for no apparent reason?",
}

GOOGLE_FORM_RESPONSE_URL = "https://docs.google.com/forms/d/e/1FAIpQLSc6lu4Ew4vadMxZ5Rr3X-aQmSGnYkCRBmVIcB--WAxiOIPtSw/formResponse"
GOOGLE_FORM_ENTRIES = {
    "swollen_joint": "entry.1679185626",
    "doctor_arthritis": "entry.751831872",
    "nail_pitting": "entry.1462993322",
    "heel_pain": "entry.1281512710",
    "dactylitis_history": "entry.530109406",
}


def pest_score(answers: dict[str, bool]) -> int:
    return sum(bool(answers.get(key, False)) for key in PEST_ITEMS)


def caspar_score(entry: bool, answers: dict[str, bool]) -> tuple[bool, int, str]:
    if not entry:
        return False, 0, "Disabled: first explicitly document inflammatory articular disease (joint, spine or enthesitis)."
    psoriasis = 2 if answers["current_psoriasis"] else (1 if answers["personal_psoriasis"] or answers["family_psoriasis"] else 0)
    total = psoriasis + sum(bool(answers[k]) for k in ["nail_dystrophy", "negative_rf", "dactylitis", "new_bone"])
    return total >= 3, total, "CASPAR classification criteria fulfilled" if total >= 3 else "CASPAR classification criteria not fulfilled"


def send_pest_to_google_form(answers: dict[str, bool]) -> None:
    """Submit anonymous PEST answers. Google Form choice fields record Yes; blank means No."""
    payload = {GOOGLE_FORM_ENTRIES["swollen_joint"]: "Yes" if answers["swollen_joint"] else "No"}
    for key in ("doctor_arthritis", "nail_pitting", "heel_pain", "dactylitis_history"):
        if answers[key]:
            payload[GOOGLE_FORM_ENTRIES[key]] = "Option 1"
    request = urllib.request.Request(
        GOOGLE_FORM_RESPONSE_URL,
        data=urllib.parse.urlencode(payload).encode("utf-8"),
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=12) as response:
        if response.status not in (200, 302):
            raise RuntimeError("Google Form did not accept the screening.")


def save_local_record(score: int, answers: dict[str, bool]) -> int:
    with sqlite3.connect(Path("psa_mvp.sqlite")) as conn:
        conn.execute("CREATE TABLE IF NOT EXISTS screenings (id INTEGER PRIMARY KEY, created_at TEXT, pest_score INTEGER, pest_answers TEXT)")
        cursor = conn.execute(
            "INSERT INTO screenings VALUES (NULL, ?, ?, ?)",
            (date.today().isoformat(), score, json.dumps(answers)),
        )
        return cursor.lastrowid


st.set_page_config(page_title="PsA Clinic MVP", page_icon="🩺", layout="wide")
st.markdown("""
<style>
.stApp { background: #f6f8fb; }
.block-container { max-width: 940px; padding-top: 2.5rem; padding-bottom: 3rem; }
.clinic-hero { background: linear-gradient(125deg, #0d5263, #247589); border-radius: 22px; color: white; padding: 2.25rem 2.4rem; margin-bottom: 1.5rem; }
.clinic-hero h1 { color: white; font-size: 2rem; margin: 0 0 .45rem; }
.clinic-hero p { margin: 0; opacity: .93; font-size: 1.05rem; }
div[data-testid="stMetric"] { background: white; border: 1px solid #dfe8ed; border-radius: 14px; padding: .7rem 1rem; }
div[role="radiogroup"] { background: white; border: 1px solid #e2e8ee; border-radius: 12px; padding: .35rem .75rem; }
.screening-note { background: #e8f3f5; border-left: 4px solid #247589; border-radius: 7px; padding: .9rem 1rem; color: #174551; }
</style>
<section class="clinic-hero"><h1>Psoriatic Arthritis Screening</h1><p>A short questionnaire for people with psoriasis. Your clinician reviews the result with you.</p></section>
""", unsafe_allow_html=True)
st.caption("Screening support only — this tool does not diagnose psoriatic arthritis or prescribe treatment.")

screening_tab, caspar_tab = st.tabs(["Patient screening", "CASPAR & psoriasis severity"])

with screening_tab:
    st.subheader("Your five questions")
    st.markdown("<div class='screening-note'>Please answer based on symptoms you have had at any time. There are no right or wrong answers.</div>", unsafe_allow_html=True)
    st.write("")
    answers = {}
    for number, (key, question) in enumerate(PEST_ITEMS.items(), start=1):
        st.markdown(f"**{number}. {question}**")
        answers[key] = st.radio("Choose one answer", ["No", "Yes"], key=f"p_{key}", horizontal=True, label_visibility="collapsed") == "Yes"
    score = pest_score(answers)
    left, right = st.columns([1, 2])
    with left:
        st.metric("Your PEST score", f"{score}/5")
    with right:
        if score >= 3:
            st.warning("Your score is 3 or more. Please discuss this with your dermatologist; a rheumatology assessment may be considered.")
        else:
            st.info("Your score is below 3. Your dermatologist will interpret this alongside your symptoms and examination.")
    st.caption("PEST scoring is calculated automatically. A score of 3/5 or more is a positive screen; it is not a diagnosis.")
    if st.button("Submit screening", type="primary", use_container_width=True):
        try:
            send_pest_to_google_form(answers)
            record_id = save_local_record(score, answers)
            st.success(f"Thank you. Your anonymous screening was submitted to the clinic response form. Local record #{record_id} was also created.")
        except Exception:
            st.error("The screening could not be submitted to the clinic response form. Please tell the clinic staff and do not re-enter personal details.")

with caspar_tab:
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
        "negative_rf": rf == "Negative", "dactylitis": st.checkbox("Current dactylitis or recorded history (1 point)", disabled=not entry),
        "new_bone": xray == "Present",
    }
    fulfilled, total, message = caspar_score(entry, caspar_answers)
    if entry:
        st.metric("Deterministic CASPAR score", f"{total} points", message)
    else:
        st.warning(message)
    reasons = []
    if score >= 3: reasons.append(f"PEST is positive ({score}/5; threshold ≥3/5).")
    if fulfilled: reasons.append(f"CASPAR classification criteria are fulfilled ({total} points; threshold ≥3).")
    st.markdown("#### Referral prompt")
    if reasons:
        st.success("Refer to rheumatology for clinician assessment. " + " ".join(f"- {reason}" for reason in reasons))
        st.caption("Decision support only. The clinician remains responsible for the referral decision.")
    else:
        st.info("No PEST- or CASPAR-based referral prompt is displayed. Clinical judgement remains essential.")

st.divider()
st.caption("Anonymous answers are sent to the clinic's Google Form when the patient submits the PEST screen. Do not enter identifying information. This tool does not diagnose PsA, replace assessment, or autonomously prescribe.")
