from rest_framework import serializers

from doctors.models import Doctor
from mappings.models import PatientDoctorMapping
from patients.models import Patient


class MappingCreateSerializer(serializers.ModelSerializer):
    patient_id = serializers.IntegerField()
    doctor_id = serializers.IntegerField()

    class Meta:
        model = PatientDoctorMapping
        fields = ("id", "patient_id", "doctor_id", "created_at")
        read_only_fields = ("id", "created_at")

    def validate_patient_id(self, value):
        try:
            patient = Patient.objects.get(pk=value, owner=self.context["request"].user)
        except Patient.DoesNotExist:
            raise serializers.ValidationError("Patient not found.")
        self._patient = patient
        return value

    def validate_doctor_id(self, value):
        try:
            doctor = Doctor.objects.get(pk=value)
        except Doctor.DoesNotExist:
            raise serializers.ValidationError("Doctor not found.")
        self._doctor = doctor
        return value

    def validate(self, attrs):
        patient = getattr(self, "_patient", None)
        doctor = getattr(self, "_doctor", None)
        if patient is not None and doctor is not None:
            if PatientDoctorMapping.objects.filter(patient=patient, doctor=doctor).exists():
                raise serializers.ValidationError(
                    {"doctor_id": "This doctor is already assigned to this patient."}
                )
        return attrs

    def create(self, validated_data):
        return PatientDoctorMapping.objects.create(
            patient=self._patient,
            doctor=self._doctor,
        )


class MappingSerializer(serializers.ModelSerializer):
    patient_id = serializers.IntegerField(read_only=True)
    doctor_id = serializers.IntegerField(read_only=True)

    class Meta:
        model = PatientDoctorMapping
        fields = ("id", "patient_id", "doctor_id", "created_at")
