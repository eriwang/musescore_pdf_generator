# MuseScore PDF Generator

Given a Drive folder that contains MuseScore files (anywhere below in the directory tree), generates PDFs for its parts and uploads them to Drive.

## First Time Setup

- You should have `python3.8` (other versions untested) and MuseScore installed.
- Run `scripts/setup.sh` from repo root. This installs the following:
    - All `python` dependencies, as well as a virtualenv
    - Git hooks for style checks

### Configuration/ Credentials

- Copy `example-config.json` to `config.json` and fill in with the correct fields.
- Create a Google API project and create an oauth token for the MuseScore PDF Generator in that project. Download the JSON file for the oauth token, or copy `example-credentials.json` to `credentials.json` and fill in with the correct fields.

## Usage

Ensure dependencies are installed (either globally or in a venv).

- Drive sync mode: `python src/main.py`
- Convert single MuseScore file: `python src/main.py --mscz-to-convert <musescore file>`

## Notes

- The generator will attempt to optimize spatium of the parts to get the largest spatium for the minimum number of pages.
- If the MuseScore file has parts already, it will not optimize the spatium at all, and just export the parts to PDFs as is. For any manual adjustments to parts such as page/ line breaks, make the parts manually.