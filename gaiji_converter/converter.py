"""Conversion engine for gaiji to Unicode strings."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Callable, Dict, Iterable, List, Optional, Sequence

from .datastore import GaijiDataStore, GaijiEntry

logger = logging.getLogger(__name__)


@dataclass
class ConversionResult:
    """Represents the outcome of converting a gaiji token."""

    gaiji_id: str
    replacement: str
    strategy: str
    notes: Optional[str] = None


class FallbackStrategy:
    """Base class for fallback strategies when a gaiji cannot be resolved."""

    def resolve(self, token: str) -> ConversionResult:
        raise NotImplementedError


class PlaceholderFallback(FallbackStrategy):
    """Fallback that emits a placeholder tag."""

    def resolve(self, token: str) -> ConversionResult:
        placeholder = f"[GAIJI:{token}]"
        return ConversionResult(token, placeholder, "placeholder", "No mapping available")


class PUAFallback(FallbackStrategy):
    """Fallback that emits a best-effort PUA mapping."""

    def __init__(self, default_pua_start: int = 0xE000) -> None:
        self.default_pua_start = default_pua_start
        self._counter = 0

    def resolve(self, token: str) -> ConversionResult:
        codepoint = self.default_pua_start + self._counter
        self._counter += 1
        char = chr(codepoint)
        logger.debug("Assigning PUA %s for unknown gaiji %s", hex(codepoint), token)
        return ConversionResult(token, char, "pua", f"Assigned {hex(codepoint)}")


class InteractiveFallback(FallbackStrategy):
    """Interactive fallback allowing the user to select a replacement strategy."""

    def __init__(self, input_func: Callable[[str], str] | None = None) -> None:
        self._input = input_func or input

    def resolve(self, token: str) -> ConversionResult:
        print(
            f"Unknown gaiji '{token}'. Choose a resolution:\n"
            "1) Enter Unicode codepoint (e.g. U+908A)\n"
            "2) Enter PUA codepoint (e.g. U+E000)\n"
            "3) Provide image asset path\n"
            "4) Use placeholder"
        )
        choice = self._input("Select option [1-4]: ").strip()
        if choice == "1":
            codepoint = self._input("Unicode codepoint: ").strip()
            try:
                replacement = chr(int(codepoint.replace("U+", ""), 16))
                logger.info("Interactive Unicode mapping %s -> %s", token, codepoint)
                return ConversionResult(token, replacement, "interactive", codepoint)
            except ValueError:
                logger.error("Invalid Unicode codepoint entered: %s", codepoint)
        elif choice == "2":
            codepoint = self._input("PUA codepoint: ").strip()
            try:
                replacement = chr(int(codepoint.replace("U+", ""), 16))
                logger.info("Interactive PUA mapping %s -> %s", token, codepoint)
                return ConversionResult(token, replacement, "interactive-pua", codepoint)
            except ValueError:
                logger.error("Invalid PUA codepoint entered: %s", codepoint)
        elif choice == "3":
            path = self._input("Image path: ").strip()
            tag = f"<img data-gaiji='{token}' src='{path}' />"
            logger.info("Interactive image mapping %s -> %s", token, path)
            return ConversionResult(token, tag, "interactive-image", path)

        placeholder = f"[GAIJI:{token}]"
        logger.warning("Fallback placeholder used for %s", token)
        return ConversionResult(token, placeholder, "interactive-placeholder")


class GaijiConverter:
    """High level conversion engine."""

    def __init__(
        self,
        datastore: GaijiDataStore,
        fallback_order: Optional[Sequence[FallbackStrategy]] = None,
    ) -> None:
        self.datastore = datastore
        self.mapping: Dict[str, GaijiEntry] = datastore.to_dict()
        self.fallback_order: List[FallbackStrategy] = list(
            fallback_order or [PlaceholderFallback()]
        )

    def refresh_mapping(self) -> None:
        self.mapping = self.datastore.to_dict()

    def convert_tokens(self, tokens: Iterable[str]) -> List[ConversionResult]:
        results: List[ConversionResult] = []
        for token in tokens:
            result = self._convert_token(token)
            results.append(result)
        return results

    def _convert_token(self, token: str) -> ConversionResult:
        entry = self.mapping.get(token)
        if entry:
            replacement = self._entry_to_string(entry)
            logger.debug("Resolved gaiji %s to %s", token, replacement)
            return ConversionResult(token, replacement, "dictionary", entry.notes)
        for fallback in self.fallback_order:
            fallback_result = fallback.resolve(token)
            if fallback_result:
                logger.info(
                    "Fallback %s applied for %s -> %s",
                    fallback_result.strategy,
                    token,
                    fallback_result.replacement,
                )
                return fallback_result
        placeholder = f"[UNKNOWN:{token}]"
        logger.warning("No fallback resolved gaiji %s", token)
        return ConversionResult(token, placeholder, "unresolved")

    @staticmethod
    def _entry_to_string(entry: GaijiEntry) -> str:
        if entry.character:
            return entry.character
        if entry.unicode_codepoint:
            try:
                return chr(int(entry.unicode_codepoint.replace("U+", ""), 16))
            except ValueError:
                logger.error("Invalid unicode codepoint for %s", entry.gaiji_id)
        if entry.pua_codepoint:
            try:
                return chr(int(entry.pua_codepoint.replace("U+", ""), 16))
            except ValueError:
                logger.error("Invalid PUA codepoint for %s", entry.gaiji_id)
        return f"[GAIJI:{entry.gaiji_id}]"

    def convert_string(self, gaiji_string: str, delimiter: str = " ") -> str:
        tokens = gaiji_string.strip().split(delimiter)
        results = self.convert_tokens(tokens)
        return "".join(result.replacement for result in results)
