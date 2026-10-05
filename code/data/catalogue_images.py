"""
catalogue_images.py - Catalogue des images du bucket public Lorem Picsum.

Source : fichier description_images.txt fourni avec le devoir. Pour chaque identifiant
d'image on garde : une description, les categories de preferences associees et les tons
de commentaires (type_comm) qui pilotent les legendes et les commentaires generes.
MongoDB ne stocke jamais l'image : seulement son URL (voir construire_url).
"""

# Les deux gabarits d'URL decrits dans le TXT. Le TXT ecrit la variante avec deux '?',
# ce qui est invalide en HTTP : on utilise '&random=' pour le second parametre.
URL_PRINCIPALE = "https://picsum.photos/id/{id}/{l}/{h}.jpg?random={graine}"
URL_VARIANTE = "https://picsum.photos/id/{id}/{l}/{h}.jpg?grayscale&blur=2&random={graine}"


def construire_url(image_id, variante="principale", graine=1, largeur=640, hauteur=480):
    """Renvoie l'URL d'une image ; 'variante' ajoute niveaux de gris + flou pour multiplier les visuels."""
    modele = URL_VARIANTE if variante == "grayscale" else URL_PRINCIPALE
    return modele.format(id=image_id, l=largeur, h=hauteur, graine=graine)


# id : (description, categories, tons)
IMAGES = {
    0: ("Ordinateur portable blanc, tasse de cafe, cahier et telephone", ["productivite"], ["concentre", "sarcastique"]),
    1: ("Quelqu'un travaille sur l'ordinateur", ["productivite", "technologie"], ["concentre", "sarcastique"]),
    2: ("Le cahier est ouvert", ["productivite", "education"], ["concentre", "sarcastique"]),
    3: ("Le telephone en main", ["productivite", "technologie"], ["concentre", "sarcastique"]),
    4: ("On ecrit dans le cahier", ["productivite", "education"], ["concentre", "sarcastique"]),
    5: ("Le cafe est bu", ["productivite"], ["concentre", "sarcastique", "salutations"]),
    6: ("Un verre d'eau s'ajoute au bureau", ["productivite"], ["salutations"]),
    7: ("Affaires rangees, discussion sur tablette", ["productivite", "technologie"], ["rdv_diner", "demande_rapport"]),
    8: ("Ordinateur laisse ouvert sur le bureau", ["productivite"], ["pause"]),
    9: ("Le telephone est pose sur le cahier", ["productivite"], ["aleatoire"]),
    10: ("Foret de sapins, montagne au loin", ["nature"], ["aleatoire"]),
    11: ("Foret ouverte, riviere, montagne", ["nature"], ["nature"]),
    12: ("Sable, mer, ilots et rochers", ["voyage", "nature"], ["touristique", "nature"]),
    13: ("Plage de galets, mer tres bleue, arbre mort", ["voyage"], ["touristique", "mariage"]),
    14: ("Cailloux dans l'eau, maree haute", ["voyage"], ["amoureuse"]),
    15: ("Chute d'eau, rochers verdoyants et glissants", ["aventure", "nature"], ["dangereux", "film", "temoignage"]),
    16: ("Tronc d'arbre sur une plage de pierres", ["nature", "voyage"], ["aleatoire"]),
    17: ("Chemin trace dans une foret de sapins", ["aventure", "nature"], ["horreur"]),
    18: ("Hautes herbes dans un champ", ["nature"], ["aleatoire"]),
    19: ("Arbre couvert de mousse au soleil", ["nature", "education"], ["savant"]),
    20: ("Table d'etudiant rose", ["education"], ["ecole"]),
    21: ("Chaussure blanche a talon pour soiree", ["mode"], ["feminin"]),
    22: ("Homme qui marche dans la rue (noir et blanc)", ["philosophie"], ["philosophique"]),
    23: ("Trois fourchettes sur fond noir et blanc", ["philosophie"], ["aleatoire"]),
    24: ("Bible ouverte", ["foi"], ["concentre", "chretien"]),
    25: ("Branches eclairees par un lever de soleil", ["nature"], ["aleatoire"]),
    26: ("Telephone, montre, casque, sac : effets personnels", ["productivite", "technologie"], ["professionnelle"]),
    27: ("Homme au bord du gouffre regardant l'horizon", ["philosophie", "aventure"], ["philosophique"]),
    28: ("Arbre et ruisseau sur des pierres", ["nature", "voyage"], ["touristique", "amoureuse"]),
    29: ("Sommet de l'Himalaya, deux grimpeurs", ["aventure"], ["extreme", "peur"]),
    30: ("Tasse avec un billet cubain et Castro", ["histoire"], ["historique"]),
    31: ("Chaussures et jambes d'une femme", ["mode"], ["style"]),
    32: ("Mur de prison gris avec un banc", ["philosophie", "histoire"], ["triste", "lecon_vie"]),
    33: ("Herbe touffue et deux petites fleurs", ["nature"], ["salutations", "bonheur"]),
    34: ("Fut d'essence rouge dans un champ", ["aventure"], ["aleatoire"]),
    35: ("Fleur piquante jaune", ["nature"], ["personnelle"]),
    36: ("Piece detachee d'un appareil electronique", ["technologie", "education"], ["ingenieux"]),
    37: ("Fleurs au bord de la plage", ["voyage", "nature"], ["touristique", "film"]),
    38: ("Ciel nuageux", ["nature"], ["aleatoire"]),
    39: ("Vieux vinyle qui tourne", ["histoire"], ["aleatoire"]),
    40: ("Nez d'un felin", ["nature"], ["aleatoire"]),
    41: ("Goutte d'eau sur une surface", ["nature", "technologie"], ["aleatoire"]),
    42: ("Table de snack, deux cafes et un telephone", ["productivite"], ["aleatoire"]),
    43: ("Pont de Manhattan (noir et blanc)", ["voyage", "histoire"], ["decouverte"]),
    44: ("Plage en noir et blanc, baigneurs", ["histoire"], ["historique"]),
    45: ("Plaque d'immatriculation en ecriture etrangere", ["voyage"], ["aleatoire"]),
}

# hashtag -> categories associees (chaque hashtag regroupe 1 a 3 preferences)
HASHTAGS = {
    "travail": ["productivite"], "bureau": ["productivite"], "focus": ["productivite", "education"],
    "cafe": ["productivite"], "etudes": ["education"], "ecole": ["education"],
    "savoir": ["education", "technologie"], "nature": ["nature"], "foret": ["nature", "aventure"],
    "montagne": ["nature", "aventure", "voyage"], "plage": ["voyage", "nature"], "voyage": ["voyage"],
    "tourisme": ["voyage", "nature"], "mariage": ["voyage"], "aventure": ["aventure"],
    "sportextreme": ["aventure"], "mode": ["mode"], "style": ["mode"], "soiree": ["mode"],
    "philo": ["philosophie"], "reflexion": ["philosophie", "foi"], "viedevie": ["philosophie", "histoire"],
    "foi": ["foi"], "priere": ["foi", "philosophie"], "histoire": ["histoire"],
    "memoire": ["histoire", "philosophie"], "retro": ["histoire", "mode"], "tech": ["technologie"],
    "innovation": ["technologie", "education"], "ingenieur": ["technologie", "education", "productivite"],
    "cameroun237": ["voyage", "histoire", "nature"], "enspd": ["education", "technologie"],
}

# ton -> legendes et commentaires (3 de chaque). Un ton vide produit une publication sans texte.
TONS = {
    "concentre": (["Concentre sur ma tache, ne pas deranger.", "Une session de travail sans interruption.", "Tout est en place, on avance."],
                  ["Courage, tu geres !", "Belle concentration.", "Continue comme ca."]),
    "sarcastique": (["Oui oui, je travaille, tres intensement.", "Productivite : 3 % travail, 97 % cafe.", "La deadline est dans 5 minutes, tout va bien."],
                    ["Haha, on te croit sur parole.", "Le cafe fait tout le travail, alors.", "Cette deadline a bien de la chance."]),
    "salutations": (["Bonjour a tous, belle journee a vous !", "Salut la communaute, bien reveilles ?", "Petit coucou du matin."],
                    ["Bonjour a toi aussi !", "Belle journee !", "Salut, bonne energie."]),
    "rdv_diner": (["Qui est partant pour un diner ce week-end ?", "Rendez-vous ce soir pour un diner entre amis.", "Je reserve une table pour samedi, vous venez ?"],
                  ["Je suis partant !", "Dis-moi l'heure et j'arrive.", "Ok pour samedi."]),
    "demande_rapport": (["Rappel : j'attends vos rapports avant vendredi.", "Qui m'envoie le rapport du projet aujourd'hui ?", "Point d'avancement demain, merci de preparer vos rapports."],
                        ["Je l'envoie ce soir.", "Bien recu, je m'en occupe.", "Il sera pret avant vendredi."]),
    "aleatoire": (["Un instant capture au hasard.", "Juste comme ca.", "Photo du jour."],
                  ["Sympa !", "Belle photo.", "J'aime bien."]),
    "nature": (["La nature est vraiment la plus belle des oeuvres.", "Un paysage qui apaise l'esprit.", "Respirer, simplement."],
               ["Magnifique !", "Quel endroit splendide.", "On se croirait dans un reve."]),
    "touristique": (["Un coin a visiter absolument.", "Destination a mettre sur votre liste.", "Voila pourquoi il faut voyager."],
                    ["C'est ou exactement ?", "Je veux y aller !", "Ca donne envie de partir."]),
    "mariage": (["Le decor ideal pour un mariage.", "On pourrait celebrer une union ici.", "Cadre de reve pour dire oui."],
                ["Ce serait parfait pour une ceremonie.", "Tellement romantique.", "Bonne idee de lieu."]),
    "amoureuse": (["Une ambiance pour deux.", "Le genre d'endroit ou l'on se promet des choses.", "Romantique a souhait."],
                  ["Trop mignon.", "Ca fait reveur.", "Belle ambiance."]),
    "dangereux": (["Attention, ces pierres sont tres glissantes.", "Beau mais dangereux, restez prudents.", "Ne vous approchez pas trop du bord."],
                  ["Prudence !", "J'ai failli glisser la-bas.", "Merci de l'avertissement."]),
    "film": (["On dirait une scene de film.", "Decor digne du cinema.", "Un plan que n'importe quel realisateur voudrait."],
             ["Oui, tres cinematographique.", "Je vois bien un film ici.", "Quelle scene !"]),
    "temoignage": (["Je suis deja tombe ici, souvenir inoubliable.", "Mon recit de randonnee, c'etait intense.", "Cette cascade m'a marque a vie."],
                   ["Merci de partager ton histoire.", "Raconte-nous la suite.", "Quelle experience."]),
    "horreur": (["Ce chemin me rappelle un film d'horreur.", "Personne ne revient de cette foret dans les films.", "Je n'irais pas la seul la nuit."],
                ["Moi non plus, jamais !", "Ca fait froid dans le dos.", "On dirait un decor de cauchemar."]),
    "savant": (["Savez-vous que la mousse indique un air tres humide ?", "Un arbre ancien, un vrai livre de science.", "La nature est le meilleur laboratoire."],
               ["Interessant, merci pour l'info.", "J'ai appris quelque chose.", "Tres instructif."]),
    "ecole": (["Retour sur les bancs, la rentree approche.", "Mon coin de revision est pret.", "Les examens arrivent, courage a tous."],
              ["Bon courage pour les exams !", "Meme situation ici.", "Reviser, toujours reviser."]),
    "feminin": (["Pour les soirees, rien ne vaut une bonne paire.", "Coup de coeur du jour.", "Elegance avant tout."],
                ["Superbe choix.", "Elles sont magnifiques.", "Tres elegant."]),
    "philosophique": (["Avancer seul n'est pas etre perdu.", "Face a l'horizon, on se pose les vraies questions.", "Le chemin compte plus que l'arrivee."],
                      ["Belle reflexion.", "Ca donne a penser.", "Tellement vrai."]),
    "chretien": (["La parole nourrit l'ame chaque matin.", "Moment de lecture et de priere.", "Que la paix soit avec vous."],
                 ["Amen.", "Dieu est bon.", "Belle benediction."]),
    "professionnelle": (["Mon kit de travail au quotidien.", "Tout ce qu'il faut pour une journee productive.", "Equipement du jour."],
                        ["Bien equipe !", "Le necessaire.", "Efficace."]),
    "extreme": (["Sport extreme : la montagne ne pardonne pas.", "Deux grimpeurs, un sommet, zero droit a l'erreur.", "L'Himalaya, le reve de tout alpiniste."],
                ["Courage a eux.", "Impressionnant.", "Je n'oserais jamais."]),
    "peur": (["Rien que de regarder, j'ai le vertige.", "Je ne monterais jamais la-haut.", "La peur du vide, c'est ici."],
             ["Moi aussi j'ai peur.", "Mes jambes tremblent.", "Pas pour moi."]),
    "historique": (["Un morceau d'histoire a ne pas oublier.", "Cette image raconte un moment du passe.", "Souvenons-nous de ce qui s'est passe."],
                   ["Important de s'en souvenir.", "Merci pour ce rappel.", "L'histoire nous enseigne."]),
    "triste": (["Parfois le silence pese plus que les murs.", "Un endroit qui raconte la solitude.", "Gris, comme certains jours."],
               ["Courage.", "Je comprends ce sentiment.", "Prenez soin de vous."]),
    "lecon_vie": (["Chaque epreuve est une lecon.", "On ressort toujours plus fort des murs qu'on a affrontes.", "Apprenons de nos erreurs."],
                  ["Sage parole.", "Tellement juste.", "Merci pour la lecon."]),
    "bonheur": (["Les petits bonheurs sont les meilleurs.", "Une fleur, un sourire, c'est suffisant.", "Je vous souhaite de la joie aujourd'hui."],
                ["Merci, pareil pour toi.", "Joie partagee.", "Un vrai bonheur simple."]),
    "personnelle": (["Je me souviens de ce jardin, mon enfance en pleine fleur.", "Une histoire personnelle que je garde pres de moi.", "Cette fleur m'a pique, mais quelle beaute."],
                    ["Beau souvenir.", "Merci de partager.", "Ca fait chaud au coeur."]),
    "ingenieux": (["Curieux de savoir comment ca marche.", "Un petit composant, tout un monde derriere.", "L'ingenierie dans le moindre detail."],
                  ["Passionnant !", "Tu pourrais l'expliquer ?", "L'electronique, quel art."]),
    "decouverte": (["Je decouvre enfin ce pont mythique.", "Comment a-t-on construit ca ?", "Ca m'etonne a chaque fois."],
                   ["Incroyable.", "Je me pose la meme question.", "A voir un jour."]),
    "pause": (["Petite pause, je reviens dans cinq minutes.", "Pause bien meritee.", "Je m'absente un instant."],
              ["A tout de suite.", "Profite bien.", "Reviens vite."]),
    "style": (["Details de style du jour.", "Inspiration mode de la semaine.", "Tenue du jour en preparation."],
              ["Joli.", "Bon gout.", "Tendance."]),
}
