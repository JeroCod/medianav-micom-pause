# Protocole MICOM et signal de vie

Le MICOM est le micro-contrôleur de l'unité MediaNav. L'application MediaNav lui parle
par une liaison série (UART, `COM2`). Il gère l'alimentation, les boutons physiques,
l'antivol… et surtout un **chien de garde** : s'il ne reçoit pas de signal de vie
périodique, il considère le système principal planté et **redémarre l'unité**
(observé : ~2 min 20 sous Windows CE, quand plus rien ne lui parle).

## Format des trames

```
AA  [mgr << 4 | groupe]  cmd  longueur  [données...]  XOR
```

- `AA` : octet de début.
- `mgr`/`groupe` : identifiant d'émetteur et de groupe.
- `cmd` : commande.
- `longueur` : nombre d'octets de données.
- `XOR` : somme de contrôle (ou exclusif des octets précédents).

Exemple de la trame de vie : `AA 11 FF 00 44`.

## Séquence qui met le chien de garde en pause

C'est exactement ce qu'envoient l'« UpgradeManager » et le gestionnaire MICOM au
démarrage normal :

1. **Ouverture** : commande `0xFD` sans donnée.
2. **Ouverture (suite)** : commande `0x07` avec la donnée `0x01`.
3. **Signal de vie** : commande `0xFF`, répétée **chaque seconde**.

Tant que le signal `0xFF` arrive à intervalle régulier, le chien de garde reste en
pause et l'unité ne redémarre pas. `build_micomm_pause.py` produit un exécutable
Windows CE qui ouvre `COM2`, joue la séquence d'ouverture, puis boucle sur le signal
de vie une fois par seconde.

## Journal de diagnostic

`micomm_pause.exe` écrit un résumé binaire de **180 octets** (réécrit chaque seconde)
sur la clé USB, que `decode_micomm_pause.py` interprète :

| Offset | Champ |
|---|---|
| 0 | signature `KDG1` |
| 4 | nombre d'itérations (≈ secondes de signal) |
| 8 | ouverture de `COM2` (`1` = OK) |
| 12 / 16 / 20 | code d'attente de réponse après `FD` / `07` / `FF` (`0` = réponse reçue, `0x102` = rien) |
| 24 / 28 / 32 | nombre d'octets reçus après `FD` / `07` / dernier `FF` |
| 36 / 84 / 132 | jusqu'à 48 octets de réponse reçus (`FD` / `07` / `FF`) |

En pratique, le MICOM renvoie un octet d'acquittement à chaque commande, ce qui
confirme que la liaison est établie et le chien de garde en pause.

## Sécurité intégrée

L'exécutable construit **ne peut pas redémarrer l'appareil** : l'import
`SetSystemPowerState` est réaffecté à `Sleep`. Il ne fait que parler au MICOM sur le
port série.
