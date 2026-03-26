#!/usr/bin/env python3
from pathlib import Path
import argparse
import subprocess
import shutil
import re
import json
import fnmatch
import html
import tempfile
from urllib.parse import quote, unquote, urlsplit, urlunsplit, urlencode
from bs4 import BeautifulSoup


PROJECT_TITLE = "ECE 4252/6252 – FunML Lecture Notes"
SCRIPT_ROOT = Path(__file__).resolve().parent
EXCLUDED_TEX_FILENAMES = {"lect1213_extra.tex"}
EXCLUDED_TEX_PATH_PARTIALS = {"lect1213_extra", "funml_l12_l13_ext"}
INCLUDEGRAPHICS_WIDTH_SCALE = 0.60

CSS = """
html, body {
  margin: 0;
  padding: 0;
  width: 100%;
  overflow-x: hidden;
}

body {
  font-family: system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial, sans-serif;
  line-height: 1.5;
  overflow-wrap: anywhere;
}

main {
  width: 100%;
  max-width: none;
  padding: 20px 24px;
  margin: 0;
  overflow-x: hidden;
  box-sizing: border-box;
}

h1, h2, h3 {
  line-height: 1.25;
}

nav {
  background: #f6f8fa;
  padding: 12px 16px;
  border-bottom: 1px solid #ddd;
}

nav a {
  margin-right: 12px;
  text-decoration: none;
  font-weight: 500;
}

img, video, svg, canvas, iframe, embed, object {
  max-width: 100%;
  height: auto;
}

img {
  display: block;
  margin: 10px auto;
}

table {
  width: 100%;
  table-layout: fixed;
  border-collapse: collapse;
  border: 1px solid #cfd7e3;
  margin: 12px 0 18px;
  background: #fff;
}

th, td {
  border: 1px solid #cfd7e3;
  padding: 8px 10px;
  vertical-align: top;
  text-align: left;
  word-break: break-word;
}

thead th {
  background: #f5f8fc;
}

* {
  box-sizing: border-box;
  max-width: 100%;
}

pre, code {
  white-space: pre-wrap;
  word-break: break-word;
}

.math.display, .MathJax_Display {
  max-width: 100%;
  overflow: hidden;
}

.interactive-notebook {
  margin: 20px 0 28px;
  padding: 18px;
  border: 1px solid #d7dfeb;
  border-radius: 14px;
  background: linear-gradient(180deg, #f9fbff 0%, #f4f7fb 100%);
}

.interactive-notebook h3 {
  margin: 0 0 8px;
}

.interactive-notebook p {
  margin: 0 0 14px;
  color: #334155;
}

.interactive-notebook-frame {
  width: 100%;
  border: 1px solid #cfd7e3;
  border-radius: 10px;
  overflow: hidden;
  background: #fff;
}

.interactive-notebook-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-top: 14px;
}

.interactive-notebook-link {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 40px;
  padding: 0 14px;
  border: 1px solid #cbd5e1;
  border-radius: 999px;
  background: #fff;
  color: #0f172a;
  text-decoration: none;
  font-weight: 600;
}

.interactive-notebook-link:hover,
.interactive-notebook-link:focus-visible {
  border-color: #2563eb;
  color: #1d4ed8;
}

.notebook-page {
  max-width: 980px;
  margin: 0 auto;
}

.notebook-page-header {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 20px;
}

.notebook-page-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.notebook-page-link {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 40px;
  padding: 0 14px;
  border: 1px solid #cbd5e1;
  border-radius: 999px;
  background: #fff;
  color: #0f172a;
  text-decoration: none;
  font-weight: 600;
}

.notebook-page-link:hover,
.notebook-page-link:focus-visible {
  border-color: #2563eb;
  color: #1d4ed8;
}

.notebook-cell {
  margin: 0 0 18px;
  border: 1px solid #d7dfeb;
  border-radius: 12px;
  overflow: hidden;
  background: #fff;
}

.notebook-cell-label {
  padding: 8px 12px;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  color: #475569;
  background: #f8fafc;
  border-bottom: 1px solid #e2e8f0;
}

.notebook-cell-body {
  padding: 14px 16px;
}

.notebook-code {
  margin: 0;
  padding: 14px 16px;
  overflow-x: auto;
  background: #0f172a;
  color: #e2e8f0;
  font-size: 14px;
  line-height: 1.55;
  white-space: pre;
}

.notebook-output {
  margin: 0;
  padding: 14px 16px;
  border-top: 1px solid #e2e8f0;
  background: #f8fafc;
  color: #0f172a;
  font-size: 14px;
  line-height: 1.55;
  white-space: pre-wrap;
}
"""


def run(cmd):
  print(" ".join(cmd))
  subprocess.check_call(cmd)


def parse_bibliography_paths(tex_path: Path, tex_text: str):
  bibliography_files = []
  seen = set()

  def add_candidate(path_str: str):
    base = path_str.strip()
    if not base:
      return
    candidates = []
    raw_path = Path(base)
    if raw_path.is_absolute():
      candidates.append(raw_path)
    else:
      candidates.append(tex_path.parent / raw_path)
      candidates.append(Path(base))
    if raw_path.suffix.lower() != ".bib":
      if raw_path.is_absolute():
        candidates.append(Path(f"{base}.bib"))
      else:
        candidates.append(tex_path.parent / f"{base}.bib")
        candidates.append(Path(f"{base}.bib"))

    for candidate in candidates:
      resolved = candidate.resolve()
      if resolved.exists() and resolved not in seen:
        seen.add(resolved)
        bibliography_files.append(resolved)
        return

  for m in re.finditer(r"\\bibliography\{([^}]*)\}", tex_text):
    for item in m.group(1).split(","):
      add_candidate(item)

  for m in re.finditer(r"\\addbibresource\{([^}]*)\}", tex_text):
    add_candidate(m.group(1))

  default_bib = (tex_path.parent / "references.bib").resolve()
  if default_bib.exists() and default_bib not in seen:
    seen.add(default_bib)
    bibliography_files.append(default_bib)

  return bibliography_files


def extract_inline_bib_entries(tex_text: str):
  entries = []
  ranges = []
  for m in re.finditer(r"(?m)^[ \t]*@[A-Za-z][A-Za-z0-9_-]*\s*\{", tex_text):
    start = m.start()
    i = tex_text.find("{", start)
    if i < 0:
      continue
    depth = 0
    end = None
    for j in range(i, len(tex_text)):
      ch = tex_text[j]
      if ch == "{":
        depth += 1
      elif ch == "}":
        depth -= 1
        if depth == 0:
          end = j + 1
          break
    if end is None:
      continue
    entries.append(tex_text[start:end].strip())
    ranges.append((start, end))

  if not ranges:
    return tex_text, entries

  chunks = []
  prev = 0
  for start, end in ranges:
    chunks.append(tex_text[prev:start])
    prev = end
  chunks.append(tex_text[prev:])
  cleaned = "".join(chunks)
  return cleaned, entries


def sanitize_tex_for_citeproc(tex_text: str):
  tex_text = re.sub(
    r"(?m)^[ \t]*\\renewcommand\s*\{\\cite\}\s*(\[[^\]]*\])?\s*\{.*\}\s*$\n?",
    "",
    tex_text,
  )
  tex_text = re.sub(r"(?m)^[ \t]*\\bibliographystyle\{[^}]*\}\s*$\n?", "", tex_text)
  tex_text = re.sub(r"(?m)^[ \t]*\\bibliography\{[^}]*\}\s*$\n?", "", tex_text)
  tex_text = re.sub(r"(?m)^[ \t]*\\addbibresource\{[^}]*\}\s*$\n?", "", tex_text)
  return tex_text


def normalize_fquote_blocks(tex_text: str):
  # Replace custom fquote macro usage with portable LaTeX so pandoc renders
  # quotes cleanly (avoids stray macro artifacts in output).
  pattern = re.compile(
    r"\\begin\{fquote\}(?:\[([^\]]*)\])?(?:\[([^\]]*)\])?\s*(.*?)\s*\\end\{fquote\}",
    re.DOTALL,
  )

  def repl(match):
    author = (match.group(1) or "").strip()
    role = (match.group(2) or "").strip()
    quote_body = match.group(3).strip()

    footer = ""
    if author and role:
      footer = f" --- {author} ({role})"
    elif author:
      footer = f" --- {author}"
    elif role:
      footer = f" ({role})"

    return f"\\begin{{quote}}\\textit{{{quote_body}}}{footer}\\end{{quote}}"

  return pattern.sub(repl, tex_text)


def extract_includegraphics_widths(tex_text: str):
  # Extract width intents from LaTeX includegraphics commands so generated HTML
  # can respect source sizing.
  width_by_path = {}
  width_by_basename = {}
  pattern = re.compile(r"\\includegraphics(?:\s*\[([^\]]*)\])?\s*\{([^}]*)\}")

  for match in pattern.finditer(tex_text):
    options = (match.group(1) or "").strip()
    raw_path = (match.group(2) or "").strip()
    if not raw_path:
      continue

    width_pct = None
    width_match = re.search(
      r"width\s*=\s*([0-9]*\.?[0-9]+)\s*\\(?:line|text)width",
      options,
      re.IGNORECASE,
    )
    if width_match:
      try:
        width_pct = max(1.0, min(100.0, float(width_match.group(1)) * 100.0))
      except ValueError:
        width_pct = None
    elif re.search(r"width\s*=\s*\\(?:line|text)width", options, re.IGNORECASE):
      width_pct = 100.0

    if width_pct is None:
      continue

    normalized = raw_path.replace("\\", "/").strip()
    if normalized.startswith("./"):
      normalized = normalized[2:]
    normalized_key = unquote(normalized).lower()
    basename_key = Path(normalized_key).name

    width_by_path.setdefault(normalized_key, width_pct)
    if basename_key:
      width_by_basename.setdefault(basename_key, width_pct)

  return width_by_path, width_by_basename


def normalize_backtick_quotes(text: str):
  # Normalize LaTeX-style and mixed quote artifacts left after pandoc.
  normalized = text
  patterns = [
    (r"``([^`<]+?)''", r"“\1”"),
    (r"``([^`<]+?)\"", r"“\1”"),
    (r"``([^`<]+?)”", r"“\1”"),
    (r"``([^`<]+?)’’", r"“\1”"),
    (r"“([^”\"<]+?)\"", r"“\1”"),
    (r"“([^”<]+?)''", r"“\1”"),
    (r"“([^”<]+?)’’", r"“\1”"),
  ]
  for pattern, replacement in patterns:
    normalized = re.sub(pattern, replacement, normalized)
  return normalized


def normalize_course_numbers(text: str):
  return re.sub(r"\b8803\b", "6252", text)


def extract_command_argument(text: str, command: str):
  pattern = re.compile(rf"\\{re.escape(command)}\s*\{{", re.IGNORECASE)
  match = pattern.search(text)
  if not match:
    return ""

  brace_start = text.find("{", match.start())
  if brace_start < 0:
    return ""

  depth = 0
  for idx in range(brace_start, len(text)):
    ch = text[idx]
    if ch == "{":
      depth += 1
    elif ch == "}":
      depth -= 1
      if depth == 0:
        return text[brace_start + 1:idx].strip()
  return ""


def clean_title_candidate(raw_title: str):
  title = (raw_title or "").strip()
  if not title:
    return ""

  title = title.replace(r"\&", "&")
  title = title.replace("\n", " ")
  title = re.sub(r"\\\\(\[[^\]]*\])?", " ", title)
  title = re.sub(r"\\(?:vspace|hspace)\*?\{[^{}]*\}", " ", title, flags=re.IGNORECASE)

  prev = None
  while prev != title:
    prev = title
    title = re.sub(
      r"\\[A-Za-z@]+\*?(?:\[[^\]]*\])?\{([^{}]*)\}",
      r"\1",
      title,
    )

  title = re.sub(r"\\[A-Za-z@]+\*?", " ", title)
  title = title.replace("{", " ").replace("}", " ")
  title = re.sub(r"\[[^\]]*\]", " ", title)
  title = title.replace("---", " - ").replace("--", " - ")
  title = re.sub(r"\s+", " ", title).strip(" -:\t")

  lecture_suffix = re.search(r"Lecture\s+\d+\s*[:\-]\s*(.+)", title, re.IGNORECASE)
  if lecture_suffix:
    suffix = lecture_suffix.group(1).strip(" -:\t")
    if suffix:
      title = suffix

  if title.lower() in {"lecture title", "title"}:
    return ""
  if not re.search(r"[A-Za-z]{3,}", title):
    return ""

  return title


def extract_title(tex_path):
  text = normalize_course_numbers(tex_path.read_text(errors="ignore"))
  # Prefer the title from \lecture{N}{Title}{...}{...} and skip template placeholders.
  lecture_macro = re.compile(
    r"\\lecture\{\s*([^}]*)\s*\}\{\s*([^}]*)\s*\}\{\s*([^}]*)\s*\}\{\s*([^}]*)\s*\}"
  )
  for m in lecture_macro.finditer(text):
    title = clean_title_candidate(m.group(2))
    if title:
      return title

  latex_title = clean_title_candidate(extract_command_argument(text, "title"))
  if latex_title:
    return latex_title

  header_title = clean_title_candidate(extract_command_argument(text, "lhead"))
  if header_title:
    return header_title

  m = re.search(r"Lecture\s+\d+[:\-]?\s*(.*)", text)
  if m:
    fallback = clean_title_candidate(m.group(0))
    if fallback:
      return fallback

  directory_fallback = clean_title_candidate(tex_path.parent.name.replace("_", " "))
  if directory_fallback:
    return directory_fallback

  return tex_path.stem


def slugify_lecture_title(title: str):
  # Produce filesystem-safe names from lecture titles.
  clean = title.replace(r"\&", "and").replace("&", "and")
  clean = re.sub(r"[^A-Za-z0-9]+", "-", clean)
  clean = re.sub(r"-+", "-", clean).strip("-")
  return clean or "Untitled"


def lecture_tex_filename(out_html_name: str):
  return f"{Path(out_html_name).stem}.tex"


def lecture_number_from_dir(lec_dir: Path):
  name = lec_dir.name
  for pattern in (r"funml[_-]?l\s*(\d+)", r"lecture\s*(\d+)"):
    m = re.search(pattern, name, re.IGNORECASE)
    if m:
      return m.group(1)
  return ""


def lecture_dir_sort_key(lec_dir: Path):
  num = lecture_number_from_dir(lec_dir)
  if num:
    return (0, int(num))
  return (1, lec_dir.name.lower())


def is_excluded_tex_file(tex_path: Path):
  lowered_name = tex_path.name.lower()
  if lowered_name in EXCLUDED_TEX_FILENAMES:
    return True
  lowered_path = tex_path.as_posix().lower()
  return any(fragment in lowered_path for fragment in EXCLUDED_TEX_PATH_PARTIALS)


def is_candidate_lecture_dir(lec_dir: Path):
  name = lec_dir.name.lower()
  patterns = (
    r"^lecture\d+",
    r"^lecturexx",
    r"^funml[_-]?l\d+",
  )
  return any(re.search(pattern, name) for pattern in patterns)


def discover_lecture_dirs(src_root: Path):
  discovered = {}
  for tex_path in src_root.rglob("*.tex"):
    try:
      rel_parent = tex_path.parent.relative_to(src_root)
    except ValueError:
      continue
    if len(rel_parent.parts) > 2:
      continue
    if any(part.lower() == "img" for part in rel_parent.parts):
      continue
    lec_dir = tex_path.parent
    if not is_candidate_lecture_dir(lec_dir):
      continue
    discovered[lec_dir.resolve()] = lec_dir
  return sorted(discovered.values(), key=lecture_dir_sort_key)


def pick_main_tex(tex_files, lecture_number: str):
  def score(tex_path: Path):
    name = tex_path.stem.lower()
    points = 0
    if "in-class" in name or "exercise" in name or "solution" in name:
      points -= 100
    if "add-on" in name or "addon" in name:
      points -= 60
    if name == "main":
      points += 60
    if lecture_number:
      if f"lecture{lecture_number}" in name:
        points += 40
      if re.search(rf"\bl{lecture_number}\b", name):
        points += 35
      if f"l{lecture_number}_" in name:
        points += 35
    if "notes" in name:
      points += 20
    if "template" in name:
      points += 10
    return points

  return sorted(tex_files, key=lambda p: (-score(p), p.name.lower()))[0]


def ensure_landing_page_assets(out_root: Path):
  # If output is a fresh directory, seed it with the portal landing files.
  for filename in ("index.html", "styles.css", "script.js"):
    target = out_root / filename
    if target.exists():
      continue
    source = SCRIPT_ROOT / filename
    if source.exists():
      shutil.copy2(source, target)


def build_single_html(
  tex: Path,
  out_html_path: Path,
  out_root: Path,
  src_root: Path,
  title: str,
  source_tex_name: str,
  notebook_rules,
  notebooks_dir: Path,
  notebook_view_mode: str,
):
  tex_text = normalize_course_numbers(tex.read_text(errors="ignore"))
  includegraphics_width_by_path, includegraphics_width_by_basename = extract_includegraphics_widths(tex_text)
  bibliography_files = parse_bibliography_paths(tex, tex_text)
  tex_text, inline_bib_entries = extract_inline_bib_entries(tex_text)
  tex_text = sanitize_tex_for_citeproc(tex_text)
  tex_text = normalize_fquote_blocks(tex_text)
  has_citations = bool(re.search(r"\\cite[a-zA-Z*]*\{", tex_text))
  if has_citations and not bibliography_files and not inline_bib_entries:
    print(f"Warning: {tex.name} contains citations but no .bib source was found.")
  tex_text = re.sub(r"\{\\bf\s+([^}]+)\}", r"\\textbf{\1}", tex_text)
  tmp_tex = out_root / f"_{out_html_path.stem}.tex"
  tmp_tex.write_text(tex_text)

  tmp_html = out_root / f"_{out_html_path.stem}.html"
  tmp_bib = None
  if inline_bib_entries:
    tmp_bib = out_root / f"_{out_html_path.stem}.bib"
    tmp_bib.write_text("\n\n".join(inline_bib_entries) + "\n")
    bibliography_files.append(tmp_bib.resolve())

  cmd = [
    "pandoc",
    str(tmp_tex),
    "--mathjax",
    "--from=latex",
    "--to=html5",
    "--number-sections",
    "-o", str(tmp_html),
  ]
  if bibliography_files:
    cmd.extend(["--citeproc", "-M", "reference-section-title=References"])
    for bib in bibliography_files:
      cmd.extend(["--bibliography", str(bib)])

  run(cmd)

  body = tmp_html.read_text(errors="ignore")
  body = normalize_backtick_quotes(body)
  body, qanda_html = clean_lecture_body(
    body,
    tex.parent,
    src_root,
    out_html_path.parent,
    includegraphics_width_by_path,
    includegraphics_width_by_basename,
    notebook_rules,
    notebooks_dir,
    notebook_view_mode,
  )
  body = normalize_backtick_quotes(body)
  qanda_html = [normalize_backtick_quotes(section) for section in qanda_html]

  final_html = f"""<!doctype html>
<html>
<head>
  <meta charset="utf-8"/>
  <title>{title}</title>
  <link rel="stylesheet" href="../assets/style.css"/>
  <script defer src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"></script>
</head>
<body>
<main>
  {body}
</main>
</body>
</html>
"""

  out_html_path.write_text(final_html)
  tmp_html.unlink()
  tmp_tex.unlink()
  if tmp_bib and tmp_bib.exists():
    tmp_bib.unlink()
  return qanda_html


def is_local_path(path: str):
  if not path:
    return False
  if path.startswith(("#", "/", "mailto:", "tel:", "data:")):
    return False
  parsed = urlsplit(path)
  return not (parsed.scheme or parsed.netloc)


def normalize_web_path(path: str):
  parsed = urlsplit(path)
  encoded_path = quote(parsed.path, safe="/%._~()-")
  return urlunsplit(("", "", encoded_path, parsed.query, parsed.fragment))


def rendered_notebook_filename(ipynb_name: str):
  return f"{Path(ipynb_name).stem}_notebook.html"


def jupyterlite_notebook_href(ipynb_name: str):
  # Force a clean workspace on open so stale browser UI state
  # does not hide/collapse cells from prior sessions.
  query = urlencode({"path": f"notebooks/{ipynb_name}", "reset": "1"})
  return normalize_web_path(f"../assets/jupyterlite/lab/index.html?{query}")


def port_asset_path(path: str, source_dir: Path, src_root: Path, lecture_out_dir: Path):
  if not is_local_path(path):
    return path

  parsed = urlsplit(path)
  decoded = unquote(parsed.path).replace("\\", "/")
  cleaned = decoded[2:] if decoded.startswith("./") else decoded
  rel_path = Path(cleaned)

  # Avoid directory traversal in output paths.
  if any(part == ".." for part in rel_path.parts):
    rel_path = Path("imported") / source_dir.name / rel_path.name

  target_path = lecture_out_dir / rel_path
  if not target_path.exists():
    candidates = []
    if Path(decoded).is_absolute():
      candidates.append(Path(decoded))
    search_roots = [source_dir, src_root]
    try:
      search_roots.extend(p for p in src_root.iterdir() if p.is_dir())
    except OSError:
      pass
    for root in search_roots:
      candidates.append(root / decoded)
      candidates.append(root / cleaned)

    source_file = None
    for candidate in candidates:
      if candidate.exists() and candidate.is_file():
        source_file = candidate
        break

    if source_file:
      target_path.parent.mkdir(parents=True, exist_ok=True)
      shutil.copy2(source_file, target_path)

  rel_web_path = rel_path.as_posix()
  return urlunsplit(("", "", quote(rel_web_path, safe="/%._~()-"), parsed.query, parsed.fragment))


def rewrite_links_for_exercises(section_html: str, lectures_prefix: str):
  soup = BeautifulSoup(section_html, "html.parser")
  def is_qanda_heading(marker_id: str, marker_text: str):
    marker_id_norm = re.sub(r"[^a-z0-9]+", "", marker_id.lower())
    marker_text_norm = re.sub(r"[^a-z0-9]+", "", marker_text.lower())
    if "qanda" in marker_id_norm or "qasection" in marker_id_norm:
      return True
    if "qanda" in marker_text_norm or "qasection" in marker_text_norm:
      return True
    if re.search(r"\bq\s*(?:&|and)\s*a\b", marker_text.lower()):
      return True
    return False

  # Normalize extracted Q&A heading into a plain "Exercises" heading.
  for heading in soup.find_all(re.compile(r"^h[1-6]$")):
    heading_id = heading.get("id", "")
    heading_text = heading.get_text(" ", strip=True)
    if not is_qanda_heading(heading_id, heading_text):
      continue
    for num_span in heading.find_all("span", class_="header-section-number"):
      num_span.decompose()
    heading.attrs.pop("data-number", None)
    heading.attrs.pop("id", None)
    heading.clear()
    heading.append("Exercises")

  for tag in soup.find_all(src=True):
    src = tag.get("src", "")
    if is_local_path(src):
      src = src[2:] if src.startswith("./") else src
      tag["src"] = normalize_web_path(f"{lectures_prefix}{src}")
  for tag in soup.find_all(href=True):
    href = tag.get("href", "")
    if is_local_path(href):
      href = href[2:] if href.startswith("./") else href
      tag["href"] = normalize_web_path(f"{lectures_prefix}{href}")
  return str(soup)


def load_notebook_embed_rules(assets_dir: Path):
  rules_path = assets_dir / "notebooks" / "embed_map.json"
  if not rules_path.exists():
    return []

  try:
    payload = json.loads(rules_path.read_text(errors="ignore"))
  except json.JSONDecodeError as exc:
    print(f"Warning: could not parse notebook embed map {rules_path}: {exc}")
    return []

  if isinstance(payload, dict):
    raw_rules = payload.get("rules", [])
  elif isinstance(payload, list):
    raw_rules = payload
  else:
    return []

  rules = []
  for rule in raw_rules:
    if not isinstance(rule, dict):
      continue
    image_match = str(rule.get("image_match", "")).strip().lower()
    notebook_html = str(rule.get("notebook_html", "")).strip()
    if not image_match or not notebook_html:
      continue
    rules.append(
      {
        "image_match": image_match,
        "notebook_html": notebook_html,
        "notebook_ipynb": str(rule.get("notebook_ipynb", "")).strip(),
        "section_title": str(rule.get("section_title", "")).strip(),
        "description": str(rule.get("description", "")).strip(),
        "iframe_title": str(rule.get("iframe_title", "")).strip(),
        "iframe_height": rule.get("iframe_height", 680),
      }
    )
  return rules


def image_matches_rule(image_src: str, image_match: str):
  if any(ch in image_match for ch in "*?[]"):
    return fnmatch.fnmatch(image_src, image_match)
  return image_match in image_src


def resolve_notebook_ipynb(rule, notebooks_dir: Path):
  notebook_ipynb = str(rule.get("notebook_ipynb", "")).strip()
  if notebook_ipynb and (notebooks_dir / notebook_ipynb).exists():
    return notebook_ipynb

  notebook_html = str(rule.get("notebook_html", "")).strip()
  if not notebook_html:
    return ""

  fallback = f"{Path(notebook_html).stem}.ipynb"
  if (notebooks_dir / fallback).exists():
    return fallback
  return ""


def render_markdown_fragment(markdown_text: str):
  if not markdown_text.strip():
    return ""

  try:
    result = subprocess.run(
      ["pandoc", "--from=markdown", "--to=html5"],
      input=markdown_text,
      text=True,
      capture_output=True,
      check=True,
    )
    return result.stdout.strip()
  except (subprocess.CalledProcessError, FileNotFoundError):
    paragraphs = []
    for chunk in markdown_text.split("\n\n"):
      chunk = chunk.strip()
      if not chunk:
        continue
      paragraphs.append(f"<p>{html.escape(chunk)}</p>")
    return "\n".join(paragraphs)


def render_notebook_outputs(outputs):
  rendered = []
  for output in outputs or []:
    if not isinstance(output, dict):
      continue

    text = ""
    if output.get("output_type") == "stream":
      text = "".join(output.get("text", []))
    elif output.get("output_type") in {"execute_result", "display_data"}:
      data = output.get("data", {})
      if isinstance(data, dict):
        text = "".join(data.get("text/plain", []))
    elif output.get("output_type") == "error":
      traceback = output.get("traceback", [])
      if traceback:
        text = "\n".join(traceback)
      else:
        ename = output.get("ename", "Error")
        evalue = output.get("evalue", "")
        text = f"{ename}: {evalue}".strip()

    if text.strip():
      rendered.append(f'<pre class="notebook-output">{html.escape(text)}</pre>')
  return "".join(rendered)


def build_rendered_notebook_page(ipynb_path: Path, out_html_path: Path):
  try:
    payload = json.loads(ipynb_path.read_text(errors="ignore"))
  except json.JSONDecodeError as exc:
    print(f"Warning: could not parse notebook {ipynb_path}: {exc}")
    return

  cells = payload.get("cells", [])
  rendered_cells = []
  title = ipynb_path.stem.replace("_", " ")

  for cell in cells:
    if not isinstance(cell, dict):
      continue

    cell_type = cell.get("cell_type", "")
    source = "".join(cell.get("source", []))
    if not source.strip() and not cell.get("outputs"):
      continue

    if cell_type == "markdown":
      body = render_markdown_fragment(source)
      label = "Markdown"
      content = f'<div class="notebook-cell-body">{body}</div>'
    elif cell_type == "code":
      label = "Code"
      content = (
        f'<pre class="notebook-code"><code>{html.escape(source)}</code></pre>'
        f'{render_notebook_outputs(cell.get("outputs", []))}'
      )
    else:
      label = cell_type.title() or "Cell"
      content = f'<pre class="notebook-code"><code>{html.escape(source)}</code></pre>'

    rendered_cells.append(
      '<section class="notebook-cell">'
      f'<div class="notebook-cell-label">{label}</div>'
      f"{content}"
      "</section>"
    )

  notebook_title = title.title()
  out_html_path.write_text(
    f"""<!doctype html>
<html>
<head>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1"/>
  <title>{notebook_title}</title>
  <link rel="stylesheet" href="../style.css"/>
</head>
<body>
<main class="notebook-page">
  <div class="notebook-page-header">
    <div>
      <h1>{notebook_title}</h1>
      <p>Rendered notebook view for reading in the browser.</p>
    </div>
  </div>
  {''.join(rendered_cells) or '<p>This notebook is empty.</p>'}
</main>
</body>
</html>
"""
  )


def build_rendered_notebook_pages(notebooks_dir: Path):
  for ipynb_path in sorted(notebooks_dir.glob("*.ipynb")):
    out_html_path = notebooks_dir / rendered_notebook_filename(ipynb_path.name)
    build_rendered_notebook_page(ipynb_path, out_html_path)


def build_jupyterlite_site(notebooks_dir: Path, assets_out: Path, out_root: Path):
  jupyter_lite_bin = shutil.which("jupyter-lite")
  if not jupyter_lite_bin:
    local_user_bin = Path.home() / ".local" / "bin" / "jupyter-lite"
    if local_user_bin.exists():
      jupyter_lite_bin = str(local_user_bin)

  notebook_files = sorted(notebooks_dir.glob("*.ipynb"))
  if not jupyter_lite_bin or not notebook_files:
    return False
  try:
    probe = subprocess.run(
      [jupyter_lite_bin, "--help"],
      capture_output=True,
      text=True,
      check=False,
    )
    if probe.returncode != 0:
      return False
  except OSError:
    return False

  lite_out = assets_out / "jupyterlite"
  doit_db = out_root / ".jupyterlite.doit.db"
  pyodide_extension_dir = (
    Path.home()
    / ".local"
    / "share"
    / "jupyter"
    / "labextensions"
    / "@jupyterlite"
    / "pyodide-kernel-extension"
  )

  def ensure_pyodide_extension():
    if not pyodide_extension_dir.exists():
      return
    ext_target = lite_out / "extensions" / "@jupyterlite" / "pyodide-kernel-extension"
    ext_target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(pyodide_extension_dir, ext_target, dirs_exist_ok=True)

    config_path = lite_out / "jupyter-lite.json"
    if not config_path.exists():
      return
    try:
      payload = json.loads(config_path.read_text(errors="ignore"))
    except json.JSONDecodeError:
      return

    config_data = payload.setdefault("jupyter-config-data", {})
    federated = config_data.setdefault("federated_extensions", [])
    if any(item.get("name") == "@jupyterlite/pyodide-kernel-extension" for item in federated if isinstance(item, dict)):
      return

    remote_entry = None
    for candidate in sorted((ext_target / "static").glob("remoteEntry*.js")):
      remote_entry = candidate.name
      break
    if not remote_entry:
      return

    federated.append(
      {
        "name": "@jupyterlite/pyodide-kernel-extension",
        "extension": "./extension",
        "load": f"extensions/@jupyterlite/pyodide-kernel-extension/static/{remote_entry}",
      }
    )
    config_path.write_text(json.dumps(payload, indent=2))
  with tempfile.TemporaryDirectory(prefix="_jupyterlite_", dir=out_root) as lite_tmp:
    lite_dir = Path(lite_tmp)
    lite_content = lite_dir / "content" / "notebooks"
    lite_content.mkdir(parents=True, exist_ok=True)

    for ipynb_path in notebook_files:
      shutil.copy2(ipynb_path, lite_content / ipynb_path.name)

    try:
      run(
        [
          jupyter_lite_bin,
          "build",
          "--lite-dir",
          str(lite_dir),
          "--contents",
          str(lite_dir / "content"),
          "--output-dir",
          str(lite_out),
          "--apps",
          "lab",
          "--no-sourcemaps",
          "--no-unused-shared-packages",
        ]
        + (
          [
            "--LiteBuildConfig.federated_extensions",
            str(pyodide_extension_dir),
          ]
          if pyodide_extension_dir.exists()
          else []
        )
      )
    except subprocess.CalledProcessError:
      print("Warning: jupyter-lite build failed; falling back to rendered notebook pages.")
      return False

  if doit_db.exists():
    doit_db.unlink()

  ensure_pyodide_extension()

  return True


def build_notebook_views(notebooks_dir: Path, assets_out: Path, out_root: Path):
  def cleanup_rendered_notebook_pages():
    removed = 0
    for rendered in list(notebooks_dir.glob("*_notebook.html")):
      if not rendered.exists():
        continue
      rendered.unlink()
      removed += 1
    if removed:
      print(f"Removed {removed} rendered notebook fallback pages.")

  if build_jupyterlite_site(notebooks_dir, assets_out, out_root):
    cleanup_rendered_notebook_pages()
    return "jupyterlite"
  existing_jupyterlite = assets_out / "jupyterlite" / "lab" / "index.html"
  if existing_jupyterlite.exists():
    print("Warning: using existing jupyterlite build from assets/jupyterlite.")
    cleanup_rendered_notebook_pages()
    return "jupyterlite"

  build_rendered_notebook_pages(notebooks_dir)
  return "rendered"


def notebook_view_href_for(ipynb_name: str, notebook_view_mode: str):
  if notebook_view_mode == "jupyterlite":
    return jupyterlite_notebook_href(ipynb_name)
  return normalize_web_path(f"../assets/notebooks/{rendered_notebook_filename(ipynb_name)}")


def inject_interactive_notebooks(soup, notebook_rules, notebooks_dir: Path, notebook_view_mode: str):
  if not notebook_rules:
    return

  injected_iframes = {
    iframe.get("src", "")
    for iframe in soup.find_all("iframe", src=True)
  }

  for img in soup.find_all("img", src=True):
    src = unquote(img.get("src", "")).replace("\\", "/").lower()
    if not src:
      continue

    matched_rule = None
    for rule in notebook_rules:
      if not image_matches_rule(src, rule["image_match"]):
        continue
      notebook_html = rule["notebook_html"]
      if not (notebooks_dir / notebook_html).exists():
        continue
      matched_rule = rule
      break

    if not matched_rule:
      continue

    notebook_ipynb = resolve_notebook_ipynb(matched_rule, notebooks_dir)
    # Keep the lecture-page embed on the standalone interactive HTML demo.
    # The notebook itself is exposed separately via the "View notebook" link.
    iframe_src = normalize_web_path(f"../assets/notebooks/{matched_rule['notebook_html']}")
    if iframe_src in injected_iframes:
      continue

    insert_after = img
    if img.parent and img.parent.name == "p":
      insert_after = img.parent
    if (
      insert_after.parent
      and insert_after.parent.name == "div"
      and "minipage" in (insert_after.parent.get("class") or [])
    ):
      insert_after = insert_after.parent
    source_visual = insert_after

    section_title = matched_rule["section_title"] or "Interactive Notebook"
    description = matched_rule["description"] or (
      "Click inside the interactive plot to move the new point. "
      "Classification updates automatically."
    )
    iframe_title = matched_rule["iframe_title"] or section_title
    try:
      iframe_height = int(matched_rule["iframe_height"])
    except (TypeError, ValueError):
      iframe_height = 680
    block = soup.new_tag("section")
    block["class"] = ["interactive-notebook"]
    h = soup.new_tag("h3")
    h.string = section_title
    block.append(h)

    p = soup.new_tag("p")
    p.string = description
    block.append(p)

    iframe = soup.new_tag("iframe")
    iframe["src"] = iframe_src
    iframe["title"] = iframe_title
    iframe["loading"] = "lazy"
    iframe["scrolling"] = "no"
    iframe["class"] = ["interactive-notebook-frame"]
    iframe["style"] = f"height:{iframe_height}px;"
    block.append(iframe)

    actions = soup.new_tag("div")
    actions["class"] = ["interactive-notebook-actions"]

    if notebook_ipynb:
      notebook_link = soup.new_tag("a")
      notebook_link["class"] = ["interactive-notebook-link"]
      notebook_link["href"] = notebook_view_href_for(notebook_ipynb, notebook_view_mode)
      notebook_link["target"] = "_blank"
      notebook_link["rel"] = "noopener noreferrer"
      notebook_link.string = "View notebook"
      actions.append(notebook_link)

    if actions.contents:
      block.append(actions)

    insert_after.insert_after(block)
    source_visual.decompose()
    injected_iframes.add(iframe_src)


def sync_portal_index(index_path: Path, lecture_pages):
  if not index_path.exists():
    return False

  soup = BeautifulSoup(index_path.read_text(errors="ignore"), "html.parser")
  lecture_list = soup.find(class_="lecture-list")
  if lecture_list is None:
    return False

  hidden_keys = {"lecture0"}
  landing_entry = next((entry for entry in lecture_pages if entry[2].lower() == "lecture0"), None)
  display_lectures = [entry for entry in lecture_pages if entry[2].lower() not in hidden_keys]
  if not display_lectures:
    display_lectures = lecture_pages[:]

  initial_entry = landing_entry or (display_lectures[0] if display_lectures else None)

  has_landing_initial = bool(landing_entry)

  def build_lecture_item(idx: int | None, title: str, filename: str, media_key: str, label: str | None = None):
    a = soup.new_tag("a")
    classes = ["lecture-item"]
    if idx is None:
      classes.append("lecture-item--plain")
    if idx is None and has_landing_initial:
      classes.append("active")
    elif idx == 1 and not has_landing_initial:
      classes.append("active")
    a["class"] = classes
    a["data-lecture"] = f"lectures/{filename}"
    a["data-lecture-key"] = media_key
    a["data-meta"] = ""
    a["data-title"] = title
    if media_key.lower() == "lecture0":
      a["data-disable-slides"] = "true"
      a["data-hide-viewer-actions"] = "true"
    a["href"] = "#"
    a["role"] = "listitem"

    if idx is not None:
      num = soup.new_tag("span")
      num["class"] = "lecture-num"
      num.string = f"{idx:02d}"
      a.append(num)

    info = soup.new_tag("div")
    title_div = soup.new_tag("div")
    title_div["class"] = "lecture-title"
    title_div.string = label or title
    info.append(title_div)
    a.append(info)
    return a

  lecture_list.clear()
  if landing_entry:
    lecture_list.append(build_lecture_item(None, landing_entry[0], landing_entry[1], landing_entry[2], label="Preface"))
    lecture_list.append("\n")
  for idx, (title, filename, media_key) in enumerate(display_lectures, start=1):
    lecture_list.append(build_lecture_item(idx, title, filename, media_key))
    lecture_list.append("\n")

  sidebar_caption = soup.find(class_="sidebar-caption")
  if sidebar_caption is not None:
    sidebar_caption.string = f"{len(display_lectures)} sessions"

  lecture_frame = soup.find(id="lecture-frame")
  if lecture_frame is not None and initial_entry:
    lecture_frame["src"] = f"lectures/{initial_entry[1]}"

  lecture_title = soup.find(id="lecture-title")
  if lecture_title is not None and initial_entry:
    lecture_title.string = initial_entry[0]

  lecture_meta = soup.find(id="lecture-meta")
  if lecture_meta is not None:
    lecture_meta.string = ""

  index_path.write_text(str(soup))
  return True


def clean_lecture_body(
  body_html: str,
  source_dir: Path,
  src_root: Path,
  lecture_out_dir: Path,
  includegraphics_width_by_path,
  includegraphics_width_by_basename,
  notebook_rules,
  notebooks_dir: Path,
  notebook_view_mode: str,
):
  soup = BeautifulSoup(body_html, "html.parser")

  def scale_percent_style(style_text: str, factor: float):
    if not style_text:
      return style_text

    def repl(match):
      try:
        value = float(match.group(1))
      except ValueError:
        return match.group(0)
      scaled = max(1.0, min(100.0, value * factor))
      return f"{match.group(0).split(':', 1)[0]}:{scaled:.2f}%"

    return re.sub(r"(?:^|;)\s*(?:width|max-width)\s*:\s*([0-9]*\.?[0-9]+)\s*%", repl, style_text)

  # Pandoc emits top-level section numbers as "1", "2", ... after removing
  # shift/offset flags. Render them as "1.", "2.", ... for readability.
  for num_span in soup.find_all("span", class_="header-section-number"):
    value = num_span.get_text(strip=True)
    if re.fullmatch(r"\d+", value):
      num_span.string = f"{value}."

  # Normalize and port local asset paths so linked resources are published.
  for tag in soup.find_all(src=True):
    src = tag.get("src", "")
    if src:
      tag["src"] = port_asset_path(src, source_dir, src_root, lecture_out_dir)
  for tag in soup.find_all(href=True):
    href = tag.get("href", "")
    if href:
      tag["href"] = port_asset_path(href, source_dir, src_root, lecture_out_dir)
  for tag in soup.find_all("a", href=True):
    href = (tag.get("href", "") or "").strip()
    if not href or href.startswith("#"):
      continue
    tag["target"] = "_blank"
    existing_rel = tag.get("rel", [])
    if isinstance(existing_rel, str):
      existing_rel = existing_rel.split()
    rel_tokens = list(dict.fromkeys([*existing_rel, "noopener", "noreferrer"]))
    tag["rel"] = rel_tokens

  # Apply width from source LaTeX includegraphics options when available.
  for img in soup.find_all("img", src=True):
    src = unquote(img.get("src", "")).replace("\\", "/")
    if src.startswith("./"):
      src = src[2:]
    src_key = src.lower()
    basename_key = Path(src_key).name
    width_pct = includegraphics_width_by_path.get(src_key)
    if width_pct is None and basename_key:
      width_pct = includegraphics_width_by_basename.get(basename_key)
    if width_pct is not None:
      scaled_width = max(1.0, min(100.0, width_pct * INCLUDEGRAPHICS_WIDTH_SCALE))
      img["style"] = f"width:{scaled_width:.2f}%; max-width:{scaled_width:.2f}%; height:auto;"
      continue

    existing_style = img.get("style", "")
    if existing_style:
      img["style"] = scale_percent_style(existing_style, INCLUDEGRAPHICS_WIDTH_SCALE)

  inject_interactive_notebooks(soup, notebook_rules, notebooks_dir, notebook_view_mode)

  # Remove repeated boilerplate block that appears at the top of many lectures.
  boilerplate_keys = {
    "contributors:",
    "teaching assistants",
    "disclaimer",
    "license",
    "errata",
  }
  for p in soup.find_all("p"):
    strong = p.find("strong")
    if not strong:
      continue
    key = strong.get_text(" ", strip=True).strip().lower()
    if any(key.startswith(k) for k in boilerplate_keys):
      p.decompose()

  # Extract Q&A sections to publish them in Exercises instead of each lecture.
  def is_qanda_marker(marker_id: str, marker_text: str):
    marker_id_norm = re.sub(r"[^a-z0-9]+", "", marker_id.lower())
    marker_text_norm = re.sub(r"[^a-z0-9]+", "", marker_text.lower())

    if "qanda" in marker_id_norm or "qasection" in marker_id_norm:
      return True
    if "qanda" in marker_text_norm or "qasection" in marker_text_norm:
      return True
    if re.search(r"\bq\s*(?:&|and)\s*a\b", marker_text.lower()):
      return True
    return False

  def is_qanda_section(sec):
    sec_id = (sec.get("id") or "").lower()
    heading = sec.find(re.compile(r"^h[1-6]$"))
    heading_text = heading.get_text(" ", strip=True).lower() if heading else ""

    return is_qanda_marker(sec_id, heading_text)

  qanda_sections = []
  for sec in soup.find_all("section"):
    if is_qanda_section(sec):
      qanda_sections.append(str(sec))
      sec.decompose()

  # Fallback for outputs that are not wrapped in <section> (heading-based).
  headings = list(soup.find_all(re.compile(r"^h[1-6]$")))
  for heading in headings:
    heading_id = heading.get("id", "")
    heading_text = heading.get_text(" ", strip=True)
    if not is_qanda_marker(heading_id, heading_text):
      continue

    heading_level = int(heading.name[1])
    nodes = [heading]
    node = heading.next_sibling
    while node is not None:
      next_node = node.next_sibling
      if getattr(node, "name", None) and re.match(r"^h[1-6]$", node.name):
        if int(node.name[1]) <= heading_level:
          break
      nodes.append(node)
      node = next_node

    block_html = "".join(str(n) for n in nodes).strip()
    if block_html:
      qanda_sections.append(f"<section>{block_html}</section>")
    for n in nodes:
      n.extract()

  return str(soup), qanda_sections


def build_site(src_root: Path, out_root: Path, write_index: bool):
  lectures_out = out_root / "lectures"
  assets_out = out_root / "assets"
  exercises_out = assets_out / "exercises"
  notebooks_out = assets_out / "notebooks"

  lectures_out.mkdir(parents=True, exist_ok=True)
  assets_out.mkdir(parents=True, exist_ok=True)
  exercises_out.mkdir(parents=True, exist_ok=True)

  # CSS for lecture pages
  (assets_out / "style.css").write_text(CSS)

  # Copy images
  img_dirs = []
  root_img = src_root / "img"
  if root_img.exists():
    img_dirs.append(root_img)
  try:
    img_dirs.extend(p / "img" for p in src_root.iterdir() if (p / "img").exists())
  except OSError:
    pass
  for img_dir in img_dirs:
    shutil.copytree(img_dir, lectures_out / "img", dirs_exist_ok=True)

  notebook_rules = load_notebook_embed_rules(assets_out)
  notebook_view_mode = build_notebook_views(notebooks_out, assets_out, out_root)

  lecture_pages = []
  qanda_entries = []
  qanda_by_lecture = {}
  # Clean previously generated pages before rebuild.
  for old in lectures_out.glob("Lecture*.html"):
    old.unlink()
  for old in lectures_out.glob("Lecture*.tex"):
    old.unlink()
  # Ensure in-class exercise artifacts are not published.
  for old in lectures_out.glob("*_exercise*.html"):
    old.unlink()
  for old in exercises_out.glob("Lecture*.html"):
    old.unlink()

  for lec_dir in discover_lecture_dirs(src_root):
    if not lec_dir.is_dir():
      continue

    tex_files = [tex for tex in lec_dir.glob("*.tex") if not is_excluded_tex_file(tex)]
    excluded = [tex.name for tex in lec_dir.glob("*.tex") if is_excluded_tex_file(tex)]
    if excluded:
      print(f"Skipping excluded lecture sources in {lec_dir.name}: {', '.join(sorted(excluded))}")
    if not tex_files:
      continue

    lecture_number = lecture_number_from_dir(lec_dir)
    tex = pick_main_tex(tex_files, lecture_number)
    title = extract_title(tex)
    display_idx = len(lecture_pages) + 1
    lecture_slug = slugify_lecture_title(title)
    out_html = f"Lecture{display_idx}_{lecture_slug}.html"
    webpage_named_tex = next(
      (candidate for candidate in tex_files if candidate.name.lower() == lecture_tex_filename(out_html).lower()),
      None,
    )
    if webpage_named_tex is not None:
      tex = webpage_named_tex
      title = extract_title(tex) or title
      lecture_slug = slugify_lecture_title(title)
      out_html = f"Lecture{display_idx}_{lecture_slug}.html"
    media_key = f"Lecture{lecture_number}" if lecture_number else f"Lecture{display_idx}"
    lecture_key = Path(out_html).stem
    lecture_label = f"Lecture{display_idx}"
    source_tex_name = lecture_tex_filename(out_html)
    shutil.copy2(tex, lectures_out / source_tex_name)
    qanda_sections = build_single_html(
      tex,
      lectures_out / out_html,
      out_root,
      src_root,
      title,
      source_tex_name,
      notebook_rules,
      notebooks_out,
      notebook_view_mode,
    )
    qanda_by_lecture[lecture_key] = qanda_sections
    if qanda_sections:
      qanda_entries.append((lecture_label, title, qanda_sections))

    lecture_pages.append((title, out_html, media_key))

  # Build a shared Exercises page using all extracted Q&A sections.
  if qanda_entries:
    qanda_blocks = []
    for lecture_name, lecture_title, sections in qanda_entries:
      section_html = "\n".join(
        rewrite_links_for_exercises(section, "../lectures/")
        for section in sections
      )
      qanda_blocks.append(
        f"<section><h2>{lecture_name} - {lecture_title}</h2>{section_html}</section>"
      )
    exercises_body = "\n".join(qanda_blocks)
  else:
    exercises_body = "<p>No Q&A sections are currently available.</p>"

  exercises_html = f"""<!doctype html>
<html>
<head>
  <meta charset="utf-8"/>
  <title>FunML Exercises</title>
  <link rel="stylesheet" href="style.css"/>
  <script defer src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"></script>
</head>
<body>
<main>
  {exercises_body}
</main>
</body>
</html>
"""
  (assets_out / "exercises.html").write_text(exercises_html)

  # Build one exercises page per lecture so each lecture maps to its own Q&A.
  for lecture_title, out_html, _ in lecture_pages:
    lecture_key = Path(out_html).stem
    sections = qanda_by_lecture.get(lecture_key, [])
    body = (
      "\n".join(rewrite_links_for_exercises(section, "../../lectures/") for section in sections)
      if sections
      else "<p>No exercises posted for this lecture yet.</p>"
    )
    single_exercises_html = f"""<!doctype html>
<html>
<head>
  <meta charset="utf-8"/>
  <title>Exercises</title>
  <link rel="stylesheet" href="../style.css"/>
  <script defer src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"></script>
</head>
<body>
<main>
  {body}
</main>
</body>
</html>
"""
    (exercises_out / f"{lecture_key}.html").write_text(single_exercises_html)

  ensure_landing_page_assets(out_root)

  if write_index and not (out_root / "index.html").exists():
    links = "\\n".join(
      f'<li><a href="lectures/{f}">{t}</a></li>'
      for t, f, _ in lecture_pages
    )

    index_html = f"""<!doctype html>
<html>
<head>
  <meta charset="utf-8"/>
  <title>{PROJECT_TITLE}</title>
  <link rel="stylesheet" href="assets/style.css"/>
</head>
<body>
<main>
  <h1>{PROJECT_TITLE}</h1>
  <ul>
    {links}
  </ul>
</main>
</body>
</html>
"""

    (out_root / "index.html").write_text(index_html)

  # Keep the portal-style landing page synchronized with the latest lectures.
  synced = sync_portal_index(out_root / "index.html", lecture_pages)
  if not synced and write_index:
    print("Warning: portal landing page not found; wrote minimal index instead.")


def main():
  parser = argparse.ArgumentParser()
  parser.add_argument(
    "--src",
    default="source/raw",
    help="Path to extracted lecture source (default: source/raw)",
  )
  parser.add_argument(
    "--out",
    default=".",
    help="Output root for the website (default: current dir)",
  )
  parser.add_argument(
    "--write-index",
    action="store_true",
    help="Also generate index.html (off by default to avoid overwriting)",
  )
  args = parser.parse_args()

  src_root = Path(args.src).resolve()
  out_root = Path(args.out).resolve()

  build_site(src_root, out_root, args.write_index)
  print("✔ Lectures built → open lectures/*.html")


if __name__ == "__main__":
  main()
