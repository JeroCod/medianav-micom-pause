# MediaNav Evolution — outils Windows CE (dBoot 1.5)

Deux petits outils de reverse engineering pour les autoradios **MediaNav Evolution**
(unités LG `LAN5xxx`, Windows CE 6.0 sur MIPS), montés sur de nombreux véhicules
**Dacia / Renault / Nissan** des années ~2012-2016.

Ils résolvent deux problèmes bien connus des bricoleurs de ces unités :

1. **Accéder au bureau Windows CE** proprement, par un bouton tactile, au lieu du
   geste capricieux sur le logo.
2. **Empêcher le redémarrage forcé** (~2 min 20) qui survient dès qu'on est sous
   Windows CE, parce que plus personne n'envoie le « signal de vie » attendu par le
   micro-contrôleur (MICOM).

> ⚠️ **Aucun binaire propriétaire n'est inclus ici.** Ces scripts *patchent votre
> propre copie* des fichiers d'origine (dont la somme SHA-256 est vérifiée avant
> toute modification). Reverse engineering à fin d'interopérabilité et d'usage
> personnel. **Aucune garantie** : voir la section Sécurité.

## Les outils (`scripts/`)

| Script | Rôle |
|---|---|
| `patch_dboot.py` | Patche `dboot.exe` (dBoot 1.5) : ajoute un **bouton « Windows CE »** tactile en bas à droite et allonge la fenêtre d'accès de 5 à 10 s. Le geste d'origine reste actif en secours. |
| `build_micomm_pause.py` | Construit `micomm_pause.exe` à partir de `dmenu.exe` : envoie au MICOM la **séquence de vie** (ouverture `FD` + `07 01`, puis `FF` chaque seconde) qui **met en pause le chien de garde**. À lancer une fois sous Windows CE. |
| `decode_micomm_pause.py` | Décode le petit journal de diagnostic (180 octets) écrit par `micomm_pause.exe`. |
| `mipsenc.py` | Mini-encodeur d'instructions MIPS32, utilisé par les scripts de build. |

## Pré-requis

- Python 3 (aucune dépendance externe).
- **Vos propres fichiers d'origine**, copiés depuis votre unité :
  `dboot.exe` et `dmenu.exe` (dans `\Storage Card\System\`).
- Un relecteur de désassemblage (radare2 ou capstone) est recommandé pour vérifier
  la sortie, mais pas requis pour exécuter.

## Utilisation

```bash
# 1) Bouton d'accès Windows CE
python3 -I scripts/patch_dboot.py  dboot.exe  dboot_patched.exe

# 2) Signal de vie MICOM (anti-redémarrage)
python3 -I scripts/build_micomm_pause.py  dmenu.exe  micomm_pause.exe

# 3) Lire le journal de diagnostic récupéré sur la clé USB
python3 -I scripts/decode_micomm_pause.py  micompause.log
```

Chaque script **vérifie la somme SHA-256** du fichier d'origine et contrôle octet par
octet chaque zone modifiée : s'il ne reconnaît pas votre binaire, il s'arrête sans
rien écrire. Copiez ensuite le fichier produit sur l'unité via le gestionnaire de
fichiers de Windows CE (TTCMD / Total Commander), en **gardant l'original** pour
pouvoir revenir en arrière.

`micomm_pause.exe` se lance une fois par session Windows CE ; tant qu'il tourne, le
chien de garde reste en pause. On l'arrête via le gestionnaire de tâches (ITaskMgr).
Sans clé USB branchée, il n'écrit pas de journal mais continue d'envoyer le signal.

## Comment ça marche

- `docs/dboot-analysis.md` — ce que fait dBoot 1.5 au démarrage, où se trouve la
  bascule Windows CE, les zones patchées.
- `docs/micom-protocol.md` — le format des trames série du MICOM et la séquence de
  vie qui désactive le chien de garde.

## Sécurité — à lire avant de toucher à quoi que ce soit

- **Sauvegardez d'abord l'intégralité de l'unité** (toutes les `Storage Card`), avec
  des sommes de contrôle. Une mauvaise manipulation peut tout perdre.
- **Ne touchez jamais** aux fichiers de configuration véhicule ni au fichier
  d'antivol (p. ex. `Antitheft.cfg`, la config MICOM du véhicule) : les effacer ou
  les corrompre peut déclencher une demande de code antivol au redémarrage.
- **Ne touchez jamais** aux images noyau (`NK.BIN`, `NA.BIN`, `NB.BIN`) : zone rouge.
- Travaillez **moteur en marche**, sans couper le contact pendant une copie.
- Gardez toujours l'original de chaque fichier modifié pour revenir en arrière.

Fourni **tel quel, sans aucune garantie**. Vous êtes seul responsable de ce que vous
faites de votre matériel. Ces outils n'embarquent aucun code propriétaire et ne
servent qu'à l'interopérabilité avec du matériel que vous possédez.

## Licence

Code sous licence MIT (voir `LICENSE`). Les marques et binaires cités appartiennent à
leurs propriétaires respectifs et ne sont pas distribués ici.
