import os

# 颜色定义
COLOR_GREEN = "#E8F5E9"  # 浅绿背景
COLOR_YELLOW = "#FFFDE7" # 浅黄背景
COLOR_ORANGE = "#FFF3E0" # 浅橙背景
COLOR_RED = "#FFEBEE"    # 浅红背景

# 支持的图片格式（元组形式，用于 endswith 检查）
SUPPORTED_IMAGE_FORMATS = (
    # JPEG 系列
    '.jpg', '.jpeg', '.jpe', '.jfif',
    # PNG
    '.png',
    # BMP
    '.bmp', '.dib',
    # GIF
    '.gif',
    # TIFF
    '.tif', '.tiff',
    # WEBP
    '.webp',
    # 其他常见格式
    '.ico',
)

# 路径常量
APP_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CONFIG_DIR = os.path.join(APP_ROOT, 'config')
ASSETS_DIR = os.path.join(APP_ROOT, 'assets')

# 默认设置 JSON
DEFAULT_SETTINGS = {
  "last_session": {
      "excel_path": "",
      "regular_output_dir": "",
      "issue_output_dir": ""
  },
  "excel_header_map": {
    "Build": "Build",
    "Config": "Config",
    "Rel_No": "No#",
    "SN": "SN",
    "Mode": "Mode",
    "WF": "WF",
    "Test": "Test"
  },
  "regular_photo": {
    "template_name": "{Build}_{Config}_{Rel_No}_{SN}_{Mode}_{WF}-{Test}_{CP}-{O}",
    "template_folder": "{Test}/{Config}/{Mode}/{Rel_No}",
    "parsed_data_map": {
      "CP": "CP",
      "O": "Orient"
    }
  },
  "issue_photo": {
    "template_name": "{Build}_{Config}_{Rel_No}_{SN}_{Mode}_{WF}-{Test}_{CP}-{Issue}",
    "template_folder": "{Test}/{Config}/{Mode}/{Rel_No}/Issue",
    "parsed_data_map": {
      "CP": "CP",
      "Issue": "Issue"
    }
  },
  "illegal_chars": ["/", "\\", ":", "*", "?", "\"", "<", ">", "|"]
}

# 默认 CP Map
DEFAULT_CP_MAP = {
  "1mG": {
    "25Drop": ["25", "25c", "25cyc", "25cycles", "25drop", "t25"],
    "50Drop": ["50", "50c", "50cyc", "50cycles", "50drop", "t50"],
    "75Drop": ["75", "75c", "75cyc", "75cycles", "75drop", "t75"],
    "100Drop": ["100", "100c", "100cyc", "100cycles", "100drop", "t100"]
  },
  "Sit Test": {
    "25Cycles": ["25", "25c", "25cyc", "t25"],
    "50Cycles": ["50", "50c", "50cyc", "t50"]
  }
}

# 默认 Issue Map
DEFAULT_ISSUE_MAP = {
  "crack": ["crack", "cracked", "hsg crack", "crk", "破", "破裂", "裂纹", "破碎", "外壳破", "开裂"],
  "discoloration": ["discoloration", "discolor", "color change", "变色", "褪色", "发黄", "色差"],
  "scratch": ["scratch", "scratched", "scr", "划痕", "刮花", "擦伤"]
}