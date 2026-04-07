/**
 * Bubble Explorer — recursive force-directed drill-down
 *
 * Click a bubble → explodes into children bubbles
 * Right-click / Esc → go back up one level
 * Hover → show detail panel
 *
 * The entire exploration happens in one continuous d3-force canvas.
 */

(function() {
  'use strict';

  // Sector color map
  const COLORS = {
    // NAICS sectors
    '11': '#4ADE80', '21': '#F59E0B', '22': '#06B6D4', '23': '#EF4444',
    '31-33': '#8B5CF6', '42': '#EC4899', '44-45': '#F97316', '48-49': '#14B8A6',
    '51': '#3B82F6', '52': '#6366F1', '53': '#A78BFA', '54': '#10B981',
    '55': '#64748B', '56': '#78716C', '61': '#2563EB', '62': '#0D9488',
    '71': '#E11D48', '72': '#D97706', '81': '#9CA3AF', '92': '#1E40AF',
    // ISIC sections
    'A': '#4ADE80', 'B': '#F59E0B', 'C': '#8B5CF6', 'D': '#06B6D4',
    'E': '#14B8A6', 'F': '#EF4444', 'G': '#F97316', 'H': '#14B8A6',
    'I': '#D97706', 'J': '#3B82F6', 'K': '#6366F1', 'L': '#A78BFA',
    'M': '#10B981', 'N': '#78716C', 'O': '#1E40AF', 'P': '#2563EB',
    'Q': '#0D9488', 'R': '#E11D48', 'S': '#9CA3AF', 'T': '#64748B',
    'U': '#7A7872',
    // System tints
    'naics_2022': '#F59E0B',
    'isic_rev4': '#3B82F6',
    'nace_rev2': '#6366F1',
    'sic_1987': '#78716C',
    'anzsic_2006': '#14B8A6',
    'nic_2008': '#F97316',
    'wz_2008': '#EF4444',
    'onace_2008': '#DC2626',
    'noga_2008': '#B91C1C',
    'jsic_2013': '#F43F5E',
  };

  const container = document.getElementById('explorer-canvas');
  if (!container) return;

  const width = container.clientWidth;
  const height = container.clientHeight || window.innerHeight - 80;

  // State
  let navStack = []; // [{type, id, code, label, nodes}]
  let simulation = null;
  let svg, g, defs;

  // ── Initialize SVG ──

  svg = d3.select(container)
    .append('svg')
    .attr('viewBox', `0 0 ${width} ${height}`);

  // Glow filter
  defs = svg.append('defs');
  const filter = defs.append('filter').attr('id', 'bubble-glow');
  filter.append('feGaussianBlur').attr('stdDeviation', '6').attr('result', 'blur');
  const merge = filter.append('feMerge');
  merge.append('feMergeNode').attr('in', 'blur');
  merge.append('feMergeNode').attr('in', 'SourceGraphic');

  g = svg.append('g');

  // Zoom
  const zoom = d3.zoom()
    .scaleExtent([0.3, 5])
    .on('zoom', (e) => g.attr('transform', e.transform));
  svg.call(zoom);

  // ── Bubble rendering ──

  function getColor(node) {
    if (node._color) return node._color;
    if (node.sector_code && COLORS[node.sector_code]) return COLORS[node.sector_code];
    if (node.code && COLORS[node.code]) return COLORS[node.code];
    if (node.id && COLORS[node.id]) return COLORS[node.id];
    return '#3B82F6';
  }

  function getRadius(node) {
    if (node._radius) return node._radius;
    // Scale by child count or node_count if available
    const count = node.node_count || node._childCount || 1;
    return Math.max(25, Math.min(80, Math.sqrt(count) * 2.5));
  }

  function renderBubbles(nodes, links) {
    // Clear previous
    g.selectAll('*').remove();

    if (simulation) simulation.stop();

    // Prepare node data
    const bubbles = nodes.map(n => ({
      ...n,
      x: width / 2 + (Math.random() - 0.5) * 200,
      y: height / 2 + (Math.random() - 0.5) * 200,
      r: getRadius(n),
      color: getColor(n),
    }));

    // Prepare link data
    const edgeData = (links || []).map(l => ({
      source: bubbles.find(b => b._id === l.source) || l.source,
      target: bubbles.find(b => b._id === l.target) || l.target,
      ...l,
    })).filter(l => l.source && l.target);

    // Force simulation
    simulation = d3.forceSimulation(bubbles)
      .force('center', d3.forceCenter(width / 2, height / 2))
      .force('charge', d3.forceManyBody().strength(d => -d.r * 3))
      .force('collision', d3.forceCollide().radius(d => d.r + 8).strength(0.8))
      .force('x', d3.forceX(width / 2).strength(0.04))
      .force('y', d3.forceY(height / 2).strength(0.04));

    if (edgeData.length > 0) {
      simulation.force('link', d3.forceLink(edgeData).distance(120).strength(0.3));
    }

    // Draw edges
    const link = g.append('g')
      .selectAll('line')
      .data(edgeData)
      .join('line')
      .attr('stroke', '#3B82F6')
      .attr('stroke-opacity', 0.12)
      .attr('stroke-width', 1);

    // Draw bubbles
    const bubble = g.append('g')
      .selectAll('g')
      .data(bubbles)
      .join('g')
      .attr('cursor', 'pointer');

    // Outer glow ring
    bubble.append('circle')
      .attr('r', d => d.r + 4)
      .attr('fill', 'none')
      .attr('stroke', d => d.color)
      .attr('stroke-width', 1)
      .attr('stroke-opacity', 0.15)
      .attr('filter', 'url(#bubble-glow)');

    // Main circle
    bubble.append('circle')
      .attr('r', d => d.r)
      .attr('fill', d => d.color)
      .attr('fill-opacity', 0.12)
      .attr('stroke', d => d.color)
      .attr('stroke-width', 1.5)
      .attr('stroke-opacity', 0.6);

    // Label: code
    bubble.append('text')
      .attr('text-anchor', 'middle')
      .attr('dy', d => d.r > 35 ? -6 : 0)
      .attr('fill', '#E8E6E1')
      .attr('font-family', "'Instrument Serif', serif")
      .attr('font-size', d => d.r > 50 ? '14px' : d.r > 35 ? '12px' : '10px')
      .text(d => {
        const label = d.name || d.title || d.code || d.id;
        const max = Math.floor(d.r / 4);
        return label.length > max ? label.slice(0, max - 1) + '…' : label;
      });

    // Label: subtitle
    bubble.filter(d => d.r > 35)
      .append('text')
      .attr('text-anchor', 'middle')
      .attr('dy', 12)
      .attr('fill', '#7A7872')
      .attr('font-family', "'Geist Mono', monospace")
      .attr('font-size', '10px')
      .text(d => {
        if (d.node_count) return `${d.node_count.toLocaleString()} codes`;
        if (d.code && d.title && d.code !== d.title) return d.code;
        return '';
      });

    // Leaf indicator
    bubble.filter(d => d.is_leaf)
      .append('circle')
      .attr('cx', d => d.r * 0.6)
      .attr('cy', d => -d.r * 0.6)
      .attr('r', 4)
      .attr('fill', '#4ADE80')
      .attr('fill-opacity', 0.6);

    // ── Interactions ──

    // Hover
    bubble.on('mouseover', function(event, d) {
      d3.select(this).selectAll('circle')
        .transition().duration(150)
        .attr('fill-opacity', function() {
          return d3.select(this).attr('stroke-opacity') ? 0.25 : 0;
        })
        .attr('stroke-opacity', 0.9);

      showDetail(d);
    }).on('mouseout', function() {
      d3.select(this).selectAll('circle')
        .transition().duration(150)
        .attr('fill-opacity', function() {
          return d3.select(this).attr('filter') ? 0 : 0.12;
        })
        .attr('stroke-opacity', function() {
          return d3.select(this).attr('filter') ? 0.15 : 0.6;
        });

      hideDetail();
    });

    // Click → drill down
    bubble.on('click', async (event, d) => {
      event.stopPropagation();
      await drillDown(d);
    });

    // Drag
    bubble.call(d3.drag()
      .on('start', (event, d) => {
        if (!event.active) simulation.alphaTarget(0.3).restart();
        d.fx = d.x; d.fy = d.y;
      })
      .on('drag', (event, d) => { d.fx = event.x; d.fy = event.y; })
      .on('end', (event, d) => {
        if (!event.active) simulation.alphaTarget(0);
        d.fx = null; d.fy = null;
      })
    );

    // Tick
    simulation.on('tick', () => {
      link
        .attr('x1', d => d.source.x)
        .attr('y1', d => d.source.y)
        .attr('x2', d => d.target.x)
        .attr('y2', d => d.target.y);
      bubble.attr('transform', d => `translate(${d.x},${d.y})`);
    });

    // Reset zoom
    svg.transition().duration(400)
      .call(zoom.transform, d3.zoomIdentity);
  }

  // ── Detail panel ──

  function showDetail(d) {
    const panel = document.getElementById('explorer-detail');
    const code = d.code || d.id || '';
    const title = d.title || d.name || d.full_name || '';
    const system = d.system_id || '';

    document.getElementById('detail-code').textContent =
      system ? `${system} : ${code}` : code;
    document.getElementById('detail-title').textContent = title;

    const meta = [];
    if (d.level !== undefined) meta.push(`Level ${d.level}`);
    if (d.is_leaf) meta.push('Leaf node');
    if (d.node_count) meta.push(`${d.node_count.toLocaleString()} codes`);
    if (d.region) meta.push(d.region);
    document.getElementById('detail-meta').textContent = meta.join(' · ');

    const actions = document.getElementById('detail-actions');
    if (system && code) {
      actions.innerHTML = `<a href="/system/${system}/${code}">Full detail →</a>`;
    } else if (d.id) {
      actions.innerHTML = `<a href="/system/${d.id}">View system →</a>`;
    } else {
      actions.innerHTML = '';
    }

    panel.classList.add('visible');
  }

  function hideDetail() {
    document.getElementById('explorer-detail').classList.remove('visible');
  }

  // ── Breadcrumb ──

  function updateBreadcrumb() {
    const el = document.getElementById('explorer-breadcrumb');
    el.innerHTML = '';

    navStack.forEach((frame, i) => {
      if (i > 0) {
        const sep = document.createElement('span');
        sep.className = 'crumb-sep';
        sep.textContent = '›';
        el.appendChild(sep);
      }

      const crumb = document.createElement('span');
      crumb.className = 'crumb' + (i === navStack.length - 1 ? ' active' : '');
      crumb.textContent = frame.label;
      crumb.addEventListener('click', () => navigateTo(i));
      el.appendChild(crumb);
    });
  }

  function navigateTo(index) {
    navStack = navStack.slice(0, index + 1);
    const frame = navStack[navStack.length - 1];
    renderBubbles(frame.nodes, frame.links || []);
    updateBreadcrumb();
  }

  // ── Drill-down logic ──

  async function drillDown(d) {
    let children = [];
    let links = [];
    let label = '';

    // Case 1: System node → load sectors/roots
    if (d.id && d.node_count !== undefined && !d.system_id) {
      const systemData = await TaxonomyAPI.getSystem(d.id);
      children = (systemData.roots || []).map(r => ({
        ...r,
        _id: `${d.id}:${r.code}`,
        name: r.title,
        _color: getColor(r),
        _radius: Math.max(25, Math.min(60, 30 + Math.sqrt(r.seq_order || 1) * 3)),
      }));
      label = d.name || d.id;
    }
    // Case 2: Classification node → load children
    else if (d.system_id && d.code) {
      const nodeChildren = await TaxonomyAPI.getChildren(d.system_id, d.code);
      children = nodeChildren.map(c => ({
        ...c,
        _id: `${d.system_id}:${c.code}`,
        name: c.title,
        _color: getColor(c),
        _radius: c.is_leaf ? 25 : 35,
      }));

      // Also load equivalences for visual connections
      try {
        const equivs = await TaxonomyAPI.getEquivalences(d.system_id, d.code);
        equivs.forEach(eq => {
          // Add equiv nodes as ghost bubbles
          const ghostId = `${eq.target_system}:${eq.target_code}`;
          if (!children.find(c => c._id === ghostId)) {
            children.push({
              _id: ghostId,
              code: eq.target_code,
              system_id: eq.target_system,
              title: eq.target_title || eq.target_code,
              name: eq.target_title || eq.target_code,
              _color: COLORS[eq.target_system] || '#64748B',
              _radius: 22,
              _ghost: true,
              is_leaf: true,
              match_type: eq.match_type,
            });
            links.push({
              source: `${d.system_id}:${d.code}`,
              target: ghostId,
            });
          }
        });
      } catch(e) { /* ignore */ }

      label = d.code;
    }

    if (children.length === 0) {
      // Leaf node — show hint
      document.getElementById('explorer-hint').textContent =
        `${d.code || d.id} is a leaf node. Right-click or Esc to go back.`;
      return;
    }

    // Push to nav stack
    navStack.push({ label, nodes: children, links });
    renderBubbles(children, links);
    updateBreadcrumb();

    document.getElementById('explorer-hint').textContent =
      `Showing ${children.length} nodes. Click to drill deeper. Esc to go back.`;
  }

  // ── Navigation: go back ──

  function goBack() {
    if (navStack.length <= 1) return;
    navStack.pop();
    const frame = navStack[navStack.length - 1];
    renderBubbles(frame.nodes, frame.links || []);
    updateBreadcrumb();
  }

  // Right-click to go back
  svg.on('contextmenu', (event) => {
    event.preventDefault();
    goBack();
  });

  // Esc to go back
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') goBack();
  });

  // ── Bootstrap: load systems as initial bubbles ──

  async function init() {
    const systems = await TaxonomyAPI.getSystems();
    const stats = await TaxonomyAPI.getStats();

    // Build edge weight lookup
    const edgeWeights = {};
    stats.forEach(s => {
      const key = [s.source_system, s.target_system].sort().join('|');
      edgeWeights[key] = (edgeWeights[key] || 0) + s.edge_count;
    });

    const nodes = systems.map(s => ({
      ...s,
      _id: s.id,
      name: s.name,
      _color: COLORS[s.id] || '#3B82F6',
      _radius: Math.max(40, Math.sqrt(s.node_count) * 1.8),
    }));

    // Build links (deduplicated)
    const links = [];
    const seen = new Set();
    stats.forEach(s => {
      const key = [s.source_system, s.target_system].sort().join('|');
      if (!seen.has(key)) {
        seen.add(key);
        links.push({
          source: s.source_system,
          target: s.target_system,
        });
      }
    });

    // Remap link source/target to _id
    const linksMapped = links.map(l => ({
      source: l.source,
      target: l.target,
    }));

    navStack = [{ label: 'Galaxy', nodes, links: linksMapped }];
    renderBubbles(nodes, linksMapped);
    updateBreadcrumb();
  }

  init();

})();
