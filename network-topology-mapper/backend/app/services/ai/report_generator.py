import logging
import json
from typing import Any

from app.config import get_settings

logger = logging.getLogger(__name__)


class ReportGenerator:
    """Uses Claude API to generate natural language resilience reports."""

    def __init__(self):
        self._client = None
        try:
            import anthropic
            settings = get_settings()
            if settings.anthropic_api_key and settings.anthropic_api_key != "sk-ant-replace-me":
                self._client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        except ImportError:
            logger.warning("anthropic SDK not installed. Report generation unavailable.")

    @property
    def available(self) -> bool:
        return self._client is not None

    def generate_resilience_report(self, resilience_data: dict,
                                    spofs: list[dict],
                                    topology_stats: dict) -> dict:
        if not self._client:
            return self._generate_fallback_report(resilience_data, spofs, topology_stats)

        try:
            settings = get_settings()
            prompt = self._build_prompt(resilience_data, spofs, topology_stats)

            message = self._client.messages.create(
                model=settings.claude_model,
                max_tokens=2000,
                messages=[{"role": "user", "content": prompt}],
            )

            report_text = message.content[0].text

            return {
                "generated": True,
                "score": resilience_data.get("score", 0),
                "max_score": 10,
                "report": report_text,
                "spofs": spofs,
                "stats": topology_stats,
            }
        except Exception as e:
            logger.error("Claude API report generation failed: %s", e)
            return self._generate_fallback_report(resilience_data, spofs, topology_stats)

    def _build_prompt(self, resilience_data: dict, spofs: list, stats: dict) -> str:
        return f"""You are a network security and resilience analyst. Generate a concise resilience report based on this data.

## Network Stats
- Total devices: {stats.get('total_devices', 0)}
- Total connections: {stats.get('total_connections', 0)}
- Resilience score: {resilience_data.get('score', 0)}/10

## Score Breakdown
{json.dumps(resilience_data.get('breakdown', {}), indent=2)}

## Single Points of Failure ({len(spofs)} found)
{json.dumps(spofs[:5], indent=2)}

Generate a report with:
1. **Executive Summary** (2-3 sentences)
2. **Critical Findings** (numbered list, top 3-5 issues)
3. **Prioritized Recommendations** (numbered list with estimated impact)

Keep the tone professional but accessible. Use specific device names and numbers from the data."""

    def _generate_fallback_report(self, resilience_data: dict, spofs: list,
                                   stats: dict) -> dict:
        score = resilience_data.get("score", 0)
        risk_level = "Low" if score >= 7 else "Moderate" if score >= 4 else "High"

        findings = []
        for i, spof in enumerate(spofs[:5], 1):
            findings.append(
                f"{i}. {spof.get('hostname', 'Unknown device')} ({spof.get('device_type', 'unknown')}) "
                f"is a single point of failure - removal disconnects {spof.get('impact', 0)} devices."
            )

        recommendations = []
        for spof in spofs[:3]:
            recommendations.append(
                f"Add redundant path for {spof.get('hostname', 'device')} "
                f"to reduce blast radius of {spof.get('impact', 0)} devices."
            )

        report = f"""# Network Resilience Assessment

## Executive Summary
Your network scores {score}/10 for resilience, indicating **{risk_level} Risk**. """

        report += f"There are {len(spofs)} single points of failure across {stats.get('total_devices', 0)} devices "
        report += f"connected by {stats.get('total_connections', 0)} links.\n\n"

        report += "## Critical Findings\n"
        for f in findings:
            report += f"{f}\n"

        report += "\n## Prioritized Recommendations\n"
        for i, r in enumerate(recommendations, 1):
            report += f"{i}. {r}\n"

        return {
            "generated": False,
            "score": score,
            "max_score": 10,
            "report": report,
            "spofs": spofs,
            "stats": stats,
        }


report_generator = ReportGenerator()
