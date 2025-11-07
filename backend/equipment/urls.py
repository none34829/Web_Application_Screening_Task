from django.urls import path

from .views import (
    DatasetHistoryView,
    DatasetPDFView,
    DatasetUploadView,
    LatestDatasetView,
    health_check,
)

urlpatterns = [
    path("health/", health_check, name="health-check"),
    path("upload/", DatasetUploadView.as_view(), name="dataset-upload"),
    path("datasets/latest/", LatestDatasetView.as_view(), name="dataset-latest"),
    path("datasets/history/", DatasetHistoryView.as_view(), name="dataset-history"),
    path("datasets/<uuid:pk>/pdf/", DatasetPDFView.as_view(), name="dataset-pdf"),
]
