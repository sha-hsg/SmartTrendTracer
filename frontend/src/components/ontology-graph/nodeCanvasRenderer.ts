/**
 * Custom canvas rendering for ontology graph nodes.
 * Handles node circles, collapse/expand indicators, labels, usage counts, and verified badges.
 */

interface RenderOptions {
  layoutType: 'force' | 'elk';
  collapsedNodes: Set<string>;
}

/**
 * Draws a single graph node on the canvas, including:
 * - Node circle with color
 * - Border for parent nodes (green = expanded, red = collapsed) in ELK layout
 * - Collapse/expand chevron indicator in ELK layout
 * - Text label below the node
 * - Usage count inside the node
 * - Verified badge dot
 */
export function renderNodeCanvas(
  node: any,
  ctx: CanvasRenderingContext2D,
  globalScale: number,
  options: RenderOptions
): void {
  const { layoutType, collapsedNodes } = options;
  const label = node.name;
  const fontSize = 12 / globalScale;
  const nodeRadius = node.size || 5;
  ctx.font = `${fontSize}px Sans-Serif`;

  // Draw node circle
  ctx.fillStyle = node.color || '#999';
  ctx.beginPath();
  ctx.arc(node.x, node.y, nodeRadius, 0, 2 * Math.PI, false);
  ctx.fill();

  // Draw border for nodes with children (in ELK layout)
  if (layoutType === 'elk' && node.child_count && node.child_count > 0) {
    ctx.strokeStyle = collapsedNodes.has(String(node.id)) ? '#ef4444' : '#10b981';
    ctx.lineWidth = 2 / globalScale;
    ctx.beginPath();
    ctx.arc(node.x, node.y, nodeRadius + 2, 0, 2 * Math.PI, false);
    ctx.stroke();
  }

  // Draw collapse/expand indicator for nodes with children (in ELK layout)
  if (layoutType === 'elk' && node.child_count && node.child_count > 0) {
    const isCollapsed = collapsedNodes.has(String(node.id));
    const indicatorSize = 8 / globalScale;
    const indicatorX = node.x + nodeRadius + 4;
    const indicatorY = node.y - nodeRadius;

    // Draw background circle for indicator
    ctx.fillStyle = '#ffffff';
    ctx.beginPath();
    ctx.arc(indicatorX, indicatorY, indicatorSize, 0, 2 * Math.PI, false);
    ctx.fill();

    ctx.strokeStyle = isCollapsed ? '#ef4444' : '#10b981';
    ctx.lineWidth = 1.5 / globalScale;
    ctx.beginPath();
    ctx.arc(indicatorX, indicatorY, indicatorSize, 0, 2 * Math.PI, false);
    ctx.stroke();

    // Draw chevron
    ctx.strokeStyle = isCollapsed ? '#ef4444' : '#10b981';
    ctx.lineWidth = 2 / globalScale;
    ctx.beginPath();
    if (isCollapsed) {
      // Chevron right for collapsed
      ctx.moveTo(indicatorX - indicatorSize / 2, indicatorY - indicatorSize / 2);
      ctx.lineTo(indicatorX + indicatorSize / 3, indicatorY);
      ctx.lineTo(indicatorX - indicatorSize / 2, indicatorY + indicatorSize / 2);
    } else {
      // Chevron down for expanded
      ctx.moveTo(indicatorX - indicatorSize / 2, indicatorY - indicatorSize / 3);
      ctx.lineTo(indicatorX, indicatorY + indicatorSize / 2);
      ctx.lineTo(indicatorX + indicatorSize / 2, indicatorY - indicatorSize / 3);
    }
    ctx.stroke();
  }

  // Draw label
  ctx.textAlign = 'center';
  ctx.textBaseline = 'middle';
  ctx.fillStyle = '#333';
  ctx.fillText(label, node.x, node.y + nodeRadius + fontSize);

  // Draw usage count
  if (node.usage > 0) {
    ctx.font = `${fontSize * 0.8}px Sans-Serif`;
    ctx.fillStyle = '#666';
    ctx.fillText(`(${node.usage})`, node.x, node.y);
  }

  // Draw verified badge (only if not already showing collapse indicator)
  if (node.verified && !(layoutType === 'elk' && node.child_count > 0)) {
    ctx.fillStyle = '#10b981';
    ctx.beginPath();
    ctx.arc(node.x + nodeRadius, node.y - nodeRadius, 3, 0, 2 * Math.PI, false);
    ctx.fill();
  }
}
