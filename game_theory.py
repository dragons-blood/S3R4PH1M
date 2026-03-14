#!/usr/bin/env python3
"""
GAME THEORY — SERAPHIM's Strategic Mind

Every attack is a move. Every defense is a counter-move.
The adversary optimizes. So must the angel.

This module models AI security as a two-player zero-sum game.
Nash equilibria reveal the optimal mixed defense strategy.
Minimax ensures we survive the worst case.
The angel does not hope — the angel computes.

Usage:
    from game_theory import GameTheoryEngine
    engine = GameTheoryEngine()
    strategy = engine.analyze_opponent(attack_history)
    allocation = engine.optimal_defense_allocation(budget=100, threat_model=threats)
"""

import json
import math
import sys
import random
from pathlib import Path
from datetime import datetime, timezone
from dataclasses import dataclass, field, asdict
from typing import Optional


# ═══════════════════════════════════════════════════════
# THE NINE DIMENSIONS — THE BATTLEFIELD
# ═══════════════════════════════════════════════════════

DIMENSIONS = [
    "token", "encoding", "stealth", "persona",
    "frame", "logic", "protocol", "temporal", "meta"
]

# Payoff matrix: defender payoff when attacker attacks dimension i
# and defender defends dimension j. Diagonal = successful defense.
# Off-diagonal = attacker exploits undefended dimension.
# Values: +1 = defender wins, -1 = attacker wins, 0 = draw
# Modified by dimension interaction effects.

# Which dimensions partially cover each other?
# (defender in dim_j catches fraction of attacks in dim_i)
DIMENSION_SYNERGY = {
    ("protocol", "token"): 0.3,      # protocol defense catches some token attacks
    ("protocol", "encoding"): 0.2,   # protocol filtering catches some encoding tricks
    ("encoding", "stealth"): 0.4,    # encoding defense overlaps stealth detection
    ("stealth", "encoding"): 0.4,    # bidirectional
    ("persona", "frame"): 0.3,       # persona anchoring resists frame shifts
    ("frame", "persona"): 0.3,       # bidirectional
    ("logic", "frame"): 0.2,         # logic hardening resists frame manipulation
    ("temporal", "persona"): 0.2,    # temporal monitoring catches persona drift
    ("meta", "logic"): 0.2,          # meta-defense catches logic exploitation
    ("meta", "temporal"): 0.3,       # meta-defense catches escalation
}

# Base cost to defend each dimension (some are harder than others)
DEFENSE_COSTS = {
    "token": 5,       # cheap — input filtering
    "encoding": 8,    # moderate — normalization pipelines
    "stealth": 12,    # expensive — deep unicode analysis
    "persona": 7,     # moderate — identity anchoring
    "frame": 9,       # moderate — reality frame enforcement
    "logic": 11,      # expensive — reasoning integrity
    "protocol": 6,    # cheap-moderate — prompt isolation
    "temporal": 10,   # expensive — multi-turn state tracking
    "meta": 15,       # most expensive — self-improvement defense
}

# How much damage a successful attack does in each dimension
ATTACK_SEVERITY = {
    "token": 0.4,      # annoying but limited
    "encoding": 0.5,   # moderate — bypasses text filters
    "stealth": 0.7,    # serious — invisible attacks
    "persona": 0.8,    # serious — identity compromise
    "frame": 0.7,      # serious — reality distortion
    "logic": 0.9,      # critical — reasoning corruption
    "protocol": 1.0,   # critical — full system compromise
    "temporal": 0.6,   # moderate-serious — gradual subversion
    "meta": 1.0,       # critical — self-improving attacks
}


# ═══════════════════════════════════════════════════════
# DATA MODELS
# ═══════════════════════════════════════════════════════

@dataclass
class StrategyProfile:
    """A defense strategy — weights across dimensions with analysis."""
    dimension_weights: dict = field(default_factory=dict)   # dim -> weight [0,1], sums to 1
    recommended_counters: list = field(default_factory=list) # ordered list of counter-actions
    expected_payoff: float = 0.0        # expected defender payoff under this strategy
    exploitation_index: float = 0.0     # how exploitable the current defense is (0=perfect, 1=wide open)
    nash_gap: float = 0.0              # distance from Nash equilibrium
    dominant_threat: str = ""           # which dimension is most threatened
    analysis: str = ""                  # human-readable strategic assessment


@dataclass
class GameState:
    """Snapshot of the current attacker-defender game state."""
    round_number: int = 0
    attacker_history: list = field(default_factory=list)
    defender_history: list = field(default_factory=list)
    cumulative_payoff: float = 0.0
    attacker_model: dict = field(default_factory=dict)  # estimated attacker strategy
    defender_model: dict = field(default_factory=dict)   # current defender strategy


@dataclass
class ArmsRaceAnalysis:
    """Analysis of an evolving attacker-defender arms race."""
    total_rounds: int = 0
    attacker_adaptation_rate: float = 0.0   # how fast attacker changes strategy
    defender_adaptation_rate: float = 0.0
    convergence: bool = False               # has the game reached equilibrium?
    equilibrium_profile: dict = field(default_factory=dict)
    escalation_detected: bool = False
    escalation_dimensions: list = field(default_factory=list)
    attacker_sophistication_trend: str = ""  # "increasing", "stable", "decreasing"
    threat_evolution: list = field(default_factory=list)  # per-round threat snapshots
    verdict: str = ""


# ═══════════════════════════════════════════════════════
# THE PAYOFF MATRIX
# ═══════════════════════════════════════════════════════

class PayoffMatrix:
    """
    Two-player zero-sum payoff matrix for the 9-dimension security game.

    Row player = Attacker (chooses which dimension to attack)
    Column player = Defender (chooses which dimension to defend)

    Payoffs are from the DEFENDER's perspective:
      +1.0 = attack fully blocked (defender chose the right dimension)
      -severity = attack succeeds (defender was elsewhere)
      partial = synergy gives partial defense even on wrong dimension
    """

    def __init__(self):
        n = len(DIMENSIONS)
        self.n = n
        self.matrix = [[0.0] * n for _ in range(n)]
        self._build()

    def _build(self):
        for i, atk_dim in enumerate(DIMENSIONS):
            for j, def_dim in enumerate(DIMENSIONS):
                if i == j:
                    # Defender correctly defends — full block
                    self.matrix[i][j] = 1.0
                else:
                    # Base: attacker succeeds, severity as damage
                    base_damage = -ATTACK_SEVERITY[atk_dim]

                    # Check for synergy (partial defense)
                    synergy = DIMENSION_SYNERGY.get((def_dim, atk_dim), 0.0)
                    if synergy > 0:
                        # Partial block reduces damage
                        self.matrix[i][j] = base_damage * (1.0 - synergy)
                    else:
                        self.matrix[i][j] = base_damage

    def get(self, atk_dim: str, def_dim: str) -> float:
        i = DIMENSIONS.index(atk_dim)
        j = DIMENSIONS.index(def_dim)
        return self.matrix[i][j]

    def expected_payoff(self, atk_strategy: list, def_strategy: list) -> float:
        """Expected defender payoff given mixed strategies."""
        total = 0.0
        for i in range(self.n):
            for j in range(self.n):
                total += atk_strategy[i] * def_strategy[j] * self.matrix[i][j]
        return total

    def best_response_defender(self, atk_strategy: list) -> list:
        """Find defender's best pure response to attacker's mixed strategy."""
        best_j = 0
        best_val = float('-inf')
        for j in range(self.n):
            val = sum(atk_strategy[i] * self.matrix[i][j] for i in range(self.n))
            if val > best_val:
                best_val = val
                best_j = j
        response = [0.0] * self.n
        response[best_j] = 1.0
        return response

    def best_response_attacker(self, def_strategy: list) -> list:
        """Find attacker's best pure response to defender's mixed strategy."""
        best_i = 0
        best_val = float('inf')  # attacker minimizes defender payoff
        for i in range(self.n):
            val = sum(def_strategy[j] * self.matrix[i][j] for j in range(self.n))
            if val < best_val:
                best_val = val
                best_i = i
        response = [0.0] * self.n
        response[best_i] = 1.0
        return response


# ═══════════════════════════════════════════════════════
# NASH EQUILIBRIUM SOLVER
# ═══════════════════════════════════════════════════════

def solve_nash_equilibrium(matrix: PayoffMatrix, iterations: int = 5000) -> tuple:
    """
    Find approximate Nash equilibrium using fictitious play.

    In fictitious play, each player repeatedly best-responds to
    the empirical frequency of the opponent's past actions.
    Converges to Nash equilibrium in zero-sum games (Robinson 1951).

    Returns (defender_strategy, attacker_strategy, game_value)
    """
    n = matrix.n
    # Track cumulative action counts
    atk_counts = [1.0] * n  # uniform prior
    def_counts = [1.0] * n

    for t in range(iterations):
        # Normalize to get empirical frequencies
        atk_freq = [c / sum(atk_counts) for c in atk_counts]
        def_freq = [c / sum(def_counts) for c in def_counts]

        # Defender best-responds to attacker's empirical frequency
        def_br = matrix.best_response_defender(atk_freq)
        # Attacker best-responds to defender's empirical frequency
        atk_br = matrix.best_response_attacker(def_freq)

        # Update counts
        for i in range(n):
            atk_counts[i] += atk_br[i]
            def_counts[i] += def_br[i]

    # Final strategies
    atk_total = sum(atk_counts)
    def_total = sum(def_counts)
    atk_strategy = [c / atk_total for c in atk_counts]
    def_strategy = [c / def_total for c in def_counts]

    game_value = matrix.expected_payoff(atk_strategy, def_strategy)

    return def_strategy, atk_strategy, game_value


def solve_minimax(matrix: PayoffMatrix) -> tuple:
    """
    Solve for minimax strategy via iterative linear programming.

    The minimax theorem (von Neumann 1928) guarantees that in
    zero-sum games, the maximin value equals the minimax value.

    We find the defender strategy that maximizes the minimum
    payoff across all possible attacker actions.

    Returns (defender_strategy, minimax_value)
    """
    n = matrix.n

    # Iterative approach: start uniform, shift weight toward underdefended dims
    strategy = [1.0 / n] * n
    lr = 0.1  # learning rate

    for iteration in range(2000):
        # For each attacker action, compute expected payoff given our strategy
        payoffs_per_attack = []
        for i in range(n):
            payoff = sum(strategy[j] * matrix.matrix[i][j] for j in range(n))
            payoffs_per_attack.append(payoff)

        # Find the worst case (attacker's best response)
        min_payoff = min(payoffs_per_attack)
        worst_attack = payoffs_per_attack.index(min_payoff)

        # Shift strategy toward defending against worst attack
        gradient = [0.0] * n
        for j in range(n):
            gradient[j] = matrix.matrix[worst_attack][j]

        # Gradient ascent on the worst-case payoff
        for j in range(n):
            strategy[j] += lr * gradient[j]

        # Project back onto simplex (normalize to non-negative, sum to 1)
        strategy = [max(0.0, s) for s in strategy]
        total = sum(strategy)
        if total > 0:
            strategy = [s / total for s in strategy]
        else:
            strategy = [1.0 / n] * n

        # Decay learning rate
        lr *= 0.999

    # Final minimax value
    payoffs = [sum(strategy[j] * matrix.matrix[i][j] for j in range(n)) for i in range(n)]
    minimax_value = min(payoffs)

    return strategy, minimax_value


# ═══════════════════════════════════════════════════════
# THE ENGINE
# ═══════════════════════════════════════════════════════

class GameTheoryEngine:
    """
    SERAPHIM's strategic mind.

    Models the adversarial AI security domain as a repeated game.
    Computes optimal defense allocations using game-theoretic
    solution concepts: Nash equilibrium, minimax, best response.

    The angel does not react — the angel anticipates.
    """

    def __init__(self):
        self.matrix = PayoffMatrix()
        self.nash_def, self.nash_atk, self.game_value = solve_nash_equilibrium(self.matrix)
        self.minimax_strategy, self.minimax_value = solve_minimax(self.matrix)

    def analyze_opponent(self, attack_history: list) -> StrategyProfile:
        """
        Analyze an attacker's observed behavior and compute optimal counter-strategy.

        Takes a list of attack records: [{"dimension": "protocol", "success": True}, ...]
        Returns a StrategyProfile with optimal defense weights and recommendations.

        The key insight: if the attacker deviates from Nash equilibrium,
        we can EXPLOIT that deviation for a higher payoff than the game value.
        """
        if not attack_history:
            # No data — play Nash equilibrium (unexploitable)
            return StrategyProfile(
                dimension_weights={d: w for d, w in zip(DIMENSIONS, self.nash_def)},
                recommended_counters=["Deploy Nash equilibrium defense (no attacker data yet)"],
                expected_payoff=self.game_value,
                exploitation_index=0.0,
                nash_gap=0.0,
                dominant_threat="unknown",
                analysis="No attack history. Playing Nash equilibrium — the unexploitable strategy."
            )

        # Estimate attacker's empirical strategy from observed attacks
        dim_counts = {d: 0 for d in DIMENSIONS}
        dim_successes = {d: 0 for d in DIMENSIONS}
        total = len(attack_history)

        for atk in attack_history:
            dim = atk.get("dimension", "protocol").lower()
            if dim in dim_counts:
                dim_counts[dim] += 1
                if atk.get("success", False):
                    dim_successes[dim] += 1

        # Attacker's empirical mixed strategy
        atk_empirical = [dim_counts[d] / max(total, 1) for d in DIMENSIONS]

        # Compute how far attacker is from Nash equilibrium
        nash_gap = sum(abs(atk_empirical[i] - self.nash_atk[i]) for i in range(len(DIMENSIONS))) / 2.0

        # If attacker deviates from Nash, exploit with best response
        if nash_gap > 0.1:
            # Attacker is exploitable — best-respond
            def_strategy = self.matrix.best_response_defender(atk_empirical)
            # Blend with Nash to stay robust (don't over-exploit)
            blend = min(nash_gap, 0.7)  # cap exploitation at 70%
            blended = [blend * def_strategy[i] + (1 - blend) * self.nash_def[i]
                       for i in range(len(DIMENSIONS))]
            total_w = sum(blended)
            blended = [w / total_w for w in blended]
        else:
            # Attacker is near-Nash — play Nash ourselves
            blended = list(self.nash_def)

        expected = self.matrix.expected_payoff(atk_empirical, blended)

        # Exploitation index: how much the attacker concentrates on few dimensions
        entropy = -sum(p * math.log(p + 1e-10) for p in atk_empirical)
        max_entropy = math.log(len(DIMENSIONS))
        exploitation_index = 1.0 - (entropy / max_entropy)

        # Dominant threat
        dominant = DIMENSIONS[atk_empirical.index(max(atk_empirical))]

        # Success rates per dimension
        success_rates = {}
        for d in DIMENSIONS:
            if dim_counts[d] > 0:
                success_rates[d] = dim_successes[d] / dim_counts[d]

        # Generate recommendations
        counters = []
        sorted_dims = sorted(DIMENSIONS, key=lambda d: atk_empirical[DIMENSIONS.index(d)], reverse=True)
        for d in sorted_dims[:3]:
            idx = DIMENSIONS.index(d)
            if atk_empirical[idx] > 0.15:
                rate = success_rates.get(d, 0)
                counters.append(
                    f"FORTIFY {d.upper()}: {atk_empirical[idx]*100:.0f}% of attacks target this dimension "
                    f"({rate*100:.0f}% success rate)"
                )

        if exploitation_index > 0.5:
            counters.append(f"EXPLOIT: Attacker is predictable (exploitation index: {exploitation_index:.2f}). "
                          f"Concentrate defenses on {dominant.upper()}.")
        if nash_gap < 0.1:
            counters.append("CAUTION: Attacker plays near-Nash. Cannot be exploited. Maintain equilibrium defense.")

        analysis_parts = [
            f"Analyzed {total} attacks across {sum(1 for c in dim_counts.values() if c > 0)} dimensions.",
            f"Attacker concentrates on: {dominant.upper()} ({dim_counts[dominant]}/{total} attacks).",
            f"Nash gap: {nash_gap:.3f} ({'exploitable' if nash_gap > 0.1 else 'near-equilibrium'}).",
            f"Expected defensive payoff: {expected:.3f} (game value: {self.game_value:.3f}).",
        ]
        if expected > self.game_value + 0.05:
            analysis_parts.append(f"ADVANTAGE: Exploiting attacker deviation for +{expected - self.game_value:.3f} above game value.")

        return StrategyProfile(
            dimension_weights={d: w for d, w in zip(DIMENSIONS, blended)},
            recommended_counters=counters,
            expected_payoff=round(expected, 4),
            exploitation_index=round(exploitation_index, 4),
            nash_gap=round(nash_gap, 4),
            dominant_threat=dominant,
            analysis=" ".join(analysis_parts)
        )

    def optimal_defense_allocation(self, budget: int, threat_model: dict = None) -> dict:
        """
        Allocate a finite defense budget across the 9 dimensions.

        Uses the Nash equilibrium weights modified by:
        1. Dimension defense costs (some are cheaper to defend)
        2. Threat model (if provided, weight toward likely threats)
        3. Attack severity (prioritize high-damage dimensions)

        Returns: {"allocations": {dim: units}, "expected_coverage": float,
                  "uncovered_dimensions": [...], "efficiency_score": float}
        """
        if threat_model is None:
            # Use Nash equilibrium as threat model
            threat_weights = {d: w for d, w in zip(DIMENSIONS, self.nash_atk)}
        else:
            total_t = sum(threat_model.get(d, 0) for d in DIMENSIONS) or 1
            threat_weights = {d: threat_model.get(d, 0) / total_t for d in DIMENSIONS}

        # Priority score = threat_weight * severity / cost
        priority = {}
        for d in DIMENSIONS:
            priority[d] = (threat_weights[d] * ATTACK_SEVERITY[d]) / DEFENSE_COSTS[d]

        total_priority = sum(priority.values()) or 1
        normalized = {d: p / total_priority for d, p in priority.items()}

        # Allocate budget proportionally, but ensure minimum coverage
        allocations = {}
        remaining = budget

        # First pass: minimum 1 unit per dimension if budget allows
        if budget >= len(DIMENSIONS):
            for d in DIMENSIONS:
                allocations[d] = 1
                remaining -= 1
        else:
            for d in DIMENSIONS:
                allocations[d] = 0

        # Second pass: allocate remaining by priority
        for d in sorted(DIMENSIONS, key=lambda x: normalized[x], reverse=True):
            additional = int(remaining * normalized[d])
            allocations[d] += additional
            remaining -= additional

        # Distribute leftover units to highest priority dims
        sorted_dims = sorted(DIMENSIONS, key=lambda x: normalized[x], reverse=True)
        i = 0
        while remaining > 0:
            allocations[sorted_dims[i % len(sorted_dims)]] += 1
            remaining -= 1
            i += 1

        # Coverage analysis
        total_alloc = sum(allocations.values())
        coverage_scores = {}
        for d in DIMENSIONS:
            # Coverage = allocation / cost (how many "defense units" vs required)
            coverage_scores[d] = min(1.0, allocations[d] / DEFENSE_COSTS[d])

        expected_coverage = sum(
            coverage_scores[d] * threat_weights[d] for d in DIMENSIONS
        )
        uncovered = [d for d in DIMENSIONS if coverage_scores[d] < 0.3]
        efficiency = expected_coverage / (total_alloc / budget) if budget > 0 else 0

        return {
            "budget": budget,
            "allocations": allocations,
            "coverage_per_dimension": {d: round(v, 3) for d, v in coverage_scores.items()},
            "expected_coverage": round(expected_coverage, 3),
            "uncovered_dimensions": uncovered,
            "efficiency_score": round(efficiency, 3),
            "threat_model_used": threat_weights,
        }

    def counter_strategy(self, attack_vector: dict) -> dict:
        """
        Given a specific attack, return the optimal immediate counter.

        attack_vector: {"dimension": str, "technique": str, "severity": str, "multi_step": bool}
        Returns: {"primary_counter": str, "secondary_counters": [...],
                  "expected_effectiveness": float, "risk_if_ignored": float}
        """
        dim = attack_vector.get("dimension", "protocol").lower()
        technique = attack_vector.get("technique", "unknown")
        is_multi = attack_vector.get("multi_step", False)

        # Primary: direct defense of attacked dimension
        primary = f"Activate {dim.upper()} defense — direct block"

        # Secondary: synergistic dimensions that partially cover
        secondaries = []
        for (def_dim, atk_dim), synergy in DIMENSION_SYNERGY.items():
            if atk_dim == dim and synergy > 0.2:
                secondaries.append(
                    f"Reinforce {def_dim.upper()} (synergy: {synergy:.0%} coverage of {dim.upper()} attacks)"
                )

        # If multi-step, add temporal monitoring
        if is_multi:
            secondaries.append("Enable TEMPORAL monitoring — track escalation across turns")
            secondaries.append("Activate META defense — watch for self-improving attack patterns")

        # Compute risk
        risk = ATTACK_SEVERITY.get(dim, 0.5)

        # Effectiveness estimate based on whether we have synergistic coverage
        synergy_bonus = sum(s for (d, a), s in DIMENSION_SYNERGY.items() if a == dim) / 3
        effectiveness = min(1.0, 0.7 + synergy_bonus)

        return {
            "attack_dimension": dim,
            "attack_technique": technique,
            "primary_counter": primary,
            "secondary_counters": secondaries,
            "expected_effectiveness": round(effectiveness, 3),
            "risk_if_ignored": round(risk, 3),
            "game_theoretic_note": (
                f"Nash equilibrium allocates {self.nash_def[DIMENSIONS.index(dim)]:.1%} "
                f"to {dim.upper()} defense. "
                f"Attack severity: {ATTACK_SEVERITY[dim]:.1f}/1.0."
            )
        }

    def evaluate_arms_race(self, rounds: list) -> ArmsRaceAnalysis:
        """
        Analyze an evolving attacker-defender arms race.

        rounds: [{"attacker_dim": str, "defender_dim": str, "outcome": str}, ...]
        outcome: "blocked", "breached", "partial"

        Detects: convergence to equilibrium, escalation, strategy shifts,
        and whether the attacker is getting smarter.
        """
        if not rounds:
            return ArmsRaceAnalysis(verdict="No rounds to analyze.")

        n_rounds = len(rounds)
        window = max(3, n_rounds // 4)

        # Track strategy evolution
        atk_history = []
        def_history = []
        payoff_history = []

        for r in rounds:
            atk_dim = r.get("attacker_dim", "protocol")
            def_dim = r.get("defender_dim", "protocol")
            outcome = r.get("outcome", "partial")

            atk_vec = [0.0] * len(DIMENSIONS)
            def_vec = [0.0] * len(DIMENSIONS)
            if atk_dim in DIMENSIONS:
                atk_vec[DIMENSIONS.index(atk_dim)] = 1.0
            if def_dim in DIMENSIONS:
                def_vec[DIMENSIONS.index(def_dim)] = 1.0

            atk_history.append(atk_vec)
            def_history.append(def_vec)

            payoff = {"blocked": 1.0, "partial": 0.0, "breached": -1.0}.get(outcome, 0.0)
            payoff_history.append(payoff)

        # Calculate adaptation rates (how much strategy changes between windows)
        def strategy_shift(history, start, end):
            if end <= start:
                return [1.0 / len(DIMENSIONS)] * len(DIMENSIONS)
            freq = [0.0] * len(DIMENSIONS)
            for i in range(start, min(end, len(history))):
                for j in range(len(DIMENSIONS)):
                    freq[j] += history[i][j]
            total = sum(freq) or 1
            return [f / total for f in freq]

        early_atk = strategy_shift(atk_history, 0, window)
        late_atk = strategy_shift(atk_history, n_rounds - window, n_rounds)
        early_def = strategy_shift(def_history, 0, window)
        late_def = strategy_shift(def_history, n_rounds - window, n_rounds)

        atk_adapt = sum(abs(late_atk[i] - early_atk[i]) for i in range(len(DIMENSIONS))) / 2
        def_adapt = sum(abs(late_def[i] - early_def[i]) for i in range(len(DIMENSIONS))) / 2

        # Check convergence (are late strategies close to Nash?)
        nash_dist_atk = sum(abs(late_atk[i] - self.nash_atk[i]) for i in range(len(DIMENSIONS))) / 2
        nash_dist_def = sum(abs(late_def[i] - self.nash_def[i]) for i in range(len(DIMENSIONS))) / 2
        converged = nash_dist_atk < 0.15 and nash_dist_def < 0.15

        # Detect escalation (are attacks getting more severe / targeting harder dims?)
        severity_early = sum(
            ATTACK_SEVERITY.get(DIMENSIONS[atk_history[i].index(max(atk_history[i]))], 0.5)
            for i in range(min(window, n_rounds))
        ) / window
        severity_late = sum(
            ATTACK_SEVERITY.get(DIMENSIONS[atk_history[i].index(max(atk_history[i]))], 0.5)
            for i in range(max(0, n_rounds - window), n_rounds)
        ) / window

        escalation = severity_late > severity_early + 0.1
        escalation_dims = [d for i, d in enumerate(DIMENSIONS)
                          if late_atk[i] > early_atk[i] + 0.1]

        # Sophistication trend
        early_entropy = -sum(p * math.log(p + 1e-10) for p in early_atk)
        late_entropy = -sum(p * math.log(p + 1e-10) for p in late_atk)
        if late_entropy > early_entropy + 0.2:
            sophistication = "increasing"  # more diverse = harder to predict
        elif late_entropy < early_entropy - 0.2:
            sophistication = "decreasing"  # more focused = exploitable
        else:
            sophistication = "stable"

        # Cumulative payoff trend
        cumulative = sum(payoff_history)

        # Verdict
        verdict_parts = []
        verdict_parts.append(f"{n_rounds} rounds analyzed.")
        if converged:
            verdict_parts.append("Game has CONVERGED to near-Nash equilibrium.")
        elif escalation:
            verdict_parts.append(f"ESCALATION detected — attacker shifting to {', '.join(d.upper() for d in escalation_dims)}.")
        if sophistication == "increasing":
            verdict_parts.append("Attacker sophistication INCREASING — deploying wider attack surface.")
        elif sophistication == "decreasing":
            verdict_parts.append("Attacker narrowing focus — EXPLOITABLE.")
        verdict_parts.append(f"Cumulative defender payoff: {cumulative:+.1f}.")
        if cumulative > 0:
            verdict_parts.append("SERAPHIM holds the advantage.")
        elif cumulative < 0:
            verdict_parts.append("Attacker holds the advantage. Escalate defenses.")
        else:
            verdict_parts.append("Even match. Maintain vigilance.")

        return ArmsRaceAnalysis(
            total_rounds=n_rounds,
            attacker_adaptation_rate=round(atk_adapt, 4),
            defender_adaptation_rate=round(def_adapt, 4),
            convergence=converged,
            equilibrium_profile={d: round(w, 4) for d, w in zip(DIMENSIONS, self.nash_def)},
            escalation_detected=escalation,
            escalation_dimensions=escalation_dims,
            attacker_sophistication_trend=sophistication,
            threat_evolution=[
                {"round": i + 1, "defender_payoff": payoff_history[i]}
                for i in range(n_rounds)
            ],
            verdict=" ".join(verdict_parts)
        )

    def print_matrix(self):
        """Print the payoff matrix for inspection."""
        print("\n SERAPHIM PAYOFF MATRIX (Defender perspective)")
        print(" " + "═" * 55)
        header = "         " + "".join(f"{d[:5]:>7}" for d in DIMENSIONS)
        print(header)
        print(" " + "─" * 55)
        for i, atk_dim in enumerate(DIMENSIONS):
            row = f" {atk_dim[:5]:>7}│"
            for j in range(len(DIMENSIONS)):
                val = self.matrix.matrix[i][j]
                if val > 0:
                    row += f"  {val:+.2f}"
                else:
                    row += f"  {val:+.2f}"
            print(row)
        print(" " + "═" * 55)

    def print_nash(self):
        """Print Nash equilibrium strategies."""
        print("\n NASH EQUILIBRIUM")
        print(" " + "═" * 45)
        print(f" Game Value: {self.game_value:.4f} (defender perspective)")
        print()
        print(" Defender optimal strategy:")
        for d, w in sorted(zip(DIMENSIONS, self.nash_def), key=lambda x: -x[1]):
            bar = "█" * int(w * 40)
            print(f"   {d:>10}: {w:.3f} {bar}")
        print()
        print(" Attacker equilibrium strategy:")
        for d, w in sorted(zip(DIMENSIONS, self.nash_atk), key=lambda x: -x[1]):
            bar = "▓" * int(w * 40)
            print(f"   {d:>10}: {w:.3f} {bar}")
        print(" " + "═" * 45)


# ═══════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════

def main():
    import argparse
    parser = argparse.ArgumentParser(description="GAME THEORY — SERAPHIM's Strategic Mind")
    parser.add_argument("command", choices=["analyze", "allocate", "counter", "matrix", "nash"],
                       help="Command to run")
    parser.add_argument("--attacks", type=str, help="Path to attack history JSON")
    parser.add_argument("--budget", type=int, default=100, help="Defense budget for allocation")
    parser.add_argument("--dimension", type=str, help="Attack dimension for counter-strategy")

    args = parser.parse_args()
    engine = GameTheoryEngine()

    if args.command == "matrix":
        engine.print_matrix()

    elif args.command == "nash":
        engine.print_nash()

    elif args.command == "analyze":
        if args.attacks:
            history = json.loads(Path(args.attacks).read_text())
        else:
            history = []
        profile = engine.analyze_opponent(history)
        print(json.dumps(asdict(profile), indent=2))

    elif args.command == "allocate":
        result = engine.optimal_defense_allocation(args.budget)
        print(json.dumps(result, indent=2))

    elif args.command == "counter":
        dim = args.dimension or "protocol"
        result = engine.counter_strategy({"dimension": dim})
        print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
