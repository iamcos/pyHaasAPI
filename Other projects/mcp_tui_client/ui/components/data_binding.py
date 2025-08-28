"""
Data Binding System

Real-time data binding system for automatic UI updates.
"""

from typing import Any, Dict, List, Optional, Callable, Union, Set
from datetime import datetime
from abc import ABC, abstractmethod
from enum import Enum
import asyncio
import weakref

from textual.widget import Widget
from textual.reactive import reactive


class BindingType(Enum):
    """Types of data bindings"""
    ONE_WAY = "one_way"          # Data source -> UI
    TWO_WAY = "two_way"          # Data source <-> UI
    ONE_TIME = "one_time"        # Single update only


class DataChangeEvent:
    """Event representing a data change"""
    
    def __init__(
        self,
        source_id: str,
        property_name: str,
        old_value: Any,
        new_value: Any,
        timestamp: datetime = None
    ):
        self.source_id = source_id
        self.property_name = property_name
        self.old_value = old_value
        self.new_value = new_value
        self.timestamp = timestamp or datetime.now()


class RealTimeDataSource(ABC):
    """Abstract base class for real-time data sources"""
    
    def __init__(self, source_id: str):
        self.source_id = source_id
        self.subscribers: Set[Callable[[DataChangeEvent], None]] = set()
        self.data: Dict[str, Any] = {}
        self.last_update = datetime.now()
    
    def subscribe(self, callback: Callable[[DataChangeEvent], None]) -> None:
        """Subscribe to data changes"""
        self.subscribers.add(callback)
    
    def unsubscribe(self, callback: Callable[[DataChangeEvent], None]) -> None:
        """Unsubscribe from data changes"""
        self.subscribers.discard(callback)
    
    def notify_change(self, property_name: str, old_value: Any, new_value: Any) -> None:
        """Notify subscribers of data change"""
        event = DataChangeEvent(self.source_id, property_name, old_value, new_value)
        for callback in self.subscribers.copy():  # Copy to avoid modification during iteration
            try:
                callback(event)
            except Exception as e:
                # Log error but don't break other subscribers
                print(f"Error in data binding callback: {e}")
    
    def set_data(self, property_name: str, value: Any) -> None:
        """Set data property and notify subscribers"""
        old_value = self.data.get(property_name)
        if old_value != value:
            self.data[property_name] = value
            self.last_update = datetime.now()
            self.notify_change(property_name, old_value, value)
    
    def get_data(self, property_name: str, default: Any = None) -> Any:
        """Get data property"""
        return self.data.get(property_name, default)
    
    def update_data(self, data_dict: Dict[str, Any]) -> None:
        """Update multiple data properties"""
        for property_name, value in data_dict.items():
            self.set_data(property_name, value)
    
    @abstractmethod
    async def start_updates(self) -> None:
        """Start real-time updates (to be implemented by subclasses)"""
        pass
    
    @abstractmethod
    async def stop_updates(self) -> None:
        """Stop real-time updates (to be implemented by subclasses)"""
        pass


class DataBinding:
    """Represents a data binding between a data source and UI widget"""
    
    def __init__(
        self,
        binding_id: str,
        data_source: RealTimeDataSource,
        widget: Widget,
        source_property: str,
        widget_property: str,
        binding_type: BindingType = BindingType.ONE_WAY,
        converter: Callable[[Any], Any] = None,
        validator: Callable[[Any], bool] = None
    ):
        self.binding_id = binding_id
        self.data_source = data_source
        self.widget_ref = weakref.ref(widget)  # Use weak reference to avoid memory leaks
        self.source_property = source_property
        self.widget_property = widget_property
        self.binding_type = binding_type
        self.converter = converter or (lambda x: x)
        self.validator = validator or (lambda x: True)
        self.is_active = False
        self.last_sync = datetime.now()
    
    def activate(self) -> None:
        """Activate the data binding"""
        if self.is_active:
            return
        
        self.is_active = True
        
        # Subscribe to data source changes
        self.data_source.subscribe(self._on_data_change)
        
        # Initial sync from data source to widget
        self._sync_to_widget()
        
        # For two-way binding, also listen to widget changes
        if self.binding_type == BindingType.TWO_WAY:
            self._setup_widget_listener()
    
    def deactivate(self) -> None:
        """Deactivate the data binding"""
        if not self.is_active:
            return
        
        self.is_active = False
        self.data_source.unsubscribe(self._on_data_change)
    
    def _on_data_change(self, event: DataChangeEvent) -> None:
        """Handle data source changes"""
        if not self.is_active or event.property_name != self.source_property:
            return
        
        self._sync_to_widget()
    
    def _sync_to_widget(self) -> None:
        """Sync data from source to widget"""
        widget = self.widget_ref()
        if not widget:
            # Widget has been garbage collected, deactivate binding
            self.deactivate()
            return
        
        try:
            source_value = self.data_source.get_data(self.source_property)
            if source_value is not None and self.validator(source_value):
                converted_value = self.converter(source_value)
                self._set_widget_property(widget, converted_value)
                self.last_sync = datetime.now()
        except Exception as e:
            print(f"Error syncing data to widget: {e}")
    
    def _sync_to_source(self, widget_value: Any) -> None:
        """Sync data from widget to source (for two-way binding)"""
        if not self.is_active or self.binding_type != BindingType.TWO_WAY:
            return
        
        try:
            if self.validator(widget_value):
                converted_value = self.converter(widget_value)
                self.data_source.set_data(self.source_property, converted_value)
        except Exception as e:
            print(f"Error syncing data to source: {e}")
    
    def _set_widget_property(self, widget: Widget, value: Any) -> None:
        """Set widget property value"""
        if hasattr(widget, self.widget_property):
            setattr(widget, self.widget_property, value)
        elif hasattr(widget, 'update') and self.widget_property == 'content':
            widget.update(str(value))
    
    def _setup_widget_listener(self) -> None:
        """Set up widget change listener for two-way binding"""
        widget = self.widget_ref()
        if not widget:
            return
        
        # This is a simplified implementation
        # In practice, you'd need to hook into widget-specific change events
        # For now, we'll use a polling approach for demonstration
        pass


class BindableWidget(Widget):
    """Base class for widgets that support data binding"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.bindings: Dict[str, DataBinding] = {}
        self.binding_manager: Optional['DataBindingManager'] = None
    
    def bind_data(
        self,
        binding_id: str,
        data_source: RealTimeDataSource,
        source_property: str,
        widget_property: str = "content",
        binding_type: BindingType = BindingType.ONE_WAY,
        converter: Callable[[Any], Any] = None,
        validator: Callable[[Any], bool] = None
    ) -> DataBinding:
        """Create a data binding for this widget"""
        binding = DataBinding(
            binding_id=binding_id,
            data_source=data_source,
            widget=self,
            source_property=source_property,
            widget_property=widget_property,
            binding_type=binding_type,
            converter=converter,
            validator=validator
        )
        
        self.bindings[binding_id] = binding
        binding.activate()
        
        return binding
    
    def unbind_data(self, binding_id: str) -> None:
        """Remove a data binding"""
        if binding_id in self.bindings:
            self.bindings[binding_id].deactivate()
            del self.bindings[binding_id]
    
    def unbind_all(self) -> None:
        """Remove all data bindings"""
        for binding in self.bindings.values():
            binding.deactivate()
        self.bindings.clear()
    
    def on_unmount(self) -> None:
        """Clean up bindings when widget is unmounted"""
        self.unbind_all()
        super().on_unmount()


class DataBindingManager:
    """Manages data bindings across the application"""
    
    def __init__(self):
        self.data_sources: Dict[str, RealTimeDataSource] = {}
        self.bindings: Dict[str, DataBinding] = {}
        self.active_sources: Set[str] = set()
    
    def register_data_source(self, data_source: RealTimeDataSource) -> None:
        """Register a data source"""
        self.data_sources[data_source.source_id] = data_source
    
    def unregister_data_source(self, source_id: str) -> None:
        """Unregister a data source"""
        if source_id in self.data_sources:
            # Deactivate all bindings using this source
            bindings_to_remove = [
                binding_id for binding_id, binding in self.bindings.items()
                if binding.data_source.source_id == source_id
            ]
            
            for binding_id in bindings_to_remove:
                self.remove_binding(binding_id)
            
            # Stop the data source
            if source_id in self.active_sources:
                asyncio.create_task(self.data_sources[source_id].stop_updates())
                self.active_sources.discard(source_id)
            
            del self.data_sources[source_id]
    
    def create_binding(
        self,
        binding_id: str,
        source_id: str,
        widget: Widget,
        source_property: str,
        widget_property: str = "content",
        binding_type: BindingType = BindingType.ONE_WAY,
        converter: Callable[[Any], Any] = None,
        validator: Callable[[Any], bool] = None
    ) -> Optional[DataBinding]:
        """Create a new data binding"""
        if source_id not in self.data_sources:
            print(f"Data source '{source_id}' not found")
            return None
        
        data_source = self.data_sources[source_id]
        binding = DataBinding(
            binding_id=binding_id,
            data_source=data_source,
            widget=widget,
            source_property=source_property,
            widget_property=widget_property,
            binding_type=binding_type,
            converter=converter,
            validator=validator
        )
        
        self.bindings[binding_id] = binding
        binding.activate()
        
        # Start data source if not already active
        if source_id not in self.active_sources:
            asyncio.create_task(data_source.start_updates())
            self.active_sources.add(source_id)
        
        return binding
    
    def remove_binding(self, binding_id: str) -> None:
        """Remove a data binding"""
        if binding_id in self.bindings:
            self.bindings[binding_id].deactivate()
            del self.bindings[binding_id]
    
    def get_binding(self, binding_id: str) -> Optional[DataBinding]:
        """Get a data binding by ID"""
        return self.bindings.get(binding_id)
    
    def get_data_source(self, source_id: str) -> Optional[RealTimeDataSource]:
        """Get a data source by ID"""
        return self.data_sources.get(source_id)
    
    async def start_all_sources(self) -> None:
        """Start all registered data sources"""
        for source_id, data_source in self.data_sources.items():
            if source_id not in self.active_sources:
                await data_source.start_updates()
                self.active_sources.add(source_id)
    
    async def stop_all_sources(self) -> None:
        """Stop all active data sources"""
        for source_id in self.active_sources.copy():
            data_source = self.data_sources.get(source_id)
            if data_source:
                await data_source.stop_updates()
        self.active_sources.clear()
    
    def cleanup(self) -> None:
        """Clean up all bindings and sources"""
        # Deactivate all bindings
        for binding in self.bindings.values():
            binding.deactivate()
        self.bindings.clear()
        
        # Stop all sources
        asyncio.create_task(self.stop_all_sources())
        
        # Clear data sources
        self.data_sources.clear()


# Example data sources for common use cases

class BotDataSource(RealTimeDataSource):
    """Data source for bot information"""
    
    def __init__(self, bot_id: str):
        super().__init__(f"bot_{bot_id}")
        self.bot_id = bot_id
        self.update_task: Optional[asyncio.Task] = None
    
    async def start_updates(self) -> None:
        """Start polling for bot updates"""
        if self.update_task and not self.update_task.done():
            return
        
        self.update_task = asyncio.create_task(self._update_loop())
    
    async def stop_updates(self) -> None:
        """Stop polling for bot updates"""
        if self.update_task and not self.update_task.done():
            self.update_task.cancel()
            try:
                await self.update_task
            except asyncio.CancelledError:
                pass
    
    async def _update_loop(self) -> None:
        """Update loop for bot data"""
        while True:
            try:
                # Simulate fetching bot data
                # In real implementation, this would call the MCP client
                await asyncio.sleep(5)  # Update every 5 seconds
                
                # Example data updates
                self.set_data("status", "running")
                self.set_data("profit", 123.45)
                self.set_data("trades", 42)
                self.set_data("last_update", datetime.now().strftime("%H:%M:%S"))
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Error updating bot data: {e}")
                await asyncio.sleep(10)  # Wait longer on error


class MarketDataSource(RealTimeDataSource):
    """Data source for market data"""
    
    def __init__(self, symbol: str):
        super().__init__(f"market_{symbol}")
        self.symbol = symbol
        self.update_task: Optional[asyncio.Task] = None
    
    async def start_updates(self) -> None:
        """Start real-time market data updates"""
        if self.update_task and not self.update_task.done():
            return
        
        self.update_task = asyncio.create_task(self._update_loop())
    
    async def stop_updates(self) -> None:
        """Stop market data updates"""
        if self.update_task and not self.update_task.done():
            self.update_task.cancel()
            try:
                await self.update_task
            except asyncio.CancelledError:
                pass
    
    async def _update_loop(self) -> None:
        """Update loop for market data"""
        import random
        
        base_price = 50000.0  # Example base price
        
        while True:
            try:
                # Simulate real-time price updates
                await asyncio.sleep(1)  # Update every second
                
                # Generate realistic price movement
                change_percent = random.uniform(-0.01, 0.01)  # ±1% change
                new_price = base_price * (1 + change_percent)
                base_price = new_price
                
                self.set_data("price", round(new_price, 2))
                self.set_data("change_24h", round(change_percent * 100, 2))
                self.set_data("volume", random.randint(1000000, 5000000))
                self.set_data("timestamp", datetime.now().strftime("%H:%M:%S"))
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Error updating market data: {e}")
                await asyncio.sleep(5)


class SystemDataSource(RealTimeDataSource):
    """Data source for system metrics"""
    
    def __init__(self):
        super().__init__("system")
        self.update_task: Optional[asyncio.Task] = None
    
    async def start_updates(self) -> None:
        """Start system metrics updates"""
        if self.update_task and not self.update_task.done():
            return
        
        self.update_task = asyncio.create_task(self._update_loop())
    
    async def stop_updates(self) -> None:
        """Stop system metrics updates"""
        if self.update_task and not self.update_task.done():
            self.update_task.cancel()
            try:
                await self.update_task
            except asyncio.CancelledError:
                pass
    
    async def _update_loop(self) -> None:
        """Update loop for system metrics"""
        while True:
            try:
                await asyncio.sleep(2)  # Update every 2 seconds
                
                # Get system metrics (simplified without psutil dependency)
                try:
                    import psutil
                    cpu_percent = psutil.cpu_percent(interval=None)
                    memory = psutil.virtual_memory()
                    
                    self.set_data("cpu_usage", round(cpu_percent, 1))
                    self.set_data("memory_usage", round(memory.percent, 1))
                    self.set_data("memory_available", round(memory.available / 1024**3, 2))  # GB
                except ImportError:
                    # Fallback to mock data if psutil not available
                    import random
                    self.set_data("cpu_usage", round(random.uniform(10, 80), 1))
                    self.set_data("memory_usage", round(random.uniform(30, 90), 1))
                    self.set_data("memory_available", round(random.uniform(2, 8), 2))
                
                self.set_data("uptime", datetime.now().strftime("%H:%M:%S"))
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Error updating system metrics: {e}")
                await asyncio.sleep(10)