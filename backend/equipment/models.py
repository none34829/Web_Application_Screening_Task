import uuid

from django.db import models


class EquipmentDataset(models.Model):
    """
    Stores a snapshot of a CSV upload plus calculated summary metrics.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    file_name = models.CharField(max_length=255)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    summary = models.JSONField()
    data = models.JSONField()

    class Meta:
        ordering = ("-uploaded_at",)

    def __str__(self) -> str:
        return f"{self.file_name} ({self.uploaded_at:%Y-%m-%d %H:%M})"
