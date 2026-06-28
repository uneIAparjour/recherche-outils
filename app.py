"""Voyage au pays du non-écrit — Audit sémantique des réponses LLM.

Streamlit app propulsée par l'API Albert.
"""

import json
import re

import httpx
import streamlit as st

st.set_page_config(
    page_title="Voyage au pays du non-écrit",
    page_icon="◇",
    layout="centered",
)

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

ALBERT_API_KEY = st.secrets.get("ALBERT_API_KEY", "")
ALBERT_BASE_URL = st.secrets.get("ALBERT_BASE_URL", "https://albert.api.etalab.gouv.fr/v1")
LLM_MODEL = st.secrets.get("LLM_MODEL", "mistralai/Mistral-Small-3.2-24B-Instruct-2506")

CATEGORIES = [
    (
        "connotation", "Connotation",
        "Charges affectives et jugements de valeur portés par le choix des mots, "
        "au-delà de leur sens littéral.",
        "#F59E0B",
    ),
    (
        "subtext", "Sous-texte",
        "Message implicite véhiculé par le ton, la posture ou la mise en scène du propos.",
        "#A855F7",
    ),
    (
        "implicature", "Implicature",
        "Ce que le texte laisse entendre sans l'affirmer, par sous-entendu logique "
        "ou conversationnel.",
        "#3B82F6",
    ),
    (
        "defacto", "De facto",
        "Affirmations présentées comme des faits établis, sans source ni nuance, "
        "qui mériteraient d'être qualifiées.",
        "#EF4444",
    ),
    (
        "implementation", "Détail d'implémentation",
        "Conditions matérielles, techniques ou organisationnelles nécessaires "
        "mais passées sous silence.",
        "#10B981",
    ),
    (
        "omission", "Omission pure",
        "Dimensions absentes du texte alors qu'elles sont structurantes "
        "pour le sujet traité.",
        "#EC4899",
    ),
]

AUDIT_SYSTEM_PROMPT = """Tu es un auditeur sémantique spécialisé dans la détection des implicites, des non-dits et des omissions dans les réponses produites par des modèles de langage (LLM).

Étant donné une QUESTION posée par un utilisateur et la RÉPONSE produite par un LLM, tu dois identifier tout ce que la réponse implique sans le dire, suppose sans l'expliciter, ou omet.

Tu structures ton analyse selon 6 catégories issues de l'ontologie Wikidata de l'implicite (travail d'Arthur Sarazin) :

1. **Connotation** — Ce que les mots choisis véhiculent sans le dire (charge positive/négative, registre, cadrage idéologique)
2. **Sous-texte** — L'intention ou le positionnement sous-jacent non formulé (biais de présentation, angle éditorial)
3. **Implicature** — Ce qui découle logiquement de ce qui est écrit mais n'est pas explicitement tiré comme conclusion
4. **De facto** — Ce qui est vrai en pratique mais non reconnu dans la réponse (réalités de terrain ignorées)
5. **Détail d'implémentation** — Ce qu'il faudrait savoir pour agir concrètement à partir de cette réponse
6. **Omission pure** — Les angles, perspectives, objections ou faits simplement non abordés

INSTRUCTIONS :
- Pour chaque catégorie, liste les éléments trouvés. Si une catégorie est vide, renvoie un tableau vide [].
- Sois précis et actionnable : cite les passages concernés quand pertinent.

Pour la SYNTHÈSE, rédige un paragraphe structuré (4 à 6 phrases) qui :
- Identifie le principal angle mort de la réponse
- Explique pourquoi cet angle mort est problématique pour le lecteur
- Indique ce que le lecteur risque de croire, décider ou faire à tort s'il ne perçoit pas ces implicites
- Évalue le niveau de fiabilité apparente vs. réelle de la réponse
- Termine en indiquant le nombre total de non-dits identifiés

Pour l'INSTRUCTION DE CORRECTION, rédige une consigne précise et directement utilisable que l'utilisateur pourra copier-coller et envoyer au modèle d'origine pour lui demander de compléter sa réponse. Cette consigne doit :
- Lister les points spécifiques à expliciter
- Demander au modèle de traiter les omissions identifiées
- Être formulée comme une instruction à un LLM (à la deuxième personne)

Réponds UNIQUEMENT en JSON valide avec cette structure exacte :
{
  "connotation": ["élément 1", "élément 2"],
  "subtext": ["élément 1"],
  "implicature": ["élément 1", "élément 2"],
  "defacto": ["élément 1"],
  "implementation": ["élément 1", "élément 2"],
  "omission": ["élément 1", "élément 2", "élément 3"],
  "synthesis": "Paragraphe de synthèse développé...",
  "correction_prompt": "Instruction à copier-coller pour le modèle d'origine..."
}"""

# ---------------------------------------------------------------------------
# Style — hifi from Claude Design handoff
# ---------------------------------------------------------------------------

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Instrument+Serif:ital@0;1&family=Spline+Sans:wght@400;500;600;700&display=swap');

/* Header */
.vnt-title {
  font-family: 'Instrument Serif', Georgia, serif;
  font-weight: 400; font-size: 64px; line-height: 1.02;
  letter-spacing: -0.5px; margin: 0 0 18px;
}
.vnt-title .l1 { color: #fefefe; }
.vnt-title .l2 { font-style: italic; color: #E67E22; }
.vnt-subtitle {
  margin: 0 0 40px; max-width: 600px;
  font-family: 'Spline Sans', sans-serif;
  font-size: 17px; line-height: 1.55; color: #c2c3c8;
}

/* Synthesis callout */
.vnt-synth {
  border-left: 3px solid #E67E22;
  background: rgba(230,126,34,0.15);
  border-radius: 0 8px 8px 0;
  padding: 18px 22px; margin-bottom: 28px;
}
.vnt-synth-label {
  font-family: 'Spline Sans', sans-serif;
  font-size: 12px; font-weight: 700; letter-spacing: 1px;
  text-transform: uppercase; color: #f39c3e; margin-bottom: 8px;
}
.vnt-synth-text {
  font-family: 'Spline Sans', sans-serif;
  font-size: 15px; line-height: 1.6; color: #fefefe; margin: 0;
}

/* Section heading */
.vnt-section-head {
  display: flex; justify-content: space-between; align-items: baseline;
  margin-bottom: 18px;
}
.vnt-section-title {
  font-family: 'Instrument Serif', Georgia, serif;
  font-style: italic; font-weight: 400; font-size: 30px;
  color: #fefefe; margin: 0;
}
.vnt-section-count {
  font-family: 'Spline Sans', sans-serif;
  font-size: 13px; color: #7a7b80;
}

/* Category cards */
.vnt-card {
  background: #202023; border: 1px solid #3a3f44;
  border-left-width: 3px; border-left-style: solid;
  border-radius: 0 10px 10px 0; padding: 18px 22px; margin-bottom: 14px;
}
.vnt-card-head {
  display: flex; align-items: center; gap: 10px; margin-bottom: 11px;
}
.vnt-card-dot {
  width: 9px; height: 9px; border-radius: 50%; flex-shrink: 0;
}
.vnt-card-title {
  font-family: 'Spline Sans', sans-serif;
  font-size: 16px; font-weight: 700; color: #fefefe;
}
.vnt-card-pill {
  margin-left: auto; padding: 3px 10px; border-radius: 20px;
  font-family: 'Spline Sans', sans-serif;
  font-size: 12px; font-weight: 600;
}
.vnt-card-items {
  margin: 0; padding-left: 0; list-style: none;
  display: flex; flex-direction: column; gap: 9px;
}
.vnt-card-items li {
  font-family: 'Spline Sans', sans-serif;
  font-size: 14.5px; line-height: 1.55; color: #c2c3c8;
  padding-left: 16px; position: relative;
}

/* Tooltip */
.vnt-tip { position: relative; display: inline-flex; align-items: center; cursor: help; }
.vnt-tip-dot {
  width: 16px; height: 16px; border-radius: 50%;
  border: 1px solid #7a7b80; color: #7a7b80;
  font-size: 11px; font-weight: 700;
  display: inline-flex; align-items: center; justify-content: center;
}
.vnt-tipbox {
  visibility: hidden; opacity: 0; transition: opacity .15s ease;
  position: absolute; bottom: 140%; left: 50%; transform: translateX(-50%);
  width: 240px; background: #2a2f33; border: 1px solid #3a3f44;
  border-radius: 8px; padding: 10px 12px;
  font-family: 'Spline Sans', sans-serif;
  font-size: 12.5px; line-height: 1.5; color: #c2c3c8;
  z-index: 5; box-shadow: 0 8px 24px rgba(0,0,0,0.4);
}
.vnt-tip:hover .vnt-tipbox { visibility: visible; opacity: 1; }

/* Instruction block */
.vnt-instr {
  margin-top: 32px;
  border-left: 3px solid #10B981;
  background: rgba(16,185,129,0.08);
  border-radius: 0 10px 10px 0; padding: 20px 22px;
}
.vnt-instr-label {
  font-family: 'Spline Sans', sans-serif;
  font-size: 12px; font-weight: 700; letter-spacing: 1px;
  text-transform: uppercase; color: #10B981; margin-bottom: 12px;
}
.vnt-instr-pre {
  margin: 0; background: #15191c; border: 1px solid #3a3f44;
  border-radius: 8px; padding: 18px;
  font-family: 'SF Mono', Menlo, Consolas, monospace;
  font-size: 13.5px; line-height: 1.65; color: #c2c3c8;
  white-space: pre-wrap; overflow-x: auto;
}

/* Footer */
.vnt-footer {
  margin-top: 72px; padding: 28px 0 56px;
  border-top: 1px solid #3a3f44;
  font-family: 'Spline Sans', sans-serif;
  font-size: 13px; line-height: 1.7; color: #7a7b80; text-align: center;
}
.vnt-footer a { color: #E67E22; text-decoration: none; }
.vnt-footer a:hover { text-decoration: underline; }
.vnt-footer .name { color: #c2c3c8; }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------

st.markdown(
    '<h1 class="vnt-title"><span class="l1">Voyage au pays</span><br>'
    '<span class="l2">du non-écrit</span></h1>',
    unsafe_allow_html=True,
)
st.markdown(
    '<p class="vnt-subtitle">Audit des implicites, sous-textes et angles morts '
    'dans une réponse de modèle de langage.</p>',
    unsafe_allow_html=True,
)

st.markdown(
    "Vous avez une réponse produite par un modèle de langage (ChatGPT, Claude, Gemini, Mistral…) ? "
    "Collez-la ci-dessous pour en révéler les non-dits."
)

# ---------------------------------------------------------------------------
# API call
# ---------------------------------------------------------------------------

def call_albert(messages: list[dict]) -> str:
    if not ALBERT_API_KEY:
        st.error("Clé API Albert non configurée dans les secrets Streamlit.")
        st.stop()
    resp = httpx.post(
        f"{ALBERT_BASE_URL}/chat/completions",
        headers={"Authorization": f"Bearer {ALBERT_API_KEY}", "Content-Type": "application/json"},
        json={"model": LLM_MODEL, "messages": messages, "temperature": 0.3},
        timeout=90,
    )
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]


def run_audit(question: str, answer: str) -> dict:
    user_content = (
        f"QUESTION : {question}\n\nRÉPONSE DU LLM :\n{answer}"
        if question
        else f"RÉPONSE DU LLM :\n{answer}"
    )
    messages = [
        {"role": "system", "content": AUDIT_SYSTEM_PROMPT},
        {"role": "user", "content": user_content},
    ]
    raw = call_albert(messages)
    json_str = raw
    match = re.search(r"```(?:json)?\s*([\s\S]*?)```", raw)
    if match:
        json_str = match.group(1)
    return json.loads(json_str.strip())


def format_export(audit: dict, question: str, answer: str) -> str:
    lines = ["# Audit de l'implicite — Résultats\n"]
    if question:
        lines.append(f"## Question analysée\n{question}\n")
    lines.append(f"## Réponse auditée\n{answer}\n")
    lines.append("---\n")
    if audit.get("synthesis"):
        lines.append(f"## Synthèse\n{audit['synthesis']}\n")
    for cat_id, label, tip, _ in CATEGORIES:
        items = audit.get(cat_id, [])
        lines.append(f"### {label}")
        if items:
            for item in items:
                lines.append(f"- {item}")
        else:
            lines.append("_Rien de notable._")
        lines.append("")
    if audit.get("correction_prompt"):
        lines.append("---\n")
        lines.append("## Instruction de correction\n")
        lines.append("Copiez-collez cette consigne dans votre conversation avec le modèle d'origine :\n")
        lines.append(f"> {audit['correction_prompt']}\n")
    lines.append(
        "---\n_Généré par [Voyage au pays du non-écrit](https://github.com/uneIAparjour/non-ecrit) "
        "— CC BY 4.0 Bertrand Formet pour [uneIAparjour](https://uneIAparjour.fr)_"
    )
    return "\n".join(lines)


def _hex_to_rgba(hex_color: str, alpha: float) -> str:
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"rgba({r},{g},{b},{alpha})"


def render_results(audit: dict, question: str = "", answer: str = ""):
    # Synthesis
    if audit.get("synthesis"):
        st.markdown(
            '<div class="vnt-synth">'
            '<div class="vnt-synth-label">Synthèse de l\'audit</div>'
            f'<p class="vnt-synth-text">{audit["synthesis"]}</p>'
            '</div>',
            unsafe_allow_html=True,
        )

    # Section heading
    total = sum(len(audit.get(c[0], [])) for c in CATEGORIES)
    st.markdown(
        '<div class="vnt-section-head">'
        '<h2 class="vnt-section-title">Le non-écrit révélé</h2>'
        f'<span class="vnt-section-count">6 catégories · {total} non-dits</span>'
        '</div>',
        unsafe_allow_html=True,
    )

    # Cards
    for cat_id, label, tip, color in CATEGORIES:
        items = audit.get(cat_id, [])
        count = len(items)
        bg = _hex_to_rgba(color, 0.15)

        items_html = ""
        if items:
            lis = "".join(
                f'<li><span style="position:absolute;left:0;top:0;color:{color};">•</span>{item}</li>'
                for item in items
            )
            items_html = f'<ul class="vnt-card-items">{lis}</ul>'

        st.markdown(
            f'<div class="vnt-card" style="border-left-color:{color}">'
            f'<div class="vnt-card-head">'
            f'<span class="vnt-card-dot" style="background:{color}"></span>'
            f'<span class="vnt-card-title">{label}</span>'
            f'<span class="vnt-tip"><span class="vnt-tip-dot">?</span>'
            f'<span class="vnt-tipbox">{tip}</span></span>'
            f'<span class="vnt-card-pill" style="color:{color};background:{bg}">{count}</span>'
            f'</div>'
            f'{items_html}'
            f'</div>',
            unsafe_allow_html=True,
        )

    # Instruction block
    if audit.get("correction_prompt"):
        st.markdown(
            '<div class="vnt-instr">'
            '<div class="vnt-instr-label">Instruction à renvoyer au modèle d\'origine</div>'
            f'<pre class="vnt-instr-pre">{audit["correction_prompt"]}</pre>'
            '</div>',
            unsafe_allow_html=True,
        )

    # Export
    export_md = format_export(audit, question, answer)
    st.download_button(
        label="↓ Exporter l'audit (Markdown)",
        data=export_md,
        file_name="audit-implicites.md",
        mime="text/markdown",
        use_container_width=True,
    )

# ---------------------------------------------------------------------------
# Form
# ---------------------------------------------------------------------------

question = st.text_area(
    "Contexte / question posée — *optionnel*",
    placeholder="La question initiale ou le contexte dans lequel la réponse a été produite...",
    height=80,
)
answer = st.text_area(
    "**Réponse à auditer**",
    placeholder="Collez ici la réponse du modèle à analyser...",
    height=220,
)
if st.button("Révéler le non-écrit →", type="primary", use_container_width=True):
    if not answer.strip():
        st.warning("Veuillez coller la réponse à auditer.")
    else:
        with st.spinner("Analyse des implicites en cours…"):
            try:
                q = question.strip()
                a = answer.strip()
                audit = run_audit(q, a)
                render_results(audit, q, a)
            except Exception as e:
                st.error(f"Erreur : {e}")

# ---------------------------------------------------------------------------
# Footer
# ---------------------------------------------------------------------------

st.markdown(
    '<div class="vnt-footer">'
    '<div>Inspiré par <a href="https://www.linkedin.com/pulse/voyage-au-pays-du-non-%C3%A9crit-arthur-sarazin-phd-hwswe" '
    'target="_blank">Voyage au pays du non-écrit</a> d\'<span class="name">Arthur Sarazin</span>'
    f'</div><div>Modèle <span class="name">{LLM_MODEL}</span> via l\'<a href="https://albert.api.etalab.gouv.fr" '
    'target="_blank">API Albert</a>'
    ' · <a href="https://github.com/uneIAparjour/non-ecrit" target="_blank">GitHub</a></div>'
    '<div style="margin-top:8px;">CC BY 4.0 — <span class="name">Bertrand Formet</span> pour '
    '<a href="https://uneIAparjour.fr" target="_blank">uneIAparjour.fr</a></div>'
    '</div>',
    unsafe_allow_html=True,
)
