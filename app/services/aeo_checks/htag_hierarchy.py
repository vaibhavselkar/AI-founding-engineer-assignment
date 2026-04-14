from app.services.aeo_checks.base import BaseCheck
from app.models.schemas import CheckResult
from app.services.content_parser import extract_htags


class HTagHierarchyCheck(BaseCheck):
    """
    Check B — H-tag Hierarchy Checker
    Tests if heading structure is valid H1 → H2 → H3
    """

    def run(self, soup, plain_text: str) -> CheckResult:

        # Extract all H tags in DOM order
        htags = extract_htags(soup)

        # Find violations
        violations = self._find_violations(htags)

        # Calculate score
        score = self._calculate_score(violations, htags)

        # Recommendation
        recommendation = self._get_recommendation(violations, htags)

        return CheckResult(
            check_id="htag_hierarchy",
            name="H-tag Hierarchy",
            passed=len(violations) == 0,
            score=score,
            max_score=20,
            details={
                "violations": violations,
                "h_tags_found": htags,
            },
            recommendation=recommendation,
        )

    def _find_violations(self, htags: list) -> list:
        """Find all heading hierarchy violations"""
        violations = []

        if not htags:
            violations.append("No heading tags found in content")
            return violations

        # Check exactly one H1
        h1_count = htags.count("h1")
        if h1_count == 0:
            violations.append("No H1 tag found — every page must have exactly one H1")
        elif h1_count > 1:
            violations.append(f"Multiple H1 tags found ({h1_count}) — only one H1 allowed")

        # Check no H tag appears before H1
        if "h1" in htags:
            h1_index = htags.index("h1")
            tags_before_h1 = htags[:h1_index]
            if tags_before_h1:
                violations.append(
                    f"Heading tags {tags_before_h1} appear before H1"
                )

        # Check no level is skipped
        level_map = {"h1": 1, "h2": 2, "h3": 3, "h4": 4, "h5": 5, "h6": 6}
        prev_level = 0

        for tag in htags:
            current_level = level_map.get(tag, 0)
            if prev_level > 0 and current_level > prev_level + 1:
                violations.append(
                    f"Heading level skipped: {tag} follows h{prev_level} "
                    f"(missing h{prev_level + 1})"
                )
            prev_level = current_level

        return violations

    def _calculate_score(self, violations: list, htags: list) -> int:
        """Calculate score based on violations"""
        # Missing H1 or 3+ violations = 0
        h1_count = htags.count("h1") if htags else 0
        if h1_count == 0 or len(violations) >= 3:
            return 0
        elif len(violations) == 0:
            return 20
        else:
            return 12

    def _get_recommendation(
        self, violations: list, htags: list
    ) -> str | None:
        """Return actionable recommendation"""
        if not violations:
            return None
        if not htags or htags.count("h1") == 0:
            return (
                "Add an H1 tag as the main title of your content. "
                "Every page must have exactly one H1."
            )
        if len(violations) >= 3:
            return (
                "Your heading structure has multiple issues. "
                "Restructure headings as H1 → H2 → H3 without skipping levels."
            )
        return (
            f"Fix heading structure issues: {', '.join(violations[:2])}."
        )