import { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { Copy, Check, RefreshCw } from 'lucide-react';
import { useCopyToClipboard } from '../../hooks/useCopyToClipboard';

interface TemplateData {
  project_name: string;
  team_name: string;
  category: string;
  description: string;
  how_it_works: string;
  problem_solved: string;
  coolest_tech: string;
  next_steps: string;
  github_url: string;
  demo_video_url: string;
  live_demo_url: string;
}

const DEFAULT_TEMPLATE: TemplateData = {
  project_name: '',
  team_name: '',
  category: '',
  description: '',
  how_it_works: '',
  problem_solved: '',
  coolest_tech: '',
  next_steps: '',
  github_url: '',
  demo_video_url: '',
  live_demo_url: '',
};

const STARTER_TEMPLATES: Record<string, TemplateData> = {
  defi: {
    project_name: 'DeFi Yield Optimizer',
    team_name: 'Yield Hunters',
    category: 'DeFi',
    description: 'An AI-powered DeFi yield optimization platform that automatically finds and compounds the best yields across multiple protocols.',
    how_it_works: 'Our AI analyzes real-time yield data across 50+ DeFi protocols, calculates optimal allocation strategies considering gas costs and risk factors, then executes automated rebalancing.',
    problem_solved: 'Manual yield farming is time-consuming and often suboptimal. Users miss opportunities and struggle with complex multi-protocol strategies.',
    coolest_tech: 'Advanced AI models for yield prediction, automated smart contract execution, and cross-chain liquidity optimization.',
    next_steps: 'Integrate with more L2 chains, add advanced risk scoring, and develop mobile app for yield monitoring.',
    github_url: 'https://github.com/yourteam/defi-yield-optimizer',
    demo_video_url: 'https://www.youtube.com/watch?v=demo',
    live_demo_url: 'https://defi-optimizer-demo.vercel.app',
  },
  ai: {
    project_name: 'AI Code Review Assistant',
    team_name: 'Code Guardians',
    category: 'AI',
    description: 'An intelligent code review assistant that provides detailed feedback, suggests improvements, and catches security vulnerabilities.',
    how_it_works: 'Uses fine-tuned language models trained on millions of code reviews to analyze pull requests and provide human-like feedback with actionable suggestions.',
    problem_solved: 'Code reviews are bottlenecks in development. Junior developers need guidance, and senior developers spend too much time on routine reviews.',
    coolest_tech: 'Custom transformer models for code analysis, AST parsing for deep semantic understanding, and integration with popular version control systems.',
    next_steps: 'Add support for more programming languages, implement team-specific style learning, and create IDE plugins.',
    github_url: 'https://github.com/yourteam/ai-code-reviewer',
    demo_video_url: 'https://www.youtube.com/watch?v=demo',
    live_demo_url: 'https://ai-code-reviewer.herokuapp.com',
  },
  gaming: {
    project_name: 'Blockchain Battle Royale',
    team_name: 'Chain Warriors',
    category: 'Gaming',
    description: 'A skill-based battle royale game where players can earn, trade, and own in-game assets as NFTs on the blockchain.',
    how_it_works: 'Players compete in matches where weapons, skins, and achievements are minted as NFTs. Winners earn tokens that can be used to upgrade gear or trade on our marketplace.',
    problem_solved: 'Traditional games lock players out of true ownership of their achievements and investments. We enable real digital ownership and rewards.',
    coolest_tech: 'Real-time multiplayer with blockchain integration, dynamic NFT generation based on gameplay, and a decentralized tournament system.',
    next_steps: 'Launch mobile version, create guild system with DAO governance, and integrate with major NFT marketplaces.',
    github_url: 'https://github.com/yourteam/blockchain-battle-royale',
    demo_video_url: 'https://www.youtube.com/watch?v=demo',
    live_demo_url: 'https://battle-royale-demo.com',
  }
};

/**
 * Experimental Templates Page - Real-time URL State Management
 * 
 * Features:
 * - Real-time URL updates as form fields change
 * - Form state recovery from URL parameters on page load
 * - Template preview and application system
 * - Clean URL sharing for collaboration
 */
export default function Templates() {
  const [searchParams, setSearchParams] = useSearchParams();
  const { copied, copyToClipboard } = useCopyToClipboard();
  
  // Initialize form data from URL or defaults
  const [formData, setFormData] = useState<TemplateData>(() => {
    const urlState = searchParams.get('draft');
    if (urlState) {
      try {
        return { ...DEFAULT_TEMPLATE, ...JSON.parse(decodeURIComponent(urlState)) };
      } catch {
        return DEFAULT_TEMPLATE;
      }
    }
    return DEFAULT_TEMPLATE;
  });

  const [selectedTemplate, setSelectedTemplate] = useState<string | null>(null);

  // Real-time URL updates when form changes
  useEffect(() => {
    const hasData = Object.values(formData).some(value => value.trim() !== '');
    
    if (hasData) {
      const cleanData = Object.fromEntries(
        Object.entries(formData).filter(([, value]) => value.trim() !== '')
      );
      const encodedState = encodeURIComponent(JSON.stringify(cleanData));
      setSearchParams({ draft: encodedState }, { replace: true });
    } else {
      setSearchParams({}, { replace: true });
    }
  }, [formData, setSearchParams]);

  const handleInputChange = (field: keyof TemplateData, value: string) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  const applyTemplate = (templateKey: string) => {
    const template = STARTER_TEMPLATES[templateKey];
    setFormData(template);
    setSelectedTemplate(null);
  };

  const clearForm = () => {
    setFormData(DEFAULT_TEMPLATE);
  };

  const getCurrentUrl = () => {
    return window.location.href;
  };

  const copyCurrentState = () => {
    copyToClipboard(getCurrentUrl(), 'Address copied!');
  };

  const hasFormData = Object.values(formData).some(value => value.trim() !== '');

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 py-8">
      <div className="max-w-6xl mx-auto px-4">
        {/* Header */}
        <div className="mb-8 text-center">
          <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100 mb-2">
            🧪 Templates Playground
          </h1>
          <p className="text-gray-600 dark:text-gray-400 mb-4">
            Real-time URL state management for collaborative form building
          </p>
          <div className="flex items-center justify-center gap-4 text-sm">
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 bg-green-500 rounded-full"></div>
              <span className="text-gray-700 dark:text-gray-300">Auto-save to URL</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 bg-blue-500 rounded-full"></div>
              <span className="text-gray-700 dark:text-gray-300">Shareable state</span>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Templates Sidebar */}
          <div className="lg:col-span-1">
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6">
              <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">
                Starter Templates
              </h2>
              
              <div className="space-y-3">
                {Object.entries(STARTER_TEMPLATES).map(([key, template]) => (
                  <div
                    key={key}
                    className="p-3 border border-gray-200 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors cursor-pointer"
                    onClick={() => setSelectedTemplate(key)}
                  >
                    <h3 className="font-medium text-gray-900 dark:text-gray-100 text-sm">
                      {template.project_name}
                    </h3>
                    <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                      {template.category} • {template.team_name}
                    </p>
                  </div>
                ))}
              </div>

              {/* URL State Controls */}
              <div className="mt-6 pt-6 border-t border-gray-200 dark:border-gray-600">
                <h3 className="text-sm font-medium text-gray-900 dark:text-gray-100 mb-3">
                  URL State
                </h3>
                <div className="space-y-2">
                  <button
                    onClick={copyCurrentState}
                    disabled={!hasFormData}
                    className="w-full flex items-center gap-2 px-3 py-2 text-xs bg-indigo-50 hover:bg-indigo-100 disabled:bg-gray-100 text-indigo-700 disabled:text-gray-400 rounded border border-indigo-200 disabled:border-gray-200 transition-colors"
                  >
                    {copied ? <Check className="w-3 h-3" /> : <Copy className="w-3 h-3" />}
                    Copy Current State
                  </button>
                  <button
                    onClick={clearForm}
                    disabled={!hasFormData}
                    className="w-full flex items-center gap-2 px-3 py-2 text-xs bg-gray-50 hover:bg-gray-100 disabled:bg-gray-100 text-gray-700 disabled:text-gray-400 rounded border border-gray-200 transition-colors"
                  >
                    <RefreshCw className="w-3 h-3" />
                    Clear Form
                  </button>
                </div>
              </div>
            </div>
          </div>

          {/* Main Form */}
          <div className="lg:col-span-2">
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6">
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
                  Project Form
                </h2>
                {hasFormData && (
                  <div className="flex items-center gap-2 text-xs text-green-600 dark:text-green-400">
                    <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
                    Auto-saved to URL
                  </div>
                )}
              </div>

              <div className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                      Project Name
                    </label>
                    <input
                      type="text"
                      value={formData.project_name}
                      onChange={(e) => handleInputChange('project_name', e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
                      placeholder="Enter project name..."
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                      Team Name
                    </label>
                    <input
                      type="text"
                      value={formData.team_name}
                      onChange={(e) => handleInputChange('team_name', e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
                      placeholder="Enter team name..."
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Category
                  </label>
                  <select
                    value={formData.category}
                    onChange={(e) => handleInputChange('category', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
                  >
                    <option value="">Select category...</option>
                    <option value="DeFi">DeFi</option>
                    <option value="AI">AI</option>
                    <option value="Gaming">Gaming</option>
                    <option value="Social">Social</option>
                    <option value="Infrastructure">Infrastructure</option>
                    <option value="Other">Other</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Description
                  </label>
                  <textarea
                    value={formData.description}
                    onChange={(e) => handleInputChange('description', e.target.value)}
                    rows={3}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
                    placeholder="Describe your project..."
                  />
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                      How it Works
                    </label>
                    <textarea
                      value={formData.how_it_works}
                      onChange={(e) => handleInputChange('how_it_works', e.target.value)}
                      rows={3}
                      className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
                      placeholder="Explain the technical implementation..."
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                      Problem Solved
                    </label>
                    <textarea
                      value={formData.problem_solved}
                      onChange={(e) => handleInputChange('problem_solved', e.target.value)}
                      rows={3}
                      className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
                      placeholder="What problem does this solve..."
                    />
                  </div>
                </div>

                <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                      GitHub URL
                    </label>
                    <input
                      type="url"
                      value={formData.github_url}
                      onChange={(e) => handleInputChange('github_url', e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
                      placeholder="https://github.com/..."
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                      Demo Video
                    </label>
                    <input
                      type="url"
                      value={formData.demo_video_url}
                      onChange={(e) => handleInputChange('demo_video_url', e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
                      placeholder="https://youtube.com/..."
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                      Live Demo
                    </label>
                    <input
                      type="url"
                      value={formData.live_demo_url}
                      onChange={(e) => handleInputChange('live_demo_url', e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
                      placeholder="https://demo.com/..."
                    />
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Template Preview Modal */}
        {selectedTemplate && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-2xl w-full m-4 max-h-[80vh] overflow-y-auto">
              <div className="p-6">
                <div className="flex items-center justify-between mb-4">
                  <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100">
                    Preview Template
                  </h2>
                  <button
                    onClick={() => setSelectedTemplate(null)}
                    className="text-gray-400 hover:text-gray-600 text-2xl"
                  >
                    ×
                  </button>
                </div>
                
                {STARTER_TEMPLATES[selectedTemplate] && (
                  <div className="space-y-4">
                    <div>
                      <h3 className="font-medium text-gray-900 dark:text-gray-100">
                        {STARTER_TEMPLATES[selectedTemplate].project_name}
                      </h3>
                      <p className="text-sm text-gray-500 dark:text-gray-400">
                        {STARTER_TEMPLATES[selectedTemplate].team_name} • {STARTER_TEMPLATES[selectedTemplate].category}
                      </p>
                    </div>
                    
                    <div className="text-sm text-gray-700 dark:text-gray-300">
                      <p className="mb-2">{STARTER_TEMPLATES[selectedTemplate].description}</p>
                      <p className="text-xs text-gray-500 dark:text-gray-400">
                        This template will populate all form fields. You can modify them after applying.
                      </p>
                    </div>
                    
                    <div className="flex gap-3 pt-4">
                      <button
                        onClick={() => applyTemplate(selectedTemplate)}
                        className="flex-1 bg-indigo-600 hover:bg-indigo-700 text-white px-4 py-2 rounded-md text-sm font-medium"
                      >
                        Apply Template
                      </button>
                      <button
                        onClick={() => setSelectedTemplate(null)}
                        className="flex-1 bg-gray-100 hover:bg-gray-200 text-gray-900 px-4 py-2 rounded-md text-sm font-medium"
                      >
                        Cancel
                      </button>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}