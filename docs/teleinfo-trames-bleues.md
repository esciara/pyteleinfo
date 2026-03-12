# Trames bleues - Teleinfo historique

Reference: **Enedis-MOP-CPT_007E** v1 (15/09/2025), remplace **Enedis-NOI-CPT_02E** v6 (15/02/2017)

Ce document decrit les trames de tele-information client emises par les compteurs electroniques "bleus" utilises par Enedis. Il s'agit du mode **historique** de la TIC (1200 bauds, separateur SP).

## Appareils de comptage couverts

Le document de specification couvre 4 types d'appareils "bleus" :

| Sigle | Nom complet | Type |
|-------|-------------|------|
| **Concentrateur** | Concentrateur de telereport | Concentrateur de donnees multi-compteurs |
| **CBEMM** | Compteur "Bleu" electronique monophase multitarif | Monophase, sans puissance apparente |
| **CBEMM ICC** | Compteur "Bleu" electronique monophase multitarif (evolution ICC) | Monophase, avec puissance apparente (PAPP) |
| **CBETM** | Compteur "Bleu" electronique triphase multitarif | Triphase, trames longues + courtes |

## Differences entre les compteurs

### Concentrateur de telereport

- Appareil de **concentration** de donnees, pas un compteur individuel.
- Identifie par le label `ADCO` (adresse du concentrateur, 12 caracteres).
- Fournit les **index d'energie** par option tarifaire (Base, HC, EJP) ainsi qu'un index gaz (`GAZ`) et un index tiers (`AUTRE`).
- **Ne fournit pas** de donnees instantanees (pas d'intensite, pas de puissance).
- Index sur **8 caracteres** (vs 9 pour les compteurs individuels).
- Separateur : SP (espace). Checksum : mode 1.

### CBEMM (monophase)

- Compteur individuel **monophase** multitarif.
- Fournit les index d'energie par option tarifaire : Base, Heures Creuses, EJP, et **Tempo** (6 index HC/HP par couleur de jour).
- Fournit des donnees **instantanees** : intensite (`IINST`, 1 phase), intensite max (`IMAX`), alerte depassement (`ADPS`).
- **Ne fournit PAS** la puissance apparente (`PAPP`) - c'est la difference majeure avec le CBEMM ICC.
- Index sur **9 caracteres**.
- Fournit aussi : preavis EJP (`PEJP`), couleur du lendemain Tempo (`DEMAIN`), horaire HP/HC (`HHPHC`).

### CBEMM ICC (monophase, evolution ICC)

- **Identique au CBEMM** a une exception pres : il ajoute la **puissance apparente** (`PAPP`, 5 caracteres, en VA).
- C'est la version la plus repandue des compteurs "bleus" monophases (y compris avant l'arrivee du Linky).

### CBETM (triphase)

- Compteur individuel **triphase** multitarif.
- Fournit les memes index tarifaires que le CBEMM.
- Donnees instantanees **par phase** : `IINST1`/`IINST2`/`IINST3`, `IMAX1`/`IMAX2`/`IMAX3`.
- Ajoute la **puissance maximale triphasee** (`PMAX`, en W) et la **puissance apparente** (`PAPP`, en VA).
- Ajoute la **presence des potentiels** (`PPOT`) pour verifier la tension sur chaque phase.
- Possede **deux types de trames** :
  - **Trames longues** : emises en situation normale, contiennent toutes les donnees.
  - **Trames courtes** : emises lors d'un depassement d'intensite souscrite sur une phase. Contiennent les alertes de depassement (`ADIR1`/`ADIR2`/`ADIR3`), l'adresse du compteur, et les intensites instantanees par phase.
- Lors d'un depassement : cycles de 20 trames courtes suivies d'une trame longue, pendant la duree du depassement + 1 minute.

### Tableau recapitulatif des differences

| Fonctionnalite | Concentrateur | CBEMM | CBEMM ICC | CBETM |
|---------------|:---:|:---:|:---:|:---:|
| Index energie (Base, HC, EJP, Tempo) | Oui (8 car.) | Oui (9 car.) | Oui (9 car.) | Oui (9 car.) |
| Index gaz / tiers (GAZ, AUTRE) | Oui | Non | Non | Non |
| Intensite souscrite (ISOUSC) | Non | Oui | Oui | Oui |
| Intensite instantanee monophasee (IINST) | Non | Oui | Oui | Non |
| Intensite instantanee par phase (IINSTi) | Non | Non | Non | Oui |
| Intensite max monophasee (IMAX) | Non | Oui | Oui | Non |
| Intensite max par phase (IMAXi) | Non | Non | Non | Oui |
| Alerte depassement mono (ADPS) | Non | Oui | Oui | Non |
| Alerte depassement par phase (ADIRi) | Non | Non | Non | Oui |
| Puissance apparente (PAPP) | Non | **Non** | **Oui** | Oui |
| Puissance max triphasee (PMAX) | Non | Non | Non | Oui |
| Presence des potentiels (PPOT) | Non | Non | Non | Oui |
| Trames courtes (depassement) | Non | Non | Non | Oui |

## Options tarifaires

L'option tarifaire (`OPTARIF`, 4 caracteres) determine quels index d'energie sont emis dans la trame :

| Valeur OPTARIF | Option tarifaire | Index emis |
|----------------|-----------------|------------|
| `BASE` | Base | BASE |
| `HC..` | Heures Creuses | HCHC, HCHP |
| `EJP.` | EJP | EJPHN, EJPHPM |
| `BBRx` | Tempo | BBRHCJB, BBRHPJB, BBRHCJW, BBRHPJW, BBRHCJR, BBRHPJR |

Pour Tempo, `x` est un caractere ASCII imprimable reflétant les programmes de commande des circuits de sortie a contacts auxiliaires.

## Periodes tarifaires en cours

La periode tarifaire en cours (`PTEC`, 4 caracteres) indique le poste horaire actif :

| Valeur PTEC | Signification |
|-------------|--------------|
| `TH..` | Toutes les Heures |
| `HC..` | Heures Creuses |
| `HP..` | Heures Pleines |
| `HN..` | Heures Normales |
| `PM..` | Heures de Pointe Mobile |
| `HCJB` | Heures Creuses Jours Bleus |
| `HCJW` | Heures Creuses Jours Blancs (White) |
| `HCJR` | Heures Creuses Jours Rouges |
| `HPJB` | Heures Pleines Jours Bleus |
| `HPJW` | Heures Pleines Jours Blancs (White) |
| `HPJR` | Heures Pleines Jours Rouges |

Note : le caractere `.` correspond au caractere ASCII point (`.`).

## Couleur du lendemain (Tempo)

La couleur du lendemain (`DEMAIN`, 4 caracteres) n'est emise que pour les compteurs programmes en option Tempo :

| Valeur | Signification |
|--------|--------------|
| `----` | Couleur du lendemain non connue |
| `BLEU` | Lendemain jour Bleu |
| `BLAN` | Lendemain jour Blanc |
| `ROUG` | Lendemain jour Rouge |

## Etats de la sortie TIC

La sortie TIC de chaque compteur peut etre programmee dans 3 etats :

| Etat | Description |
|------|------------|
| **Metrologie** | Impulsion a 50 kHz (1-20 ms) a chaque Wh consomme |
| **Veille** | Trame reduite, contient uniquement `ADCO` |
| **Tele-information** | Trames completes avec toutes les donnees tarifaires |

## Table complete des etiquettes

### Tableau 1 : Concentrateur de telereport

| Designation | Etiquette | Nb car. | Unite | Description |
|-------------|-----------|---------|-------|-------------|
| Adresse du concentrateur | `ADCO` | 12 | | 12 caracteres ASCII numeriques |
| Option tarifaire choisie | `OPTARIF` | 4 | | BASE, HC.., EJP. |
| Index option Base | `BASE` | 8 | Wh | Chaine ASCII numerique |
| Index Heures Creuses | `HCHC` | 8 | Wh | Chaine ASCII numerique |
| Index Heures Pleines | `HCHP` | 8 | Wh | Chaine ASCII numerique |
| Index EJP Heures Normales | `EJPHN` | 8 | Wh | Chaine ASCII numerique |
| Index EJP Heures Pointe Mobile | `EJPHPM` | 8 | Wh | Chaine ASCII numerique |
| Index gaz | `GAZ` | 7 | dal | Chaine ASCII numerique |
| Index troisieme compteur | `AUTRE` | 7 | dal | Chaine ASCII numerique |
| Periode Tarifaire en cours | `PTEC` | 4 | | TH.., HC.., HP.., HN.., PM.. |
| Mot d'etat du compteur | `MOTDETAT` | 6 | | Reserve au distributeur (10 car. dans la spec MOP-CPT_007E) |

### Tableau 2 : CBEMM (monophase multitarif)

| Designation | Etiquette | Nb car. | Unite | Description |
|-------------|-----------|---------|-------|-------------|
| Adresse du compteur | `ADCO` | 12 | | 12 caracteres ASCII numeriques |
| Option tarifaire choisie | `OPTARIF` | 4 | | BASE, HC.., EJP., BBRx |
| Intensite souscrite | `ISOUSC` | 2 | A | Intensite souscrite (= puissance souscrite / 200) |
| Index option Base | `BASE` | 9 | Wh | |
| Index HC Heures Creuses | `HCHC` | 9 | Wh | |
| Index HC Heures Pleines | `HCHP` | 9 | Wh | |
| Index EJP Heures Normales | `EJPHN` | 9 | Wh | |
| Index EJP Heures Pointe Mobile | `EJPHPM` | 9 | Wh | |
| Index Tempo HC Jours Bleus | `BBRHCJB` | 9 | Wh | |
| Index Tempo HP Jours Bleus | `BBRHPJB` | 9 | Wh | |
| Index Tempo HC Jours Blancs | `BBRHCJW` | 9 | Wh | |
| Index Tempo HP Jours Blancs | `BBRHPJW` | 9 | Wh | |
| Index Tempo HC Jours Rouges | `BBRHCJR` | 9 | Wh | |
| Index Tempo HP Jours Rouges | `BBRHPJR` | 9 | Wh | |
| Preavis Debut EJP (30 min) | `PEJP` | 2 | min | Uniquement en option EJP, pendant preavis et pointe mobile |
| Periode Tarifaire en cours | `PTEC` | 4 | | Voir table periodes tarifaires |
| Couleur du lendemain | `DEMAIN` | 4 | | Uniquement en option Tempo |
| Intensite Instantanee | `IINST` | 3 | A | Intensite efficace instantanee |
| Avertissement Depassement Puissance Souscrite | `ADPS` | 3 | A | Emis quand puissance > puissance souscrite |
| Intensite maximale appelee | `IMAX` | 3 | A | |
| Horaire Heures Pleines/Heures Creuses | `HHPHC` | 1 | | A, C, D, E ou Y selon programmation |
| Mot d'etat du compteur | `MOTDETAT` | 6 | | Reserve au distributeur |

### Tableau 3 : CBEMM ICC (monophase multitarif, evolution ICC)

Identique au Tableau 2 avec l'ajout suivant :

| Designation | Etiquette | Nb car. | Unite | Description |
|-------------|-----------|---------|-------|-------------|
| Puissance apparente | `PAPP` | 5 | VA | Arrondie a la dizaine de VA la plus proche |

### Tableau 4 : CBETM trames longues (triphase multitarif)

| Designation | Etiquette | Nb car. | Unite | Description |
|-------------|-----------|---------|-------|-------------|
| Adresse du compteur | `ADCO` | 12 | | 12 caracteres ASCII numeriques |
| Option tarifaire choisie | `OPTARIF` | 4 | | BASE, HC.., EJP., BBRx |
| Intensite souscrite | `ISOUSC` | 2 | A | Puissance souscrite / 200 / 3 |
| Index option Base | `BASE` | 9 | Wh | |
| Index HC Heures Creuses | `HCHC` | 9 | Wh | |
| Index HC Heures Pleines | `HCHP` | 9 | Wh | |
| Index EJP Heures Normales | `EJPHN` | 9 | Wh | |
| Index EJP Heures Pointe Mobile | `EJPHPM` | 9 | Wh | |
| Index Tempo HC Jours Bleus | `BBRHCJB` | 9 | Wh | |
| Index Tempo HP Jours Bleus | `BBRHPJB` | 9 | Wh | |
| Index Tempo HC Jours Blancs | `BBRHCJW` | 9 | Wh | |
| Index Tempo HP Jours Blancs | `BBRHPJW` | 9 | Wh | |
| Index Tempo HC Jours Rouges | `BBRHCJR` | 9 | Wh | |
| Index Tempo HP Jours Rouges | `BBRHPJR` | 9 | Wh | |
| Preavis Debut EJP (30 min) | `PEJP` | 2 | min | Option EJP uniquement |
| Periode Tarifaire en cours | `PTEC` | 4 | | |
| Couleur du lendemain | `DEMAIN` | 4 | | Option Tempo uniquement |
| Intensite Instantanee phase 1 | `IINST1` | 3 | A | Intensite efficace a +/- 0.5 A |
| Intensite Instantanee phase 2 | `IINST2` | 3 | A | |
| Intensite Instantanee phase 3 | `IINST3` | 3 | A | |
| Intensite maximale phase 1 | `IMAX1` | 3 | A | |
| Intensite maximale phase 2 | `IMAX2` | 3 | A | |
| Intensite maximale phase 3 | `IMAX3` | 3 | A | |
| Puissance maximale triphasee atteinte | `PMAX` | 5 | W | Arrondie a la dizaine la plus proche |
| Puissance apparente triphasee | `PAPP` | 5 | VA | Arrondie a la dizaine la plus proche |
| Horaire Heures Pleines/Heures Creuses | `HHPHC` | 1 | | A, C, D, E ou Y |
| Mot d'etat du compteur | `MOTDETAT` | 6 | | Reserve au distributeur |
| Presence des potentiels | `PPOT` | 2 | | Codage binaire : bit 1=phase 1, bit 2=phase 2, bit 3=phase 3 |

### Tableau 5 : CBETM trames courtes (triphase, depassement)

Emises lors d'un depassement d'intensite souscrite sur l'une des 3 phases :

| Designation | Etiquette | Nb car. | Unite | Description |
|-------------|-----------|---------|-------|-------------|
| Avert. Depassement intensite phase 1 | `ADIR1` | 3 | A | Emis si depassement sur phase 1 |
| Avert. Depassement intensite phase 2 | `ADIR2` | 3 | A | Emis si depassement sur phase 2 |
| Avert. Depassement intensite phase 3 | `ADIR3` | 3 | A | Emis si depassement sur phase 3 |
| Adresse du compteur | `ADCO` | 12 | | |
| Intensite Instantanee phase 1 | `IINST1` | 3 | A | |
| Intensite Instantanee phase 2 | `IINST2` | 3 | A | |
| Intensite Instantanee phase 3 | `IINST3` | 3 | A | |

## Table unique de toutes les etiquettes

Recapitulatif de toutes les etiquettes uniques presentes dans la specification trames bleues :

| Etiquette | Designation | Nb car. | Unite | Compteurs concernes |
|-----------|-------------|---------|-------|-------------------|
| `ADCO` | Adresse du compteur/concentrateur | 12 | | Tous |
| `ADIR1` | Avert. depassement intensite phase 1 | 3 | A | CBETM (trame courte) |
| `ADIR2` | Avert. depassement intensite phase 2 | 3 | A | CBETM (trame courte) |
| `ADIR3` | Avert. depassement intensite phase 3 | 3 | A | CBETM (trame courte) |
| `ADPS` | Avert. depassement puissance souscrite | 3 | A | CBEMM, CBEMM ICC |
| `AUTRE` | Index troisieme compteur | 7 | dal | Concentrateur |
| `BASE` | Index option Base | 8-9 | Wh | Tous |
| `BBRHCJB` | Index Tempo HC Jours Bleus | 9 | Wh | CBEMM, CBEMM ICC, CBETM |
| `BBRHCJR` | Index Tempo HC Jours Rouges | 9 | Wh | CBEMM, CBEMM ICC, CBETM |
| `BBRHCJW` | Index Tempo HC Jours Blancs | 9 | Wh | CBEMM, CBEMM ICC, CBETM |
| `BBRHPJB` | Index Tempo HP Jours Bleus | 9 | Wh | CBEMM, CBEMM ICC, CBETM |
| `BBRHPJR` | Index Tempo HP Jours Rouges | 9 | Wh | CBEMM, CBEMM ICC, CBETM |
| `BBRHPJW` | Index Tempo HP Jours Blancs | 9 | Wh | CBEMM, CBEMM ICC, CBETM |
| `DEMAIN` | Couleur du lendemain (Tempo) | 4 | | CBEMM, CBEMM ICC, CBETM |
| `EJPHN` | Index EJP Heures Normales | 8-9 | Wh | Tous |
| `EJPHPM` | Index EJP Heures Pointe Mobile | 8-9 | Wh | Tous |
| `GAZ` | Index gaz | 7 | dal | Concentrateur |
| `HCHC` | Index Heures Creuses | 8-9 | Wh | Tous |
| `HCHP` | Index Heures Pleines | 8-9 | Wh | Tous |
| `HHPHC` | Horaire Heures Pleines/Heures Creuses | 1 | | CBEMM, CBEMM ICC, CBETM |
| `IINST` | Intensite Instantanee (monophase) | 3 | A | CBEMM, CBEMM ICC |
| `IINST1` | Intensite Instantanee phase 1 | 3 | A | CBETM |
| `IINST2` | Intensite Instantanee phase 2 | 3 | A | CBETM |
| `IINST3` | Intensite Instantanee phase 3 | 3 | A | CBETM |
| `IMAX` | Intensite maximale appelee (monophase) | 3 | A | CBEMM, CBEMM ICC |
| `IMAX1` | Intensite maximale phase 1 | 3 | A | CBETM |
| `IMAX2` | Intensite maximale phase 2 | 3 | A | CBETM |
| `IMAX3` | Intensite maximale phase 3 | 3 | A | CBETM |
| `ISOUSC` | Intensite souscrite | 2 | A | CBEMM, CBEMM ICC, CBETM |
| `MOTDETAT` | Mot d'etat du compteur | 6 | | Tous |
| `OPTARIF` | Option tarifaire choisie | 4 | | Tous |
| `PAPP` | Puissance apparente | 5 | VA | CBEMM ICC, CBETM |
| `PEJP` | Preavis debut EJP (30 min) | 2 | min | CBEMM, CBEMM ICC, CBETM (option EJP) |
| `PMAX` | Puissance maximale triphasee atteinte | 5 | W | CBETM |
| `PPOT` | Presence des potentiels | 2 | | CBETM |
| `PTEC` | Periode Tarifaire en cours | 4 | | Tous |

## Caracteres ASCII speciaux utilises dans le protocole

### Caracteres speciaux (non imprimables)

| Symbole | Signification | Valeur hex |
|---------|--------------|------------|
| STX | Start of TeXt (debut de trame) | 0x02 |
| ETX | End of TeXt (fin de trame) | 0x03 |
| EOT | End Of Transmission (fin de transmission) | 0x04 |
| CR | Carriage Return (fin de groupe) | 0x0D |
| LF | Line Feed (debut de groupe) | 0x0A |
| HT | Horizontal Tab (separateur post-2013) | 0x09 |

### Caracteres de signes (imprimables)

| Symbole | Signification | Valeur hex |
|---------|--------------|------------|
| espace | SPace (separateur pre-2013) | 0x20 |
| `-` | tiret | 0x2D |
| `+` | plus | 0x2B |
| `_` | souligne | 0x5F |
| `/` | slash | 0x2F |
| `.` | point | 0x2E |
| `,` | virgule | 0x2C |
| `%` | pourcent | 0x25 |
| `?` | point d'interrogation | 0x3F |
| `:` | deux points | 0x3A |
