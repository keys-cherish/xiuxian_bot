import json
import os

def load_localisation(lang='CHS'):
    try:
        textmap_path = os.path.join(os.path.dirname(__file__), '..', 'textmaps', f'{lang}.json')
        with open(textmap_path, encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"未找到语言文件 {lang}，已使用默认 CHS。")
        textmap_path = os.path.join(os.path.dirname(__file__), '..', 'textmaps', 'CHS.json')
        with open(textmap_path, encoding='utf-8') as f:
            return json.load(f)

def get_response(key, lang='CHS', platform=None, **kwargs):
    try:
        textmap = load_localisation(lang)
        response = textmap['responses'].get(key, {})
        response_type = response.get('type', 'plain')

        text_field = 'text'
        if platform:
            if platform.lower() == 'telegram':
                text_field = 'text_TG'

        text = response.get(text_field) or response.get('text', '')
        text = text.format(**kwargs)
        return response_type, text
    except KeyError as e:
        print(f"文本资源缺失: {e}")
        msg = f"NO_TEXT({key}) | 请联系管理员补全文本。"
        if platform and platform.lower() == 'telegram':
            try:
                from telegram.helpers import escape_markdown
                msg = escape_markdown(msg, version=2)
            except Exception:
                pass
        return 'plain', msg
    except Exception as e:
        print(f"获取文本失败 key={key}, lang={lang}: {e}")
        msg = f"ERR_TEXT({key}) | 请联系管理员排查。"
        if platform and platform.lower() == 'telegram':
            try:
                from telegram.helpers import escape_markdown
                msg = escape_markdown(msg, version=2)
            except Exception:
                pass
        return 'plain', msg
