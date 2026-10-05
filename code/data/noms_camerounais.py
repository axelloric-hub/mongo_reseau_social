"""
noms_camerounais.py - Listes de valeurs realistes pour generer les utilisateurs.

Les noms melangent des patronymes bamileke (Ouest), beti (Centre/Sud), sawa (Littoral),
anglophones (Nord-Ouest/Sud-Ouest) et peuls/hausa (Nord). Tous sont distincts :
le generateur en prend exactement 150, un par utilisateur.
"""

# Le premier nom (Fotso) est reserve au compte de demonstration valdez_237.
NOMS = [
    "Fotso", "Tagne", "Lembe", "Bagneki", "Matoukam", "Kotto", "Nguemo", "Tchoumi", "Kamga", "Ngassa",
    "Nkeng", "Mbarga", "Atangana", "Ekane", "Njoya", "Tchoupo", "Bello", "Essomba", "Onana", "Mvondo",
    "Biyong", "Abena", "Owona", "Manga", "Eyenga", "Nanga", "Ndongo", "Ateba", "Bikoe", "Zang",
    "Mebenga", "Ebogo", "Nkoulou", "Ewane", "Mbella", "Epee", "Dikobo", "Njie", "Fonkou", "Kenfack",
    "Djoumessi", "Talla", "Tchatchouang", "Nana", "Wamba", "Sop", "Feudjio", "Kouam", "Nguefack", "Tsafack",
    "Pouokam", "Nono", "Domche", "Simo", "Kemajou", "Tchinda", "Kamdem", "Noubissi", "Yimga", "Fokam",
    "Teguia", "Tchuente", "Mekontso", "Dongmo", "Youmbi", "Kuete", "Ngamaleu", "Lontsi", "Wouapi", "Zeufack",
    "Nzeukou", "Tamo", "Ketcha", "Mouafo", "Nzouakeu", "Defo", "Tiomela", "Chendjou", "Fomekong", "Nzali",
    "Ndam", "Njoh", "Bouba", "Hamadou", "Abba", "Oumarou", "Issa", "Adamou", "Sali", "Yaya",
    "Tchiroma", "Abdoulaye", "Mohamadou", "Garba", "Haman", "Ngwa", "Tabe", "Ndifor", "Ashu", "Mbah",
    "Tanyi", "Achu", "Fru", "Nformi", "Awah", "Tebo", "Etta", "Besong", "Eyong", "Ayuk",
    "Takang", "Enow", "Egbe", "Manyi", "Mukete", "Nkwain", "Forbin", "Ndeh", "Anye", "Ekema",
    "Ngando", "Mouelle", "Bilong", "Ebelle", "Elimbi", "Moukoko", "Dibango", "Njock", "Bekolo", "Bile",
    "Moudio", "Tamba", "Bessala", "Ottou", "Fouda", "Menye", "Ndzana", "Ayissi", "Messi", "Mballa",
    "Ntsama", "Belinga", "Oyono", "Ndjodo", "Assiga", "Obam", "Nyemeck", "Bayiha", "Nkodo", "Evina",
    "Zoa", "Mbezele", "Tsala", "Ngono", "Mengue", "Nsangou", "Bikanda", "Kana", "Tchakounte", "Nkamgang",
]

PRENOMS_F = [
    "Aline", "Marie", "Sandra", "Rose", "Carine", "Estelle", "Lucrece", "Mireille", "Nadege", "Flore",
    "Brenda", "Joelle", "Sylvie", "Ornella", "Sorelle", "Fatima", "Prisca", "Larissa", "Danielle", "Clarisse",
    "Laure", "Manuela", "Gaelle", "Vanessa", "Grace", "Esther", "Cynthia", "Rachel", "Michelle", "Armelle",
]
PRENOMS_M = [
    "Paul", "Kevin", "Ibrahim", "Moussa", "Brice", "Landry", "Herve", "Arnaud", "Cedric", "Yannick",
    "Rodrigue", "Franck", "Boris", "Thierry", "Guy", "Idriss", "Alain", "Serge", "Junior", "Patrice",
    "Wilfried", "Hans", "Ulrich", "Ange", "Eric", "Samuel", "Daniel", "Joseph", "Martin", "Steve",
]

# ville -> region (utile pour les segmentations)
VILLES = {
    "Douala": "Littoral", "Yaounde": "Centre", "Bafoussam": "Ouest", "Dschang": "Ouest",
    "Garoua": "Nord", "Kribi": "Sud", "Buea": "Sud-Ouest", "Limbe": "Sud-Ouest",
    "Bertoua": "Est", "Bamenda": "Nord-Ouest",
}

# Poids des villes : Douala et Yaounde dominent comme dans la realite
POIDS_VILLES = [30, 22, 10, 6, 5, 4, 6, 5, 4, 8]
