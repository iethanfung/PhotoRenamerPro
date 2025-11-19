from src.core.config_manager import ConfigManager
from loguru import logger


class Learner:
    """负责自学习逻辑"""

    @staticmethod
    def learn_new_cp_alias(test_name, std_cp, new_alias):
        """
        :param test_name: "1mG"
        :param std_cp: "25Drop"
        :param new_alias: "t25"
        """
        if not new_alias or not new_alias.strip():
            return

        cp_map = ConfigManager.load_cp_map()
        new_alias_lower = new_alias.lower().strip()

        if test_name not in cp_map:
            cp_map[test_name] = {}

        if std_cp not in cp_map[test_name]:
            cp_map[test_name][std_cp] = []

        current_aliases = cp_map[test_name][std_cp]
        # 检查是否已存在
        if new_alias_lower not in [x.lower() for x in current_aliases]:
            current_aliases.append(new_alias)  # 保存用户输入的原始大小写，或者存 lower 都可以
            cp_map[test_name][std_cp] = current_aliases
            ConfigManager.save_cp_map(cp_map)
            logger.info(f"Learned new CP alias: {new_alias} -> {test_name}/{std_cp}")

    @staticmethod
    def learn_new_issue_alias(std_issue, new_alias):
        if not new_alias or not new_alias.strip():
            return

        issue_map = ConfigManager.load_issue_map()
        new_alias_lower = new_alias.lower().strip()

        if std_issue not in issue_map:
            issue_map[std_issue] = []

        current_aliases = issue_map[std_issue]
        if new_alias_lower not in [x.lower() for x in current_aliases]:
            current_aliases.append(new_alias)
            issue_map[std_issue] = current_aliases
            ConfigManager.save_issue_map(issue_map)
            logger.info(f"Learned new Issue alias: {new_alias} -> {std_issue}")