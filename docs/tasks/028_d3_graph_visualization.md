# Task 028: D3 Graph Visualization Implementation ⏳ Not Started

**Objective**: Implement a comprehensive D3.js-based graph visualization system for ArangoDB that supports multiple layout types (force-directed, hierarchical, radial, Sankey) with LLM-driven visualization recommendations and dynamic template generation.

**Requirements**:
1. Support all visualization types: force-directed, hierarchical tree, radial, and Sankey diagrams
2. Dynamic template generation with LLM recommendations using Vertex AI Gemini Flash 2.5
3. Standalone HTML output that works in Chrome without a server
4. Modern, clean graph visualization styling
5. Integration with existing ArangoDB query results
6. FastAPI server for serving visualization endpoints with caching
7. CLI commands for generating visualizations
8. Performance optimization for medium-sized graphs (100-1000 nodes)

## Overview

This task implements a flexible D3.js graph visualization system that transforms ArangoDB query results into interactive visual representations. The system uses a modular architecture with core D3.js modules, LLM-driven template selection, and dynamic visualization generation based on query characteristics.

## Research Summary

Based on extensive research, we will build a custom solution using:
- Core D3.js modules (d3-force, d3-hierarchy, d3-sankey)
- Custom wrapper for unified interface
- LLM integration for intelligent visualization selection
- Template-based rendering with dynamic customization
- FastAPI backend with caching support

## Implementation Tasks

### Task 1: D3.js Module Infrastructure ✅ Complete

**Implementation Steps**:
- [x] 1.1 Create visualization package structure
  - Create `/src/arangodb/visualization/` directory
  - Create `/src/arangodb/visualization/core/` for core modules
  - Create `/src/arangodb/visualization/templates/` for HTML templates
  - Create `/src/arangodb/visualization/styles/` for CSS themes
  - Create `/static/` directory for serving static assets
  - Update pyproject.toml with D3.js dependencies

- [x] 1.2 Implement D3VisualizationEngine class
  - Create `/src/arangodb/visualization/core/d3_engine.py`
  - Define base class with methods for each layout type
  - Implement template loading system
  - Add configuration management
  - Create method signatures for generate_visualization()

- [x] 1.3 Create base HTML template structure
  - Create `/src/arangodb/visualization/templates/base.html`
  - Include D3.js v7 from CDN
  - Set up modern CSS styling framework
  - Create placeholder divs for graph container
  - Implement responsive layout

- [x] 1.4 Implement data transformation utilities
  - Create `/src/arangodb/visualization/core/data_transformer.py`
  - Implement ArangoDB to D3.js format conversion
  - Handle node and edge transformations
  - Add metadata extraction
  - Create sampling functions for large graphs

- [x] 1.5 Add verification output
  - Create test visualization with mock data
  - Generate standalone HTML file
  - Verify D3.js loads correctly
  - Test basic SVG rendering
  - Output rich table with transformation metrics

- [x] 1.6 Git commit infrastructure

**Technical Specifications**:
- Use D3.js v7 for all visualizations
- Support ES6 module syntax
- Implement lazy loading for D3 modules
- Use type hints throughout Python code
- Follow ArangoDB project coding standards

**Verification Method**:
- Generate test.html with basic D3 visualization
- Open in Chrome and verify rendering
- Rich table showing:
  - Template loaded: ✓/✗
  - D3.js loaded: ✓/✗
  - SVG rendered: ✓/✗
  - Data transformed: ✓/✗

**Acceptance Criteria**:
- D3.js loads successfully in browser
- Basic SVG element renders
- Data transformation utilities work
- Template system loads files correctly

### Task 2: Force-Directed Layout Implementation ✅ Complete

**Implementation Steps**:
- [x] 2.1 Create force layout template
  - Create `/src/arangodb/visualization/templates/force.html`
  - Implement D3 force simulation
  - Add node drag functionality
  - Implement zoom and pan controls
  - Add tooltip on hover

**Starting Point Code** (Based on Mike Bostock's examples):
```html
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>Force-Directed Graph</title>
  <script src="https://d3js.org/d3.v7.min.js"></script>
  <style>
    .links line {
      stroke: #999;
      stroke-opacity: 0.6;
    }
    .nodes circle {
      stroke: #fff;
      stroke-width: 1.5px;
    }
  </style>
</head>
<body>
  <svg width="960" height="600"></svg>
  <script>
    const svg = d3.select("svg"),
          width = +svg.attr("width"),
          height = +svg.attr("height");

    const simulation = d3.forceSimulation()
        .force("link", d3.forceLink().id(d => d.id))
        .force("charge", d3.forceManyBody())
        .force("center", d3.forceCenter(width / 2, height / 2));

    // Load data and create visualization
    d3.json("graph.json").then(function(graph) {
      // Add links
      const link = svg.append("g")
          .attr("class", "links")
        .selectAll("line")
        .data(graph.links)
        .enter().append("line")
          .attr("stroke-width", d => Math.sqrt(d.value));

      // Add nodes
      const node = svg.append("g")
          .attr("class", "nodes")
        .selectAll("circle")
        .data(graph.nodes)
        .enter().append("circle")
          .attr("r", 5)
          .attr("fill", d => color(d.group))
          .call(d3.drag()
              .on("start", dragstarted)
              .on("drag", dragged)
              .on("end", dragended));

      // Add tooltip
      node.append("title")
          .text(d => d.id);

      simulation
          .nodes(graph.nodes)
          .on("tick", ticked);

      simulation.force("link")
          .links(graph.links);

      function ticked() {
        link
            .attr("x1", d => d.source.x)
            .attr("y1", d => d.source.y)
            .attr("x2", d => d.target.x)
            .attr("y2", d => d.target.y);

        node
            .attr("cx", d => d.x)
            .attr("cy", d => d.y);
      }
    });

    function dragstarted(event, d) {
      if (!event.active) simulation.alphaTarget(0.3).restart();
      d.fx = d.x;
      d.fy = d.y;
    }

    function dragged(event, d) {
      d.fx = event.x;
      d.fy = event.y;
    }

    function dragended(event, d) {
      if (!event.active) simulation.alphaTarget(0);
      d.fx = null;
      d.fy = null;
    }
  </script>
</body>
</html>
```

- [x] 2.2 Implement force layout in D3VisualizationEngine
  - Add generate_force_layout() method
  - Implement physics configuration options
  - Handle node and link styling
  - Add color scale for node types
  - Implement size scaling options

- [x] 2.3 Create force layout CSS theme
  - Create `/src/arangodb/visualization/styles/force.css`
  - Modern clean styling for nodes and edges
  - Hover and selection states
  - Tooltip styling
  - Responsive design elements

- [x] 2.4 Add interactive features
  - Node click to highlight connections
  - Edge weight visualization
  - Dynamic node sizing
  - Collision detection
  - Force strength controls

- [x] 2.5 Verify force layout functionality
  - Generate sample force-directed graph
  - Test with 50-100 nodes
  - Verify physics simulation
  - Check performance metrics
  - Output verification table

- [x] 2.6 Git commit force layout

**Technical Specifications**:
- Use d3-force module
- Support Barnes-Hut optimization
- Configurable force parameters
- WebGL fallback for large graphs
- 60 FPS target framerate

**Verification Method**:
- Generate force_test.html with ArangoDB sample data
- Measure frame rate during simulation
- Rich table with performance metrics:
  - Nodes rendered: count
  - FPS: average/min/max
  - Simulation time: milliseconds
  - Interaction responsiveness: pass/fail

**Acceptance Criteria**:
- Force simulation runs smoothly
- Nodes are draggable
- Graph is zoomable and pannable
- Performance meets targets

### Task 3: Hierarchical Tree Layout Implementation ✅ Complete

**Implementation Steps**:
- [x] 3.1 Create tree layout template
  - Create `/src/arangodb/visualization/templates/tree.html`
  - Implement D3 tree hierarchy
  - Add collapsible nodes
  - Support both vertical and horizontal orientations
  - Add path animations

**Starting Point Code** (Based on collapsible tree examples):
```html
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>Hierarchical Tree</title>
  <script src="https://d3js.org/d3.v7.min.js"></script>
  <style>
    .node circle {
      fill: #fff;
      stroke: steelblue;
      stroke-width: 3px;
    }
    .node text {
      font: 12px sans-serif;
    }
    .link {
      fill: none;
      stroke: #ccc;
      stroke-width: 2px;
    }
  </style>
</head>
<body>
  <svg width="960" height="600"></svg>
  <script>
    const margin = {top: 20, right: 120, bottom: 20, left: 120},
          width = 960 - margin.right - margin.left,
          height = 600 - margin.top - margin.bottom;

    const svg = d3.select("svg")
        .attr("width", width + margin.right + margin.left)
        .attr("height", height + margin.top + margin.bottom)
      .append("g")
        .attr("transform", `translate(${margin.left},${margin.top})`);

    let i = 0;
    const duration = 750;

    // Declare tree layout and root
    const tree = d3.tree().size([height, width]);

    // Load data
    d3.json("tree.json").then(function(data) {
      // Compute the new tree layout
      let root = d3.hierarchy(data);
      root.x0 = height / 2;
      root.y0 = 0;

      // Collapse after the second level
      root.children.forEach(collapse);

      update(root);
    });

    // Collapse the node and all it's children
    function collapse(d) {
      if(d.children) {
        d._children = d.children;
        d._children.forEach(collapse);
        d.children = null;
      }
    }

    function update(source) {
      // Compute the new tree layout
      const treeData = tree(root);
      const nodes = treeData.descendants();
      const links = treeData.descendants().slice(1);

      // Normalize for fixed-depth
      nodes.forEach(d => d.y = d.depth * 180);

      // ****************** Nodes section ***************************

      // Update the nodes...
      const node = svg.selectAll('g.node')
          .data(nodes, d => d.id || (d.id = ++i));

      // Enter any new nodes at the parent's previous position
      const nodeEnter = node.enter().append('g')
          .attr('class', 'node')
          .attr("transform", d => `translate(${source.y0},${source.x0})`)
          .on('click', click);

      // Add Circle for the nodes
      nodeEnter.append('circle')
          .attr('class', 'node')
          .attr('r', 1e-6)
          .style("fill", d => d._children ? "lightsteelblue" : "#fff");

      // Add labels for the nodes
      nodeEnter.append('text')
          .attr("dy", ".35em")
          .attr("x", d => d.children || d._children ? -13 : 13)
          .attr("text-anchor", d => d.children || d._children ? "end" : "start")
          .text(d => d.data.name);

      // UPDATE
      const nodeUpdate = nodeEnter.merge(node);

      // Transition to the proper position for the node
      nodeUpdate.transition()
          .duration(duration)
          .attr("transform", d => `translate(${d.y},${d.x})`);

      // Update the node attributes and style
      nodeUpdate.select('circle.node')
          .attr('r', 10)
          .style("fill", d => d._children ? "lightsteelblue" : "#fff")
          .attr('cursor', 'pointer');

      // Remove any exiting nodes
      const nodeExit = node.exit().transition()
          .duration(duration)
          .attr("transform", d => `translate(${source.y},${source.x})`)
          .remove();

      // On exit reduce the node circles size to 0
      nodeExit.select('circle')
          .attr('r', 1e-6);

      // On exit reduce the opacity of text labels
      nodeExit.select('text')
          .style('fill-opacity', 1e-6);

      // ****************** links section ***************************

      // Update the links...
      const link = svg.selectAll('path.link')
          .data(links, d => d.id);

      // Enter any new links at the parent's previous position
      const linkEnter = link.enter().insert('path', "g")
          .attr("class", "link")
          .attr('d', d => {
            const o = {x: source.x0, y: source.y0};
            return diagonal(o, o);
          });

      // UPDATE
      const linkUpdate = linkEnter.merge(link);

      // Transition back to the parent element position
      linkUpdate.transition()
          .duration(duration)
          .attr('d', d => diagonal(d, d.parent));

      // Remove any exiting links
      const linkExit = link.exit().transition()
          .duration(duration)
          .attr('d', d => {
            const o = {x: source.x, y: source.y};
            return diagonal(o, o);
          })
          .remove();

      // Store the old positions for transition
      nodes.forEach(d => {
        d.x0 = d.x;
        d.y0 = d.y;
      });

      // Creates a curved (diagonal) path from parent to the child nodes
      function diagonal(s, d) {
        path = `M ${s.y} ${s.x}
                C ${(s.y + d.y) / 2} ${s.x},
                  ${(s.y + d.y) / 2} ${d.x},
                  ${d.y} ${d.x}`;
        return path;
      }

      // Toggle children on click
      function click(event, d) {
        if (d.children) {
            d._children = d.children;
            d.children = null;
        } else {
            d.children = d._children;
            d._children = null;
        }
        update(d);
      }
    }
  </script>
</body>
</html>
```

- [x] 3.2 Implement tree layout in D3VisualizationEngine
  - Add generate_tree_layout() method
  - Implement tree data structure conversion
  - Handle parent-child relationships
  - Add level-based styling
  - Support dynamic tree updates

- [x] 3.3 Create tree layout CSS theme
  - Create `/src/arangodb/visualization/styles/tree.css`
  - Node styling by depth level
  - Link path styling
  - Expand/collapse indicators
  - Breadcrumb navigation styling

- [x] 3.4 Add tree-specific interactions
  - Click to expand/collapse branches
  - Breadcrumb navigation
  - Path highlighting on hover
  - Subtree isolation
  - Level filtering

- [x] 3.5 Verify tree layout functionality
  - Generate hierarchical data sample
  - Test expand/collapse behavior
  - Verify path calculations
  - Check layout algorithms
  - Output verification metrics

- [x] 3.6 Git commit tree layout

**Technical Specifications**:
- Use d3-hierarchy module
- Support Reingold-Tilford algorithm
- Handle multiple root nodes
- Animate transitions
- Optimize for deep trees

**Verification Method**:
- Generate tree_test.html with hierarchical data
- Test interaction features
- Rich table with tree metrics:
  - Max depth: number
  - Total nodes: count
  - Collapsed nodes: count
  - Render time: milliseconds

**Acceptance Criteria**:
- Tree renders correctly
- Nodes expand/collapse smoothly
- Paths are properly drawn
- Layout handles deep hierarchies

### Task 4: Radial Layout Implementation ⏳ Not Started

**Implementation Steps**:
- [ ] 4.1 Create radial layout template
  - Create `/src/arangodb/visualization/templates/radial.html`
  - Implement radial tree transformation
  - Add circular node arrangement
  - Support arc-based edges
  - Implement radial zoom

**Starting Point Code** (Based on radial tree examples):
```html
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>Radial Tree</title>
  <script src="https://d3js.org/d3.v7.min.js"></script>
  <style>
    .link {
      fill: none;
      stroke: #555;
      stroke-opacity: 0.4;
      stroke-width: 1.5px;
    }
    .node circle {
      fill: #999;
      cursor: pointer;
    }
    .node circle:hover {
      fill: #ff7f0e;
    }
    .node--internal circle {
      fill: #555;
    }
    .node--internal text {
      text-shadow: 0 1px 0 #fff, 0 -1px 0 #fff, 1px 0 0 #fff, -1px 0 0 #fff;
    }
    .node--leaf text {
      fill: #555;
    }
    .node--root circle {
      fill: #ff7f0e;
    }
  </style>
</head>
<body>
  <svg width="960" height="960"></svg>
  <script>
    const width = 960;
    const height = 960;
    const radius = width / 2;

    const tree = d3.tree()
        .size([2 * Math.PI, radius - 100])
        .separation((a, b) => (a.parent == b.parent ? 1 : 2) / a.depth);

    const svg = d3.select("svg")
        .attr("width", width)
        .attr("height", height);

    const g = svg.append("g")
        .attr("transform", `translate(${width / 2},${height / 2})`);

    const link = g.append("g")
        .attr("fill", "none")
        .attr("stroke", "#555")
        .attr("stroke-opacity", 0.4)
        .attr("stroke-width", 1.5);

    const node = g.append("g")
        .attr("stroke-linejoin", "round")
        .attr("stroke-width", 3);

    d3.json("tree.json").then(data => {
      const root = tree(d3.hierarchy(data));

      link.selectAll("path")
        .data(root.links())
        .join("path")
          .attr("d", d3.linkRadial()
              .angle(d => d.x)
              .radius(d => d.y));

      const nodeGroup = node.selectAll("g")
        .data(root.descendants())
        .join("g")
          .attr("transform", d => `
            rotate(${d.x * 180 / Math.PI - 90})
            translate(${d.y},0)
          `);

      nodeGroup.append("circle")
          .attr("fill", d => d.children ? "#555" : "#999")
          .attr("r", 2.5);

      nodeGroup.append("text")
          .attr("dy", "0.31em")
          .attr("x", d => d.x < Math.PI === !d.children ? 6 : -6)
          .attr("text-anchor", d => d.x < Math.PI === !d.children ? "start" : "end")
          .attr("transform", d => d.x >= Math.PI ? "rotate(180)" : null)
          .text(d => d.data.name)
          .attr("font-family", "sans-serif")
          .attr("font-size", 10)
          .clone(true).lower()
          .attr("stroke", "white");

      // Add zoom and rotation
      const zoom = d3.zoom()
          .scaleExtent([0.5, 3])
          .on("zoom", zoomed);

      svg.call(zoom);

      function zoomed(event) {
        g.attr("transform", event.transform);
      }

      // Add click interaction for collapsing
      nodeGroup.on("click", clicked);

      function clicked(event, d) {
        if (d.children) {
          d._children = d.children;
          d.children = null;
        } else if (d._children) {
          d.children = d._children;
          d._children = null;
        }
        update();
      }

      function update() {
        const newRoot = tree(root);

        // Update links
        link.selectAll("path")
          .data(newRoot.links())
          .join("path")
            .transition()
            .duration(750)
            .attr("d", d3.linkRadial()
                .angle(d => d.x)
                .radius(d => d.y));

        // Update nodes
        const nodeUpdate = node.selectAll("g")
          .data(newRoot.descendants());

        nodeUpdate.transition()
          .duration(750)
          .attr("transform", d => `
            rotate(${d.x * 180 / Math.PI - 90})
            translate(${d.y},0)
          `);

        nodeUpdate.select("circle")
          .attr("fill", d => d.children ? "#555" : "#999");
      }
    });
  </script>
</body>
</html>
```

- [ ] 4.2 Implement radial layout in D3VisualizationEngine
  - Add generate_radial_layout() method
  - Transform tree to radial coordinates
  - Handle angular distribution
  - Implement level-based radius
  - Add sector highlighting

- [ ] 4.3 Create radial layout CSS theme
  - Create `/src/arangodb/visualization/styles/radial.css`
  - Circular node styling
  - Arc path styling
  - Sector backgrounds
  - Radial gradient effects

- [ ] 4.4 Add radial-specific interactions
  - Rotate to focus on sector
  - Zoom to subtree
  - Angular selection
  - Radial distance filtering
  - Center node switching

- [ ] 4.5 Verify radial layout functionality
  - Generate radial test data
  - Test rotation mechanics
  - Verify angular calculations
  - Check sector distribution
  - Output performance metrics

- [ ] 4.6 Git commit radial layout

**Technical Specifications**:
- Based on d3-hierarchy with polar transform
- Support 360-degree distribution
- Handle overlapping labels
- Optimize for circular navigation
- Support fisheye distortion

**Verification Method**:
- Generate radial_test.html
- Test rotation and zoom
- Rich table with radial metrics:
  - Angular distribution: even/uneven
  - Label overlap: count
  - Render performance: FPS
  - Interaction latency: milliseconds

**Acceptance Criteria**:
- Radial tree renders correctly
- Rotation is smooth
- Labels are readable
- No significant overlaps

### Task 5: Sankey Diagram Implementation ⏳ Not Started

**Implementation Steps**:
- [ ] 5.1 Create Sankey layout template
  - Create `/src/arangodb/visualization/templates/sankey.html`
  - Implement D3 Sankey diagram
  - Add flow visualization
  - Support node positioning
  - Implement path gradients

**Starting Point Code** (Based on d3-sankey examples):
```html
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>Sankey Diagram</title>
  <script src="https://d3js.org/d3.v7.min.js"></script>
  <script src="https://unpkg.com/d3-sankey@0.12.3/dist/d3-sankey.min.js"></script>
  <style>
    .node rect {
      cursor: move;
      fill-opacity: .9;
      shape-rendering: crispEdges;
    }
    .node text {
      pointer-events: none;
      text-shadow: 0 1px 0 #fff;
    }
    .link {
      fill: none;
      stroke: #000;
      stroke-opacity: .2;
    }
    .link:hover {
      stroke-opacity: .5;
    }
  </style>
</head>
<body>
  <svg width="960" height="600"></svg>
  <script>
    const margin = {top: 10, right: 10, bottom: 10, left: 10};
    const width = 960 - margin.left - margin.right;
    const height = 600 - margin.top - margin.bottom;

    const svg = d3.select("svg")
        .attr("width", width + margin.left + margin.right)
        .attr("height", height + margin.top + margin.bottom);

    const g = svg.append("g")
        .attr("transform", `translate(${margin.left},${margin.top})`);

    const color = d3.scaleOrdinal(d3.schemeCategory10);

    const sankey = d3.sankey()
        .nodeWidth(15)
        .nodePadding(15)
        .extent([[1, 1], [width - 1, height - 6]]);

    d3.json("sankey.json").then(data => {
      sankey(data);

      // Add links
      const link = g.append("g")
          .attr("class", "links")
          .attr("fill", "none")
          .attr("stroke-opacity", 0.2)
        .selectAll("path")
        .data(data.links)
        .enter().append("path")
          .attr("class", "link")
          .attr("d", d3.sankeyLinkHorizontal())
          .attr("stroke", d => color(d.source.category))
          .attr("stroke-width", d => Math.max(1, d.width));

      // Add link titles
      link.append("title")
          .text(d => `${d.source.name} → ${d.target.name}\n${d.value}`);

      // Add nodes
      const node = g.append("g")
          .attr("class", "nodes")
          .attr("font-family", "sans-serif")
          .attr("font-size", 10)
        .selectAll("g")
        .data(data.nodes)
        .enter().append("g")
          .attr("class", "node");

      node.append("rect")
          .attr("x", d => d.x0)
          .attr("y", d => d.y0)
          .attr("height", d => d.y1 - d.y0)
          .attr("width", d => d.x1 - d.x0)
          .attr("fill", d => color(d.category))
          .attr("stroke", "#000");

      // Add node titles
      node.append("text")
          .attr("x", d => d.x0 - 6)
          .attr("y", d => (d.y1 + d.y0) / 2)
          .attr("dy", "0.35em")
          .attr("text-anchor", "end")
          .text(d => d.name)
        .filter(d => d.x0 < width / 2)
          .attr("x", d => d.x1 + 6)
          .attr("text-anchor", "start");

      node.append("title")
          .text(d => `${d.name}\n${d.value}`);

      // Add drag functionality
      function dragmove(event, d) {
        const rectY = d.y0;
        const rectX = d.x0;
        
        d.y0 = Math.max(0, Math.min(height - (d.y1 - d.y0), event.y));
        d.y1 = d.y0 + (d.y1 - rectY);
        
        d3.select(this).select("rect")
            .attr("y", d.y0);
        
        d3.select(this).select("text")
            .attr("y", (d.y1 + d.y0) / 2);
        
        sankey.update(data);
        link.attr("d", d3.sankeyLinkHorizontal());
      }

      node.call(d3.drag()
          .subject(d => d)
          .on("start", function() { this.parentNode.appendChild(this); })
          .on("drag", dragmove));

      // Custom gradient for links (optional enhancement)
      const gradient = svg.append("defs").selectAll("linearGradient")
          .data(data.links)
          .enter().append("linearGradient")
            .attr("id", (d, i) => `gradient${i}`)
            .attr("gradientUnits", "userSpaceOnUse")
            .attr("x1", d => d.source.x1)
            .attr("x2", d => d.target.x0);

      gradient.append("stop")
          .attr("offset", "0%")
          .attr("stop-color", d => color(d.source.category));

      gradient.append("stop")
          .attr("offset", "100%")
          .attr("stop-color", d => color(d.target.category));

      // Apply gradients to links
      link.attr("stroke", (d, i) => `url(#gradient${i})`);
    });

    // Sample data format for sankey.json:
    // {
    //   "nodes": [
    //     {"name": "Node A"},
    //     {"name": "Node B"},
    //     {"name": "Node C"}
    //   ],
    //   "links": [
    //     {"source": 0, "target": 1, "value": 2},
    //     {"source": 1, "target": 2, "value": 1}
    //   ]
    // }
  </script>
</body>
</html>
```

- [ ] 5.2 Implement Sankey layout in D3VisualizationEngine
  - Add generate_sankey_layout() method
  - Import d3-sankey module
  - Handle flow calculations
  - Implement node alignment options
  - Add cycle detection

- [ ] 5.3 Create Sankey layout CSS theme
  - Create `/src/arangodb/visualization/styles/sankey.css`
  - Flow path styling with gradients
  - Node rectangle styling
  - Label positioning
  - Tooltip styling for flows

- [ ] 5.4 Add Sankey-specific interactions
  - Hover to highlight flow paths
  - Click to isolate flow
  - Drag to reorder nodes
  - Flow filtering
  - Value-based sizing

- [ ] 5.5 Verify Sankey functionality
  - Generate flow data sample
  - Test path calculations
  - Verify flow conservation
  - Check cycle handling
  - Output flow metrics

- [ ] 5.6 Git commit Sankey layout

**Technical Specifications**:
- Use d3-sankey plugin
- Support circular flows
- Handle multiple flow types
- Optimize node positioning
- Support flow animations

**Verification Method**:
- Generate sankey_test.html
- Test with flow data
- Rich table with Sankey metrics:
  - Total flow: sum
  - Flow conservation: pass/fail
  - Cycle detection: count
  - Path overlap: minimal/significant

**Acceptance Criteria**:
- Flows render correctly
- Path widths match values
- Node positioning is optimal
- Interactions work smoothly

### Task 6: LLM Integration for Visualization ⏳ Not Started

**Implementation Steps**:
- [ ] 6.1 Create LLM recommendation module
  - Create `/src/arangodb/visualization/core/llm_recommender.py`
  - Implement LLMVisualizationRecommender class
  - Add Vertex AI client integration
  - Create prompt templates
  - Handle response parsing

- [ ] 6.2 Implement data sampling for LLM
  - Add sample_graph_data() method
  - Create statistical summary generation
  - Extract graph characteristics
  - Identify data patterns
  - Generate metadata summary

- [ ] 6.3 Design LLM prompt strategy
  - Create visualization selection prompt
  - Add customization recommendation prompt
  - Include color scheme suggestions
  - Add layout parameter tuning
  - Create focus node identification

- [ ] 6.4 Implement recommendation caching
  - Add Redis cache integration
  - Create cache key generation
  - Implement TTL strategy
  - Handle cache invalidation
  - Add fallback mechanisms

- [ ] 6.5 Verify LLM integration
  - Test with sample graph data
  - Verify recommendations
  - Check response times
  - Validate JSON parsing
  - Output recommendation table

- [ ] 6.6 Git commit LLM integration

**Technical Specifications**:
- Use Vertex AI Gemini Flash 2.5
- JSON response format
- 5-second timeout
- Cache for 1 hour
- Graceful fallback on errors

**Verification Method**:
- Test with various graph types
- Measure LLM response times
- Rich table with recommendations:
  - Query type: traverse/shortest_path
  - Recommended layout: force/tree/radial/sankey
  - Reasoning: LLM explanation
  - Custom settings: JSON

**Acceptance Criteria**:
- LLM provides valid recommendations
- Response time < 5 seconds
- Fallback works on errors
- Cache improves performance

### Task 7: FastAPI Server Implementation ⏳ Not Started

**Implementation Steps**:
- [ ] 7.1 Create FastAPI application
  - Create `/src/arangodb/api/visualization.py`
  - Set up FastAPI router
  - Add CORS configuration
  - Implement error handling
  - Add request validation

- [ ] 7.2 Implement visualization endpoints
  - Add GET /visualize/graph endpoint
  - Create POST /visualize/custom endpoint
  - Add GET /visualize/templates endpoint
  - Implement OPTIONS for CORS
  - Add health check endpoint

- [ ] 7.3 Add static file serving
  - Configure static file routes
  - Serve D3.js templates
  - Handle CSS files
  - Serve JavaScript modules
  - Add cache headers

- [ ] 7.4 Implement response caching
  - Add Redis cache layer
  - Create cache key strategy
  - Set appropriate TTLs
  - Handle cache warming
  - Add cache statistics endpoint

- [ ] 7.5 Verify API functionality
  - Test all endpoints
  - Verify CORS headers
  - Check response times
  - Test error scenarios
  - Output API metrics table

- [ ] 7.6 Git commit API server

**Technical Specifications**:
- FastAPI with uvicorn
- Redis for caching
- Pydantic for validation
- Async request handling
- OpenAPI documentation

**Verification Method**:
- Test API with curl/httpie
- Verify with Swagger UI
- Rich table with API metrics:
  - Endpoint: path
  - Method: GET/POST
  - Avg response time: ms
  - Cache hit rate: %

**Acceptance Criteria**:
- All endpoints respond correctly
- Caching improves performance
- CORS works for browser requests
- API documentation is complete

### Task 8: Integration with Existing CLI ⏳ Not Started

**Implementation Steps**:
- [ ] 8.1 Extend existing graph commands module
  - Modify `/src/arangodb/cli/graph_commands.py`
  - Add `visualize` command to existing graph_app
  - Import visualization engine modules
  - Integrate with existing output formatters
  - Follow established CLI patterns

- [ ] 8.2 Implement graph visualize command
  - Add `@graph_app.command("visualize")` decorator
  - Support `--output graph-html` option
  - Add `--layout` option (force/tree/radial/sankey)
  - Integrate with existing traverse command data
  - Support `--llm-recommend` flag
  
- [ ] 8.3 Extend existing output options
  - Modify output formatters to support HTML generation
  - Add `OutputFormat.GRAPH_HTML` enum value
  - Update format_output() to handle graph visualization
  - Ensure backward compatibility with existing outputs
  - Add progress indicators for generation

- [ ] 8.4 Enhance graph traverse command
  - Add `--output graph-html` option to traverse command
  - Generate visualization from traversal results
  - Support inline visualization in terminal (ASCII art fallback)
  - Add `--save-html` flag for file output
  - Integrate with existing result formats

- [ ] 8.5 Update main CLI integration
  - Update `/src/arangodb/cli/main.py` help text
  - Add visualization examples to quickstart
  - Update llm-help command with visualization options
  - Add health check for visualization dependencies
  - Document in CLI help system

- [ ] 8.6 Verify actual CLI functionality
  - **CRITICAL**: Must execute actual CLI commands, not unit tests
  - Test `python -m arangodb.cli visualize --help`
  - Test `python -m arangodb.cli visualize from-file test.json`
  - Test with both D3.js and ArangoDB format JSON files
  - Verify all layout types work: force, tree, radial, sankey
  - Test error conditions and edge cases
  - Create screenshots of actual CLI usage
  - Document exact command syntax and options

- [ ] 8.7 Test real data scenarios
  - Create test JSON files in both formats
  - Run CLI with real ArangoDB export data
  - Test with large graphs for performance
  - Verify file generation works correctly
  - Test --no-open-browser flag
  - Test custom output paths
  - Verify LLM integration with correct model names

- [ ] 8.8 Create CLI verification report
  - Create `/docs/reports/028_task_8_cli_testing.md`
  - Document all actual CLI commands executed
  - Include actual terminal output screenshots
  - Show generated HTML files working
  - Document any discovered issues
  - List exact model names being used
  - Include real error messages encountered

- [ ] 8.9 Git commit CLI integration

**CLI Testing Requirements** (MANDATORY):
- Execute ALL CLI commands with real data
- Test from-file with both D3.js and ArangoDB formats
- Test from-query with actual AQL queries  
- Test start-server and verify it runs
- Verify error handling with invalid inputs
- Document complete command outputs
- Include any error messages verbatim
- Test all parameter combinations
- Verify integration with LLM services
- Check data format conversions work correctly

**Example CLI Tests That Must Be Run**:
```bash
# Test 1: From file with D3.js format
arangodb visualization from-file test_data/d3_format.json

# Test 2: From file with ArangoDB format
arangodb visualization from-file test_data/arango_format.json

# Test 3: From query
arangodb visualization from-query "FOR v IN test_vertices RETURN v"

# Test 4: With custom output
arangodb visualization from-file data.json --output custom_output.html

# Test 5: Server start
arangodb visualization start-server --host 0.0.0.0 --port 8080

# Test 6: Error handling
arangodb visualization from-file nonexistent.json
```

**Technical Specifications**:
- Integrate with existing Typer structure
- Use established output formatter patterns
- Maintain CLI consistency across commands
- Support both file and stdout output
- Follow existing error handling patterns

**Verification Method**:
- Test integrated commands:
  - `arangodb graph traverse --output graph-html`
  - `arangodb graph visualize --layout force`
  - `arangodb graph visualize --llm-recommend`
- Verify backward compatibility
- Check help text updates

**Acceptance Criteria**:
- Visualization integrates seamlessly with existing CLI
- All existing commands continue to work
- Output options are consistent across commands
- Help documentation is updated

### Task 8b: CLI Command Implementation (Standalone) ⏳ Not Started

**Implementation Steps**:
- [ ] 8b.1 Create visualization CLI module (if needed)
  - Create `/src/arangodb/cli/visualization_commands.py`
  - Set up Typer app following existing patterns
  - Import from core visualization modules
  - Use existing formatters and utilities
  - Maintain CLI consistency

- [ ] 8b.2 Implement viz render command
  - Follow graph_commands.py patterns
  - Add command for standalone rendering
  - Support all output formats
  - Integration with graph queries
  - Use existing error handling

- [ ] 8b.3 Implement viz server command
  - Add server management functionality
  - Port configuration options
  - Background process management
  - Health check integration
  - Graceful shutdown handling

- [ ] 8b.4 Add to main CLI app
  - Import in `/src/arangodb/cli/main.py`
  - Add viz_app to main app
  - Update command listings
  - Add to help documentation
  - Update quickstart examples

- [ ] 8b.5 Verify standalone CLI
  - Test all viz commands
  - Check integration with main CLI
  - Verify help messages
  - Test error scenarios
  - Document usage patterns

- [ ] 8b.6 Git commit standalone CLI

**Technical Specifications**:
- Follow existing CLI patterns exactly
- Use same decorator patterns as other commands
- Consistent parameter naming
- Same output formatting approach
- Integrated error handling

**Verification Method**:
- Test standalone commands:
  - `arangodb viz render --help`
  - `arangodb viz server start`
  - `arangodb viz render --output graph.html`
- Verify main CLI integration
- Check consistency with other commands

**Acceptance Criteria**:
- Viz commands follow existing patterns
- Integration with main CLI is seamless
- Help and documentation are complete
- All commands work as expected

### Task 9: Performance Optimization ⏳ Not Started

**Implementation Steps**:
- [ ] 9.1 Implement WebGL rendering option
  - Research WebGL D3 renderers
  - Add WebGL detection
  - Implement fallback to SVG
  - Create performance comparison
  - Add renderer selection

- [ ] 9.2 Optimize large graph handling
  - Implement node clustering
  - Add level-of-detail rendering
  - Create viewport culling
  - Implement progressive loading
  - Add sampling strategies

- [ ] 9.3 Add graph simplification
  - Implement edge bundling
  - Add node aggregation
  - Create importance scoring
  - Implement filtering options
  - Add zoom-based detail

- [ ] 9.4 Optimize data structures
  - Use typed arrays where possible
  - Implement spatial indexing
  - Add quadtree optimization
  - Cache computed layouts
  - Optimize memory usage

- [ ] 9.5 Performance benchmarking
  - Create benchmark suite
  - Test with various graph sizes
  - Measure frame rates
  - Profile memory usage
  - Generate performance report

- [ ] 9.6 Git commit optimizations

**Technical Specifications**:
- Target 60 FPS for <1000 nodes
- Target 30 FPS for <5000 nodes
- Memory usage < 500MB
- Initial render < 2 seconds
- Interaction latency < 100ms

**Verification Method**:
- Run performance benchmarks
- Test with large graphs
- Rich table with metrics:
  - Graph size: nodes/edges
  - Render time: milliseconds
  - Frame rate: average FPS
  - Memory usage: MB

**Acceptance Criteria**:
- Meets performance targets
- Graceful degradation
- No memory leaks
- Smooth interactions

### Task 10: Documentation and Testing ⏳ Not Started

**Implementation Steps**:
- [ ] 10.1 Create user documentation
  - Write visualization guide
  - Document each layout type
  - Create interactive examples
  - Add troubleshooting section
  - Include performance tips

- [ ] 10.2 Create API documentation
  - Generate OpenAPI spec
  - Document all endpoints
  - Add request/response examples
  - Include error codes
  - Create integration guide

- [ ] 10.3 Implement unit tests
  - Test data transformers
  - Test layout generators
  - Test API endpoints
  - Test CLI commands
  - Achieve 80% coverage

- [ ] 10.4 Create integration tests
  - Test end-to-end workflows
  - Test with real ArangoDB data
  - Test LLM integration
  - Test caching behavior
  - Test error scenarios

- [ ] 10.5 Create visual regression tests
  - Set up screenshot comparison
  - Test each layout type
  - Verify styling consistency
  - Check responsive behavior
  - Document visual changes

- [ ] 10.6 Git commit documentation and tests

**Technical Specifications**:
- Use pytest for testing
- Use MkDocs for documentation
- Screenshot tests with Playwright
- Coverage reports with pytest-cov
- Automated test runs in CI

**Verification Method**:
- Run test suite
- Generate coverage report
- Build documentation
- Rich table with test results:
  - Test category: unit/integration/visual
  - Tests passed: count
  - Coverage: percentage
  - Documentation built: yes/no

**Acceptance Criteria**:
- All tests pass
- Coverage > 80%
- Documentation is complete
- Examples work correctly

## Usage Table

| Command / Function | Description | Example Usage | Expected Output |
|-------------------|-------------|---------------|-----------------|
| `graph traverse --output graph-html` | Traverse and visualize graph | `arangodb graph traverse doc123 --output graph-html --save-html graph.html` | Interactive D3.js graph saved to graph.html |
| `graph visualize` | Visualize existing graph data | `arangodb graph visualize --start-node doc123 --layout force --output graph.html` | Generated graph.html with force layout |
| `graph visualize --llm-recommend` | LLM-optimized visualization | `arangodb graph visualize --start-node doc123 --llm-recommend` | Auto-generated graph with best layout |
| `viz render` | Standalone visualization render | `arangodb viz render --query-result data.json --output graph.html` | Rendered visualization from JSON data |
| `viz server` | Start visualization server | `arangodb viz server start --port 8000` | Server running at http://localhost:8000 |
| `/visualize/graph` | API endpoint for graph viz | `GET /visualize/graph?start_node_id=123` | JSON with config and data |
| `D3VisualizationEngine` | Generate visualization | `engine.generate_visualization(data, 'force', config)` | HTML string with embedded D3.js |

## Version Control Plan

- **Initial Commit**: Create task-028-start tag before implementation
- **Module Commits**: After each major module (d3_engine, layouts, etc.)
- **Feature Commits**: After each visualization type is complete
- **Integration Commits**: After API and CLI integration
- **Final Tag**: Create task-028-complete after all tests pass
- **Rollback Strategy**: Use git tags to revert to last working state

## Resources

**D3.js Modules**:
- d3-force: Force-directed graph layouts
- d3-hierarchy: Tree and radial layouts  
- d3-sankey: Flow diagrams
- d3-selection: DOM manipulation
- d3-scale: Color and size scales

**Code Examples and Starting Points**:

### Force-Directed Graph Examples:
- **Official D3 Force Module**: https://github.com/d3/d3-force
  - Implements velocity Verlet numerical integrator for simulating physical forces
- **Classic Force-Directed Graph (Les Misérables)**: https://gist.github.com/mbostock/4062045
  - Character co-occurrence visualization by Mike Bostock
- **Force Dragging III**: https://gist.github.com/mbostock/ad70335eeef6d167bc36fd3c04378048
  - Demonstrates draggable nodes with d3-drag and d3-force
- **D3v4 Selectable, Draggable, Zoomable Force Graph**: https://gist.github.com/pkerpedjiev/f2e6ebb2532dae603de13f0606563f5b
  - Advanced example with selection, zoom, and drag features

Example force simulation setup:
```javascript
const simulation = d3.forceSimulation()
  .nodes(data.nodes)
  .force('link', d3.forceLink(data.links).id(d => d.id))
  .force('charge', d3.forceManyBody().strength(-300))
  .force('center', d3.forceCenter(width / 2, height / 2))
  .force('collide', d3.forceCollide().radius(30));
```

### Hierarchical Tree Examples:
- **Official D3 Hierarchy Module**: https://github.com/d3/d3-hierarchy
  - Provides tree layout algorithms including Reingold-Tilford
- **Collapsible Tree (D3 v7)**: https://gist.github.com/d3noob/918a64abe4c3682cac3b4c3c852a698d
  - Interactive collapsible tree for latest D3 version
- **Complete Tree Demo**: https://github.com/kyhau/d3-collapsible-tree-demo
  - Full repository with working example
- **Observable Example**: https://observablehq.com/@d3/collapsible-tree
  - Interactive example with click-to-collapse functionality

### Radial Tree Examples:
- **Radial Tidy Tree**: https://gist.github.com/mbostock/4063550
  - Mike Bostock's radial tree implementation
- **Collapsible Radial Tree**: https://gist.github.com/HermanSontrop/8228664
  - Interactive radial tree with collapse/expand
- **D3-Radial-Tree Repository**: https://github.com/jerisalan/d3-radial-tree
  - Complete collapsible/expandable radial tree

### Sankey Diagram Examples:
- **Official D3 Sankey**: https://github.com/d3/d3-sankey
  - Visualize flow between nodes in directed acyclic network
- **Sankey with D3 v7**: https://gist.github.com/d3noob/31665aced416f27abca4fa46f5f4b568
  - Simple Sankey implementation for latest D3
- **SKD3 - Extended Sankey**: https://github.com/fabric-io-rodrigues/skd3
  - Enhanced D3 sankey with additional features

Sankey data format:
```javascript
const data = {
  nodes: [
    { node: 0, name: "node0" },
    { node: 1, name: "node1" }
  ],
  links: [
    { source: 0, target: 1, value: 2 }
  ]
}
```

**Related Documentation**:
- [D3.js v7 Documentation](https://d3js.org/d3-hierarchy/tree)
- [D3 Graph Gallery](https://d3-graph-gallery.com/)
- [Vertex AI Gemini Docs](https://cloud.google.com/vertex-ai/docs)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)

**Styling Resources**:
- Modern D3.js themes research
- CSS Grid for responsive layouts
- SVG optimization techniques
- WebGL rendering options

## Progress Tracking

- Start date: TBD
- Current phase: Planning
- Expected completion: TBD
- Completion criteria: All layouts working, LLM integrated, API/CLI functional

## Context Management

When context length is running low during implementation, use the following approach to compact and resume work:

1. Issue the `/compact` command to create a concise summary of current progress
2. The summary will include:
   - Completed tasks and key functionality
   - Current task in progress
   - Known issues or blockers
   - Next steps to resume work

### Example Compact Summary Format:
```
COMPACT SUMMARY - Task 028: D3 Graph Visualization
Completed: 
- Task 1: D3.js infrastructure ✅
- Task 2: Force layout ✅ 
- Task 3: Tree layout (partial - 3.1-3.3 done)
In Progress: Task 3.4 - Tree interactions
Pending: Tasks 4-10 (radial, sankey, LLM, API, CLI, optimization, docs)
Issues: None currently
Next steps: Complete tree interactions, test, then start radial layout
```

---

This task document serves as the comprehensive implementation guide for the D3 graph visualization feature. Update status emojis and checkboxes as tasks are completed to maintain progress tracking.