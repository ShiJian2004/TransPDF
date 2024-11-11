import platform
import shutil
from pathlib import Path

class PlatformAdapter:
    @staticmethod
    def get_poppler_path():
        """获取poppler路径"""
        if platform.system() == "Windows":
            # 检查程序目录下的poppler
            bundled_path = Path(__file__).parent.parent / "poppler-xx" / "Library" / "bin"
            if bundled_path.exists():
                return str(bundled_path)
            
            # 检查环境变量中的poppler
            poppler_path = shutil.which("pdftoppm")
            if poppler_path:
                return str(Path(poppler_path).parent)
            return None
            
        # macOS和Linux返回None，使用系统安装的poppler
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