# -*- coding: utf-8 -*-
"""Noyau : comptes, sessions, parametres de couts.

MONO-TENANT. Aucune colonne de portee, aucun `entreprise_id`, aucun scope a
verifier : une installation = un imprimeur. C'est un choix de la reprise du
17/08/2026, et c'est ce qui retire d'un coup toute une famille de bugs de fuite
entre clients.
"""
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.types_sql import DecimalTexte


def maintenant() -> datetime:
    """UTC, toujours conscient du fuseau. Un `datetime` naif finit par etre
    compare a un autre naif d'un autre fuseau, et personne ne le voit."""
    return datetime.now(timezone.utc)


class Utilisateur(Base):
    """Le compte de l'atelier.

    Le mot de passe n'est stocke que **hache** — c'est la raison d'etre de
    `reinitialiser-mot-de-passe.bat` dans le package : sans lui, un mot de passe
    perdu bloquerait l'imprimerie sans recours.
    """

    __tablename__ = "utilisateur"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    identifiant: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    mot_de_passe_hache: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(32), nullable=False, default="administrateur")
    cree_le: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=maintenant)

    sessions: Mapped[list["SessionUtilisateur"]] = relationship(
        back_populates="utilisateur", cascade="all, delete-orphan"
    )


class SessionUtilisateur(Base):
    """Une session ouverte, **revocable cote serveur**.

    Le contrat impose la revocation en base : effacer le cookie sur un poste ne
    protege rien si le jeton reste valide ailleurs. C'est aussi pourquoi la
    session est une TABLE et non un jeton signe autoporteur — un jeton signe ne
    se revoque pas.

    `jeton_hache` : on ne stocke jamais le jeton en clair. Il ne vit que dans le
    cookie du navigateur.
    """

    __tablename__ = "session_utilisateur"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    jeton_hache: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    utilisateur_id: Mapped[int] = mapped_column(
        ForeignKey("utilisateur.id", ondelete="CASCADE"), nullable=False
    )
    cree_le: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=maintenant)
    # Expiration ABSOLUE : pas de prolongation glissante. Une session oubliee
    # sur un poste d'atelier finit par expirer, quoi qu'il arrive.
    expire_le: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoquee_le: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    utilisateur: Mapped[Utilisateur] = relationship(back_populates="sessions")


# Les champs que la calibration doit remplir. Tant qu'un seul manque,
# `calibration_faite` est faux et le front n'a pas le droit d'afficher un prix :
# un prix faux est pire qu'une absence de prix.
CHAMPS_CALIBRATION = (
    "cout_exploitation_machine_eur_h",
    "cout_operateur_eur_h",
    "marge_confort_roulage_mm",
    "cliche_prix_couleur_eur",
    "outil_base_eur",
    "outil_par_trace_eur",
    "surcout_forme_speciale_facteur",
    "calage_forfait_eur",
    "finitions_prix_m2_eur",
)


class ParametresCouts(Base):
    """Les tarifs de l'atelier — **une seule ligne**, id 1.

    ⚠️ Tout est NULL a l'installation, sauf la marge. L'application se livre a
    ZERO TARIF : livrer les tarifs d'un autre atelier produirait des devis faux,
    et un devis faux se decouvre chez le client.

    La marge fait exception parce que c'est une decision COMMERCIALE, pas un
    tarif : 30 % par defaut, confirmee explicitement a l'installation.
    """

    __tablename__ = "parametres_couts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    # En POURCENTAGE (0-100). `x (1 + pct/100)` est une marge SUR COUT DE
    # REVIENT, pas un taux de marque — cf. docs/SPEC-METIER.md.
    marge_standard_pct: Mapped[object] = mapped_column(DecimalTexte(16), nullable=False)

    cout_exploitation_machine_eur_h: Mapped[object | None] = mapped_column(DecimalTexte(16))
    cout_operateur_eur_h: Mapped[object | None] = mapped_column(DecimalTexte(16))
    marge_confort_roulage_mm: Mapped[int | None] = mapped_column(Integer)
    cliche_prix_couleur_eur: Mapped[object | None] = mapped_column(DecimalTexte(16))
    outil_base_eur: Mapped[object | None] = mapped_column(DecimalTexte(16))
    outil_par_trace_eur: Mapped[object | None] = mapped_column(DecimalTexte(16))
    surcout_forme_speciale_facteur: Mapped[object | None] = mapped_column(DecimalTexte(16))
    calage_forfait_eur: Mapped[object | None] = mapped_column(DecimalTexte(16))
    finitions_prix_m2_eur: Mapped[object | None] = mapped_column(DecimalTexte(16))

    modifie_le: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=maintenant, onupdate=maintenant
    )

    @property
    def calibration_faite(self) -> bool:
        return all(getattr(self, champ) is not None for champ in CHAMPS_CALIBRATION)
