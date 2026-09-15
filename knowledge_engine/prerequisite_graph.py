"""
Prerequisite Knowledge Graph Handler.

Loads curriculum DAG structures, manages prerequisite validation,
applies prior adjustments, and performs topological sorting for curriculum paths.
"""

import json
import os
from collections import defaultdict
from typing import Dict, List, Set


class PrerequisiteGraph:
    """
    Curriculum dependency graph manager.
    """

    def __init__(self, graph_path: str = None):
        self._graph: Dict = {}
        if graph_path is None:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            default_path = os.path.abspath(os.path.join(current_dir, "..", "data", "knowledge_graph.json"))
            if os.path.exists(default_path):
                graph_path = default_path

        if graph_path and os.path.exists(graph_path):
            with open(graph_path, 'r', encoding='utf-8') as f:
                self._graph = json.load(f)
        else:
            self._graph = {"topics": {}}

    def get_prerequisites(self, topic_id: str) -> List[str]:
        """Returns direct prerequisites for a concept."""
        topic = self._graph.get("topics", {}).get(topic_id, {})
        return topic.get("prerequisites", [])

    def get_dependents(self, topic_id: str) -> List[str]:
        """Returns concepts directly depending on the given concept."""
        dependents = []
        for t_id, t_info in self._graph.get("topics", {}).items():
            if topic_id in t_info.get("prerequisites", []):
                dependents.append(t_id)
        return dependents

    def get_topic_difficulty(self, topic_id: str) -> float:
        """Returns default calibrated concept difficulty."""
        topic = self._graph.get("topics", {}).get(topic_id, {})
        return topic.get("default_difficulty", topic.get("difficulty", 0.5))

    def adjust_prior(self, topic_id: str, user_masteries: Dict[str, float]) -> float:
        """
        Adjusts prior knowledge probability P(L0) based on mastery of prerequisites.
        Applies bonuses for strong foundation and penalties for weak prerequisites.
        """
        topic = self._graph.get("topics", {}).get(topic_id, {})
        base_prior = topic.get("base_prior", 0.15)
        prereqs = self.get_prerequisites(topic_id)

        if not prereqs:
            return base_prior

        prereq_masteries = [user_masteries.get(p, 0.0) for p in prereqs]
        mean_mastery = sum(prereq_masteries) / len(prereq_masteries)

        adjusted_prior = base_prior * mean_mastery

        if all(m >= 0.7 for m in prereq_masteries):
            adjusted_prior *= 1.25
        elif any(m < 0.4 for m in prereq_masteries):
            adjusted_prior *= 0.75

        return max(0.01, min(0.5, adjusted_prior))

    def get_learning_path(self, target_topics: List[str]) -> List[str]:
        """
        Computes an optimal study path using Kahn's topological sort
        over the subgraph formed by target topics and all prerequisites.
        """
        subgraph_nodes: Set[str] = set()

        def collect_nodes(t_id: str):
            if t_id not in subgraph_nodes:
                subgraph_nodes.add(t_id)
                for p in self.get_prerequisites(t_id):
                    collect_nodes(p)

        for topic in target_topics:
            collect_nodes(topic)

        in_degree = {n: 0 for n in subgraph_nodes}
        adj_list = defaultdict(list)

        for n in subgraph_nodes:
            prereqs = [p for p in self.get_prerequisites(n) if p in subgraph_nodes]
            for p in prereqs:
                adj_list[p].append(n)
                in_degree[n] += 1

        queue = [n for n in subgraph_nodes if in_degree[n] == 0]
        learning_path = []

        while queue:
            node = queue.pop(0)
            learning_path.append(node)
            for neighbor in adj_list[node]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        return learning_path

    def get_all_topics(self) -> List[str]:
        """Returns all registered concept identifiers in graph."""
        return list(self._graph.get("topics", {}).keys())

    def get_topic_info(self, topic_id: str) -> Dict:
        """Returns topic metadata attributes."""
        return self._graph.get("topics", {}).get(topic_id, {})
