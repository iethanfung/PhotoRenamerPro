import os
import re
from rapidfuzz import process, fuzz
from loguru import logger
from src.utils.constants import COLOR_GREEN, COLOR_YELLOW, COLOR_ORANGE, COLOR_RED


class ParserEngine:
    def __init__(self, excel_engine, settings, cp_map, issue_map):
        self.excel = excel_engine
        self.settings = settings
        self.cp_map = cp_map
        self.issue_map = issue_map

    def parse_filename(self, file_path):
        filename_only = os.path.basename(file_path)
        base_name, ext = os.path.splitext(filename_only)

        tokens = re.split(r'[_\-\s\.]+', base_name)
        tokens = [t for t in tokens if t]

        result = {
            "original": file_path,
            "base_name": base_name,
            "ext": ext,
            "rel_no": None,
            "unit_data": None,
            "raw_cp": "",
            "std_cp": "[Unknown CP]",
            "raw_detail": "",  # 🔥 新增：存储原始的 Issue 或 Orient 词
            "type": "Unknown",
            "detail": "",
            "confidence": 0.0,
            "status_color": COLOR_RED,
            "status_msg": "",
            "tokens": tokens
        }

        logger.info(f"🟢 [开始解析] 文件名: {base_name}")

        # 1. 寻找 Rel No
        candidates_rows = []
        for t in tokens:
            clean_num = None
            if re.match(r'^\d+$', t):
                clean_num = t
            elif re.match(r'(?i)^rel\d+$', t):
                clean_num = re.search(r'\d+', t).group()

            if clean_num:
                info = self.excel.get_unit_info(clean_num)
                if info:
                    candidates_rows = info if isinstance(info, list) else [info]
                    first_row = candidates_rows[0]
                    val = first_row.get('Rel_No')
                    if not val or val == 'UNKNOWN':
                        user_col = self.settings['excel_header_map'].get('Rel_No', 'No#').strip()
                        val = first_row.get(user_col)
                    if not val or val == 'UNKNOWN':
                        val = clean_num
                    result['rel_no'] = val
                    result['confidence'] = 0.4
                    break

        if not result['rel_no']:
            result['status_msg'] = "Rel No Not Found"
            return result

        # 2. 确定 Type
        orient_match = None
        orient_token = None
        for t in tokens:
            if re.match(r'(?i)^o\d+$', t):
                orient_match = t.upper()
                orient_token = t
                break

        if orient_match:
            result['type'] = "Regular"
            result['detail'] = orient_match
            result['raw_detail'] = orient_token  # 记录原始 Orientation
            result['confidence'] += 0.2
        else:
            result['type'] = "Issue"
            search_tokens = [t for t in tokens if t != result['rel_no']]
            search_str = " ".join(search_tokens).lower()
            best_issue = None
            for std_issue, aliases in self.issue_map.items():
                for alias in aliases:
                    if alias.lower() in search_str:
                        best_issue = std_issue
                        result['raw_detail'] = alias  # 🔥 记录匹配到的原始 Issue 词
                        break
                if best_issue: break
            if best_issue:
                result['detail'] = best_issue
                result['std_cp'] = best_issue
                result['confidence'] += 0.3
            else:
                result['detail'] = tokens[-1]
                result['raw_detail'] = tokens[-1]  # 🔥 没匹配到，记录最后一个词为原始词
                result['status_msg'] = "Unknown Issue"

        # 3. 智能匹配 CP
        candidate_tokens = [t for t in tokens if t != orient_token and t != result['rel_no']]

        best_score = 0
        best_row_match = None
        best_cp_match = None

        # A. 优先策略
        for row in candidates_rows:
            test_name = str(row.get('Test', 'Unknown')).strip()
            valid_cps = self.cp_map.get(test_name, {})
            cp_lookup = {}
            for std_cp, aliases in valid_cps.items():
                cp_lookup[std_cp.lower()] = std_cp
                for alias in aliases:
                    cp_lookup[str(alias).lower()] = std_cp
            if not cp_lookup: continue

            for t in candidate_tokens:
                t_lower = t.lower()
                # 排除已识别为 Issue 的词
                if result['type'] == 'Issue' and t_lower in str(result['raw_detail']).lower():
                    continue

                if t_lower in cp_lookup:
                    score = 100
                    if score > best_score:
                        best_score = score
                        best_cp_match = cp_lookup[t_lower]
                        best_row_match = row
                        result['raw_cp'] = t
                else:
                    match = process.extractOne(t_lower, cp_lookup.keys(), scorer=fuzz.WRatio)
                    if match:
                        key, score, idx = match
                        if score > 88 and score > best_score:
                            best_score = score
                            best_cp_match = cp_lookup[key]
                            best_row_match = row
                            result['raw_cp'] = key

        # B. 兜底策略 (全网搜索)
        if not best_cp_match and candidate_tokens:
            for test_name, cps in self.cp_map.items():
                temp_lookup = {}
                for std_cp, aliases in cps.items():
                    temp_lookup[std_cp.lower()] = std_cp
                    for alias in aliases:
                        temp_lookup[str(alias).lower()] = std_cp

                for t in candidate_tokens:
                    t_lower = t.lower()
                    if result['type'] == 'Issue' and t_lower in str(result['raw_detail']).lower(): continue
                    if t_lower in temp_lookup:
                        best_cp_match = temp_lookup[t_lower]
                        result['raw_cp'] = t
                        best_row_match = candidates_rows[0].copy()
                        best_row_match['Test'] = test_name
                        break
                if best_cp_match: break

        # 4. 结果结算
        if best_row_match:
            result['unit_data'] = best_row_match
            if best_cp_match:
                result['std_cp'] = best_cp_match
            else:
                result['std_cp'] = "[Unknown CP]"
                if not result['raw_cp'] and candidate_tokens:
                    # 排除 Issue 词
                    potential = [x for x in candidate_tokens if x != result['raw_detail']]
                    if potential: result['raw_cp'] = potential[0]

            result['confidence'] += 0.4
        else:
            result['unit_data'] = candidates_rows[0]
            if not result['raw_cp'] and candidate_tokens:
                potential = [x for x in candidate_tokens if x != result['raw_detail']]
                if potential: result['raw_cp'] = potential[0]
            result['std_cp'] = "[Unknown CP]"

        # 5. 强制降级逻辑
        is_cp_missing = (not result['std_cp'] or result['std_cp'] == "[Unknown CP]")
        should_downgrade = False

        if result['type'] == 'Regular' and is_cp_missing:
            should_downgrade = True
        elif result['type'] == 'Issue' and is_cp_missing and result['raw_cp']:
            should_downgrade = True
            result['std_cp'] = "[Unknown CP]"

        if should_downgrade:
            result['confidence'] = min(result['confidence'], 0.6)
            result['status_msg'] = "Fix CP"
            result['status_color'] = COLOR_ORANGE
            return result

        # 6. 颜色逻辑
        if result['confidence'] >= 0.9:
            result['status_color'] = COLOR_GREEN
            result['status_msg'] = "Ready"
        elif result['confidence'] >= 0.5:
            result['status_color'] = COLOR_YELLOW
            if "Fix" not in result['status_msg']: result['status_msg'] = "Check"
        else:
            result['status_color'] = COLOR_RED
            result['status_msg'] = result.get('status_msg', "Error")

        result['confidence'] = min(result['confidence'], 1.0)
        return result