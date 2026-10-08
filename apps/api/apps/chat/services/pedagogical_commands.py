import re
from typing import NamedTuple


class CommandDefinition(NamedTuple):
    code: str
    label: str
    description: str
    instruction: str


PEDAGOGICAL_COMMANDS: dict[str, CommandDefinition] = {
    "EXPLAIN": CommandDefinition(
        code="EXPLAIN",
        label="Explique-moi",
        description="Explication détaillée, claire et progressive du concept.",
        instruction=(
            "L'étudiant demande une explication détaillée et pédagogique. Décompose le concept "
            "pas à pas avec rigueur, clarté et bienveillance. Explique le pourquoi et le comment "
            "en t'appuyant strictement sur les sources documentaires."
        ),
    ),
    "SIMPLIFY": CommandDefinition(
        code="SIMPLIFY",
        label="Simplifie",
        description="Vulgarisation accessible pour débutant avec analogies concrètes.",
        instruction=(
            "L'étudiant demande de simplifier. Vulgarise le concept en évitant le jargon inutile, "
            "utilise une analogie concrète du monde réel et garde une formulation simple, directe "
            "et accessible, tout en restant fidèle aux documents sources."
        ),
    ),
    "SUMMARY": CommandDefinition(
        code="SUMMARY",
        label="Résume",
        description="Synthèse concise des points clés et idées maîtresses.",
        instruction=(
            "L'étudiant demande un résumé. Rédige une synthèse concise et structurée (points clés "
            "numérotés ou à puces) mettant en relief les notions capitales issues des sources documentaires."
        ),
    ),
    "EXAMPLE": CommandDefinition(
        code="EXAMPLE",
        label="Donne un exemple",
        description="Illustration concrète par des cas pratiques et réalistes.",
        instruction=(
            "L'étudiant souhaite un ou des exemples. Développe un cas pratique réaliste, étape par étape, "
            "illustrant concrètement le fonctionnement ou l'application du concept décrit dans les documents."
        ),
    ),
    "QUIZ": CommandDefinition(
        code="QUIZ",
        label="Interroge-moi",
        description="Questions interactives pour tester la compréhension.",
        instruction=(
            "L'étudiant demande à être interrogé. Formule 2 à 3 questions stimulantes de difficulté "
            "progressive basées sur les sources pour valider sa compréhension. Ne donne pas immédiatement "
            "les réponses : invite chaleureusement l'étudiant à y répondre."
        ),
    ),
    "REVISION": CommandDefinition(
        code="REVISION",
        label="Fais-moi réviser",
        description="Fiche de révision express, points d'attention et validation.",
        instruction=(
            "L'étudiant souhaite réviser. Conçois une mini fiche de révision structurée : (1) Notions "
            "fondamentales à retenir, (2) Les pièges ou confusions classiques à éviter, et (3) Mini question "
            "de validation rapide."
        ),
    ),
    "COMPARE": CommandDefinition(
        code="COMPARE",
        label="Compare",
        description="Tableau ou structure comparative entre deux concepts.",
        instruction=(
            "L'étudiant demande une comparaison. Dresse un comparatif clair (critères, points communs, "
            "différences fondamentales et cas d'usage respectifs) fondé sur les informations des documents."
        ),
    ),
    "DEFINE": CommandDefinition(
        code="DEFINE",
        label="Définis",
        description="Définition académique, précise et concise du terme.",
        instruction=(
            "L'étudiant demande une définition. Fournis une définition académique, nette, concise et exacte "
            "du concept, puis précise son rôle et son importance selon les documents sources."
        ),
    ),
}

# Regex patterns matching command prefixes
COMMAND_PATTERNS = [
    # Explicit slash commands
    (r"^/(?:explique(?:-moi)?|explain)\b[:\s]*", "EXPLAIN"),
    (r"^/(?:simplifie(?:-moi)?|simplify)\b[:\s]*", "SIMPLIFY"),
    (r"^/(?:r[eé]sume(?:-moi)?|summary)\b[:\s]*", "SUMMARY"),
    (r"^/(?:(?:donne(?:-moi)?-)?exemple|example)\b[:\s]*", "EXAMPLE"),
    (r"^/(?:interroge(?:-moi)?|quiz|teste(?:-moi)?)\b[:\s]*", "QUIZ"),
    (r"^/(?:(?:fais-moi-)?r[eé]vis(?:er|ion))\b[:\s]*", "REVISION"),
    (r"^/(?:compare|comparaison)\b[:\s]*", "COMPARE"),
    (r"^/(?:d[eé]finis(?:-moi)?|definition|define)\b[:\s]*", "DEFINE"),
    # Natural language prefixes
    (r"^(?:peux-tu\s+m['’]expliquer|explique(?:-moi|\s+moi)?)\b[:\s]*", "EXPLAIN"),
    (r"^(?:simplifie(?:-moi|\s+moi)?|vulgarise(?:-moi|\s+moi)?)\b[:\s]*", "SIMPLIFY"),
    (r"^(?:fais(?:\s+un)?\s+r[eé]sum[eé](?:\s+de)?|r[eé]sume(?:-moi|\s+moi)?)\b[:\s]*", "SUMMARY"),
    (
        r"^(?:donne(?:-moi|\s+moi)?\s+un\s+exemple(?:\s+de|\s+d['’])?|illustre(?:\s+avec)?|exemple(?:\s+de|\s+d['’])?)\b[:\s]*",
        "EXAMPLE",
    ),
    (
        r"^(?:interroge(?:-moi|\s+moi)?(?:\s+sur)?|pose(?:-moi|\s+moi)?\s+des\s+questions(?:\s+sur)?|teste(?:-moi|\s+moi)?(?:\s+sur)?)\b[:\s]*",
        "QUIZ",
    ),
    (
        r"^(?:fais(?:-moi|\s+moi)?\s+r[eé]viser(?:\s+sur)?|r[eé]vision(?:\s+de|\s+sur)?|r[eé]vise(?:\s+avec\s+moi)?)\b[:\s]*",
        "REVISION",
    ),
    (
        r"^(?:compare(?:\s+entre)?|fais\s+une\s+comparaison(?:\s+entre)?|comparatif(?:\s+de|\s+entre)?)\b[:\s]*",
        "COMPARE",
    ),
    (
        r"^(?:d[eé]finis(?:-moi|\s+moi)?|donne(?:\s+la)?\s+d[eé]finition(?:\s+de|\s+d['’])?|qu['’]est-ce\s+que(?:\s+le|\s+la|\s+l['’]|\s+les)?)\b[:\s]*",
        "DEFINE",
    ),
]


def detect_pedagogical_command(text: str, explicit_command: str | None = None) -> tuple[str | None, str]:
    """Detects pedagogical command from explicit parameter or message prefix.

    Returns:
        (command_code, cleaned_query)
    """
    cleaned_text = (text or "").strip()

    # 1. Check explicit command parameter
    if explicit_command:
        normalized = explicit_command.strip().upper()
        if normalized in PEDAGOGICAL_COMMANDS:
            # Also clean prefix if present in text
            for pattern, code in COMMAND_PATTERNS:
                if code == normalized:
                    sub_text = re.sub(pattern, "", cleaned_text, flags=re.IGNORECASE).strip()
                    if sub_text:
                        cleaned_text = sub_text
                    break
            return normalized, cleaned_text

    # 2. Match natural language or slash patterns
    for pattern, code in COMMAND_PATTERNS:
        match = re.search(pattern, cleaned_text, flags=re.IGNORECASE)
        if match:
            clean_sub = cleaned_text[match.end() :].strip()
            # If after stripping the trigger, enough text remains for search, return it;
            # otherwise keep full text for context
            final_query = clean_sub if len(clean_sub) >= 3 else cleaned_text
            return code, final_query

    return None, cleaned_text


def get_command_instruction(command_code: str | None) -> str:
    """Returns the pedagogical instruction associated with the command."""
    if not command_code:
        return (
            "Tu es un tuteur pédagogique d'élite. Réponds avec clarté, rigueur et méthode, "
            "en adaptant tes explications au niveau de l'étudiant à partir des sources documentaires."
        )

    cmd = PEDAGOGICAL_COMMANDS.get(command_code.upper())
    if cmd:
        return cmd.instruction

    return (
        "Tu es un tuteur pédagogique d'élite. Réponds avec clarté, rigueur et méthode, "
        "en t'appuyant strictement sur les sources documentaires."
    )
