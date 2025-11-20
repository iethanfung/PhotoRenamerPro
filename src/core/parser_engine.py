import os
import re
import math
from rapidfuzz import process, fuzz
from loguru import logger
from src.utils.constants import COLOR_GREEN, COLOR_YELLOW, COLOR_ORANGE, COLOR_RED


class ParserEngine:
    def __init__(self, excel_engine, settings, cp_map, issue_map):
        self.excel = excel_engine
        self.settings = settings
        self.cp_map = cp_map
        self.issue_map = issue_map

        # === 数学模型参数 ===
        # Logistic 函数参数：P = 1 / (1 + e^(-k * (x - x0)))
        self.LOGISTIC_K = 8.0  # 陡峭度：越大，好坏区分越明显
        self.LOGISTIC_X0 = 0.60  # 中心点：原始分达到 0.6 才开始算“比较可信”

    def parse_filename(self, file_path):
        filename_only = os.path.basename(file_path)
        base_name, ext = os.path.splitext(filename_only)

        # 1. 预处理：统一分隔符，生成 Token
        # 保留原始字符串用于正则，生成 clean_name 用于分词
        clean_name = base_name
        for char in ['_', '-', '—', '——', '(', ')', '[', ']', ' ']:
            clean_name = clean_name.replace(char, ' ')
        tokens = [t for t in clean_name.split() if t]

        # 初始化结果容器
        result = {
            "original": file_path,
            "base_name": base_name,
            "ext": ext,
            "rel_no": None,
            "unit_data": None,
            "raw_cp": "",
            "std_cp": "[Unknown CP]",
            "raw_detail": "",
            "type": "Unknown",
            "detail": "",
            "confidence": 0.00,
            "status_color": COLOR_RED,
            "status_msg": "",
            "debug_score": {}  # 存储详细的得分信息
        }

        #logger.info(f"🔵 [算法介入] 文件名: {base_name}")

        # === 2. 锚点特征提取 (Feature: Anchor) ===

        # A. 提取 Rel No
        all_nums = re.findall(r'\d+', base_name)
        all_nums.sort(key=len, reverse=True)  # 优先长数字

        found_rel_token = None
        candidates_rows = []  # 可能对应的 Excel 行

        for num_str in all_nums:
            info = self.excel.get_unit_info(num_str)
            if info:
                candidates_rows = info if isinstance(info, list) else [info]
                first_row = candidates_rows[0]

                # 获取 Display Rel No
                val = first_row.get('Rel_No')
                if not val or val == 'UNKNOWN':
                    user_col = self.settings['excel_header_map'].get('Rel_No', 'No#').strip()
                    val = first_row.get(user_col)
                if not val or val == 'UNKNOWN': val = num_str

                result['rel_no'] = val
                found_rel_token = num_str
                break

        if not result['rel_no']:
            result['status_msg'] = "Rel No Not Found"
            result['confidence'] = 0.0
            return result

        # B. 提取 Type (Orient/Issue)
        orient_pattern = re.compile(r'(?i)[o0][\-_]?(\d+)$')
        temp_tokens = re.split(r'[_\-\s\.]+', base_name)

        found_orient = None

        for t in reversed(temp_tokens):
            if t == found_rel_token: continue
            m = orient_pattern.match(t)
            if m:
                found_orient = "O" + m.group(1)
                result['raw_detail'] = t
                break

        if found_orient:
            result['type'] = "Regular"
            result['detail'] = found_orient
        else:
            result['type'] = "Issue"
            # Issue 匹配
            resid_for_issue = clean_name.replace(found_rel_token, "")
            best_issue_score = 0
            best_issue = None

            for std_issue, aliases in self.issue_map.items():
                for alias in aliases:
                    # 简单的包含匹配
                    if alias.lower() in resid_for_issue.lower():
                        # 优先匹配更长的词 (破裂 > 破)
                        score = len(alias)
                        if score > best_issue_score:
                            best_issue_score = score
                            best_issue = std_issue
                            result['raw_detail'] = alias

            if best_issue:
                result['detail'] = best_issue
            else:
                # 兜底
                remain = [x for x in temp_tokens if x != found_rel_token]
                if remain:
                    result['detail'] = remain[-1]
                    result['raw_detail'] = remain[-1]
                    result['status_msg'] = "Unknown Issue"

        # === 3. 构建残差 (Residual) ===
        residual = base_name
        if found_rel_token:
            residual = residual.replace(found_rel_token, " ", 1)
        if result['raw_detail']:
            residual = residual.replace(result['raw_detail'], " ", 1)

        for char in ['_', '-', '—', '——', '(', ')', '[', ']', '.jpg', '.png', '.jpeg']:
            residual = residual.replace(char, ' ')

        residual = residual.strip()
        result['raw_cp'] = residual

        # === 4. 计算匹配分数 (Model Calculation) ===

        # 确定搜索范围：Excel 指定的 Test
        target_tests = set()
        for row in candidates_rows:
            t = str(row.get('Test', 'Unknown')).strip()
            target_tests.add(t)

        best_match = {
            "std_cp": None,
            "raw_score": 0.0,  # 线性分 0-1
            "final_conf": 0.0,  # Logistic 分 0-1
            "test_name": None
        }

        if residual:
            # 第一轮：上下文搜索 (High Context Weight)
            # 这里的 True 表示这是 Excel 指定的 Test，会有 Context 加分
            ctx_match = self._search_best_cp(residual, list(target_tests), is_context_match=True)

            best_match = ctx_match

            # 第二轮：全网搜索 (Global Search)
            # 如果第一轮置信度太低 (<0.6)，尝试全网搜
            if best_match['final_conf'] < 0.6:
                all_tests = list(self.cp_map.keys())
                # is_context_match=False，没有上下文加分
                global_match = self._search_best_cp(residual, all_tests, is_context_match=False)

                # 如果全网搜索的结果显著更好 (高出 0.2 的置信度)，则采纳
                if global_match['final_conf'] > best_match['final_conf'] + 0.2:
                    best_match = global_match
                    # 修正 Excel 数据
                    if candidates_rows:
                        candidates_rows[0]['Test'] = best_match['test_name']

        # === 5. 结果结算 ===

        # 填入基础数据
        result['unit_data'] = candidates_rows[0]
        result['confidence'] = best_match['final_conf']

        if best_match['std_cp']:
            result['std_cp'] = best_match['std_cp']
        else:
            result['std_cp'] = "[Unknown CP]"

        # === 6. 状态判断 (Business Rules) ===

        is_cp_missing = (result['std_cp'] == "[Unknown CP]")
        should_downgrade = False

        # 规则 1: Regular 必须有 CP
        if result['type'] == 'Regular' and is_cp_missing:
            should_downgrade = True

        # 规则 2: Issue 如果有残差，也应该匹配到 CP，否则警告
        elif result['type'] == 'Issue' and is_cp_missing and result['raw_cp']:
            should_downgrade = True

        if should_downgrade:
            # 强制降级：无论算法算出多少分，逻辑上这是不完整的
            # 设定上限为 0.55 (黄色/橙色区间)
            result['confidence'] = min(result['confidence'], 0.55)
            result['status_msg'] = "Fix CP"
            result['status_color'] = COLOR_ORANGE
        else:
            # 根据置信度定颜色
            conf = result['confidence']
            if conf >= 0.90:
                result['status_color'] = COLOR_GREEN
                result['status_msg'] = "Ready"
            elif conf >= 0.65:
                result['status_color'] = COLOR_YELLOW
                if "Fix" not in result['status_msg']: result['status_msg'] = "Check"
            else:
                result['status_color'] = COLOR_RED
                result['status_msg'] = "Low Conf"
        logger.info(f"🔵 [解析结果] 文件名: {base_name} ==》{result}")
        return result

    def _search_best_cp(self, residual, test_scope, is_context_match):
        """
        在指定测试范围内搜索最佳匹配
        返回一个包含分数详情的字典
        """
        best_res = {
            "std_cp": None,
            "raw_score": 0.0,
            "final_conf": 0.0,
            "test_name": None
        }

        # 提取残差特征
        resid_nums = set(re.findall(r'\d+', residual))
        resid_lower = residual.lower()

        for test_name in test_scope:
            cps = self.cp_map.get(test_name, {})
            for std_cp, aliases in cps.items():
                candidates = [std_cp] + aliases

                for cand in candidates:
                    cand_lower = cand.lower()

                    # === 特征计算 (Feature Engineering) ===

                    # 1. 模糊相似度 F_fuzzy (0~1)
                    # WRatio 对乱序和部分匹配比较友好
                    # token_sort_ratio 对纯乱序友好
                    score_w = fuzz.WRatio(resid_lower, cand_lower) / 100.0
                    score_sort = fuzz.token_sort_ratio(resid_lower, cand_lower) / 100.0
                    f_fuzzy = max(score_w, score_sort)

                    # 2. 数字指纹 F_num (-1 ~ 1)
                    # 这是最关键的特征，权重极高
                    cand_nums = set(re.findall(r'\d+', cand))
                    f_num = 0.0
                    if resid_nums:
                        if resid_nums == cand_nums:
                            f_num = 1.0  # 完美
                        elif resid_nums.intersection(cand_nums):
                            f_num = 0.5  # 部分匹配
                        else:
                            f_num = -1.0  # 冲突 (如 45 vs 25)，一票否决
                    else:
                        # 用户没写数字，但标准里有数字
                        if cand_nums:
                            f_num = -0.2  # 轻微惩罚

                    # 3. 长度惩罚 F_len (0 ~ 1)
                    # 避免 "L" 匹配 "Light-45min"
                    f_len = 1.0
                    if len(resid_lower) > 0 and len(cand_lower) > 0:
                        ratio = min(len(resid_lower), len(cand_lower)) / max(len(resid_lower), len(cand_lower))
                        if ratio < 0.3: f_len = 0.5  # 长度差异大，系数打折

                    # 4. 上下文奖励 F_context (0 or 1)
                    f_context = 1.0 if is_context_match else 0.0

                    # === 线性加权 (Linear Weights) ===
                    # 总权重和建议接近 1.0 或更高，以便让 logistic 达到饱和区

                    w_fuzzy = 0.4
                    w_num = 0.5  # 数字非常重要
                    w_context = 0.1  # 哪怕模糊分低一点，如果是本测试的也优先

                    # 原始线性分
                    # 基础分 0.2 (保底) + 加权分 * 长度系数
                    raw_score = 0.2 + (w_fuzzy * f_fuzzy + w_num * f_num + w_context * f_context) * f_len

                    # === Logistic 映射 (Sigmoid) ===
                    # 将 (-inf, +inf) 映射到 (0, 1)
                    # P = 1 / (1 + e^(-k * (x - x0)))

                    final_conf = self._sigmoid(raw_score)

                    if final_conf > best_res['final_conf']:
                        best_res['std_cp'] = std_cp
                        best_res['raw_score'] = raw_score
                        best_res['final_conf'] = final_conf
                        best_res['test_name'] = test_name
        return best_res

    def _sigmoid(self, x):
        """
        Logistic 函数，将任意分数映射为概率
        """
        try:
            return 1 / (1 + math.exp(-self.LOGISTIC_K * (x - self.LOGISTIC_X0)))
        except OverflowError:
            return 0.0 if x < self.LOGISTIC_X0 else 1.0