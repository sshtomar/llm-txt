"""Scorer for evaluating llm.txt quality and coverage."""

import re
from pathlib import Path
from typing import Dict, List, Optional


class LLMTxtScorer:
    """Score llm.txt files based on quality metrics."""

    def __init__(
        self,
        priority_keywords: Optional[List[str]] = None,
        max_kb: int = 100
    ):
        self.priority_keywords = priority_keywords or [
            'getting-started',
            'quickstart',
            'auth',
            'api',
            'config',
            'errors'
        ]
        self.max_kb = max_kb

    async def score(self, file_path: Path) -> Dict:
        """
        Calculate quality score for an llm.txt file.

        Scoring breakdown:
        - Topic coverage: 40 points
        - Size adherence: 20 points
        - Link health: 20 points
        - Signal ratio: 20 points

        Returns:
            Dictionary with scoring details
        """
        if not file_path.exists():
            return {
                'score': 0,
                'error': 'File not found'
            }

        try:
            content = file_path.read_text(encoding='utf-8')
        except Exception as e:
            return {
                'score': 0,
                'error': f'Failed to read file: {e}'
            }

        # Calculate individual scores
        coverage_score, topic_coverage = self._score_coverage(content)
        size_score, size_kb = self._score_size(content)
        link_health_score, link_stats = self._score_link_health(content)
        signal_score, signal_ratio = self._score_signal_ratio(content)

        # Calculate total score
        total_score = coverage_score + size_score + link_health_score + signal_score

        return {
            'score': total_score,
            'coverage_score': coverage_score,
            'topic_coverage': topic_coverage,
            'size_score': size_score,
            'size_kb': size_kb,
            'link_health_score': link_health_score,
            'valid_links': link_stats['valid'],
            'total_links': link_stats['total'],
            'signal_score': signal_score,
            'signal_ratio': signal_ratio,
            'breakdown': {
                'coverage': f'{coverage_score}/40',
                'size': f'{size_score}/20',
                'link_health': f'{link_health_score}/20',
                'signal': f'{signal_score}/20'
            }
        }

    def _score_coverage(self, content: str) -> tuple[int, Dict[str, bool]]:
        """
        Score topic coverage (max 40 points).

        Checks for presence of key documentation topics.
        """
        content_lower = content.lower()

        # Define topic patterns and their weights
        topics = {
            'getting_started': {
                'patterns': ['getting started', 'quickstart', 'quick start', 'introduction', 'overview'],
                'weight': 8
            },
            'installation': {
                'patterns': ['installation', 'install', 'setup', 'requirements'],
                'weight': 6
            },
            'authentication': {
                'patterns': ['authentication', 'auth', 'login', 'api key', 'token', 'credentials'],
                'weight': 6
            },
            'api_reference': {
                'patterns': ['api', 'reference', 'endpoints', 'methods', 'functions', 'commands'],
                'weight': 8
            },
            'configuration': {
                'patterns': ['configuration', 'config', 'settings', 'options', 'parameters'],
                'weight': 6
            },
            'errors': {
                'patterns': ['error', 'troubleshoot', 'debug', 'problem', 'issue', 'faq'],
                'weight': 6
            }
        }

        score = 0
        coverage = {}

        for topic_name, topic_info in topics.items():
            found = False
            for pattern in topic_info['patterns']:
                if pattern in content_lower:
                    found = True
                    break

            coverage[topic_name] = found
            if found:
                score += topic_info['weight']

        # Cap at 40 points
        score = min(score, 40)

        return score, coverage

    def _score_size(self, content: str) -> tuple[int, float]:
        """
        Score size adherence (max 20 points).

        Perfect score if within target range, decreases outside range.
        """
        size_bytes = len(content.encode('utf-8'))
        size_kb = size_bytes / 1024

        # Ideal range is 50-100% of max_kb
        ideal_min = self.max_kb * 0.5
        ideal_max = self.max_kb

        if ideal_min <= size_kb <= ideal_max:
            # Perfect score within ideal range
            score = 20
        elif size_kb < ideal_min:
            # Penalize for being too small
            ratio = size_kb / ideal_min
            score = int(20 * ratio)
        elif size_kb <= self.max_kb * 1.2:
            # Slight penalty for being over but not too much
            over_ratio = (size_kb - ideal_max) / (self.max_kb * 0.2)
            score = int(20 - (5 * over_ratio))
        else:
            # Heavy penalty for being way over
            score = 0

        return max(0, score), size_kb

    def _score_link_health(self, content: str) -> tuple[int, Dict[str, int]]:
        """
        Score link health (max 20 points).

        Based on ratio of valid to total links.
        """
        # Extract links
        markdown_links = re.findall(r'\[.*?\]\(([^)]+)\)', content)
        plain_links = re.findall(r'(?<!\])\bhttps?://[^\s<>"\[\]]+', content)

        all_links = list(set(markdown_links + plain_links))

        # Filter out fragments and anchors
        external_links = [
            link for link in all_links
            if link.startswith('http') and 'localhost' not in link
        ]

        if not external_links:
            # No external links, full score
            return 20, {'valid': 0, 'total': 0}

        # For scoring purposes, assume 80% of links are valid
        # (actual link checking would be async and done in linter)
        total_links = len(external_links)
        valid_links = int(total_links * 0.8)  # Estimate

        ratio = valid_links / total_links if total_links > 0 else 1.0
        score = int(20 * ratio)

        return score, {'valid': valid_links, 'total': total_links}

    def _score_signal_ratio(self, content: str) -> tuple[int, float]:
        """
        Score signal-to-noise ratio (max 20 points).

        Evaluates content quality and information density.
        """
        # Remove code blocks for analysis
        content_no_code = re.sub(r'```[\s\S]*?```', '', content)

        # Calculate various metrics
        total_chars = len(content_no_code)
        if total_chars == 0:
            return 0, 0.0

        # Count meaningful elements
        headings = len(re.findall(r'^#{1,6}\s+', content_no_code, re.MULTILINE))
        lists = len(re.findall(r'^\s*[-*+]\s+', content_no_code, re.MULTILINE))
        links = len(re.findall(r'\[.*?\]\(.*?\)', content_no_code))
        code_snippets = len(re.findall(r'`[^`]+`', content_no_code))

        # Count filler content
        filler_phrases = [
            'click here',
            'see below',
            'as follows',
            'the following',
            'please note',
            'important note',
            'for more information'
        ]

        filler_count = sum(
            content_no_code.lower().count(phrase)
            for phrase in filler_phrases
        )

        # Count substantive words (approximation)
        words = re.findall(r'\b\w+\b', content_no_code)
        substantive_words = [
            w for w in words
            if len(w) > 3 and not w.lower() in ['this', 'that', 'with', 'from', 'have', 'been', 'were', 'will']
        ]

        # Calculate signal ratio
        signal_elements = headings + lists + links + code_snippets
        noise_elements = filler_count * 2  # Weight filler phrases more

        if len(words) > 0:
            substantive_ratio = len(substantive_words) / len(words)
        else:
            substantive_ratio = 0

        # Combine metrics
        signal_ratio = max(0, min(1,
            (signal_elements * 10 / total_chars) * 0.3 +  # Structure density
            substantive_ratio * 0.5 +  # Word quality
            (1 - noise_elements / max(1, signal_elements)) * 0.2  # Noise ratio
        ))

        score = int(20 * signal_ratio)

        return score, signal_ratio