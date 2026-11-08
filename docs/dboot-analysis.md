# dBoot 1.5 — séquence de démarrage et bascule Windows CE

Analyse statique de `dboot.exe` et `dmenu.exe` (dBoot 1.5, MediaNav Evolution,
Windows CE 6.0, MIPS little-endian). Les adresses ci-dessous valent pour la version
dont la somme SHA-256 est vérifiée dans `scripts/patch_dboot.py`.

## Ce que fait dBoot au démarrage

1. Initialise l'écran et le tactile, charge le clavier logiciel.
2. **Si `\Storage Card3\StartWinCE` existe** : il efface ce fichier, (re)crée les
   raccourcis du bureau et lance `\Windows\explorer.exe` → **bureau Windows CE**.
3. **Sinon (cas normal)** : il lance l'application MediaNav (l'« UpgradeManager »
   avec son argument de lancement) → autoradio normal.
4. Pendant une courte fenêtre après le logo, un **geste** (glissé horizontal sur le
   logo) crée `\Storage Card3\StartWinCE` puis redémarre : au reboot suivant, on
   tombe donc sur le bureau Windows CE.

`\Storage Card3\` est un petit stockage interne persistant, vide par défaut ; c'est
le « drapeau » que lit dBoot pour choisir entre MediaNav et Windows CE.

## Le patch (lot « bouton »)

`patch_dboot.py` applique trois modifications, chacune vérifiée octet par octet :

1. **Bouton tactile** : le handler `WM_LBUTTONDOWN` est dérouté vers un petit bloc
   ajouté dans une zone libre du segment `.text`. Ce bloc lit les coordonnées de
   l'appui ; si `x ≥ 560` et `y ≥ 360` (quart bas-droit d'un écran 800×480), il saute
   directement au code de bascule Windows CE d'origine. Le glissé horizontal reste
   fonctionnel en secours.
2. **Libellé** : le rectangle de texte dessiné en bas est repositionné et son contenu
   remplacé par `[  Windows CE  ]` (même longueur que la chaîne d'origine).
3. **Fenêtre d'accès** : le délai d'affichage passe de 5 s à 10 s.

Le patch est réversible : on garde l'original et on remet l'ancien `dboot.exe` pour
revenir en arrière.

## Le redémarrage forcé sous Windows CE

Sous Windows CE (branche `StartWinCE`), ni l'application MediaNav ni le gestionnaire
MICOM ne tournent. Or le micro-contrôleur (MICOM) attend un **signal de vie
périodique** ; sans lui, son chien de garde **redémarre l'unité au bout d'environ
2 min 20**. Ce minuteur n'est pas dans le code Windows CE : il est dans le firmware du
MICOM, qu'on ne modifie pas. La solution n'est donc pas de le désactiver mais de lui
**envoyer le bon signal** — voir `micom-protocol.md` et `build_micomm_pause.py`.

## Zones à ne jamais toucher

`NK.BIN`, `NA.BIN`, `NB.BIN` (images noyau) et les fichiers de configuration véhicule
/ antivol. Une erreur à ces endroits peut rendre l'unité inutilisable ou déclencher
la demande de code antivol.
