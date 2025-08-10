import time
import uuid
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import BigInteger, Boolean, Column, Integer, String

from open_webui.internal.db import Base, get_db


####################
# PPT Config DB Schema
####################


class PptConfigTable(Base):
    __tablename__ = "ppt_config"

    id = Column(String, primary_key=True)
    enabled = Column(Boolean, default=False, nullable=False)
    api_url = Column(String, default="https://open.docmee.cn", nullable=False)
    api_key = Column(String, default="", nullable=False)
    credits_per_ppt = Column(Integer, default=10, nullable=False)

    updated_at = Column(BigInteger)
    created_at = Column(BigInteger)


####################
# Forms
####################


class PptConfigModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str = Field(default_factory=lambda: "ppt_config")  # 固定ID，只有一条记录
    enabled: bool = False
    api_url: str = "https://open.docmee.cn"
    api_key: str = ""
    credits_per_ppt: int = 10
    updated_at: int = Field(default_factory=lambda: int(time.time()))
    created_at: int = Field(default_factory=lambda: int(time.time()))


####################
# Table Operations
####################


class PptConfigTableOps:
    CONFIG_ID = "ppt_config"  # 固定ID，整个系统只有一条PPT配置记录

    def get_config(self) -> Optional[PptConfigModel]:
        """获取PPT配置"""
        try:
            with get_db() as db:
                config = (
                    db.query(PptConfigTable)
                    .filter(PptConfigTable.id == self.CONFIG_ID)
                    .first()
                )
                if config:
                    return PptConfigModel.model_validate(config)
                return None
        except Exception as e:
            print(f"获取PPT配置失败: {e}")
            return None

    def create_default_config(self) -> PptConfigModel:
        """创建默认PPT配置"""
        try:
            config_model = PptConfigModel()
            with get_db() as db:
                result = PptConfigTable(**config_model.model_dump())
                db.add(result)
                db.commit()
                db.refresh(result)
                return PptConfigModel.model_validate(result)
        except Exception as e:
            print(f"创建默认PPT配置失败: {e}")
            raise e

    def get_or_create_config(self) -> PptConfigModel:
        """获取或创建PPT配置"""
        config = self.get_config()
        if config is None:
            config = self.create_default_config()
        return config

    def update_config(self, config_data: dict) -> Optional[PptConfigModel]:
        """更新PPT配置"""
        try:
            # 确保配置存在
            self.get_or_create_config()

            # 更新配置
            update_data = {**config_data, "updated_at": int(time.time())}
            with get_db() as db:
                db.query(PptConfigTable).filter(
                    PptConfigTable.id == self.CONFIG_ID
                ).update(update_data, synchronize_session=False)
                db.commit()

                # 返回更新后的配置
                updated_config = (
                    db.query(PptConfigTable)
                    .filter(PptConfigTable.id == self.CONFIG_ID)
                    .first()
                )
                return PptConfigModel.model_validate(updated_config)
        except Exception as e:
            print(f"更新PPT配置失败: {e}")
            return None


# 全局实例
PptConfigs = PptConfigTableOps()
