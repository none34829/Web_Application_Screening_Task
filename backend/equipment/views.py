from __future__ import annotations

from typing import Dict

import pandas as pd
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import EquipmentDataset
from .serializers import (
    EquipmentDatasetDetailSerializer,
    EquipmentDatasetSerializer,
)
from .services import generate_pdf_report, pdf_filename


REQUIRED_COLUMNS = {
    "equipment name": "Equipment Name",
    "type": "Type",
    "flowrate": "Flowrate",
    "pressure": "Pressure",
    "temperature": "Temperature",
}


@api_view(["GET"])
@permission_classes([AllowAny])
def health_check(request):
    return Response({"status": "ok"})


class DatasetUploadView(APIView):
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request, *args, **kwargs):
        upload = request.FILES.get("file")
        if not upload:
            return Response(
                {"detail": "CSV file is required with field name 'file'."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            dataset = self._create_dataset(upload)
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as exc:  # pragma: no cover - defensive
            return Response(
                {"detail": f"Unable to process CSV: {exc}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = EquipmentDatasetDetailSerializer(dataset)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def _create_dataset(self, upload) -> EquipmentDataset:
        data_frame = pd.read_csv(upload)
        column_lookup = self._build_column_lookup(data_frame.columns)
        self._validate_columns(column_lookup)

        numeric_columns = [
            column_lookup["flowrate"],
            column_lookup["pressure"],
            column_lookup["temperature"],
        ]
        for column in numeric_columns:
            data_frame[column] = pd.to_numeric(data_frame[column], errors="coerce")

        if data_frame[numeric_columns].isnull().any().any():
            raise ValueError("Numeric columns contain invalid values that cannot be parsed.")

        summary = self._build_summary(data_frame, column_lookup)
        records = data_frame.to_dict(orient="records")

        dataset = EquipmentDataset.objects.create(
            file_name=upload.name,
            summary=summary,
            data=records,
        )
        self._prune_history()
        return dataset

    def _build_column_lookup(self, columns) -> Dict[str, str]:
        lookup = {}
        for column in columns:
            normalized = column.strip().lower()
            lookup[normalized] = column
        return lookup

    def _validate_columns(self, lookup) -> None:
        missing = [label for label in REQUIRED_COLUMNS if label not in lookup]
        if missing:
            raise ValueError(
                "CSV is missing required columns: " + ", ".join(REQUIRED_COLUMNS[key] for key in missing)
            )

    def _build_summary(self, df: pd.DataFrame, lookup: Dict[str, str]) -> Dict[str, float]:
        type_column = lookup["type"]
        summary = {
            "total_equipment": int(len(df)),
            "avg_flowrate": round(df[lookup["flowrate"]].mean(), 2),
            "avg_pressure": round(df[lookup["pressure"]].mean(), 2),
            "avg_temperature": round(df[lookup["temperature"]].mean(), 2),
            "type_distribution": df[type_column].value_counts().to_dict(),
        }
        return summary

    def _prune_history(self) -> None:
        ids_to_keep = list(
            EquipmentDataset.objects.order_by("-uploaded_at").values_list("id", flat=True)[:5]
        )
        EquipmentDataset.objects.exclude(id__in=ids_to_keep).delete()


class LatestDatasetView(APIView):
    def get(self, request, *args, **kwargs):
        dataset = EquipmentDataset.objects.order_by("-uploaded_at").first()
        if not dataset:
            return Response(
                {"detail": "No datasets uploaded yet."},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = EquipmentDatasetDetailSerializer(dataset)
        return Response(serializer.data)


class DatasetHistoryView(generics.ListAPIView):
    serializer_class = EquipmentDatasetSerializer

    def get_queryset(self):
        return EquipmentDataset.objects.order_by("-uploaded_at")[:5]


class DatasetPDFView(APIView):
    def get(self, request, pk, *args, **kwargs):
        dataset = get_object_or_404(EquipmentDataset, pk=pk)
        pdf_buffer = generate_pdf_report(dataset)
        response = HttpResponse(pdf_buffer.getvalue(), content_type="application/pdf")
        response["Content-Disposition"] = f'attachment; filename="{pdf_filename(dataset)}"'
        return response
