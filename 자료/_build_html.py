"""
Build 데이터맵_트리.html (D3.js) and 데이터맵_이차트.html (ECharts)
from _datamap_tree.json
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')
import json
from pathlib import Path

base = Path(r'D:\Workspace\AI_PT\자료')
with open(base / '_datamap_tree.json', 'r', encoding='utf-8') as f:
    tree_json_str = f.read()

# ---------- D3.js Collapsible Tree ----------
d3_html = '''<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<title>고용노동부 데이터맵 (D3 트리)</title>
<style>
  * { box-sizing: border-box; }
  body { font-family: 'Malgun Gothic', '맑은 고딕', -apple-system, sans-serif; margin: 0; overflow: hidden; background: #1e293b; color: #e2e8f0; }
  header { position: fixed; top: 0; left: 0; right: 0; padding: 14px 24px; background: #0f172a; color: #f1f5f9; z-index: 100; box-shadow: 0 2px 8px rgba(0,0,0,0.4); border-bottom: 1px solid #334155; }
  header h1 { margin: 0; font-size: 24px; font-weight: 600; }
  header .hint { font-size: 18px; opacity: 0.85; margin-top: 6px; }
  #chart { width: 100vw; height: 100vh; cursor: grab; }
  #chart:active { cursor: grabbing; }
  .node circle { stroke-width: 2.5px; cursor: pointer; }
  .node--root circle { fill: #fbbf24; stroke: #fbbf24; }
  .node--depth1 circle { fill: #1e293b; stroke: #60a5fa; }
  .node--depth2 circle { fill: #1e293b; stroke: #34d399; }
  .node--depth3 circle { fill: #1e293b; stroke: #fb923c; }
  .node--leaf circle { fill: #334155; stroke: #94a3b8; }
  .node--collapsed circle { fill: #60a5fa; }
  .node text { font-size: 18px; pointer-events: none; user-select: none; fill: #f1f5f9; paint-order: stroke; stroke: #1e293b; stroke-width: 4px; stroke-linecap: round; stroke-linejoin: round; }
  .node--root text { font-size: 21px; font-weight: 700; fill: #fbbf24; }
  .node--depth1 text { font-size: 20px; font-weight: 600; fill: #93c5fd; }
  .link { fill: none; stroke: #475569; stroke-width: 1.5px; }
  .tooltip { position: absolute; max-width: 480px; padding: 14px 18px; background: rgba(15,23,42,0.97); color: #f1f5f9; border: 1px solid #475569; border-radius: 8px; font-size: 18px; line-height: 1.5; pointer-events: none; z-index: 200; box-shadow: 0 6px 20px rgba(0,0,0,0.5); display: none; }
  .tooltip .tt-title { font-weight: 700; margin-bottom: 8px; color: #fbbf24; font-size: 18px; }
  .tooltip .tt-meta { font-size: 17px; opacity: 0.85; margin-top: 8px; padding-top: 8px; border-top: 1px solid rgba(255,255,255,0.18); }
  .legend { position: fixed; bottom: 20px; left: 20px; background: rgba(15,23,42,0.92); border: 1px solid #334155; color: #e2e8f0; padding: 14px 18px; border-radius: 8px; font-size: 17px; box-shadow: 0 4px 14px rgba(0,0,0,0.4); }
  .legend-item { display: flex; align-items: center; gap: 8px; margin: 4px 0; }
  .legend-dot { width: 14px; height: 14px; border-radius: 50%; border: 2.5px solid; }
  .controls { position: fixed; bottom: 20px; right: 20px; display: flex; gap: 8px; }
  .btn { padding: 9px 16px; background: #334155; color: #f1f5f9; border: 1px solid #475569; border-radius: 6px; font-size: 18px; cursor: pointer; font-family: inherit; }
  .btn:hover { background: #475569; border-color: #64748b; }
</style>
</head>
<body>
<header>
  <h1>고용노동부 데이터맵 — 인터랙티브 트리</h1>
  <div class="hint">노드 클릭 = 펼침/접힘 · 데이터명에 마우스 올리기 = 주요 데이터내용 · 마우스 휠 = 줌 · 드래그 = 이동</div>
</header>
<svg id="chart"></svg>
<div id="tooltip" class="tooltip"></div>
<div class="legend">
  <div class="legend-item"><div class="legend-dot" style="background:#fbbf24;border-color:#fbbf24"></div>루트</div>
  <div class="legend-item"><div class="legend-dot" style="background:#1e293b;border-color:#60a5fa"></div>대분류</div>
  <div class="legend-item"><div class="legend-dot" style="background:#1e293b;border-color:#34d399"></div>중분류</div>
  <div class="legend-item"><div class="legend-dot" style="background:#1e293b;border-color:#fb923c"></div>소분류</div>
  <div class="legend-item"><div class="legend-dot" style="background:#334155;border-color:#94a3b8"></div>데이터명</div>
  <div class="legend-item"><div class="legend-dot" style="background:#60a5fa;border-color:#60a5fa"></div>접힘 상태</div>
</div>
<div class="controls">
  <button class="btn" onclick="expandAll()">전체 펼치기</button>
  <button class="btn" onclick="collapseAll()">전체 접기</button>
  <button class="btn" onclick="resetView()">초기화</button>
</div>

<script src="https://d3js.org/d3.v7.min.js"></script>
<script>
const data = __TREE_JSON__;

const svg = d3.select('#chart')
  .attr('width', window.innerWidth)
  .attr('height', window.innerHeight);

const g = svg.append('g');
const tooltip = d3.select('#tooltip');

const zoom = d3.zoom()
  .scaleExtent([0.2, 3])
  .on('zoom', (event) => g.attr('transform', event.transform));
svg.call(zoom);

const root = d3.hierarchy(data);
root.x0 = 0;
root.y0 = 0;

// Initial state: only depth 1 (대분류) visible — collapse depth >= 1
root.descendants().forEach(d => {
  if (d.depth >= 1 && d.children) {
    d._children = d.children;
    d.children = null;
  }
});

const dx = 34;
const dy = 280;
const treeLayout = d3.tree().nodeSize([dx, dy]);
const diagonal = d3.linkHorizontal().x(d => d.y).y(d => d.x);

let nodeIdCounter = 0;

function update(source) {
  treeLayout(root);

  const nodes = root.descendants();
  const links = root.links();

  // Compute extent for centering
  let x0 = Infinity, x1 = -Infinity;
  root.each(d => {
    if (d.x > x1) x1 = d.x;
    if (d.x < x0) x0 = d.x;
  });

  const transition = svg.transition().duration(400);

  // ----- Nodes -----
  const node = g.selectAll('g.node')
    .data(nodes, d => d.id || (d.id = ++nodeIdCounter));

  const nodeEnter = node.enter().append('g')
    .attr('class', d => {
      let cls = 'node';
      if (d.depth === 0) cls += ' node--root';
      else if (d.depth === 1) cls += ' node--depth1';
      else if (d.depth === 2) cls += ' node--depth2';
      else if (d.depth === 3) cls += ' node--depth3';
      if (!d.children && !d._children) cls += ' node--leaf';
      if (d._children) cls += ' node--collapsed';
      return cls;
    })
    .attr('transform', d => `translate(${source.y0},${source.x0})`)
    .on('click', (event, d) => {
      if (d.children) {
        d._children = d.children;
        d.children = null;
      } else if (d._children) {
        d.children = d._children;
        d._children = null;
      }
      update(d);
    })
    .on('mouseover', (event, d) => {
      // Show tooltip only for leaf (데이터명) nodes
      if (!d.children && !d._children && d.data.tooltip !== undefined) {
        const html = `
          <div class="tt-title">${escapeHtml(d.data.name)}</div>
          <div>${escapeHtml(d.data.tooltip || '(주요 데이터내용 정보 없음)')}</div>
          <div class="tt-meta">${escapeHtml(d.data.org || '')}${d.data.system ? ' · ' + escapeHtml(d.data.system) : ''}</div>
        `;
        tooltip.html(html).style('display', 'block');
      }
    })
    .on('mousemove', (event) => {
      tooltip
        .style('left', (event.clientX + 14) + 'px')
        .style('top', (event.clientY + 14) + 'px');
    })
    .on('mouseout', () => {
      tooltip.style('display', 'none');
    });

  nodeEnter.append('circle')
    .attr('r', d => d.depth === 0 ? 11 : (d.depth === 1 ? 10 : 7));

  nodeEnter.append('text')
    .attr('dy', '0.32em')
    .attr('x', d => (d.children || d._children) ? -14 : 14)
    .attr('text-anchor', d => (d.children || d._children) ? 'end' : 'start')
    .text(d => d.data.name);

  const nodeUpdate = nodeEnter.merge(node);
  nodeUpdate.transition(transition)
    .attr('transform', d => `translate(${d.y},${d.x})`)
    .attr('class', d => {
      let cls = 'node';
      if (d.depth === 0) cls += ' node--root';
      else if (d.depth === 1) cls += ' node--depth1';
      else if (d.depth === 2) cls += ' node--depth2';
      else if (d.depth === 3) cls += ' node--depth3';
      if (!d.children && !d._children) cls += ' node--leaf';
      if (d._children) cls += ' node--collapsed';
      return cls;
    });

  node.exit().transition(transition).remove()
    .attr('transform', d => `translate(${source.y},${source.x})`)
    .select('circle').attr('r', 0);

  // ----- Links -----
  const link = g.selectAll('path.link')
    .data(links, d => d.target.id);

  const linkEnter = link.enter().insert('path', 'g')
    .attr('class', 'link')
    .attr('d', d => {
      const o = {x: source.x0, y: source.y0};
      return diagonal({source: o, target: o});
    });

  linkEnter.merge(link).transition(transition)
    .attr('d', diagonal);

  link.exit().transition(transition).remove()
    .attr('d', d => {
      const o = {x: source.x, y: source.y};
      return diagonal({source: o, target: o});
    });

  root.each(d => {
    d.x0 = d.x;
    d.y0 = d.y;
  });
}

function escapeHtml(s) {
  if (!s) return '';
  return String(s).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
}

// Initial centering
update(root);
const initialTransform = d3.zoomIdentity.translate(140, window.innerHeight / 2 + 20).scale(1);
svg.call(zoom.transform, initialTransform);

function expandSubtree(node) {
  const all = node.children || node._children;
  if (!all) return;
  node.children = all;
  node._children = null;
  all.forEach(expandSubtree);
}

function collapseSubtree(node, depth) {
  const all = node.children || node._children;
  if (!all) return;
  all.forEach(c => collapseSubtree(c, depth + 1));
  if (depth >= 1) {
    node._children = all;
    node.children = null;
  } else {
    node.children = all;
    node._children = null;
  }
}

window.expandAll = function() {
  expandSubtree(root);
  update(root);
};

window.collapseAll = function() {
  collapseSubtree(root, 0);
  update(root);
};

window.resetView = function() {
  collapseSubtree(root, 0);
  update(root);
  svg.transition().duration(500).call(zoom.transform, initialTransform);
};

window.addEventListener('resize', () => {
  svg.attr('width', window.innerWidth).attr('height', window.innerHeight);
});
</script>
</body>
</html>
'''

d3_html = d3_html.replace('__TREE_JSON__', tree_json_str)
(base / '데이터맵_트리.html').write_text(d3_html, encoding='utf-8')
print(f'[D3]    데이터맵_트리.html  written ({len(d3_html)} chars)')

# ---------- ECharts Tree ----------
echarts_html = '''<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<title>고용노동부 데이터맵 (ECharts 트리)</title>
<style>
  * { box-sizing: border-box; }
  body { font-family: 'Malgun Gothic', '맑은 고딕', -apple-system, sans-serif; margin: 0; overflow: hidden; background: #fafafa; }
  header { position: fixed; top: 0; left: 0; right: 0; padding: 12px 20px; background: #1f3a5f; color: white; z-index: 100; box-shadow: 0 2px 6px rgba(0,0,0,0.15); }
  header h1 { margin: 0; font-size: 16px; font-weight: 600; }
  header .hint { font-size: 12px; opacity: 0.85; margin-top: 4px; }
  #chart { width: 100vw; height: 100vh; }
  .controls { position: fixed; bottom: 16px; right: 16px; display: flex; gap: 6px; z-index: 50; }
  .btn { padding: 6px 12px; background: white; border: 1px solid #cbd5e1; border-radius: 4px; font-size: 12px; cursor: pointer; font-family: inherit; }
  .btn:hover { background: #f1f5f9; }
  .layout-toggle { position: fixed; bottom: 16px; left: 16px; background: white; padding: 8px 12px; border-radius: 6px; font-size: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); z-index: 50; }
  .layout-toggle label { margin-right: 10px; cursor: pointer; }
</style>
</head>
<body>
<header>
  <h1>고용노동부 데이터맵 — ECharts 트리</h1>
  <div class="hint">노드 클릭 = 펼침/접힘 · 데이터명에 마우스 올리기 = 주요 데이터내용 · 마우스 휠 = 줌 · 드래그 = 이동</div>
</header>
<div id="chart"></div>
<div class="layout-toggle">
  레이아웃:
  <label><input type="radio" name="layout" value="orthogonal" checked> 가로형</label>
  <label><input type="radio" name="layout" value="radial"> 방사형</label>
</div>
<div class="controls">
  <button class="btn" onclick="expandAll()">전체 펼치기</button>
  <button class="btn" onclick="collapseAll()">초기화 (대분류만)</button>
</div>

<script src="https://cdn.jsdelivr.net/npm/echarts@5.4.3/dist/echarts.min.js"></script>
<script>
const data = __TREE_JSON__;

// Mark nodes deeper than depth 1 as collapsed
function markCollapsed(node, depth = 0) {
  if (depth >= 1 && node.children) {
    node.collapsed = true;
  }
  if (node.children) {
    node.children.forEach(c => markCollapsed(c, depth + 1));
  }
}
function uncollapseAll(node) {
  if (node.collapsed !== undefined) node.collapsed = false;
  if (node.children) node.children.forEach(uncollapseAll);
}

markCollapsed(data);

const chart = echarts.init(document.getElementById('chart'));

function buildOption(layout) {
  const isRadial = layout === 'radial';
  return {
    tooltip: {
      trigger: 'item',
      triggerOn: 'mousemove',
      enterable: false,
      confine: true,
      backgroundColor: 'rgba(15,23,42,0.95)',
      borderColor: 'rgba(15,23,42,0.95)',
      textStyle: { color: '#f1f5f9', fontSize: 12 },
      extraCssText: 'max-width: 360px; line-height: 1.5; box-shadow: 0 4px 12px rgba(0,0,0,0.25);',
      formatter: function(params) {
        const d = params.data;
        // Show tooltip only for leaf (데이터명) nodes — those that have tooltip field
        if (d.tooltip !== undefined) {
          let html = '<div style="font-weight:700;color:#fbbf24;margin-bottom:6px;">' + escapeHtml(d.name) + '</div>';
          html += '<div>' + escapeHtml(d.tooltip || '(주요 데이터내용 정보 없음)') + '</div>';
          if (d.org || d.system) {
            html += '<div style="font-size:11px;opacity:0.8;margin-top:6px;padding-top:6px;border-top:1px solid rgba(255,255,255,0.15);">';
            html += escapeHtml(d.org || '');
            if (d.system) html += ' · ' + escapeHtml(d.system);
            html += '</div>';
          }
          return html;
        }
        // For non-leaf, show simple label with child count
        const childCount = countLeaves(d);
        return '<div style="font-weight:700;color:#fbbf24;">' + escapeHtml(d.name) + '</div>' +
               '<div style="font-size:11px;opacity:0.8;margin-top:4px;">하위 데이터: ' + childCount + '건</div>';
      }
    },
    series: [{
      type: 'tree',
      data: [data],
      top: '8%',
      bottom: '8%',
      left: isRadial ? '5%' : '12%',
      right: isRadial ? '5%' : '20%',
      layout: isRadial ? 'radial' : 'orthogonal',
      orient: 'LR',
      symbol: 'circle',
      symbolSize: function(value, params) {
        if (params.treeAncestors && params.treeAncestors.length === 1) return 14; // root
        if (params.treeAncestors && params.treeAncestors.length === 2) return 11; // 대분류
        return 7;
      },
      initialTreeDepth: -1,
      roam: true,
      expandAndCollapse: true,
      animationDuration: 400,
      animationDurationUpdate: 400,
      label: {
        position: isRadial ? 'radial' : 'left',
        rotate: isRadial ? undefined : 0,
        verticalAlign: 'middle',
        align: isRadial ? undefined : 'right',
        fontSize: 12,
        fontFamily: 'Malgun Gothic, 맑은 고딕, sans-serif',
        formatter: function(params) {
          return params.data.name;
        }
      },
      leaves: {
        label: {
          position: isRadial ? 'radial' : 'right',
          rotate: isRadial ? undefined : 0,
          verticalAlign: 'middle',
          align: isRadial ? undefined : 'left',
          fontSize: 11,
          color: '#475569'
        }
      },
      lineStyle: {
        color: '#cbd5e1',
        width: 1.5,
        curveness: 0.5
      },
      itemStyle: {
        color: '#ffffff',
        borderColor: '#2563eb',
        borderWidth: 2
      },
      levels: [
        { itemStyle: { color: '#1f3a5f', borderColor: '#1f3a5f' }, label: { fontSize: 14, fontWeight: 700 } },
        { itemStyle: { color: '#ffffff', borderColor: '#2563eb' }, label: { fontSize: 13, fontWeight: 600 } },
        { itemStyle: { color: '#ffffff', borderColor: '#059669' } },
        { itemStyle: { color: '#ffffff', borderColor: '#d97706' } },
        { itemStyle: { color: '#f3f4f6', borderColor: '#6b7280' } }
      ]
    }]
  };
}

function escapeHtml(s) {
  if (!s) return '';
  return String(s).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
}

function countLeaves(node) {
  if (!node.children || node.children.length === 0) return 1;
  let n = 0;
  node.children.forEach(c => { n += countLeaves(c); });
  return n;
}

let currentLayout = 'orthogonal';
chart.setOption(buildOption(currentLayout));

document.querySelectorAll('input[name="layout"]').forEach(el => {
  el.addEventListener('change', (e) => {
    currentLayout = e.target.value;
    chart.setOption(buildOption(currentLayout), true);
  });
});

window.expandAll = function() {
  uncollapseAll(data);
  chart.setOption(buildOption(currentLayout), true);
};

window.collapseAll = function() {
  uncollapseAll(data);
  markCollapsed(data);
  chart.setOption(buildOption(currentLayout), true);
};

window.addEventListener('resize', () => chart.resize());
</script>
</body>
</html>
'''

echarts_html = echarts_html.replace('__TREE_JSON__', tree_json_str)
(base / '데이터맵_이차트.html').write_text(echarts_html, encoding='utf-8')
print(f'[ECharts] 데이터맵_이차트.html written ({len(echarts_html)} chars)')

print('\nDone.')
