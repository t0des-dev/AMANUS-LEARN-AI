from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from apps.organizations.models import Organization, OrganizationMember, RoleChoices

User = get_user_model()


class MultiTenantOrganizationTests(APITestCase):
    """
    Comprehensive test suite for Multi-Tenant Organization management and strict isolation.
    """

    def setUp(self):
        # User A and Organization A
        self.user_a = User.objects.create_user(
            email="user_a@tenant-a.com",
            password="PasswordA123!",
            first_name="Alice",
            last_name="Alpha",
        )
        self.org_a = Organization.objects.create(name="Organization Alpha")
        self.member_a_owner = OrganizationMember.objects.create(
            organization=self.org_a,
            user=self.user_a,
            role=RoleChoices.OWNER,
        )

        # User B and Organization B
        self.user_b = User.objects.create_user(
            email="user_b@tenant-b.com",
            password="PasswordB123!",
            first_name="Bob",
            last_name="Beta",
        )
        self.org_b = Organization.objects.create(name="Organization Beta")
        self.member_b_owner = OrganizationMember.objects.create(
            organization=self.org_b,
            user=self.user_b,
            role=RoleChoices.OWNER,
        )

        # Helper URLs
        self.org_list_url = reverse("v1:organization-list-create")
        self.org_a_detail_url = reverse("v1:organization-detail", kwargs={"id": self.org_a.id})
        self.org_b_detail_url = reverse("v1:organization-detail", kwargs={"id": self.org_b.id})
        self.org_a_members_url = reverse(
            "v1:organization-member-list-create", kwargs={"id": self.org_a.id}
        )
        self.org_b_members_url = reverse(
            "v1:organization-member-list-create", kwargs={"id": self.org_b.id}
        )

    def authenticate_as(self, user):
        refresh = RefreshToken.for_user(user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")

    # =========================================================================
    # 1. Multi-Tenant Strict Isolation Tests
    # =========================================================================

    def test_explicit_multi_tenant_isolation_read_cross_tenant_forbidden(self):
        """
        TEST EXPLICITE CRITIQUE :
        Un utilisateur de l'Organisation A ne peut JAMAIS lire les données de l'Organisation B.
        """
        self.authenticate_as(self.user_a)

        # User A tries to access Organization B details
        response = self.client.get(self.org_b_detail_url)
        # Should return 404 (preventing existence leak)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        # User A tries to list members of Organization B
        response = self.client.get(self.org_b_members_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_explicit_multi_tenant_isolation_update_cross_tenant_forbidden(self):
        """
        TEST EXPLICITE CRITIQUE :
        Un utilisateur de l'Organisation A ne peut JAMAIS modifier l'Organisation B.
        """
        self.authenticate_as(self.user_a)

        payload = {"name": "Hacked Name by User A"}
        response = self.client.patch(self.org_b_detail_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        self.org_b.refresh_from_db()
        self.assertEqual(self.org_b.name, "Organization Beta")

    def test_explicit_multi_tenant_isolation_delete_cross_tenant_forbidden(self):
        """
        TEST EXPLICITE CRITIQUE :
        Un utilisateur de l'Organisation A ne peut JAMAIS supprimer l'Organisation B.
        """
        self.authenticate_as(self.user_a)

        response = self.client.delete(self.org_b_detail_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        self.assertTrue(Organization.objects.filter(id=self.org_b.id).exists())

    def test_list_organizations_shows_only_own_tenants(self):
        """
        User A ne voit que l'Organisation A dans la liste, jamais l'Organisation B.
        User B ne voit que l'Organisation B dans la liste, jamais l'Organisation A.
        """
        # User A check
        self.authenticate_as(self.user_a)
        response_a = self.client.get(self.org_list_url)
        self.assertEqual(response_a.status_code, status.HTTP_200_OK)
        results_a = response_a.data.get("results", response_a.data)
        org_ids_a = [item["id"] for item in results_a]
        self.assertIn(str(self.org_a.id), org_ids_a)
        self.assertNotIn(str(self.org_b.id), org_ids_a)

        # User B check
        self.authenticate_as(self.user_b)
        response_b = self.client.get(self.org_list_url)
        self.assertEqual(response_b.status_code, status.HTTP_200_OK)
        results_b = response_b.data.get("results", response_b.data)
        org_ids_b = [item["id"] for item in results_b]
        self.assertIn(str(self.org_b.id), org_ids_b)
        self.assertNotIn(str(self.org_a.id), org_ids_b)

    # =========================================================================
    # 2. Organization CRUD Operations & Creator Ownership
    # =========================================================================

    def test_create_organization_sets_creator_as_owner(self):
        """
        Créer une organisation confère automatiquement le rôle OWNER au créateur.
        """
        new_user = User.objects.create_user(
            email="creator@amanus.ai",
            password="StrongPassword123!",
        )
        self.authenticate_as(new_user)

        payload = {"name": "New Gamma Institute", "plan": "PRO"}
        response = self.client.post(self.org_list_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        created_id = response.data["id"]
        org = Organization.objects.get(id=created_id)
        self.assertEqual(org.name, "New Gamma Institute")
        self.assertEqual(org.slug, "new-gamma-institute")
        self.assertEqual(org.plan, "PRO")

        membership = OrganizationMember.objects.filter(organization=org, user=new_user).first()
        self.assertIsNotNone(membership)
        self.assertEqual(membership.role, RoleChoices.OWNER)

    def test_owner_can_update_and_delete_organization(self):
        """Le OWNER peut modifier et supprimer son organisation."""
        self.authenticate_as(self.user_a)

        # Update
        patch_payload = {"name": "Organization Alpha Updated"}
        response = self.client.patch(self.org_a_detail_url, patch_payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], "Organization Alpha Updated")

        # Delete
        del_response = self.client.delete(self.org_a_detail_url)
        self.assertEqual(del_response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Organization.objects.filter(id=self.org_a.id).exists())

    # =========================================================================
    # 3. Roles and Permissions within the same Tenant
    # =========================================================================

    def test_admin_can_update_but_cannot_delete_organization(self):
        """L'administrateur peut modifier l'organisation mais seul l'OWNER peut la supprimer."""
        admin_user = User.objects.create_user(
            email="admin@tenant-a.com",
            password="PasswordAdmin123!",
        )
        OrganizationMember.objects.create(
            organization=self.org_a,
            user=admin_user,
            role=RoleChoices.ADMIN,
        )

        self.authenticate_as(admin_user)

        # Admin can update
        update_response = self.client.patch(
            self.org_a_detail_url, {"name": "Alpha Managed by Admin"}, format="json"
        )
        self.assertEqual(update_response.status_code, status.HTTP_200_OK)

        # Admin CANNOT delete
        delete_response = self.client.delete(self.org_a_detail_url)
        self.assertEqual(delete_response.status_code, status.HTTP_403_FORBIDDEN)

    def test_teacher_cannot_update_organization(self):
        """Un enseignant ne peut pas modifier l'organisation (403 Forbidden)."""
        teacher_user = User.objects.create_user(
            email="teacher@tenant-a.com",
            password="PasswordTeacher123!",
        )
        OrganizationMember.objects.create(
            organization=self.org_a,
            user=teacher_user,
            role=RoleChoices.TEACHER,
        )

        self.authenticate_as(teacher_user)
        response = self.client.patch(
            self.org_a_detail_url, {"name": "Unauthorized Change"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    # =========================================================================
    # 4. Member Management (List, Add, Update Role, Remove)
    # =========================================================================

    def test_add_member_to_organization_by_owner(self):
        """Le OWNER peut ajouter un nouvel apprenant ou enseignant par email."""
        self.authenticate_as(self.user_a)

        User.objects.create_user(
            email="student@tenant-a.com",
            password="PasswordStudent123!",
        )

        payload = {
            "email": "student@tenant-a.com",
            "role": RoleChoices.STUDENT,
        }
        response = self.client.post(self.org_a_members_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["role"], RoleChoices.STUDENT)
        self.assertEqual(response.data["user"]["email"], "student@tenant-a.com")

    def test_update_member_role(self):
        """Le OWNER peut promouvoir un étudiant en enseignant ou administrateur."""
        self.authenticate_as(self.user_a)

        student_user = User.objects.create_user(
            email="student.promo@tenant-a.com",
            password="Password123!",
        )
        member = OrganizationMember.objects.create(
            organization=self.org_a,
            user=student_user,
            role=RoleChoices.STUDENT,
        )

        member_detail_url = reverse(
            "v1:organization-member-detail",
            kwargs={"id": self.org_a.id, "member_id": member.id},
        )
        patch_payload = {"role": RoleChoices.TEACHER}
        response = self.client.patch(member_detail_url, patch_payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["role"], RoleChoices.TEACHER)

        member.refresh_from_db()
        self.assertEqual(member.role, RoleChoices.TEACHER)

    def test_cannot_remove_last_owner(self):
        """Il est interdit de supprimer le dernier propriétaire d'une organisation."""
        self.authenticate_as(self.user_a)

        member_detail_url = reverse(
            "v1:organization-member-detail",
            kwargs={"id": self.org_a.id, "member_id": self.member_a_owner.id},
        )
        response = self.client.delete(member_detail_url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("detail", response.data)
        self.assertTrue(OrganizationMember.objects.filter(id=self.member_a_owner.id).exists())
