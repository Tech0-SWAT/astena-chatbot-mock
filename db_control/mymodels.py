from sqlalchemy import ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from datetime import datetime
 

class Base(DeclarativeBase):
    pass

class ChangeTitle(Base):
    __tablename__ = 'ChangeTitle'
    LogID: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    OperationTimestamp: Mapped[str] = mapped_column()
    TargetRecordID: Mapped[str] = mapped_column()
    Old_ItemName: Mapped[str] = mapped_column()
    New_ItemName: Mapped[str] = mapped_column()
    Old_Amount: Mapped[float] = mapped_column()
    New_Amount: Mapped[float] = mapped_column()
    Old_AccountTitle: Mapped[str] = mapped_column()
    New_AccountTitle: Mapped[str] = mapped_column()
    Old_LegalUsefulLife: Mapped[str] = mapped_column()
    New_LegalUsefulLife: Mapped[str] = mapped_column()
    Old_Basis: Mapped[str] = mapped_column()
    New_Basis: Mapped[str] = mapped_column()
    Remarks: Mapped[str] = mapped_column()