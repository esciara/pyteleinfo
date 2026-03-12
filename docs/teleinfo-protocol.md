# Protocole Teleinfo (TIC) - Concepts et implementation

Reference: **Enedis-NOI-CPT_02E** v6 (15/02/2017) - *Sorties de tele-information client des appareils de comptage electroniques utilises par Enedis*

## Vue d'ensemble

La **tele-information client (TIC)** est une interface serie unidirectionnelle emise par les compteurs electriques electroniques d'Enedis (anciens compteurs electroniques et Linky). Elle transmet en continu des donnees de comptage sous forme de **trames** composees de **groupes d'information**.

## Trames (Frames)

Une trame est l'unite de transmission complete. Elle contient un instantane de toutes les donnees du compteur a un instant t. Les trames sont emises les unes apres les autres en continu.

### Structure d'une trame

```
STX | Groupe 1 | Groupe 2 | ... | Groupe N | ETX
```

| Element | Caractere ASCII | Valeur hex | Role |
|---------|----------------|------------|------|
| **STX** (Start of TeXt) | `STX` | `0x02` | Debut de la trame |
| **Corps** | — | — | Un ou plusieurs groupes d'information |
| **ETX** (End of TeXt) | `ETX` | `0x03` | Fin de la trame |

- La longueur d'une trame est variable (depend du type de compteur et de sa configuration).
- Entre deux trames consecutives, un silence de **16,7 a 33,4 ms** est menage.
- Entre deux groupes au sein d'une meme trame, le delai ne depasse pas **33,4 ms**.

### Interruption de l'emission

Si le compteur interrompt l'emission (ex. : releve ou programmation en cours), il emet le caractere **EOT** (`0x04`) avant l'interruption, puis reprend par un **STX** (`0x02`) au debut d'une nouvelle trame.

### Implementation dans pyteleinfo

- **`const.py`** : definit `STX_TOKEN = "\x02"`, `ETX_TOKEN = "\x03"`, `EOT_TOKEN = "\x04"`.
- **`codec.encode()`** : encadre les groupes encodes entre `STX` et `ETX`.
- **`codec.decode()`** : verifie la conformite de la trame (presence de `STX`/`ETX`, coherence des delimiteurs `LF`/`CR`), puis extrait et decode chaque groupe.
- **`codec._verify_frame_well_formed()`** : implemente les controles de l'**Etape B** de la specification (verification `STX`, `ETX`, et coherence des paires `LF`/`CR` delimitant les groupes).
- **`exceptions.FrameFormatError`** : levee si la trame est mal formee.

## Groupes d'information (Info Groups)

Chaque groupe d'information est un ensemble coherent constitue d'une **etiquette** (label) identifiant la donnee et d'une **valeur** (data) associee.

### Structure d'un groupe

```
LF | etiquette | SEP | donnee | SEP | controle | CR
```

| Element | Caractere ASCII | Valeur hex | Role |
|---------|----------------|------------|------|
| **LF** (Line Feed) | `LF` | `0x0A` | Debut du groupe |
| **Etiquette** | — | — | Identifie le type de donnee (max 8 caracteres) |
| **Separateur** | `SP` ou `HT` | `0x20` ou `0x09` | Delimite les champs |
| **Donnee** | — | — | Valeur de l'information (longueur variable) |
| **Separateur** | `SP` ou `HT` | `0x20` ou `0x09` | Delimite les champs |
| **Controle** | — | — | Checksum (1 caractere) |
| **CR** (Carriage Return) | `CR` | `0x0D` | Fin du groupe |

### Regles importantes

- Les champs etiquette et donnee ne contiennent que des caracteres ASCII imprimables (`0x20` a `0x7E`).
- L'**etiquette** ne contient jamais le caractere separateur.
- La **donnee** peut contenir le caractere separateur (ex: horodatage avec espaces). Il faut donc parser en partant de la fin pour identifier correctement le dernier separateur et la checksum.

### Implementation dans pyteleinfo

- **`const.py`** : definit `LF_TOKEN = "\n"`, `CR_TOKEN = "\r"`, `SP_TOKEN = "\x20"`, `HT_TOKEN = "\t"`.
- **`codec.decode_info_group()`** : extrait l'etiquette et la donnee d'un groupe encode, avec verification optionnelle du format et de la checksum.
- **`codec._verify_info_group_well_formed()`** : implemente les controles de l'**Etape C** (presence `LF`/`CR`, au moins 2 separateurs, pas de melange `SP`/`HT`).
- **`codec._extract_label_and_data()`** : gere le cas ou le separateur apparait dans le champ donnee en ne splitant que sur le premier separateur (conforme aux Etapes 6-12 de la spec).
- **`exceptions.InfoGroupFormatError`** : levee si un groupe est mal forme.

## Separateurs

Deux caracteres separateurs sont possibles :

| Separateur | Caractere | Hex | Usage |
|-----------|-----------|-----|-------|
| **SP** (Space) | ` ` | `0x20` | Compteurs concus **avant 2013** |
| **HT** (Horizontal Tab) | `\t` | `0x09` | Compteurs concus **apres 2013** (propose par la normalisation) |

Pour un meme compteur, tous les groupes de toutes les trames utilisent le meme separateur. L'implementation supporte les deux et les detecte automatiquement.

## Checksum (Champ controle)

La checksum permet de verifier l'integrite de chaque groupe d'information. Il existe deux modes de calcul :

### Mode 1 (compteurs <= 2013)

Zone de calcul : du debut de l'etiquette a la **fin du champ donnee** (le dernier separateur est **exclu**).

### Mode 2 (compteurs > 2013)

Zone de calcul : du debut de l'etiquette au **separateur apres le champ donnee** (le dernier separateur est **inclus**).

### Algorithme commun

1. Sommer les valeurs ASCII de tous les caracteres de la zone.
2. Ne garder que l'octet de poids faible.
3. Appliquer un ET logique avec `0x3F` (ne garder que les 6 bits de poids faible).
4. Ajouter `0x20`.

Le resultat est toujours un caractere ASCII imprimable (`0x20` a `0x5F`).

### Implementation dans pyteleinfo

- **`codec._checksum()`** : implemente l'algorithme commun (`(sum & 0x3F) + 0x20`).
- **`codec._checksum_method_1()`** : appelle `_checksum()` en excluant le dernier caractere (le separateur final).
- **`codec._checksum_method_2()`** : appelle `_checksum()` sur la totalite (separateur final inclus).
- **`codec._verify_checksum()`** : calcule les deux checksums et accepte la donnee si l'une des deux correspond. Cela rend l'implementation compatible avec tous les types de compteurs sans configuration prealable.
- **`exceptions.ChecksumError`** : levee si aucun des deux modes ne valide la checksum recue.

## Codage des caracteres serie

Chaque caractere est transmis sous la forme de **10 bits** :

| Bit | Role |
|-----|------|
| Start bit | `0` logique |
| Bits 0-6 | Caractere en ASCII 7 bits (LSB en premier) |
| Bit parite | Parite paire |
| Stop bit | `1` logique |

### Implementation dans pyteleinfo

- **`settings.py`** (`TeleinfoSettings`) : configure les parametres serie conformement a la specification :
    - `baudrate = 1200` (debit standard de la TIC historique)
    - `bytesize = SEVENBITS` (7 bits de donnees ASCII)
    - `parity = PARITY_EVEN` (parite paire)
    - `stopbits = STOPBITS_ONE` (1 bit de stop)
    - `rtscts = 1` (controle de flux materiel)
- Ces parametres sont injectables via des variables d'environnement prefixees `TELEINFO_` grace a Pydantic Settings.

## Lecture serie et decodage (CLI)

Le module console fournit deux commandes :

- **`teleinfo port <device>`** : lit les trames sur un port serie donne et les affiche en JSON decode (ou brut avec `--raw`).
- **`teleinfo discover`** : scanne automatiquement tous les ports serie disponibles pour trouver celui qui recoit des trames teleinfo valides.

### Flux de traitement

```
Port serie
  -> async_receive_frame() : lecture jusqu'au ETX
  -> decode() : verification de la trame + extraction des groupes
  -> decode_info_group() : pour chaque groupe, verification format + checksum + extraction label/data
  -> Sortie JSON : { "ADCO": "050022120078", "OPTARIF": "HC..", ... }
```

La premiere trame recue est systematiquement ecartee (`_discard_potentially_incomplete_first_frame`) car la connexion au port serie peut intervenir au milieu d'une emission.

## Exemples

### Trame brute (format texte)

```
\x02
\nADCO 050022120078 2\r
\nOPTARIF HC.. <\r
\n...\r
\x03
```

### Trame decodee (JSON)

```json
{
  "ADCO": "050022120078",
  "OPTARIF": "HC.."
}
```

### Encodage d'un groupe

Pour l'etiquette `ADCO` et la donnee `050022120078` :

1. Concatenation : `ADCO 050022120078 ` (etiquette + SP + donnee + SP)
2. Calcul checksum mode 1 (sur `ADCO 050022120078`) : resultat = `2`
3. Groupe final : `LF` + `ADCO 050022120078 2` + `CR`
