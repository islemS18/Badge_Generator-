import os
import base64
import argparse
import pandas as pd
from pathlib import Path
from jinja2 import Template


SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".gif"}

def load_participants(excel_path: str) -> pd.DataFrame:
    df = pd.read_excel(excel_path, dtype=str)
    df.columns = df.columns.str.strip()

    col_map = {}
    for col in df.columns:
        lower = col.lower()
        if "cin" in lower or "carte" in lower or "national" in lower or "identit" in lower:
            col_map[col] = "CIN"
        elif ("nom" in lower or "name" in lower or "fam" in lower) and "pren" not in lower and "first" not in lower:
            col_map[col] = "Nom"
        elif "prenom" in lower or "prénom" in lower or "first" in lower:
            col_map[col] = "Prenom"
        elif "poste" in lower or "job" in lower or "fonction" in lower or "emploi" in lower:
            col_map[col] = "Poste"
        elif "code" in lower or "issat" in lower or "hazard" in lower:
            col_map[col] = "Code"

    df = df.rename(columns=col_map)

    required = ["CIN", "Nom", "Prenom", "Poste"]
    for r in required:
        if r not in df.columns:
            raise ValueError(f"Column '{r}' not found. Detected columns: {list(df.columns)}")

    if "Code" not in df.columns:
        df["Code"] = ""
    df["Code"] = df["Code"].fillna("")

    counter = 1
    for i, row in df.iterrows():
        if not str(row["Code"]).strip().lower().startswith("issat-"):
            df.at[i, "Code"] = f"issat-{counter:03d}"
            counter += 1

    return df.fillna("").reset_index(drop=True)


def build_photo_index(photos_dir: str) -> dict[str, str]:
    """
    Scan the folder and build a dict: { CIN_string: base64_data_uri }.
    Image files must be named exactly as the CIN (e.g. 12345678.jpg).
    Lookup is case-insensitive and ignores the extension.
    """
    index: dict[str, str] = {}
    folder = Path(photos_dir)

    if not folder.exists():
        raise FileNotFoundError(f"Photos folder not found: {photos_dir}")

    for file in folder.iterdir():
        if file.suffix.lower() not in SUPPORTED_EXTENSIONS:
            continue
        cin_key = file.stem.strip()          # filename without extension
        raw = file.read_bytes()
        ext = file.suffix.lower().lstrip(".")
        mime = "jpeg" if ext in ("jpg", "jpeg") else ext
        b64 = base64.b64encode(raw).decode("utf-8")
        data_uri = f"data:image/{mime};base64,{b64}"
        index[cin_key] = data_uri
        print(f"  [IMG] Indexed: {file.name} → CIN {cin_key}")

    return index

#Html Template 

CARD_TEMPLATE = """<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Badges Participants — ISSAT</title>
  <style>
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

    body {
      font-family: 'Segoe UI', Arial, sans-serif;
      background: #eef0f5;
      padding: 40px 20px;
    }

    h1 {
      text-align: center;
      color: #1a237e;
      font-size: 26px;
      font-weight: 800;
      letter-spacing: 2px;
      text-transform: uppercase;
      margin-bottom: 8px;
    }
    .subtitle {
      text-align: center;
      color: #888;
      font-size: 13px;
      margin-bottom: 36px;
    }

    .grid {
      display: flex;
      flex-wrap: wrap;
      gap: 32px;
      justify-content: center;
    }

    /* ══ CARD ══ */
    .card {
      width: 360px;
      border-radius: 18px;
      overflow: hidden;
      box-shadow: 0 8px 32px rgba(26,35,126,0.13);
      background: #fff;
      print-color-adjust: exact;
      -webkit-print-color-adjust: exact;
    }

  
    .card-header {
      background: linear-gradient(135deg, #0d1b6e 0%, #1a237e 50%, #3949ab 100%);
      padding: 22px 20px 18px;
      display: flex;
      align-items: stretch;
      gap: 18px;
      position: relative;
    }
    .card-header::after {
      content: '';
      position: absolute;
      bottom: -1px; left: 0; right: 0;
      height: 18px;
      background: #fff;
      border-radius: 18px 18px 0 0;
    }

    /* ── Photo ── */
    .photo-frame {
      width: 88px;
      height: 108px;
      border-radius: 10px;
      border: 3px solid rgba(255,255,255,0.75);
      overflow: hidden;
      flex-shrink: 0;
      background: #c5cae9;
      display: flex;
      align-items: center;
      justify-content: center;
      position: relative;
      z-index: 1;
    }
    .photo-frame img {
      width: 100%;
      height: 100%;
      object-fit: cover;
    }
    .photo-placeholder {
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 6px;
      color: #7986cb;
    }
    .photo-placeholder svg { opacity: 0.7; }
    .photo-placeholder span { font-size: 10px; text-align: center; font-weight: 600; }

    /* ── Header text ── */
    .header-info {
      flex: 1;
      color: #fff;
      display: flex;
      flex-direction: column;
      justify-content: center;
      position: relative;
      z-index: 1;
    }
    .institution-tag {
      font-size: 10px;
      letter-spacing: 2.5px;
      text-transform: uppercase;
      opacity: 0.75;
      margin-bottom: 6px;
    }
    .fullname {
      font-size: 17px;
      font-weight: 800;
      line-height: 1.25;
      word-break: break-word;
    }
    .job-pill {
      margin-top: 8px;
      font-size: 11px;
      font-weight: 600;
      background: rgba(255,255,255,0.18);
      border: 1px solid rgba(255,255,255,0.3);
      border-radius: 20px;
      padding: 4px 12px;
      display: inline-block;
      letter-spacing: 0.4px;
    }

    /* ── Card body ── */
    .card-body {
      padding: 20px 22px 22px;
    }

    .fields {
      display: flex;
      flex-direction: column;
      gap: 0;
      border: 1px solid #e8eaf0;
      border-radius: 10px;
      overflow: hidden;
      margin-bottom: 16px;
    }
    .field {
      display: flex;
      align-items: center;
      gap: 0;
      padding: 0;
      border-bottom: 1px solid #e8eaf0;
    }
    .field:last-child { border-bottom: none; }
    .field-label {
      font-size: 10px;
      color: #7986cb;
      text-transform: uppercase;
      letter-spacing: 1px;
      font-weight: 700;
      width: 90px;
      flex-shrink: 0;
      padding: 10px 12px;
      background: #f5f6fb;
      align-self: stretch;
      display: flex;
      align-items: center;
      border-right: 1px solid #e8eaf0;
    }
    .field-value {
      font-size: 13px;
      color: #1a237e;
      font-weight: 600;
      padding: 10px 14px;
      word-break: break-all;
    }

    /* ── Code badge ── */
    .code-badge {
      background: linear-gradient(90deg, #0d1b6e, #3949ab);
      border-radius: 10px;
      padding: 12px 18px;
      display: flex;
      align-items: center;
      justify-content: space-between;
    }
    .code-left { display: flex; flex-direction: column; gap: 2px; }
    .code-label {
      color: rgba(255,255,255,0.65);
      font-size: 9px;
      letter-spacing: 1.5px;
      text-transform: uppercase;
      font-weight: 700;
    }
    .code-value {
      color: #fff;
      font-size: 18px;
      font-weight: 800;
      letter-spacing: 3px;
      font-family: 'Courier New', monospace;
    }
    .code-icon {
      width: 36px;
      height: 36px;
      background: rgba(255,255,255,0.15);
      border-radius: 8px;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 18px;
    }

    /* ── Stats bar ── */
    .stats-bar {
      text-align: center;
      color: #aaa;
      font-size: 12px;
      margin-bottom: 28px;
    }
    .stats-bar b { color: #1a237e; }

    /* Print */
    @media print {
      body { background: white; padding: 10px; }
      .card { box-shadow: none; border: 1px solid #ddd; page-break-inside: avoid; margin-bottom: 20px; }
    }
  </style>
</head>
<body>

  <h1>🪪 Badges Participants</h1>
  <p class="subtitle">ISSAT — Session {{ generation_date }}</p>
  <p class="stats-bar">
    <b>{{ total }}</b> participant(s) &nbsp;·&nbsp;
    <b>{{ with_photo }}</b> avec photo &nbsp;·&nbsp;
    <b>{{ total - with_photo }}</b> sans photo
  </p>

  <div class="grid">
    {% for p in participants %}
    <div class="card">

      <div class="card-header">
        <div class="photo-frame">
          {% if p.photo %}
            <img src="{{ p.photo }}" alt="Photo de {{ p.prenom }} {{ p.nom }}">
          {% else %}
            <div class="photo-placeholder">
              <svg width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                <circle cx="12" cy="8" r="4"/><path d="M4 20c0-4 3.6-7 8-7s8 3 8 7"/>
              </svg>
              <span>Pas de<br>photo</span>
            </div>
          {% endif %}
        </div>
        <div class="header-info">
          <div class="institution-tag">ISSAT</div>
          <div class="fullname">{{ p.prenom }}<br>{{ p.nom }}</div>
          <div class="job-pill">{{ p.poste }}</div>
        </div>
      </div>

      <div class="card-body">
        <div class="fields">
          <div class="field">
            <span class="field-label">CIN</span>
            <span class="field-value">{{ p.cin }}</span>
          </div>
          <div class="field">
            <span class="field-label">Nom</span>
            <span class="field-value">{{ p.nom }}</span>
          </div>
          <div class="field">
            <span class="field-label">Prénom</span>
            <span class="field-value">{{ p.prenom }}</span>
          </div>
          <div class="field">
            <span class="field-label">Fonction</span>
            <span class="field-value">{{ p.poste }}</span>
          </div>
        </div>

        <div class="code-badge">
          <div class="code-left">
            <span class="code-label">Code Hazard</span>
            <span class="code-value">{{ p.code }}</span>
          </div>
          <div class="code-icon">⚠️</div>
        </div>
      </div>

    </div>
    {% endfor %}
  </div>

</body>
</html>
"""

def generate_html(participants_data: list[dict], output_html: str):
    from datetime import date
    with_photo = sum(1 for p in participants_data if p["photo"])
    tpl = Template(CARD_TEMPLATE)
    html = tpl.render(
        participants=participants_data,
        total=len(participants_data),
        with_photo=with_photo,
        generation_date=date.today().strftime("%d/%m/%Y"),
    )
    with open(output_html, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"\n HTML generated → {output_html}")


def main():
    parser = argparse.ArgumentParser(
        description="Generate HTML badge cards from an Excel file + a folder of photos."
    )
    parser.add_argument("excel",      help="Path to the Excel file (.xlsx)")
    parser.add_argument("photos_dir", help="Path to the folder containing photos (filename = CIN)")
    parser.add_argument("--output",   default="badges.html", help="Output HTML file (default: badges.html)")
    args = parser.parse_args()

    print(f" Loading participants from: {args.excel}")
    df = load_participants(args.excel)
    print(f"   → {len(df)} participant(s) loaded.")

    print(f"\n Scanning photos folder: {args.photos_dir}")
    photo_index = build_photo_index(args.photos_dir)
    print(f"   → {len(photo_index)} image(s) found.")

    print("\n Matching participants ↔ photos...")
    participants_data = []
    found = 0
    for _, row in df.iterrows():
        cin = str(row["CIN"]).strip()
        data_uri = photo_index.get(cin, "")
        if data_uri:
            found += 1
            print(f"     {cin} → photo matched")
        else:
            print(f"     {cin} → no photo found")
        participants_data.append({
            "cin":    cin,
            "nom":    str(row["Nom"]).strip(),
            "prenom": str(row["Prenom"]).strip(),
            "poste":  str(row["Poste"]).strip(),
            "code":   str(row["Code"]).strip(),
            "photo":  data_uri,
        })
    print(f"\n   {found}/{len(df)} photo(s) matched.")

    # 4. Generate HTML
    generate_html(participants_data, args.output)
    print(f" Done! Open '{args.output}' in any browser to view or print.\n")


if __name__ == "__main__":
    main()
