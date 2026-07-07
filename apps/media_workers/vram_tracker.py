"""GPU heartbeat and VRAM tracking — updates gpu_nodes table."""

import asyncio
import logging

import asyncpg

logger = logging.getLogger("spark.media.vram_tracker")


async def query_nvidia_smi() -> dict | None:
    """Query nvidia-smi for total and free VRAM."""
    try:
        proc = await asyncio.create_subprocess_exec(
            "nvidia-smi",
            "--query-gpu=memory.total,memory.free",
            "--format=csv,noheader,nounits",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=10)
        if proc.returncode != 0:
            logger.warning(f"nvidia-smi failed: {stderr.decode().strip()}")
            return None
        output = stdout.decode().strip()
        if not output:
            return None
        
        lines = output.split("\n")
        total_mb = 0
        free_mb = 0
        for line in lines:
            line = line.strip()
            if not line:
                continue
            parts = line.split(",")
            if len(parts) >= 2:
                total_mb += int(parts[0].strip())
                free_mb += int(parts[1].strip())
        
        if total_mb == 0:
            return None
            
        return {
            "total_mb": total_mb,
            "free_mb": free_mb,
        }
    except FileNotFoundError:
        logger.debug("nvidia-smi not found — no GPU available")
        return None
    except TimeoutError:
        logger.warning("nvidia-smi timed out")
        return None
    except Exception as e:
        logger.warning(f"nvidia-smi query failed: {e}")
        return None


async def heartbeat(pool: asyncpg.Pool, node_name: str):
    """Query GPU VRAM and update gpu_nodes table."""
    info = await query_nvidia_smi()
    if info is None:
        return
    await pool.execute(
        """
        INSERT INTO gpu_nodes (name, total_vram_mb, free_vram_mb, last_heartbeat)
        VALUES ($1, $2, $3, now())
        ON CONFLICT (name) DO UPDATE SET
            total_vram_mb = $2,
            free_vram_mb = $3,
            last_heartbeat = now()
        """,
        node_name,
        info["total_mb"],
        info["free_mb"],
    )
    logger.debug(f"Heartbeat {node_name}: total={info['total_mb']}MB free={info['free_mb']}MB")


async def get_available_node(pool: asyncpg.Pool, required_vram_mb: int) -> dict | None:
    """Find a GPU node with enough free VRAM, recently heard from."""
    row = await pool.fetchrow(
        """
        SELECT * FROM gpu_nodes
        WHERE free_vram_mb >= $1
        AND last_heartbeat > now() - interval '30 seconds'
        ORDER BY free_vram_mb DESC
        LIMIT 1
        """,
        required_vram_mb,
    )
    return dict(row) if row else None


async def reserve_vram(pool: asyncpg.Pool, node_name: str, amount_mb: int):
    """Reserve VRAM on a node (subtract from free)."""
    await pool.execute(
        """
        UPDATE gpu_nodes
        SET free_vram_mb = free_vram_mb - $1
        WHERE name = $2 AND free_vram_mb >= $1
        """,
        amount_mb,
        node_name,
    )


async def release_vram(pool: asyncpg.Pool, node_name: str, amount_mb: int):
    """Release VRAM back to a node."""
    await pool.execute(
        """
        UPDATE gpu_nodes
        SET free_vram_mb = free_vram_mb + $1
        WHERE name = $2
        """,
        amount_mb,
        node_name,
    )


async def heartbeat_loop(pool: asyncpg.Pool, node_name: str, interval: int = 10):
    """Continuously send heartbeats in background."""
    while True:
        try:
            await heartbeat(pool, node_name)
        except Exception as e:
            logger.error(f"Heartbeat error for {node_name}: {e}")
        await asyncio.sleep(interval)
