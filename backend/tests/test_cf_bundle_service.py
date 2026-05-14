import uuid
import unittest
from unittest.mock import AsyncMock
from types import SimpleNamespace

from app.services.content_factory.bundle_service import BundleService
from app.db.schemas import CFBundleCreate, CFBundleUpdate


class TestBundleService(unittest.IsolatedAsyncioTestCase):
    async def test_create_bundle(self):
        session = AsyncMock()
        session.add = AsyncMock()
        session.flush = AsyncMock()
        session.refresh = AsyncMock()

        payload = CFBundleCreate(
            name="Эфир с Воротниковым 21 мая",
            product_stream="onco_school",
            owner_id=uuid.uuid4(),
            brief="Тема: новые подходы к лечению РМЖ.",
        )
        result = await BundleService.create(session, payload)

        self.assertEqual(result.name, payload.name)
        self.assertEqual(result.product_stream, "onco_school")
        self.assertEqual(result.status, "planning")
        session.add.assert_called_once()

    async def test_update_bundle_partial(self):
        session = AsyncMock()
        bundle = SimpleNamespace(
            id=uuid.uuid4(), name="Old", status="planning",
            product_stream="onco_school", brief=None,
        )
        # Patch the get
        BundleService.get = AsyncMock(return_value=bundle)

        result = await BundleService.update(
            session, bundle.id, CFBundleUpdate(name="New", status="production")
        )
        self.assertEqual(result.name, "New")
        self.assertEqual(result.status, "production")

    async def test_update_bundle_owner_and_product_stream(self):
        session = AsyncMock()
        old_owner_id = uuid.uuid4()
        new_owner_id = uuid.uuid4()
        bundle = SimpleNamespace(
            id=uuid.uuid4(),
            name="Old",
            status="planning",
            product_stream="onco_school",
            owner_id=old_owner_id,
            brief=None,
        )
        BundleService.get = AsyncMock(return_value=bundle)

        result = await BundleService.update(
            session,
            bundle.id,
            CFBundleUpdate(product_stream="patient_live", owner_id=new_owner_id),
        )

        self.assertEqual(result.product_stream, "patient_live")
        self.assertEqual(result.owner_id, new_owner_id)


if __name__ == "__main__":
    unittest.main()
