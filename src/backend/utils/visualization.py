"""
Visualization utility for generating charts and graphs for reports.
Supports matplotlib and plotly for various chart types.
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
from datetime import datetime
import base64
from io import BytesIO

import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # Use non-GUI backend
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

from config import settings

logger = logging.getLogger(__name__)


class ChartGenerator:
    """Generator for various types of charts and visualizations."""
    
    def __init__(self, output_dir: Optional[Path] = None):
        """
        Initialize chart generator.
        
        Args:
            output_dir: Directory to save generated charts
        """
        self.output_dir = output_dir or Path(settings.reports_dir) / "charts"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Set matplotlib style
        plt.style.use('seaborn-v0_8-darkgrid')
        
        logger.info("Chart Generator initialized")
    
    def create_line_chart(
        self,
        data: Dict[str, List],
        title: str,
        x_label: str,
        y_label: str,
        chart_id: Optional[str] = None,
        use_plotly: bool = True
    ) -> Dict[str, Any]:
        """
        Create a line chart.
        
        Args:
            data: Dictionary with 'x' and 'y' keys containing data lists
            title: Chart title
            x_label: X-axis label
            y_label: Y-axis label
            chart_id: Optional chart identifier
            use_plotly: Use plotly (True) or matplotlib (False)
            
        Returns:
            Dictionary with chart filepath and metadata
        """
        try:
            chart_id = chart_id or f"line_chart_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            if use_plotly:
                return self._create_plotly_line_chart(data, title, x_label, y_label, chart_id)
            else:
                return self._create_matplotlib_line_chart(data, title, x_label, y_label, chart_id)
                
        except Exception as e:
            logger.error(f"Error creating line chart: {e}")
            raise
    
    def create_bar_chart(
        self,
        data: Dict[str, List],
        title: str,
        x_label: str,
        y_label: str,
        chart_id: Optional[str] = None,
        use_plotly: bool = True
    ) -> Dict[str, Any]:
        """
        Create a bar chart.
        
        Args:
            data: Dictionary with 'x' and 'y' keys containing data lists
            title: Chart title
            x_label: X-axis label
            y_label: Y-axis label
            chart_id: Optional chart identifier
            use_plotly: Use plotly (True) or matplotlib (False)
            
        Returns:
            Dictionary with chart filepath and metadata
        """
        try:
            chart_id = chart_id or f"bar_chart_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            if use_plotly:
                return self._create_plotly_bar_chart(data, title, x_label, y_label, chart_id)
            else:
                return self._create_matplotlib_bar_chart(data, title, x_label, y_label, chart_id)
                
        except Exception as e:
            logger.error(f"Error creating bar chart: {e}")
            raise
    
    def create_pie_chart(
        self,
        data: Dict[str, List],
        title: str,
        chart_id: Optional[str] = None,
        use_plotly: bool = True
    ) -> Dict[str, Any]:
        """
        Create a pie chart.
        
        Args:
            data: Dictionary with 'labels' and 'values' keys
            title: Chart title
            chart_id: Optional chart identifier
            use_plotly: Use plotly (True) or matplotlib (False)
            
        Returns:
            Dictionary with chart filepath and metadata
        """
        try:
            chart_id = chart_id or f"pie_chart_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            if use_plotly:
                return self._create_plotly_pie_chart(data, title, chart_id)
            else:
                return self._create_matplotlib_pie_chart(data, title, chart_id)
                
        except Exception as e:
            logger.error(f"Error creating pie chart: {e}")
            raise
    
    def create_scatter_plot(
        self,
        data: Dict[str, List],
        title: str,
        x_label: str,
        y_label: str,
        chart_id: Optional[str] = None,
        use_plotly: bool = True
    ) -> Dict[str, Any]:
        """
        Create a scatter plot.
        
        Args:
            data: Dictionary with 'x' and 'y' keys containing data lists
            title: Chart title
            x_label: X-axis label
            y_label: Y-label
            chart_id: Optional chart identifier
            use_plotly: Use plotly (True) or matplotlib (False)
            
        Returns:
            Dictionary with chart filepath and metadata
        """
        try:
            chart_id = chart_id or f"scatter_plot_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            if use_plotly:
                return self._create_plotly_scatter(data, title, x_label, y_label, chart_id)
            else:
                return self._create_matplotlib_scatter(data, title, x_label, y_label, chart_id)
                
        except Exception as e:
            logger.error(f"Error creating scatter plot: {e}")
            raise
    
    # Plotly implementations
    def _create_plotly_line_chart(
        self,
        data: Dict[str, List],
        title: str,
        x_label: str,
        y_label: str,
        chart_id: str
    ) -> Dict[str, Any]:
        """Create line chart using plotly."""
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=data['x'],
            y=data['y'],
            mode='lines+markers',
            name=y_label
        ))
        
        fig.update_layout(
            title=title,
            xaxis_title=x_label,
            yaxis_title=y_label,
            template='plotly_white'
        )
        
        return self._save_plotly_chart(fig, chart_id, 'line_chart')
    
    def _create_plotly_bar_chart(
        self,
        data: Dict[str, List],
        title: str,
        x_label: str,
        y_label: str,
        chart_id: str
    ) -> Dict[str, Any]:
        """Create bar chart using plotly."""
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            x=data['x'],
            y=data['y'],
            name=y_label
        ))
        
        fig.update_layout(
            title=title,
            xaxis_title=x_label,
            yaxis_title=y_label,
            template='plotly_white'
        )
        
        return self._save_plotly_chart(fig, chart_id, 'bar_chart')
    
    def _create_plotly_pie_chart(
        self,
        data: Dict[str, List],
        title: str,
        chart_id: str
    ) -> Dict[str, Any]:
        """Create pie chart using plotly."""
        fig = go.Figure()
        
        fig.add_trace(go.Pie(
            labels=data['labels'],
            values=data['values']
        ))
        
        fig.update_layout(
            title=title,
            template='plotly_white'
        )
        
        return self._save_plotly_chart(fig, chart_id, 'pie_chart')
    
    def _create_plotly_scatter(
        self,
        data: Dict[str, List],
        title: str,
        x_label: str,
        y_label: str,
        chart_id: str
    ) -> Dict[str, Any]:
        """Create scatter plot using plotly."""
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=data['x'],
            y=data['y'],
            mode='markers',
            name='Data Points'
        ))
        
        fig.update_layout(
            title=title,
            xaxis_title=x_label,
            yaxis_title=y_label,
            template='plotly_white'
        )
        
        return self._save_plotly_chart(fig, chart_id, 'scatter_plot')
    
    def _save_plotly_chart(
        self,
        fig: go.Figure,
        chart_id: str,
        chart_type: str
    ) -> Dict[str, Any]:
        """Save plotly chart to file."""
        # Save as HTML
        html_path = self.output_dir / f"{chart_id}.html"
        fig.write_html(str(html_path))
        
        # Save as PNG (requires kaleido)
        try:
            png_path = self.output_dir / f"{chart_id}.png"
            fig.write_image(str(png_path))
            has_png = True
        except Exception as e:
            logger.warning(f"Could not save PNG: {e}")
            png_path = None
            has_png = False
        
        logger.info(f"Plotly chart saved: {chart_id}")
        
        return {
            "chart_id": chart_id,
            "chart_type": chart_type,
            "html_path": str(html_path),
            "png_path": str(png_path) if has_png else None,
            "created_at": datetime.now().isoformat()
        }
    
    # Matplotlib implementations
    def _create_matplotlib_line_chart(
        self,
        data: Dict[str, List],
        title: str,
        x_label: str,
        y_label: str,
        chart_id: str
    ) -> Dict[str, Any]:
        """Create line chart using matplotlib."""
        fig, ax = plt.subplots(figsize=(10, 6))
        
        ax.plot(data['x'], data['y'], marker='o', linewidth=2)
        ax.set_title(title, fontsize=14, fontweight='bold')
        ax.set_xlabel(x_label, fontsize=12)
        ax.set_ylabel(y_label, fontsize=12)
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        return self._save_matplotlib_chart(fig, chart_id, 'line_chart')
    
    def _create_matplotlib_bar_chart(
        self,
        data: Dict[str, List],
        title: str,
        x_label: str,
        y_label: str,
        chart_id: str
    ) -> Dict[str, Any]:
        """Create bar chart using matplotlib."""
        fig, ax = plt.subplots(figsize=(10, 6))
        
        ax.bar(data['x'], data['y'])
        ax.set_title(title, fontsize=14, fontweight='bold')
        ax.set_xlabel(x_label, fontsize=12)
        ax.set_ylabel(y_label, fontsize=12)
        ax.grid(True, alpha=0.3, axis='y')
        
        plt.tight_layout()
        
        return self._save_matplotlib_chart(fig, chart_id, 'bar_chart')
    
    def _create_matplotlib_pie_chart(
        self,
        data: Dict[str, List],
        title: str,
        chart_id: str
    ) -> Dict[str, Any]:
        """Create pie chart using matplotlib."""
        fig, ax = plt.subplots(figsize=(10, 8))
        
        ax.pie(data['values'], labels=data['labels'], autopct='%1.1f%%', startangle=90)
        ax.set_title(title, fontsize=14, fontweight='bold')
        
        plt.tight_layout()
        
        return self._save_matplotlib_chart(fig, chart_id, 'pie_chart')
    
    def _create_matplotlib_scatter(
        self,
        data: Dict[str, List],
        title: str,
        x_label: str,
        y_label: str,
        chart_id: str
    ) -> Dict[str, Any]:
        """Create scatter plot using matplotlib."""
        fig, ax = plt.subplots(figsize=(10, 6))
        
        ax.scatter(data['x'], data['y'], alpha=0.6)
        ax.set_title(title, fontsize=14, fontweight='bold')
        ax.set_xlabel(x_label, fontsize=12)
        ax.set_ylabel(y_label, fontsize=12)
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        return self._save_matplotlib_chart(fig, chart_id, 'scatter_plot')
    
    def _save_matplotlib_chart(
        self,
        fig: plt.Figure,
        chart_id: str,
        chart_type: str
    ) -> Dict[str, Any]:
        """Save matplotlib chart to file."""
        # Save as PNG
        png_path = self.output_dir / f"{chart_id}.png"
        fig.savefig(str(png_path), dpi=300, bbox_inches='tight')
        plt.close(fig)
        
        logger.info(f"Matplotlib chart saved: {chart_id}")
        
        return {
            "chart_id": chart_id,
            "chart_type": chart_type,
            "png_path": str(png_path),
            "created_at": datetime.now().isoformat()
        }


def create_chart_generator(output_dir: Optional[Path] = None) -> ChartGenerator:
    """
    Factory function to create a chart generator.
    
    Args:
        output_dir: Optional output directory
        
    Returns:
        ChartGenerator instance
    """
    return ChartGenerator(output_dir=output_dir)

