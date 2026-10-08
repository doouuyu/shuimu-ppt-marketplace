"""Validate explicit layout plans and audit named native PPTX objects (stdlib only)."""
import argparse
import hashlib
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
PLACEHOLDERS = re.compile(
    r'待补充|待完善|待替换|数据待确认|(?:示例|演示|示意|临时)数据|占位(?:图|符|文字)|'
    r'请输入(?:标题|正文|内容)|此处输入|输入修改文字|添加标题文本|'
    r'您的内容打在这里|在这里输入你的|单击此处|某某某|XXX|\b(?:TBD|TODO|LOREM IPSUM)\b', re.I)
PLUGIN_ROOT = Path(__file__).resolve().parents[3]
STYLE_CATALOG = {item['id']: item for item in json.loads(
    (PLUGIN_ROOT / 'styles/catalog.json').read_text(encoding='utf-8'))['styles']}
NATIVE_PROFILES = {key: item for key, item in STYLE_CATALOG.items()
                   if item['reference_kind'] == 'native-template'}


def text_values(value):
    if isinstance(value, str):
        yield value
    elif isinstance(value, list):
        for item in value:
            yield from text_values(item)
    elif isinstance(value, dict):
        for item in value.values():
            yield from text_values(item)


def check_style(plan, base):
    errors = []
    style = plan.get('style', {})
    profile, kind = style.get('id'), style.get('reference_kind')
    if not profile or kind not in ('none', 'native-template', 'image-reference'):
        return ['style 必须锁定 id 与 reference_kind']
    if profile == 'pixel-defense-academic-ppt' and style.get('explicitly_requested') is not True:
        errors.append('像素答辩只允许用户明确选择，不能作为可编辑流程默认风格')
    if profile in NATIVE_PROFILES and kind != 'native-template':
        errors.append(f'{profile}: 必须复用原生模板，不能降级为仅借用配色')
    if kind == 'none' and profile not in ('neutral', 'custom') and STYLE_CATALOG.get(profile, {}).get('reference_kind') != 'none':
        errors.append(f'{profile}: 指定风格必须关联实际参考文件')
    if kind == 'none':
        return errors
    reference = base / style.get('reference_path', '')
    if not reference.is_file():
        return errors + ['style.reference_path 必须指向实际参考文件']
    candidates = {}
    if profile in NATIVE_PROFILES:
        item = NATIVE_PROFILES[profile]
        for key, role_key in [('reference', 'roles'), ('composition_reference', 'composition_roles')]:
            if key in item:
                original = PLUGIN_ROOT / 'styles' / item[key]
                if original.is_file():
                    candidates[hashlib.sha256(original.read_bytes()).digest()] = item[role_key]
        if not candidates:
            return errors + [f'{profile}: 已有源件不可读，请定位实际资源或在当前稿按需适配']
    checked = {}

    def source_roles(path):
        key = str(path.resolve())
        if key not in checked:
            digest = hashlib.sha256(path.read_bytes()).digest()
            checked[key] = candidates.get(digest)
            if candidates and checked[key] is None:
                errors.append(f'{profile}: reference_path 与登记的原生/已认可参考不一致')
        return checked[key]

    roles = source_roles(reference) if candidates else None
    for slide in plan.get('slides', []):
        sid = slide.get('id')
        source = slide.get('template_source', {})
        if kind == 'image-reference':
            if not slide.get('reference_anchor'):
                errors.append(f'{sid}: 图片参考必须记录 reference_anchor，不能假称复制原生模板')
            continue
        local_reference = source.get('reference_path')
        local_roles = roles
        if local_reference:
            path = base / local_reference
            if not path.is_file():
                errors.append(f'{sid}: 逐页 template_source.reference_path 不可读')
            elif candidates:
                local_roles = source_roles(path)
        page, mode = source.get('slide'), source.get('mode')
        if not isinstance(page, int) or isinstance(page, bool) or page < 1:
            errors.append(f'{sid}: 缺少 template_source.slide 原模板页码')
        if local_roles and page not in local_roles.get(slide.get('role'), []):
            errors.append(f'{sid}: 源页不符合 {profile} 的 {slide.get("role")} 页面角色')
        allowed = ('duplicate-slide', 'reuse-header') if slide.get('role') == 'content' else ('duplicate-slide',)
        if mode not in allowed:
            errors.append(f'{sid}: 封面/目录/章节/结束页必须 duplicate-slide，正文可 reuse-header')
        required = {'theme', 'layout', 'background', 'logo', 'title-style'}
        if not required.issubset(set(source.get('preserve', []))):
            errors.append(f'{sid}: template_source.preserve 缺少模板保护项')
    return errors


def check_delivery(plan, base, require_assets):
    errors = check_style(plan, base)
    generated = set()
    reusable_visuals = set()
    for asset in plan.get('assets', []):
        if asset.get('source') == 'style':
            entry = STYLE_CATALOG.get(plan.get('style', {}).get('id'), {}).get('design_assets', {}).get(asset.get('bundle_key'))
            if not entry:
                errors.append(f'{asset.get("id")}: 风格素材 bundle_key 未登记')
            else:
                path = base / asset.get('path', '')
                if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != entry['sha256']:
                    errors.append(f'{asset.get("id")}: 复用素材与风格包原图不一致')
                else:
                    reusable_visuals.add(asset.get('id'))
        if asset.get('source') != 'generated':
            continue
        aid = asset.get('id')
        generated.add(aid)
        if not asset.get('prompt') or asset.get('status') not in ('planned', 'generated', 'accepted'):
            errors.append(f'{aid}: 生成素材必须记录 prompt 与 status')
        if require_assets:
            if asset.get('status') != 'accepted':
                errors.append(f'{aid}: 素材尚未验收，不能进入组装')
            if not all(number(asset.get(k)) and asset[k] > 0 for k in ('width_px', 'height_px')):
                errors.append(f'{aid}: 缺少实际像素尺寸')
            path = base / asset.get('path', '')
            if path.is_file():
                with path.open('rb') as handle:
                    header = handle.read(32)
                valid = header.startswith(b'\x89PNG\r\n\x1a\n') or header.startswith(b'\xff\xd8\xff') or (header[:4] == b'RIFF' and header[8:12] == b'WEBP')
                if not valid:
                    errors.append(f'{aid}: 生成素材不是 PNG/JPEG/WebP 图片文件')
    used = set()
    for slide in plan.get('slides', []):
        images = [e for e in slide.get('elements', []) if e.get('type') == 'image']
        used.update(e.get('asset_id') for e in images)
        if slide.get('role') == 'content':
            visual = slide.get('visual', {})
            strategy = visual.get('strategy')
            if strategy == 'primary-image':
                aid = visual.get('primary_asset_id')
                asset = next((a for a in plan.get('assets', []) if a.get('id') == aid), {})
                if not aid or aid not in {e.get('asset_id') for e in images}:
                    errors.append(f'{slide.get("id")}: 正文主图必须实际引用到本页')
                if asset.get('purpose') != 'primary' or asset.get('kind') in ('decoration', 'background', 'logo', 'icon'):
                    errors.append(f'{slide.get("id")}: 背景/Logo/小装饰不能代替语义主图')
                if not visual.get('relationship'):
                    errors.append(f'{slide.get("id")}: 须说明主图与本页内容的关系')
            elif strategy == 'native-figure':
                ids = visual.get('element_ids', [])
                meaningful = {e.get('id') for e in slide.get('elements', [])
                              if e.get('type') in ('table', 'chart', 'connector') or
                              (e.get('type') == 'shape' and e.get('purpose') == 'diagram')}
                if not visual.get('reason') or not ids or not set(ids).issubset(meaningful):
                    errors.append(f'{slide.get("id")}: 原生主图须有实际图表/关系图对象及选择理由')
            elif strategy == 'text-only':
                if not visual.get('reason') or slide.get('page_task') not in ('quotation', 'statement'):
                    errors.append(f'{slide.get("id")}: 纯文字只用于有明确理由的金句/陈述页')
            elif strategy == 'native-content':
                if not visual.get('reason') or not any(e.get('type') in ('text', 'table', 'chart', 'shape', 'connector') for e in slide.get('elements', [])):
                    errors.append(f'{slide.get("id")}: 原生内容页须有内容与版式理由')
            else:
                errors.append(f'{slide.get("id")}: 正文页须声明 visual 主图策略，不能用有图片标签替代配图设计')
        for element in slide.get('elements', []):
            eid = element.get('id')
            for field in ('text', 'runs', 'rows', 'categories', 'series', 'title', 'labels'):
                if any(PLACEHOLDERS.search(t) for t in text_values(element.get(field))):
                    errors.append(f'{eid}: 正式页面含占位/演示文字，缺项应省略并记录到独立审查文档')
            if element.get('data_status') in ('temporary', 'mock', 'synthetic', 'unverified'):
                errors.append(f'{eid}: 未核实/临时数据不能进入对外版本')
            if element.get('type') == 'chart' and not element.get('source_ref'):
                errors.append(f'{eid}: 图表必须提供 source_ref，缺数据时删除图表或改定性表达')
            if element.get('type') == 'shape':
                purpose = element.get('purpose')
                if purpose not in ('template', 'background', 'separator', 'diagram', 'content-panel'):
                    errors.append(f'{eid}: shape 必须声明用途，不能把程序图形当装饰素材')
                if purpose == 'template' and not slide.get('template_source'):
                    errors.append(f'{eid}: 声称继承模板对象却没有 template_source')
    if not ((generated | reusable_visuals) & used):
        errors.append('图文混排须实际使用生成素材或已验收的风格素材，Logo不计入')
    if plan.get('design_contract_version') == 2:
        errors.extend(check_design_contract(plan))
    return errors


def check_design_contract(plan):
    """Check planned scope, shared decoration and cover slots before generating assets."""
    errors = []
    slides = plan.get('slides', [])
    scope = plan.get('scope', {}).get('source_page_ids')
    source_ids = [s.get('source_page_id') for s in slides]
    if not isinstance(scope, list) or not scope or not all(isinstance(x, str) for x in scope) or scope != source_ids or len(set(scope)) != len(scope):
        errors.append('scope.source_page_ids 须与本次逐页 source_page_id 完全对应，不能补页或漏页')
    style = plan.get('style', {})
    bundled = STYLE_CATALOG.get(style.get('id'), {})
    assets = {a.get('id'): a for a in plan.get('assets', [])}
    for slide in slides:
        sid = slide.get('id')
        elements = {e.get('id'): e for e in slide.get('elements', [])}
        if slide.get('role') == 'content':
            override = style.get('decoration_override', {})
            if style.get('decoration_mode') == 'none':
                if override.get('source') != 'user_message' or not override.get('quote'):
                    errors.append(f'{sid}: 取消所选风格的装饰层须记录用户明确要求')
                continue
            aid = slide.get('decoration_asset_id')
            asset = assets.get(aid, {})
            if not aid or asset.get('purpose') != 'decorative' or not any(e.get('type') == 'image' and e.get('asset_id') == aid for e in elements.values()):
                errors.append(f'{sid}: 缺少实际使用的统一装饰层，主体图不能替代装饰背景')
            expected = bundled.get('default_decoration')
            if expected and (asset.get('source') != 'style' or asset.get('bundle_key') != expected):
                errors.append(f'{sid}: 默认须复用已认可的风格装饰素材')
            if expected:
                canvas = plan.get('canvas', {})
                expected_box = [0, 0, canvas.get('width'), canvas.get('height')]
                instances = [e for e in elements.values() if e.get('type') == 'image' and e.get('asset_id') == aid]
                if not any(e.get('box') == expected_box and e.get('opacity', 1) == 1 for e in instances):
                    errors.append(f'{sid}: 统一背景须按整页画布放置，不能缩成小角标或隐藏')
        if slide.get('role') == 'cover':
            slots = slide.get('cover_slots', {})
            required = bundled.get('cover_required_slots', ['title'])
            ids = [slots.get(name) for name in required]
            if len(ids) != len(set(ids)):
                errors.append(f'{sid}: 主题大字与报告标题须分别映射，不能用同一对象冒充两个文字槽')
            for name, eid in zip(required, ids):
                element = elements.get(eid, {})
                if element.get('type') != 'text' or not element.get('text', '').strip():
                    errors.append(f'{sid}: 封面 {name} 文字槽未落实到实际原生文本')
    return errors


def number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def check_style_authority(plan):
    """Attachment styling must not be promoted to a user-message exception."""
    errors = []
    order = plan.get('style_authority')
    if order is not None and order != ['user_message', 'selected_skill', 'attachment_layout']:
        errors.append('样式优先级必须为 user_message → selected_skill → attachment_layout')
    overrides = plan.get('user_overrides', [])
    if not isinstance(overrides, list):
        return errors + ['user_overrides 必须为来源明确的对象列表']
    ids = {e.get('id') for slide in plan.get('slides', []) for e in slide.get('elements', [])}
    for index, item in enumerate(overrides, 1):
        if not isinstance(item, dict) or item.get('source') != 'user_message':
            errors.append(f'user_overrides[{index}]: 样式例外须来自输入框 user_message，不能由附件或自由文本授权')
            continue
        if not isinstance(item.get('quote'), str) or not item['quote'].strip():
            errors.append(f'user_overrides[{index}]: 必须记录输入框中的用户原话 quote')
        targets = item.get('element_ids')
        if not isinstance(targets, list) or not targets or any(not isinstance(e, str) or e not in ids for e in targets):
            errors.append(f'user_overrides[{index}]: element_ids 必须列出清单中实际受影响的对象')
        if not isinstance(item.get('properties'), dict) or not item['properties']:
            errors.append(f'user_overrides[{index}]: 必须记录明确要求的样式 properties')
    return errors


def rgb(value):
    if not isinstance(value, str) or not re.fullmatch(r'#[0-9a-fA-F]{6}', value):
        return None
    return tuple(int(value[i:i + 2], 16) for i in (1, 3, 5))


def luminance(color):
    channels = [v / 255 for v in color]
    linear = [v / 12.92 if v <= .04045 else ((v + .055) / 1.055) ** 2.4 for v in channels]
    return sum(v * weight for v, weight in zip(linear, (.2126, .7152, .0722)))


def text_role(element, slide):
    if str(element.get('id', '')).endswith('-subtitle'):
        return 'subtitle'
    if element.get('text_role'):
        return element['text_role']
    if str(element.get('id', '')).endswith('-title'):
        return 'cover_title' if slide.get('role') in ('cover', 'section') else 'title'
    return 'label' if element.get('type') in ('table', 'chart') else 'body'


def check_projection(plan):
    """Check the selected reading context; ordinary screen reading is the default."""
    profile = plan.get('readability_profile', 'screen')
    profiles = {
        'screen': {'cover_title': 36, 'title': 28, 'subtitle': 24, 'body': 18, 'label': 18, 'footnote': 14, 'metric': 24},
        'projection': {'cover_title': 42, 'title': 34, 'subtitle': 28, 'body': 22, 'label': 20, 'footnote': 18, 'metric': 28},
    }
    if not isinstance(profile, str) or profile not in profiles:
        return ['readability_profile 必须为 screen 或 projection']
    floors = profiles[profile]
    scale = plan['canvas']['height'] / 720
    errors = []
    for slide in plan.get('slides', []):
        tiers = {role: [] for role in floors}
        for element in slide.get('elements', []):
            kind, eid = element.get('type'), element.get('id', '')
            if kind not in ('text', 'table', 'chart'):
                continue
            default_role = text_role(element, slide)
            if default_role == 'metric' and (kind != 'text' or not re.search(r'\d', element.get('text', '')) or len(element.get('text', '')) > 28):
                errors.append(f'{eid}: metric 仅用于简短关键数字，不能用于普通正文绕过层级检查')
            if default_role == 'subtitle' and element.get('text_role', 'subtitle') != 'subtitle':
                errors.append(f'{eid}: 页面副标题必须使用 subtitle 角色，不能标成正文或脚注')
            base = dict(element)
            base['text_role'] = default_role
            base.setdefault('background_color', slide.get('background', '#FFFFFF'))
            styles = [base]
            if kind == 'table':
                styles = [dict(base, color=element.get('body_color', element.get('color')),
                               background_color=element.get('body_fill', base['background_color']))]
                if element.get('alternate_fill'):
                    styles.append(dict(styles[0], background_color=element['alternate_fill']))
                styles.append(dict(base, color=element.get('header_color', styles[0].get('color')),
                                   background_color=element.get('header_fill', base['background_color'])))
            for override in element.get('runs', []) + element.get('text_styles', []):
                styles.append(dict(styles[0], **override))
            for style in styles:
                role, size = style.get('text_role'), style.get('font_size_pt')
                if default_role == 'subtitle' and role != 'subtitle':
                    errors.append(f'{eid}: 副标题局部样式不能改变 subtitle 角色')
                    role = 'subtitle'
                if role in tiers and number(size):
                    tiers[role].append(size)
                if role not in floors:
                    errors.append(f'{eid}: text_role 无效，必须声明真实阅读层级')
                elif not number(size) or size < floors[role] * scale:
                    errors.append(f'{eid}: {profile} 字号不足，{role} 至少 {floors[role] * scale:g} pt')
                if profile == 'projection' and style.get('bold') is not True:
                    errors.append(f'{eid}: 投影文字必须 bold=true，不使用常规或细字重')
                if style.get('opacity', 1) != 1:
                    errors.append(f'{eid}: 阅读文字必须完全不透明')
                foreground, background = rgb(style.get('color')), rgb(style.get('background_color'))
                if foreground is None or background is None:
                    errors.append(f'{eid}: 文字及其实际局部背景必须显式使用 #RRGGBB')
                    continue
                # Allow black/near-black and white; reject gray including muted blue-gray.
                if profile == 'projection' and max(foreground) > 24 and min(foreground) < 245 and max(foreground) - min(foreground) <= 40:
                    errors.append(f'{eid}: 不使用灰色/灰蓝文字，改黑色、深品牌色或深底白字')
                light, dark = sorted((luminance(foreground), luminance(background)), reverse=True)
                large = number(size) and (size >= 24 * scale or (size >= 18 * scale and style.get('bold') is True))
                contrast_floor = 3.0 if large else 4.5
                if (light + .05) / (dark + .05) < contrast_floor:
                    errors.append(f'{eid}: 文字与实际背景对比不足 {contrast_floor:g}:1')
        if tiers['subtitle']:
            titles = tiers['title'] + tiers['cover_title']
            body = tiers['body'] + tiers['label']
            gap = 2 * scale
            if not titles:
                errors.append(f'{slide.get("id")}: 有副标题时须声明同页主标题以核对字号层级')
            elif max(tiers['subtitle']) > min(titles) - gap:
                errors.append(f'{slide.get("id")}: 副标题须比主标题至少小 {gap:g} pt')
            if body and min(tiers['subtitle']) < max(body) + gap:
                errors.append(f'{slide.get("id")}: 副标题须比正文/标签至少大 {gap:g} pt')
    return errors


def retained_template_bleed(element, slide, width, height):
    """Declared source-object bleed still requires comparison with the rendered template."""
    if not (element.get('template_bleed') is True and element.get('source_object')
            and slide.get('template_source', {}).get('mode') in ('duplicate-slide', 'reuse-header')):
        return False
    x, y, w, h = element['box']
    return w > 0 and h > 0 and x < width and y < height and x + w > 0 and y + h > 0


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
            elif (box[0] < 0 or box[1] < 0 or min(box[2:]) <= 0 or box[0] + box[2] > width + .01 or box[1] + box[3] > height + .01) and not retained_template_bleed(element, slide, width, height):
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
    errors.extend(check_style_authority(plan))
    errors.extend(check_delivery(plan, base, require_assets))
    errors.extend(check_projection(plan))
    return errors


def normalized(text):
    return re.sub(r'\s+', '', text)


def audit_subtitle_font(element, obj):
    """Require resolvable subtitle sizes; do not guess template/theme inheritance."""
    eid = element['id']
    errors, sizes = [], []
    for fit in obj.findall('.//a:normAutofit', NS):
        if int(fit.get('fontScale', '100000')) < 100000:
            errors.append(f'{eid}: PPTX 副标题被自动缩小，须重新排版')
    for paragraph in obj.findall('p:txBody/a:p', NS):
        props = paragraph.find('a:pPr', NS)
        level = int(props.get('lvl', '0')) + 1 if props is not None else 1
        defaults = [
            paragraph.find('a:pPr/a:defRPr', NS),
            obj.find(f'p:txBody/a:lstStyle/a:lvl{level}pPr/a:defRPr', NS),
            obj.find('p:txBody/a:lstStyle/a:defPPr/a:defRPr', NS),
        ]
        for run in paragraph:
            text = run.find('a:t', NS)
            if text is None or not (text.text or '').strip():
                continue
            candidates = [run.find('a:rPr', NS)] + defaults
            raw = next((p.get('sz') for p in candidates if p is not None and p.get('sz')), None)
            if raw is None:
                errors.append(f'{eid}: 无法解析 PPTX 副标题字号，须显式写入字号后重检')
            else:
                sizes.append(int(raw) / 100)
    planned = [element.get('font_size_pt')]
    planned += [s.get('font_size_pt', element.get('font_size_pt'))
                for s in element.get('runs', []) + element.get('text_styles', [])]
    planned = [s for s in planned if number(s)]
    if sizes and planned and (min(sizes) < min(planned) - .05 or max(sizes) > max(planned) + .05):
        errors.append(f'{eid}: PPTX 副标题字号 {min(sizes):g}–{max(sizes):g} pt '
                      f'与设计 {min(planned):g}–{max(planned):g} pt 不一致')
    return errors


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
            actual_copy = ''.join(n.text or '' for n in root.findall('.//a:t', NS))
            if PLACEHOLDERS.search(actual_copy):
                errors.append(f'{slide["id"]}: PPTX 残留占位/演示文字（包括未列入设计的模板对象）')
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
                    if text_role(element, slide) == 'subtitle':
                        errors.extend(audit_subtitle_font(element, obj))
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
        if args.require_assets or args.pptx:
            from design_snapshot import verify_snapshot
            errors.extend(verify_snapshot(args.plan))
        if args.pptx and not errors:
            errors.extend(audit_pptx(plan, args.pptx))
    except (OSError, ValueError, KeyError, TypeError, AttributeError, zipfile.BadZipFile, ET.ParseError) as exc:
        print(f'无法检查 {args.plan}: {exc}')
        return 1
    print('\n'.join(errors) if errors else '设计/原生对象检查通过；仍需逐页渲染验证排版、素材和数据。')
    return int(bool(errors))


if __name__ == '__main__':
    raise SystemExit(main())
