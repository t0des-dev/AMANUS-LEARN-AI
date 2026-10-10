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
            if (
                "qcm" in lower_p
                or "quiz" in lower_p
                or '"questions":' in prompt
                or "اختبار" in prompt
                or "أسئلة" in prompt
            ):
                if any(
                    ar_term in prompt
                    for ar_term in [
                        "اللغة العربية",
                        "العربية",
                        "اختبار",
                        "أسئلة",
                        "سؤال",
                        "اختر الإجابة",
                    ]
                ):
                    data = {
                        "questions": [
                            {
                                "question": "ما هو الدور الرئيسي لآلية الانتباه الذاتي (Self-Attention) في نماذج المحولات؟",
                                "answers": [
                                    {
                                        "text": "تحديد أوزان ديناميكية تعكس أهمية الروابط السياقية بين الكلمات",
                                        "is_correct": True,
                                    },
                                    {
                                        "text": "تقليل الدقة الحسابية للطبقات العميقة دون تدريب",
                                        "is_correct": False,
                                    },
                                    {
                                        "text": "حذف الرموز النادرة عشوائياً لتقليل حجم المعجم",
                                        "is_correct": False,
                                    },
                                    {
                                        "text": "استبدال وظيفة طبقة الترميز بالكامل بطريقة ثابتة",
                                        "is_correct": False,
                                    },
                                ],
                                "explanation": "تتيح آلية الانتباه الذاتي للنموذج حساب درجات الترابط بين جميع الرموز في النص للتركيز على المعنى السياقي الأدق [1].",
                                "difficulty": "MEDIUM",
                                "source": "الفصل 1 : آليات الانتباه والنماذج اللغوية",
                            },
                            {
                                "question": "أي من الخوارزميات التالية تُستخدم عادة لتحسين معاملات الشبكة العصبية وتقليل دالة الخسارة؟",
                                "answers": [
                                    {
                                        "text": "خوارزمية Adam أو انحدار التدرج العشوائي (SGD)",
                                        "is_correct": True,
                                    },
                                    {
                                        "text": "خوارزمية ديكسترا لأقصر مسار",
                                        "is_correct": False,
                                    },
                                    {
                                        "text": "خوارزمية التجميع بالمتوسطات K-Means",
                                        "is_correct": False,
                                    },
                                    {
                                        "text": "الانحدار الخطي البسيط بالمربعات الصغرى",
                                        "is_correct": False,
                                    },
                                ],
                                "explanation": "تعمل خوارزميات التحسين مثل Adam على تحديث الأوزان في كل دورة تدريبية وفقاً للتدرجات المحسوبة [2].",
                                "difficulty": "EASY",
                                "source": "الفصل 2 : خوارزميات التحسين والتدريب",
                            },
                        ]
                    }
                elif "english" in lower_p or "in english" in lower_p or "language: en" in lower_p:
                    data = {
                        "questions": [
                            {
                                "question": "What is the primary role of the self-attention mechanism in Transformer models?",
                                "answers": [
                                    {
                                        "text": "Dynamically weight the contextual importance between all tokens",
                                        "is_correct": True,
                                    },
                                    {
                                        "text": "Uniformly downsample spatial feature maps",
                                        "is_correct": False,
                                    },
                                    {
                                        "text": "Compute an unweighted arithmetic mean across tokens",
                                        "is_correct": False,
                                    },
                                    {
                                        "text": "Bypass the tokenizer to directly feed raw characters",
                                        "is_correct": False,
                                    },
                                ],
                                "explanation": "Self-attention computes dynamic affinity scores between all tokens in a sequence to focus representations on relevant context [1].",
                                "difficulty": "MEDIUM",
                                "source": "Chapter 1: Self-Attention Architecture",
                            },
                            {
                                "question": "Which optimization algorithm is widely used to minimize training loss in neural networks?",
                                "answers": [
                                    {
                                        "text": "Adam or Stochastic Gradient Descent (SGD)",
                                        "is_correct": True,
                                    },
                                    {
                                        "text": "Dijkstra shortest path algorithm",
                                        "is_correct": False,
                                    },
                                    {
                                        "text": "Unsupervised K-Means clustering",
                                        "is_correct": False,
                                    },
                                    {
                                        "text": "Ordinary Least Squares linear regression",
                                        "is_correct": False,
                                    },
                                ],
                                "explanation": "Optimizers like Adam iteratively adjust weights via backpropagation based on computed gradients [2].",
                                "difficulty": "EASY",
                                "source": "Chapter 2: Optimization and Training",
                            },
                        ]
                    }
                else:
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
            elif (
                "definitions" in prompt
                or "fiche de révision" in lower_p
                or "بطاقة مراجعة" in prompt
            ):
                data = {
                    "title": "Fiche de Révision Synthétique",
                    "definitions": [
                        {
                            "term": "Attention",
                            "definition": "Pondération dynamique des représentations [1].",
                        }
                    ],
                    "key_formulas_or_rules": ["Softmax(QK^T / sqrt(d_k))V"],
                    "frequent_mistakes": ["Oublier le facteur d'échelle sqrt(d_k)"],
                    "quick_qa": [
                        {
                            "question": "Quel est le rôle du scaling factor ?",
                            "answer": "Éviter la saturation du softmax.",
                        }
                    ],
                }
            elif (
                "key_points" in prompt
                or "concepts clés" in lower_p
                or "المفاهيم والنقاط الجوهرية" in prompt
            ):
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
            elif (
                (
                    '"objectives":' in prompt
                    or "objectifs pédagogiques" in lower_p
                    or "الأهداف التعليمية" in prompt
                )
                and "chapters" not in prompt
                and "learning_objectives" not in prompt
            ):
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
            elif (
                '"chapters":' in prompt
                or "un cours d'apprentissage" in lower_p
                or "educational course" in lower_p
                or "مقرر تعليمي" in prompt
                or ("cours" in lower_p and "résumé" not in lower_p and "overview" not in prompt)
            ):
                if any(
                    ar_term in prompt for ar_term in ["المستند", "مقرر", "دورة", "الفصل", "العربية"]
                ):
                    data = {
                        "title": "مقرر الذكاء الاصطناعي والتعلم الآلي",
                        "description": "مقدمة شاملة وأهداف عامة للدورة مستندة إلى المصادر.",
                        "level": "BEGINNER",
                        "learning_objectives": ["فهم الأسس النظرية", "تطبيق الخوارزميات عملياً"],
                        "chapters": [
                            {
                                "title": "الفصل 1 : المفاهيم والأسس",
                                "summary": "ملخص شامل للمفاهيم الأساسية المستخرجة.",
                                "estimated_minutes": 30,
                                "sections": [
                                    {
                                        "title": "الدرس 1.1 : نظرة عامة على المفاهيم",
                                        "content": "شرح مفصل وواضح مع أمثلة وتوثيق من المصدر [1].",
                                        "summary": "خلاصة الدرس الأول",
                                        "objectives": ["استيعاب المفاهيم الأولية بدقة"],
                                        "estimated_minutes": 15,
                                    }
                                ],
                            },
                            {
                                "title": "الفصل 2 : التطبيقات العملية",
                                "summary": "تطبيق الخوارزميات ودراسة الحالات الميدانية.",
                                "estimated_minutes": 35,
                                "sections": [
                                    {
                                        "title": "الدرس 2.1 : دراسة الحالة الأولى",
                                        "content": "تحليل عملي للبيانات والنماذج [2].",
                                        "summary": "خلاصة التطبيق العملي",
                                        "objectives": ["تنفيذ الخوارزميات بنجاح"],
                                        "estimated_minutes": 20,
                                    }
                                ],
                            },
                        ],
                        "sections": [
                            {
                                "title": "الفصل 1 : المفاهيم والأسس",
                                "content": "شرح مفصل وواضح مع أمثلة وتوثيق من المصدر [1].",
                                "summary": "ملخص شامل للمفاهيم الأساسية المستخرجة.",
                                "objectives": ["استيعاب المفاهيم الأولية بدقة"],
                                "estimated_minutes": 30,
                            },
                            {
                                "title": "الفصل 2 : التطبيقات العملية",
                                "content": "تحليل عملي للبيانات والنماذج [2].",
                                "summary": "تطبيق الخوارزميات ودراسة الحالات الميدانية.",
                                "objectives": ["تنفيذ الخوارزميات بنجاح"],
                                "estimated_minutes": 35,
                            },
                        ],
                        "conclusion": "خاتمة وتقييم شامل للمكتسبات المعرفية.",
                    }
                elif "course" in lower_p and "document:" in lower_p:
                    data = {
                        "title": "Comprehensive Course Module",
                        "description": "Pedagogical course grounded strictly in source documents.",
                        "level": "BEGINNER",
                        "learning_objectives": [
                            "Understand core foundations",
                            "Apply methodologies in practice",
                        ],
                        "chapters": [
                            {
                                "title": "Chapter 1: Theoretical Foundations",
                                "summary": "In-depth overview of core principles.",
                                "estimated_minutes": 30,
                                "sections": [
                                    {
                                        "title": "Lesson 1.1: Core Concepts",
                                        "content": "Detailed explanation of key concepts with citations [1].",
                                        "summary": "Summary of lesson 1.1",
                                        "objectives": ["Understand foundational concepts"],
                                        "estimated_minutes": 15,
                                    }
                                ],
                            },
                            {
                                "title": "Chapter 2: Practical Implementation",
                                "summary": "Hands-on application and case studies.",
                                "estimated_minutes": 35,
                                "sections": [
                                    {
                                        "title": "Lesson 2.1: Case Study Analysis",
                                        "content": "Practical walkthrough with concrete examples [2].",
                                        "summary": "Summary of lesson 2.1",
                                        "objectives": ["Execute case studies successfully"],
                                        "estimated_minutes": 20,
                                    }
                                ],
                            },
                        ],
                        "sections": [
                            {
                                "title": "Chapter 1: Theoretical Foundations",
                                "content": "Detailed explanation of key concepts with citations [1].",
                                "summary": "In-depth overview of core principles.",
                                "objectives": ["Understand foundational concepts"],
                                "estimated_minutes": 30,
                            },
                            {
                                "title": "Chapter 2: Practical Implementation",
                                "content": "Practical walkthrough with concrete examples [2].",
                                "summary": "Hands-on application and case studies.",
                                "objectives": ["Execute case studies successfully"],
                                "estimated_minutes": 35,
                            },
                        ],
                        "conclusion": "Synthesis of learning outcomes and practical takeaways.",
                    }
                else:
                    data = {
                        "title": "Module de Cours Pédagogique",
                        "description": "Introduction pédagogique basée strictement sur les sources documentaires.",
                        "level": "BEGINNER",
                        "learning_objectives": [
                            "Comprendre les fondements théoriques",
                            "Mettre en œuvre les méthodes pratiques",
                        ],
                        "chapters": [
                            {
                                "title": "Chapitre 1 : Fondements théoriques",
                                "summary": "Présentation des concepts fondamentaux.",
                                "estimated_minutes": 30,
                                "sections": [
                                    {
                                        "title": "Leçon 1.1 : Notions de base",
                                        "content": "Explication détaillée des concepts identifiés dans le document [1].",
                                        "summary": "Résumé de la leçon 1.1",
                                        "objectives": ["Assimiler les notions de base"],
                                        "estimated_minutes": 15,
                                    }
                                ],
                            },
                            {
                                "title": "Chapitre 2 : Mise en œuvre pratique",
                                "summary": "Étude des méthodes d'application et des cas d'usage.",
                                "estimated_minutes": 35,
                                "sections": [
                                    {
                                        "title": "Leçon 2.1 : Exercices et cas d'usage",
                                        "content": "Étude des méthodes d'application et des cas d'usage [2].",
                                        "summary": "Résumé de la leçon 2.1",
                                        "objectives": ["Mettre en application les connaissances"],
                                        "estimated_minutes": 20,
                                    }
                                ],
                            },
                        ],
                        "sections": [
                            {
                                "title": "Chapitre 1 : Fondements théoriques",
                                "content": "Explication détaillée des concepts identifiés dans le document [1].",
                                "summary": "Présentation des concepts fondamentaux.",
                                "objectives": ["Assimiler les notions de base"],
                                "estimated_minutes": 30,
                            },
                            {
                                "title": "Chapitre 2 : Mise en œuvre pratique",
                                "content": "Étude des méthodes d'application et des cas d'usage [2].",
                                "summary": "Étude des méthodes d'application et des cas d'usage.",
                                "objectives": ["Mettre en application les connaissances"],
                                "estimated_minutes": 35,
                            },
                        ],
                        "conclusion": "Synthèse des acquis et perspectives d'apprentissage.",
                    }
            elif (
                "overview" in prompt
                or "résumé" in lower_p
                or "resume" in lower_p
                or "summary" in lower_p
                or "ملخص" in prompt
            ):
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
