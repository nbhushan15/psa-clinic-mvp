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

GOOGLE_FORM_RESPONSE_URL = "https://docs.google.com/forms/d/e/1FAIpQLSfnz1KbICaredRCN73tFf3Fvrzc4Wbt-0katp9Q4D5clYLVfw/formResponse"
GOOGLE_FORM_ENTRIES = {
    "uhid": "entry.1157237787",
    "swollen_joint": "entry.920246852",
    "doctor_arthritis": "entry.689126709",
    "nail_pitting": "entry.2040305267",
    "heel_pain": "entry.1460286880",
    "dactylitis_history": "entry.1951837391",
}

PSORIASIS_GUIDELINE_URL = "https://www.nice.org.uk/guidance/cg153/chapter/recommendations"
SPONDYLOARTHRITIS_GUIDELINE_URL = "https://www.nice.org.uk/guidance/ng65/chapter/Recommendations"


def pest_score(answers: dict[str, bool]) -> int:
    return sum(bool(answers.get(key, False)) for key in PEST_ITEMS)


def caspar_score(entry: bool, answers: dict[str, bool]) -> tuple[bool, int, str]:
    if not entry:
        return False, 0, "Confirm the clinical context to calculate CASPAR."
    psoriasis = 2 if answers["current_psoriasis"] else (1 if answers["personal_psoriasis"] or answers["family_psoriasis"] else 0)
    total = psoriasis + sum(bool(answers[k]) for k in ["nail_dystrophy", "negative_rf", "dactylitis", "new_bone"])
    return total >= 3, total, "CASPAR classification criteria fulfilled" if total >= 3 else "CASPAR classification criteria not fulfilled"


def send_pest_to_google_form(uhid: str, answers: dict[str, bool]) -> None:
    """Submit the UHID and PEST answers to the clinic response form."""
    payload = {GOOGLE_FORM_ENTRIES["uhid"]: uhid}
    for key in PEST_ITEMS:
        payload[GOOGLE_FORM_ENTRIES[key]] = "Yes" if answers[key] else "No"
    request = urllib.request.Request(
        GOOGLE_FORM_RESPONSE_URL,
        data=urllib.parse.urlencode(payload).encode("utf-8"),
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=12) as response:
        if response.status not in (200, 302):
            raise RuntimeError("Google Form did not accept the screening.")


def save_local_record(uhid: str, score: int, answers: dict[str, bool]) -> int:
    with sqlite3.connect(Path("psa_mvp.sqlite")) as conn:
        conn.execute(
            "CREATE TABLE IF NOT EXISTS screenings (id INTEGER PRIMARY KEY, created_at TEXT, uhid TEXT, pest_score INTEGER, pest_answers TEXT)"
        )
        columns = {row[1] for row in conn.execute("PRAGMA table_info(screenings)")}
        if "uhid" not in columns:
            conn.execute("ALTER TABLE screenings ADD COLUMN uhid TEXT")
        cursor = conn.execute(
            "INSERT INTO screenings (created_at, uhid, pest_score, pest_answers) VALUES (?, ?, ?, ?)",
            (date.today().isoformat(), uhid, score, json.dumps(answers)),
        )
        return cursor.lastrowid


st.set_page_config(page_title="Look Beyond Skin | PsA Screen", page_icon="🩺", layout="wide")
st.markdown("""
<style>
.stApp { background: #f8fafb; color: #18262b; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }
.stApp p, .stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp h5,
.stApp label, .stApp span, .stApp [data-testid="stMarkdownContainer"],
.stApp [data-testid="stCaptionContainer"] { color: #18262b !important; }
.block-container { max-width: 800px; padding-top: 1.4rem; padding-bottom: 3rem; }
.clinic-hero { background: #0d5967; border-radius: 16px; color: white; padding: 1.6rem 1.75rem; margin-bottom: 1rem; }
.stApp .clinic-hero, .stApp .clinic-hero * { color: white !important; }
.clinic-eyebrow { font-size: .72rem; font-weight: 700; letter-spacing: .13em; margin-bottom: .45rem; opacity: .82; }
.clinic-hero h1 { font-size: 2rem; line-height: 1.15; margin: 0 0 .35rem; letter-spacing: -.025em; }
.clinic-hero p { margin: 0; opacity: .9; font-size: 1rem; }
button[role="tab"] { height: 2.55rem; padding: 0 .8rem; color: #5c6a70 !important; font-weight: 600; }
button[role="tab"][aria-selected="true"] { color: #0d5967 !important; }
div[data-testid="stVerticalBlockBorderWrapper"] { background: #ffffff; border: 1px solid #e2e8ea; border-radius: 15px; box-shadow: none; }
div[role="radiogroup"] { gap: .45rem; padding-top: .15rem; }
div[role="radiogroup"] label { border: 1px solid #dce5e7; border-radius: 999px; min-height: 2.35rem; padding: .32rem .75rem; background: #ffffff; }
div[role="radiogroup"] label:has(input:checked) { background: #e7f4f4; border-color: #0d6876; }
div[role="radiogroup"] label:has(input:focus-visible) { outline: 3px solid #a9d6dc; outline-offset: 2px; }
.screening-note { background: #eef7f7; border: 1px solid #d5e9ea; border-radius: 11px; padding: .8rem 1rem; color: #194550; }
.question-number { width: 2rem; height: 2rem; border-radius: 999px; background: #e7f4f4; color: #0d5967; display: flex; align-items: center; justify-content: center; font-size: .82rem; font-weight: 750; margin-top: .1rem; }
.question-text { font-size: 1rem; font-weight: 650; line-height: 1.45; color: #18262b; padding-top: .1rem; }
.score-card { background: #f0f8f8; border: 1px solid #d4e9e9; border-radius: 14px; padding: .85rem 1rem; }
.score-card span { display: block; color: #496067 !important; font-size: .79rem; font-weight: 700; letter-spacing: .04em; text-transform: uppercase; }
.score-card strong { display: block; color: #0d5967 !important; font-size: 1.55rem; line-height: 1.2; margin-top: .12rem; }
button[kind="primary"] { border-radius: 10px !important; background: #0d5967 !important; }
</style>
<section class="clinic-hero"><div class="clinic-eyebrow">JOINT HEALTH CHECK</div><h1>Look Beyond Skin</h1><p>A short Psoriatic Arthritis screening questionnaire for people with Psoriasis.</p></section>
""", unsafe_allow_html=True)
st.caption("Screening support only — this tool does not diagnose psoriatic arthritis or prescribe treatment.")

screening_tab, caspar_tab, clinical_tests_tab = st.tabs(
    ["Screening", "CASPAR & Psoriasis", "Tests to consider"]
)

with screening_tab:
    st.subheader("Your five questions")
    uhid = st.text_input("UHID", placeholder="Enter UHID", max_chars=64)
    st.markdown("<div class='screening-note'>Please enter your UHID, then answer based on symptoms you have had at any time. There are no right or wrong answers.</div>", unsafe_allow_html=True)
    st.write("")
    answers = {}
    for number, (key, question) in enumerate(PEST_ITEMS.items(), start=1):
        with st.container(border=True):
            number_column, answer_column = st.columns([0.09, 0.91], vertical_alignment="top")
            with number_column:
                st.markdown(f"<div class='question-number'>{number:02d}</div>", unsafe_allow_html=True)
            with answer_column:
                st.markdown(f"<div class='question-text'>{question}</div>", unsafe_allow_html=True)
                answers[key] = st.radio(
                    "Choose one answer",
                    ["No", "Yes"],
                    key=f"p_{key}",
                    horizontal=True,
                    label_visibility="collapsed",
                ) == "Yes"
        st.write("")
    score = pest_score(answers)
    left, right = st.columns([1, 2])
    with left:
        st.markdown(f"<div class='score-card'><span>PEST score</span><strong>{score}/5</strong></div>", unsafe_allow_html=True)
    with right:
        if score >= 3:
            st.warning("Your score is 3 or more. Please discuss this with your dermatologist; a rheumatology assessment may be considered.")
        else:
            st.info("Your score is below 3. Your dermatologist will interpret this alongside your symptoms and examination.")
    st.caption("PEST scoring is calculated automatically. A score of 3/5 or more is a positive screen; it is not a diagnosis.")
    if st.button("Submit screening", type="primary", use_container_width=True):
        if not uhid.strip():
            st.error("Please enter the UHID before submitting the screening.")
        else:
            try:
                send_pest_to_google_form(uhid.strip(), answers)
                record_id = save_local_record(uhid.strip(), score, answers)
                st.success(f"Thank you. Your screening was submitted to the clinic response form. Local record #{record_id} was also created.")
            except Exception:
                st.error("The screening could not be submitted to the clinic response form. Please tell the clinic staff.")

with caspar_tab:
    st.subheader("CASPAR and Psoriasis Severity")
    st.caption("Classification support only. This screen does not diagnose PsA or make a referral decision.")
    severity = st.selectbox("Psoriasis Severity (local clinic recording)", ["Not recorded", "Mild", "Moderate", "Severe", "Clinically relevant to patient"])
    entry = st.checkbox(
        "Clinician confirmation: inflammatory joint, spine, or entheseal disease is established",
        help="CASPAR classification applies only in this clinical context.",
    )
    st.markdown("#### CASPAR classification module")
    rf = st.radio("Rheumatoid factor result", ["Negative", "Positive", "Not available"], index=2, horizontal=True, disabled=not entry)
    xray = st.radio("X-ray: juxta-articular new bone formation", ["Present", "Absent", "Not available"], index=2, horizontal=True, disabled=not entry)
    caspar_answers = {
        "current_psoriasis": st.checkbox("Current Psoriasis (2 points)", disabled=not entry),
        "personal_psoriasis": st.checkbox("Personal History of Psoriasis (1 point if no Current Psoriasis)", disabled=not entry),
        "family_psoriasis": st.checkbox("Family History of Psoriasis (1 point if no Current/Personal History)", disabled=not entry),
        "nail_dystrophy": st.checkbox("Psoriatic Nail Dystrophy: pitting, onycholysis, or hyperkeratosis (1 point)", disabled=not entry),
        "negative_rf": rf == "Negative", "dactylitis": st.checkbox("Current dactylitis or recorded history (1 point)", disabled=not entry),
        "new_bone": xray == "Present",
    }
    fulfilled, total, message = caspar_score(entry, caspar_answers)
    if entry:
        st.metric("Deterministic CASPAR score", f"{total} points", message)
    else:
        st.warning(message)

    if entry:
        tests_to_consider = []
        if rf == "Not available":
            tests_to_consider.append(
                "**Rheumatoid factor (RF):** record a result if clinically appropriate; a negative RF result contributes to the CASPAR classification score."
            )
        if xray == "Not available":
            tests_to_consider.append(
                "**Plain radiographs of the hands and/or feet:** consider only if clinically appropriate; CASPAR counts juxta-articular new bone formation on plain radiographs."
            )
        if tests_to_consider:
            st.markdown("#### Tests to consider")
            st.caption("Clinician prompts only — this app does not order tests or replace clinical assessment.")
            for test in tests_to_consider:
                st.markdown(f"- {test}")

    reasons = []
    if score >= 3: reasons.append(f"PEST is positive ({score}/5; threshold ≥3/5).")
    if fulfilled: reasons.append(f"CASPAR classification criteria are fulfilled ({total} points; threshold ≥3).")
    st.markdown("#### Referral prompt")
    if reasons:
        st.success("Refer to rheumatology for clinician assessment. " + " ".join(f"- {reason}" for reason in reasons))
        st.caption("Decision support only. The clinician remains responsible for the referral decision.")
    else:
        st.info("No PEST- or CASPAR-based referral prompt is displayed. Clinical judgement remains essential.")

with clinical_tests_tab:
    st.subheader("Tests to consider")
    st.caption(
        "Clinician use only. These are prompts for assessment and local pathways — they are not automatic orders, a diagnosis, or a treatment plan."
    )
    psoriasis_tests, psa_tests = st.tabs(["Psoriasis", "Suspected or established PsA"])

    with psoriasis_tests:
        st.markdown("#### Clinic Standard: Every Patient With Psoriasis")
        st.markdown(
            "The following are the clinic’s standard assessment tests for all Psoriasis patients."
        )
        st.markdown(
            "- **Complete blood count (CBC)**"
        )
        st.markdown(
            "- **Lipid profile**"
        )
        st.markdown(
            "- **Liver function tests (LFT)**"
        )
        st.markdown(
            "- **HbA1c**"
        )
        st.info("Add treatment-specific monitoring and any additional investigations according to the dermatologist’s assessment and local protocol.")

    with psa_tests:
        st.markdown("#### Clinic Standard: Suspected Psoriatic Arthritis")
        st.markdown(
            "The following are added when PsA is suspected."
        )
        st.markdown(
            "- **Rheumatoid factor (RF)** — a documented negative result is one CASPAR component; ‘Not available’ is not negative and receives no CASPAR point."
        )
        st.markdown(
            "- **C-reactive protein (CRP)**"
        )
        st.markdown(
            "- **Erythrocyte sedimentation rate (ESR)**"
        )
        st.markdown(
            "- **Ultrasound or X-ray**, selected for the clinically relevant symptomatic site."
        )
        st.markdown(
            "Normal CRP or ESR does not exclude PsA. Further investigations remain at the dermatologist’s or rheumatologist’s discretion."
        )
        st.warning("Prompt rheumatology assessment remains appropriate when PsA is suspected; do not delay referral while waiting for this checklist.")

    st.caption(
        "The test lists above are a local clinic workflow. Clinical reference context: "
        f"[NICE psoriasis assessment and management]({PSORIASIS_GUIDELINE_URL}) and "
        f"[NICE spondyloarthritis diagnosis and management]({SPONDYLOARTHRITIS_GUIDELINE_URL})."
    )

st.divider()
st.caption("Your UHID and screening answers are sent to the clinic's Google Form when the patient submits the PEST screen. Do not enter any other identifying information. This tool does not diagnose PsA, replace assessment, or autonomously prescribe.")
