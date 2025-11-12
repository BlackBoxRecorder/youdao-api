# coding:utf-8
import requests
from requests.exceptions import RequestException
from bs4 import BeautifulSoup
from flask import Flask, jsonify, request
import argparse


class YoudaoAPI:
    """
    整合有道词典Web API和柯林斯词典数据的查询服务
    """

    def __init__(self):
        self.web_url = "http://dict.youdao.com/w/eng/{0}/#keyfrom=dict2.index"
        self.mobile_collins_url = "http://mobile.youdao.com/singledict?q={word}&dict=collins&le=eng&more=false"
        self.mobile_trans_sents_url = "http://mobile.youdao.com/singledict?q={word}&dict=blng_sents_part&le=eng&more=false"
        self.voice_url = "https://dict.youdao.com/dictvoice?type=1&audio={word}"

    def parse_web_html(self, html, word):
        """
        解析web版有道的网页，提取基础信息
        """
        try:
            soup = BeautifulSoup(html, "html.parser")
            root = soup.find(id="results-contents")

            if not root:
                return {}

            result = {
                "query": word,
                "errorCode": 0,
            }

            # 基本解释
            basic = root.find(id="phrsListTab")
            if basic:
                trans = basic.find(class_="trans-container")
                if trans:
                    result["basic"] = {}
                    result["basic"]["explains"] = [
                        tran.string for tran in trans.find_all("li") if tran.string
                    ]
                    # 中文
                    if len(result["basic"]["explains"]) == 0:
                        exp = trans.find(class_="wordGroup")
                        if exp:
                            result["basic"]["explains"].append(
                                " ".join(exp.stripped_strings)
                            )

                    # 音标
                    phons = basic.find_all(class_="phonetic", limit=2)
                    if len(phons) == 2:
                        # 确保音标文本存在且格式正确
                        us_phonetic = phons[1].string if phons[1].string else ""
                        # 移除音标中的括号并构建对象格式

                        if us_phonetic.startswith("[") and us_phonetic.endswith("]"):
                            us_phonetic_text = us_phonetic[1:-1]
                            result["basic"]["phonetic"] = {
                                "phonetic": us_phonetic_text,
                                "audio": f"https://dict.youdao.com/dictvoice?type=2&audio={word}",
                            }
                    elif len(phons) == 1:
                        phonetic = phons[0].string if phons[0].string else ""
                        if phonetic.startswith("[") and phonetic.endswith("]"):
                            phonetic_text = phonetic[1:-1]
                            result["basic"]["phonetic"] = {
                                "phonetic": phonetic_text,
                                "audio": f"https://dict.youdao.com/dictvoice?type=1&audio={word}",
                            }

            # 网络释义(短语)
            web = root.find(id="webPhrase")
            if web:
                web_list = []
                for wordgroup in web.find_all(class_="wordGroup", limit=4):
                    search_js = wordgroup.find(class_="search-js")
                    span = wordgroup.find("span")
                    if search_js and span:
                        key = search_js.string.strip() if search_js.string else ""
                        # 处理值列表
                        value_text = span.next_sibling
                        if value_text:
                            # 确保value_text是字符串类型
                            value_str = str(value_text) if value_text else ""
                            if value_str:
                                values = [
                                    v.strip() for v in value_str.split(";") if v.strip()
                                ]
                                if values:
                                    web_list.append({"key": key, "value": values})
                if web_list:
                    result["web"] = web_list

            return result
        except Exception as e:
            print(f"解析网页错误: {e}")
            return {}

    def get_web_result(self, word):
        """
        通过解析有道网页版获取基础数据
        """
        try:
            response = requests.get(self.web_url.format(word))
            response.raise_for_status()
            return self.parse_web_html(response.text, word)
        except RequestException as e:
            print(f"网络错误: {e}")
            return {}

    def clean_text(self, text):
        """清理文本，处理加粗标记等问题"""
        if not text:
            return ""
        # 移除多余的空白字符
        text = text.strip()
        # 替换不间断空格
        text = text.replace("\xa0", " ")
        # 规范化空格
        text = " ".join(text.split())
        return text

    def process_bold_text(self, soup_element):
        """处理包含加粗标签的文本"""
        if not soup_element:
            return ""

        text = ""
        for content in soup_element.contents:
            if hasattr(content, "name") and content.name == "b":
                # 加粗的单词前后添加空格
                text += " " + content.get_text(strip=True) + " "
            else:
                text_content = (
                    content.get_text(strip=True)
                    if hasattr(content, "get_text")
                    else str(content)
                )
                text += text_content

        # 清理文本
        return self.clean_text(text)

    def extract_collins_sentence(self, soup):
        """提取柯林斯词典数据"""
        collins_data = []
        # 查找柯林斯词典的主要容器
        collins_div = soup.find("div", class_="per-collins-entry")
        if collins_div:
            # 查找列表
            ul = collins_div.find("ul")
            if ul:
                for li in ul.find_all("li", class_="mcols-layout"):
                    item = {}
                    # 提取描述（去除例句和翻译）
                    desc_div = li.find("div", class_="col2")
                    if desc_div:
                        # 处理词性标注，添加逗号分隔
                        description_parts = []
                        contents = list(desc_div.contents)

                        for i, content in enumerate(contents):
                            if (
                                not hasattr(content, "name") or content.name != "div"
                            ):  # 不是例句容器
                                if (
                                    hasattr(content, "name")
                                    and content.name == "span"
                                    and content.get("title")
                                ):
                                    # 词性标注，添加逗号
                                    text = content.get_text(strip=True)
                                    if text:
                                        description_parts.append(text + "，")
                                elif hasattr(content, "name") and content.name == "b":
                                    # 处理加粗的单词
                                    text = " " + content.get_text(strip=True) + " "
                                    description_parts.append(text)
                                else:
                                    text = (
                                        content.get_text(strip=True)
                                        if hasattr(content, "get_text")
                                        else str(content).strip()
                                    )
                                    if text:
                                        description_parts.append(text)

                        item["description"] = self.clean_text(
                            "".join(description_parts)
                        )

                    # 提取例句和翻译
                    example_div = li.find("div", class_="mcols-layout")
                    if example_div:
                        p_elements = example_div.find_all("p", class_="secondary")
                        if len(p_elements) >= 1:
                            # 处理例句中的加粗标记
                            item["example"] = self.process_bold_text(p_elements[0])
                        if len(p_elements) >= 2:
                            item["translate"] = self.clean_text(
                                p_elements[1].get_text(strip=True)
                            )

                    # 只有当至少有一个字段存在时才添加
                    if item:
                        # 确保所有字段都存在，即使为空
                        item.setdefault("description", "")
                        item.setdefault("example", "")
                        item.setdefault("translate", "")
                        collins_data.append(item)

        return collins_data

    def extract_trans_sentences(self, soup):
        """提取双语例句数据"""
        trans_sents_data = []
        # 查找内容容器
        content_div = soup.find("div", class_="content")
        if content_div:
            ul = content_div.find("ul")
            if ul:
                for li in ul.find_all("li", class_="mcols-layout"):
                    item = {}
                    # 提取音频URL
                    audio_elem = li.find("a", class_="dictvoice")
                    if audio_elem and audio_elem.get("data-rel"):
                        item["audio_url"] = audio_elem.get("data-rel")
                    else:
                        item["audio_url"] = ""

                    # 提取例句和翻译
                    col2_div = li.find("div", class_="col2")
                    if col2_div:
                        p_elements = col2_div.find_all("p")
                        if len(p_elements) >= 1:
                            # 处理例句中的加粗标记
                            item["example"] = self.process_bold_text(p_elements[0])
                        if len(p_elements) >= 2:
                            item["translate"] = self.clean_text(
                                p_elements[1].get_text(strip=True)
                            )

                    # 只有当至少有一个字段存在时才添加
                    if item:
                        # 确保所有字段都存在，即使为空
                        item.setdefault("audio_url", "")
                        item.setdefault("example", "")
                        item.setdefault("translate", "")
                        trans_sents_data.append(item)

            return trans_sents_data

    def get_sentence_data(self, word):
        """
        从有道移动版获取柯林斯词典和双语例句数据
        """
        try:
            # 获取柯林斯词典数据
            collins_response = requests.get(self.mobile_collins_url.format(word=word))
            collins_response.raise_for_status()
            collins_soup = BeautifulSoup(collins_response.text, "html.parser")
            collins_data = self.extract_collins_sentence(collins_soup)

            # 获取双语例句数据
            trans_sents_response = requests.get(
                self.mobile_trans_sents_url.format(word=word)
            )
            trans_sents_response.raise_for_status()
            trans_sents_soup = BeautifulSoup(trans_sents_response.text, "html.parser")
            trans_sents_data = self.extract_trans_sentences(trans_sents_soup)

            return {"collins_sents": collins_data, "trans_sents": trans_sents_data}
        except RequestException as e:
            print(f"获取移动版数据错误: {e}")
            return {"collins_sents": [], "trans_sents": []}

    def get_result(self, word):
        """
        获取完整的单词查询结果
        """

        basic_result = self.get_web_result(word)

        sentance_data = self.get_sentence_data(word)

        json_result = {
            "success": True,
            "error": "",
            "data": {
                "word": word,
                "phonetic": {},
                "explains": [],
                "phrase": [],
                "collins_sents": sentance_data["collins_sents"],
                "trans_sents": sentance_data["trans_sents"],
            },
        }

        if basic_result and isinstance(basic_result, dict):
            # 添加web字段（如果存在）
            if "web" in basic_result:
                json_result["data"]["phrase"] = basic_result["web"]

            # 添加basic字段中的信息（如果存在）
            if "basic" in basic_result and isinstance(basic_result["basic"], dict):
                basic = basic_result["basic"]
                if "explains" in basic:
                    json_result["data"]["explains"] = basic["explains"]
                if "phonetic" in basic:
                    json_result["data"]["phonetic"] = basic["phonetic"]

        return json_result


# 创建Flask应用
app = Flask(__name__)

# 配置Flask以正确显示中文字符
app.config["JSON_AS_ASCII"] = False
app.config["JSONIFY_PRETTYPRINT_REGULAR"] = True

# 初始化API服务
youdao_api = YoudaoAPI()


@app.route("/api/translate", methods=["GET"])
def translate_word():
    """
    翻译API端点
    GET: /api/translate?word=单词
    """
    try:
        # 获取要翻译的单词
        word = request.args.get("word")

        if not word:
            return jsonify(
                {
                    "success": False,
                    "error": "请提供要翻译的单词",
                    "data": {},
                }
            ), 400

        # 获取整合结果
        result = youdao_api.get_result(word)

        return jsonify(result)

    except Exception as e:
        return jsonify({"success": False, "error": str(e), "data": {}}), 500


@app.route("/api/health", methods=["GET"])
def health_check():
    """健康检查端点"""
    return jsonify(
        {"status": "healthy", "service": "youdao-combined-api", "version": "1.0.0"}
    )


@app.route("/", methods=["GET"])
def index():
    """根路径，显示API信息"""
    return jsonify(
        {
            "message": "有道词典API服务",
            "endpoints": {
                "translate": {
                    "url": "/api/translate",
                    "methods": ["GET"],
                    "description": "查询单词完整信息",
                    "parameters": {"word": "要查询的单词"},
                    "example": "/api/translate?word=query",
                },
                "health": {
                    "url": "/api/health",
                    "methods": ["GET"],
                    "description": "健康检查",
                },
            },
        }
    )


if __name__ == "__main__":
    # 解析命令行参数
    parser = argparse.ArgumentParser(description="有道词典API服务")
    parser.add_argument("--host", default="0.0.0.0", help="主机地址")
    parser.add_argument("--port", type=int, default=5088, help="端口号")
    parser.add_argument("--debug", action="store_true", help="调试模式")

    args = parser.parse_args()

    # 运行Flask应用
    app.run(debug=args.debug, host=args.host, port=args.port)
