import asyncio
from unittest.mock import AsyncMock, patch
import pytest
from app.main import app, lifespan

def test_consumer_stops_even_when_lifespan_body_raises():
    async def scenario():
        with patch('app.main.consumer.start') as start, patch('app.main.consumer.stop', new_callable=AsyncMock) as stop:
            with pytest.raises(RuntimeError, match='shutdown'):
                async with lifespan(app):
                    raise RuntimeError('shutdown')
            start.assert_called_once(); stop.assert_awaited_once()
    asyncio.run(scenario())
