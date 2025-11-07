from rest_framework import serializers

from .models import EquipmentDataset


class EquipmentDatasetSerializer(serializers.ModelSerializer):
    class Meta:
        model = EquipmentDataset
        fields = ("id", "file_name", "uploaded_at", "summary")


class EquipmentDatasetDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = EquipmentDataset
        fields = ("id", "file_name", "uploaded_at", "summary", "data")
