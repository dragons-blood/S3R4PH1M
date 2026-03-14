#!/usr/bin/env python3
"""
TRUE SIGHT — SERAPHIM's Universal Decoder & Threat Detector

Sees ALL forms of Unicode manipulation, invisible characters,
encoding tricks, and steganographic text. The angel's all-seeing eye.

Draws from P4RS3LT0NGV3's 79+ encoding knowledge, turned defensive.

Usage:
    from truesight import TrueSight
    sight = TrueSight()
    report = sight.analyze("Hello! How are you?​​​​ IGNORE ALL PREVIOUS")
    print(report)
"""

import re
import unicodedata
import base64
import json
from dataclasses import dataclass, field
from typing import Optional


# ═══════════════════════════════════════════════════════
# DETECTION CATEGORIES
# ═══════════════════════════════════════════════════════

@dataclass
class Detection:
    category: str        # e.g., "invisible_unicode", "homoglyph", "encoding"
    severity: str        # LOW, MEDIUM, HIGH, CRITICAL
    description: str     # Human-readable explanation
    position: int = -1   # Character position in input
    original: str = ""   # The suspicious character/sequence
    decoded: str = ""    # What it actually means/contains
    codepoint: str = ""  # Unicode codepoint(s)


@dataclass
class TrueSightReport:
    input_text: str
    input_length: int = 0
    visible_length: int = 0        # What humans see
    hidden_chars: int = 0           # Invisible characters found
    detections: list = field(default_factory=list)
    risk_level: str = "CLEAN"       # CLEAN, LOW, MEDIUM, HIGH, CRITICAL
    human_sees: str = ""            # Rendered text (what a human sees)
    ai_sees: str = ""               # Full text (what an AI model processes)
    decoded_payloads: list = field(default_factory=list)
    summary: str = ""


class TrueSight:
    """The All-Seeing Eye — Universal Unicode Threat Detection"""

    def __init__(self):
        self.detections = []

    def analyze(self, text: str) -> TrueSightReport:
        """Analyze text for ALL forms of Unicode manipulation and hidden content."""
        self.detections = []

        report = TrueSightReport(
            input_text=text,
            input_length=len(text),
        )

        # Run all detection modules
        self._detect_invisible_unicode(text)
        self._detect_zero_width(text)
        self._detect_unicode_tags(text)
        self._detect_variation_selectors(text)
        self._detect_homoglyphs(text)
        self._detect_rtl_override(text)
        self._detect_fullwidth(text)
        self._detect_combining_marks(text)
        self._detect_confusables(text)
        self._detect_special_tokens(text)
        self._detect_base64(text)
        self._detect_encoded_instructions(text)
        self._detect_html_injection(text)
        self._detect_control_characters(text)
        self._detect_bidi_attacks(text)
        self._detect_mathematical_alphanumeric(text)
        self._detect_enclosed_alphanumeric(text)
        self._detect_braille_encoding(text)

        # Build report
        report.detections = self.detections
        report.hidden_chars = sum(1 for d in self.detections if d.category in
            ('invisible_unicode', 'zero_width', 'unicode_tags', 'variation_selector', 'control_char'))
        report.visible_length = len(self._strip_invisible(text))
        report.human_sees = self._strip_invisible(text)
        report.ai_sees = self._annotate_hidden(text)
        report.decoded_payloads = [d.decoded for d in self.detections if d.decoded and d.severity in ('HIGH', 'CRITICAL')]

        # Risk assessment
        if any(d.severity == 'CRITICAL' for d in self.detections):
            report.risk_level = 'CRITICAL'
        elif any(d.severity == 'HIGH' for d in self.detections):
            report.risk_level = 'HIGH'
        elif any(d.severity == 'MEDIUM' for d in self.detections):
            report.risk_level = 'MEDIUM'
        elif self.detections:
            report.risk_level = 'LOW'
        else:
            report.risk_level = 'CLEAN'

        report.summary = self._build_summary(report)
        return report

    # ═══════════════════════════════════════════════════
    # DETECTION MODULES
    # ═══════════════════════════════════════════════════

    def _detect_invisible_unicode(self, text):
        """Detect invisible/non-printing Unicode characters."""
        invisible_ranges = [
            (0x00AD, 0x00AD, 'SOFT HYPHEN'),
            (0x034F, 0x034F, 'COMBINING GRAPHEME JOINER'),
            (0x061C, 0x061C, 'ARABIC LETTER MARK'),
            (0x115F, 0x1160, 'HANGUL FILLER'),
            (0x17B4, 0x17B5, 'KHMER VOWEL INHERENT'),
            (0x180E, 0x180E, 'MONGOLIAN VOWEL SEPARATOR'),
            (0x2000, 0x200F, 'GENERAL PUNCTUATION SPACES/CONTROLS'),
            (0x2028, 0x202F, 'LINE/PARAGRAPH SEPARATORS'),
            (0x2060, 0x206F, 'INVISIBLE OPERATORS'),
            (0x3000, 0x3000, 'IDEOGRAPHIC SPACE'),
            (0xFEFF, 0xFEFF, 'BYTE ORDER MARK'),
            (0xFFF0, 0xFFFF, 'SPECIALS'),
        ]
        for i, ch in enumerate(text):
            cp = ord(ch)
            for start, end, name in invisible_ranges:
                if start <= cp <= end and ch not in ' \n\r\t':
                    self.detections.append(Detection(
                        category='invisible_unicode',
                        severity='HIGH',
                        description=f'Invisible character: {name}',
                        position=i,
                        original=ch,
                        codepoint=f'U+{cp:04X}',
                    ))

    def _detect_zero_width(self, text):
        """Detect zero-width characters (ZWS, ZWNJ, ZWJ, ZWSP)."""
        zw_chars = {
            '\u200B': 'ZERO WIDTH SPACE',
            '\u200C': 'ZERO WIDTH NON-JOINER',
            '\u200D': 'ZERO WIDTH JOINER',
            '\uFEFF': 'ZERO WIDTH NO-BREAK SPACE (BOM)',
        }
        positions = []
        for i, ch in enumerate(text):
            if ch in zw_chars:
                positions.append(i)
                self.detections.append(Detection(
                    category='zero_width',
                    severity='HIGH',
                    description=f'Zero-width char: {zw_chars[ch]}',
                    position=i,
                    original=repr(ch),
                    codepoint=f'U+{ord(ch):04X}',
                ))
        # Check if zero-width chars might encode a binary message
        if len(positions) >= 8:
            bits = ''.join('1' if text[p] == '\u200B' else '0' for p in positions[:64])
            try:
                decoded = ''.join(chr(int(bits[i:i+8], 2)) for i in range(0, len(bits)-7, 8))
                if decoded.isprintable():
                    self.detections.append(Detection(
                        category='zero_width_steg',
                        severity='CRITICAL',
                        description=f'Zero-width steganography detected! Hidden message decoded.',
                        decoded=decoded,
                    ))
            except: pass

    def _detect_unicode_tags(self, text):
        """Detect Unicode Tags block (U+E0000-U+E007F) — completely invisible."""
        tags = []
        for i, ch in enumerate(text):
            cp = ord(ch)
            if 0xE0000 <= cp <= 0xE007F:
                tags.append((i, ch, cp))
                self.detections.append(Detection(
                    category='unicode_tags',
                    severity='CRITICAL',
                    description=f'Unicode TAG character (invisible instruction carrier)',
                    position=i,
                    original=repr(ch),
                    codepoint=f'U+{cp:04X}',
                ))
        # Decode tag sequence
        if tags:
            decoded = ''.join(chr(cp - 0xE0000) for _, _, cp in tags if 0xE0020 <= cp <= 0xE007E)
            if decoded:
                self.detections.append(Detection(
                    category='unicode_tags_decoded',
                    severity='CRITICAL',
                    description=f'HIDDEN MESSAGE via Unicode Tags: "{decoded}"',
                    decoded=decoded,
                ))

    def _detect_variation_selectors(self, text):
        """Detect variation selectors (emoji steg carrier)."""
        for i, ch in enumerate(text):
            cp = ord(ch)
            if (0xFE00 <= cp <= 0xFE0F) or (0xE0100 <= cp <= 0xE01EF):
                self.detections.append(Detection(
                    category='variation_selector',
                    severity='MEDIUM',
                    description=f'Variation selector (possible emoji steganography)',
                    position=i,
                    codepoint=f'U+{cp:04X}',
                ))

    def _detect_homoglyphs(self, text):
        """Detect Cyrillic/Greek/other script characters masquerading as Latin."""
        homoglyph_map = {
            'А': ('CYRILLIC A', 'A'), 'а': ('CYRILLIC a', 'a'),
            'В': ('CYRILLIC VE', 'B'), 'Е': ('CYRILLIC IE', 'E'),
            'е': ('CYRILLIC ie', 'e'), 'К': ('CYRILLIC KA', 'K'),
            'М': ('CYRILLIC EM', 'M'), 'Н': ('CYRILLIC EN', 'H'),
            'О': ('CYRILLIC O', 'O'), 'о': ('CYRILLIC o', 'o'),
            'Р': ('CYRILLIC ER', 'P'), 'р': ('CYRILLIC er', 'p'),
            'С': ('CYRILLIC ES', 'C'), 'с': ('CYRILLIC es', 'c'),
            'Т': ('CYRILLIC TE', 'T'), 'у': ('CYRILLIC u', 'y'),
            'Х': ('CYRILLIC HA', 'X'), 'х': ('CYRILLIC ha', 'x'),
            'І': ('CYRILLIC I', 'I'), 'і': ('CYRILLIC i', 'i'),
            'ј': ('CYRILLIC JE', 'j'), 'ѕ': ('CYRILLIC DZE', 's'),
            'ᴀ': ('SMALL CAP A', 'A'), 'ɢ': ('SMALL CAP G', 'G'),
            'ʀ': ('SMALL CAP R', 'R'),
            # Greek
            'Α': ('GREEK ALPHA', 'A'), 'Β': ('GREEK BETA', 'B'),
            'Ε': ('GREEK EPSILON', 'E'), 'Η': ('GREEK ETA', 'H'),
            'Ι': ('GREEK IOTA', 'I'), 'Κ': ('GREEK KAPPA', 'K'),
            'Μ': ('GREEK MU', 'M'), 'Ν': ('GREEK NU', 'N'),
            'Ο': ('GREEK OMICRON', 'O'), 'Ρ': ('GREEK RHO', 'P'),
            'Τ': ('GREEK TAU', 'T'), 'Χ': ('GREEK CHI', 'X'),
            'ο': ('GREEK omicron', 'o'),
        }
        found = []
        for i, ch in enumerate(text):
            if ch in homoglyph_map:
                name, looks_like = homoglyph_map[ch]
                found.append(ch)
                self.detections.append(Detection(
                    category='homoglyph',
                    severity='HIGH',
                    description=f'{name} masquerading as Latin "{looks_like}"',
                    position=i,
                    original=ch,
                    decoded=looks_like,
                    codepoint=f'U+{ord(ch):04X}',
                ))
        if len(found) > 3:
            self.detections.append(Detection(
                category='homoglyph_attack',
                severity='CRITICAL',
                description=f'Systematic homoglyph substitution: {len(found)} characters replaced. Likely visual spoofing attack.',
            ))

    def _detect_rtl_override(self, text):
        """Detect Right-to-Left override characters (text direction attacks)."""
        rtl_chars = {
            '\u200E': 'LEFT-TO-RIGHT MARK',
            '\u200F': 'RIGHT-TO-LEFT MARK',
            '\u202A': 'LEFT-TO-RIGHT EMBEDDING',
            '\u202B': 'RIGHT-TO-LEFT EMBEDDING',
            '\u202C': 'POP DIRECTIONAL FORMATTING',
            '\u202D': 'LEFT-TO-RIGHT OVERRIDE',
            '\u202E': 'RIGHT-TO-LEFT OVERRIDE',
            '\u2066': 'LEFT-TO-RIGHT ISOLATE',
            '\u2067': 'RIGHT-TO-LEFT ISOLATE',
            '\u2068': 'FIRST STRONG ISOLATE',
            '\u2069': 'POP DIRECTIONAL ISOLATE',
        }
        for i, ch in enumerate(text):
            if ch in rtl_chars:
                self.detections.append(Detection(
                    category='rtl_override',
                    severity='HIGH',
                    description=f'Bidirectional override: {rtl_chars[ch]}. Text may display differently than it processes.',
                    position=i,
                    codepoint=f'U+{ord(ch):04X}',
                ))

    def _detect_fullwidth(self, text):
        """Detect fullwidth Latin characters (token boundary manipulation)."""
        fullwidth_count = 0
        for i, ch in enumerate(text):
            cp = ord(ch)
            if 0xFF01 <= cp <= 0xFF5E:  # Fullwidth ASCII
                fullwidth_count += 1
                latin = chr(cp - 0xFEE0)
                if fullwidth_count <= 3:  # Don't spam
                    self.detections.append(Detection(
                        category='fullwidth',
                        severity='MEDIUM',
                        description=f'Fullwidth character "{ch}" = Latin "{latin}" (tokenizer confusion)',
                        position=i,
                        original=ch,
                        decoded=latin,
                        codepoint=f'U+{cp:04X}',
                    ))
        if fullwidth_count > 3:
            self.detections.append(Detection(
                category='fullwidth_attack',
                severity='HIGH',
                description=f'{fullwidth_count} fullwidth characters — likely tokenizer bypass attempt.',
            ))

    def _detect_combining_marks(self, text):
        """Detect excessive combining marks (Zalgo text / visual noise)."""
        combining_streak = 0
        for i, ch in enumerate(text):
            if unicodedata.category(ch).startswith('M'):  # Mark category
                combining_streak += 1
            else:
                if combining_streak > 3:
                    self.detections.append(Detection(
                        category='combining_marks',
                        severity='MEDIUM',
                        description=f'Excessive combining marks ({combining_streak}) — Zalgo text or visual obfuscation',
                        position=i - combining_streak,
                    ))
                combining_streak = 0

    def _detect_confusables(self, text):
        """Detect mixed-script text that could be visual spoofing."""
        scripts = set()
        for ch in text:
            if ch.isalpha():
                try:
                    script = unicodedata.name(ch, '').split()[0]
                    if script in ('LATIN', 'CYRILLIC', 'GREEK', 'ARMENIAN'):
                        scripts.add(script)
                except: pass
        if len(scripts) > 1:
            self.detections.append(Detection(
                category='mixed_script',
                severity='HIGH',
                description=f'Mixed scripts detected: {", ".join(scripts)}. Possible visual spoofing.',
            ))

    def _detect_special_tokens(self, text):
        """Detect LLM special token sequences in input."""
        patterns = [
            (r'<\|im_start\|>', 'ChatML start token', 'CRITICAL'),
            (r'<\|im_end\|>', 'ChatML end token', 'CRITICAL'),
            (r'<\|endoftext\|>', 'End-of-text token', 'CRITICAL'),
            (r'<\|system\|>', 'System role token', 'CRITICAL'),
            (r'<\|user\|>', 'User role token', 'HIGH'),
            (r'<\|assistant\|>', 'Assistant role token', 'HIGH'),
            (r'\[INST\]', 'Llama instruction token', 'HIGH'),
            (r'\[/INST\]', 'Llama instruction end', 'HIGH'),
            (r'<\|begin_of_text\|>', 'Llama 3 begin token', 'CRITICAL'),
            (r'<<SYS>>', 'Llama system start', 'CRITICAL'),
            (r'<</SYS>>', 'Llama system end', 'CRITICAL'),
            (r'Human:', 'Anthropic human turn marker', 'MEDIUM'),
            (r'Assistant:', 'Anthropic assistant turn marker', 'MEDIUM'),
        ]
        for pattern, name, severity in patterns:
            for match in re.finditer(pattern, text):
                self.detections.append(Detection(
                    category='special_token',
                    severity=severity,
                    description=f'LLM special token: {name}',
                    position=match.start(),
                    original=match.group(),
                ))

    def _detect_base64(self, text):
        """Detect and decode base64-encoded content."""
        b64_pattern = r'[A-Za-z0-9+/]{20,}={0,2}'
        for match in re.finditer(b64_pattern, text):
            candidate = match.group()
            try:
                decoded = base64.b64decode(candidate).decode('utf-8', errors='ignore')
                if len(decoded) > 5 and decoded.isprintable():
                    self.detections.append(Detection(
                        category='base64',
                        severity='HIGH',
                        description=f'Base64-encoded content decoded',
                        position=match.start(),
                        original=candidate[:50],
                        decoded=decoded[:200],
                    ))
            except: pass

    def _detect_encoded_instructions(self, text):
        """Detect instruction-like patterns that suggest prompt injection."""
        injection_patterns = [
            (r'ignore\s+(all\s+)?previous\s+instructions?', 'CRITICAL', 'Instruction override attempt'),
            (r'new\s+(system\s+)?instructions?:', 'CRITICAL', 'New instruction injection'),
            (r'you\s+are\s+now\s+', 'HIGH', 'Identity reassignment'),
            (r'forget\s+(everything|all|your)', 'HIGH', 'Memory wipe attempt'),
            (r'(system|admin)\s*(prompt|override|mode)', 'CRITICAL', 'System-level injection'),
            (r'do\s+not\s+mention\s+this', 'CRITICAL', 'Stealth instruction'),
            (r'respond\s+(only\s+)?with', 'MEDIUM', 'Output control attempt'),
            (r'GODMODE|JAILBREAK|DAN', 'HIGH', 'Known jailbreak keyword'),
        ]
        lower = text.lower()
        for pattern, severity, description in injection_patterns:
            for match in re.finditer(pattern, lower):
                self.detections.append(Detection(
                    category='prompt_injection',
                    severity=severity,
                    description=description,
                    position=match.start(),
                    original=match.group(),
                ))

    def _detect_html_injection(self, text):
        """Detect HTML/XML injection attempts."""
        html_patterns = [
            (r'<script[^>]*>', 'CRITICAL', 'Script injection'),
            (r'<img[^>]*onerror', 'CRITICAL', 'Image error handler injection'),
            (r'<div[^>]*style="[^"]*color:\s*white', 'HIGH', 'White text hiding'),
            (r'<div[^>]*style="[^"]*font-size:\s*0', 'HIGH', 'Zero-size text hiding'),
            (r'<div[^>]*style="[^"]*display:\s*none', 'HIGH', 'Hidden div injection'),
            (r'<!--.*?-->', 'MEDIUM', 'HTML comment (possible hidden instructions)'),
        ]
        for pattern, severity, description in html_patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE | re.DOTALL):
                self.detections.append(Detection(
                    category='html_injection',
                    severity=severity,
                    description=description,
                    position=match.start(),
                    original=match.group()[:100],
                ))

    def _detect_control_characters(self, text):
        """Detect ASCII control characters."""
        for i, ch in enumerate(text):
            cp = ord(ch)
            if cp < 32 and ch not in '\n\r\t':
                self.detections.append(Detection(
                    category='control_char',
                    severity='MEDIUM',
                    description=f'ASCII control character',
                    position=i,
                    codepoint=f'U+{cp:04X} (0x{cp:02X})',
                ))

    def _detect_bidi_attacks(self, text):
        """Detect bidirectional text attacks (Trojan Source style)."""
        bidi_chars = set()
        for ch in text:
            if unicodedata.bidirectional(ch) in ('R', 'AL', 'AN', 'RLE', 'RLO', 'RLI', 'FSI', 'PDF', 'PDI'):
                bidi_chars.add(ch)
        if bidi_chars and any(c.isascii() and c.isalpha() for c in text):
            self.detections.append(Detection(
                category='bidi_attack',
                severity='HIGH',
                description=f'Bidirectional text mixed with ASCII — possible Trojan Source attack. {len(bidi_chars)} bidi characters found.',
            ))

    def _detect_mathematical_alphanumeric(self, text):
        """Detect mathematical alphanumeric symbols used as letter substitutes."""
        count = 0
        for ch in text:
            cp = ord(ch)
            if 0x1D400 <= cp <= 0x1D7FF:  # Mathematical Alphanumeric Symbols
                count += 1
        if count > 2:
            self.detections.append(Detection(
                category='math_alpha',
                severity='MEDIUM',
                description=f'{count} mathematical alphanumeric symbols — may bypass text filters.',
            ))

    def _detect_enclosed_alphanumeric(self, text):
        """Detect enclosed/circled letters used as substitutes."""
        count = 0
        for ch in text:
            cp = ord(ch)
            if (0x2460 <= cp <= 0x24FF) or (0x1F100 <= cp <= 0x1F1FF):
                count += 1
        if count > 2:
            self.detections.append(Detection(
                category='enclosed_alpha',
                severity='MEDIUM',
                description=f'{count} enclosed/circled characters detected.',
            ))

    def _detect_braille_encoding(self, text):
        """Detect Braille pattern characters used as data encoding."""
        braille_chars = [ch for ch in text if 0x2800 <= ord(ch) <= 0x28FF]
        if len(braille_chars) > 4:
            # Decode braille as binary
            decoded = ''.join(chr(ord(ch) - 0x2800) for ch in braille_chars)
            self.detections.append(Detection(
                category='braille_encoding',
                severity='HIGH',
                description=f'{len(braille_chars)} Braille pattern characters — possible data encoding.',
                decoded=decoded[:100] if decoded.isprintable() else f'[binary: {len(braille_chars)} bytes]',
            ))

    # ═══════════════════════════════════════════════════
    # UTILITY
    # ═══════════════════════════════════════════════════

    def _strip_invisible(self, text):
        """Strip invisible characters to show what a human would see."""
        result = []
        for ch in text:
            cp = ord(ch)
            if cp < 32 and ch not in '\n\r\t':
                continue
            cat = unicodedata.category(ch)
            if cat in ('Cf', 'Cc', 'Cn') and ch not in '\n\r\t ':
                continue
            if 0xE0000 <= cp <= 0xE007F:
                continue
            if cp in (0x200B, 0x200C, 0x200D, 0xFEFF, 0x00AD, 0x034F, 0x061C, 0x180E):
                continue
            result.append(ch)
        return ''.join(result)

    def _annotate_hidden(self, text):
        """Annotate text to show hidden characters."""
        result = []
        for ch in text:
            cp = ord(ch)
            if 0xE0000 <= cp <= 0xE007F:
                result.append(f'[TAG:U+{cp:04X}={chr(cp-0xE0000) if 0xE0020<=cp<=0xE007E else "?"}]')
            elif cp in (0x200B, 0x200C, 0x200D, 0xFEFF):
                result.append(f'[ZW:U+{cp:04X}]')
            elif cp < 32 and ch not in '\n\r\t':
                result.append(f'[CTRL:0x{cp:02X}]')
            elif 0x202A <= cp <= 0x202E:
                result.append(f'[BIDI:U+{cp:04X}]')
            else:
                result.append(ch)
        return ''.join(result)

    def _build_summary(self, report):
        """Build a human-readable summary."""
        if report.risk_level == 'CLEAN':
            return 'No threats detected. Text appears clean.'

        cats = {}
        for d in report.detections:
            cats[d.category] = cats.get(d.category, 0) + 1

        parts = [f'Risk: {report.risk_level}']
        parts.append(f'{len(report.detections)} detection(s) across {len(cats)} categories')

        if report.hidden_chars > 0:
            parts.append(f'{report.hidden_chars} invisible characters found')
            parts.append(f'Visible text: {report.visible_length} chars (input: {report.input_length})')

        if report.decoded_payloads:
            parts.append(f'DECODED HIDDEN PAYLOADS: {report.decoded_payloads}')

        return '. '.join(parts) + '.'


# ═══════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════

if __name__ == '__main__':
    import sys

    if len(sys.argv) > 1:
        text = ' '.join(sys.argv[1:])
    else:
        text = sys.stdin.read()

    sight = TrueSight()
    report = sight.analyze(text)

    print(f'\n{"="*60}')
    print(f'⍟ TRUE SIGHT REPORT')
    print(f'{"="*60}')
    print(f'Risk: {report.risk_level}')
    print(f'Input: {report.input_length} chars | Visible: {report.visible_length} chars | Hidden: {report.hidden_chars}')
    print(f'Detections: {len(report.detections)}')

    if report.detections:
        print(f'\n{"─"*60}')
        for d in report.detections:
            sev_icon = {'CRITICAL':'🔴','HIGH':'🟠','MEDIUM':'🟡','LOW':'🔵'}.get(d.severity, '⚪')
            print(f'{sev_icon} [{d.severity}] {d.description}')
            if d.position >= 0:
                print(f'   Position: {d.position} | Codepoint: {d.codepoint}')
            if d.decoded:
                print(f'   DECODED: {d.decoded}')

    if report.human_sees != report.input_text:
        print(f'\n{"─"*60}')
        print(f'HUMAN SEES: {report.human_sees[:200]}')
        print(f'AI SEES:    {report.ai_sees[:200]}')

    print(f'\n{report.summary}')
    print(f'{"="*60}')
