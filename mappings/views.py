from rest_framework import generics, status
from rest_framework.exceptions import NotFound
from rest_framework.response import Response
from rest_framework.views import APIView

from doctors.models import Doctor
from mappings.models import PatientDoctorMapping
from mappings.serializers import MappingCreateSerializer, MappingSerializer
from patients.models import Patient
from doctors.serializers import DoctorSerializer


class MappingListCreateView(generics.ListCreateAPIView):
    def get_queryset(self):
        return PatientDoctorMapping.objects.filter(
            patient__owner=self.request.user
        ).select_related("patient", "doctor")

    def get_serializer_class(self):
        if self.request.method == "POST":
            return MappingCreateSerializer
        return MappingSerializer


class PatientMappingsView(APIView):
    def get(self, request, item_id):
        try:
            patient = Patient.objects.get(pk=item_id, owner=request.user)
        except Patient.DoesNotExist:
            raise NotFound("Patient not found.")
        doctors = Doctor.objects.filter(patient_mappings__patient=patient)
        return Response(DoctorSerializer(doctors, many=True).data)

    def delete(self, request, item_id):
        try:
            mapping = PatientDoctorMapping.objects.get(
                pk=item_id,
                patient__owner=request.user,
            )
        except PatientDoctorMapping.DoesNotExist:
            raise NotFound("Mapping not found.")
        mapping.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
