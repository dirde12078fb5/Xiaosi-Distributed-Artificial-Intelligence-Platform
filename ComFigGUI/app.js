/* ==========================================================
   ConfigGUI · 应用交互核心
   负责：节点渲染 / 拖拽 / 连线 / 属性 / 缩放 / 导入导出 / 模拟运行
   ========================================================== */

(function () {
  'use strict';

  // ---------- 状态 ----------
  const state = {
    nodes: [],          // 画布中的节点 { id, type, x, y, params, title, el, ... }
    wires: [],          // 连线 { id, from:{nodeId,port}, to:{nodeId,port}, el }
    selectedNodeId: null,
    nextNodeId: 1,
    nextWireId: 1,
    zoom: 1,
    view: { x: 0, y: 0 },
    draggingNode: null,   // 从库中拖拽
    movingNode: null,     // 画布内移动
    panning: false,
    connecting: null,     // 正在连线 { fromNodeId, fromPort, fromSide, tempEl }
    clipboard: null,
  };

  // ---------- DOM 引用 ----------
  const $ = (sel) => document.querySelector(sel);
  const canvas = $('#canvas');
  const nodesLayer = $('#nodes-layer');
  const wiresSvg = $('#wires');
  const nodeLibrary = $('#node-library');
  const propertyPanel = $('#property-panel');
  const emptyHint = $('#empty-hint');
  const statusText = $('#status-text');
  const zoomLabel = $('#zoom-label');
  const searchInput = $('#search-node');

  // ---------- 初始化节点库 UI ----------
  function renderNodeLibrary(keyword = '') {
    const kw = keyword.trim().toLowerCase();
    nodeLibrary.innerHTML = '';

    NODE_LIBRARY.forEach((group) => {
      const filteredNodes = group.nodes.filter((n) =>
        !kw ||
        n.title.toLowerCase().includes(kw) ||
        n.type.toLowerCase().includes(kw) ||
        (n.description || '').toLowerCase().includes(kw)
      );
      if (filteredNodes.length === 0) return;

      const groupEl = document.createElement('div');
      groupEl.className = 'node-category';

      const header = document.createElement('div');
      header.className = 'node-category-header';
      header.innerHTML = `<span class="caret">▾</span><span class="node-dot" style="background:${group.color}"></span>${group.category} · ${filteredNodes.length}`;
      header.addEventListener('click', () => groupEl.classList.toggle('collapsed'));

      const list = document.createElement('div');
      list.className = 'node-category-list';

      filteredNodes.forEach((nd) => {
        const item = document.createElement('div');
        item.className = 'node-item';
        item.innerHTML = `<span class="node-dot" style="background:${group.color}"></span><span>${nd.title}</span>`;
        item.title = nd.description || nd.title;
        item.dataset.type = nd.type;

        // 拖拽添加
        item.addEventListener('mousedown', (e) => startDragFromLibrary(e, nd.type, group.color));
        // 点击添加
        item.addEventListener('click', (e) => {
          // 若刚完成拖拽 mousedown 则忽略由 mousedown 处理
          if (e.detail === 0) return;
          const rect = canvas.getBoundingClientRect();
          const x = (rect.width / 2 - 100) / state.zoom;
          const y = (rect.height / 2 - 80) / state.zoom;
          addNode(nd.type, x, y);
        });
        list.appendChild(item);
      });

      groupEl.appendChild(header);
      groupEl.appendChild(list);
      nodeLibrary.appendChild(groupEl);
    });
  }

  // ---------- 从库中拖拽节点 ----------
  function startDragFromLibrary(e, type, color) {
    e.preventDefault();
    const ghost = document.createElement('div');
    ghost.className = 'drag-ghost';
    ghost.style.left = e.clientX + 12 + 'px';
    ghost.style.top = e.clientY + 12 + 'px';
    ghost.innerHTML = `<span class="node-dot" style="display:inline-block;width:8px;height:8px;border-radius:50%;background:${color};margin-right:8px;vertical-align:middle"></span>${type}`;
    document.body.appendChild(ghost);

    state.draggingNode = { type, ghost };

    function onMove(ev) {
      ghost.style.left = ev.clientX + 12 + 'px';
      ghost.style.top = ev.clientY + 12 + 'px';
    }
    function onUp(ev) {
      document.removeEventListener('mousemove', onMove);
      document.removeEventListener('mouseup', onUp);
      ghost.remove();
      state.draggingNode = null;

      const rect = canvas.getBoundingClientRect();
      if (
        ev.clientX >= rect.left && ev.clientX <= rect.right &&
        ev.clientY >= rect.top && ev.clientY <= rect.bottom
      ) {
        const x = (ev.clientX - rect.left - canvas.scrollLeft) / state.zoom;
        const y = (ev.clientY - rect.top - canvas.scrollTop) / state.zoom;
        addNode(type, x - 100, y - 20);
      }
    }
    document.addEventListener('mousemove', onMove);
    document.addEventListener('mouseup', onUp);
  }

  // ---------- 添加节点到画布 ----------
  function addNode(type, x, y) {
    const meta = findNodeDefinition(type);
    if (!meta) return;
    const def = meta.def;

    const params = {};
    (def.params || []).forEach((p) => { params[p.name] = p.default; });
    (def.inputs || []).forEach((inp) => {
      if (inp.control) params[inp.name] = inp.default;
    });

    const node = {
      id: 'n' + state.nextNodeId++,
      type: def.type,
      title: def.title,
      color: meta.color,
      description: def.description || '',
      x, y,
      inputs: (def.inputs || []).map((i) => ({ ...i })),
      outputs: (def.outputs || []).map((o) => ({ ...o })),
      params,
    };
    state.nodes.push(node);

    renderNodeCard(node);
    updateUIState();
    selectNode(node.id);
  }

  // ---------- 渲染节点卡片 ----------
  function renderNodeCard(node) {
    const el = document.createElement('div');
    el.className = 'node-card';
    el.dataset.id = node.id;
    el.style.left = node.x + 'px';
    el.style.top = node.y + 'px';

    // Header
    const header = document.createElement('div');
    header.className = 'node-card-header';
    header.innerHTML = `
      <div class="title">
        <span class="node-dot" style="background:${node.color}"></span>
        <span class="title-text">${node.title}</span>
      </div>
      <div class="actions">
        <button class="close" title="删除节点">×</button>
      </div>
    `;
    el.appendChild(header);

    // Body
    const body = document.createElement('div');
    body.className = 'node-card-body';

    // 输出端口（顶部，先显示 outputs 以遵循 ComfyUI 视觉：输出在右、输入在左）
    (node.outputs || []).forEach((out, idx) => {
      const row = document.createElement('div');
      row.className = 'port-row output';
      const color = PORT_COLORS[out.type] || '#888';
      row.innerHTML = `
        <div class="port-handle output" data-side="output" data-port="${out.name}" style="--port-color:${color}"></div>
        <div class="port-label" style="color:${color}">${out.name}</div>
      `;
      body.appendChild(row);
    });

    // 参数行（内联简单参数）
    const hasInline = (node.params && Object.keys(node.params).length > 0);
    if (hasInline) {
      const paramDefs = collectParamDefs(node);
      // 只在节点内显示前 2 个文本型参数，其他交给属性面板
      paramDefs.slice(0, 2).forEach((p) => {
        if (p.control === 'textarea') return; // 文本域不放节点卡
        const row = document.createElement('div');
        row.className = 'param-row';
        row.innerHTML = `<div class="param-label">${p.label}</div>${renderParamControl(p, node.params[p.name], 'inline')}`;
        body.appendChild(row);
        bindInlineParam(row, node, p);
      });
    }

    // 输入端口（在底部）
    (node.inputs || []).forEach((inp) => {
      if (inp.control) return; // 带控件的输入不视作连接端口
      const row = document.createElement('div');
      row.className = 'port-row input';
      const color = PORT_COLORS[inp.type] || '#888';
      row.innerHTML = `
        <div class="port-handle input" data-side="input" data-port="${inp.name}" style="--port-color:${color}"></div>
        <div class="port-label" style="color:${color}">${inp.name}</div>
      `;
      body.appendChild(row);
    });

    // 输入中带控件的（如 text），放在端口下方
    (node.inputs || []).forEach((inp) => {
      if (!inp.control) return;
      const row = document.createElement('div');
      row.className = 'param-row';
      row.innerHTML = `<div class="param-label">${inp.label || inp.name}</div>${renderParamControl(inp, node.params[inp.name], 'inline')}`;
      body.appendChild(row);
      bindInlineParam(row, node, inp);
    });

    el.appendChild(body);

    // 事件绑定
    header.addEventListener('mousedown', (e) => startMoveNode(e, node));
    el.addEventListener('mousedown', (e) => {
      if (e.target.classList.contains('port-handle')) return;
      if (e.target.classList.contains('close')) return;
      selectNode(node.id);
      e.stopPropagation();
    });
    el.querySelector('.close').addEventListener('click', (e) => {
      e.stopPropagation();
      deleteNode(node.id);
    });
    // 端口事件
    el.querySelectorAll('.port-handle').forEach((ph) => {
      ph.addEventListener('mousedown', (e) => startConnect(e, node, ph));
      ph.addEventListener('mouseup', (e) => finishConnect(e, node, ph));
    });

    nodesLayer.appendChild(el);
    node.el = el;
  }

  function collectParamDefs(node) {
    const meta = findNodeDefinition(node.type);
    if (!meta) return [];
    const fromParams = (meta.def.params || []).map((p) => ({ ...p }));
    const fromInputs = (meta.def.inputs || []).filter((i) => i.control).map((i) => ({ ...i }));
    return [...fromParams, ...fromInputs];
  }

  function renderParamControl(def, value, kind) {
    const v = value === undefined || value === null ? '' : String(value);
    if (def.control === 'select') {
      const opts = (def.options || []).map((o) => `<option value="${o}" ${o == v ? 'selected' : ''}>${o}</option>`).join('');
      return `<select class="param-control" data-name="${def.name}">${opts}</select>`;
    }
    if (def.control === 'textarea') {
      return `<textarea class="param-control" data-name="${def.name}" rows="2">${escapeHtml(v)}</textarea>`;
    }
    if (def.control === 'number') {
      const min = def.min !== undefined ? `min="${def.min}"` : '';
      const max = def.max !== undefined ? `max="${def.max}"` : '';
      const step = def.step !== undefined ? `step="${def.step}"` : '';
      return `<input type="number" class="param-control" data-name="${def.name}" value="${escapeAttr(v)}" ${min} ${max} ${step} />`;
    }
    // text 默认
    return `<input type="text" class="param-control" data-name="${def.name}" value="${escapeAttr(v)}" />`;
  }

  function bindInlineParam(row, node, def) {
    const ctrl = row.querySelector('[data-name]');
    if (!ctrl) return;
    ctrl.addEventListener('input', () => {
      let v = ctrl.value;
      if (def.control === 'number') v = Number(v);
      node.params[def.name] = v;
      // 如果当前选中的是此节点，刷新属性面板
      if (state.selectedNodeId === node.id) renderPropertyPanel(node);
    });
    ctrl.addEventListener('mousedown', (e) => e.stopPropagation());
  }

  // ---------- 移动节点 ----------
  function startMoveNode(e, node) {
    if (e.target.classList.contains('close')) return;
    e.preventDefault();
    selectNode(node.id);
    const startX = e.clientX, startY = e.clientY;
    const origX = node.x, origY = node.y;
    state.movingNode = node;

    function onMove(ev) {
      const dx = (ev.clientX - startX) / state.zoom;
      const dy = (ev.clientY - startY) / state.zoom;
      node.x = origX + dx;
      node.y = origY + dy;
      node.el.style.left = node.x + 'px';
      node.el.style.top = node.y + 'px';
      redrawWires();
    }
    function onUp() {
      document.removeEventListener('mousemove', onMove);
      document.removeEventListener('mouseup', onUp);
      state.movingNode = null;
    }
    document.addEventListener('mousemove', onMove);
    document.addEventListener('mouseup', onUp);
  }

  // ---------- 选择节点 ----------
  function selectNode(id) {
    state.selectedNodeId = id;
    state.nodes.forEach((n) => {
      if (n.el) n.el.classList.toggle('selected', n.id === id);
    });
    const node = state.nodes.find((n) => n.id === id);
    renderPropertyPanel(node);
  }

  // ---------- 删除节点 ----------
  function deleteNode(id) {
    const node = state.nodes.find((n) => n.id === id);
    if (!node) return;
    if (node.el) node.el.remove();
    state.nodes = state.nodes.filter((n) => n.id !== id);
    // 删除相关连线
    state.wires = state.wires.filter((w) => {
      if (w.from.nodeId === id || w.to.nodeId === id) {
        if (w.el) w.el.remove();
        return false;
      }
      return true;
    });
    if (state.selectedNodeId === id) {
      state.selectedNodeId = null;
      renderPropertyPanel(null);
    }
    updateUIState();
  }

  // ---------- 连线 ----------
  function startConnect(e, node, handleEl) {
    e.preventDefault();
    e.stopPropagation();
    const side = handleEl.dataset.side; // 'input' | 'output'
    const portName = handleEl.dataset.port;

    // 清理临时线
    if (state.connecting) cancelConnect();

    const tempEl = document.createElementNS('http://www.w3.org/2000/svg', 'path');
    tempEl.setAttribute('class', 'wire temp');
    wiresSvg.appendChild(tempEl);

    state.connecting = {
      fromNodeId: node.id,
      fromPort: portName,
      fromSide: side,
      tempEl,
    };

    handleEl.classList.add('dragging');

    function onMove(ev) {
      const from = getPortPosition(node.id, portName, side);
      const rect = canvas.getBoundingClientRect();
      const toX = (ev.clientX - rect.left - canvas.scrollLeft) / state.zoom;
      const toY = (ev.clientY - rect.top - canvas.scrollTop) / state.zoom;
      const start = side === 'output' ? from : { x: toX, y: toY };
      const end = side === 'output' ? { x: toX, y: toY } : from;
      tempEl.setAttribute('d', cubicPath(start.x, start.y, end.x, end.y, side));
    }

    function onUp(ev) {
      document.removeEventListener('mousemove', onMove);
      document.removeEventListener('mouseup', onUp);

      handleEl.classList.remove('dragging');

      // 判断是否落在另一个节点的合法端口
      const target = document.elementFromPoint(ev.clientX, ev.clientY);
      if (target && target.classList.contains('port-handle')) {
        const targetNodeEl = target.closest('.node-card');
        if (targetNodeEl && targetNodeEl.dataset.id !== node.id) {
          const other = state.nodes.find((n) => n.id === targetNodeEl.dataset.id);
          const otherSide = target.dataset.side;
          const otherPort = target.dataset.port;
          // 必须 output -> input 且类型兼容
          if (state.connecting.fromSide !== otherSide) {
            const fromNodeId = state.connecting.fromSide === 'output' ? node.id : other.id;
            const fromPort = state.connecting.fromSide === 'output' ? portName : otherPort;
            const toNodeId = state.connecting.fromSide === 'output' ? other.id : node.id;
            const toPort = state.connecting.fromSide === 'output' ? otherPort : portName;

            // 校验数据类型是否一致
            const fromNode = state.nodes.find((n) => n.id === fromNodeId);
            const toNode = state.nodes.find((n) => n.id === toNodeId);
            const fromPortDef = (fromNode.outputs || []).find((o) => o.name === fromPort);
            const toPortDef = (toNode.inputs || []).filter((i) => !i.control).find((i) => i.name === toPort);
            if (fromPortDef && toPortDef && fromPortDef.type === toPortDef.type) {
              // 一个输入只能有一条连线：先移除落到同一输入上的旧线
              state.wires = state.wires.filter((w) => {
                if (w.to.nodeId === toNodeId && w.to.port === toPort) {
                  if (w.el) w.el.remove();
                  return false;
                }
                return true;
              });
              addWire(fromNodeId, fromPort, toNodeId, toPort);
            } else {
              flashStatus('类型不匹配：' + (fromPortDef?.type || '?') + ' → ' + (toPortDef?.type || '?'));
            }
          }
        }
      }

      tempEl.remove();
      state.connecting = null;
    }

    document.addEventListener('mousemove', onMove);
    document.addEventListener('mouseup', onUp);
  }

  function cancelConnect() {
    if (state.connecting && state.connecting.tempEl) state.connecting.tempEl.remove();
    state.connecting = null;
  }

  function finishConnect(e, node, handleEl) {
    // 实际的连线落位由 startConnect 的 mouseup 统一处理
    // 这里保留空函数以避免事件冲突
  }

  function addWire(fromNodeId, fromPort, toNodeId, toPort) {
    const wire = {
      id: 'w' + state.nextWireId++,
      from: { nodeId: fromNodeId, port: fromPort },
      to: { nodeId: toNodeId, port: toPort },
    };
    const el = document.createElementNS('http://www.w3.org/2000/svg', 'path');
    el.setAttribute('class', 'wire');
    el.dataset.id = wire.id;
    el.addEventListener('click', (e) => {
      e.stopPropagation();
      // 点击连线：高亮并等待再次点击删除，这里直接删除
      el.setAttribute('stroke', '#f7768e');
      setTimeout(() => {
        state.wires = state.wires.filter((w) => w.id !== wire.id);
        el.remove();
        updateUIState();
      }, 180);
    });
    el.style.pointerEvents = 'stroke';
    wiresSvg.appendChild(el);
    wire.el = el;
    state.wires.push(wire);
    redrawWires();
    updateUIState();
  }

  function getPortPosition(nodeId, portName, side) {
    const node = state.nodes.find((n) => n.id === nodeId);
    if (!node || !node.el) return { x: 0, y: 0 };
    const handle = node.el.querySelector(`.port-handle.${side}[data-port="${CSS.escape(portName)}"]`);
    if (!handle) return { x: 0, y: 0 };
    const rect = handle.getBoundingClientRect();
    const canvasRect = canvas.getBoundingClientRect();
    const x = (rect.left + rect.width / 2 - canvasRect.left - canvas.scrollLeft) / state.zoom;
    const y = (rect.top + rect.height / 2 - canvasRect.top - canvas.scrollTop) / state.zoom;
    return { x, y };
  }

  function cubicPath(x1, y1, x2, y2, side) {
    // 平滑贝塞尔：输出向右发射，输入向左接收
    const dx = Math.max(40, Math.abs(x2 - x1) * 0.5);
    const cx1 = side === 'output' ? x1 + dx : x1 - dx;
    const cx2 = side === 'output' ? x2 - dx : x2 + dx;
    return `M ${x1.toFixed(1)} ${y1.toFixed(1)} C ${cx1.toFixed(1)} ${y1.toFixed(1)}, ${cx2.toFixed(1)} ${y2.toFixed(1)}, ${x2.toFixed(1)} ${y2.toFixed(1)}`;
  }

  function redrawWires() {
    state.wires.forEach((wire) => {
      const from = getPortPosition(wire.from.nodeId, wire.from.port, 'output');
      const to = getPortPosition(wire.to.nodeId, wire.to.port, 'input');
      // 使用 from 节点输出的颜色
      const node = state.nodes.find((n) => n.id === wire.from.nodeId);
      const portDef = node && (node.outputs || []).find((o) => o.name === wire.from.port);
      const col = portDef ? (PORT_COLORS[portDef.type] || '#7aa2f7') : '#7aa2f7';
      wire.el.setAttribute('stroke', col);
      wire.el.setAttribute('d', cubicPath(from.x, from.y, to.x, to.y, 'output'));
    });
  }

  // ---------- 属性面板 ----------
  function renderPropertyPanel(node) {
    if (!node) {
      propertyPanel.innerHTML = `<div class="property-empty">请选择一个节点以查看并编辑其属性</div>`;
      return;
    }
    const paramDefs = collectParamDefs(node);
    let html = '';
    html += `<div class="prop-section-title">节点信息</div>`;
    html += `<div class="prop-meta">
      <div><strong>${escapeHtml(node.title)}</strong></div>
      <div style="color:var(--text-dim);margin-top:4px">类型：${escapeHtml(node.type)}</div>
      <div style="color:var(--text-dim)">ID：${escapeHtml(node.id)}</div>
    </div>`;

    if (node.description) {
      html += `<div class="prop-section-title">说明</div>`;
      html += `<div class="prop-meta" style="color:var(--text-soft);line-height:1.7">${escapeHtml(node.description)}</div>`;
    }

    if (paramDefs.length > 0) {
      html += `<div class="prop-section-title">参数</div>`;
      paramDefs.forEach((p) => {
        html += `<div class="prop-item">
          <label for="prop-${node.id}-${p.name}">${p.label || p.name} <span style="color:var(--text-dim);font-weight:400">(${p.type})</span></label>
          ${renderParamControl(p, node.params[p.name], 'panel')}
        </div>`;
      });
    }

    // 端口信息
    const inputs = (node.inputs || []).filter((i) => !i.control);
    const outputs = (node.outputs || []);
    if (inputs.length || outputs.length) {
      html += `<div class="prop-section-title">端口</div>`;
      html += `<div class="prop-meta">`;
      if (inputs.length) {
        html += `<div style="margin-bottom:6px"><strong>输入</strong>：`;
        html += inputs.map((i) => `<span style="display:inline-block;padding:2px 8px;margin:2px 4px 2px 0;border:1px solid var(--border);border-radius:10px;color:${PORT_COLORS[i.type] || '#888'}">${i.name}·${i.type}</span>`).join('');
        html += `</div>`;
      }
      if (outputs.length) {
        html += `<div><strong>输出</strong>：`;
        html += outputs.map((o) => `<span style="display:inline-block;padding:2px 8px;margin:2px 4px 2px 0;border:1px solid var(--border);border-radius:10px;color:${PORT_COLORS[o.type] || '#888'}">${o.name}·${o.type}</span>`).join('');
        html += `</div>`;
      }
      html += `</div>`;
    }

    propertyPanel.innerHTML = html;

    // 绑定参数变更事件
    propertyPanel.querySelectorAll('[data-name]').forEach((ctrl) => {
      ctrl.addEventListener('input', () => {
        const name = ctrl.dataset.name;
        const def = paramDefs.find((p) => p.name === name);
        let v = ctrl.value;
        if (def && def.control === 'number') v = Number(v);
        node.params[name] = v;
        // 同步内联控件
        if (node.el) {
          const inline = node.el.querySelector(`.param-control[data-name="${CSS.escape(name)}"]`);
          if (inline && inline !== ctrl) inline.value = ctrl.value;
        }
      });
    });
  }

  // ---------- 画布空白区域交互 ----------
  canvas.addEventListener('mousedown', (e) => {
    // 点击空白区域：取消选择；中键或 Alt+左键：平移
    if (e.target === canvas || e.target === nodesLayer || e.target === wiresSvg) {
      selectNode(null);
    }
    if (e.button === 1 || (e.button === 0 && e.altKey)) {
      e.preventDefault();
      startPan(e);
    }
  });

  function startPan(e) {
    state.panning = true;
    canvas.classList.add('panning');
    const startX = e.clientX, startY = e.clientY;
    const origScrollLeft = canvas.scrollLeft, origScrollTop = canvas.scrollTop;
    function onMove(ev) {
      canvas.scrollLeft = origScrollLeft - (ev.clientX - startX);
      canvas.scrollTop = origScrollTop - (ev.clientY - startY);
      redrawWires();
    }
    function onUp() {
      state.panning = false;
      canvas.classList.remove('panning');
      document.removeEventListener('mousemove', onMove);
      document.removeEventListener('mouseup', onUp);
    }
    document.addEventListener('mousemove', onMove);
    document.addEventListener('mouseup', onUp);
  }

  // 滚轮缩放
  canvas.addEventListener('wheel', (e) => {
    if (!e.ctrlKey && !e.metaKey) return;
    e.preventDefault();
    const factor = e.deltaY > 0 ? 0.9 : 1.1;
    setZoom(state.zoom * factor, e.clientX, e.clientY);
  }, { passive: false });

  function setZoom(z, anchorClientX, anchorClientY) {
    z = Math.max(0.3, Math.min(2.5, z));
    const rect = canvas.getBoundingClientRect();
    const ax = (anchorClientX - rect.left) || rect.width / 2;
    const ay = (anchorClientY - rect.top) || rect.height / 2;
    // 以锚点为中心缩放：保持锚点对应的画布坐标不变
    const canvasX = (ax + canvas.scrollLeft) / state.zoom;
    const canvasY = (ay + canvas.scrollTop) / state.zoom;
    state.zoom = z;
    nodesLayer.style.transform = `scale(${z})`;
    wiresSvg.style.transform = `scale(${z})`;
    // wiresSvg 坐标系统以"节点坐标系"为单位，scale 作用于 svg 元素本身会同步 stroke
    canvas.scrollLeft = canvasX * z - ax;
    canvas.scrollTop = canvasY * z - ay;
    zoomLabel.textContent = Math.round(z * 100) + '%';
    redrawWires();
  }

  $('#btn-zoom-in').addEventListener('click', () => setZoom(state.zoom * 1.15));
  $('#btn-zoom-out').addEventListener('click', () => setZoom(state.zoom * 0.87));
  $('#btn-reset-view').addEventListener('click', () => {
    state.zoom = 1;
    nodesLayer.style.transform = 'scale(1)';
    wiresSvg.style.transform = 'scale(1)';
    canvas.scrollLeft = 0; canvas.scrollTop = 0;
    zoomLabel.textContent = '100%';
    redrawWires();
  });

  // ---------- 顶部按钮 ----------
  $('#btn-new').addEventListener('click', () => {
    if (state.nodes.length > 0 && !confirm('将清空当前工作流，确认继续？')) return;
    clearAll();
  });

  $('#btn-export').addEventListener('click', () => {
    const data = serializeWorkflow();
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `comfy-workflow-${Date.now()}.json`;
    a.click();
    URL.revokeObjectURL(url);
    flashStatus('已导出 JSON 工作流');
  });

  const fileInput = $('#file-input');
  $('#btn-import').addEventListener('click', () => fileInput.click());
  fileInput.addEventListener('change', async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    try {
      const text = await file.text();
      const data = JSON.parse(text);
      loadWorkflow(data);
      flashStatus('工作流导入成功：' + file.name);
    } catch (err) {
      alert('导入失败：' + err.message);
    }
    fileInput.value = '';
  });

  $('#btn-run').addEventListener('click', () => simulateRun());

  // ---------- 服务端 API：保存 / 加载 / 远端运行 ----------
  $('#btn-save').addEventListener('click', async () => {
    if (state.nodes.length === 0) { flashStatus('请先添加节点'); return; }
    const name = prompt('请输入工作流名称（留空则使用时间戳）：', '');
    if (name === null) return;
    try {
      const body = { ...serializeWorkflow(), name: name.trim() || undefined };
      const r = await fetch('/api/workflow', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      });
      if (!r.ok) throw new Error('HTTP ' + r.status);
      const data = await r.json();
      flashStatus('已保存：' + data.name);
    } catch (err) {
      alert('保存失败：' + err.message + '\n（请确认已通过 start-server.bat 启动服务端）');
    }
  });

  $('#btn-load').addEventListener('click', async () => {
    try {
      const r = await fetch('/api/workflow');
      if (!r.ok) throw new Error('HTTP ' + r.status);
      const data = await r.json();
      const list = data.workflows || [];
      if (list.length === 0) { alert('服务端暂未保存任何工作流'); return; }
      const choices = list.map((w, i) => `${i + 1}. ${w.name}  [节点 ${w.nodes} / 连线 ${w.wires} · ${w.mtime}]`).join('\n');
      const input = prompt(
        '服务端现有工作流：\n\n' + choices + '\n\n请输入要加载的编号（1 - ' + list.length + '）：',
        '1'
      );
      if (input === null) return;
      const idx = parseInt(input, 10) - 1;
      if (isNaN(idx) || idx < 0 || idx >= list.length) { alert('编号无效'); return; }
      const target = await fetch('/api/workflow/' + encodeURIComponent(list[idx].name));
      if (!target.ok) throw new Error('HTTP ' + target.status);
      const wf = await target.json();
      loadWorkflow(wf);
      flashStatus('已加载：' + list[idx].name);
    } catch (err) {
      alert('加载失败：' + err.message + '\n（请确认已通过 start-server.bat 启动服务端）');
    }
  });

  $('#btn-run-server').addEventListener('click', async () => {
    if (state.nodes.length === 0) { flashStatus('请先添加节点'); return; }
    flashStatus('正在远端执行…');
    try {
      const r = await fetch('/api/run', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(serializeWorkflow()),
      });
      if (!r.ok) throw new Error('HTTP ' + r.status);
      const res = await r.json();
      if (res.ok !== true) throw new Error(res.error || '服务端执行失败');
      const preview = (res.logs || []).slice(0, 5).map((l, i) => `  ${String(i + 1).padStart(2)}  ${l.type}  ${l.elapsed_ms} ms`).join('\n');
      alert(
        '服务端执行成功 ✓\n\n' +
        '  节点数：' + res.nodes + '\n' +
        '  连线数：' + res.wires + '\n' +
        '  总耗时：' + res.total_ms + ' ms\n' +
        '  执行时间：' + res.ts + '\n\n' +
        '执行顺序（前 5 步）：\n' + preview
      );
      flashStatus('远端执行完成（' + res.total_ms + ' ms）');
    } catch (err) {
      alert('远端执行失败：' + err.message + '\n（请确认已通过 start-server.bat 启动服务端）');
    }
  });

  searchInput.addEventListener('input', () => renderNodeLibrary(searchInput.value));

  // ---------- 键盘快捷 ----------
  document.addEventListener('keydown', (e) => {
    if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA' || e.target.tagName === 'SELECT') return;
    if ((e.key === 'Delete' || e.key === 'Backspace') && state.selectedNodeId) {
      deleteNode(state.selectedNodeId);
    }
    if (e.key === 'Escape') {
      selectNode(null);
      cancelConnect();
    }
  });

  // ---------- 序列化 / 载入 ----------
  function serializeWorkflow() {
    return {
      version: 1,
      nodes: state.nodes.map((n) => ({
        id: n.id, type: n.type, title: n.title, x: n.x, y: n.y, params: { ...n.params },
      })),
      wires: state.wires.map((w) => ({ from: w.from, to: w.to })),
    };
  }

  function loadWorkflow(data) {
    clearAll(true);
    if (!data || !Array.isArray(data.nodes)) { alert('工作流格式不正确'); return; }
    // 重建节点
    const idMap = {};
    data.nodes.forEach((n) => {
      const meta = findNodeDefinition(n.type);
      if (!meta) return;
      const def = meta.def;
      const node = {
        id: 'n' + state.nextNodeId++,
        type: def.type, title: def.title, color: meta.color, description: def.description || '',
        x: n.x, y: n.y,
        inputs: (def.inputs || []).map((i) => ({ ...i })),
        outputs: (def.outputs || []).map((o) => ({ ...o })),
        params: { ...(n.params || {}) },
      };
      state.nodes.push(node);
      renderNodeCard(node);
      idMap[n.id] = node.id;
    });
    // 重建连线
    (data.wires || []).forEach((w) => {
      const fromId = idMap[w.from.nodeId], toId = idMap[w.to.nodeId];
      if (fromId && toId) addWire(fromId, w.from.port, toId, w.to.port);
    });
    updateUIState();
  }

  function clearAll(silent) {
    state.nodes.forEach((n) => { if (n.el) n.el.remove(); });
    state.wires.forEach((w) => { if (w.el) w.el.remove(); });
    state.nodes = [];
    state.wires = [];
    state.selectedNodeId = null;
    renderPropertyPanel(null);
    updateUIState();
    if (!silent) flashStatus('已清空工作流');
  }

  // ---------- 模拟运行 ----------
  function simulateRun() {
    if (state.nodes.length === 0) {
      flashStatus('请先添加节点');
      return;
    }
    // 计算拓扑顺序（简单的依赖图）
    const inDeg = {};
    const adj = {};
    state.nodes.forEach((n) => { inDeg[n.id] = 0; adj[n.id] = []; });
    state.wires.forEach((w) => {
      adj[w.from.nodeId].push(w.to.nodeId);
      inDeg[w.to.nodeId] = (inDeg[w.to.nodeId] || 0) + 1;
    });
    const queue = state.nodes.filter((n) => inDeg[n.id] === 0).map((n) => n.id);
    const order = [];
    while (queue.length) {
      const id = queue.shift();
      order.push(id);
      (adj[id] || []).forEach((nid) => {
        inDeg[nid]--;
        if (inDeg[nid] === 0) queue.push(nid);
      });
    }
    if (order.length !== state.nodes.length) {
      flashStatus('检测到循环依赖，无法模拟执行');
      return;
    }
    // 依次高亮动画
    state.nodes.forEach((n) => { n.el.classList.remove('done'); n.el.classList.add('running'); });
    let i = 0;
    const step = () => {
      if (i >= order.length) {
        state.nodes.forEach((n) => { n.el.classList.remove('running'); n.el.classList.add('done'); });
        setTimeout(() => state.nodes.forEach((n) => n.el.classList.remove('done')), 1500);
        flashStatus(`模拟执行完成 · ${order.length} 节点 · ${state.wires.length} 连线`);
        return;
      }
      const id = order[i++];
      const n = state.nodes.find((x) => x.id === id);
      if (n) {
        n.el.classList.add('running');
        setTimeout(() => {
          n.el.classList.remove('running');
          n.el.classList.add('done');
          setTimeout(step, 180);
        }, 260);
      } else step();
    };
    step();
  }

  // ---------- UI 状态 ----------
  function updateUIState() {
    statusText.textContent = `就绪 · ${state.nodes.length} 节点 · ${state.wires.length} 连线`;
    if (state.nodes.length > 0) emptyHint.classList.add('hidden');
    else emptyHint.classList.remove('hidden');
    // 标记已连接的端口
    state.nodes.forEach((node) => {
      if (!node.el) return;
      node.el.querySelectorAll('.port-handle').forEach((ph) => {
        const side = ph.dataset.side, port = ph.dataset.port;
        let connected = false;
        if (side === 'output') connected = state.wires.some((w) => w.from.nodeId === node.id && w.from.port === port);
        if (side === 'input') connected = state.wires.some((w) => w.to.nodeId === node.id && w.to.port === port);
        ph.classList.toggle('connected', connected);
      });
    });
  }

  let statusTimer = null;
  function flashStatus(msg) {
    statusText.textContent = msg;
    if (statusTimer) clearTimeout(statusTimer);
    statusTimer = setTimeout(updateUIState, 2200);
  }

  // ---------- 工具 ----------
  function escapeHtml(s) { return String(s ?? '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c])); }
  function escapeAttr(s) { return escapeHtml(s); }

  // ---------- 初次渲染 ----------
  renderNodeLibrary();
  updateUIState();

  // 默认示例工作流：加载器 -> CLIP(正/负) + 空潜 -> KSampler -> VAEDecode -> SaveImage
  setTimeout(loadDemo, 50);

  function loadDemo() {
    const demo = {
      nodes: [
        { id: 'ckpt', type: 'CheckpointLoaderSimple', title: 'CheckpointLoaderSimple', x: 60, y: 80 },
        { id: 'pos', type: 'CLIPTextEncode', title: 'CLIPTextEncode (正)', x: 340, y: 40 },
        { id: 'neg', type: 'CLIPTextEncode', title: 'CLIPTextEncode (负)', x: 340, y: 220 },
        { id: 'latent', type: 'EmptyLatentImage', title: 'EmptyLatentImage', x: 640, y: 80 },
        { id: 'k', type: 'KSampler', title: 'KSampler', x: 920, y: 80 },
        { id: 'vae', type: 'VAEDecode', title: 'VAEDecode', x: 1240, y: 120 },
        { id: 'save', type: 'SaveImage', title: 'SaveImage', x: 1540, y: 140 },
      ],
      wires: [
        { from: { nodeId: 'ckpt', port: 'MODEL' }, to: { nodeId: 'k', port: 'model' } },
        { from: { nodeId: 'ckpt', port: 'CLIP' }, to: { nodeId: 'pos', port: 'clip' } },
        { from: { nodeId: 'ckpt', port: 'CLIP' }, to: { nodeId: 'neg', port: 'clip' } },
        { from: { nodeId: 'ckpt', port: 'VAE' }, to: { nodeId: 'vae', port: 'vae' } },
        { from: { nodeId: 'pos', port: 'COND' }, to: { nodeId: 'k', port: 'positive' } },
        { from: { nodeId: 'neg', port: 'COND' }, to: { nodeId: 'k', port: 'negative' } },
        { from: { nodeId: 'latent', port: 'LATENT' }, to: { nodeId: 'k', port: 'latent_image' } },
        { from: { nodeId: 'k', port: 'LATENT' }, to: { nodeId: 'vae', port: 'samples' } },
        { from: { nodeId: 'vae', port: 'IMAGE' }, to: { nodeId: 'save', port: 'images' } },
      ],
    };
    // 把正/负文本预填
    demo.nodes.forEach((n) => {
      if (n.id === 'pos') n.params = { text: 'masterpiece, best quality, 1girl, blue sky, cherry blossoms, cinematic lighting' };
      if (n.id === 'neg') n.params = { text: 'lowres, bad anatomy, bad hands, text, error, missing fingers, extra digit, fewer digits, cropped, worst quality, low quality, jpeg artifacts, signature, watermark, username, blurry' };
      if (n.id === 'latent') n.params = { width: 512, height: 768, batch_size: 1 };
    });
    loadWorkflow(demo);
  }
})();
