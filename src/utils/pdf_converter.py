from pdf2image import convert_from_path
import os
import logging
from typing import List
from pathlib import Path
from src.platform_adapter import PlatformAdapter

class PDFConverter:
    def __init__(self):
        self.logger = logging.getLogger('PDFConverter')
        self.logger.setLevel(logging.INFO)
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)

    def convert_pdf(self, pdf_path: str, output_dir: Path) -> List[str]:
        """
        将PDF转换为图片
        """
        try:
            # 确保输出目录存在
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # 获取平台相关的poppler路径
            poppler_path = PlatformAdapter.get_poppler_path()
            
            # 转换参数
            convert_params = {
                'output_folder': str(output_dir),
                'fmt': 'jpg',
                'output_file': Path(pdf_path).stem,
                'jpegopt': {'quality': 95, 'optimize': True}
            }
            
            # Windows下添加poppler路径
            if poppler_path:
                convert_params['poppler_path'] = poppler_path

            # 转换PDF
            images = convert_from_path(
                PlatformAdapter.normalize_path(pdf_path),
                **convert_params
            )
            
            # 获取生成的图片路径列表
            image_paths = sorted([
                str(output_dir / f"{Path(pdf_path).stem}-{i}.jpg")
                for i in range(len(images))
            ])
            
            self.logger.info(f"PDF转换完成，共生成 {len(image_paths)} 张图片")
            return image_paths

        except Exception as e:
            self.logger.error(f"PDF转换失败: {str(e)}")
            raise

    def cleanup_temp_files(self, image_paths: List[str]) -> None:
        """
        清理临时图片文件
        """
        try:
            for image_path in image_paths:
                try:
                    if os.path.exists(image_path):
                        os.remove(image_path)
                except Exception as e:
                    self.logger.warning(f"删除临时文件 {image_path} 失败: {str(e)}")
        except Exception as e:
            self.logger.warning(f"清理临时文件时出现警告: {str(e)}")