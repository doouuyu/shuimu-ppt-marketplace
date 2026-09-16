"""Read-only preflight for the pixel academic prompt document. Stdlib only."""
import argparse
import math
import re
from pathlib import Path

PALETTES = {
    'blue': '机构蓝（主蓝 #0B58A8、亮蓝 #1674C2、深蓝 #083E78、浅蓝 #EAF2FA；红色强调 #C82820、黄色 #F0D21A）',
    'green': '机构绿（主绿 #087057、深绿 #07513F、浅绿 #E8F3EE；红色强调 #C82820、黄色 #F0D21A）',
    'red': '机构红（主红 #A60000、亮红 #C92B1E、深红 #790000、浅红 #F7EAEA；黑色正文、黄色 #F0D21A）',
}


def style_prefix(theme='blue'):
    source = Path(__file__).resolve().parents[1] / 'references/style-contract.md'
    block = re.search(r'```text\s*\n(.*?)\n```', source.read_text(encoding='utf-8'), re.S)
    return block.group(1).replace('{主题色}', PALETTES[theme])


def normalize(text):
    return re.sub(r'\s+', '', text)


def validate(document, theme='blue'):
    errors = []
    pages = list(re.finditer(r'^## P(\d+)[｜|].*$', document, re.M))
    if not pages:
        return ['未找到 ## P01｜标题 格式的页面章节']
    numbers = [int(p.group(1)) for p in pages]
    if numbers != list(range(1, len(pages) + 1)):
        errors.append('页面编号须从 P01 连续递增，且不能重复')
    content_headers = []
    for index, page in enumerate(pages):
        label = f'P{int(page.group(1)):02d}'
        section = document[page.end():pages[index + 1].start() if index + 1 < len(pages) else len(document)]
        blocks = re.findall(r'```text\s*\n(.*?)\n```', section, re.S)
        if len(blocks) != 1:
            errors.append(f'{label}: 必须恰好有一个 text 提示词块')
            continue
        body = blocks[0]
        if normalize(style_prefix(theme)) not in normalize(body):
            errors.append(f'{label}: 缺少完整 {theme} 固定风格前缀或前缀被改写')
        fields = dict(re.findall(r'^([^\n：:]+)[：:]\s*(\S[^\n]*)$', body, re.M))
        for name in ('页面角色', '页面家族', '标题系统', '密度级别', '版式', '证据图版'):
            if not fields.get(name):
                errors.append(f'{label}: 缺少 {name}')
        if fields.get('页面角色') not in ('cover', 'agenda', 'section', 'content', 'ending'):
            errors.append(f'{label}: 页面角色无效')
        copy = re.search(r'^画面文字[：:]\s*\n(.+)', body, re.M | re.S)
        if not copy:
            errors.append(f'{label}: 缺少逐字画面文字')
        if fields.get('页面角色') == 'content':
            content_headers.append(fields.get('标题系统'))
            if not fields.get('顶部结论句'):
                errors.append(f'{label}: 缺少顶部结论句（证据不足可显式写“无”）')
            if copy and not re.match(r'\s*\d+(?:\.\d+)+\s+\S', copy.group(1)):
                errors.append(f'{label}: 内容标题需包含 1.1 等章节层级编号')
    if len(content_headers) >= 3 and content_headers.count('全宽顶部标题条') < math.ceil(len(content_headers) * .6):
        errors.append('至少 60% 普通内容页须使用全宽顶部标题条，防止整套退化为轻标题科技风')
    return errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('document', nargs='?', type=Path)
    parser.add_argument('--theme', choices=PALETTES, default='blue')
    parser.add_argument('--print-prefix', action='store_true')
    args = parser.parse_args()
    if args.print_prefix:
        print(style_prefix(args.theme))
        return 0
    if args.document is None:
        parser.error('需要提示词文档或 --print-prefix')
    errors = validate(args.document.read_text(encoding='utf-8'), args.theme)
    print('\n'.join(errors) if errors else '提示词结构与固定前缀通过；仍需视觉验收。')
    return 1 if errors else 0


if __name__ == '__main__':
    raise SystemExit(main())
