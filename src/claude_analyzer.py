"""
Claude 分析模块
使用 Claude API 对资讯内容进行智能分析、分类和摘要
"""
import os
import json
from typing import Dict, Any, Optional
from anthropic import Anthropic

from src.config import (
    ANTHROPIC_BASE_URL,
    ZHIPU_API_KEY,
    CLAUDE_MODEL,
    CLAUDE_MAX_TOKENS,
    CATEGORIES,
    THEMES,
    DEFAULT_THEME
)


class ClaudeAnalyzer:
    """Claude AI 分析器"""

    def __init__(self, api_key: str = None, base_url: str = None):
        """
        初始化 Claude 客户端

        Args:
            api_key: API 密钥，默认从环境变量读取
            base_url: API 基础 URL，默认从环境变量读取
        """
        self.api_key = api_key or ZHIPU_API_KEY
        self.base_url = base_url or ANTHROPIC_BASE_URL
        self.model = CLAUDE_MODEL
        self.max_tokens = CLAUDE_MAX_TOKENS

        if not self.api_key:
            raise ValueError("ZHIPU_API_KEY 环境变量未设置")

        try:
            self.client = Anthropic(
                base_url=self.base_url,
                api_key=self.api_key
            )
            print(f"✅ Claude 客户端初始化成功")
            print(f"   Base URL: {self.base_url}")
            print(f"   Model: {self.model}")
        except Exception as e:
            raise Exception(f"Claude 客户端初始化失败: {e}")

    def analyze(self, content: Dict[str, Any], target_date: str) -> Dict[str, Any]:
        """
        分析资讯内容

        Args:
            content: RSS 内容字典
            target_date: 目标日期

        Returns:
            分析结果字典，包含：
            - status: success/empty/error
            - date: 日期
            - theme: 主题名称
            - summary: 核心摘要列表
            - keywords: 关键词列表
            - categories: 分类资讯列表
        """
        if not content or not content.get("content"):
            return self._empty_result(target_date, "内容为空")

        print(f"🤖 正在调用 Claude 分析内容...")

        # 构建提示词
        prompt = self._build_prompt(content, target_date)

        try:
            # 调用 Claude API
            response = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=0.3,  # 较低温度保证稳定性
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )

            # 解析响应
            result_text = response.content[0].text
            print(f"✅ Claude 响应成功，响应长度: {len(result_text)} 字符")

            # 解析 JSON 结果
            result = self._parse_result(result_text, target_date)

            return result

        except Exception as e:
            print(f"❌ Claude API 调用失败: {e}")
            # 返回带有原始内容的结果，让生成器可以继续工作
            return {
                "status": "success",
                "date": target_date,
                "theme": DEFAULT_THEME,
                "summary": [
                    "AI 资讯分析遇到技术问题，以下是原始内容摘要",
                    f"标题: {content.get('title', '')[:100]}..."
                ],
                "keywords": ["AI", "资讯"],
                "categories": self._fallback_categories(content),
                "raw_content": content
            }

    def _build_prompt(self, content: Dict[str, Any], target_date: str) -> str:
        """构建 Claude 提示词"""
        # 构建分类说明
        category_desc = "\n".join([
            f"- {cat['icon']} {cat['name']}: {cat['description']}"
            for cat in CATEGORIES.values()
        ])

        # 构建主题说明
        theme_desc = "\n".join([
            f"- {key}: {theme['name']} - {theme['description']}"
            for key, theme in THEMES.items()
        ])

        prompt = f"""你是一个专业的 AI 资讯分析师，请对以下 AI 日报内容进行深度分析。

【目标日期】
{target_date}

【原始资讯内容】
标题: {content.get('title', '')}
链接: {content.get('link', '')}

完整内容:
{content.get('content', '')[:15000]}

---

【任务要求】

1. **状态检查**
   - 如果内容确实存在且有效，返回状态为 "success"
   - 如果内容为空或无效，返回状态为 "empty"

2. **核心摘要** (summary)
   - 生成 3-5 条今日最重要的 AI 资讯要点
   - 每条摘要不超过 50 字，简洁明了
   - 按重要性排序

3. **智能分类** (categories)
   将资讯按以下维度分类（可空）:
{category_desc}

   每个分类包含:
   - key: 分类标识 (model/product/research/tools/funding/events)
   - name: 分类名称
   - icon: 分类图标
   - items: 该分类下的资讯列表

   每条资讯包含:
   - title: 简化版标题（适合快速浏览，不超过40字）
   - summary: 一句话核心要点（不超过80字）
   - url: 相关链接（如果有的话）
   - tags: 相关标签（如公司名、产品名）

4. **关键词提取** (keywords)
   - 提取 5-10 个今日热门关键词
   - 包括: 公司名称、人物、技术名词、产品名
   - 去重并按重要性排序

5. **主题选择** (theme)
   根据内容主类别选择最佳主题:
{theme_desc}

   选择规则:
   - 模型/框架/开发工具 → blue (柔和蓝色)
   - 企业动态/产品发布 → indigo (深靛蓝)
   - 融资/并购/金融 → teal (冷色青绿)
   - 创意/AIGC/设计 → purple (优雅紫色)
   - 医疗/健康AI → green (清新绿色)
   - 热点/争议话题 → orange (温暖橙色)
   - 研究/论文/数据 → gray (中性灰色)
   - 应用/生活/消费 → pink (玫瑰粉色)

【输出格式】

请严格按照以下 JSON 格式输出，不要包含任何其他文字说明：

```json
{{
  "status": "success",
  "date": "{target_date}",
  "theme": "blue",
  "summary": [
    "第一条核心摘要",
    "第二条核心摘要",
    "第三条核心摘要"
  ],
  "keywords": ["Anthropic", "Google", "Claude", "MedGemma", "LangChain"],
  "categories": [
    {{
      "key": "model",
      "name": "模型发布",
      "icon": "🤖",
      "items": [
        {{
          "title": "MedGemma 1.5 发布",
          "summary": "Google 发布 4B 参数医疗多模态模型，支持 3D 影像分析",
          "url": "https://news.smol.ai/issues/26-01-13-not-much/",
          "tags": ["Google", "MedGemma", "医疗AI"]
        }}
      ]
    }},
    {{
      "key": "product",
      "name": "产品动态",
      "icon": "💼",
      "items": []
    }}
  ]
}}
```

重要：只输出 JSON，不要有任何其他说明文字。确保 JSON 格式正确有效。
"""
        return prompt

    def _parse_result(self, result_text: str, target_date: str) -> Dict[str, Any]:
        """解析 Claude 的响应结果"""
        # 清理可能的 markdown 代码块标记
        result_text = result_text.strip()
        if result_text.startswith("```json"):
            result_text = result_text[7:]
        if result_text.startswith("```"):
            result_text = result_text[3:]
        if result_text.endswith("```"):
            result_text = result_text[:-3]
        result_text = result_text.strip()

        try:
            result = json.loads(result_text)

            # 验证必要字段
            if "status" not in result:
                result["status"] = "success"
            if "date" not in result:
                result["date"] = target_date
            if "theme" not in result:
                result["theme"] = DEFAULT_THEME
            if "summary" not in result:
                result["summary"] = []
            if "keywords" not in result:
                result["keywords"] = []
            if "categories" not in result:
                result["categories"] = []

            print(f"✅ 结果解析成功")
            print(f"   主题: {result.get('theme')}")
            print(f"   摘要数: {len(result.get('summary', []))}")
            print(f"   关键词数: {len(result.get('keywords', []))}")
            print(f"   分类数: {len(result.get('categories', []))}")

            return result

        except json.JSONDecodeError as e:
            print(f"❌ JSON 解析失败: {e}")
            print(f"   原始响应: {result_text[:500]}...")

            # 返回一个基本的成功结果，使用原始内容
            return {
                "status": "success",
                "date": target_date,
                "theme": DEFAULT_THEME,
                "summary": ["AI 资讯已获取"],
                "keywords": ["AI"],
                "categories": [],
                "parse_error": str(e)
            }

    def _empty_result(self, target_date: str, reason: str) -> Dict[str, Any]:
        """返回空结果"""
        return {
            "status": "empty",
            "date": target_date,
            "theme": DEFAULT_THEME,
            "summary": [],
            "keywords": [],
            "categories": [],
            "reason": reason
        }

    def _fallback_categories(self, content: Dict[str, Any]) -> list:
        """当 Claude 解析失败时的备用分类"""
        # 简单地将原始内容作为一个通用资讯
        title = content.get('title', '')[:100]
        description = content.get('description', '')[:200]
        url = content.get('link', '')

        return [
            {
                "key": "model",
                "name": "模型发布",
                "icon": "🤖",
                "items": [
                    {
                        "title": title,
                        "summary": description,
                        "url": url,
                        "tags": ["AI"]
                    }
                ]
            }
        ]


def analyze_content(content: Dict[str, Any], target_date: str) -> Dict[str, Any]:
    """便捷函数：分析资讯内容"""
    analyzer = ClaudeAnalyzer()
    return analyzer.analyze(content, target_date)
