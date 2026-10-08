import json
from typing import Any

from .base import AIProvider, AIResponse


class MockAIProvider(AIProvider):
    """Deterministic Mock AI Provider for testing and offline development."""

    name: str = "mock"
    default_model: str = "mock-gpt-4o"

    def __init__(self, model_name: str = "mock-gpt-4o"):
        self.default_model = model_name

    def generate(
        self,
        prompt: str,
        system_instruction: str = "",
        model: str | None = None,
        temperature: float = 0.2,
        max_tokens: int = 3000,
        response_format: str = "text",
    ) -> AIResponse:
        active_model = model or self.default_model
        input_tokens = max(1, len(prompt.split()) + len(system_instruction.split()))

        # If JSON is expected
        if response_format == "json":
            # Detect type from prompt
            lower_p = prompt.lower()
            if "résumé" in lower_p or "summary" in lower_p:
                data: dict[str, Any] = {
                    "overview": "Résumé général du document basé sur les sources extraites.",
                    "key_takeaways": [
                        "Compréhension des notions fondamentales du document.",
                        "Structure logique divisée en chapitres et sections.",
                    ],
                    "chapters_summary": [
                        {
                            "title": "Introduction",
                            "summary": "Présentation des concepts clés et du contexte.",
                        }
                    ],
                }
            elif "point" in lower_p or "notion" in lower_p:
                data = {
                    "key_points": [
                        {
                            "point": "Principe d'attention",
                            "explanation": "Mécanisme central permettant de pondérer les tokens.",
                        },
                        {
                            "point": "Rétropropagation",
                            "explanation": "Algorithme d'optimisation par descente de gradient.",
                        },
                        {
                            "point": "Normalisation",
                            "explanation": "Standardisation des distributions internes du réseau.",
                        },
                    ]
                }
            elif "objectif" in lower_p or "objective" in lower_p:
                data = {
                    "objectives": [
                        {
                            "level": "Comprendre",
                            "objective": "Assimiler l'architecture globale et ses composants.",
                        },
                        {
                            "level": "Appliquer",
                            "objective": "Être capable de reproduire la démarche sur des données réelles.",
                        },
                        {
                            "level": "Évaluer",
                            "objective": "Mesurer la pertinence des résultats obtenus.",
                        },
                    ]
                }
            elif "qcm" in lower_p or "quiz" in lower_p:
                data = {
                    "questions": [
                        {
                            "question": "Quel est le rôle principal du mécanisme d'attention dans les Transformers ?",
                            "answers": [
                                {
                                    "text": "Pondérer dynamiquement l'importance relative de chaque token",
                                    "is_correct": True,
                                },
                                {
                                    "text": "Réduire la résolution spatiale des tenseurs d'entrée",
                                    "is_correct": False,
                                },
                                {
                                    "text": "Calculer une moyenne arithmétique simple sans pondération",
                                    "is_correct": False,
                                },
                                {
                                    "text": "Remplacer l'étape de tokenisation des séquences",
                                    "is_correct": False,
                                },
                            ],
                            "explanation": "L'auto-attention permet de calculer des scores d'affinité entre tous les tokens de la séquence pour focaliser le traitement sur les éléments contextuels clés [1].",
                            "difficulty": "MEDIUM",
                            "source": "Chapitre 1 : Auto-attention",
                        },
                        {
                            "question": "Quel algorithme d'optimisation est couramment employé pour minimiser la fonction de perte ?",
                            "answers": [
                                {
                                    "text": "Adam ou SGD (Descente de gradient stochastique)",
                                    "is_correct": True,
                                },
                                {
                                    "text": "L'algorithme de Dijkstra pour les graphes",
                                    "is_correct": False,
                                },
                                {
                                    "text": "Le clustering non supervisé K-Means",
                                    "is_correct": False,
                                },
                                {
                                    "text": "La régression linéaire par moindres carrés ordinaires",
                                    "is_correct": False,
                                },
                            ],
                            "explanation": "Les optimiseurs comme Adam ou SGD ajustent itérativement les poids synaptiques par rétropropagation du gradient [2].",
                            "difficulty": "EASY",
                            "source": "Chapitre 1 : Optimisation",
                        },
                    ]
                }
            elif "cours" in lower_p or "lesson" in lower_p:
                data = {
                    "title": "Module de Cours Pédagogique",
                    "introduction": "Introduction pédagogique basée strictement sur les sources documentaires.",
                    "sections": [
                        {
                            "title": "Section 1 : Fondements théoriques",
                            "content": "Explication détaillée des concepts identifiés dans le document.",
                        },
                        {
                            "title": "Section 2 : Mise en œuvre pratique",
                            "content": "Étude des méthodes d'application et des cas d'usage.",
                        },
                    ],
                    "conclusion": "Synthèse des acquis et perspectives d'apprentissage.",
                }
            else:
                data = {
                    "status": "success",
                    "generated_content": "Contenu structuré généré par le MockProvider.",
                }

            content = json.dumps(data, ensure_ascii=False, indent=2)
            parsed_json = data
        else:
            # Plain text generation with pedagogical adaptations
            lower_all = (prompt + " " + system_instruction).lower()
            if "simplifi" in lower_all or "vulgaris" in lower_all:
                content = (
                    "Explication simplifiée :\n\n"
                    "Imaginez ce concept comme un chef d'orchestre qui guide chaque instrument au bon moment. "
                    "Dans les faits, d'après les documents consultés [1], ce mécanisme permet de traiter l'information "
                    "étape par étape sans complication inutile."
                )
            elif "résum" in lower_all or "resum" in lower_all:
                content = (
                    "Synthèse pédagogique des points essentiels :\n\n"
                    "1. Définition et principe fondamental issus de la source [1].\n"
                    "2. Mécanismes d'action et étapes clés du processus.\n"
                    "3. Applications pratiques et points de vigilance."
                )
            elif "exemple" in lower_all or "illustr" in lower_all:
                content = (
                    "Exemple concret d'application :\n\n"
                    "Prenons un cas pratique illustré dans vos documents [1] : lorsqu'une donnée entre dans le système, "
                    "elle est transformée et validée selon les règles établies. Cet exemple démontre concrètement "
                    "l'utilité du mécanisme étudié."
                )
            elif "interrog" in lower_all or "question" in lower_all or "quiz" in lower_all:
                content = (
                    "Voici 2 questions pour tester votre compréhension :\n\n"
                    "1. Quel est le rôle principal du concept selon les sources [1] ?\n"
                    "2. Quelles sont les conséquences d'une mauvaise application de ce principe ?\n\n"
                    "Prenez le temps d'y répondre, je vous corrigerai ensuite !"
                )
            elif "révis" in lower_all or "revis" in lower_all:
                content = (
                    "Fiche de révision express :\n\n"
                    "• Notion clé : Voir les principes fondamentaux [1].\n"
                    "• Règle d'or : Respecter les étapes méthodologiques.\n"
                    "• Piège à éviter : Confondre les entrées et les sorties du modèle."
                )
            elif "compar" in lower_all:
                content = (
                    "Tableau comparatif :\n\n"
                    "- Points communs : Les deux approches partagent le même socle théorique [1].\n"
                    "- Différences clés : La première privilégie la rapidité, tandis que la seconde optimise la précision.\n"
                    "- Recommandation : Adapter le choix selon les contraintes de votre projet."
                )
            elif "défin" in lower_all or "defin" in lower_all:
                content = (
                    "Définition précise :\n\n"
                    "Selon les documents de votre organisation [1], ce concept se définit comme un ensemble structuré "
                    "de règles et de méthodes visant à optimiser l'apprentissage et le traitement des données."
                )
            else:
                content = (
                    "Explication pédagogique basée sur vos documents :\n\n"
                    "D'après les sources documentaires analysées [1], ce principe repose sur une organisation "
                    "méthodique permettant de structurer les connaissances et de garantir une progression optimale."
                )
            parsed_json = None

        output_tokens = max(1, len(content.split()))

        return AIResponse(
            content=content,
            parsed_json=parsed_json,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            model=active_model,
            provider=self.name,
        )
