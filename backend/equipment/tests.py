from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from rest_framework.test import APIClient

SAMPLE_CSV = """Equipment Name,Type,Flowrate,Pressure,Temperature
Pump A,Pump,100,50,300
Pump B,Pump,150,60,310
Valve C,Valve,90,55,290
"""


class EquipmentAPITests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.user = user_model.objects.create_user(username="tester", password="secret")
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def _upload(self, name="sample.csv"):
        upload = SimpleUploadedFile(name, SAMPLE_CSV.encode("utf-8"), content_type="text/csv")
        response = self.client.post("/api/upload/", {"file": upload}, format="multipart")
        self.assertEqual(response.status_code, 201, response.content)
        return response.data

    def test_upload_returns_summary(self):
        data = self._upload()
        self.assertEqual(data["summary"]["total_equipment"], 3)
        self.assertAlmostEqual(data["summary"]["avg_flowrate"], 113.33, places=2)

    def test_history_is_limited_to_five(self):
        for index in range(6):
            self._upload(name=f"file-{index}.csv")
        history_response = self.client.get("/api/datasets/history/")
        self.assertEqual(history_response.status_code, 200)
        self.assertEqual(len(history_response.data), 5)
