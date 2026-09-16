# -*- coding: utf-8 -*-
"""`assurer_baremes()` sous acces concurrent — constat 2 de l'audit du 16/09/2026.

Le docstring du service affirmait « idempotent et se repare tout seul : une
ligne manquante ne peut jamais casser un ecran ». **Mesure faite avant
correction : faux.** L'ancienne version lisait les types existants, **puis**
inserait, **puis** commitait. Entre la lecture et le commit, une autre requete
peut creer les quatre lignes : la premiere insere alors des doublons et prend
une `IntegrityError` non rattrapee — donc **500 sur `GET /api/baremes`**, le
tout premier appel de l'ecran barmes.

⚠️ **Deux fausses pistes ont ete ecartees en les mesurant**, et elles sont
notees ici pour que personne ne les reprenne :

1. *« Il suffit qu'une session ait une vue perimee. »* Non : mesure faite, une
   session SQLAlchemy en transaction **voit** les lignes commitees par une
   autre. SQLite en journal de restauration relache sa transaction de lecture
   apres chaque instruction — il n'y a pas d'instantane fige. Un test bati
   la-dessus passe sur le code fautif, donc ne prouve rien.
2. *« Il suffit de retarder le commit de la premiere. »* Non : cela tient une
   transaction d'ecriture ouverte indefiniment, ce que la production ne connait
   pas (le pilote SQLite attend 5 s par defaut et l'autre requete commite en
   quelques microsecondes). On y mesure alors un `database is locked` qui
   n'arrive jamais.

La fenetre est un vrai TOCTOU **en temps reel**. Elle exige donc de la
concurrence reelle, et c'est ce que ce fichier met en place : un fil d'execution
suspendu **entre sa lecture et son commit**, par un ecouteur SQLAlchemy.

**Portee** : la fenetre n'existe que tant que des baremes manquent, donc **une
fois**, au premier acces apres deploiement. C'est precisement le moment ou
plusieurs visiteurs arrivent sur la demo publique.
"""
import threading

import pytest
from sqlalchemy import create_engine, event, select
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models import TYPES_BAREMES, Bareme
from app.services.baremes import assurer_baremes

# Bornes de patience des rendez-vous entre fils. Genereuses pour la CI, mais
# finies : un test de concurrence qui peut bloquer indefiniment est pire que le
# defaut qu'il surveille.
ATTENTE_MAX_S = 5.0


@pytest.fixture()
def moteur(tmp_path):
    """Une base de FICHIER, pas en memoire.

    En memoire, chaque connexion aurait la sienne : les deux fils ne se
    verraient jamais et le test passerait sans rien exercer.
    """
    moteur = create_engine(f"sqlite:///{tmp_path / 'course.db'}")
    Base.metadata.create_all(moteur, tables=[Bareme.__table__])
    return moteur


@pytest.fixture()
def fabrique_de_sessions(moteur):
    return sessionmaker(bind=moteur)


def test_la_course_entre_deux_requetes_ne_casse_PAS(moteur, fabrique_de_sessions):
    """Un fil suspendu entre sa lecture et son commit, l'autre qui le double.

    AVANT correction : le fil suspendu a lu « aucun bareme », l'autre les cree,
    le premier insere quand meme et casse au commit. APRES : il n'y a plus de
    lecture du tout, donc plus de fenetre — l'ecouteur ne se declenche jamais et
    le rendez-vous expire sans consequence.
    """
    a_lu = threading.Event()
    b_a_fini = threading.Event()
    fil_lent = {}
    incident = {}

    @event.listens_for(moteur, "after_cursor_execute")
    def _suspendre_apres_la_lecture(conn, curseur, requete, parametres, contexte, multiple):  # noqa: ARG001
        est_le_fil_lent = threading.current_thread() is fil_lent.get("objet")
        lit_les_baremes = requete.lstrip().upper().startswith("SELECT") and "bareme" in requete.lower()
        if est_le_fil_lent and lit_les_baremes and not a_lu.is_set():
            a_lu.set()
            b_a_fini.wait(timeout=ATTENTE_MAX_S)

    def travail_du_fil_lent():
        session = fabrique_de_sessions()
        try:
            assurer_baremes(session)
        except Exception as exc:  # noqa: BLE001 — c'est justement ce qu'on mesure
            incident["erreur"] = exc
        finally:
            session.close()

    fil = threading.Thread(target=travail_du_fil_lent)
    fil_lent["objet"] = fil
    fil.start()

    # Si le code ne lit plus, l'ecouteur ne se declenche pas : on n'attend pas
    # indefiniment, on passe. C'est le cas nominal APRES correction.
    a_lu.wait(timeout=2.0)

    autre = fabrique_de_sessions()
    assurer_baremes(autre)
    autre.close()
    b_a_fini.set()

    fil.join(timeout=ATTENTE_MAX_S * 2)
    event.remove(moteur, "after_cursor_execute", _suspendre_apres_la_lecture)

    assert not fil.is_alive(), "le fil suspendu ne s'est jamais termine"
    assert "erreur" not in incident, f"la course a casse : {incident.get('erreur')!r}"

    types = fabrique_de_sessions().execute(select(Bareme.type)).scalars().all()
    assert sorted(types) == sorted(code for code, _ in TYPES_BAREMES)


def test_un_appel_ne_ECRASE_PAS_un_bareme_deja_calibre(fabrique_de_sessions):
    """Le danger de `ON CONFLICT` mal pose : ecraser au lieu d'ignorer.

    Si la correction avait employe `DO UPDATE` — ou un `merge()` — elle rendrait
    ses donnees neutres, a chaque `GET`, a un bareme que l'imprimeur vient de
    calibrer. C'est pire que le 500 : le 500 se voit, une courbe remise a zero
    ne se voit pas.
    """
    session = fabrique_de_sessions()
    assurer_baremes(session)

    calibre = session.get(Bareme, "echenillage")
    calibre.donnees = {"points": [{"x": 1, "y": 2}]}
    session.commit()

    assurer_baremes(session)  # comme en produit n'importe quel `GET` suivant

    relu = fabrique_de_sessions().get(Bareme, "echenillage")
    assert relu.donnees == {"points": [{"x": 1, "y": 2}]}
    assert relu.neutre is False


def test_la_creation_reste_idempotente_en_sequence(fabrique_de_sessions):
    """Le cas que la suite couvrait deja. Il doit continuer a passer."""
    session = fabrique_de_sessions()

    assurer_baremes(session)
    assurer_baremes(session)
    assurer_baremes(session)

    types = fabrique_de_sessions().execute(select(Bareme.type)).scalars().all()
    assert len(types) == len(TYPES_BAREMES)
