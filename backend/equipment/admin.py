from django.contrib import admin

from .models import EquipmentDataset


@admin.register(EquipmentDataset)
class EquipmentDatasetAdmin(admin.ModelAdmin):
    list_display = ("file_name", "uploaded_at", "summary_preview")
    ordering = ("-uploaded_at",)

    def summary_preview(self, obj):
        total = obj.summary.get("total_equipment", "?")
        return f"{total} items"

    summary_preview.short_description = "Summary"
