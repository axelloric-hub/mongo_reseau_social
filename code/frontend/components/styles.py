"""
styles.py - Design system central : jetons (couleurs, rayons, espacements) et CSS global.

Ce module existe pour qu'aucune page ne contienne de CSS : tout le rendu visuel est defini ici,
une seule fois, puis injecte par injecter(). Principe : Streamlit sert de moteur ; on masque son
habillage par defaut et on style (1) des conteneurs a cle (classe st-key-...) pour les cartes,
(2) les boutons dont la cle commence par un prefixe (nav_, ico-<icone>__) pour y ajouter une
icone Lucide, (3) st.pills pour les filtres et les onglets.

Convention de cles (le CSS s'appuie dessus) :
  card_*            conteneur affiche comme une carte blanche
  nav_<page>        bouton de navigation de la barre laterale
  ico-<icone>__*    bouton d'action avec une icone Lucide devant le libelle
  tabs_*            st.pills affiche comme des onglets soulignes
  champ-recherche_* champ de texte avec loupe
  conv_* / convbtn_ ligne de conversation cliquable (bouton invisible superpose)
"""
import streamlit as st

from frontend.components.icons import fond_champ, masque

# --- Jetons du design system ---------------------------------------------------------------------
COULEURS = {
    "navy": "#0F172A", "fond": "#F8FAFC", "carte": "#FFFFFF", "bordure": "#E2E8F0",
    "primaire": "#3B82F6", "primaire-fonce": "#2563EB", "primaire-pale": "#EFF6FF", "primaire-bord": "#BFDBFE",
    "danger": "#EF4444", "danger-pale": "#FEF2F2", "succes": "#22C55E", "succes-pale": "#DCFCE7", "succes-texte": "#15803D",
    "alerte": "#F59E0B", "alerte-pale": "#FEF3C7",
    "texte": "#0F172A", "texte-2": "#64748B", "texte-3": "#94A3B8", "surface": "#F1F5F9",
}

# Icones des boutons de navigation (cle du bouton -> icone Lucide)
ICONES_NAV = {"fil": "home", "profil": "user", "amis": "users", "groupes": "users-round", "messages": "message-circle",
              "notifications": "bell", "confidentialite": "shield", "supervision": "eye",
              "parametres": "settings", "deconnexion": "log-out"}

# Icones disponibles pour les boutons d'action : key="ico-<nom>__xxx"
ICONES_BOUTONS = ["thumbs-up", "message-circle", "share-2", "ellipsis", "image", "hash", "plus", "pencil", "trash-2",
                  "send", "user-plus", "check", "check-check", "arrow-left", "x", "corner-down-right", "users", "lock", "eye",
                  "chevron-left", "chevron-right", "search"]


def _jetons_css():
    return ":root{" + "".join("--%s:%s;" % (k, v) for k, v in COULEURS.items()) + "}"


IMPORT_POLICE = "@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');"

CSS_BASE = """

/* ===== 1. Base : police uniquement a la racine (ne jamais forcer 'span', elle porte les icones Streamlit) ===== */
.stApp, .stApp button, .stApp input, .stApp textarea { font-family: 'Inter', system-ui, -apple-system, 'Segoe UI', Roboto, sans-serif; }
.stApp { background: var(--fond); color: var(--texte); font-size: 14px; line-height: 1.5; -webkit-font-smoothing: antialiased; }
[data-testid="stHeader"] { background: transparent; height: 2.5rem; }
/* on masque les actions Streamlit (deploy, menu) mais PAS la barre qui contient le bouton d'ouverture du menu mobile */
[data-testid="stToolbarActions"], [data-testid="stAppDeployButton"], [data-testid="stMainMenu"], [data-testid="stDeployButton"], [data-testid="stStatusWidget"], footer, #MainMenu { display: none !important; }
[data-testid="stExpandSidebarButton"] { background: #fff; border: 1px solid var(--bordure); border-radius: 10px; color: var(--navy); }
[data-testid="stExpandSidebarButton"]:hover { background: var(--surface); }
[data-testid="stMainBlockContainer"] { max-width: 1120px; padding: 24px 40px 64px; }
[data-testid="stMainBlockContainer"] [data-testid="stVerticalBlock"] { gap: 16px; }
/* Streamlit comprime les elements plus hauts que leur rangee (ex. colonnes centrees) : on l'interdit */
[data-testid="stElementContainer"], [data-testid="stLayoutWrapper"] { flex-shrink: 0; }
[data-testid="stMarkdown"], [data-testid="stMarkdown"] > div { height: auto; min-height: min-content; flex-shrink: 0; }
/* Streamlit applique margin-bottom:-1rem a tout bloc Markdown (il annule la marge du dernier <p>) :
   notre HTML n'a pas de <p>, ce qui rognait 16 px de hauteur et faisait deborder chaque bloc sur le suivant */
[data-testid="stMarkdownContainer"] { margin-bottom: 0 !important; }
.stApp h1, .stApp h2, .stApp h3, .stApp h4 { color: var(--texte); letter-spacing: -0.01em; }
.stApp p { margin: 0; }
.stApp a { color: var(--primaire-fonce); }
.ico { flex: none; vertical-align: middle; }
/* le bloc <style> injecte par Streamlit ne doit pas creer d'espace dans la mise en page */
[data-testid="stElementContainer"]:has(style) { display: none; }

/* ===== 2. En-tete de page et titres ===== */
.page-header { margin-bottom: 4px; }
.page-title { font-size: 32px; font-weight: 700; line-height: 1.2; letter-spacing: -0.02em; color: var(--texte); margin: 0; }
.page-subtitle { font-size: 14px; color: var(--texte-2); margin-top: 4px; }
.section-title { font-size: 22px; font-weight: 700; letter-spacing: -0.01em; margin: 8px 0 0; }
.card-title { font-size: 16px; font-weight: 600; color: var(--texte); line-height: 1.3; }
.card-text { font-size: 14px; color: var(--texte-2); margin-top: 2px; }
.small { font-size: 12.5px; color: var(--texte-2); }
.muted { color: var(--texte-3); }

/* ===== 3. Barre laterale ===== */
[data-testid="stSidebar"] { background: var(--navy); border-right: 0; min-width: 264px; max-width: 264px; }
[data-testid="stSidebar"] [data-testid="stSidebarUserContent"] { padding: 4px 12px 16px; }
[data-testid="stSidebar"] [data-testid="stVerticalBlock"] { gap: 4px; }
[data-testid="stSidebar"] p, [data-testid="stSidebar"] span, [data-testid="stSidebar"] label { color: #CBD5E1; }
[data-testid="stSidebarCollapseButton"] button, [data-testid="stExpandSidebarButton"] button { color: #94A3B8; }
.user-card { display: flex; align-items: center; gap: 12px; padding: 12px; border: 1px solid rgba(255,255,255,0.08);
             border-radius: 12px; background: rgba(255,255,255,0.03); margin-bottom: 20px; }
.user-card .name { color: #fff; font-weight: 600; font-size: 14px; line-height: 1.25; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.user-card .meta { color: #94A3B8; font-size: 12px; line-height: 1.35; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.user-card .txt { min-width: 0; }
.nav-sep { height: 1px; background: rgba(255,255,255,0.08); margin: 12px 4px; }
.nav-label { color: #64748B !important; font-size: 11px; font-weight: 600; letter-spacing: .04em; padding: 4px 12px 6px; }

/* Boutons de navigation : un st.button 'tertiary' habille en entree de menu, l'icone vient de ::before */
[data-testid="stSidebar"] [class*="st-key-nav_"] button {
    width: 100%; justify-content: flex-start; gap: 12px; padding: 0 12px; min-height: 40px; border: 0; border-radius: 10px;
    background: transparent; color: #CBD5E1; font-weight: 500; transition: background .15s ease, color .15s ease; }
[data-testid="stSidebar"] [class*="st-key-nav_"] button > div, [class*="st-key-ico-"] button > div { flex: 1 1 auto; text-align: left !important; display: flex; justify-content: flex-start; }
[data-testid="stSidebar"] [class*="st-key-nav_"] button p { font-size: 14px; font-weight: 500; color: inherit; line-height: 1; text-align: left !important; }
[data-testid="stSidebar"] [class*="st-key-nav_"] button::before {
    content: ""; width: 18px; height: 18px; flex: none; background-color: currentColor;
    -webkit-mask-repeat: no-repeat; mask-repeat: no-repeat; -webkit-mask-position: center; mask-position: center;
    -webkit-mask-size: contain; mask-size: contain; }
[data-testid="stSidebar"] [class*="st-key-nav_"] button:hover { background: rgba(255,255,255,0.07); color: #fff; }
[data-testid="stSidebar"] [class*="st-key-nav_"] button:hover p { color: #fff; }
[data-testid="stSidebar"] [class*="st-key-nav_"] button:focus-visible { outline: 2px solid var(--primaire); outline-offset: 1px; }
[data-testid="stSidebar"] [class*="st-key-nav_"] button::after { margin-left: auto; flex: none; box-sizing: border-box; }
[data-testid="stSidebar"] [class*="st-key-nav_"] button { overflow: visible; }

/* ===== 4. Cartes ===== */
[class*="st-key-card_"] { background: var(--carte); border: 1px solid var(--bordure); border-radius: 16px; padding: 20px;
                          box-shadow: 0 4px 12px rgba(0,0,0,0.05); }
[data-testid="stVerticalBlock"][class*="st-key-card_"] { gap: 12px; }
[class*="st-key-card_flat_"] { box-shadow: none; }
[class*="st-key-card_nonlue_"] { border-left: 3px solid var(--primaire); }
[class*="st-key-card_info_"] { background: var(--primaire-pale); border-color: var(--primaire-bord); box-shadow: none; }
[class*="st-key-card_dim_"] { background: #FBFDFF; box-shadow: none; }
[class*="st-key-card_"] [data-testid="stVerticalBlock"] { gap: 12px; }

/* ===== 5. Boutons ===== */
[data-testid="stMainBlockContainer"] button[data-testid^="stBaseButton"], [data-testid="stDialog"] button[data-testid^="stBaseButton"] {
    border-radius: 10px; font-weight: 500; font-size: 14px; min-height: 38px; padding: 0 14px; transition: background .15s ease, border-color .15s ease, color .15s ease; }
button[data-testid="stBaseButton-secondary"], button[data-testid="stBaseButton-secondaryFormSubmit"] { background: #fff; border: 1px solid var(--bordure); color: var(--texte); }
button[data-testid="stBaseButton-secondary"]:hover, button[data-testid="stBaseButton-secondaryFormSubmit"]:hover { background: var(--fond); border-color: #CBD5E1; color: var(--texte); }
button[data-testid="stBaseButton-primary"], button[data-testid="stBaseButton-primaryFormSubmit"] { background: var(--primaire); border: 1px solid var(--primaire); color: #fff; border-radius: 12px; }
button[data-testid="stBaseButton-primary"]:hover, button[data-testid="stBaseButton-primaryFormSubmit"]:hover { background: var(--primaire-fonce); border-color: var(--primaire-fonce); color: #fff; }
button[data-testid="stBaseButton-primary"]:disabled { background: #BFDBFE; border-color: #BFDBFE; }
button[data-testid="stBaseButton-tertiary"] { background: transparent; border: 0; color: var(--texte-2); }
button[data-testid="stBaseButton-tertiary"]:hover { background: var(--surface); color: var(--texte); }
button:focus-visible { outline: 2px solid var(--primaire) !important; outline-offset: 2px; }
[class*="st-key-danger_"] button { background: var(--danger) !important; border-color: var(--danger) !important; color: #fff !important; }
[class*="st-key-danger_"] button:hover { background: #DC2626 !important; }

/* Boutons d'action avec icone Lucide (cle 'ico-<nom>__...') : style discret, icone avant le libelle */
[class*="st-key-ico-"] button { gap: 8px; background: transparent; border: 1px solid transparent; color: var(--texte-2); padding: 0 12px; }
[class*="st-key-ico-"] button:hover { background: var(--surface); color: var(--texte); border-color: transparent; }
[class*="st-key-ico-"] button::before { content: ""; width: 17px; height: 17px; flex: none; background-color: currentColor;
    -webkit-mask-repeat: no-repeat; mask-repeat: no-repeat; -webkit-mask-position: center; mask-position: center; -webkit-mask-size: contain; mask-size: contain; }
[class*="st-key-ico-"] button[data-testid="stBaseButton-primary"] { background: var(--primaire-pale); border-color: var(--primaire-pale); color: var(--primaire-fonce); }
[class*="st-key-ico-"] button[data-testid="stBaseButton-primary"]:hover { background: #DBEAFE; border-color: #DBEAFE; color: var(--primaire-fonce); }
[class*="st-key-ico-"] button p { font-size: 14px; font-weight: 500; color: inherit; text-align: left; }
[class*="st-key-ico-"] button { justify-content: flex-start; }
[class*="st-key-ico-"][class*="__plein"] button, [class*="st-key-ico-"][class*="__bord"] button { justify-content: center; }
[class*="st-key-ico-"][class*="__plein"] button > div, [class*="st-key-ico-"][class*="__bord"] button > div { flex: 0 1 auto; }
[class*="st-key-ico-"][class*="__bord"] button { border-color: var(--bordure); background: #fff; }
[class*="st-key-ico-"][class*="__bord"] button:hover { background: var(--fond); border-color: #CBD5E1; }
/* Bouton 'plein' (ex. Publier) avec icone : on garde le fond primaire */
[class*="st-key-ico-"][class*="__plein"] button { background: var(--primaire); color: #fff; border-color: var(--primaire); border-radius: 12px; }
[class*="st-key-ico-"][class*="__plein"] button:hover { background: var(--primaire-fonce); color: #fff; }
/* Menu '...' : libelle masque (reste lu par les lecteurs d'ecran), seule l'icone apparait */
[class*="st-key-ico-ellipsis__"] { display: flex; justify-content: flex-end; }
[class*="st-key-ico-ellipsis__"] button { padding: 0; width: 36px; min-height: 36px; justify-content: center; color: var(--texte-3); }
[class*="st-key-ico-ellipsis__"] button p, [class*="st-key-ico-ellipsis__"] button [data-testid="stIconMaterial"] { display: none; }
[class*="st-key-ico-"] [data-testid="stPopover"] button [data-testid="stIconMaterial"] { display: none; }

/* ===== 6. Champs de saisie ===== */
.stApp label, [data-testid="stWidgetLabel"] p { font-size: 13px; font-weight: 500; color: #334155; }
[data-baseweb="input"], [data-baseweb="textarea"], [data-baseweb="select"] > div, [data-baseweb="base-input"] { background: #fff; }
[data-baseweb="input"], [data-baseweb="textarea"], [data-baseweb="select"] > div:first-child {
    border: 1px solid var(--bordure) !important; border-radius: 10px !important; box-shadow: none !important; transition: border-color .15s ease, box-shadow .15s ease; }
[data-baseweb="input"] > div, [data-baseweb="base-input"] { border: 0 !important; }
[data-baseweb="input"]:focus-within, [data-baseweb="textarea"]:focus-within, [data-baseweb="select"] > div:first-child:focus-within {
    border-color: var(--primaire) !important; box-shadow: 0 0 0 3px rgba(59,130,246,0.15) !important; }
.stApp input, .stApp textarea { color: var(--texte); font-size: 14px; }
.stApp input::placeholder, .stApp textarea::placeholder { color: var(--texte-3); opacity: 1; }
[class*="st-key-champ-recherche_"] input { padding-left: 36px !important; }
[class*="st-key-card_composer"] [data-baseweb="textarea"] { background: var(--fond); border-color: transparent !important; }
[class*="st-key-card_composer"] [data-baseweb="textarea"] textarea { background: transparent; }
[data-testid="stCheckbox"] label p, [data-testid="stToggle"] label p { font-size: 14px; color: var(--texte); }
[data-testid="stChatInput"] { border-radius: 12px; border: 1px solid var(--bordure); background: #fff; }
[data-testid="stChatInput"] textarea { background: transparent; }
[data-testid="stForm"] { border: 0; padding: 0; background: transparent; }
[data-testid="stExpander"] details { border: 1px solid var(--bordure); border-radius: 12px; background: #fff; }
[data-testid="stExpander"] summary { font-size: 13px; font-weight: 500; color: var(--texte-2); }
[data-testid="stPopoverBody"] { border-radius: 12px; border: 1px solid var(--bordure); box-shadow: 0 8px 24px rgba(15,23,42,0.10); }
[data-testid="stDialog"] [role="dialog"] { border-radius: 16px; }
[data-testid="stAlert"] { border-radius: 12px; border: 1px solid var(--bordure); }
[data-testid="stImage"] img { border-radius: 12px; }
[data-testid="stPlotlyChart"] { margin: 0 -4px; }
hr { border-color: var(--bordure); margin: 8px 0; }

/* ===== 7. Pills (filtres) et onglets : st.pills n'a pas de data-testid par bouton, l'etat actif est aria-checked ===== */
[data-testid="stButtonGroup"] { gap: 8px; flex-wrap: wrap; }
[data-testid="stButtonGroup"] button { border-radius: 999px; background: #fff; border: 1px solid var(--bordure); color: var(--texte-2);
    padding: 0 16px; min-height: 34px; font-size: 13px; font-weight: 500; transition: background .15s ease, border-color .15s ease, color .15s ease; }
[data-testid="stButtonGroup"] button p { color: inherit; font-size: 13px; font-weight: inherit; }
[data-testid="stButtonGroup"] button:hover { background: var(--fond); border-color: #CBD5E1; color: var(--texte); }
[data-testid="stButtonGroup"] button[aria-checked="true"] { background: var(--primaire) !important; border-color: var(--primaire) !important; color: #fff !important; font-weight: 600; }
[data-testid="stButtonGroup"] button[aria-checked="true"] p, [data-testid="stButtonGroup"] button[aria-checked="true"] span { color: #fff !important; }
/* onglets soulignes : meme composant st.pills, cle 'tabs_*' */
[class*="st-key-tabs_"] { border-bottom: 1px solid var(--bordure); }
[class*="st-key-tabs_"] [data-testid="stButtonGroup"] { gap: 24px; flex-wrap: nowrap; overflow-x: auto; }
[class*="st-key-tabs_"] [data-testid="stButtonGroup"] button { border-radius: 0; background: transparent !important; border: 0 !important; border-bottom: 2px solid transparent !important;
    padding: 0 2px; min-height: 40px; margin-bottom: -1px; white-space: nowrap; color: var(--texte-2); font-size: 14px; font-weight: 500; }
[class*="st-key-tabs_"] [data-testid="stButtonGroup"] button:hover { color: var(--texte); }
[class*="st-key-tabs_"] [data-testid="stButtonGroup"] button[aria-checked="true"] { color: var(--primaire-fonce) !important; border-bottom-color: var(--primaire) !important; font-weight: 600; }
[class*="st-key-tabs_"] [data-testid="stButtonGroup"] button[aria-checked="true"] p, [class*="st-key-tabs_"] [data-testid="stButtonGroup"] button[aria-checked="true"] span { color: var(--primaire-fonce) !important; }

/* ===== 8. Avatars, badges, puces ===== */
.avatar { display: inline-flex; align-items: center; justify-content: center; border-radius: 50%; font-weight: 600; flex: none; letter-spacing: .01em; user-select: none; }
.badge { display: inline-flex; align-items: center; gap: 6px; padding: 2px 10px; border-radius: 999px; font-size: 12px; font-weight: 600; line-height: 18px; white-space: nowrap; }
.badge.neutre { background: var(--surface); color: #475569; }
.badge.primaire { background: var(--primaire-pale); color: var(--primaire-fonce); }
.badge.succes { background: var(--succes-pale); color: var(--succes-texte); }
.badge.danger { background: var(--danger-pale); color: #B91C1C; }
.badge.alerte { background: var(--alerte-pale); color: #B45309; }
.badge .point { width: 6px; height: 6px; border-radius: 50%; background: currentColor; }
.compteur { display: inline-flex; align-items: center; justify-content: center; min-width: 20px; padding: 0 6px; height: 20px; border-radius: 999px;
            background: var(--danger); color: #fff; font-size: 11px; font-weight: 700; line-height: 1; }
.compteur.primaire { background: var(--primaire); }
.chips { display: flex; flex-wrap: wrap; gap: 6px; }
.post-head + .chips { margin-top: 10px; }
.chip { display: inline-flex; align-items: center; gap: 4px; padding: 2px 10px; border-radius: 999px; background: var(--surface); color: #475569; font-size: 12.5px; font-weight: 500; }
.chip.tag { background: var(--primaire-pale); color: var(--primaire-fonce); }

/* ===== 9. Publications et commentaires ===== */
.post-head { display: flex; align-items: center; gap: 12px; }
.post-head .who { min-width: 0; }
.post-head .name { font-weight: 600; font-size: 15px; color: var(--texte); line-height: 1.25; }
.post-head .meta { font-size: 12.5px; color: var(--texte-2); line-height: 1.35; }
.post-body { font-size: 15px; color: var(--texte); line-height: 1.55; overflow-wrap: anywhere; }
.post-raison { display: inline-flex; align-items: center; gap: 6px; font-size: 12.5px; font-weight: 500; color: var(--primaire-fonce); background: var(--primaire-pale); padding: 3px 10px; border-radius: 999px; width: fit-content; }
.post-media { display: block; width: 100%; max-width: 560px; max-height: 380px; object-fit: cover; border-radius: 12px; background: var(--surface); min-height: 120px; border: 1px solid var(--bordure); }
.post-media-legende { font-size: 12px; color: var(--texte-3); margin-top: 6px; }
.comment { display: flex; gap: 10px; align-items: flex-start; }
.comment .bulle-com { background: var(--surface); border-radius: 12px; padding: 8px 12px; min-width: 0; }
.comment .nom { font-size: 13px; font-weight: 600; }
.comment .texte { font-size: 14px; overflow-wrap: anywhere; }
.comment .date { font-size: 12px; color: var(--texte-3); }
.reponse { margin-left: 38px; }

/* ===== 10. KPI, etats vides ===== */
.kpi { background: var(--carte); border: 1px solid var(--bordure); border-radius: 16px; padding: 20px; box-shadow: 0 4px 12px rgba(0,0,0,0.05); height: 100%; }
.kpi .haut { display: flex; justify-content: space-between; align-items: center; }
.kpi .label { font-size: 13px; font-weight: 500; color: var(--texte-2); }
.kpi .icone { width: 34px; height: 34px; border-radius: 10px; background: var(--primaire-pale); color: var(--primaire-fonce); display: inline-flex; align-items: center; justify-content: center; }
.kpi .valeur { font-size: 30px; font-weight: 700; letter-spacing: -0.02em; line-height: 1.15; margin-top: 12px; color: var(--texte); }
.kpi .note { font-size: 12.5px; color: var(--texte-2); margin-top: 4px; }
.kpi.alerte .icone { background: var(--danger-pale); color: #B91C1C; }
.empty { display: flex; flex-direction: column; align-items: center; justify-content: center; text-align: center; gap: 8px; padding: 48px 24px;
         background: var(--primaire-pale); border: 1px dashed var(--primaire-bord); border-radius: 16px; min-height: 280px; }
.empty .pastille { width: 56px; height: 56px; border-radius: 16px; background: #fff; color: var(--primaire); display: inline-flex; align-items: center; justify-content: center; box-shadow: 0 4px 12px rgba(59,130,246,0.15); }
.empty .titre { font-size: 16px; font-weight: 600; color: var(--texte); margin-top: 8px; }
.empty .texte { font-size: 14px; color: var(--texte-2); max-width: 340px; }
.empty.compact { min-height: 0; padding: 28px 20px; background: #fff; border-color: var(--bordure); }
.empty.compact .pastille { background: var(--surface); color: var(--texte-3); box-shadow: none; }

/* ===== 11. Messagerie ===== */
[class*="st-key-conv_"] { position: relative; border-radius: 12px; border: 1px solid transparent; transition: background .15s ease; }
[class*="st-key-conv_"]:hover { background: var(--surface); }
[class*="st-key-conv_actif_"] { background: var(--primaire-pale); border-color: var(--primaire-bord); }
[class*="st-key-conv_"] [data-testid="stVerticalBlock"] { gap: 0; }
[class*="st-key-convbtn_"] { position: absolute; inset: 0; z-index: 2; }
[class*="st-key-convbtn_"] button { width: 100%; height: 100%; opacity: 0; cursor: pointer; }
.conv-row { display: flex; align-items: center; gap: 12px; padding: 10px 12px; }
.conv-row .corps { flex: 1; min-width: 0; }
.conv-row .haut { display: flex; justify-content: space-between; gap: 8px; align-items: baseline; }
.conv-row .nom { font-weight: 600; font-size: 14px; color: var(--texte); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.conv-row .heure { font-size: 12px; color: var(--texte-3); flex: none; }
.conv-row .bas { display: flex; justify-content: space-between; align-items: center; gap: 8px; }
.conv-row .apercu { font-size: 13px; color: var(--texte-2); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.conv-row.nonlu .apercu { color: var(--texte); font-weight: 500; }
.thread-head { display: flex; align-items: center; gap: 12px; padding-bottom: 12px; border-bottom: 1px solid var(--bordure); }
.thread-head .nom { font-weight: 600; font-size: 15px; line-height: 1.25; }
.fil-bulles { display: flex; flex-direction: column-reverse; gap: 6px; padding: 4px 0; max-height: 440px; overflow-y: auto; }
.bulle { max-width: 78%; padding: 8px 12px; border-radius: 14px 14px 14px 4px; background: var(--surface); width: fit-content; font-size: 14px; overflow-wrap: anywhere; }
.bulle.moi { align-self: flex-end; background: var(--primaire); color: #fff; border-radius: 14px 14px 4px 14px; }
.bulle .qui { font-size: 12px; font-weight: 600; color: var(--primaire-fonce); }
.bulle .quand { font-size: 11.5px; color: var(--texte-3); margin-top: 2px; }
.bulle.moi .quand { color: #DBEAFE; }
.bulle .nouveau { color: var(--succes-texte); font-weight: 700; }
.bulle.moi .nouveau { color: #fff; }

/* ===== 12. Notifications ===== */
.notif { display: flex; gap: 14px; align-items: flex-start; }
.notif .corps { flex: 1; min-width: 0; font-size: 14px; color: var(--texte); }
.notif .corps b { font-weight: 600; }
.notif .quand { font-size: 12.5px; color: var(--texte-2); margin-top: 4px; display: flex; align-items: center; gap: 6px; }

/* ===== 13. Reglages ===== */
.reglage-titre { font-size: 16px; font-weight: 600; color: var(--texte); }
.reglage-texte { font-size: 14px; color: var(--texte-2); margin-top: 2px; }
.a-venir { display: flex; justify-content: space-between; align-items: center; gap: 12px; padding: 12px 0; border-top: 1px solid var(--bordure); }
.a-venir:first-of-type { border-top: 0; }

/* ===== 14. Responsive ===== */
@media (max-width: 1100px) {
    /* Messages : liste et discussion s'empilent quand la largeur utile devient trop faible */
    [data-testid="stHorizontalBlock"]:has([class*="st-key-champ-recherche_conv"]) { flex-wrap: wrap !important; }
    [data-testid="stHorizontalBlock"]:has([class*="st-key-champ-recherche_conv"]) > [data-testid="stColumn"] { flex: 1 1 100% !important; min-width: 100% !important; }
}
@media (max-width: 900px) {
    [data-testid="stMainBlockContainer"] { padding: 48px 20px 48px; }
    .page-title { font-size: 26px; }
}
@media (max-width: 640px) {
    /* Streamlit empile toutes les colonnes sous 640 px : on garde sur une ligne les rangees compactes (actions, composer, menu) */
    [class*="st-key-card_post_"] [data-testid="stHorizontalBlock"], [class*="st-key-card_composer"] [data-testid="stHorizontalBlock"] { flex-wrap: nowrap !important; gap: 8px; }
    [class*="st-key-card_post_"] [data-testid="stColumn"], [class*="st-key-card_composer"] [data-testid="stColumn"] { min-width: 0 !important; width: auto !important; flex: 0 0 auto !important; }
    [class*="st-key-card_composer"] [data-testid="stColumn"]:has(> [data-testid="stVerticalBlock"]:empty), [class*="st-key-card_post_"] [data-testid="stColumn"]:has(> [data-testid="stVerticalBlock"]:empty) { display: none !important; }
    [class*="st-key-card_composer"] [data-testid="stHorizontalBlock"]:not(:has([data-testid="stTextArea"])) { justify-content: space-between; }
    [data-testid="stHorizontalBlock"]:has([data-testid="stTextArea"]) > [data-testid="stColumn"]:last-child { flex: 1 1 0 !important; }
    [data-testid="stHorizontalBlock"]:has([data-testid="stTextArea"]) > [data-testid="stColumn"]:first-child { flex: 0 0 44px !important; }
    [class*="st-key-card_post_"] [data-testid="stHorizontalBlock"]:has([class*="st-key-ico-ellipsis__"]) > [data-testid="stColumn"]:first-child { flex: 1 1 auto !important; }
    [class*="st-key-card_post_"] [data-testid="stHorizontalBlock"]:has([class*="st-key-ico-ellipsis__"]) > [data-testid="stColumn"]:last-child { flex: 0 0 40px !important; }
    [class*="st-key-ico-"] button { padding: 0 8px; }
    [class*="st-key-card_composer"] [class*="st-key-ico-"] button p { font-size: 13px; }
    /* grille de KPI : 2 par ligne au lieu de 8 lignes empilees */
    [data-testid="stHorizontalBlock"]:has(.kpi) { flex-wrap: wrap !important; gap: 12px; }
    [data-testid="stHorizontalBlock"]:has(.kpi) > [data-testid="stColumn"] { flex: 0 0 calc(50% - 6px) !important; width: calc(50% - 6px) !important; min-width: calc(50% - 6px) !important; }
    [data-testid="stMainBlockContainer"] { padding: 48px 12px 40px; }
    [data-testid="stMainBlockContainer"] [data-testid="stVerticalBlock"] { gap: 12px; }
    [class*="st-key-card_"] { padding: 14px; border-radius: 14px; }
    .page-title { font-size: 24px; }
    .kpi { padding: 14px; } .kpi .valeur { font-size: 24px; }
    .bulle { max-width: 90%; }
    .post-media { max-height: 260px; }
    [data-testid="stSidebar"] { min-width: 0; max-width: 100%; }
}
@media (prefers-reduced-motion: reduce) { * { transition: none !important; } }
"""


def _regles_icones():
    """Genere une regle CSS par icone : le masque SVG est applique au ::before du bouton correspondant."""
    regles = []
    for cle, nom in ICONES_NAV.items():
        m = masque(nom)
        regles.append('[data-testid="stSidebar"] .st-key-nav_%s button::before{-webkit-mask-image:%s;mask-image:%s}' % (cle, m, m))
    for nom in ICONES_BOUTONS:
        m = masque(nom)
        regles.append('[class*="st-key-ico-%s__"] button::before{-webkit-mask-image:%s;mask-image:%s}' % (nom, m, m))
    loupe = fond_champ("search")
    regles.append('[class*="st-key-champ-recherche_"] input{background-image:%s;background-repeat:no-repeat;background-position:12px center;background-size:16px}' % loupe)
    return "\n".join(regles)


def _regles_navigation(actif, nb_notifications):
    """Etat actif de la navigation + badge de notifications (valeurs dynamiques, donc generees a chaque rendu)."""
    regles = []
    if actif:
        regles.append('[data-testid="stSidebar"] .st-key-nav_%s button{background:rgba(59,130,246,0.20);color:#fff}' % actif)
        regles.append('[data-testid="stSidebar"] .st-key-nav_%s button:hover{background:rgba(59,130,246,0.28)}' % actif)
        regles.append('[data-testid="stSidebar"] .st-key-nav_%s button p{color:#fff}' % actif)
    if nb_notifications:
        texte = str(nb_notifications)
        regles.append('[data-testid="stSidebar"] .st-key-nav_notifications button::after{content:"%s";background:#EF4444;color:#fff;'
                      'font-size:11px;font-weight:700;border-radius:999px;padding:0 7px;min-width:22px;height:20px;line-height:20px;text-align:center;display:inline-block}' % texte)
    return "\n".join(regles)


def injecter(actif_nav=None, nb_notifications=0):
    """Injecte le design system dans la page (a appeler une fois par rendu, avant tout contenu)."""
    css = "\n".join([IMPORT_POLICE, _jetons_css(), CSS_BASE, _regles_icones(), _regles_navigation(actif_nav, nb_notifications)])
    st.markdown("<style>%s</style>" % css, unsafe_allow_html=True)
