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
    
    def get_recent_commits(self, owner, repo, days=30):
        """Get commit activity for the past N days."""
        try:
            since = (datetime.now() - timedelta(days=days)).isoformat()
            url = f"{self.base_url}/repos/{owner}/{repo}/commits"
            params = {'since': since, 'per_page': 100}
            
            resp = requests.get(url, headers=self.headers, params=params)
            resp.raise_for_status()
            
            commits = resp.json()
            
            # Analyze commit patterns
            commit_analysis = {
                'total_commits': len(commits),
                'unique_authors': len(set(c['commit']['author']['name'] for c in commits if c['commit']['author'])),
                'daily_average': round(len(commits) / days, 2),
                'last_commit': commits[0]['commit']['author']['date'] if commits else None
            }
            
            return commit_analysis
        except Exception as e:
            logger.error(f"Error fetching commits: {e}")
            return {}
    
    def get_readme(self, owner, repo):
        """Get README content."""
        try:
            url = f"{self.base_url}/repos/{owner}/{repo}/readme"
            resp = requests.get(url, headers=self.headers)
            
            if resp.status_code == 404:
                return {"exists": False}
            
            resp.raise_for_status()
            data = resp.json()
            
            # Decode content
            import base64
            content = base64.b64decode(data['content']).decode('utf-8')
            
            return {
                "exists": True,
                "size": len(content),
                "word_count": len(content.split()),
                "has_sections": bool(content.count('#') > 3),
                "has_installation": 'install' in content.lower(),
                "has_usage": 'usage' in content.lower() or 'example' in content.lower(),
                "has_license_section": 'license' in content.lower()
            }
        except Exception as e:
            logger.error(f"Error fetching README: {e}")
            return {"exists": False, "error": str(e)}
    
    def get_file_structure(self, owner, repo):
        """Get basic file structure analysis."""
        try:
            url = f"{self.base_url}/repos/{owner}/{repo}/contents"
            resp = requests.get(url, headers=self.headers)
            resp.raise_for_status()
            
            contents = resp.json()
            
            structure = {
                'total_files': 0,
                'total_dirs': 0,
                'has_tests': False,
                'has_docs': False,
                'has_ci': False,
                'has_package_json': False,
                'has_requirements': False,
                'has_dockerfile': False
            }
            
            for item in contents:
                if item['type'] == 'file':
                    structure['total_files'] += 1
                    
                    # Check for specific files
                    name_lower = item['name'].lower()
                    if name_lower == 'package.json':
                        structure['has_package_json'] = True
                    elif name_lower in ['requirements.txt', 'requirements.pip']:
                        structure['has_requirements'] = True
                    elif name_lower == 'dockerfile':
                        structure['has_dockerfile'] = True
                        
                elif item['type'] == 'dir':
                    structure['total_dirs'] += 1
                    
                    # Check for specific directories
                    name_lower = item['name'].lower()
                    if name_lower in ['test', 'tests', '__tests__']:
                        structure['has_tests'] = True
                    elif name_lower in ['docs', 'documentation']:
                        structure['has_docs'] = True
                    elif name_lower in ['.github', '.circleci', '.travis']:
                        structure['has_ci'] = True
            
            return structure
        except Exception as e:
            logger.error(f"Error fetching file structure: {e}")
            return {}
    
    def analyze_repository(self, repo_url):
        """Perform complete repository analysis."""
        owner, repo = self.extract_repo_info(repo_url)
        
        if not owner or not repo:
            return {
                "error": "Invalid GitHub URL",
                "url": repo_url
            }
        
        logger.info(f"Analyzing repository: {owner}/{repo}")
        
        # Get all data
        repo_data = self.get_repo_data(owner, repo)
        
        if "error" in repo_data:
            return repo_data
        
        # Gather all analysis data
        analysis = {
            "url": repo_url,
            "owner": owner,
            "name": repo,
            "description": repo_data.get('description', ''),
            "created_at": repo_data.get('created_at', ''),
            "updated_at": repo_data.get('updated_at', ''),
            "stars": repo_data.get('stargazers_count', 0),
            "forks": repo_data.get('forks_count', 0),
            "open_issues": repo_data.get('open_issues_count', 0),
            "license": repo_data.get('license', {}).get('name', 'None') if repo_data.get('license') else 'None',
            "default_branch": repo_data.get('default_branch', 'main'),
            "size_kb": repo_data.get('size', 0),
            "languages": self.get_languages(owner, repo),
            "commit_activity": self.get_recent_commits(owner, repo),
            "readme_analysis": self.get_readme(owner, repo),
            "file_structure": self.get_file_structure(owner, repo),
            "analyzed_at": datetime.now().isoformat()
        }
        
        # Calculate quality score
        analysis['quality_score'] = self.calculate_quality_score(analysis)
        
        return analysis
    
    def calculate_quality_score(self, analysis):
        """Calculate a quality score based on various factors."""
        score = 0
        max_score = 100
        
        # README quality (20 points)
        readme = analysis.get('readme_analysis', {})
        if readme.get('exists'):
            score += 5
            if readme.get('word_count', 0) > 100:
                score += 5
            if readme.get('has_sections'):
                score += 5
            if readme.get('has_usage'):
                score += 5
        
        # Code structure (20 points)
        structure = analysis.get('file_structure', {})
        if structure.get('has_tests'):
            score += 10
        if structure.get('has_docs'):
            score += 5
        if structure.get('has_ci'):
            score += 5
        
        # Activity (20 points)
        commits = analysis.get('commit_activity', {})
        if commits.get('total_commits', 0) > 10:
            score += 10
        if commits.get('unique_authors', 0) > 1:
            score += 5
        if commits.get('daily_average', 0) > 0.5:
            score += 5
        
        # Community (20 points)
        if analysis.get('stars', 0) > 0:
            score += 5
        if analysis.get('forks', 0) > 0:
            score += 5
        if analysis.get('license') != 'None':
            score += 10
        
        # Technical diversity (20 points)
        languages = analysis.get('languages', {})
        if len(languages) > 1:
            score += 10
        if len(languages) > 3:
            score += 10
        
        return min(score, max_score)

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