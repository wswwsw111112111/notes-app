"""
测试数据生成器
用于生成测试所需的各种文件和数据
"""

import os
import io
from PIL import Image
import random
import string


class TestDataGenerator:
    """测试数据生成器类"""

    def __init__(self, output_dir='test_files'):
        """初始化，创建输出目录"""
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def generate_test_image(self, filename='test_image.png', size=(800, 600), color=None):
        """
        生成测试图片
        :param filename: 文件名
        :param size: 图片尺寸 (宽, 高)
        :param color: RGB颜色元组，如 (255, 0, 0) 为红色，None为随机
        :return: 文件路径
        """
        if color is None:
            color = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))

        img = Image.new('RGB', size, color=color)
        filepath = os.path.join(self.output_dir, filename)
        img.save(filepath, 'PNG')

        print(f"✅ 生成测试图片: {filepath} ({size[0]}x{size[1]}, {os.path.getsize(filepath)} bytes)")
        return filepath

    def generate_test_text_file(self, filename='test_document.txt', size_kb=10):
        """
        生成测试文本文件
        :param filename: 文件名
        :param size_kb: 文件大小（KB）
        :return: 文件路径
        """
        filepath = os.path.join(self.output_dir, filename)

        content = self._generate_random_text(size_kb * 1024)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)

        print(f"✅ 生成测试文本: {filepath} ({os.path.getsize(filepath)} bytes)")
        return filepath

    def generate_large_file(self, filename='large_file.bin', size_mb=50):
        """
        生成大文件（用于测试存储限制）
        :param filename: 文件名
        :param size_mb: 文件大小（MB）
        :return: 文件路径
        """
        filepath = os.path.join(self.output_dir, filename)

        chunk_size = 1024 * 1024  # 1MB chunks
        with open(filepath, 'wb') as f:
            for _ in range(size_mb):
                f.write(os.urandom(chunk_size))

        print(f"✅ 生成大文件: {filepath} ({os.path.getsize(filepath)} bytes, {size_mb}MB)")
        return filepath

    def generate_multiple_images(self, count=10, prefix='gallery_'):
        """
        生成多张图片（用于测试画廊功能）
        :param count: 图片数量
        :param prefix: 文件名前缀
        :return: 文件路径列表
        """
        filepaths = []
        for i in range(count):
            filename = f"{prefix}{i+1:02d}.png"
            color = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
            size = (random.randint(400, 1200), random.randint(300, 900))
            filepath = self.generate_test_image(filename, size, color)
            filepaths.append(filepath)

        print(f"✅ 共生成 {count} 张图片用于画廊测试")
        return filepaths

    def generate_mixed_files(self, image_count=5, doc_count=3):
        """
        生成混合类型文件（用于测试压缩包上传）
        :param image_count: 图片数量
        :param doc_count: 文档数量
        :return: 文件路径列表
        """
        filepaths = []

        # 生成图片
        for i in range(image_count):
            filepath = self.generate_test_image(f'mixed_img_{i+1}.png', size=(600, 400))
            filepaths.append(filepath)

        # 生成文档
        for i in range(doc_count):
            filepath = self.generate_test_text_file(f'mixed_doc_{i+1}.txt', size_kb=5)
            filepaths.append(filepath)

        print(f"✅ 生成混合文件: {image_count}张图片 + {doc_count}个文档")
        return filepaths

    def generate_invalid_file(self, filename='invalid_file.xyz'):
        """
        生成无效格式文件（用于测试文件验证）
        :param filename: 文件名
        :return: 文件路径
        """
        filepath = os.path.join(self.output_dir, filename)

        with open(filepath, 'wb') as f:
            f.write(b'This is an invalid file format')

        print(f"✅ 生成无效文件: {filepath}")
        return filepath

    def _generate_random_text(self, size_bytes):
        """生成指定大小的随机文本"""
        lines = []
        current_size = 0

        while current_size < size_bytes:
            line = ''.join(random.choices(string.ascii_letters + string.digits + ' ', k=80))
            lines.append(line + '\n')
            current_size += len(line) + 1

        return ''.join(lines)[:size_bytes]

    def cleanup(self):
        """清理生成的测试文件"""
        import shutil
        if os.path.exists(self.output_dir):
            shutil.rmtree(self.output_dir)
            print(f"🧹 已清理测试文件目录: {self.output_dir}")


def generate_all_test_data():
    """生成所有测试数据"""
    print("\n" + "=" * 70)
    print("开始生成测试数据")
    print("=" * 70 + "\n")

    generator = TestDataGenerator()

    # 1. 生成各种尺寸的测试图片
    print("\n📸 生成测试图片:")
    generator.generate_test_image('small_image.png', size=(200, 150))
    generator.generate_test_image('medium_image.jpg', size=(800, 600))
    generator.generate_test_image('large_image.png', size=(1920, 1080))

    # 2. 生成文本文件
    print("\n📄 生成测试文档:")
    generator.generate_test_text_file('small_doc.txt', size_kb=10)
    generator.generate_test_text_file('medium_doc.txt', size_kb=100)

    # 3. 生成画廊测试图片
    print("\n🖼️  生成画廊测试图片:")
    generator.generate_multiple_images(count=10, prefix='gallery_')

    # 4. 生成混合文件
    print("\n📦 生成混合文件:")
    generator.generate_mixed_files(image_count=5, doc_count=3)

    # 5. 生成大文件（测试存储限制）
    print("\n💾 生成大文件:")
    generator.generate_large_file('large_50mb.bin', size_mb=50)

    # 6. 生成无效文件
    print("\n❌ 生成无效文件:")
    generator.generate_invalid_file('invalid.xyz')

    print("\n" + "=" * 70)
    print("✅ 测试数据生成完成！")
    print(f"📁 文件位置: {os.path.abspath(generator.output_dir)}")
    print("=" * 70 + "\n")

    return generator


if __name__ == '__main__':
    # 生成测试数据
    generator = generate_all_test_data()

    # 询问是否清理
    print("\n提示: 测试完成后，可以运行以下命令清理测试文件:")
    print(f"  python -c \"from test_data_generator import TestDataGenerator; TestDataGenerator().cleanup()\"")