import re
import json
import statistics
import math
from collections import Counter, defaultdict
import logging

logger = logging.getLogger(__name__)

class IVRAnalytics:
    """
    Analyze IVR (Interactive Voice Response) transcripts and flowcharts
    to extract meaningful metrics and insights.
    """
    
    def __init__(self, transcript, flowchart):
        """
        Initialize IVR analytics with transcript and flowchart data
        
        Args:
            transcript (str): The transcribed IVR call text
            flowchart (str): The Mermaid flowchart representation
        """
        self.transcript = transcript
        self.flowchart = flowchart
        self.metrics = {}
        self._parse_flowchart()
        self.analyze()
    
    def _parse_flowchart(self):
        """Parse the Mermaid flowchart to extract nodes and connections"""
        self.nodes = []
        self.connections = []
        
        # Extract nodes (lines containing -->)
        node_pattern = r'(\w+)\s*\[(.*?)\]'
        connection_pattern = r'(\w+)\s*-->\s*(\w+)'
        
        # Find all nodes
        for match in re.finditer(node_pattern, self.flowchart):
            node_id, node_text = match.groups()
            self.nodes.append({
                'id': node_id,
                'text': node_text.strip('"')
            })
            
        # Find all connections
        for match in re.finditer(connection_pattern, self.flowchart):
            source, target = match.groups()
            self.connections.append({
                'source': source,
                'target': target
            })
    
    def analyze(self):
        """Run all analysis methods and collect metrics"""
        self.analyze_complexity()
        self.analyze_menu_options()
        self.analyze_potential_issues()
        self.analyze_sentiment()
        self.analyze_path_efficiency()
        self.analyze_customer_experience()
        self.analyze_best_practices()
        self.generate_recommendations()
        
    def analyze_complexity(self):
        """Analyze the complexity of the IVR system"""
        # Count nodes in flowchart
        node_count = len(self.nodes)
        
        # Count decision points (diamonds)
        decision_count = len(self.connections)
        
        # Count edges
        edge_count = len(self.connections)
        
        # Count levels (estimate depth)
        max_indent = 0
        for node in self.nodes:
            indent = len(node['text']) - len(node['text'].lstrip())
            max_indent = max(max_indent, indent)
        estimated_depth = max(1, max_indent // 2)
        
        # Calculate cyclomatic complexity (M = E - N + 2P)
        # where E is edges, N is nodes, P is connected components (assume 1)
        cyclomatic = edge_count - node_count + 2
        
        self.metrics['complexity'] = {
            'total_nodes': node_count,
            'decision_points': decision_count,
            'total_connections': edge_count,
            'estimated_depth': estimated_depth,
            'cyclomatic_complexity': cyclomatic,
            'complexity_rating': self._rate_complexity(node_count, decision_count, estimated_depth)
        }
    
    def _rate_complexity(self, nodes, decisions, depth):
        """Rate the complexity of the IVR system on a scale of 1-5"""
        # Simple algorithm to rate complexity
        score = 0
        
        # Based on total nodes
        if nodes < 5:
            score += 1
        elif nodes < 10:
            score += 2
        elif nodes < 15:
            score += 3
        elif nodes < 20:
            score += 4
        else:
            score += 5
        
        # Based on decision points
        if decisions < 2:
            score += 1
        elif decisions < 4:
            score += 2
        elif decisions < 6:
            score += 3
        elif decisions < 8:
            score += 4
        else:
            score += 5
        
        # Based on depth
        if depth < 2:
            score += 1
        elif depth < 3:
            score += 2
        elif depth < 4:
            score += 3
        elif depth < 5:
            score += 4
        else:
            score += 5
        
        # Average and round
        return round(score / 3)
    
    def analyze_menu_options(self):
        """Analyze menu options and their distribution"""
        # Find potential menu option patterns with more flexible matching
        menu_patterns = [
            r'(?:press|select|choose|dial|enter)\s+(\d+)(?:\s+for\s+|\s+to\s+)(.*?)(?:\.|$)',
            r'(?:press|select|choose|dial|enter)\s+(\d+)(?:\.|$)',
            r'(?:if you|for|to)\s+(.*?)(?:,\s*press\s+(\d+))',
            r'(?:press|select|choose|dial|enter)\s+(\d+)(?:\s+for\s+|\s+to\s+)(.*?)(?:\.|$)',
            r'(?:option|number)\s+(\d+)(?:\s+for\s+|\s+to\s+)(.*?)(?:\.|$)',
            r'(\d+)(?:\s+for\s+|\s+to\s+)(.*?)(?:\.|$)'
        ]
        
        # Extract menu options with their descriptions
        menu_options = []
        current_menu = []
        menu_text = []
        
        # Split transcript into sentences
        sentences = [s.strip() for s in self.transcript.split('.') if s.strip()]
        
        for sentence in sentences:
            # Check if this sentence contains a menu option
            option_found = False
            for pattern in menu_patterns:
                option_match = re.search(pattern, sentence.lower())
                if option_match:
                    groups = option_match.groups()
                    if len(groups) == 2:
                        if groups[0].isdigit():  # If first group is the number
                            option_num, description = groups
                        else:  # If first group is the description
                            description, option_num = groups
                    else:
                        option_num = groups[0]
                        description = sentence.lower().replace(f"press {option_num}", "").replace(f"press {option_num} for", "").replace(f"press {option_num} to", "").strip()
                    
                    current_menu.append({
                        'number': option_num,
                        'description': description.strip()
                    })
                    menu_text.append(sentence)
                    option_found = True
                    break
            
            # If no option found and we have a current menu, end it
            if not option_found and current_menu:
                menu_options.append({
                    'options': current_menu,
                    'text': ' '.join(menu_text)
                })
                current_menu = []
                menu_text = []
        
        # Add the last menu if exists
        if current_menu:
            menu_options.append({
                'options': current_menu,
                'text': ' '.join(menu_text)
            })
        
        # Calculate menu statistics
        menu_sizes = [len(menu['options']) for menu in menu_options]
        
        # Count total options mentioned
        all_options = []
        for menu in menu_options:
            all_options.extend([opt['number'] for opt in menu['options']])
        option_counter = Counter(all_options)
        
        self.metrics['menu_options'] = {
            'total_options_mentioned': len(all_options),
            'unique_options': len(option_counter),
            'estimated_menus': len(menu_sizes) if menu_sizes else 0,
            'avg_menu_size': statistics.mean(menu_sizes) if menu_sizes else 0,
            'max_menu_size': max(menu_sizes) if menu_sizes else 0,
            'menu_structure': menu_options,
            'option_descriptions': {opt['number']: opt['description'] for menu in menu_options for opt in menu['options']}
        }
    
    def analyze_potential_issues(self):
        """Identify potential issues in the IVR design"""
        issues = []
        
        # Check for potentially long menus
        if self.metrics.get('menu_options', {}).get('max_menu_size', 0) > 5:
            issues.append({
                'type': 'usability',
                'severity': 'medium',
                'description': 'Long menu detected with more than 5 options',
                'recommendation': 'Consider breaking long menus into categories'
            })
        
        # Check for dead ends in flowchart
        if 'End' not in self.flowchart and 'end' not in self.flowchart:
            issues.append({
                'type': 'design',
                'severity': 'low',
                'description': 'Potential missing end points in the IVR flow',
                'recommendation': 'Ensure all paths have proper termination points'
            })
        
        # Check for excessive depth
        if self.metrics.get('complexity', {}).get('estimated_depth', 0) > 4:
            issues.append({
                'type': 'usability',
                'severity': 'high',
                'description': 'Deep IVR tree with more than 4 levels',
                'recommendation': 'Flatten menu structure to improve navigation'
            })
        
        # Check for potentially confusing repeat instructions
        repeat_mentions = len(re.findall(r'repeat|say again|say that again', self.transcript.lower()))
        if repeat_mentions > 2:
            issues.append({
                'type': 'clarity',
                'severity': 'medium',
                'description': 'Multiple mentions of repeat instructions may indicate clarity issues',
                'recommendation': 'Simplify prompts and instructions'
            })
        
        # Check for timeouts or no-input handling
        if 'timeout' not in self.transcript.lower() and 'no input' not in self.transcript.lower():
            issues.append({
                'type': 'error_handling',
                'severity': 'medium',
                'description': 'No clear timeout or no-input handling detected',
                'recommendation': 'Add explicit timeout handling to improve user experience'
            })
        
        # Check for long greeting
        greeting_words = 0
        first_sentence = self.transcript.split('.')[0] if self.transcript and '.' in self.transcript else self.transcript
        greeting_words = len(first_sentence.split())
        if greeting_words > 25:
            issues.append({
                'type': 'efficiency',
                'severity': 'low',
                'description': 'Long greeting message detected',
                'recommendation': 'Keep initial greeting concise to reduce wait time'
            })
        
        # Check for potential accessibility issues
        accessibility_terms = ['tty', 'hearing impaired', 'accessibility', 'disability']
        has_accessibility = any(term in self.transcript.lower() for term in accessibility_terms)
        if not has_accessibility:
            issues.append({
                'type': 'accessibility',
                'severity': 'medium',
                'description': 'No apparent accessibility options mentioned',
                'recommendation': 'Consider adding TTY or options for hearing impaired users'
            })
        
        self.metrics['potential_issues'] = issues
    
    def analyze_sentiment(self):
        """Basic sentiment analysis of the IVR transcript"""
        # Simple word lists for basic sentiment analysis
        positive_words = [
            'thank', 'thanks', 'please', 'welcome', 'help', 'assist', 
            'happy', 'glad', 'sorry', 'appreciate', 'pleasure', 'convenient',
            'easy', 'quick', 'simple', 'helpful'
        ]
        
        negative_words = [
            'error', 'problem', 'issue', 'cannot', 'invalid', 'unavailable',
            'unfortunately', 'trouble', 'failed', 'retry', 'difficult', 
            'complicated', 'wrong', 'mistake', 'delay'
        ]
        
        urgent_words = [
            'emergency', 'urgent', 'immediately', 'critical', 'important',
            'priority', 'necessary', 'attention'
        ]
        
        # Count occurrences
        pos_count = sum(1 for word in positive_words if word in self.transcript.lower())
        neg_count = sum(1 for word in negative_words if word in self.transcript.lower())
        urgent_count = sum(1 for word in urgent_words if word in self.transcript.lower())
        
        # Calculate simple sentiment score (-1 to 1)
        total = pos_count + neg_count
        sentiment_score = 0
        if total > 0:
            sentiment_score = (pos_count - neg_count) / total
        
        # Customer service phrases detection
        service_phrases = ['how may i help you', 'how can i help', 'assist you', 'serving you', 
                          'customer service', 'customer support', 'representative']
        service_phrases_count = sum(1 for phrase in service_phrases if phrase in self.transcript.lower())
        
        self.metrics['sentiment'] = {
            'positive_word_count': pos_count,
            'negative_word_count': neg_count,
            'sentiment_score': sentiment_score,
            'tone': 'positive' if sentiment_score > 0.2 else ('negative' if sentiment_score < -0.2 else 'neutral')
        }
    
    def analyze_path_efficiency(self):
        """Analyze the efficiency of navigation paths"""
        # Extract potential paths from flowchart
        all_paths = []
        path_parts = re.findall(r'(\w+)-->(\w+)', self.flowchart)
        
        # Build graph of connections
        graph = defaultdict(list)
        for source, target in path_parts:
            graph[source].append(target)
        
        # Identify start node(s)
        start_nodes = []
        target_nodes = set()
        for source, target in path_parts:
            target_nodes.add(target)
        
        for node in graph.keys():
            if node not in target_nodes:
                start_nodes.append(node)
        
        if not start_nodes and graph:
            # If no clear start node, use the first node in the graph
            start_nodes = [list(graph.keys())[0]]
        
        # Identify end nodes (nodes with no outgoing connections)
        end_nodes = []
        for node in target_nodes:
            if node not in graph:
                end_nodes.append(node)
        
        # Calculate metrics based on graph structure
        avg_options_per_node = sum(len(targets) for targets in graph.values()) / max(1, len(graph))
        max_options = max([len(targets) for targets in graph.values()]) if graph else 0
        
        # Estimate shortest and longest paths
        shortest_path = float('inf')
        longest_path = 0
        
        if start_nodes and end_nodes:
            # Find all paths from start to end nodes
            for start in start_nodes:
                for end in end_nodes:
                    # Simple BFS to find shortest path
                    queue = [(start, [start])]
                    visited = set([start])
                    
                    while queue:
                        (node, path) = queue.pop(0)
                        
                        if node == end:
                            path_length = len(path) - 1  # Number of edges = nodes - 1
                            shortest_path = min(shortest_path, path_length)
                            longest_path = max(longest_path, path_length)
                            continue
                            
                        for neighbor in graph.get(node, []):
                            if neighbor not in visited:
                                visited.add(neighbor)
                                queue.append((neighbor, path + [neighbor]))
        
        if shortest_path == float('inf'):
            shortest_path = 0
        
        self.metrics['path_efficiency'] = {
            'max_options': max_options,
            'shortest_path_length': shortest_path,
            'longest_path_length': longest_path
        }
    
    def analyze_customer_experience(self):
        """Analyze potential customer experience factors"""
        # Check for customer-friendly phrases
        thank_you_count = len(re.findall(r'thank you|thanks|thank', self.transcript.lower()))
        please_count = len(re.findall(r'please', self.transcript.lower()))
        
        # Check for personalization elements
        personalization_phrases = [
            'your account', 'your information', 'your preferences', 
            'your recent', 'your request', 'your call'
        ]
        personalization_count = sum(1 for phrase in personalization_phrases if phrase in self.transcript.lower())
        
        # Check for customer support options
        support_phrases = [
            'speak to a representative', 'speak to an agent', 'talk to a person',
            'customer service', 'customer support', 'speak with a', 'talk with a'
        ]
        has_human_option = any(phrase in self.transcript.lower() for phrase in support_phrases)
        
        # Estimate waiting time mentions
        waiting_phrases = ['wait time', 'estimated wait', 'waiting time', 'hold time', 'queue']
        waiting_mentioned = any(phrase in self.transcript.lower() for phrase in waiting_phrases)
        
        # Calculate verbosity and efficiency
        word_count = len(self.transcript.split())
        menu_options = self.metrics.get('menu_options', {}).get('total_options_mentioned', 0)
        words_per_option = word_count / max(1, menu_options) if menu_options > 0 else word_count
        
        # Brevity score: lower is better (more concise)
        brevity_score = min(10, max(1, 5 - (words_per_option - 15) / 10))
        
        # Calculate overall CX score
        politeness_factor = (thank_you_count + please_count) / max(1, word_count / 100)
        personalization_factor = personalization_count / max(1, word_count / 200)
        human_option_factor = 1 if has_human_option else 0
        
        cx_score = (politeness_factor * 3 + personalization_factor * 2 + human_option_factor * 3 + brevity_score * 2) / 10
        cx_score = min(10, max(1, cx_score * 10))  # Scale to 1-10 range
        
        self.metrics['customer_experience'] = {
            'politeness_score': min(10, politeness_factor * 10),
            'personalization_score': min(10, personalization_factor * 10),
            'has_human_option': has_human_option,
            'mentions_wait_time': waiting_mentioned,
            'wordiness': words_per_option,
            'brevity_score': brevity_score,
            'overall_cx_score': cx_score
        }
    
    def analyze_best_practices(self):
        """Analyze the IVR against best practices"""
        best_practices = []
        
        # Check menu size
        if self.metrics['menu_options']['max_menu_size'] <= 5:
            best_practices.append({
                'status': 'pass',
                'description': 'Menu size is optimal (≤ 5 options)',
                'suggestion': None
            })
        else:
            best_practices.append({
                'status': 'fail',
                'description': 'Menu size exceeds recommended limit',
                'suggestion': 'Consider breaking down menus with more than 5 options into sub-menus'
            })
        
        # Check menu depth
        if self.metrics['complexity']['estimated_depth'] <= 3:
            best_practices.append({
                'status': 'pass',
                'description': 'Menu depth is reasonable (≤ 3 levels)',
                'suggestion': None
            })
        else:
            best_practices.append({
                'status': 'fail',
                'description': 'Menu depth exceeds recommended limit',
                'suggestion': 'Consider flattening the menu structure to reduce navigation depth'
            })
        
        # Check for clear instructions
        instruction_phrases = ['press', 'select', 'choose', 'dial', 'enter']
        has_clear_instructions = any(phrase in self.transcript.lower() for phrase in instruction_phrases)
        best_practices.append({
            'status': 'pass' if has_clear_instructions else 'fail',
            'description': 'Clear user instructions present',
            'suggestion': None if has_clear_instructions else 'Add clear instructions for user actions'
        })
        
        self.metrics['best_practices'] = best_practices
    
    def generate_recommendations(self):
        """Generate actionable recommendations based on analysis"""
        recommendations = []
        
        # Complexity recommendations
        complexity = self.metrics.get('complexity', {})
        if complexity.get('complexity_rating', 0) >= 4:
            recommendations.append({
                'category': 'structure',
                'priority': 'high',
                'title': 'Simplify IVR structure',
                'description': 'Your IVR is relatively complex. Consider reducing the number of menu levels and options.',
                'action': 'Identify paths that could be shortened or combined to create a more intuitive experience.'
            })
        
        # Menu size recommendations
        menu_options = self.metrics.get('menu_options', {})
        if menu_options.get('max_menu_size', 0) > 5:
            recommendations.append({
                'category': 'usability',
                'priority': 'medium',
                'title': 'Reorganize menu options',
                'description': f"One of your menus has {menu_options.get('max_menu_size', 0)} options, which may overwhelm callers.",
                'action': 'Group related options into categories to keep each menu under 5 choices.'
            })
        
        # Path efficiency recommendations
        path_efficiency = self.metrics.get('path_efficiency', {})
        if path_efficiency.get('longest_path_length', 0) > 4:
            recommendations.append({
                'category': 'efficiency',
                'priority': 'medium',
                'title': 'Shorten customer journeys',
                'description': f"Your longest path requires {path_efficiency.get('longest_path_length', 0)} steps, which may frustrate callers.",
                'action': 'Add shortcuts to frequently requested services from the main menu.'
            })
        
        # Customer experience recommendations
        cx = self.metrics.get('customer_experience', {})
        if not cx.get('has_human_option', False):
            recommendations.append({
                'category': 'service',
                'priority': 'high',
                'title': 'Add option to speak with an agent',
                'description': 'No clear path to speak with a human agent was detected.',
                'action': 'Add an option to speak with a representative in the main menu and at critical decision points.'
            })
        
        if cx.get('brevity_score', 0) < 4:
            recommendations.append({
                'category': 'content',
                'priority': 'medium',
                'title': 'Reduce wordiness',
                'description': 'Your prompts are relatively verbose, which may extend call duration.',
                'action': 'Edit prompts to be more concise while maintaining clarity and politeness.'
            })
        
        # Accessibility recommendations
        issues = self.metrics.get('potential_issues', [])
        accessibility_issue = next((issue for issue in issues if issue.get('type') == 'accessibility'), None)
        if accessibility_issue:
            recommendations.append({
                'category': 'accessibility',
                'priority': 'medium',
                'title': 'Enhance accessibility options',
                'description': 'No accessibility options were detected in your IVR system.',
                'action': 'Add TTY options and ensure compliance with accessibility standards.'
            })
        
        # Sentiment recommendations
        sentiment = self.metrics.get('sentiment', {})
        if sentiment.get('customer_focus_score', 0) < 5:
            recommendations.append({
                'category': 'tone',
                'priority': 'low',
                'title': 'Enhance customer-focused language',
                'description': 'Your IVR could benefit from more customer-centered language.',
                'action': 'Add more personalized language and acknowledgments throughout the script.'
            })
        
        self.metrics['recommendations'] = recommendations
    
    def get_metrics(self):
        """Get all collected metrics"""
        return self.metrics
    
    def get_summary(self):
        """Get a human-readable summary of the analysis"""
        complexity = self.metrics.get('complexity', {})
        menu_options = self.metrics.get('menu_options', {})
        issues = self.metrics.get('potential_issues', [])
        sentiment = self.metrics.get('sentiment', {})
        path_efficiency = self.metrics.get('path_efficiency', {})
        cx = self.metrics.get('customer_experience', {})
        
        complexity_level = ['Very Simple', 'Simple', 'Moderate', 'Complex', 'Very Complex']
        complexity_rating = complexity.get('complexity_rating', 3)
        
        summary = {
            'ivr_complexity': complexity_level[complexity_rating - 1] if 1 <= complexity_rating <= 5 else 'Moderate',
            'total_interaction_points': complexity.get('total_nodes', 0),
            'number_of_menus': menu_options.get('estimated_menus', 0),
            'average_options_per_menu': round(menu_options.get('avg_menu_size', 0), 1),
            'max_menu_depth': complexity.get('estimated_depth', 0),
            'tone': sentiment.get('tone', 'neutral').capitalize(),
            'estimated_minimum_steps': path_efficiency.get('shortest_path_length', 0),
            'customer_experience_score': round(cx.get('overall_cx_score', 5), 1),
            'issues_found': len(issues),
            'high_priority_issues': sum(1 for issue in issues if issue.get('severity') == 'high'),
            'top_recommendations': [rec.get('title') for rec in self.metrics.get('recommendations', [])[:3]],
            'best_practices': self.metrics.get('best_practices', [])
        }
        
        return summary
    
    def get_visualization_data(self):
        """Get data for visualization"""
        visualization_data = {
            'radar_chart': {
                'labels': [
                    'Simplicity', 
                    'Efficiency', 
                    'Clarity',
                    'Customer Focus',
                    'Structure',
                    'Accessibility'
                ],
                'datasets': [{
                    'label': 'IVR Performance',
                    'data': [
                        10 - min(10, self.metrics.get('complexity', {}).get('complexity_rating', 5) * 2),  # Simplicity (inverse of complexity)
                        self.metrics.get('path_efficiency', {}).get('click_efficiency_score', 5),  # Efficiency
                        10 - len([i for i in self.metrics.get('potential_issues', []) if i.get('type') == 'clarity']),  # Clarity
                        self.metrics.get('customer_experience', {}).get('overall_cx_score', 5),  # Customer Focus
                        10 - min(10, self.metrics.get('complexity', {}).get('estimated_depth', 3) * 2),  # Structure (inverse of depth)
                        10 - len([i for i in self.metrics.get('potential_issues', []) if i.get('type') == 'accessibility']) * 3  # Accessibility
                    ]
                }]
            },
            'bar_chart': {
                'labels': ['Politeness', 'Personalization', 'Brevity', 'Path Efficiency', 'Option Clarity'],
                'datasets': [{
                    'label': 'Scores',
                    'data': [
                        self.metrics.get('customer_experience', {}).get('politeness_score', 5),
                        self.metrics.get('customer_experience', {}).get('personalization_score', 5),
                        self.metrics.get('customer_experience', {}).get('brevity_score', 5),
                        self.metrics.get('path_efficiency', {}).get('click_efficiency_score', 5),
                        10 - min(10, (self.metrics.get('menu_options', {}).get('max_menu_size', 3) - 3))
                    ]
                }]
            },
            'issue_severity': {
                'labels': ['High', 'Medium', 'Low'],
                'data': [
                    sum(1 for i in self.metrics.get('potential_issues', []) if i.get('severity') == 'high'),
                    sum(1 for i in self.metrics.get('potential_issues', []) if i.get('severity') == 'medium'),
                    sum(1 for i in self.metrics.get('potential_issues', []) if i.get('severity') == 'low')
                ]
            },
            'complexity': self.metrics['complexity'],
            'menu_options': self.metrics['menu_options'],
            'best_practices': self.metrics.get('best_practices', []),
            'issues': self.metrics.get('potential_issues', [])
        }
        
        return visualization_data
    
    def to_json(self):
        """Return metrics as JSON string"""
        return json.dumps({
            'metrics': self.metrics,
            'summary': self.get_summary(),
            'visualization_data': self.get_visualization_data()
        }, indent=2)