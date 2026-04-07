/**
 * Galaxy View — animated d3-force simulation of classification systems
 * Living constellation with breathing nodes, pulsing data flow along edges,
 * orbiting particles, and gentle perpetual drift.
 */

document.addEventListener('DOMContentLoaded', async () => {
  const container = document.getElementById('galaxy-viz');
  if (!container) return;

  const systems = await TaxonomyAPI.getSystems();
  const stats = await TaxonomyAPI.getStats();

  const totalNodes = systems.reduce((sum, s) => sum + s.node_count, 0);
  const totalEdges = stats.reduce((sum, s) => sum + s.edge_count, 0);
  document.getElementById('stat-systems').textContent = systems.length;
  document.getElementById('stat-nodes').textContent = totalNodes.toLocaleString();
  document.getElementById('stat-edges').textContent = totalEdges.toLocaleString();

  // ── Responsive sizing ──
  function getDimensions() {
    const w = container.clientWidth;
    const h = Math.max(400, Math.min(w * 0.75, window.innerHeight - 200));
    return { w, h };
  }

  let { w: width, h: height } = getDimensions();
  const isMobile = width < 600;

  const maxRadius = isMobile ? 35 : 55;
  const minRadius = isMobile ? 18 : 25;
  const maxNodeCount = Math.max(...systems.map(s => s.node_count));

  const nodes = systems.map((s, i) => {
    const t = Math.sqrt(s.node_count / maxNodeCount);
    return {
      id: s.id,
      name: s.name,
      fullName: s.full_name,
      region: s.region,
      nodeCount: s.node_count,
      radius: minRadius + t * (maxRadius - minRadius),
      color: s.tint_color || '#3B82F6',
      // Each node gets a unique phase offset for breathing
      phase: (i / systems.length) * Math.PI * 2,
      breathSpeed: 0.4 + Math.random() * 0.3,
    };
  });

  const links = [];
  const seen = new Set();
  stats.forEach(s => {
    const key = [s.source_system, s.target_system].sort().join('|');
    if (!seen.has(key)) {
      seen.add(key);
      links.push({
        source: s.source_system,
        target: s.target_system,
        weight: s.edge_count,
      });
    }
  });

  // ── SVG setup ──
  const svg = d3.select(container)
    .append('svg')
    .attr('viewBox', `0 0 ${width} ${height}`)
    .attr('preserveAspectRatio', 'xMidYMid meet')
    .attr('class', 'galaxy-svg')
    .style('width', '100%')
    .style('height', 'auto');

  const defs = svg.append('defs');

  // Glow filter (soft outer glow)
  const glow = defs.append('filter').attr('id', 'glow').attr('x', '-50%').attr('y', '-50%').attr('width', '200%').attr('height', '200%');
  glow.append('feGaussianBlur').attr('stdDeviation', '4').attr('result', 'blur');
  const glowMerge = glow.append('feMerge');
  glowMerge.append('feMergeNode').attr('in', 'blur');
  glowMerge.append('feMergeNode').attr('in', 'SourceGraphic');

  // Stronger glow for hover
  const glowStrong = defs.append('filter').attr('id', 'glow-strong').attr('x', '-50%').attr('y', '-50%').attr('width', '200%').attr('height', '200%');
  glowStrong.append('feGaussianBlur').attr('stdDeviation', '8').attr('result', 'blur');
  const glowSMerge = glowStrong.append('feMerge');
  glowSMerge.append('feMergeNode').attr('in', 'blur');
  glowSMerge.append('feMergeNode').attr('in', 'SourceGraphic');

  // Gradient defs for each link (colored by source/target)
  links.forEach((l, i) => {
    const grad = defs.append('linearGradient')
      .attr('id', `link-grad-${i}`)
      .attr('gradientUnits', 'userSpaceOnUse');
    grad.append('stop').attr('offset', '0%').attr('class', `lg-${i}-start`);
    grad.append('stop').attr('offset', '100%').attr('class', `lg-${i}-end`);
  });

  // ── Background star field ──
  const starCount = isMobile ? 40 : 80;
  const starsG = svg.append('g').attr('class', 'stars');
  for (let i = 0; i < starCount; i++) {
    starsG.append('circle')
      .attr('cx', Math.random() * width)
      .attr('cy', Math.random() * height)
      .attr('r', Math.random() * 1.2 + 0.3)
      .attr('fill', '#fff')
      .attr('opacity', Math.random() * 0.3 + 0.05);
  }

  // ── Force simulation ──
  const padding = maxRadius + 15;
  const linkDist = isMobile ? 60 : 100;
  const chargeStrength = isMobile ? -120 : -200;

  const simulation = d3.forceSimulation(nodes)
    .force('link', d3.forceLink(links).id(d => d.id).distance(linkDist).strength(0.5))
    .force('charge', d3.forceManyBody().strength(chargeStrength))
    .force('center', d3.forceCenter(width / 2, height / 2))
    .force('collision', d3.forceCollide().radius(d => d.radius + (isMobile ? 8 : 12)))
    .force('x', d3.forceX(width / 2).strength(0.08))
    .force('y', d3.forceY(height / 2).strength(0.08))
    .velocityDecay(0.4);

  // ── Draw edges ──
  const linkG = svg.append('g');

  // Main edge lines
  const linkLine = linkG.selectAll('line.edge')
    .data(links)
    .join('line')
    .attr('class', 'edge')
    .attr('stroke', (d, i) => `url(#link-grad-${i})`)
    .attr('stroke-opacity', 0.12)
    .attr('stroke-width', d => Math.max(1, Math.log(d.weight) * 0.6));

  // Data-flow particles along edges
  const particlesPerLink = isMobile ? 1 : 2;
  const particles = [];
  links.forEach((l, li) => {
    for (let p = 0; p < particlesPerLink; p++) {
      particles.push({
        link: l,
        linkIndex: li,
        t: Math.random(),                       // position along edge [0,1]
        speed: 0.002 + Math.random() * 0.003,   // how fast it travels
        size: 1.5 + Math.random() * 1.5,
        reverse: p % 2 === 1,                    // alternate direction
      });
    }
  });

  const particleDots = svg.append('g')
    .selectAll('circle.particle')
    .data(particles)
    .join('circle')
    .attr('class', 'particle')
    .attr('r', d => d.size)
    .attr('fill', '#fff')
    .attr('opacity', 0);

  // ── Draw nodes ──
  const nodeG = svg.append('g');

  const node = nodeG.selectAll('g.node')
    .data(nodes)
    .join('g')
    .attr('class', 'node')
    .attr('cursor', 'pointer')
    .on('click', (event, d) => {
      window.location.href = `/system/${d.id}`;
    })
    .call(d3.drag()
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

  // Outer halo ring (subtle pulsing aura)
  node.append('circle')
    .attr('class', 'halo')
    .attr('r', d => d.radius + 6)
    .attr('fill', 'none')
    .attr('stroke', d => d.color)
    .attr('stroke-width', 0.5)
    .attr('stroke-opacity', 0);

  // Main circle
  node.append('circle')
    .attr('class', 'orb')
    .attr('r', d => d.radius)
    .attr('fill', d => d.color)
    .attr('fill-opacity', 0.12)
    .attr('stroke', d => d.color)
    .attr('stroke-width', 1.5)
    .attr('filter', 'url(#glow)');

  // Inner bright core
  node.append('circle')
    .attr('class', 'core')
    .attr('r', d => d.radius * 0.15)
    .attr('fill', d => d.color)
    .attr('fill-opacity', 0.4);

  // Labels
  const fontSize = isMobile ? '11px' : '13px';
  const countSize = isMobile ? '9px' : '10px';

  node.append('text')
    .attr('text-anchor', 'middle')
    .attr('dy', -6)
    .attr('fill', '#E8E6E1')
    .attr('font-family', "'Instrument Serif', serif")
    .attr('font-size', fontSize)
    .attr('pointer-events', 'none')
    .text(d => d.name);

  node.append('text')
    .attr('text-anchor', 'middle')
    .attr('dy', 10)
    .attr('fill', '#7A7872')
    .attr('font-family', "'Geist Mono', monospace")
    .attr('font-size', countSize)
    .attr('pointer-events', 'none')
    .text(d => `${d.nodeCount.toLocaleString()} codes`);

  // ── Hover effects ──
  let hoveredNode = null;

  node.on('mouseover', function(event, d) {
    hoveredNode = d.id;
    d3.select(this).select('.orb')
      .transition().duration(200)
      .attr('fill-opacity', 0.35)
      .attr('stroke-width', 2.5)
      .attr('filter', 'url(#glow-strong)');
    d3.select(this).select('.core')
      .transition().duration(200)
      .attr('r', d.radius * 0.25)
      .attr('fill-opacity', 0.7);
    d3.select(this).select('.halo')
      .transition().duration(200)
      .attr('stroke-opacity', 0.4)
      .attr('r', d.radius + 12);

    // Highlight connected edges
    linkLine.transition().duration(200)
      .attr('stroke-opacity', l =>
        (l.source.id === d.id || l.target.id === d.id) ? 0.5 : 0.04
      )
      .attr('stroke-width', l =>
        (l.source.id === d.id || l.target.id === d.id)
          ? Math.max(2, Math.log(l.weight) * 0.8)
          : Math.max(1, Math.log(l.weight) * 0.5)
      );

    // Dim unconnected nodes
    node.select('.orb').transition().duration(200)
      .attr('fill-opacity', n => {
        if (n.id === d.id) return 0.35;
        const connected = links.some(l =>
          (l.source.id === d.id && l.target.id === n.id) ||
          (l.target.id === d.id && l.source.id === n.id)
        );
        return connected ? 0.2 : 0.06;
      });

  }).on('mouseout', function(event, d) {
    hoveredNode = null;
    d3.select(this).select('.orb')
      .transition().duration(300)
      .attr('fill-opacity', 0.12)
      .attr('stroke-width', 1.5)
      .attr('filter', 'url(#glow)');
    d3.select(this).select('.core')
      .transition().duration(300)
      .attr('r', d.radius * 0.15)
      .attr('fill-opacity', 0.4);
    d3.select(this).select('.halo')
      .transition().duration(300)
      .attr('stroke-opacity', 0)
      .attr('r', d.radius + 6);

    linkLine.transition().duration(300)
      .attr('stroke-opacity', 0.12)
      .attr('stroke-width', l => Math.max(1, Math.log(l.weight) * 0.6));

    node.select('.orb').transition().duration(300)
      .attr('fill-opacity', 0.12);
  });

  // ── Tick (force layout) ──
  simulation.on('tick', () => {
    nodes.forEach(d => {
      d.x = Math.max(padding, Math.min(width - padding, d.x));
      d.y = Math.max(padding, Math.min(height - padding, d.y));
    });

    // Update link gradient endpoints
    links.forEach((l, i) => {
      svg.select(`.lg-${i}-start`)
        .attr('stop-color', l.source.color || '#3B82F6')
        .attr('stop-opacity', 0.6);
      svg.select(`.lg-${i}-end`)
        .attr('stop-color', l.target.color || '#3B82F6')
        .attr('stop-opacity', 0.6);
      svg.select(`#link-grad-${i}`)
        .attr('x1', l.source.x).attr('y1', l.source.y)
        .attr('x2', l.target.x).attr('y2', l.target.y);
    });

    linkLine
      .attr('x1', d => d.source.x).attr('y1', d => d.source.y)
      .attr('x2', d => d.target.x).attr('y2', d => d.target.y);

    node.attr('transform', d => `translate(${d.x},${d.y})`);
  });

  // ── Perpetual animation loop ──
  let t0 = performance.now();

  function animate(now) {
    const elapsed = (now - t0) / 1000; // seconds

    // 1. Breathing: subtle scale pulse on each node
    node.select('.orb').each(function(d) {
      if (hoveredNode === d.id) return; // skip hovered node
      const breath = 1 + Math.sin(elapsed * d.breathSpeed + d.phase) * 0.04;
      d3.select(this).attr('r', d.radius * breath);
    });

    // 2. Halo pulse (when not hovered)
    node.select('.halo').each(function(d) {
      if (hoveredNode === d.id) return;
      const pulse = Math.sin(elapsed * 0.8 + d.phase) * 0.5 + 0.5; // 0..1
      d3.select(this)
        .attr('r', d.radius + 4 + pulse * 4)
        .attr('stroke-opacity', pulse * 0.12);
    });

    // 3. Core shimmer
    node.select('.core').each(function(d) {
      if (hoveredNode === d.id) return;
      const shimmer = 0.3 + Math.sin(elapsed * 1.2 + d.phase + 1) * 0.15;
      d3.select(this).attr('fill-opacity', shimmer);
    });

    // 4. Star twinkle
    starsG.selectAll('circle').each(function(d, i) {
      const twinkle = 0.05 + Math.sin(elapsed * 0.5 + i * 1.7) * 0.15;
      d3.select(this).attr('opacity', Math.max(0.02, twinkle));
    });

    // 5. Data-flow particles traveling along edges
    particleDots.each(function(d) {
      d.t += d.reverse ? -d.speed : d.speed;
      if (d.t > 1) d.t -= 1;
      if (d.t < 0) d.t += 1;

      const src = d.link.source;
      const tgt = d.link.target;
      if (!src.x || !tgt.x) return;

      const x = src.x + (tgt.x - src.x) * d.t;
      const y = src.y + (tgt.y - src.y) * d.t;

      // Fade in/out at endpoints
      const edgeFade = Math.sin(d.t * Math.PI);
      const isConnected = hoveredNode &&
        (src.id === hoveredNode || tgt.id === hoveredNode);
      const baseOpacity = isConnected ? 0.7 : 0.3;

      d3.select(this)
        .attr('cx', x)
        .attr('cy', y)
        .attr('opacity', edgeFade * baseOpacity)
        .attr('fill', src.color || '#fff');
    });

    // 6. Gentle drift: keep simulation alive with tiny random nudges
    if (simulation.alpha() < 0.01) {
      nodes.forEach(d => {
        if (d.fx !== null) return; // skip dragged nodes
        d.vx += (Math.random() - 0.5) * 0.15;
        d.vy += (Math.random() - 0.5) * 0.15;
      });
      simulation.alpha(0.015).restart();
    }

    requestAnimationFrame(animate);
  }

  // Start animation after simulation settles a bit
  setTimeout(() => requestAnimationFrame(animate), 1500);

  // ── Resize ──
  window.addEventListener('resize', () => {
    const { w, h } = getDimensions();
    width = w;
    height = h;
    svg.attr('viewBox', `0 0 ${width} ${height}`);
    simulation.force('center', d3.forceCenter(width / 2, height / 2));
    simulation.force('x', d3.forceX(width / 2).strength(0.08));
    simulation.force('y', d3.forceY(height / 2).strength(0.08));
    simulation.alpha(0.3).restart();
  });
});
