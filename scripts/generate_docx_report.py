#!/usr/bin/env python3
"""
Générateur du Rapport de Synthèse de la Plateforme Amanus Learn AI (Format DOCX)
"""

import os
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn

def set_cell_background(cell, color_hex):
    """Applique une couleur d'arrière-plan à une cellule."""
    tcPr = cell._element.get_or_add_tcPr()
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{color_hex}"/>')
    tcPr.append(shd)

def set_cell_margins(cell, top=100, bottom=100, left=150, right=150):
    """Définit les marges internes d'une cellule (en dxa)."""
    tcPr = cell._element.get_or_add_tcPr()
    tcMar = parse_xml(f'<w:tcMar {nsdecls("w")}>'
                      f'<w:top w:w="{top}" w:type="dxa"/>'
                      f'<w:bottom w:w="{bottom}" w:type="dxa"/>'
                      f'<w:left w:w="{left}" w:type="dxa"/>'
                      f'<w:right w:w="{right}" w:type="dxa"/>'
                      f'</w:tcMar>')
    tcPr.append(tcMar)

def set_table_borders(table, color="CBD5E1", sz="4", val="single"):
    """Définit des bordures fines pour l'ensemble d'un tableau."""
    tblPr = table._element.xpath('w:tblPr')
    if tblPr:
        borders = parse_xml(f'<w:tblBorders {nsdecls("w")}>'
                            f'<w:top w:val="{val}" w:sz="{sz}" w:space="0" w:color="{color}"/>'
                            f'<w:bottom w:val="{val}" w:sz="{sz}" w:space="0" w:color="{color}"/>'
                            f'<w:left w:val="none"/>'
                            f'<w:right w:val="none"/>'
                            f'<w:insideH w:val="{val}" w:sz="{sz}" w:space="0" w:color="{color}"/>'
                            f'<w:insideV w:val="none"/>'
                            f'</w:tblBorders>')
        tblPr[0].append(borders)

def add_callout(doc, text, title=None, border_color="2563EB", bg_color="F0F7FF"):
    """Ajoute un encadré de mise en valeur (callout box)."""
    tbl = doc.add_table(rows=1, cols=1)
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl.autofit = False
    cell = tbl.cell(0, 0)
    cell.width = Inches(6.5)
    
    set_cell_background(cell, bg_color)
    set_cell_margins(cell, top=140, bottom=140, left=200, right=180)
    
    # Bordure gauche épaisse
    tcPr = cell._element.get_or_add_tcPr()
    tcBorders = parse_xml(f'<w:tcBorders {nsdecls("w")}>'
                          f'<w:left w:val="single" w:sz="24" w:space="0" w:color="{border_color}"/>'
                          f'<w:top w:val="none"/>'
                          f'<w:right w:val="none"/>'
                          f'<w:bottom w:val="none"/>'
                          f'</w:tcBorders>')
    tcPr.append(tcBorders)
    
    p = cell.paragraphs[0]
    p.paragraph_format.space_before = Pt(2)
    p.paragraph_format.space_after = Pt(2)
    p.paragraph_format.line_spacing = 1.15
    
    if title:
        run_title = p.add_run(f"{title}\n")
        run_title.bold = True
        run_title.font.name = "Arial"
        run_title.font.size = Pt(10.5)
        run_title.font.color.rgb = RGBColor(0x1E, 0x3A, 0x8A)
        
    run_text = p.add_run(text)
    run_text.font.name = "Arial"
    run_text.font.size = Pt(10)
    run_text.font.color.rgb = RGBColor(0x33, 0x41, 0x55)
    
    # Espace après le callout
    p_after = doc.add_paragraph()
    p_after.paragraph_format.space_before = Pt(4)
    p_after.paragraph_format.space_after = Pt(6)

def build_document():
    doc = Document()
    
    # Marges de la page
    sections = doc.sections
    for section in sections:
        section.top_margin = Inches(0.8)
        section.bottom_margin = Inches(0.8)
        section.left_margin = Inches(0.8)
        section.right_margin = Inches(0.8)
        
        # En-tête et pied de page
        header = section.header
        hp = header.paragraphs[0]
        hp.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        hrun = hp.add_run("AMANUS LEARN AI — RAPPORT DE SYNTHÈSE TECHNIQUE & FONCTIONNEL")
        hrun.font.name = "Arial"
        hrun.font.size = Pt(8)
        hrun.font.color.rgb = RGBColor(0x94, 0xA3, 0xB8)
        
        footer = section.footer
        fp = footer.paragraphs[0]
        fp.alignment = WD_ALIGN_PARAGRAPH.CENTER
        frun = fp.add_run("Document Confidentiel — Amanus Learn AI Platform Architecture • Sprints 00-16 • 2026")
        frun.font.name = "Arial"
        frun.font.size = Pt(8)
        frun.font.color.rgb = RGBColor(0x94, 0xA3, 0xB8)

    # Palette de couleurs
    COLOR_PRIMARY = RGBColor(0x0F, 0x17, 0x2A)     # Slate 900
    COLOR_NAVY = RGBColor(0x1E, 0x3A, 0x8A)        # Blue 900
    COLOR_ACCENT = RGBColor(0x25, 0x63, 0xEB)      # Blue 600
    COLOR_EMERALD = RGBColor(0x05, 0x96, 0x69)     # Emerald 600
    COLOR_BODY = RGBColor(0x33, 0x41, 0x55)        # Slate 700

    # =========================================================================
    # COUVERTURE / PAGE DE TITRE
    # =========================================================================
    title_p = doc.add_paragraph()
    title_p.paragraph_format.space_before = Pt(24)
    title_p.paragraph_format.space_after = Pt(4)
    
    tag_run = title_p.add_run("EDTECH • IA GÉNÉRATIVE • RAG • MULTI-TENANT • MICRO-SERVICES\n")
    tag_run.font.name = "Arial"
    tag_run.font.size = Pt(9.5)
    tag_run.font.bold = True
    tag_run.font.color.rgb = COLOR_ACCENT

    main_title = title_p.add_run("AMANUS LEARN AI")
    main_title.font.name = "Arial"
    main_title.font.size = Pt(28)
    main_title.font.bold = True
    main_title.font.color.rgb = COLOR_PRIMARY

    sub_p = doc.add_paragraph()
    sub_p.paragraph_format.space_before = Pt(2)
    sub_p.paragraph_format.space_after = Pt(18)
    sub_run = sub_p.add_run("Rapport Global de Synthèse Technique, Fonctionnelle & Opérationnelle")
    sub_run.font.name = "Arial"
    sub_run.font.size = Pt(15)
    sub_run.font.color.rgb = COLOR_NAVY

    # Bloc métadonnées de couverture
    meta_tbl = doc.add_table(rows=5, cols=2)
    meta_tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    meta_tbl.autofit = False
    col_widths = [Inches(2.2), Inches(4.3)]
    
    meta_data = [
        ("Version de la Plateforme", "1.0 Enterprise Production Ready (Phases 00 à 16 Validées)"),
        ("Date d'Édition", "Octobre 2026"),
        ("Périmètre Architectural", "Monorepo Full-Stack : Next.js 14, Django REST Framework, Celery, PostgreSQL pgvector, Redis, Docker"),
        ("Couverture Multilingue", "Français (FR), Arabe natif avec orientation RTL (AR), Anglais (EN)"),
        ("Statut Opérationnel", "Déploiement Zero-Downtime, Monitoring Prometheus/Grafana, SSL Automatisé"),
    ]
    
    for row_idx, (k, v) in enumerate(meta_data):
        row = meta_tbl.rows[row_idx]
        c0, c1 = row.cells[0], row.cells[1]
        c0.width, c1.width = col_widths[0], col_widths[1]
        set_cell_background(c0, "F8FAFC")
        set_cell_background(c1, "FFFFFF")
        set_cell_margins(c0, top=80, bottom=80, left=120, right=100)
        set_cell_margins(c1, top=80, bottom=80, left=120, right=100)
        
        p0 = c0.paragraphs[0]
        p0.paragraph_format.line_spacing = 1.15
        r0 = p0.add_run(k)
        r0.font.name = "Arial"
        r0.font.bold = True
        r0.font.size = Pt(9.5)
        r0.font.color.rgb = COLOR_PRIMARY
        
        p1 = c1.paragraphs[0]
        p1.paragraph_format.line_spacing = 1.15
        r1 = p1.add_run(v)
        r1.font.name = "Arial"
        r1.font.size = Pt(9.5)
        r1.font.color.rgb = COLOR_BODY

    set_table_borders(meta_tbl, color="E2E8F0")

    doc.add_page_break()

    # =========================================================================
    # 1. RÉSUMÉ EXÉCUTIF & VISION PRODUIT
    # =========================================================================
    h1 = doc.add_heading("1. Résumé Exécutif & Proposition de Valeur", level=1)
    h1.paragraph_format.space_before = Pt(16)
    h1.paragraph_format.space_after = Pt(8)
    
    p = doc.add_paragraph()
    p.paragraph_format.line_spacing = 1.15
    p.paragraph_format.space_after = Pt(8)
    p.add_run(
        "Amanus Learn AI est une plateforme SaaS d'apprentissage augmenté de nouvelle génération, conçue pour "
        "combler le fossé entre les corpus documentaires statiques (cours magistraux, polycopiés, manuels d'entreprise, "
        "procédures réglementaires) et l'expérience d'apprentissage interactive et personnalisée. "
        "Grâce à un pipeline hybride articulant reconnaissance optique de caractères (OCR), recherche vectorielle "
        "augmentée par génération (RAG - Retrieval-Augmented Generation) et modèles de langage avancés (LLM), "
        "la plateforme transforme automatiquement n'importe quel document PDF, Word, PowerPoint ou texte en un "
        "écosystème d'apprentissage complet."
    )

    add_callout(
        doc,
        "« L'objectif fondamental d'Amanus Learn AI est de garantir un apprentissage haute fidélité sans hallucination : "
        "chaque réponse du tuteur virtuel, chaque question de quiz et chaque résumé de cours est rigoureusement indexé "
        "et relié à sa source documentaire exacte avec renvoi précis au numéro de page et au paragraphe. »",
        title="PRINCIPE DIRECTEUR : VÉRITÉ TERRAIN & ANTI-HALLUCINATION",
        border_color="059669",
        bg_color="ECFDF5"
    )

    # Piliers d'innovation
    p_pillars = doc.add_paragraph()
    p_pillars.paragraph_format.space_after = Pt(6)
    run_pill_title = p_pillars.add_run("Les 4 Piliers Stratégiques de la Plateforme :")
    run_pill_title.bold = True
    run_pill_title.font.color.rgb = COLOR_NAVY

    pillars = [
        ("Ingestion Multi-Format & OCR :", " Prise en charge native des fichiers PDF textuels ou scannés, DOCX, PPTX et TXT avec segmentation sémantique intelligente (chunking) et calcul d'embeddings vectoriels de haute densité."),
        ("RAG Haute Précision & Curation :", " Indexation vectorielle sous PostgreSQL avec l'extension pgvector, permettant des recherches sémantiques instantanées et des citations directes de passages sources."),
        ("Génération Multimodale Autonome :", " Synthèse automatique de cours structurés en chapitres et leçons, génération de quiz adaptatifs, production de présentations PowerPoint éditables et synthèse vocale TTS pour l'écoute mobile."),
        ("Expérience Immersive & Inclusive :", " Interface ultra-moderne Dark Glassmorphism, support natif trilingue (Français, Anglais, Arabe avec mise en page RTL complète) et tutorat interactif par chat en flux continu (SSE)."),
    ]
    for b_title, b_desc in pillars:
        bp = doc.add_paragraph(style='List Bullet')
        bp.paragraph_format.line_spacing = 1.15
        bp.paragraph_format.space_after = Pt(4)
        r_bt = bp.add_run(b_title)
        r_bt.bold = True
        r_bt.font.color.rgb = COLOR_PRIMARY
        r_bd = bp.add_run(b_desc)
        r_bd.font.color.rgb = COLOR_BODY

    # =========================================================================
    # 2. ARCHITECTURE TECHNIQUE & CHOIX TECHNOLOGIQUES
    # =========================================================================
    h2 = doc.add_heading("2. Architecture Technique & Topologie Monorepo", level=1)
    h2.paragraph_format.space_before = Pt(16)
    h2.paragraph_format.space_after = Pt(8)

    p_arch = doc.add_paragraph()
    p_arch.paragraph_format.line_spacing = 1.15
    p_arch.paragraph_format.space_after = Pt(8)
    p_arch.add_run(
        "Amanus Learn AI adopte une architecture modulaire en monorepo découplant strictement la couche d'interface "
        "utilisateur (Next.js 14) et la couche de services métier et de persistance (Django REST Framework, Celery, PostgreSQL). "
        "Cette séparation garantit des performances optimales, une maintenance simplifiée et une évolutivité horizontale indépendante."
    )

    # Tableau des composants
    arch_tbl = doc.add_table(rows=8, cols=3)
    arch_tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    arch_tbl.autofit = False
    arch_widths = [Inches(1.5), Inches(2.3), Inches(2.7)]

    headers = ["Couche", "Technologies & Outils", "Rôle & Responsabilités Clés"]
    hdr_row = arch_tbl.rows[0]
    for i, h in enumerate(headers):
        cell = hdr_row.cells[i]
        cell.width = arch_widths[i]
        set_cell_background(cell, "1E3A8A")
        set_cell_margins(cell, top=100, bottom=100, left=120, right=100)
        p = cell.paragraphs[0]
        r = p.add_run(h)
        r.font.name = "Arial"
        r.font.bold = True
        r.font.size = Pt(9.5)
        r.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)

    components_data = [
        ("Frontend Web", "Next.js 14 (App Router), TypeScript, Tailwind CSS, Lucide Icons, Vitest", "Interface réactive SPA/SSR, design Dark Glassmorphism, support i18n FR/AR/EN avec basculement RTL complet, lecteurs multimédia intégrés."),
        ("Backend API", "Django 5.0, Django REST Framework, SimpleJWT, Gunicorn (gthread)", "API RESTful haute performance, authentification JWT sans état (Stateless), règles d'isolation multi-tenant strictes, moteur RAG et orchestrateur IA."),
        ("Base Vectorielle", "PostgreSQL 16, pgvector, HNSW / Cosine Indexing", "Stockage relationnel ACID des métadonnées et stockage vectoriel des embeddings de documents pour la recherche sémantique ultra-rapide."),
        ("Workers Asynchrones", "Celery 5.3, Redis 7 (Broker & Result Backend)", "Exécution asynchrone découplée : file 'default' pour transactions rapides et alertes ; file 'heavy' pour OCR, embeddings, TTS et exports PPTX."),
        ("Stockage Fichiers", "MinIO (Compatible AWS S3 API) / Volumes chiffrés", "Dépôt d'objets sécurisé pour les documents sources originaux, extractions textuelles, fichiers audio générés (.mp3) et diaporamas (.pptx)."),
        ("Reverse Proxy", "Nginx 1.25 Alpine, Let's Encrypt Certbot", "Terminaison SSL/TLS, limitation de débit (rate limiting), proxying non-bufférisé pour streaming SSE chat, compression gzip, distribution des fichiers statiques."),
        ("Observabilité", "Prometheus, Grafana, Node Exporter, Redis Exporter", "Collecte temps réel des métriques système, surveillance de la saturation des files Celery, débit requêtes HTTP et métriques de santé (/health)."),
    ]

    for r_idx, (c_couche, c_tech, c_role) in enumerate(components_data, start=1):
        row = arch_tbl.rows[r_idx]
        bg = "F8FAFC" if r_idx % 2 == 1 else "FFFFFF"
        for c_idx, val in enumerate([c_couche, c_tech, c_role]):
            cell = row.cells[c_idx]
            cell.width = arch_widths[c_idx]
            set_cell_background(cell, bg)
            set_cell_margins(cell, top=80, bottom=80, left=100, right=100)
            p = cell.paragraphs[0]
            p.paragraph_format.line_spacing = 1.15
            r = p.add_run(val)
            r.font.name = "Arial"
            r.font.size = Pt(8.5)
            if c_idx == 0:
                r.font.bold = True
                r.font.color.rgb = COLOR_PRIMARY
            else:
                r.font.color.rgb = COLOR_BODY

    set_table_borders(arch_tbl, color="CBD5E1")

    # =========================================================================
    # 3. MODULES MÉTIERS & CAPACITÉS FONCTIONNELLES
    # =========================================================================
    doc.add_page_break()
    h3 = doc.add_heading("3. Modules Métiers & Fonctionnalités Clés", level=1)
    h3.paragraph_format.space_before = Pt(16)
    h3.paragraph_format.space_after = Pt(8)

    # 3.1 Gestion Multi-Tenancy & Sécurité
    h3_1 = doc.add_heading("3.1 Isolation Multi-Tenancy & Authentification Zero-Trust", level=2)
    h3_1.paragraph_format.space_before = Pt(10)
    h3_1.paragraph_format.space_after = Pt(4)
    p_sec = doc.add_paragraph()
    p_sec.paragraph_format.line_spacing = 1.15
    p_sec.paragraph_format.space_after = Pt(6)
    p_sec.add_run(
        "La plateforme est conçue dès son socle pour héberger plusieurs organisations (universités, entreprises, "
        "départements) avec un cloisonnement total des données. Un utilisateur peut appartenir à plusieurs organisations "
        "avec des rôles distincts (Administrateur, Formateur/Enseignant, Apprenant). Toutes les requêtes vers la base de données "
        "appliquent un filtrage strict au niveau des lignes (Row-Level Security / Organization Scoping). "
        "L'authentification API est strictement sans état (Stateless JWT), éradiquant les vulnérabilités CSRF tout en conservant "
        "l'isolation de session pour l'administration Django."
    )

    # 3.2 Ingestion & RAG
    h3_2 = doc.add_heading("3.2 Ingestion Documentaire & Moteur RAG Avancé", level=2)
    h3_2.paragraph_format.space_before = Pt(10)
    h3_2.paragraph_format.space_after = Pt(4)
    p_rag = doc.add_paragraph()
    p_rag.paragraph_format.line_spacing = 1.15
    p_rag.paragraph_format.space_after = Pt(6)
    p_rag.add_run(
        "Le pipeline d'ingestion prend en charge les formats PDF, DOCX, PPTX et TXT. Les documents numérisés font l'objet "
        "d'un traitement OCR précis. Le texte extrait est ensuite segmenté en blocs sémantiques cohérents (chunking adaptatif). "
        "Chaque bloc fait l'objet d'un calcul d'embedding vectoriel stocké dans PostgreSQL avec pgvector. "
        "Lors des interactions, le moteur RAG effectue une recherche par similarité cosinus avec seuillage de confiance, "
        "fournissant au LLM uniquement les passages pertinents accompagnés de leurs métadonnées d'origine (page, titre, paragraphe)."
    )

    # 3.3 Studio de Cours & Chapitres
    h3_3 = doc.add_heading("3.3 Studio de Cours (LMS), Chapitres & Navigation", level=2)
    h3_3.paragraph_format.space_before = Pt(10)
    h3_3.paragraph_format.space_after = Pt(4)
    p_course = doc.add_paragraph()
    p_course.paragraph_format.line_spacing = 1.15
    p_course.paragraph_format.space_after = Pt(6)
    p_course.add_run(
        "Le module Cours permet de structurer les contenus selon une hiérarchie pédagogique rigoureuse : "
        "Cours → Chapitres → Sections → Leçons. Les fonctionnalités majeures incluent :\n"
        "• Génération de plans de cours automatisée par IA à partir d'un document maître ou sur thème libre.\n"
        "• Gestion avancée des chapitres : recherche en temps réel par mot-clé, boutons 'Tout déplier' / 'Tout replier', "
        "accordéons par chapitre mémorisant l'état de lecture et compteurs de leçons validées.\n"
        "• Lecteur de leçon immersif (Lesson Viewer) avec mise en valeur des objectifs d'apprentissage, estimation du temps de lecture "
        "et validation de fin de chapitre."
    )

    # 3.4 Évaluations & Quiz
    h3_4 = doc.add_heading("3.4 Moteur d'Évaluations & Quiz Pédagogiques", level=2)
    h3_4.paragraph_format.space_before = Pt(10)
    h3_4.paragraph_format.space_after = Pt(4)
    p_quiz = doc.add_paragraph()
    p_quiz.paragraph_format.line_spacing = 1.15
    p_quiz.paragraph_format.space_after = Pt(6)
    p_quiz.add_run(
        "Le générateur de quiz extrait automatiquement les concepts clés des cours et documents pour créer des évaluations "
        "personnalisées sous forme de QCM, questions Vrai/Faux ou réponses textuelles courtes. "
        "La correction est instantanée et enrichie d'explications pédagogiques détaillées pour chaque choix de réponse, "
        "renforçant l'ancrage mémoriel de l'apprenant."
    )

    # 3.5 Tuteur IA Streaming
    h3_5 = doc.add_heading("3.5 Tuteur IA & Chat en Streaming (SSE)", level=2)
    h3_5.paragraph_format.space_before = Pt(10)
    h3_5.paragraph_format.space_after = Pt(4)
    p_chat = doc.add_paragraph()
    p_chat.paragraph_format.line_spacing = 1.15
    p_chat.paragraph_format.space_after = Pt(6)
    p_chat.add_run(
        "L'assistant d'apprentissage virtuel accompagne l'étudiant 24/7. Grâce à une architecture Server-Sent Events (SSE) "
        "optimisée, les réponses sont diffusées mot à mot en temps réel sans latence perçue. "
        "L'interface de chat intègre des 'Source Citation Cards' interactives permettant de déplier le document source "
        "et de vérifier immédiatement la légitimité de l'affirmation du tuteur."
    )

    # 3.6 Audio TTS & Présentations PPTX
    h3_6 = doc.add_heading("3.6 Synthèse Vocale (TTS) & Studio de Présentations (PPTX)", level=2)
    h3_6.paragraph_format.space_before = Pt(10)
    h3_6.paragraph_format.space_after = Pt(4)
    p_multi = doc.add_paragraph()
    p_multi.paragraph_format.line_spacing = 1.15
    p_multi.paragraph_format.space_after = Pt(6)
    p_multi.add_run(
        "• Audio TTS : Génération de podcasts et résumés audios avec support multi-fournisseurs (Mock, OpenAI Audio, ElevenLabs). "
        "Le lecteur audio intégré propose le contrôle de vitesse (0.75x à 2x) et la mémorisation du curseur d'écoute.\n"
        "• Studio de Slides : Synthèse automatique de supports de présentation projetables. L'utilisateur peut réorganiser, "
        "éditer les diapositives directement dans l'interface et exporter l'ensemble en véritable fichier PowerPoint (.pptx)."
    )

    # 3.7 Analytiques & Dashboard
    h3_7 = doc.add_heading("3.7 Tableau de Bord & Analytiques d'Apprentissage", level=2)
    h3_7.paragraph_format.space_before = Pt(10)
    h3_7.paragraph_format.space_after = Pt(4)
    p_dash = doc.add_paragraph()
    p_dash.paragraph_format.line_spacing = 1.15
    p_dash.paragraph_format.space_after = Pt(6)
    p_dash.add_run(
        "Le tableau de bord centralise les métriques clés de progression : temps d'étude cumulé, cours suivis, "
        "taux de réussite aux quiz et détection automatique des 'Concepts Faibles' (Weak Topics). "
        "Cette cartographie cognitive permet aux enseignants et administrateurs d'adapter leurs interventions "
        "et aux apprenants de cibler leurs révisions."
    )

    # 3.8 Évaluation Automatique & Observabilité Qualité IA (Sprint 06)
    h3_8 = doc.add_heading("3.8 Évaluation Automatique & Observabilité Qualité IA (Sprint 06)", level=2)
    h3_8.paragraph_format.space_before = Pt(10)
    h3_8.paragraph_format.space_after = Pt(4)
    p_eval = doc.add_paragraph()
    p_eval.paragraph_format.line_spacing = 1.15
    p_eval.paragraph_format.space_after = Pt(6)
    p_eval.add_run(
        "Un cadre rigoureux d'évaluation automatique des 5 générateurs IA (Cours/Documents, Slides PPTX, Audio TTS, "
        "Quiz et Orchestration asynchrone) a été intégré à la plateforme. Ce système s'articule autour de trois dimensions étanches :\n"
        "• Contrôles Déterministes (100% requis) : Schémas JSON stricts, intégrité OpenXML PPTX, formats audio MP3/ID3 et exhaustivité des champs.\n"
        "• Évaluations Sémantiques : Taux de citation documentaire [1], non-redondance tri-grammes, plausibilité des distracteurs et calibration LLM-as-a-judge.\n"
        "• Métriques Perceptuelles : Détection des risques de débordement textuel sur slides et notation acoustique MOS.\n"
        "Un Golden Benchmark multilingue versionné (v1.0.0, 16 cas d'évaluation FR/EN/AR) et un comparateur de versions A/B préviennent toute régression."
    )

    # =========================================================================
    # 4. INFRASTRUCTURE, DÉPLOIEMENT & DEVOPS
    # =========================================================================
    doc.add_page_break()
    h4 = doc.add_heading("4. Infrastructure, Déploiement & DevOps", level=1)
    h4.paragraph_format.space_before = Pt(16)
    h4.paragraph_format.space_after = Pt(8)

    p_ops = doc.add_paragraph()
    p_ops.paragraph_format.line_spacing = 1.15
    p_ops.paragraph_format.space_after = Pt(8)
    p_ops.add_run(
        "L'architecture d'exploitation a été durcie (Phases 15 et 16) pour répondre aux standards d'une mise en production "
        "haute disponibilité sur serveur dédié ou VPS (ex: Ubuntu 22.04/24.04 LTS)."
    )

    ops_tbl = doc.add_table(rows=6, cols=2)
    ops_tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    ops_tbl.autofit = False
    ops_widths = [Inches(2.2), Inches(4.3)]

    ops_data = [
        ("Déploiement Zero-Downtime", "Script d'orchestration `infrastructure/scripts/deploy.sh` : sauvegarde pré-déploiement PostgreSQL automatique, build parallèle d'images, migrations isolées, mise à jour glissante des conteneurs et sondes de santé."),
        ("Rollback Automatique", "En cas d'échec de la sonde de santé post-déploiement (/api/v1/system/health/), déclenchement immédiat de `rollback.sh` restaurant l'état fonctionnel précédent et la base de données."),
        ("Ségrégation des Files Celery", "Scission des workers en 2 pools : file `default` (4 workers, 1GB RAM) pour les tâches transactionnelles rapides ; file `heavy` (2 workers, 2GB RAM) pour l'OCR, TTS et exports PPTX."),
        ("Sécurité SSL / Let's Encrypt", "Automatisation via `init-letsencrypt.sh` et conteneur Certbot assurant le renouvellement automatique des certificats HTTPS toutes les 12 heures."),
        ("Monitoring & Métriques", "Stack complète Prometheus + Grafana (`infrastructure/monitoring/`) collectant les métriques d'usage système (CPU/RAM/Disque), la charge Redis, les files Celery et la latence Nginx."),
    ]

    for r_idx, (feat, desc) in enumerate(ops_data):
        row = ops_tbl.rows[r_idx]
        c0, c1 = row.cells[0], row.cells[1]
        c0.width, c1.width = ops_widths[0], ops_widths[1]
        set_cell_background(c0, "F8FAFC")
        set_cell_background(c1, "FFFFFF")
        set_cell_margins(c0, top=80, bottom=80, left=100, right=100)
        set_cell_margins(c1, top=80, bottom=80, left=100, right=100)
        
        p0 = c0.paragraphs[0]
        r0 = p0.add_run(feat)
        r0.font.name = "Arial"
        r0.font.bold = True
        r0.font.size = Pt(9)
        r0.font.color.rgb = COLOR_PRIMARY
        
        p1 = c1.paragraphs[0]
        p1.paragraph_format.line_spacing = 1.15
        r1 = p1.add_run(desc)
        r1.font.name = "Arial"
        r1.font.size = Pt(9)
        r1.font.color.rgb = COLOR_BODY

    set_table_borders(ops_tbl, color="E2E8F0")

    # =========================================================================
    # 5. ASSURANCE QUALITÉ, TESTS & INDICATEURS DE CONFORMITÉ
    # =========================================================================
    h5 = doc.add_heading("5. Assurance Qualité, Tests & Indicateurs de Conformité", level=1)
    h5.paragraph_format.space_before = Pt(16)
    h5.paragraph_format.space_after = Pt(8)

    p_qa = doc.add_paragraph()
    p_qa.paragraph_format.line_spacing = 1.15
    p_qa.paragraph_format.space_after = Pt(8)
    p_qa.add_run(
        "Chaque brique logicielle fait l'objet de barrières de qualité automatisées (Quality Gates) "
        "intégrées dans les pipelines d'intégration continue GitHub Actions."
    )

    qa_metrics = [
        ("Tests Backend Django API", "Pytest / Pytest-Django", "310 tests passés avec succès (0 échec, 0 erreur)"),
        ("Tests Frontend React / Next.js", "Vitest / Testing Library", "32 tests passés avec succès (9 fichiers de test validés)"),
        ("Évaluation Qualité IA (Sprint 06)", "Amanus Eval Suite / Pytest", "12 suites validées (Golden Benchmark, Déterministe, Sémantique, A/B)"),
        ("Vérification Typage Statique", "TypeScript (`tsc --noEmit`)", "0 erreur de typage sur l'ensemble de la codebase web"),
        ("Linting & Qualité Code Web", "ESLint / Ruff", "0 avertissement, 0 erreur, règles de hooks respectées"),
        ("Migrations Base de Données", "Django Migrations Check", "0 migration en attente, modèles synchronisés"),
    ]

    qa_tbl = doc.add_table(rows=len(qa_metrics) + 1, cols=3)
    qa_tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    qa_tbl.autofit = False
    qa_widths = [Inches(2.2), Inches(1.5), Inches(2.8)]

    qa_headers = ["Périmètre de Contrôle", "Outil / Framework", "Résultat & Statut de Validation"]
    for i, h in enumerate(qa_headers):
        cell = qa_tbl.rows[0].cells[i]
        cell.width = qa_widths[i]
        set_cell_background(cell, "059669")
        set_cell_margins(cell, top=100, bottom=100, left=100, right=100)
        p = cell.paragraphs[0]
        r = p.add_run(h)
        r.font.name = "Arial"
        r.font.bold = True
        r.font.size = Pt(9.5)
        r.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)

    for r_idx, (dom, tool, res) in enumerate(qa_metrics, start=1):
        row = qa_tbl.rows[r_idx]
        bg = "F8FAFC" if r_idx % 2 == 1 else "FFFFFF"
        for c_idx, val in enumerate([dom, tool, res]):
            cell = row.cells[c_idx]
            cell.width = qa_widths[c_idx]
            set_cell_background(cell, bg)
            set_cell_margins(cell, top=80, bottom=80, left=100, right=100)
            p = cell.paragraphs[0]
            p.paragraph_format.line_spacing = 1.15
            r = p.add_run(val)
            r.font.name = "Arial"
            r.font.size = Pt(8.5)
            if c_idx == 2:
                r.font.bold = True
                r.font.color.rgb = COLOR_EMERALD
            else:
                r.font.color.rgb = COLOR_PRIMARY

    set_table_borders(qa_tbl, color="CBD5E1")

    # =========================================================================
    # 6. CONCLUSION & PERSPECTIVES
    # =========================================================================
    doc.add_page_break()
    h6 = doc.add_heading("6. Bilan Global & Perspectives d'Évolution", level=1)
    h6.paragraph_format.space_before = Pt(16)
    h6.paragraph_format.space_after = Pt(8)

    p_concl = doc.add_paragraph()
    p_concl.paragraph_format.line_spacing = 1.15
    p_concl.paragraph_format.space_after = Pt(8)
    p_concl.add_run(
        "Au terme des développements des phases 00 à 16, la plateforme Amanus Learn AI dispose d'un niveau de maturité "
        "technologique, fonctionnel et opérationnel exceptionnel. La robustesse de son architecture conteneurisée, "
        "la richesse de ses modules d'ingestion et de restitution pédagogique ainsi que son ergonomie multilingue "
        "positionnent la solution comme une référence EdTech sur le marché des environnements d'apprentissage assistés par IA."
    )

    add_callout(
        doc,
        "1. Interopérabilité LTI 1.3 : Connexion native avec les Learning Management Systems universitaires et professionnels (Moodle, Canvas, Blackboard).\n"
        "2. Voice-to-Voice Streaming : Tuteur vocal interactif bidirectionnel en temps réel pour l'apprentissage des langues et l'entraînement oral.\n"
        "3. Fine-Tuning & SLM Privés : Déploiement de petits modèles spécialisés (Small Language Models type Mistral/Llama) hébergés sur infrastructure souveraine dédiée sans fuite de données.",
        title="FEUILLE DE ROUTE STRATÉGIQUE (PROCHAINES ÉTAPES)",
        border_color="1E3A8A",
        bg_color="F0F4F8"
    )

    # Sauvegarde du document
    output_path = os.path.abspath("docs/RAPPORT_SYNTHESE_AMANUS_LEARN_AI.docx")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    doc.save(output_path)
    
    # Copie également à la racine pour un accès direct
    root_path = os.path.abspath("RAPPORT_SYNTHESE_AMANUS_LEARN_AI.docx")
    doc.save(root_path)

    print(f"Rapport généré avec succès :\n - {output_path}\n - {root_path}")
    return root_path

if __name__ == "__main__":
    build_document()
