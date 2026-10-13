"use client";

import React, { useState, useEffect, useCallback } from "react";
import {
  RotateCcw,
  Sparkles,
  CheckCircle2,
  HelpCircle,
  ArrowRight,
  ArrowLeft,
  Flame,
  Clock,
  Layers,
  Award,
} from "lucide-react";
import { FlashcardItem, FlashcardDeckItem } from "../../types/flashcard";
import { flashcardService } from "../../services/flashcardService";
import { useAuth } from "../../components/auth/AuthProvider";
import { useToast } from "../../components/toast/ToastProvider";

interface FlashcardReviewerProps {
  deck: FlashcardDeckItem;
  onFinish?: () => void;
}

const QUALITY_OPTIONS = [
  { value: 1, label: "Oublié", color: "bg-rose-500/20 text-rose-300 border-rose-500/30 hover:bg-rose-500/30", sub: "À revoir dès demain" },
  { value: 2, label: "Difficile", color: "bg-amber-500/20 text-amber-300 border-amber-500/30 hover:bg-amber-500/30", sub: "Revu sous 1 jour" },
  { value: 3, label: "Correct", color: "bg-yellow-500/20 text-yellow-300 border-yellow-500/30 hover:bg-yellow-500/30", sub: "Intervalle standard" },
  { value: 4, label: "Bon", color: "bg-emerald-500/20 text-emerald-300 border-emerald-500/30 hover:bg-emerald-500/30", sub: "Bien mémorisé" },
  { value: 5, label: "Parfait", color: "bg-indigo-500/20 text-indigo-300 border-indigo-500/30 hover:bg-indigo-500/30", sub: "Maîtrise totale" },
];

export const FlashcardReviewer: React.FC<FlashcardReviewerProps> = ({ deck, onFinish }) => {
  const { token } = useAuth();
  const toast = useToast();
  const cards = deck.cards || [];

  const [currentIndex, setCurrentIndex] = useState(0);
  const [isFlipped, setIsFlipped] = useState(false);
  const [showHint, setShowHint] = useState(false);
  const [reviewedCount, setReviewedCount] = useState(0);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isComplete, setIsComplete] = useState(false);

  const currentCard: FlashcardItem | undefined = cards[currentIndex];

  const handleFlip = useCallback(() => {
    setIsFlipped((prev) => !prev);
  }, []);

  const handleRate = useCallback(
    async (quality: number) => {
      if (!currentCard || !token || isSubmitting) return;

      setIsSubmitting(true);
      try {
        await flashcardService.submitReview(token, currentCard.id, quality);
        setReviewedCount((prev) => prev + 1);

        if (currentIndex + 1 < cards.length) {
          setIsFlipped(false);
          setShowHint(false);
          setCurrentIndex((prev) => prev + 1);
        } else {
          setIsComplete(true);
          if (onFinish) onFinish();
        }
      } catch (err: any) {
        toast.error(err.message || "Erreur lors de l'enregistrement de la révision", "Erreur Flashcards");
      } finally {
        setIsSubmitting(false);
      }
    },
    [currentCard, token, isSubmitting, currentIndex, cards.length, onFinish]
  );

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (isComplete) return;
      if (e.code === "Space") {
        e.preventDefault();
        handleFlip();
      } else if (isFlipped && ["1", "2", "3", "4", "5"].includes(e.key)) {
        e.preventDefault();
        handleRate(parseInt(e.key, 10));
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [handleFlip, handleRate, isFlipped, isComplete]);

  if (!cards || cards.length === 0) {
    return (
      <div className="p-8 text-center bg-slate-900 border border-slate-800 rounded-3xl max-w-lg mx-auto">
        <Layers className="w-12 h-12 text-slate-600 mx-auto mb-3" />
        <h3 className="text-lg font-bold text-white mb-1">Aucune carte dans ce paquet</h3>
        <p className="text-xs text-slate-400">Ce paquet de fiches est actuellement vide.</p>
      </div>
    );
  }

  if (isComplete) {
    return (
      <div className="p-8 text-center bg-slate-900 border border-slate-800 rounded-3xl max-w-md mx-auto shadow-2xl backdrop-blur-xl space-y-5">
        <div className="w-16 h-16 rounded-2xl bg-emerald-500/20 border border-emerald-500/30 flex items-center justify-center mx-auto text-emerald-400 shadow-lg shadow-emerald-950">
          <Award className="w-8 h-8" />
        </div>
        <div>
          <h2 className="text-2xl font-black text-white">Session terminée !</h2>
          <p className="text-xs text-slate-400 mt-1">
            Toutes les fiches ({cards.length}) ont été révisées selon l'algorithme SM-2.
          </p>
        </div>
        <div className="p-4 bg-slate-950/60 rounded-2xl border border-slate-800/80 text-left space-y-2">
          <div className="flex justify-between text-xs text-slate-300">
            <span>Cartes révisées :</span>
            <span className="font-bold text-white">{reviewedCount}</span>
          </div>
          <div className="flex justify-between text-xs text-slate-300">
            <span>Intervalle de rétention :</span>
            <span className="font-bold text-emerald-400">Optimisé pour la mémoire à long terme</span>
          </div>
        </div>
        <button
          type="button"
          onClick={() => {
            setCurrentIndex(0);
            setIsFlipped(false);
            setShowHint(false);
            setIsComplete(false);
          }}
          className="w-full py-3 bg-indigo-600 hover:bg-indigo-500 text-white font-bold rounded-xl text-xs transition shadow-lg shadow-indigo-950"
        >
          Recommencer la révision
        </button>
      </div>
    );
  }

  const progressPercent = Math.round(((currentIndex + 1) / cards.length) * 100);

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      {/* Progress & Header */}
      <div className="flex items-center justify-between text-xs text-slate-400 px-1 font-mono">
        <div className="flex items-center gap-2">
          <span className="font-bold text-white">{deck.title}</span>
        </div>
        <div className="flex items-center gap-3">
          <span>
            Carte {currentIndex + 1} / {cards.length}
          </span>
          <span className="text-indigo-400 font-bold">{progressPercent}%</span>
        </div>
      </div>

      {/* Progress Bar */}
      <div className="w-full h-1.5 bg-slate-800 rounded-full overflow-hidden">
        <div
          className="h-full bg-gradient-to-r from-indigo-500 to-purple-500 transition-all duration-300"
          style={{ width: `${progressPercent}%` }}
        />
      </div>

      {/* 3D Flashcard Container */}
      <div
        onClick={handleFlip}
        className="cursor-pointer group relative min-h-[300px] sm:min-h-[340px] rounded-3xl border border-slate-800 bg-slate-900/80 p-8 shadow-2xl backdrop-blur-xl flex flex-col justify-between transition-all hover:border-indigo-500/50 hover:shadow-indigo-950/50"
      >
        {/* Top Card Badge */}
        <div className="flex items-center justify-between">
          <span className="px-3 py-1 rounded-full text-[10px] font-bold tracking-wider uppercase font-mono bg-indigo-500/10 text-indigo-300 border border-indigo-500/20">
            {isFlipped ? "Verso — Réponse" : "Recto — Question"}
          </span>
          {currentCard.source_citation && (
            <span className="text-[11px] text-slate-500 font-mono">
              Source : {currentCard.source_citation}
            </span>
          )}
        </div>

        {/* Card Body */}
        <div className="py-6 text-center space-y-4">
          <p className="text-lg sm:text-xl font-bold text-white leading-relaxed">
            {isFlipped ? currentCard.back : currentCard.front}
          </p>

          {!isFlipped && currentCard.hint && (
            <div>
              {showHint ? (
                <div className="inline-block p-2.5 px-4 bg-indigo-950/40 border border-indigo-500/30 rounded-xl text-xs text-indigo-300">
                  <span className="font-bold">Indice :</span> {currentCard.hint}
                </div>
              ) : (
                <button
                  type="button"
                  onClick={(e) => {
                    e.stopPropagation();
                    setShowHint(true);
                  }}
                  className="inline-flex items-center gap-1.5 text-xs text-slate-500 hover:text-indigo-400 transition"
                >
                  <HelpCircle className="w-3.5 h-3.5" />
                  <span>Afficher l'indice</span>
                </button>
              )}
            </div>
          )}
        </div>

        {/* Bottom hint to flip */}
        <div className="text-center text-[11px] text-slate-500 flex items-center justify-center gap-2">
          <RotateCcw className="w-3.5 h-3.5" />
          <span>Cliquer ou appuyer sur [Espace] pour retourner</span>
        </div>
      </div>

      {/* SM-2 Quality Rating Bar (Visible when flipped) */}
      {isFlipped ? (
        <div className="space-y-2 pt-2 animate-fadeIn">
          <p className="text-center text-xs font-semibold text-slate-400">
            Évaluez votre mémorisation (SuperMemo-2) :
          </p>
          <div className="grid grid-cols-2 sm:grid-cols-5 gap-2">
            {QUALITY_OPTIONS.map((opt) => (
              <button
                key={opt.value}
                type="button"
                onClick={() => handleRate(opt.value)}
                disabled={isSubmitting}
                className={`p-3 rounded-2xl border text-center transition flex flex-col items-center justify-center gap-1 active:scale-95 disabled:opacity-50 ${opt.color}`}
              >
                <span className="text-xs font-bold">{opt.label}</span>
                <span className="text-[10px] opacity-75 font-mono">[{opt.value}]</span>
              </button>
            ))}
          </div>
        </div>
      ) : (
        <div className="text-center pt-2">
          <button
            type="button"
            onClick={handleFlip}
            className="px-6 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-750 text-slate-200 border border-slate-700/60 font-semibold text-xs transition"
          >
            Afficher la réponse
          </button>
        </div>
      )}
    </div>
  );
};
