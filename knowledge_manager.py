import json
import os

class KnowledgeManager:
    def __init__(self, filename="learning_history.json"):
        self.filename = filename
        self.data = self._load_data()

    def _load_data(self):
        if os.path.exists(self.filename):
            with open(self.filename, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {
            "current_topic": "待开始",
            "completed_topics": [],
            "concepts_learned": []
        }

    def save_data(self):
        with open(self.filename, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, ensure_ascii=False, indent=4)

    def update_topic(self, topic):
        self.data["current_topic"] = topic
        self.save_data()

    def add_learned_concept(self, concept):
        if concept not in self.data["concepts_learned"]:
            self.data["concepts_learned"].append(concept)
            self.save_data()

    def get_summary(self):
        return f"""
        ### 📚 学习概览
        **当前话题**: {self.data['current_topic']}
        **已学概念**: {', '.join(self.data['concepts_learned']) if self.data['concepts_learned'] else '暂无'}
        """
