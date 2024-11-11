import platform
import shutil
from pathlib import Path
import sys
import os

def get_base_path():
    """获取基础路径（考虑打包后的情况）"""
    if getattr(sys, 'frozen', False):
        # 打包后的环境
        return os.path.dirname(sys.executable)
    # 开发环境
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
class PlatformAdapter:
    @staticmethod
    def get_poppler_path():
        """获取poppler路径"""
        if platform.system() == "Windows":
            # 检查打包后的路径
            base_path = PlatformAdapter.get_base_path()
            bundled_path = Path(base_path) / "poppler-xx" / "Library" / "bin"
            if bundled_path.exists():
                return str(bundled_path)
            
            # 检查开发环境路径
            dev_path = Path(__file__).parent.parent / "poppler-xx" / "Library" / "bin"
            if dev_path.exists():
                return str(dev_path)
            
            # 检查环境变量
            poppler_path = shutil.which("pdftoppm")
            if poppler_path:
                return str(Path(poppler_path).parent)
            return None
            
        return None

    @staticmethod
    def normalize_path(path: str) -> str:
        """统一路径格式"""
        return str(Path(path))

    @staticmethod
    def create_temp_dir(base_path: str) -> Path:
        """创建临时目录"""
        temp_dir = Path(base_path).parent / "temp_images"
        temp_dir.mkdir(parents=True, exist_ok=True)
        return temp_dir