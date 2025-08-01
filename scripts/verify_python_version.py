#!/usr/bin/env python3
"""
Python Version Verification Script
---------------------------------
Verifies that Python 3.11+ is being used and all modern syntax features work.

Run with: python scripts/verify_python_version.py
"""

import sys
from typing import Self
from enum import IntEnum

def verify_python_version():
    """Verify Python version is 3.11 or higher"""
    version = sys.version_info
    print(f"🐍 Python Version: {version.major}.{version.minor}.{version.micro}")
    
    if version.major < 3 or (version.major == 3 and version.minor < 11):
        print("❌ ERROR: Python 3.11 or higher is required!")
        print("   This project uses modern Python features including:")
        print("   - match statements (Python 3.10+)")
        print("   - union types with | syntax (Python 3.10+)")
        print("   - Self type hints (Python 3.11+)")
        return False
    else:
        print("✅ Python version is compatible!")
        return True

def test_union_types():
    """Test union types with | syntax"""
    print("\n🔗 Testing Union Types (| syntax)...")
    
    # Test union type annotation
    def process_data(data: str | int | None) -> str:
        match data:
            case str():
                return f"String: {data}"
            case int():
                return f"Integer: {data}"
            case None:
                return "None"
            case _:
                return "Unknown"
    
    # Test the function
    result1 = process_data("hello")
    result2 = process_data(42)
    result3 = process_data(None)
    
    print(f"   String test: {result1}")
    print(f"   Integer test: {result2}")
    print(f"   None test: {result3}")
    print("✅ Union types work correctly!")

def test_match_statements():
    """Test match statements"""
    print("\n🎯 Testing Match Statements...")
    
    def analyze_value(value: str | int | list | None) -> str:
        match value:
            case str() as s if len(s) > 5:
                return f"Long string: {s[:5]}..."
            case str():
                return f"Short string: {value}"
            case int() as n if n > 100:
                return f"Large number: {n}"
            case int():
                return f"Small number: {value}"
            case list() as lst if len(lst) > 0:
                return f"Non-empty list with {len(lst)} items"
            case list():
                return "Empty list"
            case None:
                return "None value"
            case _:
                return "Unknown type"
    
    # Test the function
    tests = [
        "short",
        "very long string here",
        50,
        150,
        [],
        [1, 2, 3],
        None
    ]
    
    for test in tests:
        result = analyze_value(test)
        print(f"   {test!r} -> {result}")
    
    print("✅ Match statements work correctly!")

def test_self_type_hints():
    """Test Self type hints"""
    print("\n🔄 Testing Self Type Hints...")
    
    class ExampleClass:
        def __init__(self, value: int):
            self.value = value
        
        def add(self, other: int) -> Self:
            return ExampleClass(self.value + other)
        
        def multiply(self, factor: int) -> Self:
            return ExampleClass(self.value * factor)
        
        def __str__(self) -> str:
            return f"ExampleClass({self.value})"
    
    # Test the class
    obj1 = ExampleClass(10)
    obj2 = obj1.add(5).multiply(2)
    
    print(f"   Original: {obj1}")
    print(f"   After add(5).multiply(2): {obj2}")
    print("✅ Self type hints work correctly!")

def test_modern_enums():
    """Test modern enum features"""
    print("\n📊 Testing Modern Enums...")
    
    class Status(IntEnum):
        PENDING = 0
        RUNNING = 1
        COMPLETED = 2
        FAILED = 3
    
    def process_status(status: Status) -> str:
        match status:
            case Status.PENDING:
                return "Waiting to start"
            case Status.RUNNING:
                return "Currently executing"
            case Status.COMPLETED:
                return "Successfully finished"
            case Status.FAILED:
                return "Execution failed"
            case _:
                return "Unknown status"
    
    # Test the enum
    for status in Status:
        result = process_status(status)
        print(f"   {status.name} ({status.value}) -> {result}")
    
    print("✅ Modern enums work correctly!")

def test_pydantic_models():
    """Test Pydantic models with modern syntax"""
    print("\n📋 Testing Pydantic Models...")
    
    try:
        from pydantic import BaseModel, Field
        
        class User(BaseModel):
            name: str
            age: int
            email: str | None = None
            is_active: bool = True
        
        # Test model creation
        user1 = User(name="Alice", age=30)
        user2 = User(name="Bob", age=25, email="bob@example.com", is_active=False)
        
        print(f"   User 1: {user1}")
        print(f"   User 2: {user2}")
        print("✅ Pydantic models work correctly!")
        
    except ImportError:
        print("⚠️ Pydantic not available, skipping Pydantic test")

def test_dataclasses():
    """Test dataclasses with modern syntax"""
    print("\n📦 Testing Dataclasses...")
    
    from dataclasses import dataclass
    
    @dataclass
    class Point:
        x: float
        y: float
        
        def distance_to(self, other: Self) -> float:
            return ((self.x - other.x) ** 2 + (self.y - other.y) ** 2) ** 0.5
        
        def __str__(self) -> str:
            return f"Point({self.x}, {self.y})"
    
    # Test the dataclass
    p1 = Point(0, 0)
    p2 = Point(3, 4)
    distance = p1.distance_to(p2)
    
    print(f"   Point 1: {p1}")
    print(f"   Point 2: {p2}")
    print(f"   Distance: {distance}")
    print("✅ Dataclasses work correctly!")

def main():
    """Main verification function"""
    print("🚀 Python 3.11+ Feature Verification")
    print("=" * 50)
    
    # Check Python version first
    if not verify_python_version():
        sys.exit(1)
    
    # Test all modern features
    test_union_types()
    test_match_statements()
    test_self_type_hints()
    test_modern_enums()
    test_pydantic_models()
    test_dataclasses()
    
    print("\n" + "=" * 50)
    print("🎉 All Python 3.11+ features verified successfully!")
    print("\n✅ Your environment is ready for pyHaasAPI development!")
    print("   You can now use all modern Python features including:")
    print("   - Union types with | syntax")
    print("   - Match statements")
    print("   - Self type hints")
    print("   - Modern enums and dataclasses")
    print("   - Pydantic models with modern syntax")

if __name__ == "__main__":
    main() 