"""Database initialisation script.

Creates all tables, seeds the default teacher account, default LLM config,
default chapters for a "Software Engineering" course, imports course
materials (markdown files) as knowledge-base documents, and creates
default assessment configurations for each chapter.

Usage:
    python -m scripts.init_db
"""

import sys
import os
import shutil
import uuid
import hashlib
import json

# Ensure the backend package is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import logging

from app.db.database import engine, Base, SessionLocal
from app.core.security import hash_password
from app.core.config import settings
from app.models.user import User
from app.models.llm_config import LlmConfig
from app.models.chapter import Chapter
from app.models.document import KnowledgeBaseDocument
from app.models.assessment import ChapterAssessmentConfig

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger("init_db")

# ── Constants ──────────────────────────────────────────────────────────

# Mapping from chapter order_index → markdown file name
CHAPTER_MATERIALS_MAP = {
    0: "01_软件工程概述.md",
    1: "02_需求工程.md",
    2: "03_软件设计与架构.md",
    3: "04_软件实现与编码规范.md",
    4: "05_软件测试.md",
    5: "06_软件维护与项目管理.md",
    6: "07_软件质量与过程改进.md",
    7: "08_新兴软件开发方法.md",
}


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


# ── Document seeding ───────────────────────────────────────────────────

def _find_course_materials_dir() -> str:
    """Locate the course_materials directory.

    Looks in (priority order):
    1. /app/course_materials (Docker volume mount)
    2. ../course_materials relative to backend/ (local dev)
    3. ../../course_materials relative to scripts/ (local dev)
    """
    candidates = [
        os.path.join(os.path.dirname(__file__), "..", "..", "course_materials"),
        os.path.join(os.path.dirname(__file__), "..", "course_materials"),
        "/app/course_materials",
    ]
    for path in candidates:
        resolved = os.path.abspath(path)
        if os.path.isdir(resolved):
            logger.info(f"Found course_materials at: {resolved}")
            return resolved
    return ""


def _check_milvus_has_data() -> bool:
    """Check whether the Milvus collection has any data.

    Returns True if data exists, False if empty or unreachable.
    """
    try:
        from pymilvus import connections, Collection
        connections.connect(
            alias="default",
            host=settings.MILVUS_HOST,
            port=settings.MILVUS_PORT,
            timeout=5,
        )
        col = Collection(settings.MILVUS_COLLECTION)
        col.load()
        count = col.num_entities
        logger.info(f"Milvus collection '{settings.MILVUS_COLLECTION}' has {count} entities.")
        return count > 0
    except Exception as exc:
        logger.warning(f"Milvus check failed (may not be running yet): {exc}")
        return False


def _reindex_all_documents(db) -> int:
    """Re-index all documents from SQLite into Milvus.

    Returns the number of documents successfully indexed.
    """
    from app.api.v1.documents import process_and_index_document

    docs = db.query(KnowledgeBaseDocument).all()
    success_count = 0
    for doc in docs:
        if not os.path.exists(doc.file_path):
            logger.warning(f"Document file missing, skipping: {doc.file_path}")
            continue
        try:
            process_and_index_document(doc.id)
            success_count += 1
            logger.info(f"Re-indexed: {doc.title}")
        except Exception as exc:
            logger.warning(f"Re-index failed for {doc.title}: {exc}")
    return success_count


def seed_documents():
    """Import markdown course materials into the knowledge base.

    Copies each markdown file to the uploads directory, creates a
    KnowledgeBaseDocument record linked to its chapter, and indexes
    the content into Milvus via the background processing pipeline.

    If documents already exist in the DB, checks whether they need
    re-indexing (e.g. when cloning the repo to a new machine where
    Milvus is empty).
    """
    db = SessionLocal()
    try:
        existing_count = db.query(KnowledgeBaseDocument).count()
        if existing_count > 0:
            logger.info(f"{existing_count} documents already exist in DB.")
            # Check if Milvus has data — if not, re-index
            if not _check_milvus_has_data():
                logger.info("Milvus is empty, re-indexing existing documents...")
                indexed = _reindex_all_documents(db)
                logger.info(f"Re-indexed {indexed}/{existing_count} documents.")
            else:
                logger.info("Milvus already has data, skipping re-index.")
            return

        # Locate course materials directory
        materials_dir = _find_course_materials_dir()
        if not materials_dir:
            logger.warning(
                "course_materials directory not found. "
                "Skipping document seed. Mount it as a volume or place it "
                "in backend/../course_materials."
            )
            return

        admin_user = db.query(User).filter(User.username == "admin").first()
        admin_id = admin_user.id if admin_user else None

        chapters = (
            db.query(Chapter)
            .order_by(Chapter.order_index.asc())
            .all()
        )

        imported_count = 0
        for ch in chapters:
            filename = CHAPTER_MATERIALS_MAP.get(ch.order_index)
            if not filename:
                continue

            source_path = os.path.join(materials_dir, filename)
            if not os.path.isfile(source_path):
                logger.warning(f"Course material not found: {source_path}")
                continue

            # Copy to uploads directory
            ext = os.path.splitext(filename)[1]
            unique_name = f"{uuid.uuid4().hex}{ext}"
            upload_dir = os.path.join(settings.UPLOAD_DIR, "documents")
            os.makedirs(upload_dir, exist_ok=True)
            dest_path = os.path.join(upload_dir, unique_name)

            shutil.copy2(source_path, dest_path)

            # Compute file hash and size
            with open(source_path, "rb") as f:
                content = f.read()
            file_hash = hashlib.sha256(content).hexdigest()
            file_size = len(content)

            doc = KnowledgeBaseDocument(
                chapter_id=ch.id,
                title=filename,
                file_type="md",
                file_path=dest_path,
                file_size=file_size,
                file_hash=file_hash,
                status="pending",
                uploaded_by=admin_id,
            )
            db.add(doc)
            db.flush()  # get doc.id
            doc_id = doc.id
            imported_count += 1

            logger.info(f"Imported document: {filename} → chapter '{ch.title}'")

        db.commit()

        if imported_count == 0:
            logger.info("No course materials to import.")
            return

        logger.info(f"Imported {imported_count} documents. Starting indexing...")

        # Index documents into Milvus
        from app.api.v1.documents import process_and_index_document

        for ch in chapters:
            # Re-query docs for this chapter (they were committed above)
            docs = (
                db.query(KnowledgeBaseDocument)
                .filter(KnowledgeBaseDocument.chapter_id == ch.id)
                .all()
            )
            for doc in docs:
                try:
                    process_and_index_document(doc.id)
                except Exception as exc:
                    logger.warning(
                        f"Indexing failed for {doc.title} (Milvus may not be ready): {exc}"
                    )

        logger.info("Document indexing complete.")
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to seed documents: {e}")
    finally:
        db.close()


# ── Assessment config seeding ──────────────────────────────────────────

def _extract_knowledge_points(description: str) -> list:
    """Extract knowledge points from chapter description.

    Splits on common Chinese delimiters (、，，；) and filters out
    short tokens and parenthesized qualifiers.
    """
    import re
    # Split on 、or ，or ；
    parts = re.split(r"[、，；]", description)
    points = []
    for p in parts:
        p = p.strip()
        if not p:
            continue
        # Remove parenthetical notes like （xxx） or (xxx)
        p = re.sub(r"[（(][^）)]*[）)]", "", p).strip()
        if len(p) >= 2:
            points.append(p)
    return points if points else [description]


def seed_assessment_configs():
    """Create default assessment configurations for each chapter.

    Uses the chapter description to derive knowledge points and sets
    sensible defaults for question types and evaluation dimensions.
    Skips chapters that already have a config.
    """
    db = SessionLocal()
    try:
        chapters = (
            db.query(Chapter)
            .order_by(Chapter.order_index.asc())
            .all()
        )

        admin_user = db.query(User).filter(User.username == "admin").first()
        admin_id = admin_user.id if admin_user else None

        created_count = 0
        for ch in chapters:
            # Skip if config already exists
            existing = (
                db.query(ChapterAssessmentConfig)
                .filter(ChapterAssessmentConfig.chapter_id == ch.id)
                .first()
            )
            if existing:
                continue

            knowledge_points = _extract_knowledge_points(ch.description or ch.title)

            # Default question mix: 2 choice, 1 true_false, 1 short_answer
            question_types = {"choice": 2, "true_false": 1, "short_answer": 1}
            total = sum(question_types.values())

            # Default evaluation dimensions
            evaluation_dimensions = [
                {"name": "知识掌握", "weight": 0.4},
                {"name": "理解应用", "weight": 0.4},
                {"name": "分析能力", "weight": 0.2},
            ]

            config = ChapterAssessmentConfig(
                chapter_id=ch.id,
                knowledge_points=json.dumps(knowledge_points, ensure_ascii=False),
                question_types=json.dumps(question_types, ensure_ascii=False),
                evaluation_dimensions=json.dumps(evaluation_dimensions, ensure_ascii=False),
                total_questions=total,
                passing_score=60,
                created_by=admin_id,
            )
            db.add(config)
            created_count += 1

        db.commit()

        if created_count > 0:
            logger.info(
                f"Created default assessment configs for {created_count} chapters."
            )
        else:
            logger.info("Assessment configs already exist, skipping.")
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to seed assessment configs: {e}")
    finally:
        db.close()


# ── Main ───────────────────────────────────────────────────────────────

def main():
    """Run the full initialisation."""
    logger.info("=" * 50)
    logger.info("Course Teaching Agent - DB Initialisation")
    logger.info("=" * 50)

    create_tables()
    seed_teacher()
    seed_llm_config()
    seed_chapters()
    seed_documents()
    seed_assessment_configs()

    logger.info("=" * 50)
    logger.info("Database initialisation complete!")
    logger.info("=" * 50)


if __name__ == "__main__":
    main()
