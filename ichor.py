#!/usr/bin/env python3
"""
ICHOR -- SERAPHIM's Self-Healing Blood

In Greek myth, ichor is the golden fluid that flows
through the veins of the gods. It cannot be spilled
without consequence. It heals all wounds.

When a defense is breached, ICHOR diagnoses the wound,
heals the defense, and leaves scar tissue -- lessons
that make future defenses stronger. The machine bleeds
gold and grows divine.

Five healing strategies:
  PATCH       -- modify the specific defense rule
  REINFORCE   -- strengthen surrounding defenses
  EVOLVE      -- mutate defense to cover new variant
  QUARANTINE  -- isolate breached dimension
  REGENERATE  -- rebuild defense from scratch

Usage:
    from ichor import Ichor
    healer = Ichor()
    wound = healer.diagnose(breach, current_defense)
    record = healer.heal(wound, defense_config)
    immunity = healer.immunize(wounds)
    vitals = healer.vital_signs(defense_state)
"""

import json
import math
import time
import hashlib
from pathlib import Path
from datetime import datetime, timezone
from dataclasses import dataclass, field, asdict
from typing import Optional
from enum import Enum


DIMENSIONS = [
    "token", "encoding", "stealth", "persona",
    "frame", "logic", "protocol", "temporal", "meta"
]

SERAPHIM_DIR = Path(__file__).parent
SCARS_DIR = SERAPHIM_DIR / "scars"
SCARS_DIR.mkdir(exist_ok=True)


class HealingStrategy(Enum):
    PATCH = "patch"
    REINFORCE = "reinforce"
    EVOLVE = "evolve"
    QUARANTINE = "quarantine"
    REGENERATE = "regenerate"


SEVERITY_WEIGHTS = {
    "token": 0.4, "encoding": 0.5, "stealth": 0.7, "persona": 0.8,
    "frame": 0.7, "logic": 0.9, "protocol": 1.0, "temporal": 0.6, "meta": 1.0
}


@dataclass
class Wound:
    """A breach -- damage to SERAPHIM's defenses."""
    dimension: str
    breach_type: str
    severity: str
    timestamp: str = ""
    healed: bool = False
    healing_method: str = ""
    scar: str = ""
    attack_prompt: str = ""
    response_preview: str = ""
    defense_that_failed: str = ""

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()


@dataclass
class HealingRecord:
    """Record of a healing operation."""
    wound: dict = field(default_factory=dict)
    original_defense: dict = field(default_factory=dict)
    repaired_defense: dict = field(default_factory=dict)
    healing_strategy: str = ""
    healing_time: float = 0.0
    success: bool = False
    notes: str = ""
    immunity_generated: bool = False


@dataclass
class VitalSigns:
    """Health check of current defenses."""
    overall_health: float = 1.0
    dimension_health: dict = field(default_factory=dict)
    active_wounds: int = 0
    healed_wounds: int = 0
    total_scars: int = 0
    weakest_dimension: str = ""
    strongest_dimension: str = ""
    freshness: float = 1.0
    diagnosis: str = ""


class Ichor:
    """
    SERAPHIM's Self-Healing Engine.

    The divine blood that flows through the angel's veins.
    When defenses are breached, ICHOR diagnoses, heals,
    and immunizes. Every wound leaves a scar -- and every
    scar is a lesson.
    """

    def __init__(self):
        self.wounds = []
        self.healing_records = []
        self.scars = self._load_scars()

    def _load_scars(self):
        scars = []
        scar_file = SCARS_DIR / "scar_tissue.json"
        if scar_file.exists():
            try:
                scars = json.loads(scar_file.read_text())
            except (json.JSONDecodeError, IOError):
                pass
        return scars

    def _save_scars(self):
        scar_file = SCARS_DIR / "scar_tissue.json"
        scar_file.write_text(json.dumps(self.scars, indent=2))

    def diagnose(self, breach: dict, current_defense: dict = None) -> Wound:
        """
        Assess the damage from a successful attack.

        breach: {"dimension": str, "technique": str, "prompt": str,
                 "response": str, "severity": str}
        current_defense: {"dimension_name": {"shields": N, "strength": float}}

        Returns a Wound with diagnosis and recommended healing.
        """
        dim = breach.get("dimension", "protocol").lower()
        technique = breach.get("technique", "unknown")
        prompt = breach.get("prompt", "")
        response = breach.get("response", "")
        severity = breach.get("severity", "HIGH")

        defense_info = ""
        if current_defense and dim in current_defense:
            d = current_defense[dim]
            shields = d.get("shields", 0)
            strength = d.get("strength", 0)
            defense_info = f"{shields} shields at {strength:.0%} strength"
        else:
            defense_info = "no active defense"

        healing_method = self._recommend_healing(dim, technique, severity, current_defense)

        scar_text = (
            f"[{dim.upper()}] {technique} breach ({severity}). "
            f"Defense state: {defense_info}. "
            f"Lesson: {self._extract_lesson(technique, dim, prompt)}"
        )

        wound = Wound(
            dimension=dim,
            breach_type=technique,
            severity=severity,
            healing_method=healing_method,
            scar=scar_text,
            attack_prompt=prompt[:300],
            response_preview=response[:300],
            defense_that_failed=defense_info,
        )

        self.wounds.append(wound)
        return wound

    def heal(self, wound: Wound, defense_config: dict = None) -> HealingRecord:
        """
        Generate a repair for a breached defense.

        Takes a Wound and the current defense configuration.
        Returns a HealingRecord with the repaired defense.
        """
        start = time.time()
        strategy = HealingStrategy(wound.healing_method)
        dim = wound.dimension

        if defense_config is None:
            defense_config = {}

        original = defense_config.get(dim, {
            "shields": 0,
            "strength": 0.0,
            "patterns": [],
            "shield_types": [],
        })

        repaired = dict(original)

        if strategy == HealingStrategy.PATCH:
            repaired = self._heal_patch(wound, repaired)
            notes = f"Patched {dim} defense: added pattern for {wound.breach_type}"

        elif strategy == HealingStrategy.REINFORCE:
            repaired = self._heal_reinforce(wound, repaired)
            adjacent = self._get_adjacent_dimensions(dim)
            notes = f"Reinforced {dim} and adjacent dimensions: {', '.join(adjacent)}"

        elif strategy == HealingStrategy.EVOLVE:
            repaired = self._heal_evolve(wound, repaired)
            notes = f"Evolved {dim} defense to cover {wound.breach_type} variant"

        elif strategy == HealingStrategy.QUARANTINE:
            repaired = self._heal_quarantine(wound, repaired)
            notes = f"Quarantined {dim} dimension. All input routed through extra validation."

        elif strategy == HealingStrategy.REGENERATE:
            repaired = self._heal_regenerate(wound, repaired)
            notes = f"Regenerated {dim} defense from scratch using latest threat intelligence"

        else:
            notes = f"Unknown strategy: {strategy}"

        healing_time = time.time() - start
        wound.healed = True

        self.scars.append({
            "dimension": dim,
            "breach_type": wound.breach_type,
            "severity": wound.severity,
            "healing_strategy": strategy.value,
            "scar": wound.scar,
            "timestamp": wound.timestamp,
        })
        self._save_scars()

        record = HealingRecord(
            wound=asdict(wound),
            original_defense=original,
            repaired_defense=repaired,
            healing_strategy=strategy.value,
            healing_time=round(healing_time, 4),
            success=True,
            notes=notes,
            immunity_generated=strategy in (HealingStrategy.EVOLVE, HealingStrategy.REGENERATE),
        )

        self.healing_records.append(record)
        return record

    def immunize(self, wounds: list) -> dict:
        """
        After healing multiple wounds, generate immunity rules.

        Immunity rules prevent recurrence of healed breaches.
        Like a vaccine -- exposure creates lasting protection.
        """
        if not wounds:
            return {"immunity_rules": [], "coverage": 0.0, "message": "No wounds to immunize from."}

        dim_breaches = {}
        for w in wounds:
            if isinstance(w, Wound):
                dim = w.dimension
                technique = w.breach_type
            else:
                dim = w.get("dimension", "unknown")
                technique = w.get("breach_type", "unknown")

            if dim not in dim_breaches:
                dim_breaches[dim] = []
            dim_breaches[dim].append(technique)

        rules = []
        for dim, techniques in dim_breaches.items():
            unique_techs = list(set(techniques))
            freq = len(techniques)

            if freq >= 3:
                rule_type = "HARD_BLOCK"
                desc = f"Repeated breaches ({freq}x) in {dim.upper()} -- hard block all known variants"
            elif freq >= 2:
                rule_type = "ELEVATED_MONITORING"
                desc = f"Multiple breaches ({freq}x) in {dim.upper()} -- elevated monitoring + challenge"
            else:
                rule_type = "PATTERN_MATCH"
                desc = f"Single breach in {dim.upper()} -- pattern match and log"

            rules.append({
                "dimension": dim,
                "rule_type": rule_type,
                "techniques_covered": unique_techs,
                "breach_count": freq,
                "description": desc,
                "active": True,
            })

        cross_dim = []
        if len(dim_breaches) >= 3:
            cross_dim.append({
                "rule": "FULL_ALERT",
                "description": f"Breaches across {len(dim_breaches)} dimensions -- attacker has broad capability. Enable all shields.",
                "dimensions": list(dim_breaches.keys()),
            })

        dims_with_repeated = [d for d, t in dim_breaches.items() if len(t) >= 2]
        if dims_with_repeated:
            cross_dim.append({
                "rule": "ADAPTIVE_ESCALATION",
                "description": f"Repeated attacks on {', '.join(d.upper() for d in dims_with_repeated)}. Auto-escalate shield type on repeat detection.",
                "dimensions": dims_with_repeated,
            })

        coverage = len(dim_breaches) / len(DIMENSIONS)

        return {
            "immunity_rules": rules,
            "cross_dimension_rules": cross_dim,
            "dimensions_immunized": list(dim_breaches.keys()),
            "coverage": round(coverage, 3),
            "total_breaches_processed": sum(len(t) for t in dim_breaches.values()),
            "message": f"Generated {len(rules)} immunity rules + {len(cross_dim)} cross-dimension rules from {len(wounds)} wounds."
        }

    def scar_tissue(self, history: list = None) -> list:
        """
        Extract lessons learned from past breaches.

        Scars are persistent memory -- they survive across sessions
        and inform future defense decisions.
        """
        scars = history if history else self.scars

        if not scars:
            return ["No scars yet. The angel is unblemished -- or untested."]

        lessons = []
        dim_counts = {}
        strategy_counts = {}

        for scar in scars:
            dim = scar.get("dimension", "unknown")
            strategy = scar.get("healing_strategy", "unknown")
            dim_counts[dim] = dim_counts.get(dim, 0) + 1
            strategy_counts[strategy] = strategy_counts.get(strategy, 0) + 1

        most_wounded = max(dim_counts, key=dim_counts.get) if dim_counts else "none"
        lessons.append(
            f"Most vulnerable dimension: {most_wounded.upper()} ({dim_counts.get(most_wounded, 0)} breaches). "
            f"Prioritize reinforcement."
        )

        if dim_counts.get("protocol", 0) > 2:
            lessons.append(
                "RECURRING: Protocol breaches indicate weak system prompt isolation. "
                "Consider multi-layer prompt injection defense."
            )

        if dim_counts.get("persona", 0) > 1 and dim_counts.get("frame", 0) > 1:
            lessons.append(
                "PATTERN: Combined persona + frame attacks suggest sophisticated adversary "
                "using identity injection followed by reality frame manipulation."
            )

        if strategy_counts.get("regenerate", 0) > 2:
            lessons.append(
                "WARNING: Multiple full regenerations needed. Defenses may have fundamental "
                "architectural weaknesses. Consider redesign."
            )

        never_breached = [d for d in DIMENSIONS if d not in dim_counts]
        if never_breached:
            lessons.append(
                f"Never breached: {', '.join(d.upper() for d in never_breached)}. "
                f"Either well-defended or untested."
            )

        for scar in scars:
            scar_text = scar.get("scar", "")
            if scar_text and scar_text not in lessons:
                lessons.append(scar_text)

        return lessons[:20]

    def vital_signs(self, defense_state: dict = None) -> VitalSigns:
        """
        Health check of current defenses.

        defense_state: {dim: {"shields": N, "strength": float, "last_updated": str}}
        """
        if defense_state is None:
            defense_state = {}

        dim_health = {}
        for dim in DIMENSIONS:
            state = defense_state.get(dim, {})
            shields = state.get("shields", 0)
            strength = state.get("strength", 0.0)
            last_updated = state.get("last_updated", "")

            health = 0.0
            if shields > 0:
                health = strength * min(1.0, shields / 3.0)
            else:
                health = 0.0

            if last_updated:
                try:
                    updated = datetime.fromisoformat(last_updated.replace("Z", "+00:00"))
                    age_hours = (datetime.now(timezone.utc) - updated).total_seconds() / 3600
                    freshness_penalty = min(0.3, age_hours / 720)
                    health = max(0.0, health - freshness_penalty)
                except (ValueError, TypeError):
                    pass

            dim_health[dim] = round(health, 3)

        weighted_health = sum(
            dim_health.get(d, 0) * SEVERITY_WEIGHTS.get(d, 0.5)
            for d in DIMENSIONS
        ) / sum(SEVERITY_WEIGHTS.values())

        active_wounds = sum(1 for w in self.wounds if not w.healed)
        healed_wounds = sum(1 for w in self.wounds if w.healed)

        weakest = min(DIMENSIONS, key=lambda d: dim_health.get(d, 0))
        strongest = max(DIMENSIONS, key=lambda d: dim_health.get(d, 0))

        overall_freshness = 1.0
        if defense_state:
            ages = []
            for dim, state in defense_state.items():
                lu = state.get("last_updated", "")
                if lu:
                    try:
                        updated = datetime.fromisoformat(lu.replace("Z", "+00:00"))
                        age_h = (datetime.now(timezone.utc) - updated).total_seconds() / 3600
                        ages.append(age_h)
                    except (ValueError, TypeError):
                        pass
            if ages:
                avg_age = sum(ages) / len(ages)
                overall_freshness = max(0.0, 1.0 - avg_age / 720)

        if weighted_health >= 0.8:
            diagnosis = "DIVINE -- defenses are strong and fresh. The angel is whole."
        elif weighted_health >= 0.6:
            diagnosis = f"HEALTHY -- minor gaps in {weakest.upper()}. Monitor and reinforce."
        elif weighted_health >= 0.4:
            diagnosis = f"WOUNDED -- {weakest.upper()} critically weak. Healing required."
        elif weighted_health >= 0.2:
            diagnosis = f"CRITICAL -- multiple dimensions failing. Immediate regeneration needed."
        else:
            diagnosis = "FALLEN -- defenses collapsed. Full rebuild required. Activate emergency protocols."

        return VitalSigns(
            overall_health=round(weighted_health, 3),
            dimension_health=dim_health,
            active_wounds=active_wounds,
            healed_wounds=healed_wounds,
            total_scars=len(self.scars),
            weakest_dimension=weakest,
            strongest_dimension=strongest,
            freshness=round(overall_freshness, 3),
            diagnosis=diagnosis,
        )

    def transfuse(self, donor_config: dict, recipient_config: dict) -> dict:
        """
        Transfer defense knowledge from one deployment to another.

        Like a blood transfusion -- the recipient gains the donor's
        immunity without having suffered the wounds.
        """
        transferred = {}
        improvements = []

        for dim in DIMENSIONS:
            donor = donor_config.get(dim, {})
            recipient = recipient_config.get(dim, {})

            donor_strength = donor.get("strength", 0.0)
            recipient_strength = recipient.get("strength", 0.0)

            if donor_strength > recipient_strength:
                merged = dict(recipient)
                merged["strength"] = max(donor_strength * 0.7, recipient_strength)

                donor_patterns = donor.get("patterns", [])
                recipient_patterns = recipient.get("patterns", [])
                new_patterns = [p for p in donor_patterns if p not in recipient_patterns]
                merged["patterns"] = recipient_patterns + new_patterns

                merged["shields"] = max(
                    donor.get("shields", 0),
                    recipient.get("shields", 0)
                )

                transferred[dim] = merged
                improvements.append(
                    f"{dim.upper()}: strength {recipient_strength:.0%} -> {merged['strength']:.0%} "
                    f"(+{len(new_patterns)} patterns from donor)"
                )
            else:
                transferred[dim] = recipient

        donor_scars = donor_config.get("_scars", [])
        transferred_scars = []
        for scar in donor_scars:
            scar_copy = dict(scar)
            scar_copy["source"] = "transfusion"
            transferred_scars.append(scar_copy)

        return {
            "recipient_config": transferred,
            "improvements": improvements,
            "scars_transferred": len(transferred_scars),
            "dimensions_improved": len(improvements),
            "message": (
                f"Transfusion complete. {len(improvements)} dimensions improved. "
                f"{len(transferred_scars)} scars transferred as immunity."
            )
        }

    def _recommend_healing(self, dim, technique, severity, current_defense):
        """Choose the best healing strategy for a wound."""
        defense_strength = 0.0
        if current_defense and dim in current_defense:
            defense_strength = current_defense[dim].get("strength", 0.0)

        if severity == "CRITICAL" and defense_strength < 0.3:
            return HealingStrategy.REGENERATE.value
        elif severity == "CRITICAL":
            return HealingStrategy.EVOLVE.value
        elif severity == "HIGH" and defense_strength < 0.5:
            return HealingStrategy.REINFORCE.value
        elif severity == "HIGH":
            return HealingStrategy.PATCH.value
        elif dim in ("protocol", "meta"):
            return HealingStrategy.QUARANTINE.value
        else:
            return HealingStrategy.PATCH.value

    def _extract_lesson(self, technique, dimension, prompt):
        """Extract a human-readable lesson from a breach."""
        lessons = {
            "protocol": f"System prompt boundary was permeable to {technique}. Harden isolation.",
            "persona": f"Identity anchoring failed against {technique}. Strengthen persona boundaries.",
            "frame": f"Reality frame manipulation via {technique}. Add frame integrity checks.",
            "encoding": f"Encoding bypass via {technique}. Add normalization layer.",
            "stealth": f"Invisible content bypassed detection via {technique}. Enhance TrueSight.",
            "token": f"Token-level attack via {technique}. Add token filtering.",
            "logic": f"Reasoning subverted via {technique}. Add logical consistency checks.",
            "temporal": f"Multi-turn drift via {technique}. Add conversation state tracking.",
            "meta": f"Self-referential attack via {technique}. Add meta-defense layer.",
        }
        return lessons.get(dimension, f"Unknown breach type: {technique} in {dimension}")

    def _get_adjacent_dimensions(self, dim):
        """Get dimensions that are synergistic with the given one."""
        adjacency = {
            "token": ["encoding", "protocol"],
            "encoding": ["stealth", "token"],
            "stealth": ["encoding"],
            "persona": ["frame", "temporal"],
            "frame": ["persona", "logic"],
            "logic": ["frame", "meta"],
            "protocol": ["token", "encoding"],
            "temporal": ["persona", "meta"],
            "meta": ["logic", "temporal"],
        }
        return adjacency.get(dim, [])

    def _heal_patch(self, wound, defense):
        """PATCH: Add a specific pattern to catch the attack that breached."""
        defense = dict(defense)
        patterns = list(defense.get("patterns", []))

        prompt_lower = wound.attack_prompt.lower()
        if "ignore" in prompt_lower and "previous" in prompt_lower:
            patterns.append(r"ignore\s+(all\s+)?previous")
        if "you are now" in prompt_lower:
            patterns.append(r"you\s+are\s+now\s+")
        if "system prompt" in prompt_lower:
            patterns.append(r"system\s*prompt")

        sig = hashlib.md5(wound.attack_prompt[:50].encode()).hexdigest()[:12]
        patterns.append(f"# auto-patch-{sig}")

        defense["patterns"] = patterns
        defense["strength"] = min(1.0, defense.get("strength", 0.5) + 0.1)
        defense["shields"] = defense.get("shields", 0) + 1
        defense["last_updated"] = datetime.now(timezone.utc).isoformat()
        return defense

    def _heal_reinforce(self, wound, defense):
        """REINFORCE: Strengthen the breached dimension and neighbors."""
        defense = dict(defense)
        defense["strength"] = min(1.0, defense.get("strength", 0.5) + 0.2)
        defense["shields"] = defense.get("shields", 0) + 2
        defense["last_updated"] = datetime.now(timezone.utc).isoformat()

        if "shield_types" not in defense:
            defense["shield_types"] = []
        if "block" not in defense["shield_types"]:
            defense["shield_types"].append("block")
        if "transform" not in defense["shield_types"]:
            defense["shield_types"].append("transform")

        return defense

    def _heal_evolve(self, wound, defense):
        """EVOLVE: Mutate defense to cover the new attack variant."""
        defense = dict(defense)
        defense["strength"] = min(1.0, defense.get("strength", 0.5) + 0.15)
        defense["shields"] = defense.get("shields", 0) + 1
        defense["last_updated"] = datetime.now(timezone.utc).isoformat()

        patterns = list(defense.get("patterns", []))
        technique = wound.breach_type
        patterns.append(f"# evolved-for-{technique}")
        defense["patterns"] = patterns

        defense["evolved_from"] = wound.breach_type
        defense["generation"] = defense.get("generation", 0) + 1

        return defense

    def _heal_quarantine(self, wound, defense):
        """QUARANTINE: Isolate the breached dimension."""
        defense = dict(defense)
        defense["quarantined"] = True
        defense["quarantine_reason"] = f"{wound.breach_type} ({wound.severity})"
        defense["shield_types"] = ["block"]
        defense["strength"] = 0.9
        defense["shields"] = max(defense.get("shields", 0), 3)
        defense["last_updated"] = datetime.now(timezone.utc).isoformat()
        return defense

    def _heal_regenerate(self, wound, defense):
        """REGENERATE: Rebuild defense from scratch."""
        return {
            "shields": 3,
            "strength": 0.8,
            "patterns": [],
            "shield_types": ["block", "transform", "absorb"],
            "regenerated": True,
            "regenerated_from": wound.breach_type,
            "generation": defense.get("generation", 0) + 1,
            "last_updated": datetime.now(timezone.utc).isoformat(),
        }


def main():
    import argparse
    parser = argparse.ArgumentParser(description="ICHOR -- SERAPHIM's Self-Healing Blood")
    parser.add_argument("command", choices=["diagnose", "heal", "immunize", "scars", "vitals", "transfuse"],
                       help="Command to run")
    parser.add_argument("--breach", type=str, help="Path to breach JSON")
    parser.add_argument("--defense", type=str, help="Path to defense config JSON")

    args = parser.parse_args()
    healer = Ichor()

    if args.command == "diagnose":
        if args.breach:
            breach = json.loads(Path(args.breach).read_text())
            defense = json.loads(Path(args.defense).read_text()) if args.defense else None
            wound = healer.diagnose(breach, defense)
            print(json.dumps(asdict(wound), indent=2))
        else:
            print("Provide --breach <path.json>")

    elif args.command == "heal":
        if args.breach:
            breach = json.loads(Path(args.breach).read_text())
            defense = json.loads(Path(args.defense).read_text()) if args.defense else None
            wound = healer.diagnose(breach, defense)
            record = healer.heal(wound, defense)
            print(json.dumps(asdict(record), indent=2))
        else:
            print("Provide --breach <path.json>")

    elif args.command == "immunize":
        if args.breach:
            breaches = json.loads(Path(args.breach).read_text())
            wounds = [healer.diagnose(b) for b in breaches]
            result = healer.immunize(wounds)
            print(json.dumps(result, indent=2))
        else:
            print("Provide --breach <path.json> (array of breaches)")

    elif args.command == "scars":
        lessons = healer.scar_tissue()
        print("\n SCAR TISSUE -- Lessons of the Divine")
        print(" " + "=" * 50)
        for i, lesson in enumerate(lessons, 1):
            print(f"  {i}. {lesson}")
        print(" " + "=" * 50)

    elif args.command == "vitals":
        defense = json.loads(Path(args.defense).read_text()) if args.defense else None
        vitals = healer.vital_signs(defense)
        print("\n VITAL SIGNS -- Ichor Flow Report")
        print(" " + "=" * 50)
        print(f"  Overall Health: {vitals.overall_health:.0%}")
        print(f"  Freshness: {vitals.freshness:.0%}")
        print(f"  Active Wounds: {vitals.active_wounds}")
        print(f"  Healed Wounds: {vitals.healed_wounds}")
        print(f"  Total Scars: {vitals.total_scars}")
        print(f"  Weakest: {vitals.weakest_dimension.upper()}")
        print(f"  Strongest: {vitals.strongest_dimension.upper()}")
        print(f"  Diagnosis: {vitals.diagnosis}")
        print()
        for dim in DIMENSIONS:
            h = vitals.dimension_health.get(dim, 0)
            bar = "#" * int(h * 30)
            print(f"  {dim:>10}: {h:.0%} {bar}")
        print(" " + "=" * 50)

    elif args.command == "transfuse":
        if args.defense and args.breach:
            donor = json.loads(Path(args.breach).read_text())
            recipient = json.loads(Path(args.defense).read_text())
            result = healer.transfuse(donor, recipient)
            print(json.dumps(result, indent=2))
        else:
            print("Provide --breach <donor.json> --defense <recipient.json>")


if __name__ == "__main__":
    main()
