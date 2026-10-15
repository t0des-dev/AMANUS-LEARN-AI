# 0001. OpenAPI comme contrat d'API source de vérité

- **Statut** : Accepté
- **Date** : 2026-10-15

## Contexte

L'API Django/DRF évolue rapidement (endpoints, sérialiseurs, permissions).
Sans contrat versionné, le front et les intégrateurs détériorent progressivement
(parms manquantes, champs renommés non signalés), et aucune vérification
automatique ne détecte ces ruptures. Le projet expose déjà drf-spectacular
(`SPECTACULAR_SETTINGS` dans `config/settings/base.py`), mais le schéma n'était
généré ni committé ni vérifié.

## Décision

1. **`apps/api/openapi.yaml` (OpenAPI 3.0.3) est committé dans le dépôt** et
   constitue le contrat public de l'API (`/api/v1/*`).
2. **Le CI vérifie la non-régression du contrat** : la workflow régénère le
   schéma et échoue (`diff -u`) si le fichier committé n'est plus à jour.
3. **Tout changement d'API doit être accompagné d'une régénération** :

   ```bash
   cd apps/api
   python manage.py spectacular --file openapi.yaml
   ```

4. Les warnings/errors de génération (endpoints non documentés) sont tolérés
   aujourd'hui ; les réduire est un objectif d'amélioration continue, pas un
   gate bloquant.

## Conséquences

- **Positif** : toute évolution d'API rend visible son impact (diff de schéma
  lisible en revue de PR) ; base pour tests de contrat, générateurs de clients
  et documentation externe.
- **Négatif** : les contributors doivent régénérer `openapi.yaml` au même moment
  que le code — sinon la CI échoue (c'est voulue : c'est le signal).
- Le schéma committé peut grossir ; il reste lisible en YAML (une ligne par
  chemin/paramètre notable).

## Alternatives écartées

- **Génération uniquement en CI (artefact non committé)** : pas de diff lisible
  en PR, pas de contrat stable pour les consommateurs hors CI.
- **Contrat écrit à la main (spec-first)** : coût de synchronisation élevé avec
  DRF, propice à la dérive pour ce projet.
