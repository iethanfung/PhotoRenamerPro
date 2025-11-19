from functools import lru_cache
from PySide6.QtGui import QPixmap, QImage
from PIL import Image, ImageOps


class ImageLoader:
    @staticmethod
    @lru_cache(maxsize=100)
    def load_thumbnail(path, max_size=(400, 400)):
        """加载图片并生成缩略图，使用缓存避免卡顿"""
        try:
            if not path:
                return None

            # 使用 Pillow 打开，处理 EXIF 旋转
            img = Image.open(path)
            img = ImageOps.exif_transpose(img)

            img.thumbnail(max_size, Image.Resampling.LANCZOS)

            # 转换为 QImage
            if img.mode == "RGB":
                r, g, b = img.split()
                img = Image.merge("RGB", (b, g, r))
                im2 = img.convert("RGBA")
                data = im2.tobytes("raw", "BGRA")
                qim = QImage(data, im2.width, im2.height, QImage.Format_ARGB32)
            else:
                im2 = img.convert("RGBA")
                data = im2.tobytes("raw", "BGRA")
                qim = QImage(data, im2.width, im2.height, QImage.Format_ARGB32)

            return QPixmap.fromImage(qim)
        except Exception as e:
            print(f"Error loading image {path}: {e}")
            return None