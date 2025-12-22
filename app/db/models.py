from sqlalchemy import Column, Date, Enum, Float, Integer, String, ForeignKey
from sqlalchemy.orm import relationship

from app.db.base import Base
from app.schemas.consumption import ConsumptionType


class Household(Base):
    __tablename__ = "households"

    id = Column(Integer, primary_key=True)
    household_id = Column(String(10), unique=True, index=True)
    meter_point_id = Column(String(13), index=True)

    consumption_items = relationship(
        "Consumption",
        back_populates="household",
        cascade="all, delete"
    )


class Consumption(Base):
    __tablename__ = "consumption"

    id = Column(Integer, primary_key=True)
    household_id = Column(Integer, ForeignKey("households.id"))
    consumption_type = Column(Enum(ConsumptionType))
    consumption_value = Column(Float)
    consumption_date = Column(Date)

    household = relationship("Household", back_populates="consumption_items")
