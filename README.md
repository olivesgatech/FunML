# FunML Website Build Guide

This repository builds the FunML website from the lecture zip and a small set of website source files.

## Copy These Files And Folders First

Copy these into the project root before building:

- `.gitignore`
- `README.md`
- `buildsite.py`
- `index.html`
- `styles.css`
- `script.js`
- `assets/media_resources.json`
- `assets/slides/`
- `assets/notebooks/`
- `assets/demos.html`
- `assets/disclaimer.html`

These are the required tracked website source inputs.

Also place this local build input in the project root before building:

- `source/FunML_Sp_26_LectNotes.zip`

The lecture zip and extracted `source/raw/` tree are ignored by git, so they stay local and are not committed.

## Install Dependencies

```bash
pip install beautifulsoup4
pip install "jupyterlite-core[lab]" jupyterlite-pyodide-kernel
```

Also install:

- `python3`
- `pandoc`

## Build The Website

Run these commands from the repository root:

```bash
mkdir -p source/raw
unzip -q source/FunML_Sp_26_LectNotes.zip -d source/raw
find source/raw -type f \( -iname "*in-class exercise*.tex" -o -iname "*in class exercise*.tex" \) -delete
python3 buildsite.py --src source/raw --out .
```

## Generated Automatically

After the build, these are generated automatically:

- `source/raw/`
- `lectures/`
- `lectures/img/`
- `assets/style.css`
- `assets/exercises.html`
- `assets/exercises/`
- `assets/jupyterlite/` if JupyterLite dependencies are installed

`source/raw/` and `source/FunML_Sp_26_LectNotes.zip` are local-only build inputs covered by `.gitignore`.

## Preview Locally

```bash
python3 -m http.server 8000
```

Open:

`http://localhost:8000`

## Push Changes

Run these commands from the repository root:

```bash
git add -A
git commit -m "Update FunML website"
git push origin main
```

Optional local cleanup after pushing:

```bash
rm -rf source/raw
rm -f source/FunML_Sp_26_LectNotes.zip
```
