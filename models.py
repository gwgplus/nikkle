from typing import List, Optional

from sqlalchemy import CHAR, DateTime, ForeignKeyConstraint, Index, Integer, String
from sqlalchemy.dialects.mysql import TINYINT
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
import datetime

class Base(DeclarativeBase):
    pass


class Account(Base):
    __tablename__ = 'account'

    Account: Mapped[str] = mapped_column(CHAR(20, 'utf8mb4_unicode_ci'), primary_key=True)
    Name: Mapped[str] = mapped_column(String(50, 'utf8mb4_unicode_ci'))
    Password: Mapped[str] = mapped_column(String(64, 'utf8mb4_unicode_ci'))
    NeedPassword: Mapped[Optional[int]] = mapped_column(TINYINT(1))
    IsAdmin: Mapped[Optional[int]] = mapped_column(TINYINT(1))

    ocrlog: Mapped[List['Ocrlog']] = relationship('Ocrlog', back_populates='account')


class Ocrlog(Base):
    __tablename__ = 'ocrlog'
    __table_args__ = (
        ForeignKeyConstraint(['Account'], ['account.Account'], ondelete='CASCADE', onupdate='CASCADE', name='FK_OCRLog_ToAccount'),
        Index('IX_OCRLog_Account', 'Account'),
        Index('IX_OCRLog_Time', 'Time')
    )

    Id: Mapped[int] = mapped_column(Integer, primary_key=True)
    Account_: Mapped[str] = mapped_column('Account', CHAR(20, 'utf8mb4_unicode_ci'))
    Time: Mapped[datetime.datetime] = mapped_column(DateTime)
    Source: Mapped[str] = mapped_column(String(50, 'utf8mb4_unicode_ci'))
    OCRResult: Mapped[str] = mapped_column(String(50, 'utf8mb4_unicode_ci'))
    OK: Mapped[int] = mapped_column(TINYINT(1))
    Image: Mapped[str] = mapped_column(String(255, 'utf8mb4_unicode_ci'))
    Manual: Mapped[int] = mapped_column(TINYINT(1))
    Judgment: Mapped[int] = mapped_column(Integer)
    KeyInResult: Mapped[Optional[str]] = mapped_column(String(255, 'utf8mb4_unicode_ci'))
    Processor: Mapped[Optional[str]] = mapped_column(String(255, 'utf8mb4_unicode_ci'))
    IsExteriorOK: Mapped[Optional[int]] = mapped_column(TINYINT(1))
    ExteriorClass: Mapped[Optional[int]] = mapped_column(Integer)
    ExteriorErrReason: Mapped[Optional[int]] = mapped_column(Integer)

    account: Mapped['Account'] = relationship('Account', back_populates='ocrlog')
