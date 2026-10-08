# Look Beyond Skin — PsA Screening

## Static HTML version

`index.html` is a self-contained, mobile-friendly version of the clinic questionnaire. It contains deterministic JavaScript for the PEST and CASPAR scores; no AI calculates or interprets the scores.

It keeps the current workflow:

- The PEST submit button sends the UHID plus the five PEST answers to the clinic Google Form.
- The CASPAR complete-screening button sends the UHID, the five PEST answers, and a structured CASPAR assessment summary (Psoriasis Severity, criteria selections, RF and X-ray status, deterministic score, and referral prompt) to the same form.
- Use the CASPAR complete-screening button instead of the PEST-only button when one combined record is wanted; using both buttons intentionally creates two form responses.
- The Google Form owner receives a new-response notification by email; clinical details remain in the form response, not the notification email.
- There is no local SQLite database in the static version.

The Google Form submission uses a browser `POST` to a hidden frame. UHID and answers are therefore not placed in the page URL. A static page cannot read Google’s cross-origin response, so its confirmation means the browser sent the form; it is not an independently verified delivery receipt.

## Publish it

For free static hosting, enable GitHub Pages for the `main` branch and the repository root. The page will then be available at:

`https://nbhushan15.github.io/psa-clinic-mvp/`

Keep the existing Streamlit version live until the GitHub Pages page has been checked on a phone. Once the static URL is live, update the OPD QR code to use that URL.

## Local preview

Open `index.html` in a modern browser, or serve this folder with any simple local web server. Do not use patient identifiers while testing.
