"""Resolve production mode independently of a reusable visual style (stdlib only)."""
import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / 'styles/catalog.json'
WORKFLOWS = {
    'editable-ppt': ('图文混排', '图文混排 PPT', '可编辑', '可编辑版', '可编辑版（$editable-ppt）', 'editable', 'hybrid', 'PPT Image', 'shuimu-ppt'),
    'ppt-image-deck': ('纯图片', '纯图片 PPT', '图片版', '整页图片', 'image'),
    'native-template-ppt': ('纯原生模板', '纯原生模板 PPT', '原生模板', 'native'),
}


def normalized(value):
    return re.sub(r'\s+', '', value.strip().lstrip('$')).casefold()


def resolve(workflow=None, style=None, template=None):
    catalog = json.loads(CATALOG.read_text(encoding='utf-8'))
    selected_mode = catalog['default_workflow']
    if workflow:
        token = normalized(workflow)
        matches = [key for key, aliases in WORKFLOWS.items()
                   if token in [normalized(a) for a in (key, *aliases)]]
        if not matches:
            raise ValueError(f'未知制作方式 {workflow}；请选择纯图片、图文混排或纯原生模板')
        selected_mode = matches[0]
    token = normalized(style or catalog['default_style'])
    tokens = [token]
    for suffix in ('原生模板', '模板'):
        if token.endswith(suffix):
            tokens.append(token[:-len(suffix)])
    selected_style = next((s for s in catalog['styles']
                           if set(tokens) & {normalized(a) for a in (s['id'], s['name'], *s.get('aliases', []))}), None)
    if selected_style is None:
        selected_style = {'id': 'custom', 'name': style, 'reference_kind': 'none',
                          'visual_description': style, 'native_brand_required': False}
    result = {'workflow': selected_mode, 'style': dict(selected_style),
              'style_explicit': style is not None,
              'native_cover_and_header': selected_style.get('native_brand_required', False)}
    for key in ('reference', 'preview', 'guide', 'visual_guide', 'visual_reference', 'composition_reference', 'composition_preview'):
        if key in result['style']:
            result['style'][key] = str(ROOT / 'styles' / result['style'][key])
    if template:
        path = Path(template).expanduser().resolve()
        if not path.is_file():
            raise ValueError(f'指定模板不可读：{path}')
        result['template_override'] = str(path)
        result['template_priority'] = 'user-provided'
        if style is None:
            result['style'] = {'id': 'custom', 'name': '用户提供模板', 'reference_kind': 'none',
                               'visual_description': '依据用户提供模板的视觉体系',
                               'native_brand_required': False}
            result['native_cover_and_header'] = False
            result['template_inspection_required'] = True
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--workflow')
    parser.add_argument('--style')
    parser.add_argument('--template')
    args = parser.parse_args()
    try:
        print(json.dumps(resolve(args.workflow, args.style, args.template), ensure_ascii=False, indent=2))
    except (OSError, ValueError) as exc:
        parser.error(str(exc))


if __name__ == '__main__':
    main()
