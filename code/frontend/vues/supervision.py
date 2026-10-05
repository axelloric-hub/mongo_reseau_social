"""
supervision.py - Page 'Supervision' : indicateurs globaux et agregations MongoDB.

Les chiffres viennent d'agregations MongoDB (agregations.py via l'API). Chaque graphique repond a
une question precise et reste relie au code : l'expander montre le pipeline Python qui le produit.
Seuls des diagrammes a barres et des camemberts sont utilises, dans une palette sobre.
"""
import pandas as pd
import plotly.express as px
import streamlit as st

from frontend.components.cards import carte, en_tete
from frontend.components.helpers import essayer, pills
from frontend.components.kpi import kpi

# Bleus et ardoises : la couleur distingue des categories, elle ne decore pas
COULEURS = ["#3B82F6", "#0F172A", "#93C5FD", "#64748B", "#22C55E", "#F59E0B", "#CBD5E1", "#1D4ED8", "#EF4444", "#94A3B8"]
LIBELLES = {"M": "Hommes", "F": "Femmes", "employe": "Employés", "ecolier / etudiant": "Écoliers / étudiants", "retraite": "Retraités",
            "influenceur": "Influenceurs", "normal": "Normaux", "timide_reseau": "Timides", "populaire": "Populaires",
            "moins_populaire": "Moins populaires", "restreint": "Privés / restreints", "prive": "Messages privés", "groupe": "Messages de groupe",
            "jaime": "J'aime", "commentaire": "Commentaires", "message": "Messages", "demande_ami": "Demandes d'ami",
            "lue": "Lues", "non_lue": "Non lues"}


def lib(valeur):
    return LIBELLES.get(valeur, str(valeur))


def _donnees(nom):
    ok, r = essayer("agregation", nom=nom)
    return pd.DataFrame(r) if ok and r else pd.DataFrame()


def _style(fig, hauteur=300):
    fig.update_layout(height=hauteur, margin=dict(l=4, r=4, t=4, b=4), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                      font=dict(family="Inter, system-ui, sans-serif", color="#0F172A", size=12), legend_title_text="",
                      legend=dict(font=dict(color="#64748B")))
    return fig


def camembert(df, noms, valeurs, cle):
    df = df.copy()
    df[noms] = df[noms].map(lib)
    fig = px.pie(df, names=noms, values=valeurs, hole=0.55, color_discrete_sequence=COULEURS)
    fig.update_traces(textinfo="percent", textfont=dict(color="#FFFFFF", size=12), marker=dict(line=dict(color="#FFFFFF", width=2)))
    st.plotly_chart(_style(fig), width="stretch", key=cle, config={"displayModeBar": False})


def barres(df, x, y, cle, horizontal=False, couleur=None, empile=False):
    df = df.copy()
    if couleur:
        df[couleur] = df[couleur].map(lib)
    fig = px.bar(df, x=y if horizontal else x, y=x if horizontal else y, orientation="h" if horizontal else "v", color=couleur,
                 color_discrete_sequence=COULEURS, barmode="stack" if empile else "group", text_auto=True)
    fig.update_traces(marker_cornerradius=4, textfont=dict(size=11))
    fig.update_xaxes(showgrid=False, title=None, linecolor="#E2E8F0", tickfont=dict(color="#64748B"))
    fig.update_yaxes(gridcolor="#EEF2F7", title=None, zeroline=False, tickfont=dict(color="#64748B"))
    if horizontal:
        fig.update_yaxes(autorange="reversed", showgrid=False)
        fig.update_xaxes(showgrid=True, gridcolor="#EEF2F7")
    st.plotly_chart(_style(fig), width="stretch", key=cle, config={"displayModeBar": False})


def graphique(titre, question, nom_agg, rendu, cle):
    """Une carte = titre + question metier + graphique + code de l'agregation (expander)."""
    with carte("chart_" + cle):
        st.markdown('<div class="card-title">%s</div><div class="card-text">%s</div>' % (titre, question), unsafe_allow_html=True)
        df = _donnees(nom_agg)
        if df.empty:
            st.markdown('<div class="small">Aucune donnée.</div>', unsafe_allow_html=True)
        else:
            rendu(df)
        with st.expander("Voir l'agrégation (code Python et pipeline MongoDB)"):
            ok, r = essayer("source_agregation", nom=nom_agg)
            if ok:
                st.code(r["source"], language="python")
            st.dataframe(df, width="stretch", hide_index=True)


def _kpis(s):
    par_user = lambda n: "%.1f par membre" % (n / max(s["utilisateurs"], 1))
    taux = round(100 * s["notifications_non_lues"] / max(s["notifications"], 1))
    cartes = [("Membres", s["utilisateurs"], "users", "Communauté complète", False),
              ("Groupes", s["groupes"], "users-round", "%.1f membres en moyenne" % (sum(g["nb_membres"] for g in _taille_groupes()) / max(s["groupes"], 1)), False),
              ("Publications", s["publications"], "file-text", par_user(s["publications"]), False),
              ("Commentaires", s["commentaires"], "message-circle", "%.1f par publication" % (s["commentaires"] / max(s["publications"], 1)), False),
              ("Messages", s["messages"], "messages-square", par_user(s["messages"]), False),
              ("Notifications", s["notifications"], "bell", "Toutes catégories", False),
              ("Non lues", s["notifications_non_lues"], "eye", "%d %% des notifications" % taux, s["notifications_non_lues"] > 0),
              ("Documents archivés", s["archives"], "archive", "Suppressions non destructives", False)]
    for ligne in (cartes[:4], cartes[4:]):
        for col, (label, valeur, ico, note, alerte) in zip(st.columns(4), ligne):
            with col:
                kpi(label, valeur, ico, note, alerte)


@st.cache_data(ttl=30, show_spinner=False)
def _taille_groupes_cache(_signature):
    ok, r = essayer("agregation", nom="tailles_groupes")
    return r if ok else []


def _taille_groupes():
    return _taille_groupes_cache(1)


def afficher(moi):
    en_tete("Supervision", "Vue d'ensemble de la communauté, calculée en direct par des agrégations MongoDB.")
    ok, s = essayer("stats", user_id=moi["_id"])
    if not ok:
        return
    _kpis(s)
    section = pills("sup_section", ["Utilisateurs", "Publications", "Groupes", "Messagerie"], "Utilisateurs", onglets=True)
    if section == "Utilisateurs":
        a, b = st.columns(2)
        with a:
            graphique("Répartition par sexe", "La communauté est-elle équilibrée entre femmes et hommes ?", "repartition_sexe",
                      lambda df: camembert(df, "valeur", "n", "c_sexe"), "sexe")
        with b:
            graphique("Répartition par fonction", "Quelle part d'employés, d'étudiants et de retraités ?", "repartition_fonction",
                      lambda df: camembert(df, "valeur", "n", "c_fonction"), "fonction")
        a, b = st.columns(2)
        with a:
            graphique("Tranches d'âge", "Quelles générations composent la communauté ?", "repartition_age",
                      lambda df: barres(df.sort_values("ordre"), "valeur", "n", "c_age"), "age")
        with b:
            graphique("Membres par ville", "D'où viennent les membres ?", "repartition_ville",
                      lambda df: barres(df, "valeur", "n", "c_ville", horizontal=True), "ville")
        a, b = st.columns(2)
        with a:
            graphique("Catégories d'activité", "Combien d'influenceurs, de membres normaux et de timides ?", "categories_utilisateurs",
                      lambda df: barres(df, "valeur", "n", "c_cat"), "cat")
        with b:
            graphique("Préférences les plus choisies", "Quels centres d'intérêt pilotent le fil personnalisé ?", "preferences",
                      lambda df: barres(df, "preference", "n", "c_pref", horizontal=True), "pref")
    elif section == "Publications":
        a, b = st.columns(2)
        with a:
            graphique("Volume de publications par catégorie (cible 70 / 25 / 5 %)", "Qui produit réellement le contenu ?", "volume_publications",
                      lambda df: camembert(df, "categorie", "publications", "c_volume"), "volume")
        with b:
            graphique("Hashtags les plus utilisés ($unwind)", "Quels sujets reviennent le plus souvent ?", "top_hashtags",
                      lambda df: barres(df, "hashtag", "utilisations", "c_tags", horizontal=True), "tags")
        a, b = st.columns(2)
        with a:
            graphique("Membres les plus actifs", "Qui anime la communauté (publications + commentaires) ?", "utilisateurs_actifs",
                      lambda df: barres(df.melt(id_vars="pseudo", value_vars=["publications", "commentaires"], var_name="type", value_name="n"),
                                        "pseudo", "n", "c_actifs", horizontal=True, couleur="type", empile=True), "actifs")
        with b:
            graphique("Engagement moyen par ville ($lookup)", "Dans quelles villes les publications suscitent-elles le plus de réactions ?", "engagement_par_ville",
                      lambda df: barres(df, "ville", "engagement_moyen", "c_engage"), "engage")
    elif section == "Groupes":
        a, b = st.columns(2)
        with a:
            graphique("Popularité des groupes (cible 50 / 35 / 15 %)", "Les groupes se répartissent-ils comme prévu ?", "popularite_groupes",
                      lambda df: camembert(df, "valeur", "n", "c_pop"), "pop")
        with b:
            graphique("Groupes par membre", "Combien de membres sont dans 0, 1 ou plusieurs groupes ?", "groupes_par_utilisateur",
                      lambda df: barres(df, "nb_groupes", "utilisateurs", "c_gpu"), "gpu")
        graphique("Groupes les plus peuplés et leur créateur ($lookup)", "Quels groupes rassemblent le plus de monde, et qui les a fondés ?", "groupes_peuples",
                  lambda df: (barres(df, "groupe", "nb_membres", "c_peuples", horizontal=True),
                              st.dataframe(df[["groupe", "nb_membres", "createur", "pseudo_createur"]], width="stretch", hide_index=True)), "peuples")
    else:
        graphique("Messages par jour sur la dernière semaine", "L'activité de messagerie est-elle régulière ?", "messages_par_jour",
                  lambda df: barres(df, "jour", "messages", "c_jours", couleur="type", empile=True), "jours")
        a, b = st.columns(2)
        with a:
            graphique("Messages privés et de groupe", "Quelle part de la messagerie se passe en groupe ?", "messages_par_type",
                      lambda df: camembert(df, "valeur", "n", "c_mtype"), "mtype")
        with b:
            graphique("Notifications par type et par statut", "Combien de notifications restent à lire, par type ?", "notifications_par_type",
                      lambda df: barres(df, "type", "n", "c_notif", couleur="statut", empile=True), "notif")
