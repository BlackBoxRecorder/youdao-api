# coding:utf-8
import sqlite3
import json
from typing import Dict, Any, Optional


class DatabaseManager:
    def __init__(self, db_path: str = "cache.db"):
        self.db_path = db_path
        self.init_database()

    def init_database(self):
        """初始化数据库和表结构"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # 创建单词缓存表
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS word_cache (
                word TEXT PRIMARY KEY,
                phonetic TEXT,
                explains TEXT,
                phrase TEXT,
                collins_sents TEXT,
                trans_sents TEXT
            )
            """
        )

        conn.commit()
        conn.close()

    def get_word_cache(self, word: str) -> Optional[Dict[str, Any]]:
        """从缓存中获取单词数据"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT word, phonetic, explains, phrase, collins_sents, trans_sents
            FROM word_cache WHERE word = ?
            """,
            (word,),
        )

        row = cursor.fetchone()
        conn.close()

        if row:
            return {
                "word": row[0],
                "phonetic": json.loads(row[1]) if row[1] else {},
                "explains": json.loads(row[2]) if row[2] else [],
                "phrase": json.loads(row[3]) if row[3] else [],
                "collins_sents": json.loads(row[4]) if row[4] else [],
                "trans_sents": json.loads(row[5]) if row[5] else [],
            }

        return None

    def save_word_cache(self, data: Dict[str, Any]):
        """保存单词数据到缓存"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT OR REPLACE INTO word_cache 
            (word, phonetic, explains, phrase, collins_sents, trans_sents)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                data.get("word", ""),
                json.dumps(data.get("phonetic", {})),
                json.dumps(data.get("explains", [])),
                json.dumps(data.get("phrase", [])),
                json.dumps(data.get("collins_sents", [])),
                json.dumps(data.get("trans_sents", [])),
            ),
        )

        conn.commit()
        conn.close()
