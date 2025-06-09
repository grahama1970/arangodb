# Responsive D3 Graph Design Specification

## Current Problems
- Fixed viewport dimensions (100vw/100vh)
- Desktop-only controls UI
- No mobile touch gestures
- Fixed font sizes
- No responsive breakpoints
- Controls panel overlaps on small screens

## Responsive Requirements

### 1. **Breakpoint Strategy**
```css
/* Mobile: 320px - 768px */
@media (max-width: 768px) {
  .controls { bottom: 10px; right: 10px; width: 100%; }
  .node-label { font-size: clamp(10px, 2.5vw, 14px); }
  .legend { display: none; } /* Hide on mobile */
}

/* Tablet: 768px - 1024px */
@media (min-width: 768px) and (max-width: 1024px) {
  .controls { right: 20px; width: auto; }
  .node-label { font-size: clamp(12px, 1.5vw, 16px); }
}

/* Desktop: 1024px+ */
@media (min-width: 1024px) {
  .controls { right: 20px; width: 250px; }
  .node-label { font-size: 14px; }
}
```

### 2. **Dynamic Sizing Strategy**
```javascript
// Responsive dimension calculation
function getResponsiveDimensions(containerElement) {
  const rect = containerElement.getBoundingClientRect();
  const isMobile = window.innerWidth <= 768;
  const isTablet = window.innerWidth <= 1024;
  
  return {
    width: rect.width,
    height: isMobile ? window.innerHeight * 0.6 : rect.height,
    nodeRadius: isMobile ? 4 : isTablet ? 6 : 8,
    fontSize: isMobile ? 10 : isTablet ? 12 : 14,
    linkDistance: isMobile ? 40 : isTablet ? 60 : 80,
    controlsPosition: isMobile ? 'bottom' : 'top-right'
  };
}
```

### 3. **Touch Gesture Support**
```javascript
// Mobile touch gestures
function addTouchSupport(svg, simulation) {
  // Pinch to zoom
  svg.call(d3.zoom()
    .scaleExtent([0.1, 10])
    .on("zoom", handleZoom));
  
  // Touch drag for nodes
  node.call(d3.drag()
    .on("start", dragstarted)
    .on("drag", dragged)
    .on("end", dragended)
    .touchable(true)); // Enable touch
  
  // Double tap to reset
  svg.on("dblclick.zoom", function() {
    svg.transition().duration(750)
       .call(zoom.transform, d3.zoomIdentity);
  });
}
```

### 4. **Adaptive UI Controls**
```javascript
// Mobile-first controls
function createResponsiveControls(container) {
  const isMobile = window.innerWidth <= 768;
  
  if (isMobile) {
    // Collapsible bottom drawer
    return `
      <div class="mobile-controls">
        <button class="controls-toggle">⚙️</button>
        <div class="controls-drawer">
          <div class="control-row">
            <label>Physics</label>
            <button class="toggle-physics">⏸️</button>
          </div>
          <div class="control-row">
            <label>Labels</label>
            <button class="toggle-labels">👁️</button>
          </div>
        </div>
      </div>
    `;
  } else {
    // Desktop sidebar controls
    return createDesktopControls();
  }
}
```

## Complete Responsive Template

### CSS Framework
```css
/* Base responsive graph container */
.graph-container {
  width: 100%;
  height: 100%;
  position: relative;
  overflow: hidden;
  min-height: 300px; /* Minimum usable height */
}

/* Responsive SVG */
.graph-svg {
  width: 100%;
  height: 100%;
  display: block;
}

/* Fluid node labels */
.node-label {
  font-size: clamp(8px, 2vw, 14px);
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  pointer-events: none;
  user-select: none;
}

/* Responsive controls */
.controls {
  position: absolute;
  background: rgba(255, 255, 255, 0.95);
  border-radius: 8px;
  box-shadow: 0 2px 12px rgba(0,0,0,0.15);
  backdrop-filter: blur(10px);
  z-index: 100;
}

/* Mobile controls (bottom drawer) */
@media (max-width: 768px) {
  .controls {
    bottom: 0;
    left: 0;
    right: 0;
    border-radius: 12px 12px 0 0;
    max-height: 40vh;
    transform: translateY(calc(100% - 60px));
    transition: transform 0.3s ease;
  }
  
  .controls.expanded {
    transform: translateY(0);
  }
  
  .controls-toggle {
    position: absolute;
    top: -40px;
    left: 50%;
    transform: translateX(-50%);
    background: rgba(255, 255, 255, 0.9);
    border: none;
    border-radius: 20px;
    width: 40px;
    height: 40px;
    font-size: 18px;
  }
  
  .legend {
    display: none; /* Hide legend on mobile */
  }
  
  .tooltip {
    font-size: 12px;
    max-width: 250px;
  }
}

/* Tablet controls */
@media (min-width: 768px) and (max-width: 1024px) {
  .controls {
    top: 20px;
    right: 20px;
    width: 200px;
    padding: 12px;
  }
  
  .legend {
    bottom: 20px;
    left: 20px;
    max-width: 200px;
  }
}

/* Desktop controls */
@media (min-width: 1024px) {
  .controls {
    top: 20px;
    right: 20px;
    width: 250px;
    padding: 15px;
  }
  
  .legend {
    bottom: 20px;
    left: 20px;
    max-width: 250px;
  }
}

/* Touch-friendly buttons */
.control-btn {
  min-height: 44px; /* iOS minimum touch target */
  min-width: 44px;
  padding: 8px 16px;
  border: 1px solid #dee2e6;
  background: white;
  border-radius: 6px;
  cursor: pointer;
  font-size: clamp(12px, 1.5vw, 14px);
  transition: all 0.2s;
}

@media (hover: hover) {
  .control-btn:hover {
    background-color: #f8f9fa;
    border-color: #adb5bd;
  }
}

/* Responsive node sizes */
.nodes circle {
  r: clamp(3, 1vw, 8);
  stroke: #fff;
  stroke-width: clamp(1, 0.3vw, 2);
  cursor: pointer;
}

/* Responsive link widths */
.links line {
  stroke: #999;
  stroke-opacity: 0.6;
  stroke-width: clamp(1, 0.2vw, 3);
}
```

### JavaScript Framework
```javascript
class ResponsiveD3Graph {
  constructor(container, data, options = {}) {
    this.container = container;
    this.data = data;
    this.options = options;
    this.dimensions = this.calculateDimensions();
    
    // Responsive breakpoints
    this.breakpoints = {
      mobile: 768,
      tablet: 1024
    };
    
    this.init();
    this.addResizeListener();
  }
  
  calculateDimensions() {
    const rect = this.container.getBoundingClientRect();
    const width = rect.width || window.innerWidth;
    const height = rect.height || window.innerHeight;
    const isMobile = window.innerWidth <= this.breakpoints.mobile;
    const isTablet = window.innerWidth <= this.breakpoints.tablet;
    
    return {
      width,
      height: isMobile ? Math.min(height, window.innerHeight * 0.7) : height,
      nodeRadius: isMobile ? 4 : isTablet ? 6 : 8,
      fontSize: isMobile ? 10 : isTablet ? 12 : 14,
      linkDistance: isMobile ? 30 : isTablet ? 50 : 80,
      chargeStrength: isMobile ? -100 : isTablet ? -150 : -200,
      isMobile,
      isTablet
    };
  }
  
  init() {
    // Create responsive SVG
    this.svg = d3.select(this.container)
      .append("svg")
      .attr("viewBox", `0 0 ${this.dimensions.width} ${this.dimensions.height}`)
      .attr("preserveAspectRatio", "xMidYMid meet")
      .classed("graph-svg", true);
    
    // Add responsive zoom
    this.addZoomBehavior();
    
    // Create force simulation with responsive parameters
    this.createSimulation();
    
    // Render graph elements
    this.render();
    
    // Add responsive controls
    this.addControls();
  }
  
  addZoomBehavior() {
    const { isMobile } = this.dimensions;
    
    this.zoom = d3.zoom()
      .scaleExtent([0.1, 10])
      .on("zoom", (event) => {
        this.g.attr("transform", event.transform);
      });
    
    this.svg.call(this.zoom);
    
    // Add touch-friendly reset
    if (isMobile) {
      this.svg.on("dblclick.zoom", () => {
        this.svg.transition().duration(750)
           .call(this.zoom.transform, d3.zoomIdentity);
      });
    }
  }
  
  createSimulation() {
    const { width, height, linkDistance, chargeStrength, nodeRadius } = this.dimensions;
    
    this.simulation = d3.forceSimulation()
      .force("link", d3.forceLink()
        .id(d => d.id)
        .distance(linkDistance))
      .force("charge", d3.forceManyBody()
        .strength(chargeStrength))
      .force("center", d3.forceCenter(width / 2, height / 2))
      .force("collision", d3.forceCollide().radius(nodeRadius * 1.5));
  }
  
  addResizeListener() {
    let resizeTimer;
    window.addEventListener("resize", () => {
      clearTimeout(resizeTimer);
      resizeTimer = setTimeout(() => {
        this.handleResize();
      }, 250); // Debounce resize
    });
  }
  
  handleResize() {
    // Recalculate dimensions
    this.dimensions = this.calculateDimensions();
    
    // Update SVG viewBox
    this.svg.attr("viewBox", `0 0 ${this.dimensions.width} ${this.dimensions.height}`);
    
    // Update force simulation
    this.simulation
      .force("center", d3.forceCenter(this.dimensions.width / 2, this.dimensions.height / 2))
      .force("link").distance(this.dimensions.linkDistance)
      .force("charge").strength(this.dimensions.chargeStrength)
      .alpha(0.3).restart();
    
    // Update controls layout
    this.updateControlsLayout();
  }
  
  addControls() {
    const { isMobile } = this.dimensions;
    
    if (isMobile) {
      this.addMobileControls();
    } else {
      this.addDesktopControls();
    }
  }
  
  addMobileControls() {
    // Bottom drawer implementation
    const controlsHtml = `
      <div class="controls">
        <button class="controls-toggle">⚙️</button>
        <div class="controls-content">
          <div class="control-grid">
            <button class="control-btn" data-action="toggle-physics">⏸️ Physics</button>
            <button class="control-btn" data-action="toggle-labels">👁️ Labels</button>
            <button class="control-btn" data-action="reset-zoom">🎯 Reset</button>
            <button class="control-btn" data-action="center-graph">📍 Center</button>
          </div>
        </div>
      </div>
    `;
    
    this.container.insertAdjacentHTML('beforeend', controlsHtml);
    this.bindControlEvents();
  }
}

// Usage
const responsiveGraph = new ResponsiveD3Graph(
  document.getElementById('graph-container'),
  graphData,
  { layout: 'force' }
);
```

## Chat Integration Responsive Component
```jsx
// ResponsiveGraphMessage.jsx
import React, { useEffect, useRef, useState } from 'react';

const ResponsiveGraphMessage = ({ graphData, title, layout = "force" }) => {
  const containerRef = useRef();
  const [dimensions, setDimensions] = useState({ width: 0, height: 0 });
  
  useEffect(() => {
    const updateDimensions = () => {
      if (containerRef.current) {
        const rect = containerRef.current.getBoundingClientRect();
        setDimensions({
          width: rect.width,
          height: Math.min(400, window.innerHeight * 0.5)
        });
      }
    };
    
    updateDimensions();
    window.addEventListener('resize', updateDimensions);
    return () => window.removeEventListener('resize', updateDimensions);
  }, []);
  
  useEffect(() => {
    if (dimensions.width > 0) {
      const graph = new ResponsiveD3Graph(
        containerRef.current,
        graphData,
        { layout, responsive: true }
      );
    }
  }, [graphData, dimensions, layout]);
  
  return (
    <div className="graph-message">
      <h3 className="graph-title">{title}</h3>
      <div 
        ref={containerRef} 
        className="graph-container"
        style={{ 
          width: '100%', 
          height: `${dimensions.height}px`,
          minHeight: '300px'
        }}
      />
    </div>
  );
};
```

## Key Benefits
- ✅ **Universal compatibility**: Works on all devices
- ✅ **Touch-optimized**: Pinch, zoom, drag gestures
- ✅ **Adaptive UI**: Controls adjust to screen size
- ✅ **Scalable text**: Font sizes respond to viewport
- ✅ **Performance**: Debounced resize handling
- ✅ **Chat integration**: Works in message bubbles
- ✅ **Accessible**: Meets touch target requirements