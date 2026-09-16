"""Validate explicit layout plans and audit named native PPTX objects (stdlib only)."""
import argparse
import json
import math
import posixpath
import re
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

NS = {
    'p': 'http://schemas.openxmlformats.org/presentationml/2006/main',
    'a': 'http://schemas.openxmlformats.org/drawingml/2006/main',
    'c': 'http://schemas.openxmlformats.org/drawingml/2006/chart',
    'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships',
}
TYPES = {'text', 'image', 'shape', 'connector', 'table', 'chart'}


def number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def validate_plan(plan, base, require_assets=False):
    errors = []
    if not isinstance(plan, dict):
        return ['清单必须是 JSON object']
    if plan.get('workflow') != 'editable-ppt':
        errors.append('workflow 必须为 editable-ppt')
    canvas = plan.get('canvas', {})
    width, height = canvas.get('width'), canvas.get('height')
    if canvas.get('unit') != 'px' or not all(number(v) and v > 0 for v in (width, height)):
        return errors + ['canvas 必须声明正数 width/height 和 unit=px']
    assets = {}
    for asset in plan.get('assets', []):
        aid = asset.get('id')
        if not aid or aid in assets:
            errors.append(f'素材 ID 缺失或重复：{aid}')
        assets[aid] = asset
        for field in ('path', 'kind', 'source'):
            if not asset.get(field):
                errors.append(f'{aid}: 缺少 {field}')
        if asset.get('source') == 'generated' and asset.get('text_free') is not True:
            errors.append(f'{aid}: 生成素材必须 text_free=true，标签应作为原生文字')
        if require_assets and not (base / asset.get('path', '')).is_file():
            errors.append(f'{aid}: 素材文件不存在：{asset.get("path")}')
    slides = plan.get('slides')
    if not isinstance(slides, list) or not slides:
        return errors + ['slides 必须为非空列表']
    seen = set()
    for index, slide in enumerate(slides, 1):
        sid = slide.get('id')
        if sid != f'P{index:02d}':
            errors.append(f'{sid}: 页码必须从 P01 连续递增')
        elements = slide.get('elements', [])
        if not elements:
            errors.append(f'{sid}: elements 不得为空')
        for element in elements:
            eid, kind = element.get('id'), element.get('type')
            if not eid or eid in seen:
                errors.append(f'{sid}: 对象 ID 缺失或重复：{eid}')
            seen.add(eid)
            if kind not in TYPES:
                errors.append(f'{eid}: type 必须为 {sorted(TYPES)}')
            box = element.get('box', [])
            if not isinstance(box, list) or len(box) != 4 or not all(number(v) for v in box):
                errors.append(f'{eid}: box 必须是 [x,y,w,h] 四个有限数值')
            elif box[0] < 0 or box[1] < 0 or min(box[2:]) <= 0 or box[0] + box[2] > width + .01 or box[1] + box[3] > height + .01:
                errors.append(f'{eid}: box 越界或尺寸非正')
            if not number(element.get('z')):
                errors.append(f'{eid}: 缺少有效 z 层级')
            if kind in ('text', 'table', 'chart'):
                if not element.get('font_family') or not number(element.get('font_size_pt')) or element.get('font_size_pt', 0) <= 0:
                    errors.append(f'{eid}: 缺少有效字体/字号')
            if kind == 'text':
                if not isinstance(element.get('text'), str) or not element['text'].strip():
                    errors.append(f'{eid}: text 不得为空')
                if element.get('align') not in ('left', 'center', 'right', 'justify') or element.get('valign') not in ('top', 'middle', 'bottom'):
                    errors.append(f'{eid}: 缺少有效横向/纵向对齐')
                if not re.fullmatch(r'#[0-9A-Fa-f]{6}', str(element.get('color', ''))):
                    errors.append(f'{eid}: color 必须为 #RRGGBB')
                margin = element.get('margin_px', [])
                if not isinstance(margin, list) or len(margin) != 4 or not all(number(v) and v >= 0 for v in margin):
                    errors.append(f'{eid}: margin_px 必须为上右下左四个非负数值')
                for field in ('line_spacing', 'paragraph_after_pt'):
                    value = element.get(field)
                    if not number(value) or value < 0 or (field == 'line_spacing' and value == 0):
                        errors.append(f'{eid}: 缺少有效 {field}')
            if kind == 'image':
                if element.get('asset_id') not in assets:
                    errors.append(f'{eid}: 引用了不存在的 asset_id')
                if element.get('fit') not in ('contain', 'cover'):
                    errors.append(f'{eid}: fit 必须是 contain/cover')
            if kind == 'shape' and not element.get('geometry'):
                errors.append(f'{eid}: 缺少 geometry')
            if kind == 'connector' and not all(element.get(k) for k in ('from', 'to')):
                errors.append(f'{eid}: 缺少连接端点 from/to')
            if kind == 'table':
                rows = element.get('rows', [])
                if not rows or not all(isinstance(r, list) and len(r) == len(rows[0]) and len(r) > 0 for r in rows):
                    errors.append(f'{eid}: rows 必须为非空矩形数据表')
                else:
                    for field, count in (('column_widths', len(rows[0])), ('row_heights', len(rows))):
                        values = element.get(field, [])
                        if len(values) != count or not all(number(v) and v > 0 for v in values):
                            errors.append(f'{eid}: {field} 与表格维度不一致')
                        elif len(box) == 4 and all(number(v) for v in box):
                            extent = box[2] if field == 'column_widths' else box[3]
                            if abs(sum(values) - extent) > .1:
                                errors.append(f'{eid}: {field} 总和与 box 尺寸不一致')
            if kind == 'chart':
                categories, series = element.get('categories', []), element.get('series', [])
                if not element.get('chart_type') or not categories or not series:
                    errors.append(f'{eid}: 缺少 chart_type/categories/series')
                for item in series:
                    values = item.get('values', [])
                    if not item.get('name') or len(values) != len(categories) or not all(number(v) for v in values):
                        errors.append(f'{eid}: 图表系列名称/值与类别不匹配')
        local_ids = {e.get('id') for e in elements}
        for e in elements:
            if e.get('type') == 'connector' and any(e.get(k) not in local_ids for k in ('from', 'to')):
                errors.append(f'{e.get("id")}: 连接端点必须存在于同页')
    return errors


def normalized(text):
    return re.sub(r'\s+', '', text)


def audit_pptx(plan, pptx):
    """Check slide order, object types and text. Rendering/fonts/data still need visual QA."""
    errors = []
    with zipfile.ZipFile(pptx) as archive:
        presentation = ET.fromstring(archive.read('ppt/presentation.xml'))
        rels = ET.fromstring(archive.read('ppt/_rels/presentation.xml.rels'))
        targets = {r.get('Id'): r.get('Target') for r in rels if r.get('TargetMode') != 'External'}
        slide_paths = []
        for item in presentation.findall('p:sldIdLst/p:sldId', NS):
            target = targets[item.get(f'{{{NS["r"]}}}id')]
            slide_paths.append(target.lstrip('/') if target.startswith('/') else posixpath.normpath('ppt/' + target))
        if len(slide_paths) != len(plan['slides']):
            errors.append(f'页数不符：PPTX={len(slide_paths)}，设计={len(plan["slides"])}')
        for slide, path in zip(plan['slides'], slide_paths):
            root = ET.fromstring(archive.read(path))
            objects = {}
            for tag in ('sp', 'pic', 'graphicFrame', 'cxnSp'):
                for obj in root.findall(f'.//p:{tag}', NS):
                    name = obj.find('.//p:cNvPr', NS)
                    if name is not None:
                        key = name.get('name')
                        if key in objects:
                            errors.append(f'{slide["id"]}: PPT 对象名称重复 {key}')
                        objects[key] = obj
            for element in slide['elements']:
                eid, kind = element['id'], element['type']
                obj = objects.get(eid)
                if obj is None:
                    errors.append(f'{slide["id"]}/{eid}: 缺少原生对象，需保留设计 ID 为对象名称')
                    continue
                props = obj.find('.//p:cNvPr', NS)
                if props is not None and props.get('hidden') in ('1', 'true'):
                    errors.append(f'{eid}: 原生对象被隐藏')
                if any(n.get('val') == '0' for n in obj.findall('.//a:alpha', NS)):
                    errors.append(f'{eid}: 检出全透明组件，需核查文字可见性')
                if kind == 'text':
                    if obj.tag != f'{{{NS["p"]}}}sp' or obj.find('p:txBody', NS) is None:
                        errors.append(f'{eid}: 文字没有保留为原生文本对象')
                    actual = ''.join(n.text or '' for n in obj.findall('.//a:t', NS))
                    if normalized(actual) != normalized(element['text']):
                        errors.append(f'{eid}: 原生文字与设计文案不一致')
                elif kind == 'table':
                    table = obj.find('.//a:tbl', NS)
                    if table is None:
                        errors.append(f'{eid}: 表格被栅格化或丢失')
                    else:
                        actual = [[normalized(''.join(n.text or '' for n in cell.findall('.//a:t', NS))) for cell in row.findall('a:tc', NS)] for row in table.findall('a:tr', NS)]
                        expected = [[normalized(str(v)) for v in row] for row in element['rows']]
                        if actual != expected:
                            errors.append(f'{eid}: 表格单元格内容不一致')
                elif kind == 'chart':
                    if obj.find('.//c:chart', NS) is None:
                        errors.append(f'{eid}: 图表不是原生 chart')
                else:
                    expected_tag = {'image': 'pic', 'shape': 'sp', 'connector': 'cxnSp'}[kind]
                    if obj.tag != f'{{{NS["p"]}}}{expected_tag}':
                        errors.append(f'{eid}: 原生对象类型不符（要求 {kind}）')
    return errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('plan', type=Path)
    parser.add_argument('--require-assets', action='store_true')
    parser.add_argument('--pptx', type=Path)
    args = parser.parse_args()
    try:
        plan = json.loads(args.plan.read_text(encoding='utf-8'))
        errors = validate_plan(plan, args.plan.parent, args.require_assets)
        if args.pptx and not errors:
            errors.extend(audit_pptx(plan, args.pptx))
    except (OSError, ValueError, KeyError, TypeError, AttributeError, zipfile.BadZipFile, ET.ParseError) as exc:
        print(f'无法检查 {args.plan}: {exc}')
        return 1
    print('\n'.join(errors) if errors else '设计/原生对象检查通过；仍需逐页渲染验证排版、素材和数据。')
    return int(bool(errors))


if __name__ == '__main__':
    raise SystemExit(main())
