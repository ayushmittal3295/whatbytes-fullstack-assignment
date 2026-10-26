from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import AccessToken

from accounts.models import User
from doctors.models import Doctor
from mappings.models import PatientDoctorMapping
from patients.models import Patient


class HealthcareAPITests(APITestCase):
    password = "CorrectHorseBattery9!"

    def setUp(self):
        self.user = User.objects.create_user(
            email="owner@example.com",
            name="Record Owner",
            password=self.password,
        )
        self.other_user = User.objects.create_user(
            email="other@example.com",
            name="Other Owner",
            password=self.password,
        )

    def authenticate(self, user=None):
        token = AccessToken.for_user(user or self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

    def patient_data(self, **overrides):
        data = {
            "name": "Sam Patient",
            "age": 35,
            "gender": "unspecified",
            "address": "1 Main Street",
            "phone": "555-0100",
        }
        data.update(overrides)
        return data

    def doctor_data(self, **overrides):
        data = {
            "name": "Dr. Alex",
            "specialization": "General practice",
            "email": "doctor@example.com",
            "phone": "555-0110",
        }
        data.update(overrides)
        return data

    def test_registration_login_and_duplicate_email(self):
        response = self.client.post(
            "/api/auth/register/",
            {
                "name": "New User",
                "email": "NEW@example.com",
                "password": self.password,
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        user = User.objects.get(email="new@example.com")
        self.assertTrue(user.check_password(self.password))

        duplicate = self.client.post(
            "/api/auth/register/",
            {
                "name": "Duplicate",
                "email": "NEW@example.com",
                "password": self.password,
            },
            format="json",
        )
        self.assertEqual(duplicate.status_code, status.HTTP_400_BAD_REQUEST)

        login = self.client.post(
            "/api/auth/login/",
            {"email": "new@example.com", "password": self.password},
            format="json",
        )
        self.assertEqual(login.status_code, status.HTTP_200_OK)
        self.assertIn("access", login.data)
        self.assertIn("refresh", login.data)

        invalid_login = self.client.post(
            "/api/auth/login/",
            {"email": "new@example.com", "password": "wrong"},
            format="json",
        )
        self.assertEqual(invalid_login.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_registration_rejects_missing_invalid_email_and_weak_password(self):
        missing = self.client.post("/api/auth/register/", {}, format="json")
        self.assertEqual(missing.status_code, status.HTTP_400_BAD_REQUEST)

        invalid_email = self.client.post(
            "/api/auth/register/",
            {"name": "New User", "email": "not-an-email", "password": self.password},
            format="json",
        )
        self.assertEqual(invalid_email.status_code, status.HTTP_400_BAD_REQUEST)

        weak_password = self.client.post(
            "/api/auth/register/",
            {"name": "New User", "email": "new@example.com", "password": "123"},
            format="json",
        )
        self.assertEqual(weak_password.status_code, status.HTTP_400_BAD_REQUEST)

    def test_protected_endpoints_reject_unauthenticated_requests(self):
        for url in (
            "/api/patients/",
            "/api/doctors/",
            "/api/mappings/",
        ):
            response = self.client.get(url)
            self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        self.client.credentials(HTTP_AUTHORIZATION="Bearer invalid-token")
        response = self.client.get("/api/patients/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_patient_crud_and_owner_isolation(self):
        self.authenticate()
        created = self.client.post(
            "/api/patients/", self.patient_data(), format="json"
        )
        self.assertEqual(created.status_code, status.HTTP_201_CREATED)
        patient_id = created.data["id"]
        self.assertEqual(Patient.objects.get(pk=patient_id).owner, self.user)

        listed = self.client.get("/api/patients/")
        self.assertEqual(len(listed.data), 1)
        detail = self.client.get(f"/api/patients/{patient_id}/")
        self.assertEqual(detail.status_code, status.HTTP_200_OK)

        updated = self.client.put(
            f"/api/patients/{patient_id}/",
            self.patient_data(name="Updated Patient"),
            format="json",
        )
        self.assertEqual(updated.status_code, status.HTTP_200_OK)
        self.assertEqual(updated.data["name"], "Updated Patient")

        self.client.credentials()
        self.authenticate(self.other_user)
        self.assertEqual(
            self.client.get(f"/api/patients/{patient_id}/").status_code,
            status.HTTP_404_NOT_FOUND,
        )
        self.assertEqual(self.client.get("/api/patients/").data, [])
        self.assertEqual(
            self.client.delete(f"/api/patients/{patient_id}/").status_code,
            status.HTTP_404_NOT_FOUND,
        )
        self.assertTrue(Patient.objects.filter(pk=patient_id).exists())

        self.authenticate()
        deleted = self.client.delete(f"/api/patients/{patient_id}/")
        self.assertEqual(deleted.status_code, status.HTTP_204_NO_CONTENT)

    def test_patient_validation_and_missing_record(self):
        self.authenticate()
        invalid = self.client.post(
            "/api/patients/", self.patient_data(age=-1), format="json"
        )
        self.assertEqual(invalid.status_code, status.HTTP_400_BAD_REQUEST)
        missing = self.client.get("/api/patients/99999/")
        self.assertEqual(missing.status_code, status.HTTP_404_NOT_FOUND)

    def test_doctor_crud_validation_and_missing_record(self):
        self.authenticate()
        created = self.client.post(
            "/api/doctors/", self.doctor_data(), format="json"
        )
        self.assertEqual(created.status_code, status.HTTP_201_CREATED)
        doctor_id = created.data["id"]
        self.assertEqual(self.client.get("/api/doctors/").status_code, status.HTTP_200_OK)
        self.assertEqual(
            self.client.get(f"/api/doctors/{doctor_id}/").status_code,
            status.HTTP_200_OK,
        )

        updated = self.client.put(
            f"/api/doctors/{doctor_id}/",
            self.doctor_data(name="Dr. Updated"),
            format="json",
        )
        self.assertEqual(updated.status_code, status.HTTP_200_OK)
        self.assertEqual(updated.data["name"], "Dr. Updated")

        invalid = self.client.post(
            "/api/doctors/", self.doctor_data(email="invalid"), format="json"
        )
        self.assertEqual(invalid.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            self.client.get("/api/doctors/99999/").status_code,
            status.HTTP_404_NOT_FOUND,
        )
        self.assertEqual(
            self.client.delete(f"/api/doctors/{doctor_id}/").status_code,
            status.HTTP_204_NO_CONTENT,
        )

    def test_mappings_create_list_patient_lookup_delete_and_duplicate(self):
        self.authenticate()
        patient_response = self.client.post(
            "/api/patients/", self.patient_data(), format="json"
        )
        doctor_response = self.client.post(
            "/api/doctors/", self.doctor_data(), format="json"
        )
        patient_id = patient_response.data["id"]
        doctor_id = doctor_response.data["id"]

        mapping_response = self.client.post(
            "/api/mappings/",
            {"patient_id": patient_id, "doctor_id": doctor_id},
            format="json",
        )
        self.assertEqual(mapping_response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(mapping_response.data["patient_id"], patient_id)
        self.assertEqual(mapping_response.data["doctor_id"], doctor_id)
        mapping_id = mapping_response.data["id"]
        self.assertEqual(PatientDoctorMapping.objects.count(), 1)

        listing = self.client.get("/api/mappings/")
        self.assertEqual(len(listing.data), 1)
        patient_doctors = self.client.get(f"/api/mappings/{patient_id}/")
        self.assertEqual(patient_doctors.status_code, status.HTTP_200_OK)
        self.assertEqual([d["id"] for d in patient_doctors.data], [doctor_id])

        duplicate = self.client.post(
            "/api/mappings/",
            {"patient_id": patient_id, "doctor_id": doctor_id},
            format="json",
        )
        self.assertEqual(duplicate.status_code, status.HTTP_400_BAD_REQUEST)

        deleted = self.client.delete(f"/api/mappings/{mapping_id}/")
        self.assertEqual(deleted.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(PatientDoctorMapping.objects.exists())

    def test_mappings_validate_ids_and_enforce_patient_ownership(self):
        self.authenticate(self.other_user)
        other_patient = self.client.post(
            "/api/patients/", self.patient_data(), format="json"
        ).data["id"]
        doctor = Doctor.objects.create(
            name="Dr. Existing",
            specialization="Cardiology",
            email="existing@example.com",
            phone="555-0120",
        )

        self.authenticate()
        wrong_owner = self.client.post(
            "/api/mappings/",
            {"patient_id": other_patient, "doctor_id": doctor.pk},
            format="json",
        )
        self.assertEqual(wrong_owner.status_code, status.HTTP_400_BAD_REQUEST)
        invalid_patient = self.client.post(
            "/api/mappings/",
            {"patient_id": 99999, "doctor_id": doctor.pk},
            format="json",
        )
        self.assertEqual(invalid_patient.status_code, status.HTTP_400_BAD_REQUEST)
        invalid_doctor = self.client.post(
            "/api/mappings/",
            {"patient_id": self.client.post(
                "/api/patients/", self.patient_data(), format="json"
            ).data["id"], "doctor_id": 99999},
            format="json",
        )
        self.assertEqual(invalid_doctor.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            self.client.get(f"/api/mappings/{other_patient}/").status_code,
            status.HTTP_404_NOT_FOUND,
        )
        self.assertEqual(
            self.client.delete("/api/mappings/99999/").status_code,
            status.HTTP_404_NOT_FOUND,
        )
        self.assertEqual(
            self.client.get("/api/mappings/99999/").status_code,
            status.HTTP_404_NOT_FOUND,
        )
