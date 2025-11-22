import os
import re
import math
from rapidfuzz import process, fuzz
from loguru import logger
from src.utils.constants import COLOR_GREEN, COLOR_YELLOW, COLOR_ORANGE, COLOR_RED


class ParserEngine:
    def __init__(self, excel_engine, settings, cp_map, issue_map, orient_map):
        self.excel = excel_engine
        self.settings = settings
        self.cp_map = cp_map
        self.issue_map = issue_map
        self.orient_map = orient_map

        self.LOGISTIC_K = 8.0
        self.LOGISTIC_X0 = 0.60

    def parse_filename(self, file_path):
        filename_only = os.path.basename(file_path)
        base_name, ext = os.path.splitext(filename_only)

        clean_name = base_name
        for char in ['_', '-', '—', '——', '(', ')', '[', ']', ' ', '+']:
            clean_name = clean_name.replace(char, ' ')
        tokens = [t for t in clean_name.split() if t]

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
            "detail": "[Unknown]",
            "confidence": 0.00,
            "status_color": COLOR_RED,
            "status_msg": "",
            "tokens": tokens,
        }

        logger.info(f"🔵 [V4.3 严格匹配] 文件: {base_name}")

        # 1. 提取 Rel No
        all_nums = re.findall(r'\d+', base_name)
        all_nums.sort(key=len, reverse=True)

        found_rel_token = None
        candidates_rows = []

        for num_str in all_nums:
            info = self.excel.get_unit_info(num_str)
            if info:
                candidates_rows = info if isinstance(info, list) else [info]
                first_row = candidates_rows[0]
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
            return result

        # 2. 提取 Type & Detail
        temp_tokens = re.split(r'[_\-\s\.]+', base_name)
        found_orient_std = None
        found_orient_raw = None

        # A. Orient Map
        for t in reversed(temp_tokens):
            if t == found_rel_token: continue
            t_clean = t.strip()
            for std_o, aliases in self.orient_map.items():
                if t_clean.lower() in [a.lower() for a in aliases]:
                    found_orient_std = std_o
                    found_orient_raw = t_clean
                    break
            if found_orient_std: break

        # B. Orient Regex
        if not found_orient_std:
            orient_pattern = re.compile(r'(?i)^o\s*[-_]?\s*(\d+)$')
            for t in reversed(temp_tokens):
                if t == found_rel_token: continue
                m = orient_pattern.match(t)
                if m:
                    found_orient_std = "O" + m.group(1)
                    found_orient_raw = t
                    break

        if found_orient_std:
            result['type'] = "Regular"
            result['detail'] = found_orient_std
            result['raw_detail'] = found_orient_raw
        else:
            result['type'] = "Issue"
            resid_for_issue = clean_name.replace(found_rel_token, "")
            best_issue_score = 0
            best_issue_std = None
            best_issue_raw = None

            for std_issue, aliases in self.issue_map.items():
                for alias in aliases:
                    if alias.lower() in resid_for_issue.lower():
                        score = len(alias)
                        if score > best_issue_score:
                            best_issue_score = score
                            best_issue_std = std_issue
                            best_issue_raw = alias

            if best_issue_std:
                result['detail'] = best_issue_std
                result['raw_detail'] = best_issue_raw
                result['confidence'] += 0.3
            else:
                remain = [x for x in temp_tokens if x != found_rel_token]
                if remain:
                    result['raw_detail'] = remain[-1]
                    result['detail'] = "[Unknown Issue]"
                    result['status_msg'] = "Unknown Issue"

        # 3. 构建残差
        residual = base_name
        if found_rel_token:
            residual = residual.replace(found_rel_token, " ", 1)
        if result['raw_detail']:
            residual = residual.replace(result['raw_detail'], " ", 1)

        for char in ['_', '-', '—', '——', '(', ')', '[', ']', '.jpg', '.png', '.jpeg', '+']:
            residual = residual.replace(char, ' ')

        residual = residual.strip()
        result['raw_cp'] = residual

        # 4. 搜寻 CP
        excel_test_strings = set()
        for row in candidates_rows:
            t = str(row.get('Test', 'Unknown')).strip()
            excel_test_strings.add(t)

        best_match = {"std_cp": None, "raw_score": 0.0, "final_conf": 0.0}

        if residual:
            strict_scope = set()
            for test_str in excel_test_strings:
                if test_str in self.cp_map:
                    strict_scope.add(test_str)
                if '+' in test_str:
                    parts = [p.strip() for p in test_str.split('+')]
                    for p in parts:
                        if p in self.cp_map:
                            strict_scope.add(p)

            if strict_scope:
                best_match = self._search_best_cp(residual, list(strict_scope), is_context_match=True)
            else:
                # 只有 CSV Test 未知时才允许全网搜
                all_tests = list(self.cp_map.keys())
                best_match = self._search_best_cp(residual, all_tests, is_context_match=False)

        # 5. 结果结算
        result['unit_data'] = candidates_rows[0].copy()
        result['confidence'] = best_match['final_conf']

        if best_match['std_cp']:
            result['std_cp'] = best_match['std_cp']
        else:
            result['std_cp'] = "[Unknown CP]"
            if not result['raw_cp'] and result['tokens']:
                potential = [x for x in result['tokens'] if x != result['raw_detail'] and x != found_rel_token]
                if potential: result['raw_cp'] = potential[0]

        # 6. 状态判断
        is_cp_unknown = (result['std_cp'] == "[Unknown CP]")
        is_detail_unknown = (result['detail'] == "[Unknown]" or result['detail'] == "[Unknown Issue]")

        should_downgrade = False
        if result['type'] == 'Regular':
            if is_cp_unknown or is_detail_unknown: should_downgrade = True
        else:
            if is_detail_unknown: should_downgrade = True
            if is_cp_unknown and result['raw_cp']: should_downgrade = True

        if should_downgrade:
            result['confidence'] = min(result['confidence'], 0.55)
            result['status_msg'] = "Fix Info"
            result['status_color'] = COLOR_ORANGE
        else:
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

        result['confidence'] = min(result['confidence'], 1.00)
        return result

    def _search_best_cp(self, residual, test_scope, is_context_match):
        best_res = {"std_cp": None, "raw_score": 0.0, "final_conf": 0.0}
        resid_nums = set(re.findall(r'\d+', residual))
        resid_lower = residual.lower()

        for test_name in test_scope:
            cps = self.cp_map.get(test_name, {})
            for std_cp, aliases in cps.items():
                candidates = [std_cp] + aliases
                for cand in candidates:
                    cand_lower = cand.lower()

                    # 1. 模糊相似度
                    score_w = fuzz.WRatio(resid_lower, cand_lower) / 100.0
                    score_sort = fuzz.token_sort_ratio(resid_lower, cand_lower) / 100.0
                    f_fuzzy = max(score_w, score_sort)

                    # 2. 数字指纹 (🔥 核心修复 🔥)
                    cand_nums = set(re.findall(r'\d+', cand))
                    f_num = 0.0

                    if resid_nums:
                        if cand_nums:
                            # 双方都有数字 -> 必须匹配
                            if resid_nums == cand_nums:
                                f_num = 1.0
                            elif resid_nums.intersection(cand_nums):
                                f_num = 0.5
                            else:
                                f_num = -1.0  # 数字冲突
                        else:
                            # 🔥 修复点：用户有数字(120万)，标准词没数字(T0) -> 冲突！
                            f_num = -1.0
                    else:
                        # 用户没数字，标准词有数字 -> 惩罚
                        if cand_nums: f_num = -0.2

                    # 3. 长度惩罚
                    f_len = 1.0
                    if len(resid_lower) > 0 and len(cand_lower) > 0:
                        ratio = min(len(resid_lower), len(cand_lower)) / max(len(resid_lower), len(cand_lower))
                        if ratio < 0.3: f_len = 0.5

                    f_context = 1.0 if is_context_match else 0.0
                    w_fuzzy, w_num, w_context = 0.35, 0.55, 0.10

                    raw_score = 0.2 + (w_fuzzy * f_fuzzy + w_num * f_num + w_context * f_context) * f_len
                    final_conf = self._sigmoid(raw_score)

                    if final_conf > best_res['final_conf']:
                        best_res['std_cp'] = std_cp
                        best_res['raw_score'] = raw_score
                        best_res['final_conf'] = final_conf

        # 🔥🔥🔥 修复点：垃圾分数熔断机制 🔥🔥🔥
        # 如果费半天劲算出来的最高分连 0.4 都不到，那就别瞎猜了
        if best_res['final_conf'] < 0.4:
            return {"std_cp": None, "raw_score": 0.0, "final_conf": 0.0}

        return best_res

    def _sigmoid(self, x):
        try:
            return 1 / (1 + math.exp(-self.LOGISTIC_K * (x - self.LOGISTIC_X0)))
        except OverflowError:
            return 0.0 if x < self.LOGISTIC_X0 else 1.0