import asyncio
import logging
import json
import shutil
import subprocess

logger = logging.getLogger(__name__)


class ReportGenerator:
    """Uses Claude Code headless to generate natural language resilience reports."""

    def __init__(self):
        self._claude_path = shutil.which("claude")

    @property
    def available(self) -> bool:
        return self._claude_path is not None

    def _run_claude(self, prompt: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            [self._claude_path, "-p",
             "--output-format", "json", "--max-turns", "1"],
            input=prompt, capture_output=True, text=True, timeout=120,
        )

    async def generate_resilience_report(self, resilience_data: dict,
                                          spofs: list[dict],
                                          topology_stats: dict) -> dict:
        if not self._claude_path:
            return self._generate_fallback_report(resilience_data, spofs, topology_stats)

        try:
            prompt = self._build_prompt(resilience_data, spofs, topology_stats)

            proc = await asyncio.to_thread(self._run_claude, prompt)

            if proc.returncode != 0:
                logger.error("Claude Code failed (exit %d): %s",
                             proc.returncode, proc.stderr)
                return self._generate_fallback_report(resilience_data, spofs, topology_stats)

            result = json.loads(proc.stdout)

            if result.get("is_error"):
                logger.error("Claude Code returned error: %s", result.get("result", ""))
                return self._generate_fallback_report(resilience_data, spofs, topology_stats)

            report_text = result.get("result", "")

            return {
                "generated": True,
                "score": resilience_data.get("score", 0),
                "max_score": 10,
                "report": report_text,
                "spofs": spofs,
                "stats": topology_stats,
            }
        except subprocess.TimeoutExpired:
            logger.error("Claude Code timed out after 120s")
            return self._generate_fallback_report(resilience_data, spofs, topology_stats)
        except Exception as e:
            logger.error("Claude Code report generation failed: %r", e, exc_info=True)
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
3. **Prioritized Recommendations** (numbered list — end each recommendation with "Estimated impact: ..." on the same line)

Keep the tone professional but accessible. Use specific device names and numbers from the data. Use ## for section headings. Do not use markdown tables."""

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
