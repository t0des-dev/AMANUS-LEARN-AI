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
                adapted_q = self._generate_adapted_questions_from_prompt(prompt, lower_p)
                if adapted_q:
                    data = adapted_q
                elif any(
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
                '"chapters":' in prompt
                or "un cours d'apprentissage" in lower_p
                or "educational course" in lower_p
                or "مقرر تعليمي" in prompt
                or ("cours" in lower_p and "résumé" not in lower_p and "overview" not in prompt)
            ):
                adapted = self._generate_adapted_course_from_prompt(prompt, lower_p)
                if adapted:
                    data = adapted
                elif any(
                    ar_term in prompt for ar_term in ["المستند", "مقرر", "دورة", "الفصل", "العربية"]
                ):
                    data = {
                        "title": "مقرر شامل : الذكاء الاصطناعي ومعالجة البيانات",
                        "description": "برنامج تعليمي متكامل وشامل يغطي كافة جوانب المحتوى المستخرج من المصادر والوثائق.",
                        "level": "BEGINNER",
                        "learning_objectives": [
                            "فهم وتطبيق الأسس النظرية والمفاهيم الجوهرية",
                            "تحليل النماذج والخوارزميات وآليات المعالجة",
                            "تنفيذ مشاريع وتطبيقات عملية متوافقة مع متطلبات الأداء",
                        ],
                        "chapters": [
                            {
                                "title": "الفصل 1 : المقدمة والمفاهيم النظرية التأسيسية",
                                "summary": "مدخل منهجي شامل للمفاهيم الأساسية، المصطلحات والركائز المعرفية الأولية.",
                                "estimated_minutes": 35,
                                "sections": [
                                    {
                                        "title": "الدرس 1.1 : الإطار المفاهيمي والمصطلحات الأساسية",
                                        "content": "## مدخل إلى الإطار المفاهيمي\n\nيُشكل هذا المحور الركيزة الأساسية لفهم منظومة الذكاء الاصطناعي وهندسة البيانات. استناداً إلى الوثائق المرجعية، تتوزع المفاهيم المحورية على مبادئ التعلّم الآلي وهياكل النماذج [1].\n\n### الركائز التأسيسية\n- **التعلم الخاضع للإشراف (Supervised Learning) :** يعتمد على بيانات مدربة وموسومة مسبقاً للوصول إلى دقة تنبؤ عالية [1].\n- **معالجة اللغات الطبيعية (NLP) :** تحويل النصوص غير المهيكلة إلى تمثيلات شعاعية قابلة للتحليل [2].\n\n> **ملاحظة منهجية :** يجب دائماً التحقق من جودة البيانات الخام قبل تغذيتها في خوارزميات التدريب لتفادي الانحياز الحسابي.",
                                        "summary": "استيعاب المصطلحات والركائز النظرية التأسيسية.",
                                        "objectives": ["استيعاب المفاهيم الأولية بدقة", "التمييز بين فئات التعلم الآلي"],
                                        "estimated_minutes": 15,
                                    },
                                    {
                                        "title": "الدرس 1.2 : هياكل المعالجة والبيانات المرجعية",
                                        "content": "## هيكلية تدفق البيانات\n\nتعتمد المعالجة الحديثة على تقسيم التدفق إلى مراحل متسلسلة تبدأ من الاستخراج والتنقية وصولاً إلى التغذية الراجعة [1].\n\n### مراحل دورة حياة البيانات\n1. الاستخراج من المصادر المعتمدة.\n2. التنظيف واستبعاد القيم الشاذة والمتطرفة [2].\n3. التحويل القياسي (Normalization) للسمات والخصائص.\n\n> **تنبيه مهم :** يُعد التوثيق المستمر لمصادر البيانات شرطاً أساسياً لضمان قابلية التكرار والتدقيق الأكاديمي.",
                                        "summary": "إتقان خطوات تنقية وتحضير تدفقات البيانات.",
                                        "objectives": ["تحديد متطلبات تنقية وتطبيع البيانات"],
                                        "estimated_minutes": 20,
                                    },
                                ],
                            },
                            {
                                "title": "الفصل 2 : النماذج والخوارزميات وآليات العمل",
                                "summary": "استعراض معمق لخوارزميات المحولات والانتباه وآليات التقييم.",
                                "estimated_minutes": 40,
                                "sections": [
                                    {
                                        "title": "الدرس 2.1 : آلية الانتباه الذاتي ونماذج المحولات",
                                        "content": "## آلية الانتباه الذاتي (Self-Attention)\n\nتُعد آلية الانتباه الذاتي القوة الدافعة خلف نماذج المحولات (Transformers) الحديثة، حيث تتيح حساب أوزان ديناميكية تمثل درجة الارتباط الدلالي بين الرموز في النص [1].\n\n### المميزات الجوهرية\n- القدرة على المعالجة المتوازية للرموز بدلاً من التسلسل البطيء.\n- التقاط العلاقات السياقية طويلة المدى بدقة غير مسبوقة [2].\n\n> **قاعدة أساسية :** يتم قياس التفاعل عبر ضرب مصفوفات الاستعلام والمفتاح والقيمة وفق المعادلة القياسية الموزونة.",
                                        "summary": "فهم طريقة عمل آلية الانتباه والمحولات الحديثة.",
                                        "objectives": ["فهم حسابات أوزان الانتباه الذاتي", "مقارنة المحولات بالنماذج التكرارية"],
                                        "estimated_minutes": 20,
                                    },
                                    {
                                        "title": "الدرس 2.2 : خوارزميات التحسين وضبط الأوزان",
                                        "content": "## خوارزميات التدريب والتحسين\n\nيتم تدريب النماذج عبر تقليل دالة الخسارة باستخدام خوارزميات انحدار التدرج الحديثة مثل Adam و AdamW [2].\n\n### معايير ضبط معاملات التدريب\n- **معدل التعلم (Learning Rate) :** القيمة المثلى تضمن التقارب السريع دون تشتت.\n- **حجم الدفعة (Batch Size) :** يؤثر مباشرة على استقرار التدرجات واستهلاك الذاكرة [1].",
                                        "summary": "معايير تحسين معاملات النماذج الحسابية.",
                                        "objectives": ["إتقان ضبط معدل التعلم وحجم الدفعات"],
                                        "estimated_minutes": 20,
                                    },
                                ],
                            },
                            {
                                "title": "الفصل 3 : المنهجية والبنية الهندسية للأنظمة",
                                "summary": "تصميم معماريات الأنظمة الذكية، أنظمة الاسترجاع المعزز RAG وقواعد البيانات المتجهة.",
                                "estimated_minutes": 45,
                                "sections": [
                                    {
                                        "title": "الدرس 3.1 : بنية الاسترجاع المعزز بالتوليد (RAG)",
                                        "content": "## معمارية أنظمة RAG\n\nتجمع أنظمة RAG بين دقة استرجاع المستندات الموثوقة وقدرة النماذج التوليدية على صياغة إجابات مترابطة، مما يقضي على ظاهرة الهلوسة [1].\n\n### المكونات الأساسية للنظام\n1. **مستودع الوثائق والتقطيع الدلالي (Semantic Chunking).**\n2. **فهارس المتجهات وقواعد بيانات pgvector [1].**\n3. **محرك إعادة الترتيب (Reranker) والتوليد المقيد بالمصادر [2].**\n\n> **أفضل ممارسة :** تطبيق البحث الهجين (Hybrid Search) الذي يدمج البحث النصي BM25 والبحث المتجهي لتحقيق أقصى درجات الدقة.",
                                        "summary": "تصميم وتنفيذ أنظمة RAG المتكاملة والآمنة.",
                                        "objectives": ["هندسة أنظمة البحث الهجين والاسترجاع"],
                                        "estimated_minutes": 25,
                                    },
                                    {
                                        "title": "الدرس 3.2 : إدارة المتجهات والفهرسة المتقدمة",
                                        "content": "## استراتيجيات الفهرسة والتقطيع\n\nيُحدد حجم المقطع (Chunk Size) ونسبة التداخل (Overlap) جودة السياق المسترجع للنظام [1].\n\n### التوصيات التقنية\n- المقاطع المتوسطة (500 إلى 800 حرف) تحافظ على وحدة المعنى.\n- استخدام نماذج تضمين متخصصة باللغة العربية لتحسين دقة التقارب الشعاعي [2].",
                                        "summary": "إتقان استراتيجيات تقطيع وفهرسة المحتوى.",
                                        "objectives": ["اختيار المعايير المناسبة لتضمين النصوص"],
                                        "estimated_minutes": 20,
                                    },
                                ],
                            },
                            {
                                "title": "الفصل 4 : التطبيقات العملية ودراسات الحالة",
                                "summary": "سيناريوهات تطبيقية واقعية، بناء خطوط الأنابيب ومعالجة المشكلات الميدانية.",
                                "estimated_minutes": 40,
                                "sections": [
                                    {
                                        "title": "الدرس 4.1 : بناء خط أنابيب معالجة المستندات عملياً",
                                        "content": "## خطوات التنفيذ العملي\n\nتطبيق عملي لخط أنابيب الاستيعاب الشامل بدءاً من رفع ملفات PDF وحتى استخلاص النصوص عبر محرك OCR المتخصص [1].\n\n### مراحل التنفيذ خطوة بخطوة\n1. فحص وسلامة الملف والتحقق من التنسيق السليم.\n2. التقطيع الدلالي وحساب تضمينات المتجهات المتزامنة [2].\n3. اختبار كفاءة الاستعلام عبر أمثلة واقعية.",
                                        "summary": "تنفيذ واختبار خط أنابيب متكامل لمعالجة الوثائق.",
                                        "objectives": ["بناء خط أنابيب استيعاب كامل بنجاح"],
                                        "estimated_minutes": 20,
                                    },
                                    {
                                        "title": "الدرس 4.2 : الأمان والعزل المتعدد في بيئات المؤسسات",
                                        "content": "## متطلبات الأمان المؤسسي\n\nيتطلب نشر الأنظمة في بيئات العمل المشتركة تطبيق العزل المنطقي الكامل بين المنظمات ومراقبة الحصص الاستهلاكية بدقة [2].\n\n### آليات الحماية\n- تحديد سقف الاستهلاك (Rate Limiting) عبر بوابات الـ API [1].\n- المعالجة غير المتزامنة للمهام الثقيلة عبر Celery.",
                                        "summary": "تطبيق قواعد الأمان والعزل متعدد المستأجرين.",
                                        "objectives": ["تأمين الأنظمة وتطبيق العزل الصارم بين المنظمات"],
                                        "estimated_minutes": 20,
                                    },
                                ],
                            },
                            {
                                "title": "الفصل 5 : التقييم وضمان الجودة والآفاق المستقبلية",
                                "summary": "قياس دقة الاسترجاع، تفادي الهلوسة والتحسين المستمر للأنظمة.",
                                "estimated_minutes": 35,
                                "sections": [
                                    {
                                        "title": "الدرس 5.1 : معايير التقييم الآلي والدقة المرجعية",
                                        "content": "## معايير التقييم والقياس\n\nتعتمد موثوقية الأنظمة على مؤشرات كمية صارمة تشمل الأمانة للمصادر (Faithfulness) وملاءمة الإجابة (Relevance) [1].\n\n### أهداف الجودة المعتمدة\n- نسبة الهلوسة: 0% للإجابات المرجعية.\n- زمن الاستجابة: أقل من ثانية واحدة للاستعلامات المخبأة [2].",
                                        "summary": "استخدام أدوات التقييم الآلي وقياس الأداء.",
                                        "objectives": ["قياس مؤشرات دقة الإجابات والاسترجاع"],
                                        "estimated_minutes": 15,
                                    },
                                    {
                                        "title": "الدرس 5.2 : الخلاصة الشاملة وخارطة طريق التعلم المستمر",
                                        "content": "## الخلاصة والآفاق التطويرية\n\nيُشكل هذا المقرر دليلاً شاملاً لكافة الأسس والتقنيات الواردة في المستند المرجعي [1].\n\n### أبرز المخرجات\n- الأنظمة المقيدة بالمصادر هي الأكثر موثوقية واستقراراً.\n- التصميم المعياري يضمن سهولة التحديث والتطوير المستمر [2].",
                                        "summary": "تلخيص شامل للمكتسبات المعرفية للدورة.",
                                        "objectives": ["ترسيخ المكتسبات المعرفية وبناء خطة عمل مستقبلية"],
                                        "estimated_minutes": 20,
                                    },
                                ],
                            },
                        ],
                        "conclusion": "خلاصة شاملة لكافة المحاور وتوصيات للتطبيق العملي.",
                    }
                elif "en" in lower_p or "english" in lower_p:
                    data = {
                        "title": "Comprehensive Course: Artificial Intelligence & Knowledge Systems",
                        "description": "Full structured educational curriculum covering theoretical, architectural, and practical aspects grounded strictly in source documents.",
                        "level": "BEGINNER",
                        "learning_objectives": [
                            "Understand foundational theories and core concepts",
                            "Analyze neural architectures and vector retrieval systems",
                            "Implement production-grade pipelines following industry best practices",
                        ],
                        "chapters": [
                            {
                                "title": "Chapter 1: Introduction & Theoretical Foundations",
                                "summary": "Foundational concepts, industry terminology, and theoretical groundwork.",
                                "estimated_minutes": 35,
                                "sections": [
                                    {
                                        "title": "Lesson 1.1: Conceptual Framework & Core Definitions",
                                        "content": "## Conceptual Groundwork\n\nThis introductory module establishes the essential technical foundations based on the source document [1].\n\n### Key Pillars\n- **Supervised Learning:** Training models on verified labeled pairs to establish predictive mappings [1].\n- **Vector Representations (Embeddings):** Geometric mapping of text tokens into continuous multidimensional manifolds preserving semantic affinity [2].\n\n> **Core Axiom:** System answers must be verifiable against source document citations.",
                                        "summary": "Grasping core terminology and theoretical foundations.",
                                        "objectives": ["Understand foundational concepts", "Differentiate learning paradigms"],
                                        "estimated_minutes": 15,
                                    },
                                    {
                                        "title": "Lesson 1.2: Data Ingestion & Lifecycle Management",
                                        "content": "## The Data Processing Pipeline\n\nHigh-performing systems require deterministic ingestion and strict chunking boundaries [1].\n\n### Critical Pipeline Stages\n1. Ingestion and file validation.\n2. Normalization and artifact removal [2].\n3. Semantic chunking with overlap protection.",
                                        "summary": "Mastering the end-to-end data lifecycle.",
                                        "objectives": ["Map out document processing pipelines"],
                                        "estimated_minutes": 20,
                                    },
                                ],
                            },
                            {
                                "title": "Chapter 2: Neural Architectures & Attention Mechanisms",
                                "summary": "Transformer internals, multi-head self-attention, and training dynamics.",
                                "estimated_minutes": 40,
                                "sections": [
                                    {
                                        "title": "Lesson 2.1: Self-Attention & Transformer Mechanics",
                                        "content": "## Inside the Transformer\n\nSelf-attention dynamically computes affinity weights across tokens regardless of their relative distance [1].\n\n### Distinct Advantages\n- **Full parallelization:** Eliminating sequential constraints of recurrence.\n- **Long-context capture:** Retaining long-range dependencies accurately [2].",
                                        "summary": "Understanding self-attention mechanics and Transformers.",
                                        "objectives": ["Explain self-attention calculations", "Compare Transformers against RNNs"],
                                        "estimated_minutes": 20,
                                    },
                                    {
                                        "title": "Lesson 2.2: Optimization Dynamics & Loss Minimization",
                                        "content": "## Loss Landscapes and Optimizers\n\nWeight updates are guided by adaptive gradient descent optimizers including Adam and AdamW [2].\n\n### Critical Hyperparameters\n- **Learning Rate:** Governs the magnitude of parameter updates.\n- **Batch Size:** Dictates gradient variance and memory bandwidth [1].",
                                        "summary": "Calibrating optimization parameters and training runs.",
                                        "objectives": ["Configure model training hyper-parameters"],
                                        "estimated_minutes": 20,
                                    },
                                ],
                            },
                            {
                                "title": "Chapter 3: System Architecture & Vector Search (RAG)",
                                "summary": "RAG architecture, vector databases, hybrid search, and reranking pipelines.",
                                "estimated_minutes": 45,
                                "sections": [
                                    {
                                        "title": "Lesson 3.1: Hybrid Search & RAG Architecture",
                                        "content": "## RAG System Engineering\n\nRetrieval-Augmented Generation connects generative models to grounded external vector stores to eliminate hallucinations [1].\n\n### Architectural Layers\n1. Document parsing and semantic chunking.\n2. Vector indexing with PostgreSQL pgvector [1].\n3. Cross-encoder reranking and source citation enforcement [2].",
                                        "summary": "Designing reliable, zero-hallucination RAG pipelines.",
                                        "objectives": ["Build production-grade retrieval architectures"],
                                        "estimated_minutes": 25,
                                    },
                                    {
                                        "title": "Lesson 3.2: Chunking Strategies & Vector Optimization",
                                        "content": "## Ingestion Parameter Optimization\n\nOptimal chunk size and overlap prevent context fragmentation while retaining fine-grained factual accuracy [1].\n\n### Best Practices\n- Medium chunks (500–800 characters) balance semantic coherence.\n- Dense embeddings preserve cross-lingual relationships [2].",
                                        "summary": "Calibrating chunk boundaries for optimal retrieval precision.",
                                        "objectives": ["Select optimal chunking parameters"],
                                        "estimated_minutes": 20,
                                    },
                                ],
                            },
                            {
                                "title": "Chapter 4: Practical Implementation & Case Studies",
                                "summary": "Real-world deployment scenarios, pipeline testing, and engineering challenges.",
                                "estimated_minutes": 40,
                                "sections": [
                                    {
                                        "title": "Lesson 4.1: Building Ingestion Pipelines Hands-On",
                                        "content": "## Concrete Pipeline Implementation\n\nA full walkthrough from PDF parsing to vector persistence and query validation [1].\n\n### Step-by-Step Procedure\n1. Ingest documents and validate MIME boundaries.\n2. Generate embeddings and populate indices [2].\n3. Run benchmark queries and verify top-k relevancy.",
                                        "summary": "Implementing end-to-end ingestion and vector search.",
                                        "objectives": ["Execute end-to-end ingestion successfully"],
                                        "estimated_minutes": 20,
                                    },
                                    {
                                        "title": "Lesson 4.2: Enterprise Multitenancy & Scaling",
                                        "content": "## Production Hardening\n\nOperating in a multi-tenant environment requires strict logical tenant isolation, atomic quotas, and concurrency locks [2].\n\n### Hardening Patterns\n- Rate limiting at API gateways [1].\n- Background async job distribution via Celery workers.",
                                        "summary": "Addressing scaling bottlenecks in enterprise deployments.",
                                        "objectives": ["Enforce multi-tenant data isolation"],
                                        "estimated_minutes": 20,
                                    },
                                ],
                            },
                            {
                                "title": "Chapter 5: Evaluation, Quality Assurance & Best Practices",
                                "summary": "Evaluation metrics, benchmark datasets, and ongoing governance.",
                                "estimated_minutes": 35,
                                "sections": [
                                    {
                                        "title": "Lesson 5.1: Automated Evaluation & Groundedness Metrics",
                                        "content": "## Measuring System Quality\n\nAccurate evaluation relies on quantifiable metrics: Faithfulness, Answer Relevance, and Context Recall [1].\n\n### Benchmarking Targets\n- Hallucination rate: strictly 0% on factual queries.\n- Latency: sub-second for cached retrieval [2].",
                                        "summary": "Mastering evaluation frameworks and benchmark metrics.",
                                        "objectives": ["Measure retrieval faithfulness accurately"],
                                        "estimated_minutes": 15,
                                    },
                                    {
                                        "title": "Lesson 5.2: Synthesis and Roadmap for Continuous Learning",
                                        "content": "## Course Synthesis\n\nThis comprehensive curriculum synthesizes all foundational, architectural, and practical topics covered throughout the source document [1].\n\n### Key Takeaways\n- Grounded systems outperform unbounded generation in reliability.\n- Modular design guarantees seamless model upgrades [2].",
                                        "summary": "Comprehensive recap of learning achievements.",
                                        "objectives": ["Consolidate learning into actionable engineering plans"],
                                        "estimated_minutes": 20,
                                    },
                                ],
                            },
                        ],
                        "conclusion": "Synthesis of learning outcomes and actionable engineering takeaways.",
                    }
                else:
                    data = {
                        "title": "Cours Complet : Intelligence Artificielle & Ingénierie des Connaissances",
                        "description": "Programme pédagogique complet et structuré couvrant l'intégralité des axes théoriques, méthodologiques et pratiques du document source.",
                        "level": "BEGINNER",
                        "learning_objectives": [
                            "Maîtriser les fondements théoriques et les concepts clés",
                            "Comprendre les architectures de modèles et les systèmes de recherche vectorielle",
                            "Mettre en œuvre des solutions fiables, robustes et conformes aux meilleures pratiques",
                        ],
                        "chapters": [
                            {
                                "title": "Chapitre 1 : Introduction & Fondements Théoriques",
                                "summary": "Cadre général, notions fondamentales et définitions indispensables.",
                                "estimated_minutes": 35,
                                "sections": [
                                    {
                                        "title": "Leçon 1.1 : Cadre Conceptuel et Définitions Clés",
                                        "content": "## Cadre Conceptuel Général\n\nCe premier module établit les bases théoriques indispensables pour appréhender l'ensemble du domaine. En s'appuyant strictement sur les sources documentaires, nous analysons les principes directeurs et la terminologie consacrée [1].\n\n### Notions Essentielles\n- **Apprentissage Supervisé :** Méthode consistant à entraîner des algorithmes sur des données préalablement labellisées pour établir une fonction prédictive [1].\n- **Représentations Vectorielles (Embeddings) :** Projection géométrique de textes dans un espace multidimensionnel préservant les proximités sémantiques [2].\n\n> **Définition clé :** La fidélité documentaire (groundedness) impose que chaque affirmation produite soit traçable vers un extrait textuel source vérifié.",
                                        "summary": "Assimiler le vocabulaire et les notions théoriques de base.",
                                        "objectives": ["Assimiler les notions de base", "Distinguer les types d'apprentissage"],
                                        "estimated_minutes": 15,
                                    },
                                    {
                                        "title": "Leçon 1.2 : Cycle de Vie et Structuration des Données",
                                        "content": "## Le Cycle de Traitement des Données\n\nLa qualité d'un système intelligent dépend directement de la rigueur de sa chaîne de traitement des flux documentaires [1].\n\n### Étapes Clés du Pipeline\n1. **Ingestion et validation formelle :** Contrôle des formats et extraction du texte brut.\n2. **Nettoyage et normalisation :** Élimination des artefacts et filtrage des doublons [2].\n3. **Découpage sémantique (Chunking) :** Préservation de la continuité logique entre paragraphes.\n\n> **Règle méthodologique :** Une traçabilité intégrale des métadonnées (page, chapitre, section) est requise pour toute citation ultérieure.",
                                        "summary": "Comprendre les phases du cycle de vie des données.",
                                        "objectives": ["Identifier les étapes de traitement documentaire"],
                                        "estimated_minutes": 20,
                                    },
                                ],
                            },
                            {
                                "title": "Chapitre 2 : Principes Architecturaux & Modèles",
                                "summary": "Mécanismes d'attention, modèles Transformers et algorithmes d'optimisation.",
                                "estimated_minutes": 40,
                                "sections": [
                                    {
                                        "title": "Leçon 2.1 : Mécanisme d'Auto-Attention et Transformers",
                                        "content": "## L'Architecture Transformer\n\nLe mécanisme d'auto-attention (Self-Attention) permet au modèle de pondérer l'importance relative de chaque token par rapport à tous les autres au sein d'une même séquence [1].\n\n### Avantages Déterminants\n- **Parallélisation massive :** Suppression de la dépendance séquentielle des réseaux récurrents traditionnels.\n- **Contexte étendu :** Capture fidèle des relations sémantiques à longue distance [2].\n\n> **Formule pivot :** Le calcul de l'attention repose sur le produit scalaire mis à l'échelle entre les matrices de Requêtes (Queries), Clés (Keys) et Valeurs (Values).",
                                        "summary": "Maîtriser le fonctionnement de l'auto-attention et des Transformers.",
                                        "objectives": ["Expliquer le mécanisme d'auto-attention", "Comparer Transformers et RNNs"],
                                        "estimated_minutes": 20,
                                    },
                                    {
                                        "title": "Leçon 2.2 : Optimisation et Convergence des Poids",
                                        "content": "## Algorithmes de Descente de Gradient\n\nL'ajustement itératif des poids synaptiques est gouverné par des optimiseurs adaptatifs tels qu'Adam ou AdamW pour minimiser la fonction de perte [2].\n\n### Paramètres Critiques\n- **Taux d'apprentissage (Learning Rate) :** Détermine la magnitude des mises à jour des poids.\n- **Taille de lot (Batch Size) :** Équilibre la régularité du gradient et la consommation de mémoire GPU [1].",
                                        "summary": "Comprendre la dynamique d'entraînement et d'optimisation.",
                                        "objectives": ["Configurer les hyperparamètres d'entraînement"],
                                        "estimated_minutes": 20,
                                    },
                                ],
                            },
                            {
                                "title": "Chapitre 3 : Architecture des Systèmes & Recherche Vectorielle (RAG)",
                                "summary": "Conception des architectures RAG, bases vectorielles et recherche hybride.",
                                "estimated_minutes": 45,
                                "sections": [
                                    {
                                        "title": "Leçon 3.1 : Architecture RAG (Génération Augmentée par Récupération)",
                                        "content": "## Principes Fondamentaux du RAG\n\nLe système RAG associe la précision d'une base de connaissances documentaire indexée à la capacité de rédaction d'un modèle de langage [1].\n\n### Composants Majeurs de la Chaîne\n1. **Indexation vectorielle :** Stockage des représentations dans pgvector [1].\n2. **Recherche hybride (RRF) :** Combinaison optimale de la recherche lexicale (BM25) et de la recherche dense.\n3. **Réordonnancement (Reranking) :** Réévaluation fine des chunks les plus pertinents avant génération [2].\n\n> **Bonne pratique :** L'application de filtres stricts empêche la génération de réponses non étayées par les sources.",
                                        "summary": "Concevoir des architectures RAG robustes et performantes.",
                                        "objectives": ["Concevoir une architecture RAG complète"],
                                        "estimated_minutes": 25,
                                    },
                                    {
                                        "title": "Leçon 3.2 : Stratégies de Découpage et Indexation Vectorielle",
                                        "content": "## Optimisation du Chunking\n\nLe paramétrage de la taille des segments (Chunk Size) et du chevauchement (Overlap) conditionne la pertinence des extraits transmis au modèle [1].\n\n### Recommandations Opérationnelles\n- Segments de 600 à 1000 caractères pour préserver les contextes autonomes.\n- Recours à des modèles d'embeddings adaptés à la langue cible [2].",
                                        "summary": "Paramétrer finement le découpage et l'indexation.",
                                        "objectives": ["Sélectionner la granularité idéale de chunking"],
                                        "estimated_minutes": 20,
                                    },
                                ],
                            },
                            {
                                "title": "Chapitre 4 : Mise en Œuvre Pratique & Déploiement",
                                "summary": "Construction pas à pas de pipelines, gestion des flux et études de cas.",
                                "estimated_minutes": 40,
                                "sections": [
                                    {
                                        "title": "Leçon 4.1 : Déploiement d'un Pipeline de RAG en Production",
                                        "content": "## Implémentation Pratique pas à pas\n\nCette leçon détaille l'enchaînement opérationnel : extraction OCR, vectorisation et configuration des workers Celery [1].\n\n### Déroulement Opérationnel\n1. Réception et validation du document source.\n2. Ingestion asynchrone et découpage par paragraphes.\n3. Stockage et calcul des embeddings pgvector [2].",
                                        "summary": "Déployer un pipeline documentaire de bout en bout.",
                                        "objectives": ["Configurer un pipeline RAG fonctionnel"],
                                        "estimated_minutes": 20,
                                    },
                                    {
                                        "title": "Leçon 4.2 : Sécurité, Isolation Multi-Tenant et Quotas",
                                        "content": "## Robustesse et Isolation des Données\n\nDans un environnement multi-tenant, chaque organisation dispose d'un espace logique hermétique et de quotas de jetons stricts [1].\n\n### Mesures de Sécurité\n- Isolation au niveau base de données par organisation [2].\n- Limitation de débit (Rate Limiting) sur les endpoints de génération.",
                                        "summary": "Garantir la sécurité et l'isolation des données d'entreprise.",
                                        "objectives": ["Appliquer l'isolation des données multi-tenant"],
                                        "estimated_minutes": 20,
                                    },
                                ],
                            },
                            {
                                "title": "Chapitre 5 : Évaluation, Contrôle Qualité & Perspectives",
                                "summary": "Audit qualité, métriques de fidélité documentaire et bilan des acquis.",
                                "estimated_minutes": 35,
                                "sections": [
                                    {
                                        "title": "Leçon 5.1 : Métriques d'Évaluation de la Fidélité Documentaire",
                                        "content": "## Contrôle Qualité et Mesure de la Fidélité\n\nL'évaluation continue garantit que les réponses générées sont strictement conformes aux sources [1].\n\n### Métriques Majeures\n- **Fidélité (Faithfulness) :** Taux d'affirmations sourcées dans le contexte.\n- **Pertinence de la réponse (Answer Relevance) :** Adéquation directe avec la requête utilisateur [2].",
                                        "summary": "Mesurer et auditer la qualité des réponses générées.",
                                        "objectives": ["Auditer la fidélité documentaire d'un système IA"],
                                        "estimated_minutes": 15,
                                    },
                                    {
                                        "title": "Leçon 5.2 : Synthèse Globale et Validation des Acquis",
                                        "content": "## Bilan et Synthèse Pédagogique\n\nCette leçon clôture le parcours en consolidant les compétences acquises à travers l'ensemble des modules [1].\n\n### Points d'Ancrage\n- Maîtrise des principes théoriques et des architectures Transformers.\n- Mise en pratique concrète et déploiement de solutions robustes [2].",
                                        "summary": "Consolider les acquis et valider les compétences.",
                                        "objectives": ["Valider l'ensemble des compétences du cours"],
                                        "estimated_minutes": 20,
                                    },
                                ],
                            },
                        ],
                        "conclusion": "Bilan pédagogique complet et consolidation des compétences acquises.",
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
            elif (
                "podcast" in lower_p
                or "dialogue" in lower_p
                or "notebooklm" in lower_p
                or "بودكاست" in prompt
            ):
                data = {
                    "title": "Épisode : Au Cœur des Notions Clés",
                    "description": "Une discussion dynamique et approfondie décryptant les concepts majeurs du document source.",
                    "hosts": [
                        {"name": "Camille", "role": "host", "voice_id": "shimmer"},
                        {"name": "Alex", "role": "expert", "voice_id": "onyx"},
                    ],
                    "turns": [
                        {
                            "speaker": "Camille",
                            "role": "host",
                            "text": "Bonjour à tous et bienvenue dans ce nouvel épisode ! Alex, aujourd'hui on explore un sujet passionnant qui suscite beaucoup de questions.",
                        },
                        {
                            "speaker": "Alex",
                            "role": "expert",
                            "text": "Salut Camille ! Absolument. Dès la lecture des premières sources [1], ce qui frappe, c'est la rigueur avec laquelle le problème est abordé.",
                        },
                        {
                            "speaker": "Camille",
                            "role": "host",
                            "text": "Pour quelqu'un qui découvre le domaine, quelle est l'intuition centrale à retenir en priorité ?",
                        },
                        {
                            "speaker": "Alex",
                            "role": "expert",
                            "text": "C'est avant tout l'articulation entre les principes théoriques et la mise en œuvre pratique [2]. Les sources insistent sur le fait qu'il ne faut pas sauter les étapes fondamentales.",
                        },
                        {
                            "speaker": "Camille",
                            "role": "host",
                            "text": "Exactement comme une recette où chaque ingrédient joue un rôle critique. Et quels sont les pièges à éviter absolument ?",
                        },
                        {
                            "speaker": "Alex",
                            "role": "expert",
                            "text": "Le piège classique, souligné dans le document [1], est de négliger l'alignement méthodologique. Sans vérification empirique, les risques de dérive augmentent.",
                        },
                        {
                            "speaker": "Camille",
                            "role": "host",
                            "text": "C'est limpide ! Merci infiniment Alex pour ces explications éclairantes. Et à très bientôt pour un prochain épisode !",
                        },
                    ],
                    "key_takeaways": [
                        "Maîtrise des concepts fondamentaux appuyée sur les sources [1].",
                        "Application rigoureuse de la méthodologie éprouvée [2].",
                        "Vigilance continue contre les pièges d'implémentation.",
                    ],
                    "estimated_duration_minutes": 4,
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

    def _generate_adapted_course_from_prompt(
        self, prompt: str, lower_p: str
    ) -> dict[str, Any] | None:
        import re

        is_arabic = (
            any("\u0600" <= c <= "\u06FF" for c in prompt[:1000])
            or "العربية" in prompt
            or "المستند" in prompt
            or "الفصل" in prompt
        )
        is_english = ("en" in lower_p or "english" in lower_p) and not is_arabic

        # 1. Extract document title
        doc_title = ""
        for pat in [
            r'(?:المستند|DOCUMENT|Document)\s*:\s*«([^»]+)»',
            r'(?:المستند|DOCUMENT|Document)\s*:\s*"([^"]+)"',
            r'(?:المستند|DOCUMENT|Document)\s*:\s*[«"\'“](.*?)[»"\'”]',
        ]:
            m = re.search(pat, prompt)
            if m:
                doc_title = m.group(1).strip()
                break
        if not doc_title:
            title_match2 = re.search(r'(?:المستند|DOCUMENT|Document)\s*:\s*([^\n\r]+)', prompt)
            if title_match2:
                candidate = title_match2.group(1).strip().strip('«»"\'“').strip()
                if not any(token in candidate for token in ["NIVEAU", "CRITICAL", "MANDATORY"]):
                    doc_title = candidate

        # 2. Extract context / chunks from prompt
        context_text = ""
        for marker in [
            "المصادر والفقرات المتاحة :",
            "المصادر والفقرات المتاحة:",
            "SOURCES / EXTRAITS DU DOCUMENT :",
            "SOURCES / RETRIEVED CHUNKS:",
            "CONTEXT :",
            "CONTEXT:",
        ]:
            if marker in prompt:
                parts = prompt.split(marker, 1)
                if len(parts) > 1:
                    sub = parts[1]
                    for end_marker in [
                        "توجيه المستوى",
                        "NIVEAU CIBLE",
                        "FOCUS PARTICULIER",
                        "هيكل JSON",
                        "CRITICAL INSTRUCTIONS",
                        "MANDATORY JSON STRUCTURE",
                        "Structure JSON attendue",
                        "JSON structure",
                    ]:
                        if end_marker in sub:
                            sub = sub.split(end_marker, 1)[0]
                    context_text = sub.strip()
                    break

        # 3. Extract chunk blocks
        extracted_chunks = []
        if context_text:
            raw_chunks = re.split(r'(?:^|\n)---\s*Source\s*\[\d+\][^\n]*---\n?|\[\d+\]', context_text)
            for ch in raw_chunks:
                # Remove header lines like '--- Source [1] : ... ---'
                cleaned = re.sub(r'^[^\n]*---\n?', '', ch).strip()
                cleaned = re.sub(
                    r'^(?:Extrait|Source|Page|Document)[^\n:]*:', '', cleaned, flags=re.IGNORECASE
                ).strip()
                cleaned = re.sub(r'^[:\-—\s]+', '', cleaned).strip()
                if (
                    len(cleaned) > 25
                    and not cleaned.startswith("{")
                    and '"title":' not in cleaned
                    and "{" not in cleaned[:10]
                ):
                    extracted_chunks.append(cleaned)

        # If neither real title nor chunks were found (e.g. unit test using dummy query), return None for fallback
        if not doc_title and not extracted_chunks:
            return None

        # If chunks are empty but doc_title exists, create thematic chunks adapted to doc_title
        if not extracted_chunks and doc_title:
            extracted_chunks = [
                f"{doc_title} - الإطار العام والمفاهيم التأسيسية",
                f"{doc_title} - القواعد والأحكام الجوهرية المنظمة",
                f"{doc_title} - الإجراءات والآليات الميدانية والضمانات",
                f"{doc_title} - المعايير التطبيقية والأحكام الختامية",
            ] if is_arabic else [
                f"{doc_title} - Foundational Framework & Key Concepts",
                f"{doc_title} - Core Principles & Structural Guidelines",
                f"{doc_title} - Implementation Procedures & Safeguards",
                f"{doc_title} - Synthesis & Operational Standards",
            ] if is_english else [
                f"{doc_title} - Cadre Général & Notions Fondamentales",
                f"{doc_title} - Principes Directeurs & Règles Essentielles",
                f"{doc_title} - Modalités Pratiques & Garanties d'Application",
                f"{doc_title} - Synthèse Globale & Dispositions Clés",
            ]

        # Helper to extract a concise topic from chunk
        def _get_chunk_topic(text: str, default: str) -> str:
            lines = [l.strip() for l in text.split("\n") if l.strip()]
            for line in lines[:4]:
                clean_line = re.sub(r'^[#*_\-\s\d.:|]+', '', line).strip()
                clean_line = re.sub(r'--+.*--+', '', clean_line).strip()
                clean_line = re.sub(
                    r'^(?:Source|Extrait|Chapitre|Section)[^:]*:', '', clean_line, flags=re.IGNORECASE
                ).strip()
                words = clean_line.split()
                if 2 <= len(words) <= 12 and not clean_line.startswith("http"):
                    return clean_line
            return default

        # If chunks exist, partition into 3 to 6 chapters with lessons each
        if extracted_chunks:
            # If document has few chunks, ensure at least 3 distinct modules
            if len(extracted_chunks) < 3:
                base_c = extracted_chunks[0]
                while len(extracted_chunks) < 3:
                    extracted_chunks.append(base_c)

            total_chunks = len(extracted_chunks)
            num_chapters = min(6, max(3, (total_chunks + 1) // 2))
            chunks_per_chap = max(1, (total_chunks + num_chapters - 1) // num_chapters)

            chapters = []
            for ch_i in range(num_chapters):
                start_idx = ch_i * chunks_per_chap
                end_idx = min(total_chunks, start_idx + chunks_per_chap)
                ch_chunks = extracted_chunks[start_idx:end_idx]
                if not ch_chunks:
                    ch_chunks = [extracted_chunks[ch_i % len(extracted_chunks)]]

                lead_text = ch_chunks[0]
                if is_arabic:
                    thematic_suffixes = [
                        "الأسس النظرية والتأسيسية",
                        "المبادئ الجوهرية والتحليل المعمق",
                        "التطبيقات الميدانية ودراسات الحالة",
                        "المنهجيات وقواعد الاستيعاب",
                        "الخلاصة والتقييم الشامل",
                    ]
                    suffix = thematic_suffixes[ch_i % len(thematic_suffixes)]
                    ch_topic = _get_chunk_topic(lead_text, suffix)
                    ch_title = f"الفصل {ch_i + 1} : {ch_topic}"
                    ch_summary = f"دراسة تفصيلية وشاملة للمفاهيم المرتبطة بـ {ch_topic}."
                elif is_english:
                    thematic_suffixes = [
                        "Theoretical Foundations & Concepts",
                        "Core Principles & In-depth Analysis",
                        "Practical Applications & Case Studies",
                        "Methodology & Best Practices",
                        "Synthesis & Comprehensive Evaluation",
                    ]
                    suffix = thematic_suffixes[ch_i % len(thematic_suffixes)]
                    ch_topic = _get_chunk_topic(lead_text, suffix)
                    ch_title = f"Chapter {ch_i + 1}: {ch_topic}"
                    ch_summary = f"In-depth analysis of foundational concepts around {ch_topic}."
                else:
                    thematic_suffixes = [
                        "Fondements Théoriques & Notions Clés",
                        "Principes Directeurs & Analyse Approfondie",
                        "Applications Pratiques & Cas Réels",
                        "Méthodologie & Bonnes Pratiques",
                        "Synthèse Globale & Évaluation",
                    ]
                    suffix = thematic_suffixes[ch_i % len(thematic_suffixes)]
                    ch_topic = _get_chunk_topic(lead_text, suffix)
                    ch_title = f"Chapitre {ch_i + 1} : {ch_topic}"
                    ch_summary = f"Étude approfondie et structurée des concepts de {ch_topic}."

                sections = []
                for s_i, chunk_content in enumerate(ch_chunks):
                    if is_arabic:
                        s_default = f"المفهوم الرئيسي {s_i + 1}"
                        s_topic = _get_chunk_topic(chunk_content, s_default)
                        s_title = f"الدرس {ch_i + 1}.{s_i + 1} : {s_topic}"
                        content_md = (
                            f"## {s_topic}\n\n"
                            f"{chunk_content}\n\n"
                            f"### النقاط الرئيسية المستخلصة\n"
                            f"- تحليل وتأطير المفاهيم وفق الوثيقة المرجعية [1].\n"
                            f"- معايير التطبيق والمنهجية الميدانية [2].\n\n"
                            f"> **ملاحظة منهجية :** يجب التركيز على القواعد المعرفية المحددة في هذا الدرس لضمان الاستيعاب الدقيق."
                        )
                        s_obj = [f"استيعاب مبادئ {s_topic}"]
                        s_sum = (
                            chunk_content[:150] + "..."
                            if len(chunk_content) > 150
                            else chunk_content
                        )
                    elif is_english:
                        s_default = f"Core Concept {s_i + 1}"
                        s_topic = _get_chunk_topic(chunk_content, s_default)
                        s_title = f"Lesson {ch_i + 1}.{s_i + 1}: {s_topic}"
                        content_md = (
                            f"## {s_topic}\n\n"
                            f"{chunk_content}\n\n"
                            f"### Key Learning Takeaways\n"
                            f"- Core insights grounded directly in document source material [1].\n"
                            f"- Practical evaluation and application methodologies [2].\n\n"
                            f"> **Key Note:** Thorough understanding of this concept is essential for overall mastery."
                        )
                        s_obj = [f"Master the foundations of {s_topic}"]
                        s_sum = (
                            chunk_content[:150] + "..."
                            if len(chunk_content) > 150
                            else chunk_content
                        )
                    else:
                        s_default = f"Concept Clé {s_i + 1}"
                        s_topic = _get_chunk_topic(chunk_content, s_default)
                        s_title = f"Leçon {ch_i + 1}.{s_i + 1} : {s_topic}"
                        content_md = (
                            f"## {s_topic}\n\n"
                            f"{chunk_content}\n\n"
                            f"### Points Clés Pédagogiques\n"
                            f"- Analyse détaillée des notions extraites du document source [1].\n"
                            f"- Mise en perspective méthodologique et applications [2].\n\n"
                            f"> **Règle fondamentale :** Assimiler précisément les définitions et éléments structurels de ce module."
                        )
                        s_obj = [f"Comprendre et maîtriser les notions de {s_topic}"]
                        s_sum = (
                            chunk_content[:150] + "..."
                            if len(chunk_content) > 150
                            else chunk_content
                        )

                    sections.append(
                        {
                            "title": s_title,
                            "content": content_md,
                            "summary": s_sum,
                            "objectives": s_obj,
                            "estimated_minutes": 15 + (s_i * 5),
                        }
                    )

                chapters.append(
                    {
                        "title": ch_title,
                        "summary": ch_summary,
                        "estimated_minutes": 30 + (len(sections) * 10),
                        "sections": sections,
                    }
                )

            effective_title = (
                doc_title
                or (
                    "مقرر تعليمي شامل"
                    if is_arabic
                    else "Comprehensive Course" if is_english else "Cours Pédagogique Complet"
                )
            )
            if is_arabic:
                return {
                    "title": (
                        f"مقرر شامل : {effective_title}"
                        if not effective_title.startswith("مقرر")
                        else effective_title
                    ),
                    "description": f"دورة تعليمية شاملة مستخرجة بدقة من محتوى الوثيقة « {effective_title} »، تغطي كافة المحاور والنقاط الجوهرية.",
                    "level": "BEGINNER",
                    "learning_objectives": [
                        f"استيعاب المفاهيم والمحاور الأساسية لموضوع {effective_title}",
                        "التمكن من المنهجيات والآليات التطبيقية المستخلصة",
                        "تقييم المعارف المكتسبة وتطبيقها بدقة وفق الوثائق المرجعية",
                    ],
                    "chapters": chapters,
                    "conclusion": f"خاتمة شاملة وتقييم نهائي لمكتسبات دورة {effective_title}.",
                }
            elif is_english:
                return {
                    "title": f"Comprehensive Course: {effective_title}",
                    "description": f"Complete curriculum grounded faithfully in source material from '{effective_title}'.",
                    "level": "BEGINNER",
                    "learning_objectives": [
                        f"Understand the core concepts of {effective_title}",
                        "Analyze primary methodologies and practical frameworks",
                        "Demonstrate comprehensive mastery of source content",
                    ],
                    "chapters": chapters,
                    "conclusion": f"Comprehensive conclusion and final review of {effective_title}.",
                }
            else:
                return {
                    "title": (
                        f"Cours Complet : {effective_title}"
                        if not effective_title.startswith("Cours")
                        else effective_title
                    ),
                    "description": f"Programme pédagogique complet élaboré à partir du document « {effective_title} ».",
                    "level": "BEGINNER",
                    "learning_objectives": [
                        f"Maîtriser les concepts fondamentaux de {effective_title}",
                        "Analyser les méthodologies et démarches clés",
                        "Appliquer les connaissances issues du document source avec rigueur",
                    ],
                    "chapters": chapters,
                    "conclusion": f"Bilan global des acquis pédagogiques du cours {effective_title}.",
                }

        return None

    def _generate_adapted_questions_from_prompt(
        self, prompt: str, lower_p: str
    ) -> dict[str, Any] | None:
        """Dynamically generates grounded QCM questions based on actual document chunks and title in prompt."""
        import re

        # Detect language
        is_arabic = (
            any(
                ar_term in prompt
                for ar_term in [
                    "اللغة العربية",
                    "المستند المصدر",
                    "المقاطع المستندية",
                    "اختبار",
                    "أسئلة",
                    "سؤال",
                ]
            )
            or any("\u0600" <= c <= "\u06ff" for c in prompt[:300])
        )
        is_english = (
            "source document" in lower_p
            or "in english" in lower_p
            or ("generate" in lower_p and "questions" in lower_p and not is_arabic and "français" not in lower_p)
        )

        # 1. Extract document title
        doc_title = None
        for pattern in [
            r'المستند\s*المصدر\s*:\s*«([^»]+)»',
            r'المستند\s*:\s*«([^»]+)»',
            r'SOURCE DOCUMENT:\s*«([^»]+)»',
            r'DOCUMENT SOURCE\s*:\s*«([^»]+)»',
            r'DOCUMENT\s*:\s*«([^»]+)»',
            r'المستند\s*المصدر\s*:\s*"([^"]+)"',
            r'SOURCE DOCUMENT:\s*"([^"]+)"',
            r'DOCUMENT SOURCE\s*:\s*"([^"]+)"',
            r'DOCUMENT\s*:\s*"([^"]+)"',
        ]:
            match = re.search(pattern, prompt, re.IGNORECASE)
            if match:
                doc_title = match.group(1).strip()
                break

        # 2. Extract textual chunks from prompt
        raw_chunks = re.split(
            r'\[(?:Extrait|المقطع|Chunk|Source)\s*\d+[^\]]*\]', prompt, flags=re.IGNORECASE
        )
        extracted_chunks: list[str] = []
        for c in raw_chunks:
            cleaned = c.strip()
            if (
                len(cleaned) > 40
                and not cleaned.startswith("JSON")
                and not cleaned.startswith("FORMAT")
                and not cleaned.startswith("MANDATORY")
                and not cleaned.startswith("تنسيق")
                and not cleaned.startswith("RÈGLES")
                and not cleaned.startswith("MISSION")
                and not cleaned.startswith("المهمة")
            ):
                extracted_chunks.append(cleaned)

        if not doc_title and not extracted_chunks:
            return None

        effective_title = doc_title or (
            "الوثيقة المعتمدة"
            if is_arabic
            else ("Source Material" if is_english else "Document Source")
        )

        def _get_chunk_topic(text: str, default: str) -> str:
            lines = [l.strip() for l in text.split("\n") if l.strip()]
            for line in lines[:3]:
                clean_line = re.sub(r'^[#*_\-\s\d.:]+', '', line).strip()
                words = clean_line.split()
                if 2 <= len(words) <= 12 and not clean_line.startswith("http"):
                    return clean_line
            return default

        # Target count from prompt
        count_match = re.search(r'(?:générer|generate|إنشاء)\s+(\d+)\s+questions', prompt, re.IGNORECASE)
        target_count = int(count_match.group(1)) if count_match else 5
        target_count = max(2, min(10, target_count))

        if not extracted_chunks:
            extracted_chunks = [effective_title]

        # Rich multi-angle templates to guarantee zero redundancy
        fr_templates = [
            (
                "Quelle est la notion fondamentale mise en avant dans « {title} » concernant {topic} ?",
                "L'application rigoureuse des principes méthodologiques établis dans la source [{src}]",
                "Une simplification excessive omettant les conditions de validité requises",
                "Un contournement direct des étapes analytiques documentées dans le texte",
                "Une hypothèse purement intuitive sans validation empirique formelle",
                "Le document « {title} » détaille scrupuleusement la validité de ce principe dans l'extrait [{src}].",
            ),
            (
                "Quel objectif d'apprentissage prioritaire ressort de « {title} » au sujet de {topic} ?",
                "La maîtrise opérationnelle des critères énoncés en référence [{src}]",
                "La mémorisation superficielle sans compréhension des mécanismes sous-jacents",
                "La substitution des règles prescrites par des approximations informelles",
                "L'abandon des contrôles de cohérence au profit de la rapidité d'exécution",
                "L'extrait [{src}] de la source « {title} » insiste expressément sur la maîtrise de ces critères.",
            ),
            (
                "Quelle démarche méthodologique est préconisée par « {title} » pour aborder {topic} ?",
                "Une démarche structurée respectant fidèlement le cadre de l'extrait [{src}]",
                "Une approche aléatoire non reproductible dans des conditions normales",
                "L'application d'un protocole obsolète contredit par les résultats actuels",
                "Une généralisation hâtive à partir d'un échantillon non représentatif",
                "La démarche recommandée dans « {title} » repose sur le cadre formalisé dans l'extrait [{src}].",
            ),
            (
                "Quel élément de validation essentiel est requis dans « {title} » pour {topic} ?",
                "La conformité vérifiable avec les données probantes de la source [{src}]",
                "La simple acceptation tacite d'un consensus non documenté",
                "Une tolérance arbitraire d'erreurs systématiques dans le processus",
                "Une validation unilatérale sans contrôle croisé ni vérification",
                "D'après « {title} », seule la conformité vérifiable avec l'extrait [{src}] garantit la rigueur.",
            ),
            (
                "Quelle conclusion opérationnelle se dégage de « {title} » concernant {topic} ?",
                "L'obtention de résultats mesurables et conformes aux exigences du document [{src}]",
                "Une incertitude méthodologique permanente invalidant l'analyse",
                "L'incapacité structurelle à relier les observations empiriques à la théorie",
                "Un écart persistant entre les objectifs déclarés et les réalisations",
                "Les conclusions présentées dans « {title} » démontrent l'atteinte des exigences de l'extrait [{src}].",
            ),
        ]

        ar_templates = [
            (
                "ما هي القاعدة النظرية الجوهرية المعتمدة في الوثيقة « {title} » بخصوص {topic}؟",
                "التطبيق المنهجي المعتمد وفقاً لما ورد في المصدر الموثق [{src}]",
                "افتراض مناقض يتعارض مع المعطيات الصريحة للمستند",
                "إجراء فرعي غير معتمد ضمن الشروط الأساسية للنص",
                "تفسير تقديري يخرج عن السياق الدقيق للوثيقة",
                "تؤكد الوثيقة « {title} » بوضوح في المقطع المرجعي [{src}] على صحة هذا الطرح وأهميته المنهجية.",
            ),
            (
                "ما هو الهدف البيداغوجي الأساسي الذي تركز عليه وثيقة « {title} » في {topic}؟",
                "استيعاب المعايير الإجرائية وتطبيقها بصرامة وفق المرجع [{src}]",
                "الحفظ السطحي للمصطلحات دون إدراك للعلاقات السببية",
                "استبدال القواعد المحددة بتقديرات جزافية غير مدروسة",
                "تجاهل شروط الضبط المنهجي الواردة في الإطار المرجعي",
                "يبرز المقطع [{src}] من « {title} » ضرورة استيعاب المعايير وتطبيقها بدقة بالغة.",
            ),
            (
                "أي منهجية عملية تدعو وثيقة « {title} » لاتباعها في معالجة {topic}؟",
                "نهج منظم يلتزم بالمحددات التحليلية المذكورة في المقطع [{src}]",
                "أسلوب عشوائي يفتقر إلى ضوابط القياس والمتابعة الميدانية",
                "اعتماد نماذج قديمة تم تفنيد نتائجها في التحليلات الحديثة",
                "تعميم غير مبرر يخالف المعايير التوجيهية للنص",
                "توصي الوثيقة « {title} » باعتماد التحليل المنظم المبين في المقطع المرجعي [{src}].",
            ),
            (
                "ما هو المعيار الحاسم لتقييم النتائج في موضوع {topic} حسب « {title} »؟",
                "التوافق التام مع البيانات والأدلة المستخرجة من المصدر [{src}]",
                "القبول الضمني بافتراضات غير موثقة بالبيانات الرسمية",
                "التساهل مع التناقضات المنهجية دون تصحيح أو تدقيق",
                "اعتماد خلاصات أحادية الجانب دون مقارنة موضوعية",
                "تشترط وثيقة « {title} » التحقق الصارم والمطابقة التامة مع بيانات المصدر [{src}].",
            ),
            (
                "ما هي الخلاصة التطبيقية الرئيسية المستفادة من الوثيقة « {title} » حول {topic}؟",
                "تحقيق كفاءة قابلة للتحقق والقياس وفق متطلبات الوثيقة [{src}]",
                "استمرار الغموض الإجرائي مما يعيق الاستفادة العملية",
                "العجز عن الربط بين المبادئ النظرية والممارسة الواقعية",
                "وجود فجوة منهجية دائمة بين الأهداف المعلنة ومخرجات العمل",
                "تُبرهن النتائج المدرجة في « {title} » على بلوغ الكفاءة المحددة بالمقطع [{src}].",
            ),
        ]

        en_templates = [
            (
                "What is the core theoretical principle established in '{title}' regarding {topic}?",
                "The methodological framework validated in referenced source [{src}]",
                "An ungrounded assumption directly contradicted by the source text",
                "A secondary mechanism omitted from the formal requirements",
                "An arbitrary extrapolation lacking documented evidence",
                "The document '{title}' explicitly substantiates this conclusion in reference [{src}].",
            ),
            (
                "What primary instructional goal does '{title}' emphasize in {topic}?",
                "Thorough conceptual mastery guided by criteria in reference [{src}]",
                "Superficial memorization without structural comprehension",
                "Replacing verified guidelines with informal estimations",
                "Omitting consistency audits during procedural execution",
                "Excerpt [{src}] in '{title}' emphasizes structured comprehension over rote recall.",
            ),
            (
                "Which rigorous methodology is recommended by '{title}' for {topic}?",
                "A structured protocol strictly adhering to excerpt [{src}]",
                "A non-reproducible heuristic lacking systematic controls",
                "An obsolete standard refuted by documented conclusions",
                "Over-generalization based on insufficient reference data",
                "The methodology outlined in '{title}' relies strictly upon the framework in excerpt [{src}].",
            ),
            (
                "What essential validation criterion is highlighted in '{title}' concerning {topic}?",
                "Verifiable alignment with empirical evidence cited in [{src}]",
                "Passive acceptance of uncorroborated consensus",
                "Arbitrary tolerance for uncalibrated procedural discrepancies",
                "Unilateral sign-off without independent verification",
                "According to '{title}', empirical alignment with source [{src}] remains the mandatory standard.",
            ),
            (
                "What key practical takeaway emerges from '{title}' regarding {topic}?",
                "Achieving reproducible performance meeting the standards in [{src}]",
                "Residual methodological ambiguity preventing sound implementation",
                "Failure to align theoretical foundations with operational practice",
                "A persistent disconnect between targeted outcomes and real-world results",
                "The operational conclusions in '{title}' affirm the benchmarks set in reference [{src}].",
            ),
        ]

        templates = ar_templates if is_arabic else (en_templates if is_english else fr_templates)

        questions = []
        for idx in range(target_count):
            tpl = templates[idx % len(templates)]
            chunk_text = extracted_chunks[idx % len(extracted_chunks)]
            source_num = (idx % len(extracted_chunks)) + 1
            default_label = f"المحور {idx + 1}" if is_arabic else (f"Section {idx + 1}" if is_english else f"Partie {idx + 1}")
            topic = _get_chunk_topic(chunk_text, default_label)

            q_text = tpl[0].format(title=effective_title, topic=topic)
            ans_correct = tpl[1].format(src=source_num)
            ans_d1 = tpl[2]
            ans_d2 = tpl[3]
            ans_d3 = tpl[4]
            explanation = tpl[5].format(title=effective_title, src=source_num)

            source_label = (
                f"« {effective_title} » - المقطع {source_num}"
                if is_arabic
                else (f"'{effective_title}' - Section {source_num}" if is_english else f"« {effective_title} » - Extrait {source_num}")
            )

            questions.append({
                "question": q_text,
                "answers": [
                    {"text": ans_correct, "is_correct": True},
                    {"text": ans_d1, "is_correct": False},
                    {"text": ans_d2, "is_correct": False},
                    {"text": ans_d3, "is_correct": False},
                ],
                "explanation": explanation,
                "difficulty": "MEDIUM",
                "source": source_label,
            })

        return {"questions": questions}


