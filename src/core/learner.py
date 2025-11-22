from src.core.config_manager import ConfigManager
from loguru import logger


class Learner:
    """
    负责自学习逻辑 - 严格模式
    只允许添加别名(Alias)，不允许创建新Key
    """

    @staticmethod
    def learn_new_cp_alias(test_name, std_cp, new_alias):
        if not new_alias or not new_alias.strip(): return False, "Empty alias"

        cp_map = ConfigManager.load_cp_map()
        new_alias_clean = new_alias.strip()

        # 1. 检查 Test 是否存在
        if test_name not in cp_map:
            return False, f"Test项目 '{test_name}' 不在 cp_map 中"

        # 2. 检查 Standard CP (Key) 是否存在
        # 注意：cp_map[test_name] 可能是 list (旧版) 或 dict (新版)，根据你的JSON结构
        # 假设结构是: "1mG": { "25Drop": ["25",...], ... }
        if std_cp not in cp_map[test_name]:
            return False, f"标准节点 '{std_cp}' 不在 cp_map['{test_name}'] 中。\n请先在配置文件中添加该节点 Key。"

        # 3. 执行添加
        current_aliases = cp_map[test_name][std_cp]
        # 查重 (忽略大小写)
        if new_alias_clean.lower() not in [x.lower() for x in current_aliases]:
            current_aliases.append(new_alias_clean)
            cp_map[test_name][std_cp] = current_aliases
            ConfigManager.save_cp_map(cp_map)
            logger.info(f"Learned CP: {new_alias_clean} -> {std_cp}")
            return True, "Success"

        return True, "Already exists"  # 已存在也算成功，不报错

    @staticmethod
    def learn_new_issue_alias(std_issue, new_alias):
        if not new_alias or not new_alias.strip(): return False, "Empty alias"

        issue_map = ConfigManager.load_issue_map()
        new_alias_clean = new_alias.strip()

        # 严格检查 Key 是否存在
        if std_issue not in issue_map:
            return False, f"标准问题 '{std_issue}' 不在 issue_map 中。\n请先在配置文件中添加该 Key。"

        current_aliases = issue_map[std_issue]
        if new_alias_clean.lower() not in [x.lower() for x in current_aliases]:
            current_aliases.append(new_alias_clean)
            issue_map[std_issue] = current_aliases
            ConfigManager.save_issue_map(issue_map)
            logger.info(f"Learned Issue: {new_alias_clean} -> {std_issue}")
            return True, "Success"

        return True, "Already exists"

    @staticmethod
    def learn_new_orient_alias(std_orient, new_alias):
        if not new_alias or not new_alias.strip(): return False, "Empty alias"

        orient_map = ConfigManager.load_orient_map()
        new_alias_clean = new_alias.strip()

        # 严格检查 Key 是否存在
        if std_orient not in orient_map:
            return False, f"标准方向 '{std_orient}' 不在 orient_map 中。\n请先在配置文件中添加该 Key。"

        current_aliases = orient_map[std_orient]
        if new_alias_clean.lower() not in [x.lower() for x in current_aliases]:
            current_aliases.append(new_alias_clean)
            orient_map[std_orient] = current_aliases
            # 这里假设 ConfigManager 有 save_orient_map，如果没有需要去加
            # 暂时假设你有，或者用通用的 save 方法
            # 补丁：如果没有 save_orient_map，请在 ConfigManager 加一下，或者这里直接写文件
            # 建议去 ConfigManager 加一个 save_orient_map
            ConfigManager.save_orient_map(orient_map)
            logger.info(f"Learned Orient: {new_alias_clean} -> {std_orient}")
            return True, "Success"

        return True, "Already exists"