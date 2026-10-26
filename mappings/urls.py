from django.urls import path

from mappings.views import MappingListCreateView, PatientMappingsView


urlpatterns = [
    path("", MappingListCreateView.as_view(), name="mapping-list-create"),
    path("<int:item_id>/", PatientMappingsView.as_view(), name="mapping-detail"),
]
