import logging
from typing import Any, Optional
from neo4j import GraphDatabase, AsyncGraphDatabase
from app.config import get_settings

logger = logging.getLogger(__name__)


class Neo4jClient:
    _driver = None
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def connect(self):
        settings = get_settings()
        try:
            self._driver = GraphDatabase.driver(
                settings.neo4j_uri,
                auth=(settings.neo4j_user, settings.neo4j_password),
            )
            self._driver.verify_connectivity()
            self._init_schema()
            logger.info("Connected to Neo4j at %s", settings.neo4j_uri)
        except Exception as e:
            logger.warning("Neo4j not available: %s. Using in-memory fallback.", e)
            self._driver = None

    def _init_schema(self):
        if not self._driver:
            return
        with self._driver.session() as session:
            session.run("CREATE INDEX IF NOT EXISTS FOR (d:Device) ON (d.id)")
            session.run("CREATE INDEX IF NOT EXISTS FOR (d:Device) ON (d.ip)")
            session.run("CREATE INDEX IF NOT EXISTS FOR (v:VLAN) ON (v.vlan_id)")

    @property
    def available(self) -> bool:
        return self._driver is not None

    def close(self):
        if self._driver:
            self._driver.close()

    def execute_read(self, query: str, params: dict | None = None) -> list[dict]:
        if not self._driver:
            return []
        with self._driver.session() as session:
            result = session.run(query, params or {})
            return [record.data() for record in result]

    def execute_write(self, query: str, params: dict | None = None) -> Any:
        if not self._driver:
            return None
        with self._driver.session() as session:
            result = session.run(query, params or {})
            return result.consume()

    def upsert_device(self, device: dict) -> None:
        query = """
        MERGE (d:Device {id: $id})
        SET d += $props
        """
        self.execute_write(query, {"id": device["id"], "props": device})

    def upsert_connection(self, conn: dict) -> None:
        query = """
        MATCH (s:Device {id: $source_id})
        MATCH (t:Device {id: $target_id})
        MERGE (s)-[r:CONNECTS_TO {id: $id}]->(t)
        SET r += $props
        """
        self.execute_write(query, {
            "source_id": conn["source_id"],
            "target_id": conn["target_id"],
            "id": conn["id"],
            "props": {k: v for k, v in conn.items() if k not in ("source_id", "target_id")},
        })

    def upsert_dependency(self, dep: dict) -> None:
        query = """
        MATCH (s:Device {id: $source_id})
        MATCH (t:Device {id: $target_id})
        MERGE (s)-[r:DEPENDS_ON {id: $id}]->(t)
        SET r += $props
        """
        self.execute_write(query, {
            "source_id": dep["source_id"],
            "target_id": dep["target_id"],
            "id": dep["id"],
            "props": {k: v for k, v in dep.items() if k not in ("source_id", "target_id")},
        })

    def get_all_devices(self) -> list[dict]:
        query = "MATCH (d:Device) RETURN d"
        results = self.execute_read(query)
        return [r["d"] for r in results]

    def get_device(self, device_id: str) -> dict | None:
        query = "MATCH (d:Device {id: $id}) RETURN d"
        results = self.execute_read(query, {"id": device_id})
        return results[0]["d"] if results else None

    def get_all_connections(self) -> list[dict]:
        query = """
        MATCH (s:Device)-[r:CONNECTS_TO]->(t:Device)
        RETURN properties(r) as r, s.id as source_id, t.id as target_id
        """
        results = self.execute_read(query)
        return [{**r["r"], "source_id": r["source_id"], "target_id": r["target_id"]} for r in results]

    def get_device_connections(self, device_id: str) -> list[dict]:
        query = """
        MATCH (d:Device {id: $id})-[r:CONNECTS_TO]-(other:Device)
        RETURN r, other.id as other_id, other.hostname as other_hostname
        """
        return self.execute_read(query, {"id": device_id})

    def get_all_dependencies(self) -> list[dict]:
        query = """
        MATCH (s:Device)-[r:DEPENDS_ON]->(t:Device)
        RETURN properties(r) as r, s.id as source_id, t.id as target_id
        """
        results = self.execute_read(query)
        return [{**r["r"], "source_id": r["source_id"], "target_id": r["target_id"]} for r in results]

    def get_topology(self) -> dict:
        devices = self.get_all_devices()
        connections = self.get_all_connections()
        dependencies = self.get_all_dependencies()
        return {
            "devices": devices,
            "connections": connections,
            "dependencies": dependencies,
        }

    def clear_all(self):
        self.execute_write("MATCH (n) DETACH DELETE n")


neo4j_client = Neo4jClient()
