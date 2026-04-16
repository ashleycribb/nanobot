import asyncio
import time
from unittest.mock import AsyncMock, MagicMock

class MockResponse:
    def __init__(self, content):
        self.content = content

    def raise_for_status(self):
        pass

async def benchmark_old(attachments, http_client, file_path_mock):
    media_paths = []

    start = time.time()
    for attachment in attachments:
        url = attachment.get("url")
        resp = await http_client.get(url)
        resp.raise_for_status()
        await asyncio.to_thread(file_path_mock.write_bytes, resp.content)
        media_paths.append("path")
    end = time.time()
    return end - start

async def benchmark_new(attachments, http_client, file_path_mock):
    media_paths = []

    start = time.time()
    async def download_attachment(attachment):
        url = attachment.get("url")
        resp = await http_client.get(url)
        resp.raise_for_status()
        await asyncio.to_thread(file_path_mock.write_bytes, resp.content)
        return "path"

    results = await asyncio.gather(*(download_attachment(att) for att in attachments))
    media_paths.extend([r for r in results if r])
    end = time.time()
    return end - start

async def main():
    attachments = [{"url": f"http://example.com/{i}", "filename": f"file{i}.txt", "id": f"id{i}"} for i in range(10)]

    async def mock_get(url):
        await asyncio.sleep(0.1) # Simulate network delay
        return MockResponse(b"test data")

    http_client = AsyncMock()
    http_client.get.side_effect = mock_get

    file_path_mock = MagicMock()
    file_path_mock.write_bytes = lambda x: time.sleep(0.01) # Simulate disk IO

    old_time = await benchmark_old(attachments, http_client, file_path_mock)
    print(f"Old sequential time: {old_time:.4f}s")

    new_time = await benchmark_new(attachments, http_client, file_path_mock)
    print(f"New concurrent time: {new_time:.4f}s")
    print(f"Improvement: {old_time/new_time:.2f}x faster")

if __name__ == "__main__":
    asyncio.run(main())
