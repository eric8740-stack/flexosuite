=============================================================================
  FlexoSuite - installation sur le serveur de l'imprimerie
  Notice destinee au technicien informatique
=============================================================================

CE QU'IL FAUT SAVOIR AVANT DE COMMENCER
---------------------------------------
L'application est autonome. Elle n'installe RIEN sur le serveur : ni Python,
ni base de donnees, ni serveur web. Tout est dans ce dossier.

Le code et les donnees sont separes, volontairement :

  - le CODE     : ce dossier, remplace a chaque mise a jour
  - les DONNEES : C:\ProgramData\FlexoSuite, jamais touchees

Une mise a jour ne peut donc pas detruire les devis.


INSTALLATION (une seule fois)
-----------------------------
  1. Copiez ce dossier sur le serveur, par exemple C:\FlexoSuite
     ATTENTION : evitez les chemins tres longs et les dossiers synchronises
     (OneDrive, Dropbox). Un chemin trop long fait echouer la decompression.

  2. Double-cliquez sur       installer.bat

     Le script prepare C:\ProgramData\FlexoSuite et cree la base. Il est
     relancable sans risque : il ne reecrit jamais une base existante.


DEMARRAGE
---------
  Double-cliquez sur          demarrer-flexosuite.bat

  Le navigateur s'ouvre sur http://127.0.0.1:8000/
  Fermer la fenetre noire arrete l'application.


ACCES DEPUIS LES AUTRES POSTES DU RESEAU
----------------------------------------
  1. Ouvrez C:\ProgramData\FlexoSuite\app.env
  2. Remplacez    HOST=127.0.0.1    par    HOST=0.0.0.0
  3. Autorisez le port dans le pare-feu Windows, en administrateur :

     netsh advfirewall firewall add rule name="FlexoSuite" dir=in action=allow protocol=TCP localport=8000

  4. Relancez demarrer-flexosuite.bat

  Les autres postes ouvrent alors  http://<IP-du-serveur>:8000/


DEMARRAGE AUTOMATIQUE AU BOOT (optionnel)
-----------------------------------------
  Clic droit sur              installer-service.bat
  puis "Executer en tant qu'administrateur".

  A savoir : la tache tourne sous le compte SYSTEME. Si des fichiers d'import
  vivent sur un partage reseau, SYSTEME n'y a pas acces - utilisez alors un
  compte de service dedie.


MISE A JOUR
-----------
  Double-cliquez sur          mettre-a-jour.bat
  puis indiquez le dossier du nouveau package.

  Le script arrete l'application, remplace le code, sauvegarde la base, migre,
  et compare une empreinte de la base avant et apres. Les donnees restent en
  place. Une copie d'avant migration est conservee sous le nom
  prod.avant-maj.db


MOT DE PASSE ADMINISTRATEUR PERDU
---------------------------------
  Double-cliquez sur          reinitialiser-mot-de-passe.bat

  Le mot de passe n'est stocke que sous forme hachee : il est impossible de le
  retrouver. Ce script permet d'en definir un nouveau. Il ne touche a aucune
  donnee metier. L'application doit etre arretee.


OU SONT LES CHOSES
------------------
  Base de donnees   C:\ProgramData\FlexoSuite\prod.db
  Configuration     C:\ProgramData\FlexoSuite\app.env
  Journaux          C:\ProgramData\FlexoSuite\logs\

  Pour une sauvegarde : copiez tout le dossier C:\ProgramData\FlexoSuite,
  application arretee.


EN CAS DE PROBLEME
------------------
  "Python embarque introuvable"   -> le package est incomplet, redemandez-le.
  "Le port 8000 est deja utilise" -> l'application tourne deja, ou un autre
                                     logiciel occupe le port. Changez PORT
                                     dans app.env.
  Les migrations echouent         -> consultez
                                     C:\ProgramData\FlexoSuite\logs\migrations.log
