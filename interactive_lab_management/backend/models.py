from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()

class Script(Base):
    __tablename__ = 'scripts'

    id = Column(String, primary_key=True)
    name = Column(String)
    parameters = relationship("Parameter", back_populates="script")
    templates = relationship("ParameterTemplate", back_populates="script")

class Parameter(Base):
    __tablename__ = 'parameters'

    id = Column(Integer, primary_key=True)
    key = Column(String)
    script_id = Column(String, ForeignKey('scripts.id'))
    script = relationship("Script", back_populates="parameters")
    history = relationship("ParameterHistory", back_populates="parameter")

class Backtest(Base):
    __tablename__ = 'backtests'

    id = Column(Integer, primary_key=True)
    script_id = Column(String, ForeignKey('scripts.id'))
    market = Column(String)
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    roi = Column(Float)
    max_drawdown = Column(Float)
    sharpe_ratio = Column(Float, nullable=True)
    sortino_ratio = Column(Float, nullable=True)
    qualitative_assessment = Column(String, nullable=True)
    log = Column(Text)
    trades = Column(Text)

class ParameterHistory(Base):
    __tablename__ = 'parameter_history'

    id = Column(Integer, primary_key=True)
    parameter_id = Column(Integer, ForeignKey('parameters.id'))
    parameter = relationship("Parameter", back_populates="history")
    backtest_id = Column(Integer, ForeignKey('backtests.id'))
    min_value = Column(Float)
    max_value = Column(Float)

class ParameterTemplate(Base):
    __tablename__ = 'parameter_templates'

    id = Column(Integer, primary_key=True)
    script_id = Column(String, ForeignKey('scripts.id'))
    name = Column(String, unique=True, nullable=False)
    parameters_json = Column(Text, nullable=False) # Store parameters as JSON string
    script = relationship("Script", back_populates="templates")
