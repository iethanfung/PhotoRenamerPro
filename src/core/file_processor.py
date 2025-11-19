import os
import shutil
from src.utils.constants import COLOR_RED


class FileProcessor:
    def __init__(self, settings):
        self.settings = settings

    def generate_target_path(self, parse_result, output_dir_override=None):
        if not parse_result['rel_no'] or not parse_result['unit_data']:
            return None, None

        is_issue = (parse_result['type'] == 'Issue')
        config_key = 'issue_photo' if is_issue else 'regular_photo'

        template_name = self.settings[config_key]['template_name']
        template_folder = self.settings[config_key]['template_folder']
        parsed_map = self.settings[config_key]['parsed_data_map']

        base_out = output_dir_override
        if not base_out:
            base_out = self.settings['last_session'].get('issue_output_dir' if is_issue else 'regular_output_dir')

        if not base_out:
            return None, "No Output Dir"

        # 准备数据
        data = parse_result['unit_data'].copy()

        cp_key = parsed_map.get('CP', 'CP')
        std_cp = parse_result['std_cp']
        if not std_cp or std_cp == "[Unknown CP]":
            std_cp = "UnknownCP"
        data[cp_key] = std_cp

        if is_issue:
            issue_key = parsed_map.get('Issue', 'Issue')
            data[issue_key] = parse_result['detail']
        else:
            orient_key = parsed_map.get('O', 'Orient')
            data[orient_key] = parse_result['detail']

        # 1. 生成文件名 (is_folder=False, 所有非法字符都替换)
        filename = self._fill_template(template_name, data, is_folder=False)
        filename += parse_result['ext']

        # 2. 生成文件夹路径 (is_folder=True, 保留 / 和 \)
        folder_relative = self._fill_template(template_folder, data, is_folder=True)

        # 标准化路径
        folder_relative = os.path.normpath(folder_relative)

        full_path = os.path.join(base_out, folder_relative, filename)

        return full_path, filename

    def _fill_template(self, template, data, is_folder=False):
        result = template
        illegal_chars = self.settings.get('illegal_chars', [])

        # 1. 先处理数据值中的非法字符
        safe_data = {}
        for key, val in data.items():
            val_str = str(val).strip()
            # 无论如何，数据值里不能有非法字符 (比如机台号里不能有 /)
            for char in illegal_chars:
                val_str = val_str.replace(char, "-")
            safe_data[key] = val_str

        # 2. 替换变量
        for key, val in safe_data.items():
            result = result.replace(f"{{{key}}}", val)

        # 3. 最后清理模板本身可能残留的非法字符
        # 如果是文件夹模式，保留路径分隔符 / 和 \
        chars_to_strip = list(illegal_chars)
        if is_folder:
            if '/' in chars_to_strip: chars_to_strip.remove('/')
            if '\\' in chars_to_strip: chars_to_strip.remove('\\')

        for char in chars_to_strip:
            result = result.replace(char, "-")

        return result

    def check_duplicate(self, target_path):
        if os.path.exists(target_path):
            return True
        return False