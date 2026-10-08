"""Freeze a real design before generation and reject stale or retroactive plans."""
import argparse
import copy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re

ASSET_RESULT_FIELDS = {'status', 'width_px', 'height_px', 'generated_path',
                       'generation_record', 'actual_sha256', 'reviewed_at', 'accepted_at'}


def digest(data):
    return hashlib.sha256(data).hexdigest()


def planned_content(plan):
    data = copy.deepcopy(plan)
    for key in ('delivery', 'execution', 'design_snapshot'):
        data.pop(key, None)
    for asset in data.get('assets', []):
        for key in ASSET_RESULT_FIELDS:
            asset.pop(key, None)
    return json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()


def normalize(text):
    return re.sub(r'[\s*`]+', '', str(text))


def document_errors(plan, document):
    errors = []
    normalized = normalize(document)
    for slide in plan.get('slides', []):
        if slide['id'] not in document:
            errors.append(f'{slide["id"]}: 设计文档未覆盖此页')
        for e in slide.get('elements', []):
            if e.get('type') == 'text' and normalize(e.get('text', '')) not in normalized:
                errors.append(f'{e.get("id")}: 实际文案未出现在生图前设计文档中')
    for asset in plan.get('assets', []):
        if asset.get('source') == 'generated':
            if asset.get('id') not in document or normalize(asset.get('prompt', '')) not in normalized:
                errors.append(f'{asset.get("id")}: 完整生成提示词须先写入设计文档')
    return errors


def snapshot_path(plan_path):
    return plan_path.parent / 'design-snapshot.json'


def asset_specs(plan):
    specs = {}
    for asset in plan.get('assets', []):
        if asset.get('source') != 'generated':
            continue
        spec = {k: v for k, v in asset.items() if k not in ASSET_RESULT_FIELDS}
        spec['style_id'] = plan.get('style', {}).get('id')
        specs[asset['id']] = digest(json.dumps(spec, ensure_ascii=False, sort_keys=True).encode())
    return specs


def freeze(plan_path, design_path, revise_reason=None):
    # Import only here so the delivery checker can import verify_snapshot safely.
    from validate_deck import validate_plan
    plan_path = plan_path.resolve()
    design_path = design_path.resolve()
    plan = json.loads(plan_path.read_text(encoding='utf-8'))
    if plan.get('design_contract_version') != 2:
        raise ValueError('新任务必须使用 design_contract_version=2 并先确定页范围、装饰与封面文字槽')
    errors = validate_plan(plan, plan_path.parent)
    document = design_path.read_text(encoding='utf-8')
    errors.extend(document_errors(plan, document))
    if errors:
        raise ValueError('\n'.join(errors))
    output = snapshot_path(plan_path)
    previous = json.loads(output.read_text(encoding='utf-8')) if output.exists() else None
    plan_hash = digest(planned_content(plan))
    document_hash = digest(design_path.read_bytes())
    if previous and plan_hash == previous['plan_sha256'] and document_hash == previous['design_sha256']:
        return previous
    if previous and not revise_reason:
        raise ValueError('设计已改变；先同步文档与清单，再用 --revise 原因 保存新版本')
    specs = asset_specs(plan)
    if previous:
        for a in plan.get('assets', []):
            if a.get('source') == 'generated' and specs[a['id']] != previous.get('asset_specs', {}).get(a['id']):
                if (plan_path.parent / a['path']).is_file():
                    raise ValueError(f'{a["id"]}: 生成要求已变化，请先在设计中使用新的待生成文件路径，不能沿用旧图并标记通过')
    if not previous:
        for a in plan.get('assets', []):
            if a.get('source') == 'generated' and (plan_path.parent / a['path']).is_file():
                raise ValueError(f'{a["id"]}: 首次设计快照前已存在生成图，不能事后补作生图前设计；已有素材应如实登记为复用来源')
    now = datetime.now(timezone.utc).isoformat()
    import os
    record = {
        'schema_version': 1,
        'revision': previous['revision'] + 1 if previous else 1,
        'created_at': previous['created_at'] if previous else now,
        'updated_at': now,
        'revision_reason': revise_reason,
        'plan_file': plan_path.name,
        'design_file': os.path.relpath(design_path, plan_path.parent),
        'plan_sha256': plan_hash,
        'design_sha256': document_hash,
        'source_page_ids': plan['scope']['source_page_ids'],
        'asset_specs': specs,
    }
    output.write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return record


def verify_snapshot(plan_path):
    plan_path = Path(plan_path).resolve()
    path = snapshot_path(plan_path)
    if not path.is_file():
        return ['缺少生图前设计快照：先完成设计文档/layout.json 并运行 design_snapshot.py freeze']
    try:
        plan = json.loads(plan_path.read_text(encoding='utf-8'))
        record = json.loads(path.read_text(encoding='utf-8'))
        design = plan_path.parent / record['design_file']
        errors = []
        if plan.get('design_contract_version') != 2 or record.get('plan_file') != plan_path.name:
            errors.append('设计快照与当前计划不匹配')
        if digest(planned_content(plan)) != record['plan_sha256']:
            errors.append('布局/文案/提示词已变更，须先同步设计并记录新版本')
        if not design.is_file() or digest(design.read_bytes()) != record['design_sha256']:
            errors.append('设计文档缺失或已变化，不能用旧快照继续制作')
        return errors
    except (OSError, ValueError, KeyError, TypeError) as exc:
        return [f'设计快照不可用：{exc}']


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['freeze', 'verify'])
    parser.add_argument('plan', type=Path)
    parser.add_argument('--design', type=Path)
    parser.add_argument('--revise', metavar='REASON')
    args = parser.parse_args()
    try:
        if args.action == 'freeze':
            if args.design is None:
                parser.error('freeze requires --design')
            record = freeze(args.plan, args.design, args.revise)
            print(f'设计已锁定 revision={record["revision"]}；按此文档生成素材和组装')
        else:
            errors = verify_snapshot(args.plan)
            print('\n'.join(errors) if errors else '当前布局与生图前设计快照一致')
            return int(bool(errors))
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(str(exc))
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
