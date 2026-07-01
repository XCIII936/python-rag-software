"""Database initialisation script.

Creates all tables, seeds the default teacher account, default LLM config,
and default chapters for a "Software Engineering" course.

Usage:
    python -m scripts.init_db
"""

import sys
import os

# Ensure the backend package is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import logging

from app.db.database import engine, Base, SessionLocal
from app.core.security import hash_password
from app.models.user import User
from app.models.llm_config import LlmConfig
from app.models.chapter import Chapter

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger("init_db")


def create_tables():
    """Create all database tables."""
    logger.info("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    logger.info("Tables created successfully.")


def seed_teacher():
    """Seed the default teacher account (admin / admin123)."""
    db = SessionLocal()
    try:
        existing = db.query(User).filter(User.username == "admin").first()
        if existing:
            logger.info("Default teacher account already exists, skipping.")
            return

        teacher = User(
            username="admin",
            password_hash=hash_password("admin123"),
            role="teacher",
            email="admin@course-agent.local",
            is_active=True,
        )
        db.add(teacher)
        db.commit()
        logger.info("Default teacher account created: admin / admin123")
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to seed teacher: {e}")
        raise
    finally:
        db.close()


def seed_llm_config():
    """Seed the default LLM configuration (DashScope / Qwen)."""
    db = SessionLocal()
    try:
        existing = db.query(LlmConfig).filter(LlmConfig.is_active == True).first()
        if existing:
            logger.info("Default LLM config already exists, skipping.")
            return

        config = LlmConfig(
            provider="dashscope",
            api_key="",
            api_key_encrypted=False,
            model_name="qwen3-max",
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
            embedding_model="text-embedding-v3",
            temperature=0.7,
            max_tokens=2048,
            top_p=0.9,
            is_active=True,
        )
        db.add(config)
        db.commit()
        logger.info("Default LLM config created: dashscope / qwen3-max")
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to seed LLM config: {e}")
        raise
    finally:
        db.close()


def seed_chapters():
    """Seed default chapters for the 'Software Engineering' course."""
    db = SessionLocal()
    try:
        existing_count = db.query(Chapter).count()
        if existing_count > 0:
            logger.info(f"{existing_count} chapters already exist, skipping seed.")
            return

        chapters = [
            Chapter(
                title="软件工程概述",
                description="软件工程的定义、发展历史、软件危机、软件过程模型（瀑布模型、敏捷开发等）",
                order_index=0,
                is_active=True,
            ),
            Chapter(
                title="需求工程",
                description="需求获取、需求分析、需求规格说明、需求验证、面向对象的需求分析方法",
                order_index=1,
                is_active=True,
            ),
            Chapter(
                title="软件设计与架构",
                description="软件设计原则、架构模式（MVC、微服务等）、模块化设计、设计模式简介",
                order_index=2,
                is_active=True,
            ),
            Chapter(
                title="软件实现与编码规范",
                description="编码规范、代码重构、版本控制（Git）、代码审查、单元测试",
                order_index=3,
                is_active=True,
            ),
            Chapter(
                title="软件测试",
                description="测试类型（白盒、黑盒、集成测试、系统测试）、测试用例设计、自动化测试",
                order_index=4,
                is_active=True,
            ),
            Chapter(
                title="软件维护与项目管理",
                description="软件维护类型、配置管理、项目计划与估算、风险管理、团队协作",
                order_index=5,
                is_active=True,
            ),
            Chapter(
                title="软件质量与过程改进",
                description="软件质量保证、CMMI、ISO标准、度量与分析、持续改进",
                order_index=6,
                is_active=True,
            ),
            Chapter(
                title="新兴软件开发方法",
                description="DevOps、持续集成/持续部署、云原生开发、AI辅助开发",
                order_index=7,
                is_active=True,
            ),
        ]

        for ch in chapters:
            db.add(ch)
        db.commit()
        logger.info(f"Seeded {len(chapters)} chapters for '软件工程' course.")
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to seed chapters: {e}")
        raise
    finally:
        db.close()


def main():
    """Run the full initialisation."""
    logger.info("=" * 50)
    logger.info("Course Teaching Agent - DB Initialisation")
    logger.info("=" * 50)

    create_tables()
    seed_teacher()
    seed_llm_config()
    seed_chapters()

    logger.info("=" * 50)
    logger.info("Database initialisation complete!")
    logger.info("=" * 50)


if __name__ == "__main__":
    main()
