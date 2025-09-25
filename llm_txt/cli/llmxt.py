#!/usr/bin/env python3
"""llmxt - Cross-platform CLI for generating llm.txt from documentation repositories."""

import asyncio
import json
import logging
import os
import sys
import tempfile
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import click
import yaml
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('llmxt')


class LLMXTConfig:
    """Configuration for llmxt CLI."""

    def __init__(self, config_path: Optional[Path] = None):
        self.config_path = config_path or Path('llm.config.yml')
        self.config = self._load_config()

    def _load_config(self) -> Dict:
        """Load configuration from file or use defaults."""
        defaults = {
            'framework': 'auto',
            'include': ['**/*.md', '**/*.mdx'],
            'exclude': ['**/changelog/**', '**/drafts/**', '**/node_modules/**'],
            'priority': [
                'getting-started',
                'quickstart',
                'auth',
                'api',
                'config',
                'errors'
            ],
            'size_kb': 100,
            'blocked_paths': ['/admin', '/cart'],
            'redact': [r'(sk|pk)_(live|test)_[A-Za-z0-9]{16,}'],
            'output': {
                'llm': 'public/llm.txt',
                'full': 'public/llms-full.txt'
            },
            'reports': {
                'dir': 'reports'
            }
        }

        if self.config_path.exists():
            try:
                with open(self.config_path, 'r') as f:
                    user_config = yaml.safe_load(f) or {}
                # Merge user config with defaults
                defaults.update(user_config)
            except Exception as e:
                logger.warning(f"Could not load config from {self.config_path}: {e}")

        return defaults

    def save(self):
        """Save current configuration to file."""
        with open(self.config_path, 'w') as f:
            yaml.dump(self.config, f, default_flow_style=False)


@click.group()
@click.version_option(version='0.1.0', prog_name='llmxt')
@click.option('--config', type=click.Path(exists=False), help='Config file path')
@click.option('--quiet', is_flag=True, help='Suppress output')
@click.option('--json', 'output_json', is_flag=True, help='Output in JSON format')
@click.pass_context
def cli(ctx, config, quiet, output_json):
    """llmxt - Generate spec-compliant llm.txt from documentation repositories."""
    ctx.ensure_object(dict)
    ctx.obj['config_path'] = Path(config) if config else None
    ctx.obj['quiet'] = quiet
    ctx.obj['json'] = output_json

    if quiet:
        logging.getLogger().setLevel(logging.ERROR)


@cli.command()
@click.argument('path', type=click.Path(exists=True), default='.')
@click.option('--out', help='Output path for llm.txt')
@click.option('--full-out', help='Output path for llms-full.txt')
@click.option('--max-kb', type=int, help='Maximum size in KB')
@click.option('--include', multiple=True, help='Include patterns')
@click.option('--exclude', multiple=True, help='Exclude patterns')
@click.option('--framework', type=click.Choice(['auto', 'docusaurus', 'mkdocs', 'sphinx', 'starlight']))
@click.option('--fail-on', multiple=True, type=click.Choice(['oversize', 'blocked', 'broken-links', 'warnings']))
@click.pass_context
def gen(ctx, path, out, full_out, max_kb, include, exclude, framework, fail_on):
    """Build llm.txt from repo files (framework-aware)."""
    config = LLMXTConfig(ctx.obj.get('config_path'))

    # Override config with CLI options
    if out:
        config.config['output']['llm'] = out
    if full_out:
        config.config['output']['full'] = full_out
    if max_kb:
        config.config['size_kb'] = max_kb
    if include:
        config.config['include'] = list(include)
    if exclude:
        config.config['exclude'] = list(exclude)
    if framework:
        config.config['framework'] = framework

    # Import here to avoid circular dependencies
    from ..frameworks import FrameworkDetector, get_framework_adapter
    from ..ingest import RepoIngestor
    from ..composer import LLMTxtComposer

    start_time = time.time()

    try:
        repo_path = Path(path).resolve()

        if ctx.obj.get('json'):
            output = {'status': 'starting', 'path': str(repo_path)}
            click.echo(json.dumps(output))
        else:
            click.echo(f"Processing repository: {repo_path}")

        # Detect framework
        if config.config['framework'] == 'auto':
            detector = FrameworkDetector()
            detected = detector.detect(repo_path)
            framework_name = detected or 'generic'
            if not ctx.obj.get('quiet'):
                click.echo(f"Detected framework: {framework_name}")
        else:
            framework_name = config.config['framework']

        # Get framework adapter
        adapter = get_framework_adapter(framework_name)

        # Ingest files
        ingestor = RepoIngestor(
            include_patterns=config.config['include'],
            exclude_patterns=config.config['exclude'],
            framework_adapter=adapter
        )

        pages = ingestor.ingest(repo_path)

        if not pages:
            raise click.ClickException("No documentation files found")

        if not ctx.obj.get('quiet'):
            click.echo(f"Found {len(pages)} documentation files")

        # Compose llm.txt
        composer = LLMTxtComposer(
            max_kb=config.config['size_kb'],
            priority_keywords=config.config['priority'],
            blocked_paths=config.config['blocked_paths'],
            redact_patterns=config.config['redact']
        )

        llm_content, trim_report = asyncio.run(
            composer.compose_with_budget(pages)
        )

        # Write llm.txt
        output_path = repo_path / config.config['output']['llm']
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(llm_content, encoding='utf-8')

        size_kb = len(llm_content.encode('utf-8')) / 1024

        # Write full version if configured
        if config.config['output'].get('full'):
            full_content = asyncio.run(composer.compose_full(pages))
            full_path = repo_path / config.config['output']['full']
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.write_text(full_content, encoding='utf-8')

        # Write reports
        reports_dir = repo_path / config.config['reports']['dir']
        reports_dir.mkdir(parents=True, exist_ok=True)

        trim_report_path = reports_dir / 'trim.json'
        trim_report_path.write_text(
            json.dumps(trim_report, indent=2),
            encoding='utf-8'
        )

        duration = time.time() - start_time

        # Check fail conditions
        exit_code = 0
        if fail_on:
            if 'oversize' in fail_on and size_kb > config.config['size_kb']:
                exit_code = 10
            if 'blocked' in fail_on and trim_report.get('blocked_content'):
                exit_code = 11

        if ctx.obj.get('json'):
            output = {
                'status': 'success',
                'files_processed': len(pages),
                'output_size_kb': round(size_kb, 1),
                'duration': round(duration, 1),
                'trimmed_sections': len(trim_report.get('trimmed', [])),
                'exit_code': exit_code
            }
            click.echo(json.dumps(output))
        else:
            click.echo(f"""
Generation complete!
   Files processed: {len(pages)}
   Output size: {size_kb:.1f} KB
   Duration: {duration:.1f}s
   Location: {output_path}
            """)

        sys.exit(exit_code)

    except Exception as e:
        if ctx.obj.get('json'):
            output = {'status': 'error', 'error': str(e)}
            click.echo(json.dumps(output))
        else:
            click.echo(f"Generation failed: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.argument('path', type=click.Path(exists=True), default='.')
@click.option('--fail-on', multiple=True, type=click.Choice(['oversize', 'blocked', 'broken-links', 'warnings']))
@click.pass_context
def lint(ctx, path, fail_on):
    """Validate existing outputs against rules."""
    config = LLMXTConfig(ctx.obj.get('config_path'))

    # Import linter module
    from ..lint import LLMTxtLinter

    try:
        repo_path = Path(path).resolve()
        llm_path = repo_path / config.config['output']['llm']

        if not llm_path.exists():
            raise click.ClickException(f"llm.txt not found at {llm_path}")

        linter = LLMTxtLinter(
            max_kb=config.config['size_kb'],
            blocked_paths=config.config['blocked_paths'],
            redact_patterns=config.config['redact']
        )

        results = asyncio.run(linter.lint(llm_path))

        # Determine exit code based on failures
        exit_code = 0
        if fail_on:
            if 'oversize' in fail_on and results['oversize']:
                exit_code = 10
            elif 'blocked' in fail_on and results['blocked_content']:
                exit_code = 11
            elif 'broken-links' in fail_on and results['broken_links']:
                exit_code = 12
            elif 'warnings' in fail_on and results['warnings']:
                exit_code = 13

        if ctx.obj.get('json'):
            output = {
                'status': 'success' if exit_code == 0 else 'failed',
                'results': results,
                'exit_code': exit_code
            }
            click.echo(json.dumps(output))
        else:
            # Display results
            click.echo("\nLint Results:")
            click.echo(f"   Size: {'OVERSIZE' if results['oversize'] else 'OK'} ({results['size_kb']:.1f}/{config.config['size_kb']} KB)")
            click.echo(f"   Blocked paths: {'FOUND' if results['blocked_content'] else 'NONE'}")
            click.echo(f"   Secrets: {'FOUND' if results['secrets_found'] else 'NONE'}")
            click.echo(f"   Broken links: {'FOUND' if results['broken_links'] else 'NONE'}")
            click.echo(f"   Warnings: {len(results['warnings'])}")

            if results['warnings']:
                click.echo("\nWarnings:")
                for warning in results['warnings']:
                    click.echo(f"   - {warning}")

        sys.exit(exit_code)

    except Exception as e:
        if ctx.obj.get('json'):
            output = {'status': 'error', 'error': str(e)}
            click.echo(json.dumps(output))
        else:
            click.echo(f"Lint failed: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.argument('path', type=click.Path(exists=True), default='.')
@click.pass_context
def score(ctx, path):
    """Coverage/size/link health/overall score."""
    config = LLMXTConfig(ctx.obj.get('config_path'))

    # Import scoring module
    from ..score import LLMTxtScorer

    try:
        repo_path = Path(path).resolve()
        llm_path = repo_path / config.config['output']['llm']

        if not llm_path.exists():
            raise click.ClickException(f"llm.txt not found at {llm_path}")

        scorer = LLMTxtScorer(
            priority_keywords=config.config['priority']
        )

        results = asyncio.run(scorer.score(llm_path))

        if ctx.obj.get('json'):
            click.echo(json.dumps(results))
        else:
            click.echo(f"""
Quality Score: {results['score']}/100

   Coverage: {results['coverage_score']}/40
     {', '.join(f"{k}: {'YES' if v else 'NO'}" for k, v in results['topic_coverage'].items())}

   Size adherence: {results['size_score']}/20
     Current: {results['size_kb']:.1f} KB (limit: {config.config['size_kb']} KB)

   Link health: {results['link_health_score']}/20
     Valid: {results['valid_links']}/{results['total_links']}

   Signal ratio: {results['signal_score']}/20
     Content quality: {results['signal_ratio']:.1%}
            """)

        # Save score report
        reports_dir = repo_path / config.config['reports']['dir']
        reports_dir.mkdir(parents=True, exist_ok=True)
        score_report_path = reports_dir / 'score.json'
        score_report_path.write_text(
            json.dumps(results, indent=2),
            encoding='utf-8'
        )

    except Exception as e:
        if ctx.obj.get('json'):
            output = {'status': 'error', 'error': str(e)}
            click.echo(json.dumps(output))
        else:
            click.echo(f"Score calculation failed: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.argument('path', type=click.Path(exists=True), default='.')
@click.pass_context
def diff(ctx, path):
    """Show diff between current and would-be output."""
    config = LLMXTConfig(ctx.obj.get('config_path'))

    try:
        repo_path = Path(path).resolve()
        current_path = repo_path / config.config['output']['llm']

        # Generate new content in temp file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as tmp:
            # Run gen command to temp file
            ctx.invoke(gen, path=str(repo_path), out=tmp.name)
            temp_path = Path(tmp.name)

        # Compare files
        import difflib

        current_content = current_path.read_text() if current_path.exists() else ""
        new_content = temp_path.read_text()

        diff = difflib.unified_diff(
            current_content.splitlines(keepends=True),
            new_content.splitlines(keepends=True),
            fromfile='current/llm.txt',
            tofile='new/llm.txt'
        )

        diff_text = ''.join(diff)

        if ctx.obj.get('json'):
            output = {
                'has_changes': bool(diff_text),
                'current_size': len(current_content),
                'new_size': len(new_content),
                'diff': diff_text
            }
            click.echo(json.dumps(output))
        else:
            if diff_text:
                click.echo("Changes detected:\n")
                click.echo(diff_text)
            else:
                click.echo("No changes detected")

        # Cleanup
        temp_path.unlink()

    except Exception as e:
        if ctx.obj.get('json'):
            output = {'status': 'error', 'error': str(e)}
            click.echo(json.dumps(output))
        else:
            click.echo(f"Diff generation failed: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.argument('url')
@click.option('--max-pages', type=int, default=50, help='Maximum pages to crawl')
@click.option('--max-depth', type=int, default=3, help='Maximum crawl depth')
@click.option('--out', default='llm.txt', help='Output path')
@click.option('--full-out', help='Full output path')
@click.pass_context
def crawl(ctx, url, max_pages, max_depth, out, full_out):
    """Polite crawl → llm.txt (fallback for external docs)."""
    config = LLMXTConfig(ctx.obj.get('config_path'))

    # Import crawler
    from ..crawler.sync_wrapper import WebCrawlerSync
    from ..crawler import CrawlConfig
    from ..composer import LLMTxtComposer

    try:
        if not ctx.obj.get('quiet'):
            click.echo(f"Crawling: {url}")

        # Configure crawler
        crawl_config = CrawlConfig(
            max_pages=max_pages,
            max_depth=max_depth,
            request_delay=1.0,
            respect_robots=True
        )

        crawler = WebCrawlerSync(crawl_config)
        result = crawler.crawl(url)

        if not result.pages:
            raise click.ClickException("No pages could be crawled")

        if not ctx.obj.get('quiet'):
            click.echo(f"Crawled {len(result.pages)} pages")

            if result.blocked_urls:
                click.echo(f"{len(result.blocked_urls)} URLs blocked by robots.txt")

        # Compose content
        composer = LLMTxtComposer(
            max_kb=config.config['size_kb'],
            priority_keywords=config.config['priority']
        )

        llm_content = asyncio.run(composer.compose_llm_txt(result.pages))

        # Write output
        output_path = Path(out)
        output_path.write_text(llm_content, encoding='utf-8')

        size_kb = len(llm_content.encode('utf-8')) / 1024

        if full_out:
            full_content = asyncio.run(composer.compose_llms_full_txt(result.pages))
            Path(full_out).write_text(full_content, encoding='utf-8')

        if ctx.obj.get('json'):
            output = {
                'status': 'success',
                'pages_crawled': len(result.pages),
                'output_size_kb': round(size_kb, 1),
                'duration': round(result.duration, 1)
            }
            click.echo(json.dumps(output))
        else:
            click.echo(f"""
Crawl complete!
   Pages: {len(result.pages)}
   Size: {size_kb:.1f} KB
   Duration: {result.duration:.1f}s
   Output: {output_path}
            """)

    except Exception as e:
        if ctx.obj.get('json'):
            output = {'status': 'error', 'error': str(e)}
            click.echo(json.dumps(output))
        else:
            click.echo(f"Crawl failed: {e}", err=True)
        sys.exit(1)


@cli.command()
def doctor():
    """Env & config checks."""
    config = LLMXTConfig()

    checks = []

    # Check Python version
    py_version = f"{sys.version_info.major}.{sys.version_info.minor}"
    checks.append({
        'name': 'Python version',
        'status': sys.version_info >= (3, 9),
        'info': py_version
    })

    # Check config file
    checks.append({
        'name': 'Config file',
        'status': config.config_path.exists(),
        'info': str(config.config_path)
    })

    # Check required modules
    required_modules = [
        'click', 'yaml', 'requests', 'bs4',
        'markdownify', 'aiohttp', 'playwright'
    ]

    for module in required_modules:
        try:
            __import__(module)
            checks.append({
                'name': f'Module: {module}',
                'status': True,
                'info': 'installed'
            })
        except ImportError:
            checks.append({
                'name': f'Module: {module}',
                'status': False,
                'info': 'not installed'
            })

    # Check GitHub token if available
    github_token_path = Path.home() / '.llmxt' / 'github.token'
    checks.append({
        'name': 'GitHub token',
        'status': github_token_path.exists(),
        'info': 'configured' if github_token_path.exists() else 'not configured'
    })

    # Display results
    click.echo("\nSystem Check Results:\n")

    all_ok = True
    for check in checks:
        status_icon = "[OK]" if check['status'] else "[FAIL]"
        click.echo(f"{status_icon} {check['name']}: {check['info']}")
        if not check['status']:
            all_ok = False

    if all_ok:
        click.echo("\nAll checks passed! System is ready.")
    else:
        click.echo("\nSome checks failed. Please fix the issues above.")
        sys.exit(1)


# GitHub commands group
@cli.group()
def github():
    """GitHub integration commands."""
    pass


@github.command()
@click.pass_context
def login(ctx):
    """Authenticate via GitHub device flow."""
    from ..github import GitHubAuth

    try:
        auth = GitHubAuth()

        if not ctx.obj.get('quiet'):
            click.echo("Starting GitHub device flow authentication...")

        # Get client ID from environment or config
        client_id = os.getenv('GH_APP_CLIENT_ID')
        if not client_id:
            client_id = click.prompt('Enter GitHub App Client ID')

        success = asyncio.run(auth.device_flow_login(client_id))

        if success:
            click.echo("Successfully authenticated!")
        else:
            click.echo("Authentication failed", err=True)
            sys.exit(1)

    except Exception as e:
        click.echo(f"Login failed: {e}", err=True)
        sys.exit(1)


@github.command()
@click.pass_context
def whoami(ctx):
    """Verify GitHub identity."""
    from ..github import GitHubAuth

    try:
        auth = GitHubAuth()
        user = asyncio.run(auth.get_user())

        if user:
            if ctx.obj.get('json'):
                click.echo(json.dumps(user))
            else:
                click.echo(f"Logged in as: {user['login']}")
                click.echo(f"   Name: {user.get('name', 'N/A')}")
                click.echo(f"   Email: {user.get('email', 'N/A')}")
        else:
            click.echo("Not authenticated. Run 'llmxt github login' first.", err=True)
            sys.exit(1)

    except Exception as e:
        click.echo(f"Failed to get user info: {e}", err=True)
        sys.exit(1)


@github.command()
@click.option('--owner', help='Repository owner')
@click.option('--repo', help='Repository name')
@click.option('--dry-run', is_flag=True, help='Show what would be done')
@click.pass_context
def pr(ctx, owner, repo, dry_run):
    """Create/update PR adding public/llm.txt."""
    from ..github import GitHubPR

    try:
        config = LLMXTConfig(ctx.obj.get('config_path'))

        # Get repo info
        if not owner or not repo:
            # Try to detect from git remote
            import subprocess
            result = subprocess.run(
                ['git', 'remote', 'get-url', 'origin'],
                capture_output=True, text=True
            )
            if result.returncode == 0:
                url = result.stdout.strip()
                # Parse GitHub URL
                import re
                match = re.search(r'github\.com[:/]([^/]+)/([^/.]+)', url)
                if match:
                    owner = owner or match.group(1)
                    repo = repo or match.group(2).replace('.git', '')

        if not owner or not repo:
            raise click.ClickException("Could not determine repository. Specify --owner and --repo")

        pr_manager = GitHubPR(owner, repo)

        # Check for existing llm.txt
        llm_path = Path('.') / config.config['output']['llm']
        if not llm_path.exists():
            click.echo("No llm.txt found. Generating first...")
            ctx.invoke(gen)

        if dry_run:
            click.echo(f"Dry run - would create PR for {owner}/{repo}")
            click.echo(f"   Files to add: {config.config['output']['llm']}")
            if config.config['output'].get('full'):
                click.echo(f"                {config.config['output']['full']}")
        else:
            pr_url = asyncio.run(pr_manager.create_or_update_pr(
                llm_path=llm_path,
                full_path=Path(config.config['output']['full']) if config.config['output'].get('full') else None,
                reports_dir=Path(config.config['reports']['dir'])
            ))

            if pr_url:
                click.echo(f"PR created/updated: {pr_url}")
            else:
                click.echo("Failed to create PR", err=True)
                sys.exit(1)

    except Exception as e:
        click.echo(f"PR creation failed: {e}", err=True)
        sys.exit(1)


def main():
    """Main entry point for llmxt CLI."""
    cli(obj={})


if __name__ == '__main__':
    main()