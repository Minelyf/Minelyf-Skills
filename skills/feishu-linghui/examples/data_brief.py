"""虚构演示：任务处理概览。所有名称和数字仅用于演示排版，不代表真实业务。
在 skill 的 examples 目录运行此脚本生成 diagram.svg。
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'scripts'))
from board import Board, HUES

b = Board()
b.title('任务处理：明确目标、逐项执行、检查结果', '虚构演示 · 100 项模拟任务 · 所有数字仅用于展示排版')
b.panel(40, 128, 920, 238, HUES['ink'], '1', '任务概览', '以模拟任务总数为统计口径')
for i, (num, label, meta) in enumerate([
    ('100', '模拟任务总数', '虚构数据'),
    ('70', '已完成', '占全部任务的 70%'),
    ('30', '待处理', '占全部任务的 30%'),
]):
    b.kpi(56 + i * 300, 224, 288, HUES['ink'], num, label, meta)
b.panel(40, 390, 452, 278, HUES['teal'], '2', '完成情况', '各状态互斥，合计 100%')
b.bars(60, 490, 412, [('已完成', 70, False, None), ('处理中', 20, False, None), ('未开始', 10, False, None)], HUES['teal'], 100)
b.panel(508, 390, 452, 278, HUES['rose'], '3', '下一步行动', '按顺序推进，逐项检查')
for i, line in enumerate(['1. 明确每项任务的验收条件', '2. 优先推进处理中的任务', '3. 完成后复查并更新状态']):
    b.text(530, 502 + i * 44, line, 16)
b.takeaway(692, '一句话：先对齐目标，再推进执行，最后检查结果。', '以上名称与数据均为虚构，仅用于展示数字卡、比例条和流程排版。')
b.save('diagram.svg', 820)
print('diagram.svg')
