"""
图片生成模块
使用 Firefly Card API 将 Markdown 内容转换为精美图片
根据内容长度和结构智能调整尺寸和排版参数
"""
import os
import base64
import requests
from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path

from src.config import (
    FIREFLY_API_URL,
    FIREFLY_API_KEY,
    FIREFLY_DEFAULT_CONFIG,
    ENABLE_IMAGE_GENERATION,
    OUTPUT_DIR
)


@dataclass
class ContentAnalysis:
    """内容分析结果"""
    total_lines: int          # 总行数
    content_lines: int        # 内容行数（不含空行）
    headings: Dict[str, int]  # 各级标题数量
    list_items: int           # 列表项数量
    categories: int           # 分类数量
    max_line_length: int      # 最长行字符数
    total_chars: int          # 总字符数
    complexity: str           # 复杂度：simple/standard/detailed/complete


class ImageGenerator:
    """Firefly Card API 图片生成器"""

    # 尺寸配置
    MIN_WIDTH = 440
    MAX_WIDTH = 680
    MIN_HEIGHT = 500
    MAX_HEIGHT = 2000

    # 排版常量（基于中文阅读习惯）
    # 中文阅读舒适宽度：每行 20-28 个汉字
    CHAR_PER_LINE = 24        # 每行目标字符数
    AVG_CHAR_WIDTH = 14       # 平均字符宽度（像素）
    LINE_HEIGHT_RATIO = 1.6   # 行高与字号比
    PADDING_RATIO = 0.10      # 边距占宽度比例

    def __init__(self, api_url: str = None, api_key: str = None):
        """
        初始化图片生成器

        Args:
            api_url: Firefly API 地址
            api_key: API 密钥（如果需要）
        """
        self.api_url = api_url or FIREFLY_API_URL
        self.api_key = api_key or FIREFLY_API_KEY
        self.default_config = FIREFLY_DEFAULT_CONFIG.copy()
        self.enabled = ENABLE_IMAGE_GENERATION

    def _analyze_content(self, content: str) -> ContentAnalysis:
        """
        分析内容结构

        Args:
            content: Markdown 内容

        Returns:
            内容分析结果
        """
        lines = content.split('\n')
        analysis = ContentAnalysis(
            total_lines=len(lines),
            content_lines=0,
            headings={"#": 0, "##": 0, "###": 0},
            list_items=0,
            categories=0,
            max_line_length=0,
            total_chars=0,
            complexity="simple"
        )

        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue

            analysis.content_lines += 1
            analysis.total_chars += len(stripped)
            analysis.max_line_length = max(analysis.max_line_length, len(stripped))

            # 统计标题
            if stripped.startswith("# "):
                analysis.headings["#"] += 1
            elif stripped.startswith("## "):
                analysis.headings["##"] += 1
            elif stripped.startswith("### "):
                analysis.headings["###"] += 1
                analysis.categories += 1
            # 统计列表项
            elif stripped.startswith("- ") or stripped.startswith("* "):
                analysis.list_items += 1

        # 判断复杂度
        if analysis.content_lines < 12:
            analysis.complexity = "simple"
        elif analysis.content_lines < 22:
            analysis.complexity = "standard"
        elif analysis.content_lines < 38:
            analysis.complexity = "detailed"
        else:
            analysis.complexity = "complete"

        return analysis

    def _get_optimal_config(self, analysis: ContentAnalysis) -> Dict[str, Any]:
        """
        根据内容分析结果获取最优配置

        Args:
            analysis: 内容分析结果

        Returns:
            最优配置字典
        """
        # 根据复杂度确定基础配置
        configs = {
            "simple": {
                "width": 480,
                "padding": 18,
                "fontScale": 1.05,
                "base_height": 120,
                "line_height": 22,
            },
            "standard": {
                "width": 540,
                "padding": 22,
                "fontScale": 1.1,
                "base_height": 140,
                "line_height": 24,
            },
            "detailed": {
                "width": 600,
                "padding": 26,
                "fontScale": 1.15,
                "base_height": 160,
                "line_height": 26,
            },
            "complete": {
                "width": 660,
                "padding": 30,
                "fontScale": 1.2,
                "base_height": 180,
                "line_height": 28,
            }
        }

        base_config = configs.get(analysis.complexity, configs["standard"])

        # 根据最长行调整宽度
        # 确保最长行能舒适显示（每行约 CHAR_PER_LINE 个字符）
        min_width_for_content = analysis.max_line_length * self.AVG_CHAR_WIDTH
        adjusted_width = max(base_config["width"], min_width_for_content)
        adjusted_width = min(adjusted_width, self.MAX_WIDTH)

        # 动态调整 padding（保持 8-12% 的比例）
        adjusted_padding = int(adjusted_width * self.PADDING_RATIO)
        adjusted_padding = max(16, min(adjusted_padding, 36))

        return {
            "width": adjusted_width,
            "padding": adjusted_padding,
            "fontScale": base_config["fontScale"],
            "base_height": base_config["base_height"],
            "line_height": base_config["line_height"],
            "complexity": analysis.complexity
        }

    def _calculate_dimensions(self, content: str) -> Tuple[int, int, str, Dict[str, Any]]:
        """
        计算最佳图片尺寸和配置

        Args:
            content: Markdown 内容

        Returns:
            (width, height, ratio, config)
        """
        # 分析内容
        analysis = self._analyze_content(content)

        # 获取最优配置
        opt_config = self._get_optimal_config(analysis)

        width = opt_config["width"]
        padding = opt_config["padding"]
        base_height = opt_config["base_height"]
        line_height = opt_config["line_height"]

        # 计算有效内容宽度
        content_width = width - 2 * padding

        # 计算需要的行数（考虑换行）
        estimated_lines = 0

        for line in content.split('\n'):
            stripped = line.strip()
            if not stripped:
                continue

            # 去除 Markdown 标记后的纯文本长度
            text_len = len(stripped)

            # 根据元素类型估算行数
            if stripped.startswith("# "):
                estimated_lines += 2.2  # 一级标题占位多
            elif stripped.startswith("## "):
                estimated_lines += 1.9
            elif stripped.startswith("### "):
                estimated_lines += 1.6
            elif stripped.startswith("- ") or stripped.startswith("* "):
                # 列表项需要考虑换行
                lines_needed = max(1, (text_len * self.AVG_CHAR_WIDTH) / content_width)
                estimated_lines += lines_needed
            elif stripped.startswith("**"):
                # 粗体标题
                lines_needed = max(1, (text_len * self.AVG_CHAR_WIDTH * 1.1) / content_width)
                estimated_lines += lines_needed
            else:
                # 普通文本
                lines_needed = max(1, (text_len * self.AVG_CHAR_WIDTH) / content_width)
                estimated_lines += lines_needed

        # 计算高度
        content_height = int(estimated_lines * line_height)
        total_height = base_height + content_height

        # 限制高度范围
        total_height = max(self.MIN_HEIGHT, min(total_height, self.MAX_HEIGHT))

        # 计算最接近的比例
        ratio_wh = width / total_height
        if ratio_wh > 0.85:
            ratio = "1:1"
        elif ratio_wh > 0.7:
            ratio = "3:4"
        elif ratio_wh > 0.5:
            ratio = "2:3"
        elif ratio_wh > 0.4:
            ratio = "9:16"
        else:
            ratio = "9:19"

        # 打印调试信息
        print(f"   内容分析: 复杂度={analysis.complexity}, 行数={analysis.content_lines}")
        print(f"   尺寸配置: {width}x{total_height}, padding={padding}, ratio={ratio}")

        return width, total_height, ratio, opt_config

    def generate(
        self,
        markdown_content: str,
        output_path: str = None,
        custom_config: Dict[str, Any] = None
    ) -> Optional[str]:
        """
        生成图片

        Args:
            markdown_content: Markdown 格式的内容
            output_path: 图片保存路径，默认为 docs/images/{date}.png
            custom_config: 自定义配置，会与智能配置合并

        Returns:
            成功返回图片保存路径，失败返回 None
        """
        if not self.enabled:
            print("   图片生成功能未启用，跳过")
            return None

        if not markdown_content or not markdown_content.strip():
            print("   内容为空，跳过图片生成")
            return None

        # 构建请求数据
        request_data = self.default_config.copy()

        # 计算最佳尺寸和配置
        width, height, ratio, opt_config = self._calculate_dimensions(markdown_content)

        # 应用智能配置
        request_data["width"] = width
        request_data["height"] = height
        request_data["ratio"] = ratio
        request_data["padding"] = opt_config["padding"]
        request_data["fontScale"] = opt_config["fontScale"]

        # 用户自定义配置可以覆盖
        if custom_config:
            request_data.update(custom_config)

        request_data["content"] = markdown_content

        # 如果有 API Key，添加到请求头
        headers = {
            "Content-Type": "application/json"
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        try:
            print(f"   正在调用 Firefly API 生成图片...")
            print(f"   API URL: {self.api_url}")

            response = requests.post(
                self.api_url,
                json=request_data,
                headers=headers,
                timeout=60
            )

            # 检查响应状态
            response.raise_for_status()

            # 检查 Content-Type
            content_type = response.headers.get('Content-Type', '')

            # 如果直接返回二进制图片流
            if 'image/' in content_type:
                image_bytes = response.content

                # 确定保存路径
                if not output_path:
                    output_dir = Path(OUTPUT_DIR) / "images"
                    output_dir.mkdir(parents=True, exist_ok=True)
                    # 使用日期作为文件名
                    from datetime import datetime
                    date_str = datetime.now().strftime("%Y-%m-%d")
                    output_path = str(output_dir / f"{date_str}.png")

                # 保存图片
                Path(output_path).parent.mkdir(parents=True, exist_ok=True)
                with open(output_path, 'wb') as f:
                    f.write(image_bytes)

                print(f"   图片已保存: {output_path}")
                print(f"   文件大小: {len(image_bytes)} bytes")
                return output_path

            # 如果返回 JSON（兼容其他可能的响应格式）
            else:
                result = response.json()

                # API 返回的数据可能是 base64 编码的图片，或者是图片 URL
                if "data" in result:
                    image_data = result["data"]

                    if isinstance(image_data, str) and image_data.startswith("http"):
                        print(f"   图片 URL: {image_data}")
                        return image_data

                    if isinstance(image_data, str):
                        if image_data.startswith("data:image/"):
                            image_data = image_data.split(",", 1)[1]

                        image_bytes = base64.b64decode(image_data)

                        if not output_path:
                            output_dir = Path(OUTPUT_DIR) / "images"
                            output_dir.mkdir(parents=True, exist_ok=True)
                            output_path = str(output_dir / "daily-card.png")

                        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
                        with open(output_path, 'wb') as f:
                            f.write(image_bytes)

                        print(f"   图片已保存: {output_path}")
                        return output_path

                if "imageUrl" in result:
                    print(f"   图片 URL: {result['imageUrl']}")
                    return result["imageUrl"]

                if "url" in result:
                    print(f"   图片 URL: {result['url']}")
                    return result["url"]

                print(f"   响应 Content-Type: {content_type}")
                print(f"   响应内容: {result}")
                print("   无法从响应中提取图片数据")
                return None

        except requests.exceptions.RequestException as e:
            print(f"   API 请求失败: {e}")
            return None
        except Exception as e:
            print(f"   图片生成失败: {e}")
            return None

    def generate_from_analysis_result(
        self,
        analysis_result: Dict[str, Any],
        output_path: str = None
    ) -> Optional[str]:
        """
        从分析结果生成 Markdown 并转换为图片

        Args:
            analysis_result: Claude 分析结果
            output_path: 图片保存路径

        Returns:
            成功返回图片路径，失败返回 None
        """
        markdown = self._build_card_markdown(analysis_result)
        return self.generate(markdown, output_path)

    def _build_card_markdown(self, result: Dict[str, Any]) -> str:
        """
        构建适合卡片显示的精简 Markdown

        Args:
            result: 分析结果

        Returns:
            Markdown 格式的字符串
        """
        date = result.get("date", "")
        summary = result.get("summary", [])
        categories = result.get("categories", [])
        keywords = result.get("keywords", [])

        # 格式化日期
        try:
            from datetime import datetime
            dt = datetime.strptime(date, "%Y-%m-%d")
            formatted_date = f"{dt.year}年{dt.month}月{dt.day}日"
        except:
            formatted_date = date

        # 构建标题
        lines = [f"# AI Daily\n## {formatted_date}\n"]

        # 核心摘要
        if summary:
            lines.append("### 核心摘要")
            for item in summary[:5]:
                lines.append(f"- {item}")
            lines.append("")

        # 分类资讯
        for cat in categories:
            if not cat.get("items"):
                continue

            cat_name = cat.get("name", "")
            cat_items = cat.get("items", [])

            lines.append(f"### {cat_name}")
            for item in cat_items[:3]:
                title = item.get("title", "")
                lines.append(f"**{title}**")
            lines.append("")

        # 关键词
        if keywords:
            lines.append(f"{' '.join(['#' + kw for kw in keywords[:8]])}")

        return "\n".join(lines)


def generate_card_image(
    markdown_content: str,
    output_path: str = None
) -> Optional[str]:
    """便捷函数：生成卡片图片"""
    generator = ImageGenerator()
    return generator.generate(markdown_content, output_path)


def generate_card_from_analysis(
    analysis_result: Dict[str, Any],
    output_path: str = None
) -> Optional[str]:
    """便捷函数：从分析结果生成卡片图片"""
    generator = ImageGenerator()
    return generator.generate_from_analysis_result(analysis_result, output_path)
