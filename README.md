# Look Beyond Skin — PsA Screening

## Static HTML version

`index.html` is a self-contained, mobile-friendly version of the clinic questionnaire. It contains deterministic JavaScript for the PEST and CASPAR scores; no AI calculates or interprets the scores.

It keeps the current workflow:

- UHID plus the five PEST answers are sent to the clinic Google Form.
- CASPAR, Psoriasis Severity, referral prompts, and test prompts remain in the browser and are not sent to Google Forms.
- There is no local SQLite database in the static version.

The Google Form submission uses a browser `POST` to a hidden frame. UHID and answers are therefore not placed in the page URL. A static page cannot read Google’s cross-origin response, so its confirmation means the browser sent the form; it is not an independently verified delivery receipt.

## Publish it

For free static hosting, enable GitHub Pages for the `main` branch and the repository root. The page will then be available at:

`https://nbhushan15.github.io/psa-clinic-mvp/`

Keep the existing Streamlit version live until the GitHub Pages page has been checked on a phone. Once the static URL is live, update the OPD QR code to use that URL.

## Local preview

Open `index.html` in a modern browser, or serve this folder with any simple local web server. Do not use patient identifiers while testing.
