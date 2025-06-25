# Hackathon Technical Implementation - WordPress with Elementor

> **Dashboard-Inspired API & Data Model (NEW)**
>
> The WordPress hackathon judging system should follow the same API-driven, modular approach as the canonical dashboard implementation. See the new [API Reference](./api-reference.md) and [Data Model](./data-model.md) pages for recommended endpoints, field definitions, and data structures. These are designed for drop-in compatibility with the React/static frontend and are kept in sync with the canonical system.
>
> - All endpoints should be under `/wp-json/hackathon/v1/` and match the canonical API.
> - All fields and data models should match [hackathon-show-config.md](../hackathon-show-config.md) and [dashboard/app.py](../../scripts/hackathon/dashboard/app.py).
> - This section is a living document—update as the implementation evolves.

> **Philosophy & Canonical Reference**
>
> This document describes an alternative WordPress-based implementation for the Clank Tank Hackathon judging system. The canonical, production-ready system is implemented in Python/SQLite/React (see [PROGRESS.md](../github-issues/PROGRESS.md), [PLAN.md](../github-issues/PLAN.md), and [hackathon-show-config.md](../hackathon-show-config.md)).
>
> - **This guide is for reference and experimental use.**
> - For all schemas, field definitions, and judge logic, the above docs are the source of truth.
> - The recommended handoff is a 'Final Judgement' object (scores, feedback, verdicts), not a full episode JSON.
> - See [episode-format.md](../episode-format.md) for the unified episode format and handoff details.

---

## Architecture Overview

```
Elementor Form → Custom Post Type → WP REST API → AI Processing → Judge Scoring
                                          ↓               ↓
                                  Discord Webhook    Admin Dashboard
```

## 1. WordPress Plugin Structure

```
clank-tank-hackathon/
├── clank-tank-hackathon.php      # Main plugin file
├── includes/
│   ├── post-types.php            # Custom post type registration
│   ├── api-endpoints.php         # REST API routes
│   ├── ai-integration.php        # OpenRouter/AI calls
│   ├── discord-integration.php   # Discord webhook handler
│   ├── scoring-system.php        # Judge scoring logic
│   ├── admin-panel.php           # Admin UI components
│   ├── elementor-widgets.php     # Custom Elementor widgets
│   └── acf-fields.php            # ACF field definitions (if using ACF)
├── assets/
│   ├── css/
│   └── js/
└── templates/
    └── elementor/
        ├── submission-form.php
        └── leaderboard-widget.php
```

### Plugin Header

```php
<?php
/**
 * Plugin Name: Clank Tank Hackathon
 * Description: AI-powered hackathon judging system for WordPress
 * Version: 1.0.0
 * Author: Clank Tank Team
 * Text Domain: clank-tank-hackathon
 * Requires at least: 6.0
 * Requires PHP: 7.4
 * Elementor tested up to: 3.20.0
 * Elementor Pro tested up to: 3.20.0
 */

// Check for required plugins
add_action('admin_notices', function() {
    if (!class_exists('Elementor\Plugin')) {
        echo '<div class="notice notice-error"><p>Clank Tank Hackathon requires Elementor to be installed and activated.</p></div>';
    }
});
```

## 2. Elementor Form Integration

```php
// includes/elementor-widgets.php
use Elementor\Widget_Base;
use Elementor\Controls_Manager;

class Hackathon_Submission_Form extends Widget_Base {
    public function get_name() {
        return 'hackathon_submission';
    }
    
    public function get_title() {
        return 'Hackathon Submission Form';
    }
    
    protected function register_controls() {
        // Form field controls for Elementor editor
    }
}

// Hook into Elementor form submission
add_action('elementor_pro/forms/new_record', function($record, $handler) {
    $form_name = $record->get_form_settings('form_name');
    
    if ('Hackathon Submission' !== $form_name) {
        return;
    }
    
    $raw_fields = $record->get('fields');
    $fields = [];
    foreach ($raw_fields as $id => $field) {
        $fields[$id] = $field['value'];
    }
    
    // Create custom post
    $post_data = [
        'post_title' => $fields['project_name'],
        'post_content' => $fields['description'],
        'post_type' => 'hackathon_project',
        'post_status' => 'pending'
    ];
    
    $post_id = wp_insert_post($post_data);
    
    // Save all meta fields (update to match canonical fields)
    update_post_meta($post_id, '_team_info', [
        'name' => $fields['team_name'],
        'email' => $fields['email'],
        'discord' => $fields['discord'],
        'twitter' => $fields['twitter']
    ]);
    update_post_meta($post_id, '_project_urls', [
        'github' => $fields['github_url'],
        'demo_video' => $fields['demo_video_url'],
        'live_demo' => $fields['live_demo_url']
    ]);
    update_post_meta($post_id, '_category', $fields['category']);
    update_post_meta($post_id, '_status', 'submitted');
    update_post_meta($post_id, '_how_it_works', $fields['how_it_works']);
    update_post_meta($post_id, '_problem_solved', $fields['problem_solved']);
    update_post_meta($post_id, '_technical_highlights', $fields['technical_highlights']);
    update_post_meta($post_id, '_whats_next', $fields['whats_next']);
    
}, 10, 2);
```

## 3. Custom Post Type vs. Category

> **Note:** The canonical system uses a dedicated database. In WordPress, you may use a custom post type (`hackathon_project`) **or** a standard post with a special category. Using a custom post type is recommended for clarity and separation, but using a category may be simpler for some setups (see 'JedAI Council' workflow). Document your choice and keep field names consistent with the canonical system.

## 4. AI Research Integration

```php
// includes/ai-integration.php
class HackathonAIResearch {
    private $api_key;
    private $endpoint = 'https://openrouter.ai/api/v1/chat/completions';
    
    public function research_project($post_id) {
        $project = get_post($post_id);
        $meta = get_post_meta($post_id);
        
        $prompt = $this->build_research_prompt($project, $meta);
        
        $response = wp_remote_post($this->endpoint, [
            'headers' => [
                'Authorization' => 'Bearer ' . $this->api_key,
                'Content-Type' => 'application/json'
            ],
            'body' => json_encode([
                'model' => 'perplexity/sonar-small-online',
                'messages' => [['role' => 'user', 'content' => $prompt]]
            ])
        ]);
        
        $research = json_decode(wp_remote_retrieve_body($response), true);
        update_post_meta($post_id, '_ai_research', $research);
        
        return $research;
    }
}
```

## 5. Judge Scoring System

```php
// includes/scoring-system.php
class JudgeScoring {
    // All judges use same criteria but with different weights
    private $judge_weights = [
        'aimarc' => [
            'innovation' => 1.2,
            'technical_execution' => 0.8,
            'market_potential' => 1.5,
            'user_experience' => 1.0
        ],
        'aishaw' => [
            'innovation' => 1.0,
            'technical_execution' => 1.5,
            'market_potential' => 0.8,
            'user_experience' => 1.2
        ],
        'spartan' => [
            'innovation' => 0.7,
            'technical_execution' => 0.8,
            'market_potential' => 1.3,
            'user_experience' => 1.3
        ],
        'peepo' => [
            'innovation' => 1.3,
            'technical_execution' => 0.7,
            'market_potential' => 1.0,
            'user_experience' => 1.2
        ]
    ];
    
    public function calculate_weighted_score($post_id) {
        $scores = get_post_meta($post_id, '_judge_scores', true);
        $weighted_totals = [];
        
        foreach ($scores as $round => $round_scores) {
            foreach ($round_scores as $judge => $criteria_scores) {
                $weights = $this->judge_weights[$judge];
                $weighted_total = 0;
                
                foreach ($criteria_scores as $criterion => $score) {
                    $weighted_total += $score * $weights[$criterion];
                }
                
                $weighted_totals[$round][$judge] = $weighted_total;
            }
        }
        
        return $weighted_totals;
    }
}

> **Judge weights and criteria must match the canonical source:**
> See [hackathon-show-config.md](../hackathon-show-config.md) and [PROGRESS.md](../github-issues/PROGRESS.md) for the latest weights and scoring logic.
```

## 6. Elementor Leaderboard Widget

```php
// Custom Elementor widget for displaying leaderboard
class Hackathon_Leaderboard_Widget extends Widget_Base {
    
    public function get_name() {
        return 'hackathon_leaderboard';
    }
    
    public function get_title() {
        return 'Hackathon Leaderboard';
    }
    
    protected function render() {
        $settings = $this->get_settings_for_display();
        
        $projects = get_posts([
            'post_type' => 'hackathon_project',
            'posts_per_page' => -1,
            'meta_key' => '_total_score',
            'orderby' => 'meta_value_num',
            'order' => 'DESC'
        ]);
        ?>
        <div class="hackathon-leaderboard-widget">
            <table class="elementor-table">
                <thead>
                    <tr>
                        <th>Rank</th>
                        <th>Project</th>
                        <th>Team</th>
                        <th>Category</th>
                        <th>Score</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
                    <?php foreach ($projects as $index => $project): 
                        $team_info = get_post_meta($project->ID, '_team_info', true);
                        $urls = get_post_meta($project->ID, '_project_urls', true);
                    ?>
                    <tr>
                        <td class="rank-<?php echo $index + 1; ?>"><?php echo $index + 1; ?></td>
                        <td>
                            <a href="<?php echo get_permalink($project); ?>">
                                <?php echo get_the_title($project); ?>
                            </a>
                        </td>
                        <td><?php echo esc_html($team_info['name']); ?></td>
                        <td><?php echo get_post_meta($project->ID, '_category', true); ?></td>
                        <td><?php echo get_post_meta($project->ID, '_total_score', true); ?></td>
                        <td>
                            <a href="<?php echo esc_url($urls['demo_video']); ?>" class="elementor-button elementor-size-sm">
                                Watch Demo
                            </a>
                        </td>
                    </tr>
                    <?php endforeach; ?>
                </tbody>
            </table>
        </div>
        <?php
    }
}
```

## 7. Discord Integration

```php
// includes/discord-integration.php
add_action('rest_api_init', function() {
    register_rest_route('hackathon/v1', '/discord-webhook', [
        'methods' => 'POST',
        'callback' => 'handle_discord_webhook',
        'permission_callback' => '__return_true',
        'args' => [
            'type' => [
                'required' => true,
                'type' => 'string',
                'enum' => ['reaction', 'comment', 'vote']
            ],
            'project_id' => [
                'required' => true,
                'type' => 'integer',
                'validate_callback' => function($param) {
                    return get_post($param) !== null;
                }
            ],
            'reaction' => [
                'type' => 'string',
                'enum' => ['check', 'hundred', 'moneybag', 'fire']
            ],
            'user_id' => [
                'required' => true,
                'type' => 'string'
            ]
        ]
    ]);
});

function handle_discord_webhook($request) {
    $data = $request->get_json_params();
    
    // Process Discord reactions/votes
    if ($data['type'] === 'reaction') {
        $project_id = $data['project_id'];
        $reaction = $data['reaction'];
        $user_id = $data['user_id'];
        
        // Update community feedback
        $feedback = get_post_meta($project_id, '_community_feedback', true) ?: [];
        $feedback['reactions'][$reaction][] = $user_id;
        
        update_post_meta($project_id, '_community_feedback', $feedback);
    }
    
    return new WP_REST_Response(['status' => 'success'], 200);
}

> **Community bonus calculation and Discord bot logic:**
> For anti-spam, session independence, and bonus scoring, see [PROGRESS.md](../github-issues/PROGRESS.md) and the Discord bot implementation in the canonical system.
```

## 8. Admin Dashboard

```php
// includes/admin-panel.php
class HackathonAdminPanel {
    public function __construct() {
        add_action('admin_menu', [$this, 'add_menu_pages']);
    }
    
    public function add_menu_pages() {
        add_menu_page(
            'Hackathon Dashboard',
            'Hackathon',
            'manage_options',
            'hackathon-dashboard',
            [$this, 'render_dashboard'],
            'dashicons-awards',
            30
        );
        
        add_submenu_page(
            'hackathon-dashboard',
            'Judge Scoring',
            'Scoring',
            'manage_options',
            'hackathon-scoring',
            [$this, 'render_scoring_page']
        );
    }
    
    public function render_dashboard() {
        // Dashboard with project stats, status overview
        ?>
        <div class="wrap">
            <h1>Hackathon Dashboard</h1>
            
            <!-- Status Cards -->
            <div class="hackathon-stats" style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px; margin: 20px 0;">
                <div class="stat-card" style="background: #fff; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                    <h3>Total Submissions</h3>
                    <p style="font-size: 2em; margin: 0;"><?php echo $this->get_submission_count(); ?></p>
                </div>
                <div class="stat-card" style="background: #fff; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                    <h3>Pending Review</h3>
                    <p style="font-size: 2em; margin: 0;"><?php echo $this->get_pending_count(); ?></p>
                </div>
                <div class="stat-card" style="background: #fff; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                    <h3>Round 1 Complete</h3>
                    <p style="font-size: 2em; margin: 0;"><?php echo $this->get_round1_count(); ?></p>
                </div>
                <div class="stat-card" style="background: #fff; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                    <h3>Final Scores</h3>
                    <p style="font-size: 2em; margin: 0;"><?php echo $this->get_completed_count(); ?></p>
                </div>
            </div>
            
            <div class="recent-submissions">
                <?php $this->display_recent_submissions(); ?>
            </div>
        </div>
        <?php
    }
}
```

## 9. Automated Processing

```php
// WP-Cron for automated judging
add_action('init', function() {
    if (!wp_next_scheduled('process_hackathon_submissions')) {
        wp_schedule_event(time(), 'hourly', 'process_hackathon_submissions');
    }
});

add_action('process_hackathon_submissions', function() {
    // Get pending submissions
    $args = [
        'post_type' => 'hackathon_project',
        'meta_key' => '_status',
        'meta_value' => 'submitted',
        'posts_per_page' => 5 // Process 5 at a time
    ];
    
    $query = new WP_Query($args);
    
    while ($query->have_posts()) {
        $query->the_post();
        $post_id = get_the_ID();
        
        // Run AI research
        $ai = new HackathonAIResearch();
        $ai->research_project($post_id);
        
        // Update status
        update_post_meta($post_id, '_status', 'researched');
    }
    
    wp_reset_postdata();
});
```

## 10. Elementor Page Templates

```php
// Create Elementor template for project display
add_filter('single_template', function($template) {
    global $post;
    
    if ($post->post_type === 'hackathon_project') {
        // Check if Elementor template exists
        $elementor_template = locate_template('single-hackathon_project.php');
        if ($elementor_template) {
            return $elementor_template;
        }
    }
    
    return $template;
});

// Dynamic tags for Elementor
add_action('elementor/dynamic_tags/register', function($dynamic_tags_manager) {
    $dynamic_tags_manager->register(new \Hackathon_Score_Tag());
    $dynamic_tags_manager->register(new \Hackathon_Judge_Comments_Tag());
    $dynamic_tags_manager->register(new \Hackathon_Community_Reactions_Tag());
});
```

## 11. Episode Generation & Handoff

> **Canonical Handoff:**
> The recommended output is a 'Final Judgement' object (scores, feedback, verdicts), not a full episode JSON. Show production should be a separate step/system. See [episode-format.md](../episode-format.md) and [PROGRESS.md](../github-issues/PROGRESS.md) for details.

```php
// Generate episode data for recording
function generate_episode_data($post_id, $round) {
    $project = get_post($post_id);
    $scores = get_post_meta($post_id, '_judge_scores', true);
    $research = get_post_meta($post_id, '_ai_research', true);
    $community = get_post_meta($post_id, '_community_feedback', true);
    
    $episode = [
        'show_id' => 'clank_tank_hackathon',
        'episode_id' => 'HTH_R' . $round . '_' . $post_id,
        'title' => get_the_title($post_id),
        'scenes' => generate_judging_scenes($project, $scores, $research, $community, $round)
    ];
    
    // Save for external recording system
    update_post_meta($post_id, '_episode_data_round_' . $round, $episode);
    
    // Or export to JSON file
    $upload_dir = wp_upload_dir();
    $file_path = $upload_dir['basedir'] . '/hackathon-episodes/round' . $round . '/' . $post_id . '.json';
    wp_mkdir_p(dirname($file_path));
    file_put_contents($file_path, json_encode($episode, JSON_PRETTY_PRINT));
    
    return $episode;
}
```

## 12. REST API Endpoints & Schemas

> **Reference:** Ensure all endpoints and payloads match the canonical system. Add any missing endpoints for 'final judgement' export as needed. See [PROGRESS.md](../github-issues/PROGRESS.md) for canonical API and schema.

### Available Endpoints

```
GET  /wp-json/wp/v2/hackathon-projects         - List all projects
GET  /wp-json/wp/v2/hackathon-projects/{id}    - Get single project
POST /wp-json/hackathon/v1/submit              - Submit new project
POST /wp-json/hackathon/v1/discord-webhook     - Discord reactions
GET  /wp-json/hackathon/v1/scores/{id}         - Get project scores
POST /wp-json/hackathon/v1/judge/{id}          - Trigger AI judging
GET  /wp-json/hackathon/v1/leaderboard         - Get ranked projects
```

### REST API Response Schemas

```json
// GET /wp-json/wp/v2/hackathon-projects/{id}
{
    "id": 123,
    "date": "2024-01-15T12:00:00",
    "date_gmt": "2024-01-15T12:00:00",
    "guid": {
        "rendered": "https://m3org.com/tv/?post_type=hackathon_project&p=123"
    },
    "modified": "2024-01-16T14:30:00",
    "modified_gmt": "2024-01-16T14:30:00",
    "slug": "defi-lending-protocol",
    "status": "publish",
    "type": "hackathon_project",
    "link": "https://m3org.com/tv/hackathon/defi-lending-protocol/",
    "title": {
        "rendered": "DeFi Lending Protocol"
    },
    "content": {
        "rendered": "<p>Project description...</p>",
        "protected": false
    },
    "excerpt": {
        "rendered": "<p>A decentralized lending platform...</p>",
        "protected": false
    },
    "author": 1,
    "featured_media": 456,
    "template": "",
    "meta": {
        "_team_info": {
            "name": "Team Alpha",
            "email": "team@example.com",
            "discord": "TeamAlpha#1234",
            "twitter": "@teamalpha"
        },
        "_project_urls": {
            "github": "https://github.com/team/project",
            "demo_video": "https://youtube.com/watch?v=...",
            "live_demo": "https://demo.example.com"
        },
        "_category": "DeFi",
        "_status": "round1_complete",
        "_total_score": 38.5
    },
    "acf": {
        "team_info": {
            "name": "Team Alpha",
            "email": "team@example.com",
            "discord": "TeamAlpha#1234",
            "twitter": "@teamalpha"
        },
        "project_urls": {
            "github": "https://github.com/team/project",
            "demo_video": "https://youtube.com/watch?v=...",
            "live_demo": "https://demo.example.com"
        },
        "category": "defi"
    },
    "_links": {
        "self": [
            {
                "href": "https://m3org.com/tv/wp-json/wp/v2/hackathon-projects/123",
                "targetHints": {
                    "allow": ["GET", "POST", "PUT", "PATCH", "DELETE"]
                }
            }
        ],
        "collection": [
            {
                "href": "https://m3org.com/tv/wp-json/wp/v2/hackathon-projects"
            }
        ],
        "about": [
            {
                "href": "https://m3org.com/tv/wp-json/wp/v2/types/hackathon_project"
            }
        ],
        "author": [
            {
                "embeddable": true,
                "href": "https://m3org.com/tv/wp-json/wp/v2/users/1"
            }
        ],
        "wp:featuredmedia": [
            {
                "embeddable": true,
                "href": "https://m3org.com/tv/wp-json/wp/v2/media/456"
            }
        ],
        "wp:attachment": [
            {
                "href": "https://m3org.com/tv/wp-json/wp/v2/media?parent=123"
            }
        ],
        "curies": [
            {
                "name": "wp",
                "href": "https://api.w.org/{rel}",
                "templated": true
            }
        ]
    }
}

// GET /wp-json/hackathon/v1/scores/{id}
{
    "project_id": 123,
    "project_name": "DeFi Lending Protocol",
    "rounds": {
        "1": {
            "judges": {
                "aimarc": {
                    "raw_scores": {
                        "innovation": 8,
                        "technical_execution": 7,
                        "market_potential": 9,
                        "user_experience": 7
                    },
                    "weighted_total": 33.5
                },
                "aishaw": {
                    "raw_scores": {
                        "innovation": 7,
                        "technical_execution": 9,
                        "market_potential": 6,
                        "user_experience": 8
                    },
                    "weighted_total": 34.2
                }
                // ... other judges
            },
            "round_total": 135.7
        },
        "2": {
            // Round 2 scores with community feedback incorporated
        }
    },
    "community_bonus": 1.5,
    "final_score": 38.5
}

// GET /wp-json/hackathon/v1/leaderboard
{
    "projects": [
        {
            "rank": 1,
            "id": 123,
            "name": "DeFi Lending Protocol",
            "team": "Team Alpha",
            "category": "DeFi",
            "score": 38.5,
            "rounds_complete": 2
        },
        // ... more projects
    ],
    "total_projects": 25,
    "last_updated": "2024-01-01T12:00:00Z"
}
```

### Form Submission Schema

```json
// POST /wp-json/hackathon/v1/submit
{
    "project_name": "DeFi Lending Protocol",
    "description": "A decentralized lending platform...",
    "category": "DeFi",
    "team_name": "Team Alpha",
    "email": "team@example.com",
    "discord": "TeamAlpha#1234",
    "twitter": "@teamalpha",
    "github_url": "https://github.com/team/project",
    "demo_video_url": "https://youtube.com/watch?v=...",
    "live_demo_url": "https://demo.example.com",
    "how_it_works": "Our platform uses smart contracts...",
    "problem_solved": "Traditional lending is slow and expensive...",
    "technical_highlights": "We implemented a novel liquidation mechanism...",
    "whats_next": "We plan to add cross-chain support..."
}
```

## Benefits of WordPress + Elementor Approach

1. **Visual Form Builder**: Use Elementor's form widget with custom actions
2. **Drag-and-Drop Pages**: Create submission pages and leaderboards visually
3. **Dynamic Content**: Use Elementor's dynamic tags for project data
4. **Responsive Design**: Built-in mobile optimization
5. **User-Friendly**: Non-developers can modify layouts and content
6. **Template System**: Create reusable templates for project displays
7. **Popup Integration**: Use Elementor popups for voting/feedback
8. **Performance**: Elementor's optimization features for fast loading

## WordPress Environment Notes

Based on your m3org.com/tv setup:

1. **Existing Infrastructure**:
   - WordPress with standard REST API structure
   - Elementor Pro installed (confirmed by `elementor_library` post type)
   - ACF (Advanced Custom Fields) available for field management
   - Standard post types only (no custom hackathon types yet)

2. **Implementation Recommendations**:
   - Use ACF for managing hackathon fields (cleaner UI than raw meta)
   - Leverage Elementor Pro's form actions for submission handling
   - Build on existing REST API patterns from your site
   - Consider using existing post categories vs custom post type for simpler setup

3. **Quick Start Path**:
   - Create ACF field group for hackathon submissions
   - Use Elementor form with custom webhook action
   - Store in regular posts with specific category
   - Add custom REST endpoints only where needed

## Developer Notes on Existing M3 TV WordPress Integration

> **Legacy/Experimental:** The following notes reflect the original WordPress integration and may not match the current canonical system. Use for reference only.

### Existing JedAI Council Workflow in WordPress

- **Content Structure**: Episodes are standard WordPress `POSTS`. The show title (e.g., "JedAI Council") is the post `CATEGORY`.
- **Data Storage**:
    - The full episode JSON is stored in the post's main `CONTENT` field.
    - The post's built-in `EXCERPT` field is used for the episode description.
    - The `FEATURED IMAGE` is used for the episode thumbnail.
- **Metadata**: Show-specific metadata (like YouTube URL, character summaries) is managed via the **Advanced Custom Fields (ACF)** plugin. These fields are visible at the bottom of the post edit screen.
- **API and Automation**:
    - Posts and ACF metadata can be edited via the standard WordPress REST API.
    - A custom endpoint exists for episode submission, which intelligently extracts specific data from the main episode JSON and populates the corresponding ACF fields for easier filtering and indexing.

### Critical Reflection on Hackathon Episode Generation

A key insight from reviewing the existing system is a potential flaw in our current hackathon pipeline design:

> **"Your judging system shouldn't generate shmotime JSON. You should just judge it in a legit hive mind. Then give the write-up of their judgement to the episode generator."**

This suggests our current plan for `scripts/hackathon/generate_episode.py` might be overly complex and could violate the "separate system" principle at the presentation layer.

**Proposed Philosophical Shift:**

1.  The hackathon scripts (`hackathon_research.py`, `hackathon_manager.py`, `discord_bot.py`, etc.) should have **one final output**: a structured block of text or simple JSON object representing the **"Final Judgement"**. This would contain the scores, the community feedback summary, and the judges' final verdict paragraphs.
2.  This "Final Judgement" artifact would then be passed to a **completely separate episode generation system** (like the existing Clank Tank one).
3.  This creates a cleaner handoff. The hackathon system is responsible only for **judging**, not for **show production**. This strengthens our core architectural goal of separation.