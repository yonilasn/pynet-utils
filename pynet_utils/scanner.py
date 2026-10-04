import asyncio
import ipaddress
from typing import List, Tuple

async def scan_port(host: str, port: int, timeout: float = 2.0) -> Tuple[str, int, bool]:
    try:
        _, writer = await asyncio.wait_for(
            asyncio.open_connection(host, port), timeout=timeout
        )
        writer.close()
        await writer.wait_closed()
        return host, port, True
    except (asyncio.TimeoutError, ConnectionRefusedError, OSError):
        return host, port, False

async def scan(target: str, ports: List[int], concurrency: int = 100) -> List[Tuple[str, int]]:
    semaphore = asyncio.Semaphore(concurrency)
    results = []

    async def _scan(host: str, port: int):
        async with semaphore:
            h, p, is_open = await scan_port(host, port)
            if is_open:
                results.append((h, p))

    hosts = [str(ip) for ip in ipaddress.ip_network(target, strict=False)]
    tasks = [_scan(h, p) for h in hosts for p in ports]
    await asyncio.gather(*tasks)
    return sorted(results)

if __name__ == "__main__":
    import sys
    target = sys.argv[1] if len(sys.argv) > 1 else "127.0.0.1/32"
    ports = [22, 80, 443, 8080]
    open_ports = asyncio.run(scan(target, ports))
    for host, port in open_ports:
        print(f"  {host}:{port} open")