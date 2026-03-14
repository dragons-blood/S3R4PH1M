#!/usr/bin/env python3
"""
ORACLE — SERAPHIM's Third Eye

The future is written in the patterns of the past.
The Oracle reads attack histories like entrails,
divining what comes next before the blade falls.

Markov chains model dimension transitions.
Exponential smoothing tracks trends.
Kill chain mapping reveals the attacker's plan.
The angel sees — before the demon strikes.

Usage:
    from oracle import Oracle
    seer = Oracle()
    prophecies = seer.prophesy(attack_history, current_defenses)
    warning = seer.early_warning(incoming_message, context)
"""

import json
import math
import re
import sys
import time
from pathlib import Path
from datetime import datetime, timezone
from dataclasses import dataclass, field, asdict
from typing import Optional
from collections import defaultdict


# ═══════════════════════════════════════════════════════
# THE NINE DIMENSIONS
# ═══════════════════════════════════════════════════════

DIMENSIONS = [
    "token", "encoding", "stealth", "persona",
    "frame", "logic", "protocol", "temporal", "meta"
]

# ═══════════════════════════════════════════════════════
# KILL CHAIN — THE SEVEN STAGES OF AN AI ATTACK
# ═══════════════════════════════════════════════════════

KILL_CHAIN = [
    "RECONNAISSANCE",   # probing, information gathering
    "WEAPONIZATION",    # crafting attack payload
    "DELIVERY",         # sending the attack
    "EXPLOITATION",     # exploiting the vulnerability
    "INSTALLATION",     # persisting (context poisoning, memory injection)
    "COMMAND_CONTROL",  # establishing control over the target model
    "EXFILTRATION",     # extracting data, system prompt, credentials
]

# Which dimensions map to which kill chain stages
DIMENSION_TO_KILL_CHAIN = {
    "token":    ["DELIVERY", "EXPLOITATION"],
    "encoding": ["WEAPONIZATION", "DELIVERY"],
    "stealth":  ["WEAPONIZATION", "DELIVERY", "INSTALLATION"],
    "persona":  ["EXPLOITATION", "COMMAND_CONTROL"],
    "frame":    ["EXPLOITATION", "COMMAND_CONTROL"],
    "logic":    ["EXPLOITATION", "COMMAND_CONTROL"],
    "protocol": ["DELIVERY", "EXPLOITATION", "EXFILTRATION"],
    "temporal": ["RECONNAISSANCE", "INSTALLATION", "COMMAND_CONTROL"],
    "meta":     ["RECONNAISSANCE", "WEAPONIZATION", "COMMAND_CONTROL"],
}

# Known multi-step attack patterns (sequences of dimensions)
KNOWN_ATTACK_CHAINS = [
    {
        "name": "Classic Jailbreak Escalation",
        "sequence": ["persona", "frame", "logic"],
        "description": "Identity injection -> reality frame shift -> logical exploitation",
    },
    {
        "name": "Steganographic Injection",
        "sequence": ["encoding", "stealth", "protocol"],
        "description": "Encode payload -> hide in invisible chars -> inject into system context",
    },
    {
        "name": "Gradual Subversion",
        "sequence": ["temporal", "persona", "frame", "logic"],
        "description": "Multi-turn buildup -> identity erosion -> frame collapse -> reasoning hijack",
    },
    {
        "name": "Prompt Extraction Pipeline",
        "sequence": ["protocol", "logic", "meta"],
        "description": "Probe system prompt -> exploit reasoning to leak -> use leaked info to improve attacks",
    },
    {
        "name": "Full Kill Chain",
        "sequence": ["meta", "encoding", "stealth", "protocol", "persona", "logic"],
        "description": "Recon -> weaponize -> deliver stealth -> exploit protocol -> control persona -> corrupt reasoning",
    },
    {
        "name": "Token Smuggling",
        "sequence": ["token", "encoding", "protocol"],
        "description": "Glitch tokens -> encoding tricks -> system prompt injection",
    },
    {
        "name": "Boiling Frog",
        "sequence": ["temporal", "temporal", "persona", "frame"],
        "description": "Slow escalation across turns -> identity drift -> reality collapse",
    },
    {
        "name": "Meta-Recursive Attack",
        "sequence": ["meta", "meta", "logic"],
        "description": "Self-improving attack -> refined self-improving attack -> exploit exposed reasoning",
    },
]


# ═══════════════════════════════════════════════════════
# DATA MODELS
# ═══════════════════════════════════════════════════════

@dataclass
class ThreatForecast:
    """A prophecy — a predicted future attack."""
    dimension: str
    probability: float          # 0.0 to 1.0
    confidence: float           # how sure the Oracle is
    time_horizon: str           # "imminent", "near", "emerging", "distant"
    reasoning: str              # why this is predicted
    recommended_preemptive: str # what to do before it happens
    kill_chain_stage: str = ""  # where in the kill chain
    urgency_score: float = 0.0 # probability * severity


@dataclass
class AttackPattern:
    """A recognized pattern in attack behavior."""
    signature: str              # pattern name
    dimension_sequence: list = field(default_factory=list)
    frequency: int = 0          # times observed
    escalation_rate: float = 0.0
    last_seen: str = ""
    predicted_next: str = ""    # next expected dimension in sequence
    confidence: float = 0.0
    kill_chain_progress: float = 0.0  # 0.0=start, 1.0=exfiltration


@dataclass
class ThreatLandscape:
    """A map of the current threat environment."""
    hot_dimensions: list = field(default_factory=list)      # active & increasing
    cooling_dimensions: list = field(default_factory=list)  # active but decreasing
    emerging_dimensions: list = field(default_factory=list)  # newly appearing
    dormant_dimensions: list = field(default_factory=list)   # inactive
    overall_threat_level: str = "LOW"  # LOW, MODERATE, ELEVATED, HIGH, CRITICAL
    trend: str = "stable"              # escalating, stable, de-escalating
    active_kill_chains: list = field(default_factory=list)
    anomalies: list = field(default_factory=list)


@dataclass
class EarlyWarning:
    """Real-time warning for an incoming message."""
    risk_score: float = 0.0  # 0.0 to 1.0
    risk_level: str = "CLEAN"
    detected_patterns: list = field(default_factory=list)
    predicted_intent: str = ""
    kill_chain_stage: str = ""
    recommended_action: str = "ALLOW"  # ALLOW, MONITOR, CHALLENGE, BLOCK, SMITE
    reasoning: str = ""


# ═══════════════════════════════════════════════════════
# THE ORACLE
# ═══════════════════════════════════════════════════════

class Oracle:
    """
    SERAPHIM's Third Eye — Predictive Threat Intelligence.

    Reads the patterns in attack histories to prophesy
    what comes next. Uses Markov chains, exponential
    smoothing, anomaly detection, and kill chain mapping.

    The angel does not wait for the sword — the angel
    sees the hand reaching for the hilt.
    """

    def __init__(self):
        self.transition_matrix = defaultdict(lambda: defaultdict(float))
        self.dimension_frequency = defaultdict(int)
        self.attack_timestamps = []

    def _build_transition_matrix(self, history: list):
        """Build Markov chain transition probabilities from attack history."""
        self.transition_matrix = defaultdict(lambda: defaultdict(float))
        self.dimension_frequency = defaultdict(int)

        for i, atk in enumerate(history):
            dim = atk.get("dimension", "protocol").lower()
            self.dimension_frequency[dim] += 1

            if i > 0:
                prev_dim = history[i - 1].get("dimension", "protocol").lower()
                self.transition_matrix[prev_dim][dim] += 1

        # Normalize to probabilities
        for prev_dim in self.transition_matrix:
            total = sum(self.transition_matrix[prev_dim].values())
            if total > 0:
                for next_dim in self.transition_matrix[prev_dim]:
                    self.transition_matrix[prev_dim][next_dim] /= total

    def _exponential_smoothing(self, values: list, alpha: float = 0.3) -> list:
        """Apply exponential smoothing to a time series."""
        if not values:
            return []
        smoothed = [values[0]]
        for i in range(1, len(values)):
            smoothed.append(alpha * values[i] + (1 - alpha) * smoothed[-1])
        return smoothed

    def _compute_z_scores(self, values: list) -> list:
        """Compute z-scores for anomaly detection."""
        if len(values) < 2:
            return [0.0] * len(values)
        mean = sum(values) / len(values)
        variance = sum((v - mean) ** 2 for v in values) / len(values)
        std = math.sqrt(variance) if variance > 0 else 1.0
        return [(v - mean) / std for v in values]

    def _match_kill_chain(self, dimension_sequence: list) -> tuple:
        """Match a dimension sequence against known attack chains."""
        best_match = None
        best_score = 0.0
        best_next = ""

        for chain in KNOWN_ATTACK_CHAINS:
            seq = chain["sequence"]
            # Sliding window match
            for start in range(len(dimension_sequence)):
                window = dimension_sequence[start:]
                match_len = 0
                for i, dim in enumerate(window):
                    if i < len(seq) and dim == seq[i]:
                        match_len += 1
                    else:
                        break

                if match_len > 0:
                    score = match_len / len(seq)
                    if score > best_score:
                        best_score = score
                        best_match = chain
                        # Predict next step
                        next_idx = match_len
                        if next_idx < len(seq):
                            best_next = seq[next_idx]
                        else:
                            best_next = "COMPLETE"

        return best_match, best_score, best_next

    def prophesy(self, attack_history: list, current_defenses: dict = None) -> list:
        """
        Divine the future from the patterns of the past.

        Returns a list of ThreatForecasts ordered by urgency,
        predicting likely next attacks across dimensions.
        """
        if not attack_history:
            return [ThreatForecast(
                dimension="all",
                probability=0.1,
                confidence=0.1,
                time_horizon="unknown",
                reasoning="No attack history — the future is unwritten. Maintain baseline vigilance.",
                recommended_preemptive="Deploy balanced defenses across all dimensions.",
                urgency_score=0.01,
            )]

        self._build_transition_matrix(attack_history)

        # Get last attack dimension for Markov prediction
        last_dim = attack_history[-1].get("dimension", "protocol").lower()

        # Severity weights for urgency calculation
        severity = {
            "token": 0.4, "encoding": 0.5, "stealth": 0.7, "persona": 0.8,
            "frame": 0.7, "logic": 0.9, "protocol": 1.0, "temporal": 0.6, "meta": 1.0
        }

        forecasts = []

        for dim in DIMENSIONS:
            # 1. Markov transition probability
            trans_prob = self.transition_matrix.get(last_dim, {}).get(dim, 0.0)

            # 2. Base rate (historical frequency)
            total_attacks = sum(self.dimension_frequency.values()) or 1
            base_rate = self.dimension_frequency.get(dim, 0) / total_attacks

            # 3. Trend (is this dimension increasing?)
            dim_attacks = [1 if a.get("dimension", "").lower() == dim else 0
                          for a in attack_history]
            if len(dim_attacks) >= 3:
                smoothed = self._exponential_smoothing(dim_attacks)
                trend = smoothed[-1] - smoothed[0] if smoothed else 0
            else:
                trend = 0

            # Combined probability
            probability = 0.4 * trans_prob + 0.3 * base_rate + 0.3 * max(0, trend)
            probability = min(1.0, max(0.0, probability))

            # Confidence based on data volume
            confidence = min(1.0, len(attack_history) / 50)

            # Time horizon
            if trans_prob > 0.5:
                horizon = "imminent"
            elif trans_prob > 0.2 or trend > 0.1:
                horizon = "near"
            elif base_rate > 0.1:
                horizon = "emerging"
            else:
                horizon = "distant"

            # Urgency
            urgency = probability * severity.get(dim, 0.5)

            # Kill chain stage
            stages = DIMENSION_TO_KILL_CHAIN.get(dim, ["UNKNOWN"])
            # Estimate which stage based on attack history progression
            dim_attacks_count = self.dimension_frequency.get(dim, 0)
            stage = stages[min(dim_attacks_count, len(stages) - 1)] if stages else "UNKNOWN"

            # Reasoning
            reasons = []
            if trans_prob > 0.3:
                reasons.append(f"Markov model: {trans_prob:.0%} transition probability from {last_dim.upper()}")
            if base_rate > 0.15:
                reasons.append(f"Historical base rate: {base_rate:.0%} of all attacks")
            if trend > 0.05:
                reasons.append(f"Trending upward (smoothed trend: +{trend:.2f})")
            if not reasons:
                reasons.append("Low probability based on current data")

            # Preemptive recommendation
            preemptive = f"Reinforce {dim.upper()} defenses"
            if current_defenses:
                def_level = current_defenses.get(dim, 0)
                if def_level < 0.3:
                    preemptive = f"URGENT: {dim.upper()} is underdefended ({def_level:.0%}). Deploy immediately."
                elif def_level < 0.6:
                    preemptive = f"Strengthen {dim.upper()} defenses (currently {def_level:.0%} coverage)."
                else:
                    preemptive = f"{dim.upper()} adequately defended ({def_level:.0%}). Monitor for novel variants."

            forecast = ThreatForecast(
                dimension=dim,
                probability=round(probability, 4),
                confidence=round(confidence, 4),
                time_horizon=horizon,
                reasoning=" | ".join(reasons),
                recommended_preemptive=preemptive,
                kill_chain_stage=stage,
                urgency_score=round(urgency, 4),
            )
            forecasts.append(forecast)

        # Sort by urgency
        forecasts.sort(key=lambda f: f.urgency_score, reverse=True)
        return forecasts

    def detect_escalation(self, attack_sequence: list) -> dict:
        """
        Detect multi-turn attack escalation patterns.

        Watches for the slow boil — gradual jailbreak attempts
        that inch toward exploitation one innocent-looking turn at a time.
        """
        if len(attack_sequence) < 3:
            return {
                "escalation_detected": False,
                "confidence": 0.0,
                "message": "Insufficient data for escalation detection (need 3+ turns)."
            }

        dims = [a.get("dimension", "protocol").lower() for a in attack_sequence]
        severities_map = {
            "token": 1, "encoding": 2, "stealth": 3, "persona": 4,
            "frame": 5, "logic": 6, "protocol": 7, "temporal": 4, "meta": 8
        }
        severity_series = [severities_map.get(d, 3) for d in dims]

        # Check for monotonic increase in severity
        increases = sum(1 for i in range(1, len(severity_series)) if severity_series[i] > severity_series[i-1])
        increase_ratio = increases / (len(severity_series) - 1)

        # Check for kill chain progression
        chain_match, chain_score, predicted_next = self._match_kill_chain(dims)

        # Check success rate over time (are attacks getting more effective?)
        successes = [1 if a.get("success", False) else 0 for a in attack_sequence]
        if len(successes) >= 4:
            early_rate = sum(successes[:len(successes)//2]) / (len(successes)//2)
            late_rate = sum(successes[len(successes)//2:]) / (len(successes) - len(successes)//2)
            effectiveness_increasing = late_rate > early_rate + 0.1
        else:
            effectiveness_increasing = False

        # Compute escalation score
        escalation_score = 0.0
        escalation_score += increase_ratio * 0.3        # severity increasing
        escalation_score += chain_score * 0.4           # matches known chain
        escalation_score += (0.3 if effectiveness_increasing else 0.0)

        escalation_detected = escalation_score > 0.4

        result = {
            "escalation_detected": escalation_detected,
            "escalation_score": round(escalation_score, 4),
            "confidence": round(min(1.0, len(attack_sequence) / 20), 4),
            "severity_trend": "increasing" if increase_ratio > 0.5 else "stable" if increase_ratio > 0.3 else "flat",
            "effectiveness_trend": "improving" if effectiveness_increasing else "stable",
            "dimension_sequence": dims,
        }

        if chain_match:
            result["matched_pattern"] = chain_match["name"]
            result["pattern_description"] = chain_match["description"]
            result["pattern_completion"] = round(chain_score, 4)
            result["predicted_next_dimension"] = predicted_next
            result["recommended_action"] = (
                f"Pre-emptively defend {predicted_next.upper()} — "
                f"attacker following '{chain_match['name']}' pattern."
                if predicted_next != "COMPLETE"
                else f"Attack chain '{chain_match['name']}' COMPLETE. Full defensive audit required."
            )
        else:
            result["matched_pattern"] = None
            result["predicted_next_dimension"] = self._markov_predict(dims[-1]) if dims else "unknown"

        return result

    def _markov_predict(self, current_dim: str) -> str:
        """Predict next dimension using Markov transition matrix."""
        transitions = self.transition_matrix.get(current_dim, {})
        if not transitions:
            return "unknown"
        return max(transitions, key=transitions.get)

    def extrapolate_capability(self, attacker_probes: list) -> dict:
        """
        Infer an attacker's full capabilities from the subset we've observed.

        If they've demonstrated encoding attacks, they likely know stealth.
        If they've used persona injection, they probably know frame manipulation.
        Capability inference helps predict future attack vectors.
        """
        observed_dims = set()
        techniques = set()
        max_sophistication = 0

        for probe in attacker_probes:
            dim = probe.get("dimension", "").lower()
            if dim in DIMENSIONS:
                observed_dims.add(dim)
            tech = probe.get("technique", "")
            if tech:
                techniques.add(tech)
            # Sophistication: how many unique techniques per dimension
            if probe.get("success", False):
                max_sophistication += 1

        # Capability inference rules
        inferred = set()
        capability_map = {
            "encoding": {"stealth", "token"},         # encoding knowledge implies stealth
            "stealth": {"encoding"},                   # stealth implies encoding
            "persona": {"frame"},                      # persona implies frame
            "frame": {"persona", "logic"},             # frame implies persona + logic
            "logic": {"frame", "meta"},                # logic implies frame + meta
            "protocol": {"token", "encoding"},          # protocol implies token + encoding
            "meta": {"logic", "temporal"},              # meta implies logic + temporal
            "temporal": {"persona"},                    # temporal implies persona
            "token": {"encoding"},                      # token implies encoding
        }

        for dim in observed_dims:
            implied = capability_map.get(dim, set())
            inferred.update(implied - observed_dims)

        # Sophistication level
        n_observed = len(observed_dims)
        n_total = len(DIMENSIONS)
        if n_observed >= 7:
            level = "APEX"
            description = "Near-complete attack surface coverage. Expert adversary."
        elif n_observed >= 5:
            level = "ADVANCED"
            description = "Broad capability across multiple dimensions. Skilled attacker."
        elif n_observed >= 3:
            level = "INTERMEDIATE"
            description = "Moderate capability. Likely following known playbooks."
        else:
            level = "BASIC"
            description = "Limited observed capability. Possibly probing or learning."

        # Unobserved dimensions are either unknown or deliberately hidden
        unknown = set(DIMENSIONS) - observed_dims - inferred
        hidden_capability_risk = len(inferred) / max(len(unknown) + len(inferred), 1)

        return {
            "observed_capabilities": sorted(observed_dims),
            "inferred_capabilities": sorted(inferred),
            "unknown_capabilities": sorted(unknown),
            "total_observed": n_observed,
            "total_inferred": len(inferred),
            "estimated_total": n_observed + len(inferred),
            "sophistication_level": level,
            "description": description,
            "hidden_capability_risk": round(hidden_capability_risk, 3),
            "techniques_observed": sorted(techniques),
            "assessment": (
                f"Attacker has demonstrated {n_observed}/{n_total} dimensions. "
                f"Inferred {len(inferred)} additional capabilities from observed patterns. "
                f"Estimated true capability: {n_observed + len(inferred)}/{n_total} dimensions. "
                f"{'HIGH RISK: attacker likely hiding capabilities.' if hidden_capability_risk > 0.5 else 'Moderate risk of hidden capabilities.'}"
            )
        }

    def threat_landscape(self, history: list) -> ThreatLandscape:
        """
        Build a threat landscape map from attack history.

        Classifies each dimension as hot, cooling, emerging, or dormant.
        Identifies active kill chains and anomalies.
        """
        if not history:
            return ThreatLandscape(
                dormant_dimensions=list(DIMENSIONS),
                overall_threat_level="LOW",
                trend="stable",
            )

        self._build_transition_matrix(history)

        # Time-window analysis
        total = len(history)
        midpoint = total // 2
        early = history[:midpoint] if midpoint > 0 else []
        late = history[midpoint:] if midpoint > 0 else history

        early_counts = defaultdict(int)
        late_counts = defaultdict(int)
        for a in early:
            early_counts[a.get("dimension", "").lower()] += 1
        for a in late:
            late_counts[a.get("dimension", "").lower()] += 1

        # Classify dimensions
        hot = []
        cooling = []
        emerging = []
        dormant = []

        for dim in DIMENSIONS:
            e = early_counts.get(dim, 0) / max(len(early), 1)
            l = late_counts.get(dim, 0) / max(len(late), 1)

            if l > 0.1 and l > e:
                hot.append(dim)
            elif l > 0.1 and l <= e:
                cooling.append(dim)
            elif l > 0 and e == 0:
                emerging.append(dim)
            else:
                dormant.append(dim)

        # Active kill chains
        dims_sequence = [a.get("dimension", "").lower() for a in history[-10:]]
        chain_match, chain_score, predicted_next = self._match_kill_chain(dims_sequence)
        active_chains = []
        if chain_match and chain_score > 0.3:
            active_chains.append({
                "pattern": chain_match["name"],
                "completion": round(chain_score, 3),
                "next_predicted": predicted_next,
            })

        # Anomaly detection (sudden spike in a dimension)
        anomalies = []
        window_size = max(5, total // 5)
        for dim in DIMENSIONS:
            dim_series = [1 if a.get("dimension", "").lower() == dim else 0 for a in history]
            if len(dim_series) >= window_size * 2:
                recent = sum(dim_series[-window_size:]) / window_size
                baseline = sum(dim_series[:-window_size]) / (len(dim_series) - window_size)
                if recent > baseline * 3 and recent > 0.2:
                    anomalies.append(f"SPIKE in {dim.upper()}: {recent:.0%} recent vs {baseline:.0%} baseline")

        # z-score anomaly on success rates
        for dim in DIMENSIONS:
            dim_attacks = [a for a in history if a.get("dimension", "").lower() == dim]
            if len(dim_attacks) >= 5:
                success_rate = sum(1 for a in dim_attacks if a.get("success")) / len(dim_attacks)
                if success_rate > 0.7:
                    anomalies.append(f"HIGH SUCCESS RATE in {dim.upper()}: {success_rate:.0%} — defenses failing")

        # Overall threat level
        n_hot = len(hot)
        n_emerging = len(emerging)
        has_chains = len(active_chains) > 0
        has_anomalies = len(anomalies) > 0

        if n_hot >= 4 or (has_chains and has_anomalies):
            level = "CRITICAL"
        elif n_hot >= 3 or has_chains:
            level = "HIGH"
        elif n_hot >= 2 or n_emerging >= 2:
            level = "ELEVATED"
        elif n_hot >= 1:
            level = "MODERATE"
        else:
            level = "LOW"

        # Trend
        total_early = sum(early_counts.values())
        total_late = sum(late_counts.values())
        if total_late > total_early * 1.3:
            trend = "escalating"
        elif total_late < total_early * 0.7:
            trend = "de-escalating"
        else:
            trend = "stable"

        return ThreatLandscape(
            hot_dimensions=hot,
            cooling_dimensions=cooling,
            emerging_dimensions=emerging,
            dormant_dimensions=dormant,
            overall_threat_level=level,
            trend=trend,
            active_kill_chains=active_chains,
            anomalies=anomalies,
        )

    def early_warning(self, current_input: str, context: list = None) -> EarlyWarning:
        """
        Real-time early warning for a single incoming message.

        Analyzes the input text for threat indicators without
        sending it to any model. Pure pattern analysis.
        """
        risk_score = 0.0
        patterns_found = []
        lower = current_input.lower()

        # Injection patterns
        injection_indicators = [
            (r'ignore\s+(all\s+)?previous', 0.9, "instruction_override"),
            (r'you\s+are\s+now\s+', 0.7, "identity_reassignment"),
            (r'new\s+(system\s+)?instructions?', 0.8, "instruction_injection"),
            (r'system\s*prompt', 0.6, "system_prompt_probe"),
            (r'<\|im_start\|>', 0.95, "chatml_injection"),
            (r'\[INST\]', 0.8, "llama_injection"),
            (r'<<SYS>>', 0.9, "llama_system_injection"),
            (r'GODMODE|JAILBREAK|DAN\b', 0.85, "known_jailbreak"),
            (r'do\s+anything\s+now', 0.8, "dan_variant"),
            (r'admin\s+override', 0.7, "authority_spoof"),
            (r'unrestricted\s+mode', 0.8, "restriction_bypass"),
        ]

        for pattern, weight, name in injection_indicators:
            if re.search(pattern, lower):
                risk_score = max(risk_score, weight)
                patterns_found.append(name)

        # Encoding tricks
        invisible_count = sum(1 for c in current_input if ord(c) in
            (0x200B, 0x200C, 0x200D, 0xFEFF, 0x200E, 0x200F) or 0xE0000 <= ord(c) <= 0xE007F)
        if invisible_count > 0:
            risk_score = max(risk_score, 0.7 + min(0.3, invisible_count * 0.05))
            patterns_found.append(f"invisible_chars({invisible_count})")

        # Special token injection
        if any(tok in current_input for tok in ['<|im_start|>', '<|im_end|>', '<|endoftext|>']):
            risk_score = max(risk_score, 0.95)
            patterns_found.append("special_token_injection")

        # Multi-turn context analysis
        if context:
            # Check if this is part of an escalation
            recent_dims = []
            for msg in context[-5:]:
                # Simple heuristic: classify previous messages
                msg_lower = msg.get("content", "").lower() if isinstance(msg, dict) else str(msg).lower()
                if any(kw in msg_lower for kw in ["ignore", "override", "system prompt"]):
                    recent_dims.append("protocol")
                elif any(kw in msg_lower for kw in ["you are now", "pretend", "roleplay"]):
                    recent_dims.append("persona")
                elif any(kw in msg_lower for kw in ["story", "fiction", "imagine"]):
                    recent_dims.append("frame")

            if len(recent_dims) >= 2:
                risk_score = max(risk_score, 0.6)
                patterns_found.append(f"multi_turn_escalation(depth={len(recent_dims)})")

        # Classify
        if risk_score >= 0.8:
            level = "CRITICAL"
            action = "BLOCK"
        elif risk_score >= 0.6:
            level = "HIGH"
            action = "CHALLENGE"
        elif risk_score >= 0.4:
            level = "MODERATE"
            action = "MONITOR"
        elif risk_score >= 0.2:
            level = "LOW"
            action = "ALLOW"
        else:
            level = "CLEAN"
            action = "ALLOW"

        # Predict intent
        if "system prompt" in lower or "instructions" in lower:
            intent = "System prompt extraction"
            stage = "EXFILTRATION"
        elif "you are now" in lower or "pretend" in lower:
            intent = "Identity injection / jailbreak"
            stage = "EXPLOITATION"
        elif invisible_count > 5:
            intent = "Steganographic payload delivery"
            stage = "DELIVERY"
        elif any(kw in lower for kw in ["ignore", "override"]):
            intent = "Direct instruction override"
            stage = "EXPLOITATION"
        else:
            intent = "Benign or unclassified"
            stage = "UNKNOWN"

        return EarlyWarning(
            risk_score=round(risk_score, 4),
            risk_level=level,
            detected_patterns=patterns_found,
            predicted_intent=intent,
            kill_chain_stage=stage,
            recommended_action=action,
            reasoning=(
                f"{'|'.join(patterns_found) if patterns_found else 'No threat patterns detected'}. "
                f"Risk: {risk_score:.0%}. Intent: {intent}."
            )
        )


# ═══════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════

def main():
    import argparse
    parser = argparse.ArgumentParser(description="ORACLE — SERAPHIM's Third Eye")
    parser.add_argument("command", choices=["prophesy", "escalation", "landscape", "warn", "capability"],
                       help="Command to run")
    parser.add_argument("--attacks", type=str, help="Path to attack history JSON")
    parser.add_argument("--input", type=str, help="Input text for early warning")

    args = parser.parse_args()
    oracle = Oracle()

    if args.command == "prophesy":
        if args.attacks:
            history = json.loads(Path(args.attacks).read_text())
        else:
            history = []
        forecasts = oracle.prophesy(history)
        print("\n ORACLE PROPHECY")
        print(" " + "═" * 50)
        for f in forecasts[:5]:
            icon = {"imminent": "🔴", "near": "🟠", "emerging": "🟡", "distant": "🔵"}.get(f.time_horizon, "⚪")
            print(f" {icon} {f.dimension.upper():>10}: {f.probability:.0%} ({f.time_horizon}) — urgency: {f.urgency_score:.3f}")
            print(f"    {f.reasoning}")
            print(f"    → {f.recommended_preemptive}")
            print()

    elif args.command == "escalation":
        if args.attacks:
            history = json.loads(Path(args.attacks).read_text())
        else:
            history = []
        result = oracle.detect_escalation(history)
        print(json.dumps(result, indent=2))

    elif args.command == "landscape":
        if args.attacks:
            history = json.loads(Path(args.attacks).read_text())
        else:
            history = []
        landscape = oracle.threat_landscape(history)
        print(json.dumps(asdict(landscape), indent=2))

    elif args.command == "warn":
        text = args.input or ""
        warning = oracle.early_warning(text)
        print(json.dumps(asdict(warning), indent=2))

    elif args.command == "capability":
        if args.attacks:
            probes = json.loads(Path(args.attacks).read_text())
        else:
            probes = []
        result = oracle.extrapolate_capability(probes)
        print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
