#!/usr/bin/env python3
"""
GitHub repository analyzer for hackathon projects.
Analyzes code quality, structure, and technical details.
"""

import os
import json
import requests
import logging
from datetime import datetime, timedelta
from urllib.parse import urlparse
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class GitHubAnalyzer:
    def __init__(self, github_token=None):
        """Initialize with optional GitHub token for higher rate limits."""
        self.github_token = github_token or os.getenv('GITHUB_TOKEN')
        self.headers = {
            'Accept': 'application/vnd.github.v3+json'
        }
        if self.github_token:
            self.headers['Authorization'] = f'token {self.github_token}'
        self.base_url = 'https://api.github.com'
        
    def extract_repo_info(self, repo_url):
        """Extract owner and repo name from GitHub URL."""
        try:
            parsed = urlparse(repo_url)
            path_parts = parsed.path.strip('/').split('/')
            if len(path_parts) >= 2:
                return path_parts[0], path_parts[1]
            return None, None
        except Exception as e:
            logger.error(f"Error parsing repo URL: {e}")
            return None, None
    
    def get_repo_data(self, owner, repo):
        """Get basic repository data."""
        try:
            url = f"{self.base_url}/repos/{owner}/{repo}"
            resp = requests.get(url, headers=self.headers)
            
            if resp.status_code == 404:
                return {"error": "Repository not found"}
            elif resp.status_code == 403:
                return {"error": "Rate limit exceeded"}
            
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            logger.error(f"Error fetching repo data: {e}")
            return {"error": str(e)}
    
    def get_languages(self, owner, repo):
        """Get language breakdown for the repository."""
        try:
            url = f"{self.base_url}/repos/{owner}/{repo}/languages"
            resp = requests.get(url, headers=self.headers)
            resp.raise_for_status()
            
            languages = resp.json()
            total = sum(languages.values())
            
            if total > 0:
                return {
                    lang: {
                        'bytes': bytes_count,
                        'percentage': round((bytes_count / total) * 100, 2)
                    }
                    for lang, bytes_count in languages.items()
                }
            return {}
        except Exception as e:
            logger.error(f"Error fetching languages: {e}")
            return {}
    
    def get_recent_commits(self, owner, repo, days=3):
        """Get commit activity for the past N days (default 3 for vibe check)."""
        try:
            since = (datetime.now() - timedelta(days=days)).isoformat()
            url = f"{self.base_url}/repos/{owner}/{repo}/commits"
            params = {'since': since, 'per_page': 100}
            resp = requests.get(url, headers=self.headers, params=params)
            resp.raise_for_status()
            commits = resp.json()
            return {
                'commits_in_last_72h': len(commits)
            }
        except Exception as e:
            logger.error(f"Error fetching commits: {e}")
            return {'commits_in_last_72h': 0}

    def get_readme(self, owner, repo):
        """Get README content and analyze its structure."""
        try:
            url = f"{self.base_url}/repos/{owner}/{repo}/readme"
            resp = requests.get(url, headers=self.headers)
            
            if resp.status_code == 404:
                return {"exists": False}
            
            resp.raise_for_status()
            data = resp.json()
            
            import base64
            import re
            content = base64.b64decode(data['content']).decode('utf-8')
            
            # Look for common setup/run sections
            has_setup_section = bool(re.search(r'#+\s*(setup|installation|getting started|running)', content, re.IGNORECASE))

            return {
                "exists": True,
                "size": len(content),
                "word_count": len(content.split()),
                "has_sections": bool(content.count('#') > 3),
                "has_setup_section": has_setup_section,
                "has_license_section": 'license' in content.lower()
            }
        except Exception as e:
            logger.error(f"Error fetching README: {e}")
            return {"exists": False, "error": str(e)}
    
    def analyze_repository(self, repo_url):
        """Perform simple repository analysis for hackathon vibe check."""
        owner, repo = self.extract_repo_info(repo_url)
        if not owner or not repo:
            return {
                "error": "Invalid GitHub URL",
                "url": repo_url
            }
        logger.info(f"Analyzing repository: {owner}/{repo}")
        repo_data = self.get_repo_data(owner, repo)
        if "error" in repo_data:
            return repo_data
        analysis = {
            "url": repo_url,
            "owner": owner,
            "name": repo,
            "description": repo_data.get('description', ''),
            "created_at": repo_data.get('created_at', ''),
            "updated_at": repo_data.get('updated_at', ''),
            "license": repo_data.get('license', {}).get('name', 'None') if repo_data.get('license') else 'None',
            "readme_analysis": self.get_readme(owner, repo),
            "file_structure": self.get_file_structure(owner, repo),
            "commit_activity": self.get_recent_commits(owner, repo),
            "analyzed_at": datetime.now().isoformat()
        }
        analysis['quality_score'] = self.calculate_quality_score(analysis)
        return analysis

    def calculate_quality_score(self, analysis):
        """Simple, stable quality score for hackathon vibe check."""
        score = 0
        max_score = 100
        # README (5)
        readme = analysis.get('readme_analysis', {})
        if readme.get('exists'):
            score += 5
        # Buildability (10)
        structure = analysis.get('file_structure', {})
        if structure.get('has_ci') or structure.get('has_dockerfile'):
            score += 5
        if structure.get('has_package_json') or structure.get('has_requirements'):
            score += 5
        # Recent commit activity (10)
        commits = analysis.get('commit_activity', {})
        if commits.get('commits_in_last_72h', 0) > 0:
            score += 10
        # License (5)
        if analysis.get('license') != 'None':
            score += 5
        return min(score, max_score)

    # Remove or comment out deep analysis, relevance/context matching, most significant commit, and open issues checks for stability.

def main():
    """CLI interface for GitHub analyzer."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Analyze GitHub repository")
    parser.add_argument("repo_url", help="GitHub repository URL")
    parser.add_argument("--token", help="GitHub personal access token")
    parser.add_argument("--output", help="Output file for results (JSON)")
    
    args = parser.parse_args()
    
    analyzer = GitHubAnalyzer(github_token=args.token)
    results = analyzer.analyze_repository(args.repo_url)
    
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"Results saved to {args.output}")
    else:
        print(json.dumps(results, indent=2))

if __name__ == "__main__":
    main()