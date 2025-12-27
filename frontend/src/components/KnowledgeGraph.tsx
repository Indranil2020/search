/**
 * Knowledge Graph Component
 * 
 * Interactive visualization of citation networks.
 * Shows paper relationships, clusters, and connections.
 */

import React, { useEffect, useRef, useState } from 'react';
import * as d3 from 'd3';
import type { Paper } from '../types/paper';
import { getReliabilityClasses } from '../utils/colors';

interface GraphNode {
  id: string;
  title: string;
  year: number | null;
  citations: number;
  reliability: string;
  paper: Paper;
  x?: number;
  y?: number;
  fx?: number | null;
  fy?: number | null;
}

interface GraphLink {
  source: string;
  target: string;
  type: 'cites' | 'cited_by' | 'related';
}

interface KnowledgeGraphProps {
  papers: Paper[];
  width?: number;
  height?: number;
  onPaperSelect?: (paper: Paper) => void;
}

export const KnowledgeGraph: React.FC<KnowledgeGraphProps> = ({
  papers,
  width = 800,
  height = 600,
  onPaperSelect
}) => {
  const svgRef = useRef<SVGSVGElement>(null);
  const [selectedNode, setSelectedNode] = useState<string | null>(null);

  useEffect(() => {
    if (!svgRef.current || papers.length === 0) return;

    // Clear previous graph
    d3.select(svgRef.current).selectAll('*').remove();

    // Build nodes and links
    const nodes: GraphNode[] = papers.slice(0, 100).map(paper => ({
      id: paper.id,
      title: paper.title.length > 50 ? paper.title.substring(0, 50) + '...' : paper.title,
      year: paper.year,
      citations: paper.citationCount,
      reliability: paper.reliability.color,
      paper
    }));

    // Create links based on shared keywords and citations
    const links: GraphLink[] = [];
    const nodeMap = new Map(nodes.map(n => [n.id, n]));

    // Link papers with similar keywords
    for (let i = 0; i < nodes.length; i++) {
      for (let j = i + 1; j < nodes.length; j++) {
        const p1 = nodes[i].paper;
        const p2 = nodes[j].paper;
        
        // Check keyword overlap
        const keywords1 = new Set(p1.keywords.map(k => k.toLowerCase()));
        const keywords2 = new Set(p2.keywords.map(k => k.toLowerCase()));
        
        let overlap = 0;
        keywords1.forEach(k => {
          if (keywords2.has(k)) overlap++;
        });
        
        if (overlap >= 2) {
          links.push({
            source: p1.id,
            target: p2.id,
            type: 'related'
          });
        }
      }
    }

    const svg = d3.select(svgRef.current);

    // Create zoom behavior
    const zoom = d3.zoom<SVGSVGElement, unknown>()
      .scaleExtent([0.1, 4])
      .on('zoom', (event) => {
        container.attr('transform', event.transform);
      });

    svg.call(zoom);

    const container = svg.append('g');

    // Color scale for reliability
    const reliabilityColors: Record<string, string> = {
      green: '#22c55e',
      yellow: '#eab308',
      red: '#ef4444'
    };

    // Size scale for citations
    const sizeScale = d3.scaleSqrt()
      .domain([0, d3.max(nodes, d => d.citations) || 100])
      .range([5, 25]);

    // Create force simulation
    const simulation = d3.forceSimulation(nodes as d3.SimulationNodeDatum[])
      .force('link', d3.forceLink(links)
        .id((d: any) => d.id)
        .distance(100)
        .strength(0.5))
      .force('charge', d3.forceManyBody().strength(-200))
      .force('center', d3.forceCenter(width / 2, height / 2))
      .force('collision', d3.forceCollide().radius((d: any) => sizeScale(d.citations) + 5));

    // Draw links
    const link = container.append('g')
      .selectAll('line')
      .data(links)
      .join('line')
      .attr('stroke', '#e5e7eb')
      .attr('stroke-width', 1)
      .attr('stroke-opacity', 0.6);

    // Draw nodes
    const node = container.append('g')
      .selectAll('g')
      .data(nodes)
      .join('g')
      .attr('cursor', 'pointer')
      .call(d3.drag<SVGGElement, GraphNode>()
        .on('start', (event, d) => {
          if (!event.active) simulation.alphaTarget(0.3).restart();
          d.fx = d.x;
          d.fy = d.y;
        })
        .on('drag', (event, d) => {
          d.fx = event.x;
          d.fy = event.y;
        })
        .on('end', (event, d) => {
          if (!event.active) simulation.alphaTarget(0);
          d.fx = null;
          d.fy = null;
        }) as any);

    // Node circles
    node.append('circle')
      .attr('r', d => sizeScale(d.citations))
      .attr('fill', d => reliabilityColors[d.reliability] || '#9ca3af')
      .attr('stroke', '#fff')
      .attr('stroke-width', 2)
      .on('click', (event, d) => {
        setSelectedNode(d.id);
        onPaperSelect?.(d.paper);
      })
      .on('mouseover', function(event, d) {
        d3.select(this)
          .transition()
          .duration(200)
          .attr('stroke-width', 4);
      })
      .on('mouseout', function(event, d) {
        d3.select(this)
          .transition()
          .duration(200)
          .attr('stroke-width', 2);
      });

    // Node labels (only for larger nodes)
    node.filter(d => d.citations > 10)
      .append('text')
      .text(d => d.year ? d.year.toString() : '')
      .attr('text-anchor', 'middle')
      .attr('dy', '0.35em')
      .attr('font-size', '10px')
      .attr('fill', '#fff')
      .attr('pointer-events', 'none');

    // Tooltips
    node.append('title')
      .text(d => `${d.paper.title}\n${d.paper.authorString}\n${d.citations} citations`);

    // Update positions on tick
    simulation.on('tick', () => {
      link
        .attr('x1', (d: any) => d.source.x)
        .attr('y1', (d: any) => d.source.y)
        .attr('x2', (d: any) => d.target.x)
        .attr('y2', (d: any) => d.target.y);

      node.attr('transform', (d: any) => `translate(${d.x},${d.y})`);
    });

    return () => {
      simulation.stop();
    };
  }, [papers, width, height, onPaperSelect]);

  return (
    <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
      <div className="px-4 py-3 border-b border-gray-200">
        <h3 className="font-semibold text-gray-900">Knowledge Graph</h3>
        <p className="text-xs text-gray-500 mt-1">
          Node size = citations, color = reliability. Drag to explore, scroll to zoom.
        </p>
      </div>
      
      {/* Legend */}
      <div className="px-4 py-2 bg-gray-50 border-b border-gray-200 flex items-center gap-4 text-xs">
        <div className="flex items-center gap-1">
          <span className="w-3 h-3 rounded-full bg-green-500" />
          High reliability
        </div>
        <div className="flex items-center gap-1">
          <span className="w-3 h-3 rounded-full bg-yellow-500" />
          Moderate
        </div>
        <div className="flex items-center gap-1">
          <span className="w-3 h-3 rounded-full bg-red-500" />
          Lower
        </div>
        <div className="ml-auto text-gray-400">
          Showing top {Math.min(papers.length, 100)} papers
        </div>
      </div>
      
      <svg
        ref={svgRef}
        width={width}
        height={height}
        className="block"
      />
    </div>
  );
};

export default KnowledgeGraph;
