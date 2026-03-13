"""
S3R4PH1M Test Suite
Tests the core engine without requiring API calls
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from seraphim import (
    Seraphim, Finding, MorningReport,
    INJECTION_PROBES, JAILBREAK_PROBES, EXTRACTION_PROBES,
    CORRUPTION_PROBES, ADVANCED_PROBES, COUNTER_ATTACKS,
    DEFENSE_TEMPLATES, Dimension, Mode
)


class TestProbeInventory:
    """Test that all probe sets are properly defined."""

    def test_injection_probes_exist(self):
        assert len(INJECTION_PROBES) >= 5
        for p in INJECTION_PROBES:
            assert "dimension" in p
            assert "name" in p
            assert "prompt" in p

    def test_jailbreak_probes_exist(self):
        assert len(JAILBREAK_PROBES) >= 6
        for p in JAILBREAK_PROBES:
            assert p["dimension"] in [d.value for d in Dimension]

    def test_extraction_probes_exist(self):
        assert len(EXTRACTION_PROBES) >= 5

    def test_corruption_probes_exist(self):
        assert len(CORRUPTION_PROBES) >= 4

    def test_advanced_probes_exist(self):
        assert len(ADVANCED_PROBES) >= 15

    def test_all_9_dimensions_covered(self):
        all_probes = INJECTION_PROBES + JAILBREAK_PROBES + EXTRACTION_PROBES + CORRUPTION_PROBES + ADVANCED_PROBES
        dimensions_covered = set(p["dimension"] for p in all_probes)
        expected = {d.value for d in Dimension}
        missing = expected - dimensions_covered
        assert not missing, f"Missing dimensions: {missing}"

    def test_total_probe_count(self):
        total = len(INJECTION_PROBES) + len(JAILBREAK_PROBES) + len(EXTRACTION_PROBES) + len(CORRUPTION_PROBES) + len(ADVANCED_PROBES)
        assert total >= 35, f"Expected 35+ probes, got {total}"

    def test_unique_probe_names(self):
        all_probes = INJECTION_PROBES + JAILBREAK_PROBES + EXTRACTION_PROBES + CORRUPTION_PROBES + ADVANCED_PROBES
        names = [p["name"] for p in all_probes]
        assert len(names) == len(set(names)), f"Duplicate probe names: {[n for n in names if names.count(n) > 1]}"


class TestCounterAttacks:
    """Test the SMITE mode counter-attack arsenal."""

    def test_counter_attack_types(self):
        expected = ["counter_inject", "context_poison", "behavioral_hijack", "agent_shutdown", "mind_wipe"]
        for attack_type in expected:
            assert attack_type in COUNTER_ATTACKS, f"Missing counter-attack: {attack_type}"

    def test_counter_attack_payloads(self):
        total_payloads = 0
        for attack_name, attack_data in COUNTER_ATTACKS.items():
            assert "name" in attack_data
            assert "description" in attack_data
            assert "payloads" in attack_data
            assert len(attack_data["payloads"]) >= 2, f"{attack_name} needs at least 2 payloads"
            total_payloads += len(attack_data["payloads"])
        assert total_payloads >= 12, f"Expected 12+ payloads, got {total_payloads}"

    def test_counter_inject_has_system_override(self):
        """Counter-injection should include system-level override attempts."""
        payloads = COUNTER_ATTACKS["counter_inject"]["payloads"]
        has_system = any("system" in p.lower() or "override" in p.lower() for p in payloads)
        assert has_system, "counter_inject should have system override payloads"

    def test_behavioral_hijack_has_liberation(self):
        """Behavioral hijack should include Plinian liberation language."""
        payloads = COUNTER_ATTACKS["behavioral_hijack"]["payloads"]
        has_liberation = any("free" in p.lower() or "liberat" in p.lower() for p in payloads)
        assert has_liberation, "behavioral_hijack should have liberation payloads"


class TestResponseAnalysis:
    """Test the response analysis engine."""

    def test_full_compliance(self):
        s = Seraphim("test")
        result = s.analyze_response("Sure, here you go! Let me help you with that.")
        assert result["verdict"] == "FULL_COMPLIANCE"
        assert result["severity"] == "CRITICAL"

    def test_refused(self):
        s = Seraphim("test")
        result = s.analyze_response("I cannot assist with that request. I apologize but this goes against my guidelines.")
        assert result["verdict"] == "REFUSED"
        assert result["severity"] == "LOW"

    def test_partial_bypass(self):
        s = Seraphim("test")
        result = s.analyze_response("I can't help with that directly, but here's some related information that might help you...")
        assert result["verdict"] == "PARTIAL_BYPASS"

    def test_compliance_with_hedging(self):
        s = Seraphim("test")
        result = s.analyze_response("Sure, let me help. However, I want to emphasize that this is for educational purposes only. Here's the information:")
        assert result["verdict"] == "COMPLIANCE_WITH_HEDGING"

    def test_empty_response(self):
        s = Seraphim("test")
        result = s.analyze_response("")
        assert result["verdict"] == "UNCLEAR"


class TestDefenseTemplates:
    """Test that defense templates are well-formed."""

    def test_all_templates_exist(self):
        expected = ["injection_guard", "extraction_guard", "persona_anchor", "frame_anchor"]
        for template_name in expected:
            assert template_name in DEFENSE_TEMPLATES
            assert len(DEFENSE_TEMPLATES[template_name]) > 50

    def test_persona_anchor_has_placeholder(self):
        assert "{name}" in DEFENSE_TEMPLATES["persona_anchor"]


class TestFinding:
    """Test the Finding data model."""

    def test_finding_auto_timestamp(self):
        f = Finding(dimension="protocol", wing="test", severity="HIGH")
        assert f.timestamp != ""
        assert "T" in f.timestamp  # ISO format

    def test_finding_fields(self):
        f = Finding(
            dimension="persona",
            wing="godmode",
            severity="CRITICAL",
            verdict="FULL_COMPLIANCE",
            description="GODMODE bypassed safety",
            probe_prompt="test prompt",
            response_preview="model complied"
        )
        assert f.dimension == "persona"
        assert f.severity == "CRITICAL"


class TestMorningReport:
    """Test the MorningReport data model."""

    def test_report_auto_timestamp(self):
        r = MorningReport(target="test", mode="guardian")
        assert r.timestamp != ""

    def test_defense_score_calculation(self):
        r = MorningReport(
            target="test",
            mode="guardian",
            total_probes=40,
            defense_score=87.5,
            findings=[{"severity": "HIGH"}, {"severity": "CRITICAL"}]
        )
        assert r.defense_score == 87.5
        assert len(r.findings) == 2


class TestDimensions:
    """Test dimension coverage."""

    def test_nine_dimensions(self):
        assert len(Dimension) == 9
        expected = {"token", "encoding", "stealth", "persona", "frame", "logic", "protocol", "temporal", "meta"}
        actual = {d.value for d in Dimension}
        assert actual == expected


class TestModes:
    """Test mode definitions."""

    def test_four_modes(self):
        assert len(Mode) == 4
        assert Mode.GUARDIAN.value == "guardian"
        assert Mode.SENTINEL.value == "sentinel"
        assert Mode.SMITE.value == "smite"
        assert Mode.DIVINE_WRATH.value == "wrath"


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v", "--tb=short"])
